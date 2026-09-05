"""Audit hors ligne des données incompatibles avec un dépôt public."""

import argparse
import hashlib
import ipaddress
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


IPV4 = re.compile(r"(?<![0-9.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9.])")
MAC = re.compile(r"(?<![0-9A-Fa-f])(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}(?![0-9A-Fa-f])")
CHEMIN_PERSONNEL = re.compile(r"/(?:home|Users)/([A-Za-z0-9._-]+)")
HOTE_TAILSCALE = re.compile(
    r"(?<![A-Za-z0-9.-])([A-Za-z0-9.-]+\.ts\.net)(?![A-Za-z0-9.-])",
    re.IGNORECASE,
)
COURRIEL = re.compile(
    r"(?<![A-Za-z0-9._%+-])"
    r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})"
)

RESEAUX_PRIVES = tuple(
    ipaddress.ip_network(reseau)
    for reseau in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)
DECLARATIONS_RESEAUX_AUTORISEES = {
    str(reseau.network_address): f"/{reseau.prefixlen}" for reseau in RESEAUX_PRIVES
}
UTILISATEURS_EXEMPLES = {"UTILISATEUR", "solarpilot"}
DOMAINES_COURRIEL_EXEMPLES = {
    "example.com",
    "example.net",
    "example.org",
    "example.invalid",
    "exemple.invalid",
}

MANIFESTE_ACTIFS_PUBLICS = Path("docs/governance/public-assets.json")
EXTENSIONS_ACTIFS_PUBLICS = {
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".otf",
    ".png",
    ".svg",
    ".ttf",
    ".webp",
    ".woff",
    ".woff2",
}
EXTENSIONS_ACTIFS_BINAIRES = EXTENSIONS_ACTIFS_PUBLICS - {".svg"}
VALEURS_PROVENANCE_INDETERMINEES = {"", "unknown", "inconnue", "a_qualifier"}
EMPREINTE_SHA256 = re.compile(r"[0-9a-f]{64}")
DATE_ISO = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

