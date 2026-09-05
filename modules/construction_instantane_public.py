"""Construit hors ligne un instantané public depuis une liste blanche exacte."""

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlsplit

from modules.audit_publication import (
    EXTENSIONS_ACTIFS_BINAIRES,
    EXTENSIONS_ACTIFS_PUBLICS,
    MANIFESTE_ACTIFS_PUBLICS,
    ViolationPublication,
    auditer_actifs_publics,
    auditer_fichiers,
)


MANIFESTE_PAR_DEFAUT = Path("docs/governance/public-snapshot.json")
INVENTAIRE_INSTANTANE = Path(".justinwatt-public-snapshot.json")
STATUTS_MANIFESTE = {"draft", "qualified"}
CARACTERES_JOKER = frozenset("*?[]{}")
CHAMPS_MANIFESTE = {"schema_version", "status", "review", "files"}
CHAMPS_REVUE = {"reviewed_on", "reference"}
LIEN_MARKDOWN = re.compile(
    r"!?\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)"
)
DEFINITION_MARKDOWN = re.compile(r"^\s*\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))", re.MULTILINE)


class ErreurInstantanePublic(ValueError):
    """Erreur fermée ne contenant jamais le contenu sensible détecté."""

    def __init__(self, code, chemin=None):
        self.code = code
        self.chemin = Path(chemin) if chemin is not None else None
        detail = f" : {self.chemin.as_posix()}" if self.chemin is not None else ""
        super().__init__(f"{code}{detail}")


@dataclass(frozen=True)
class ManifesteInstantanePublic:
    statut: str
    fichiers: tuple[Path, ...]
    date_revue: Optional[str]
    reference_revue: Optional[str]
    chemin: Path


def _executer_git(racine, *arguments):
    return subprocess.run(
        ["git", "-C", str(racine), *arguments],
        check=True,
        capture_output=True,
    )


def _lister_fichiers_suivis(racine):
    resultat = _executer_git(racine, "ls-files", "--cached", "-z")
    return {
        Path(nom.decode("utf-8"))
        for nom in resultat.stdout.split(b"\0")
        if nom
    }


def _normaliser_chemin(chemin_brut):
    if not isinstance(chemin_brut, str) or not chemin_brut:
        raise ErreurInstantanePublic("chemin_invalide")
    chemin = Path(chemin_brut)
    if (
        chemin.is_absolute()
        or chemin_brut.startswith("/")
        or "\\" in chemin_brut
        or chemin.as_posix() != chemin_brut
        or any(part in {"", ".", ".."} for part in chemin.parts)
        or any(caractere in chemin_brut for caractere in CARACTERES_JOKER)
    ):
        raise ErreurInstantanePublic("chemin_invalide", chemin)
    return chemin


def _verifier_absence_lien_symbolique(racine, chemin):
    courant = racine
    for partie in chemin.parts:
        courant = courant / partie
        if courant.is_symlink():
            raise ErreurInstantanePublic("lien_symbolique_refuse", chemin)


