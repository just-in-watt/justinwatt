import ast
from dataclasses import dataclass
from pathlib import Path


METHODES_ECRITURE_MODBUS = {
    "write_coil",
    "write_coils",
    "write_register",
    "write_registers",
    "mask_write_register",
    "readwrite_registers",
    "execute",
}

REQUETES_ECRITURE_MODBUS = {
    "WriteSingleCoilRequest",
    "WriteMultipleCoilsRequest",
    "WriteSingleRegisterRequest",
    "WriteMultipleRegistersRequest",
    "MaskWriteRegisterRequest",
    "ReadWriteMultipleRegistersRequest",
}

PREFIXES_API_MUTATION = tuple(
    f"/api/{action}"
    for action in (
        "save",
        "set",
        "update",
        "write",
    )
)

COMMANDES_RPC_SHELLY_INTERDITES = tuple(
    f"Switch.{action}"
    for action in (
        "Set",
        "Toggle",
    )
)

COMMANDE_RPC_SHELLY_LABORATOIRE = "Switch." + "Set"
FICHIER_LABORATOIRE_SHELLY = "qualification_commande_shelly_piscine.py"
FICHIER_ACTION_SHELLY_PISCINE = "action_filtration_piscine.py"
FICHIERS_COMMANDE_SHELLY_AUTORISES = {
    FICHIER_LABORATOIRE_SHELLY,
    FICHIER_ACTION_SHELLY_PISCINE,
}


@dataclass(frozen=True)
class ViolationSecurite:
    fichier: Path
    ligne: int
    methode: str


def analyser_fichier(chemin, autoriser_switch_set=False):
    chemin = Path(chemin)
    arbre = ast.parse(chemin.read_text(encoding="utf-8"), filename=str(chemin))
    violations = []
    alias_interdits = set()

    for noeud in ast.walk(arbre):
        if (
            isinstance(noeud, ast.Constant)
            and isinstance(noeud.value, str)
            and (
                noeud.value.startswith(PREFIXES_API_MUTATION)
                or any(
                    commande in noeud.value
                    for commande in COMMANDES_RPC_SHELLY_INTERDITES
                    if not (
                        autoriser_switch_set
                        and commande == COMMANDE_RPC_SHELLY_LABORATOIRE
                    )
                )
            )
        ):
            nature = (
                "commande RPC Shelly"
                if any(
                    commande in noeud.value
                    for commande in COMMANDES_RPC_SHELLY_INTERDITES
                    if not (
                        autoriser_switch_set
                        and commande == COMMANDE_RPC_SHELLY_LABORATOIRE
                    )
                )
                else "route API"
            )
            violations.append(
                ViolationSecurite(
                    fichier=chemin,
                    ligne=noeud.lineno,
                    methode=f"{nature} {noeud.value}",
                )
            )

    for noeud in ast.walk(arbre):
        if not isinstance(noeud, (ast.Assign, ast.AnnAssign)):
            continue

        valeur = noeud.value
        cibles = noeud.targets if isinstance(noeud, ast.Assign) else [noeud.target]
        interdit = (
            isinstance(valeur, ast.Attribute)
            and valeur.attr in METHODES_ECRITURE_MODBUS
        ) or (
            isinstance(valeur, ast.Name)
            and valeur.id in METHODES_ECRITURE_MODBUS | REQUETES_ECRITURE_MODBUS
        )

        if interdit:
            alias_interdits.update(
                cible.id for cible in cibles if isinstance(cible, ast.Name)
            )

    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Call):
            continue

        fonction = noeud.func

        methode = None

        if isinstance(fonction, ast.Attribute) and (
            fonction.attr in METHODES_ECRITURE_MODBUS
            or fonction.attr in REQUETES_ECRITURE_MODBUS
        ):
            methode = fonction.attr
        elif isinstance(fonction, ast.Name) and (
            fonction.id in METHODES_ECRITURE_MODBUS
            or fonction.id in REQUETES_ECRITURE_MODBUS
            or fonction.id in alias_interdits
        ):
            methode = fonction.id
        elif (
            isinstance(fonction, ast.Call)
            and isinstance(fonction.func, ast.Name)
            and fonction.func.id == "getattr"
            and len(fonction.args) >= 2
            and isinstance(fonction.args[1], ast.Constant)
            and fonction.args[1].value in METHODES_ECRITURE_MODBUS
        ):
            methode = fonction.args[1].value
        elif (
            isinstance(fonction, ast.Name)
            and fonction.id == "envoyer_etat_shelly"
            and not autoriser_switch_set
        ):
            methode = "appel de commande Shelly envoyer_etat_shelly"

        if methode is not None:
            violations.append(
                ViolationSecurite(
                    fichier=chemin,
                    ligne=noeud.lineno,
                    methode=methode,
                )
            )

    return violations


def auditer_code(dossier="modules"):
    dossier = Path(dossier)
    violations = []

    for chemin in sorted(dossier.glob("*.py")):
        violations.extend(
            analyser_fichier(
                chemin,
                autoriser_switch_set=(
                    chemin.name in FICHIERS_COMMANDE_SHELLY_AUTORISES
                ),
            )
        )

    return violations


def main():
    violations = auditer_code()

    if not violations:
        print(
            "✅ Aucune écriture Modbus ni commande Shelly hors modules "
            "explicitement autorisés détectée."
        )
        return 0

    print("❌ Opération(s) physique(s) interdite(s) détectée(s) :")

    for violation in violations:
        print(
            f"- {violation.fichier}:{violation.ligne} "
            f"({violation.methode})"
        )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
