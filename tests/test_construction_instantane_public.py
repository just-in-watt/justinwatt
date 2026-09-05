import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from modules.construction_instantane_public import (
    ErreurInstantanePublic,
    auditer_selection,
    charger_manifeste,
    construire_instantane,
    verifier_dependances_python,
    verifier_manifeste,
)


class TestConstructionInstantanePublic(unittest.TestCase):
    MANIFESTE = Path("docs/governance/public-snapshot.json")

    def initialiser_depot(self, racine):
        subprocess.run(["git", "init", "-q", str(racine)], check=True)
        subprocess.run(
            ["git", "-C", str(racine), "config", "user.email", "test@example.com"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(racine), "config", "user.name", "Test"],
            check=True,
        )

    def ecrire_manifeste(
        self,
        racine,
        fichiers=None,
        *,
        statut="draft",
        revue=None,
        ajouter=True,
        committer=False,
    ):
        chemin = racine / self.MANIFESTE
        chemin.parent.mkdir(parents=True, exist_ok=True)
        fichiers = list(fichiers or [])
        if self.MANIFESTE.as_posix() not in fichiers:
            fichiers.append(self.MANIFESTE.as_posix())
        fichiers.sort()
        if revue is None:
            revue = {"reviewed_on": None, "reference": None}
        chemin.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": statut,
                    "review": revue,
                    "files": fichiers,
                }
            ),
            encoding="utf-8",
        )
        if ajouter:
            subprocess.run(["git", "-C", str(racine), "add", "."], check=True)
        if committer:
            subprocess.run(
                ["git", "-C", str(racine), "commit", "-qm", "fixture"],
                check=True,
            )
        return chemin

    def assert_code(self, code, action):
        with self.assertRaises(ErreurInstantanePublic) as contexte:
            action()
        self.assertEqual(contexte.exception.code, code)

    def test_manifeste_reel_est_valide_et_auto_inclus(self):
        racine = Path(__file__).resolve().parents[1]

        manifeste = verifier_manifeste(racine)

        self.assertIn(manifeste.statut, {"draft", "qualified"})
        self.assertIn(self.MANIFESTE, manifeste.fichiers)

    def test_selection_reelle_inclut_une_ci_sans_dependance_obligatoire(self):
        racine = Path(__file__).resolve().parents[1]

        manifeste = charger_manifeste(racine)
        workflow = racine / ".github/workflows/tests.yml"

        self.assertIn(Path(".github/workflows/tests.yml"), manifeste.fichiers)
        self.assertIn(Path(".gitignore"), manifeste.fichiers)
        self.assertIn(Path("TRADEMARKS.md"), manifeste.fichiers)
        contenu = workflow.read_text(encoding="utf-8")
        self.assertIn("hashFiles('requirements.txt') != ''", contenu)
        self.assertIn("permissions:\n  contents: read", contenu)
        self.assertIn(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            contenu,
        )
        self.assertIn(
            "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
            contenu,
        )

    def test_refuse_joker_traversal_doublon_et_ordre_ambigu(self):
        cas = {
            "joker": (["*.py"], "chemin_invalide"),
            "traversal": (["../secret"], "chemin_invalide"),
            "doublon": ([self.MANIFESTE.as_posix()] * 2, "chemin_duplique"),
            "ordre": (["z.txt", "a.txt"], "liste_fichiers_non_triee"),
        }
        for nom, (fichiers, code) in cas.items():
            with self.subTest(nom=nom), tempfile.TemporaryDirectory() as dossier:
                racine = Path(dossier)
                self.initialiser_depot(racine)
                fichiers_valides = {
                    item
                    for item in fichiers
                    if not any(c in item for c in "*?[]{}") and ".." not in item
                }
                for fichier in fichiers_valides:
                    chemin = racine / fichier
                    chemin.parent.mkdir(parents=True, exist_ok=True)
                    chemin.write_text("contenu", encoding="utf-8")
                chemin_manifeste = racine / self.MANIFESTE
                chemin_manifeste.parent.mkdir(parents=True, exist_ok=True)
                liste = list(fichiers)
                if nom not in {"doublon", "ordre"}:
                    liste.append(self.MANIFESTE.as_posix())
                    liste.sort()
                chemin_manifeste.write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "status": "draft",
                            "review": None,
                            "files": liste,
                        }
                    ),
                    encoding="utf-8",
                )
                subprocess.run(["git", "-C", str(racine), "add", "."], check=True)

                self.assert_code(code, lambda: charger_manifeste(racine))

    def test_refuse_fichier_non_suivi_absent_ou_symbolique(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            self.initialiser_depot(racine)
            (racine / "non-suivi.txt").write_text("contenu", encoding="utf-8")
            self.ecrire_manifeste(racine, ["non-suivi.txt"], ajouter=False)
            subprocess.run(
                ["git", "-C", str(racine), "add", self.MANIFESTE.as_posix()],
                check=True,
            )
            self.assert_code(
                "fichier_non_suivi", lambda: charger_manifeste(racine)
            )

            (racine / "non-suivi.txt").unlink()
            (racine / "manquant.txt").write_text("contenu", encoding="utf-8")
            self.ecrire_manifeste(racine, ["manquant.txt"])
            (racine / "manquant.txt").unlink()
            self.assert_code("fichier_absent", lambda: charger_manifeste(racine))

            (racine / "cible.txt").write_text("contenu", encoding="utf-8")
            (racine / "lien.txt").symlink_to("cible.txt")
            self.ecrire_manifeste(racine, ["lien.txt"])
            self.assert_code(
                "lien_symbolique_refuse", lambda: charger_manifeste(racine)
            )

    def test_refuse_qualification_sans_preuve_humaine(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            self.initialiser_depot(racine)
            self.ecrire_manifeste(racine, statut="qualified", revue=None)

            self.assert_code("date_revue_invalide", lambda: charger_manifeste(racine))

    def test_bloque_un_secret_dans_la_selection(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            self.initialiser_depot(racine)
            (racine / "public.txt").write_text(
                "gh" + "p_" + "A" * 24, encoding="utf-8"
            )
            self.ecrire_manifeste(racine, ["public.txt"])

            self.assert_code("jeton_github", lambda: verifier_manifeste(racine))

    def test_bloque_un_lien_markdown_vers_un_fichier_prive(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            self.initialiser_depot(racine)
            (racine / "README.md").write_text(
                "[preuve privée](docs/preuve.md)", encoding="utf-8"
            )
            (racine / "docs").mkdir()
            (racine / "docs/preuve.md").write_text("privé", encoding="utf-8")
            self.ecrire_manifeste(racine, ["README.md"])

            self.assert_code(
                "lien_markdown_hors_selection", lambda: verifier_manifeste(racine)
            )

    def test_bloque_un_import_python_interne_hors_selection(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            self.initialiser_depot(racine)
            (racine / "modules").mkdir()
            (racine / "modules/public.py").write_text(
                "from modules.prive import Secret\n", encoding="utf-8"
            )
            (racine / "modules/prive.py").write_text(
                "class Secret:\n    pass\n", encoding="utf-8"
            )
            self.ecrire_manifeste(racine, ["modules/public.py"])

            manifeste = charger_manifeste(racine)
            violations = verifier_dependances_python(racine, manifeste)

            self.assertEqual(len(violations), 1)
            self.assertEqual(
                violations[0].categorie, "dependance_python_hors_selection"
            )
            self.assert_code(
                "dependance_python_hors_selection",
                lambda: verifier_manifeste(racine),
            )

    def test_audite_un_sous_ensemble_d_actifs_recenses(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            self.initialiser_depot(racine)
            actifs = []
            for nom in ("public.svg", "prive.svg"):
                chemin = racine / "interface_web" / nom
                chemin.parent.mkdir(exist_ok=True)
                chemin.write_text(f"<svg><title>{nom}</title></svg>", encoding="utf-8")
                actifs.append(
                    {
                        "path": chemin.relative_to(racine).as_posix(),
                        "sha256": hashlib.sha256(chemin.read_bytes()).hexdigest(),
                        "origin": "original_project_geometry",
                        "license": "Apache-2.0",
                        "reviewed_on": "2026-09-05",
                    }
                )
            manifeste_actifs = racine / "docs/governance/public-assets.json"
            manifeste_actifs.parent.mkdir(parents=True)
            manifeste_actifs.write_text(
                json.dumps({"schema_version": 1, "assets": actifs}), encoding="utf-8"
            )
            self.ecrire_manifeste(
                racine,
                [
                    "docs/governance/public-assets.json",
                    "interface_web/public.svg",
                ],
            )

            manifeste = charger_manifeste(racine)

            self.assertEqual(auditer_selection(racine, manifeste), [])

    def test_un_brouillon_ne_peut_pas_etre_construit(self):
        with tempfile.TemporaryDirectory() as dossier:
            base = Path(dossier)
            racine = base / "source"
            racine.mkdir()
            self.initialiser_depot(racine)
            self.ecrire_manifeste(racine)

            self.assert_code(
                "manifeste_non_qualifie",
                lambda: construire_instantane(racine, base / "sortie"),
            )

    def test_construit_une_copie_neuve_et_un_inventaire_deterministe(self):
        with tempfile.TemporaryDirectory() as dossier:
            base = Path(dossier)
            racine = base / "source"
            racine.mkdir()
            self.initialiser_depot(racine)
            (racine / "public.txt").write_text("contenu public\n", encoding="utf-8")
            self.ecrire_manifeste(
                racine,
                ["public.txt"],
                statut="qualified",
                revue={"reviewed_on": "2026-09-05", "reference": "revue-42"},
                committer=True,
            )
            destination = base / "sortie"

            chemin_inventaire = construire_instantane(racine, destination)

            inventaire = json.loads(chemin_inventaire.read_text(encoding="utf-8"))
            self.assertEqual((destination / "public.txt").read_text(), "contenu public\n")
            self.assertFalse((destination / ".git").exists())
            self.assertEqual(
                [item["path"] for item in inventaire["included_files"]],
                [self.MANIFESTE.as_posix(), "public.txt"],
            )
            self.assertEqual(inventaire["excluded_tracked_file_count"], 0)
            self.assertEqual(inventaire["review_reference"], "revue-42")

    def test_refuse_destination_existante_et_selection_non_commitee(self):
        with tempfile.TemporaryDirectory() as dossier:
            base = Path(dossier)
            racine = base / "source"
            racine.mkdir()
            self.initialiser_depot(racine)
            fichier = racine / "public.txt"
            fichier.write_text("version 1", encoding="utf-8")
            self.ecrire_manifeste(
                racine,
                ["public.txt"],
                statut="qualified",
                revue={"reviewed_on": "2026-09-05", "reference": "revue-42"},
                committer=True,
            )
            destination = base / "sortie"
            destination.mkdir()

            self.assert_code(
                "destination_existante",
                lambda: construire_instantane(racine, destination),
            )

            destination.rmdir()
            fichier.write_text("version 2", encoding="utf-8")
            self.assert_code(
                "selection_non_commitee",
                lambda: construire_instantane(racine, destination),
            )


if __name__ == "__main__":
    unittest.main()