def charger_manifeste(racine, chemin=MANIFESTE_PAR_DEFAUT):
    """Charge et valide la structure et les chemins du manifeste versionné."""
    racine = Path(racine).resolve()
    chemin = _normaliser_chemin(Path(chemin).as_posix())
    chemin_absolu = racine / chemin
    _verifier_absence_lien_symbolique(racine, chemin)

    try:
        donnees = json.loads(chemin_absolu.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as erreur:
        raise ErreurInstantanePublic("manifeste_invalide", chemin) from erreur

    if not isinstance(donnees, dict) or donnees.get("schema_version") != 1:
        raise ErreurInstantanePublic("schema_manifeste_invalide", chemin)
    if set(donnees) != CHAMPS_MANIFESTE:
        raise ErreurInstantanePublic("champs_manifeste_invalides", chemin)

    statut = donnees.get("status")
    if statut not in STATUTS_MANIFESTE:
        raise ErreurInstantanePublic("statut_manifeste_invalide", chemin)

    fichiers_bruts = donnees.get("files")
    if not isinstance(fichiers_bruts, list) or not fichiers_bruts:
        raise ErreurInstantanePublic("liste_fichiers_invalide", chemin)

    fichiers = tuple(_normaliser_chemin(item) for item in fichiers_bruts)
    if len(set(fichiers)) != len(fichiers):
        raise ErreurInstantanePublic("chemin_duplique")
    if tuple(sorted(fichiers)) != fichiers:
        raise ErreurInstantanePublic("liste_fichiers_non_triee")
    if chemin not in fichiers:
        raise ErreurInstantanePublic("manifeste_non_inclus", chemin)

    suivis = _lister_fichiers_suivis(racine)
    for fichier in fichiers:
        _verifier_absence_lien_symbolique(racine, fichier)
        if fichier not in suivis:
            raise ErreurInstantanePublic("fichier_non_suivi", fichier)
        if not (racine / fichier).is_file():
            raise ErreurInstantanePublic("fichier_absent", fichier)

    revue = donnees.get("review")
    if not isinstance(revue, dict) or set(revue) != CHAMPS_REVUE:
        raise ErreurInstantanePublic("champs_revue_invalides", chemin)
    date_revue = revue.get("reviewed_on")
    reference_revue = revue.get("reference")
    if date_revue is not None and not isinstance(date_revue, str):
        raise ErreurInstantanePublic("date_revue_invalide", chemin)
    if reference_revue is not None and not isinstance(reference_revue, str):
        raise ErreurInstantanePublic("reference_revue_invalide", chemin)
    if statut == "qualified":
        try:
            date.fromisoformat(date_revue)
        except (TypeError, ValueError) as erreur:
            raise ErreurInstantanePublic("date_revue_invalide", chemin) from erreur
        if not isinstance(reference_revue, str) or not reference_revue.strip():
            raise ErreurInstantanePublic("reference_revue_absente", chemin)

    return ManifesteInstantanePublic(
        statut=statut,
        fichiers=fichiers,
        date_revue=date_revue,
        reference_revue=reference_revue,
        chemin=chemin,
    )


def auditer_selection(racine, manifeste):
    """Retourne les violations automatiques de la seule sélection publique."""
    racine = Path(racine).resolve()
    fichiers_texte = [
        fichier
        for fichier in manifeste.fichiers
        if fichier.suffix.lower() not in EXTENSIONS_ACTIFS_BINAIRES
    ]
    violations = auditer_fichiers(racine, fichiers_texte)

    actifs = {
        fichier
        for fichier in manifeste.fichiers
        if fichier.suffix.lower() in EXTENSIONS_ACTIFS_PUBLICS
    }
    if actifs:
        violations.extend(
            auditer_actifs_publics(
                racine,
                actifs | ({MANIFESTE_ACTIFS_PUBLICS} & set(manifeste.fichiers)),
                exiger_actifs_recenses_absents=False,
            )
        )
    return violations


def _cibles_markdown(contenu):
    for motif in (LIEN_MARKDOWN, DEFINITION_MARKDOWN):
        for correspondance in motif.finditer(contenu):
            yield correspondance.group(1) or correspondance.group(2)


def verifier_liens_markdown(racine, manifeste):
    """Signale les liens relatifs qui sortent de la sélection ou sont absents."""
    racine = Path(racine).resolve()
    selection = set(manifeste.fichiers)
    violations = []
    for fichier in manifeste.fichiers:
        if fichier.suffix.lower() not in {".md", ".markdown"}:
            continue
        contenu = (racine / fichier).read_text(encoding="utf-8")
        for cible_brute in _cibles_markdown(contenu):
            morceaux = urlsplit(cible_brute)
            if morceaux.scheme or morceaux.netloc or cible_brute.startswith("#"):
                continue
            cible_texte = unquote(morceaux.path)
            if not cible_texte:
                continue
            if cible_texte.startswith("/"):
                violations.append(
                    ViolationPublication(fichier, 0, "lien_markdown_hors_selection")
                )
                continue
            cible = Path(os.path.normpath((fichier.parent / cible_texte).as_posix()))
            if (
                ".." in cible.parts
                or cible not in selection
                or not (racine / cible).is_file()
            ):
                violations.append(
                    ViolationPublication(fichier, 0, "lien_markdown_hors_selection")
                )
    return violations


def _candidats_module_interne(racine, nom_module):
    parties = tuple(partie for partie in nom_module.split(".") if partie)
    if not parties:
        return ()
    module = Path(*parties).with_suffix(".py")
    paquet = Path(*parties) / "__init__.py"
    return tuple(
        candidat for candidat in (module, paquet) if (racine / candidat).is_file()
    )


def _nom_import_relatif(fichier, noeud):
    paquet = list(fichier.with_suffix("").parts[:-1])
    remontees = noeud.level - 1
    if remontees > len(paquet):
        return None
    if remontees:
        paquet = paquet[:-remontees]
    if noeud.module:
        paquet.extend(noeud.module.split("."))
    return ".".join(paquet)


def _imports_internes(racine, fichier):
    arbre = ast.parse(
        (racine / fichier).read_text(encoding="utf-8"),
        filename=str(fichier),
    )
    for noeud in ast.walk(arbre):
        noms = []
        if isinstance(noeud, ast.Import):
            noms.extend(alias.name for alias in noeud.names)
        elif isinstance(noeud, ast.ImportFrom):
            base = (
                noeud.module
                if noeud.level == 0
                else _nom_import_relatif(fichier, noeud)
            )
            if base:
                noms.append(base)
                noms.extend(f"{base}.{alias.name}" for alias in noeud.names)
        for nom in noms:
            for dependance in _candidats_module_interne(racine, nom):
                yield dependance, getattr(noeud, "lineno", 0)


def verifier_dependances_python(racine, manifeste):
    """Signale tout import Python interne résolu mais absent de la sélection."""
    racine = Path(racine).resolve()
    selection = set(manifeste.fichiers)
    violations = []
    deja_signalees = set()
    for fichier in manifeste.fichiers:
        if fichier.suffix.lower() != ".py":
            continue
        try:
            imports = tuple(_imports_internes(racine, fichier))
        except (SyntaxError, UnicodeError):
            violations.append(
                ViolationPublication(fichier, 0, "syntaxe_python_invalide")
            )
            continue
        for dependance, ligne in imports:
            cle = (fichier, ligne, dependance)
            if dependance not in selection and cle not in deja_signalees:
                deja_signalees.add(cle)
                violations.append(
                    ViolationPublication(
                        fichier,
                        ligne,
                        "dependance_python_hors_selection",
                    )
                )
    return violations


def verifier_manifeste(racine, chemin=MANIFESTE_PAR_DEFAUT):
    """Valide le manifeste et bloque toute sélection encore ambiguë."""
    manifeste = charger_manifeste(racine, chemin)
    violations = auditer_selection(racine, manifeste)
    violations.extend(verifier_liens_markdown(racine, manifeste))
    violations.extend(verifier_dependances_python(racine, manifeste))
    if violations:
        premiere = violations[0]
        raise ErreurInstantanePublic(premiere.categorie, premiere.fichier)
    return manifeste


def _empreinte(chemin):
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


def _revision_source(racine):
    return _executer_git(racine, "rev-parse", "HEAD").stdout.decode("ascii").strip()


def _selection_est_propre(racine, fichiers):
    resultat = subprocess.run(
        [
            "git",
            "-C",
            str(racine),
            "diff",
            "--quiet",
            "HEAD",
            "--",
            *map(str, fichiers),
        ],
        check=False,
    )
    return resultat.returncode == 0


def construire_instantane(racine, destination, chemin=MANIFESTE_PAR_DEFAUT):
    """Construit une copie locale neuve, sans Git, depuis un manifeste qualifié."""
    racine = Path(racine).resolve()
    destination = Path(destination).resolve()
    manifeste = verifier_manifeste(racine, chemin)
    if manifeste.statut != "qualified":
        raise ErreurInstantanePublic("manifeste_non_qualifie", manifeste.chemin)
    if destination == racine or destination.is_relative_to(racine):
        raise ErreurInstantanePublic("destination_dans_source", destination)
    if destination.exists():
        raise ErreurInstantanePublic("destination_existante", destination)
    if not destination.parent.is_dir():
        raise ErreurInstantanePublic("parent_destination_absent", destination.parent)
    if not _selection_est_propre(racine, manifeste.fichiers):
        raise ErreurInstantanePublic("selection_non_commitee")

    suivis = _lister_fichiers_suivis(racine)
    destination.mkdir(parents=False)
    try:
        inventaire = []
        for fichier in manifeste.fichiers:
            source = racine / fichier
            cible = destination / fichier
            cible.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, cible)
            mode = source.stat().st_mode
            cible.chmod(0o755 if mode & stat.S_IXUSR else 0o644)
            inventaire.append(
                {"path": fichier.as_posix(), "sha256": _empreinte(cible)}
            )

        contenu_inventaire = {
            "schema_version": 1,
            "source_revision": _revision_source(racine),
            "reviewed_on": manifeste.date_revue,
            "review_reference": manifeste.reference_revue,
            "included_files": inventaire,
            "excluded_tracked_file_count": len(suivis - set(manifeste.fichiers)),
        }
        (destination / INVENTAIRE_INSTANTANE).write_text(
            json.dumps(contenu_inventaire, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        violations_copie = auditer_selection(destination, manifeste)
        violations_copie.extend(verifier_liens_markdown(destination, manifeste))
        violations_copie.extend(
            auditer_fichiers(destination, [INVENTAIRE_INSTANTANE])
        )
        if violations_copie:
            premiere = violations_copie[0]
            raise ErreurInstantanePublic(premiere.categorie, premiere.fichier)
        if not _selection_est_propre(racine, manifeste.fichiers):
            raise ErreurInstantanePublic("selection_modifiee_pendant_copie")
    except Exception:
        shutil.rmtree(destination)
        raise
    return destination / INVENTAIRE_INSTANTANE


def main(argv=None):
    analyseur = argparse.ArgumentParser(
        description="Vérifie ou construit l'instantané public JustInWatt."
    )
    analyseur.add_argument("--racine", type=Path, default=Path.cwd())
    analyseur.add_argument("--manifeste", type=Path, default=MANIFESTE_PAR_DEFAUT)
    analyseur.add_argument("--destination", type=Path)
    arguments = analyseur.parse_args(argv)

    try:
        if arguments.destination is None:
            manifeste = verifier_manifeste(arguments.racine, arguments.manifeste)
            print(
                f"✅ Liste blanche {manifeste.statut} valide : "
                f"{len(manifeste.fichiers)} fichiers exacts."
            )
        else:
            inventaire = construire_instantane(
                arguments.racine, arguments.destination, arguments.manifeste
            )
            print(f"✅ Instantané local construit ; inventaire : {inventaire}")
    except ErreurInstantanePublic as erreur:
        print(f"❌ Instantané public bloqué : {erreur}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