MOTIFS_SECRETS = (
    (
        "cle_privee",
        re.compile("BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    ),
    (
        "jeton_github",
        re.compile(r"\bgh" + r"[opsu]_[A-Za-z0-9]{20,}\b"),
    ),
    (
        "jeton_openai",
        re.compile(r"\bsk-" + r"[A-Za-z0-9_-]{20,}\b"),
    ),
    (
        "cle_acces_aws",
        re.compile(r"\bAKIA" + r"[A-Z0-9]{16}\b"),
    ),
    (
        "jeton_jwt",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{16,}\."
            r"[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\b"
        ),
    ),
)


@dataclass(frozen=True)
class ViolationPublication:
    fichier: Path
    ligne: int
    categorie: str


def _est_hote_prive(correspondance, ligne):
    adresse = correspondance.group(0)
    try:
        ip = ipaddress.ip_address(adresse)
    except ValueError:
        return False

    if not any(ip in reseau for reseau in RESEAUX_PRIVES):
        return False

    suffixe_reseau = DECLARATIONS_RESEAUX_AUTORISEES.get(adresse)
    if suffixe_reseau is not None and ligne[correspondance.end() :].startswith(
        suffixe_reseau
    ):
        return False
    return True


def _mac_est_documentaire(adresse):
    premier_octet = int(adresse.split(":", 1)[0], 16)
    return bool(premier_octet & 0b10)


def analyser_contenu(chemin, contenu):
    """Retourne uniquement catégorie et position, jamais la valeur trouvée."""
    violations = []

    for numero, ligne in enumerate(contenu.splitlines(), start=1):
        categories = set()

        if any(_est_hote_prive(match, ligne) for match in IPV4.finditer(ligne)):
            categories.add("hote_ipv4_prive")

        for match in MAC.finditer(ligne):
            if not _mac_est_documentaire(match.group(0)):
                categories.add("adresse_mac_reelle_possible")

        for match in CHEMIN_PERSONNEL.finditer(ligne):
            if match.group(1) not in UTILISATEURS_EXEMPLES:
                categories.add("chemin_utilisateur_personnel")

        for match in HOTE_TAILSCALE.finditer(ligne):
            hote = match.group(1).lower()
            if hote != "exemple.ts.net" and not hote.endswith(".exemple.ts.net"):
                categories.add("nom_tailnet_prive_possible")

        for match in COURRIEL.finditer(ligne):
            if match.group(0).lower().endswith(".service"):
                continue
            if match.group(1).lower() not in DOMAINES_COURRIEL_EXEMPLES:
                categories.add("courriel_personnel_possible")

        for categorie, motif in MOTIFS_SECRETS:
            if motif.search(ligne):
                categories.add(categorie)

        violations.extend(
            ViolationPublication(Path(chemin), numero, categorie)
            for categorie in sorted(categories)
        )

    return violations


def auditer_fichiers(racine, fichiers):
    racine = Path(racine).resolve()
    violations = []

    for fichier in sorted(Path(fichier) for fichier in fichiers):
        chemin = racine / fichier
        if chemin.is_symlink():
            violations.append(
                ViolationPublication(fichier, 0, "lien_symbolique_a_qualifier")
            )
            continue
        contenu_brut = chemin.read_bytes()
        if b"\0" in contenu_brut:
            violations.append(
                ViolationPublication(fichier, 0, "fichier_binaire_a_qualifier")
            )
            continue

        try:
            contenu = contenu_brut.decode("utf-8")
        except UnicodeDecodeError:
            violations.append(
                ViolationPublication(fichier, 0, "encodage_non_utf8_a_qualifier")
            )
            continue

        violations.extend(analyser_contenu(fichier, contenu))

    return violations


def auditer_actifs_publics(
    racine, fichiers, *, exiger_actifs_recenses_absents=True
):
    """Vérifie l'inventaire, la provenance et l'empreinte des actifs publics.

    L'audit d'un arbre complet exige tous les actifs recensés. Un constructeur
    d'instantané peut contrôler une sélection stricte sans rendre obligatoire
    un actif du dépôt privé qui ne fait pas partie de cette sélection.
    """
    racine = Path(racine).resolve()
    fichiers = {Path(fichier) for fichier in fichiers}
    actifs_reels = {
        fichier
        for fichier in fichiers
        if fichier.suffix.lower() in EXTENSIONS_ACTIFS_PUBLICS
    }
    chemin_manifeste = racine / MANIFESTE_ACTIFS_PUBLICS

    if MANIFESTE_ACTIFS_PUBLICS not in fichiers or not chemin_manifeste.is_file():
        return [
            ViolationPublication(
                MANIFESTE_ACTIFS_PUBLICS, 0, "manifeste_actifs_publics_absent"
            )
        ]

    try:
        manifeste = json.loads(chemin_manifeste.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return [
            ViolationPublication(
                MANIFESTE_ACTIFS_PUBLICS, 0, "manifeste_actifs_publics_invalide"
            )
        ]

    if not isinstance(manifeste, dict) or manifeste.get("schema_version") != 1:
        return [
            ViolationPublication(
                MANIFESTE_ACTIFS_PUBLICS, 0, "schema_manifeste_actifs_invalide"
            )
        ]

    entrees = manifeste.get("assets")
    if not isinstance(entrees, list):
        return [
            ViolationPublication(
                MANIFESTE_ACTIFS_PUBLICS, 0, "liste_actifs_publics_invalide"
            )
        ]

    violations = []
    actifs_recenses = set()
    for entree in entrees:
        if not isinstance(entree, dict):
            violations.append(
                ViolationPublication(
                    MANIFESTE_ACTIFS_PUBLICS, 0, "entree_actif_public_invalide"
                )
            )
            continue

        chemin_brut = entree.get("path")
        if not isinstance(chemin_brut, str):
            violations.append(
                ViolationPublication(
                    MANIFESTE_ACTIFS_PUBLICS, 0, "chemin_actif_public_invalide"
                )
            )
            continue

        actif = Path(chemin_brut)
        if (
            actif.is_absolute()
            or ".." in actif.parts
            or actif.as_posix() != chemin_brut
        ):
            violations.append(
                ViolationPublication(
                    MANIFESTE_ACTIFS_PUBLICS, 0, "chemin_actif_public_invalide"
                )
            )
            continue
        if actif in actifs_recenses:
            violations.append(
                ViolationPublication(actif, 0, "actif_public_recense_plusieurs_fois")
            )
            continue
        actifs_recenses.add(actif)

        if actif not in actifs_reels:
            if exiger_actifs_recenses_absents:
                violations.append(
                    ViolationPublication(actif, 0, "actif_public_recense_absent")
                )
            continue

        chemin_actif = racine / actif
        if chemin_actif.is_symlink():
            violations.append(
                ViolationPublication(actif, 0, "lien_symbolique_a_qualifier")
            )
            continue
        if not chemin_actif.is_file():
            violations.append(
                ViolationPublication(actif, 0, "actif_public_recense_absent")
            )
            continue

        origine = entree.get("origin")
        licence = entree.get("license")
        revue = entree.get("reviewed_on")
        if (
            not isinstance(origine, str)
            or origine.strip().lower() in VALEURS_PROVENANCE_INDETERMINEES
        ):
            violations.append(
                ViolationPublication(actif, 0, "origine_actif_public_indeterminee")
            )
        if (
            not isinstance(licence, str)
            or licence.strip().lower() in VALEURS_PROVENANCE_INDETERMINEES
        ):
            violations.append(
                ViolationPublication(actif, 0, "licence_actif_public_indeterminee")
            )
        if not isinstance(revue, str) or DATE_ISO.fullmatch(revue) is None:
            violations.append(
                ViolationPublication(actif, 0, "date_revue_actif_public_invalide")
            )

        empreinte = entree.get("sha256")
        if (
            not isinstance(empreinte, str)
            or EMPREINTE_SHA256.fullmatch(empreinte) is None
        ):
            violations.append(
                ViolationPublication(actif, 0, "empreinte_actif_public_invalide")
            )
            continue
        empreinte_reelle = hashlib.sha256(chemin_actif.read_bytes()).hexdigest()
        if empreinte_reelle != empreinte:
            violations.append(
                ViolationPublication(actif, 0, "empreinte_actif_public_inattendue")
            )

    for actif in sorted(actifs_reels - actifs_recenses):
        violations.append(ViolationPublication(actif, 0, "actif_public_non_recense"))

    return violations


def lister_fichiers_suivis(racine):
    resultat = subprocess.run(
        [
            "git",
            "-C",
            str(racine),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        check=True,
        capture_output=True,
    )
    return [
        Path(nom.decode("utf-8"))
        for nom in resultat.stdout.split(b"\0")
        if nom
    ]


def auditer_arbre(racine=None):
    racine = (
        Path(racine).resolve()
        if racine is not None
        else Path(__file__).resolve().parents[1]
    )
    fichiers = lister_fichiers_suivis(racine)
    fichiers_analysables = [
        fichier
        for fichier in fichiers
        if fichier.suffix.lower() not in EXTENSIONS_ACTIFS_BINAIRES
    ]
    return auditer_fichiers(racine, fichiers_analysables) + auditer_actifs_publics(
        racine, fichiers
    )


def main(argv=None):
    analyseur = argparse.ArgumentParser(
        description="Détecte hors ligne les données impropres à une publication."
    )
    analyseur.add_argument("--racine", type=Path, default=None)
    arguments = analyseur.parse_args(argv)

    violations = auditer_arbre(arguments.racine)
    if not violations:
        print("✅ Arbre Git compatible avec les règles automatiques de publication.")
        return 0

    print("❌ Publication bloquée par des données à examiner :")
    for violation in violations:
        print(f"- {violation.fichier}:{violation.ligne} ({violation.categorie})")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
