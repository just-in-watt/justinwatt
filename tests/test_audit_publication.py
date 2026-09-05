import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from modules.audit_publication import (
    analyser_contenu,
    auditer_actifs_publics,
    auditer_arbre,
    auditer_fichiers,
)


class TestAuditPublication(unittest.TestCase):

    def ecrire_manifeste_actifs(self, racine, actifs):
        manifeste = racine / "docs/governance/public-assets.json"
        manifeste.parent.mkdir(parents=True)
        manifeste.write_text(
            json.dumps({"schema_version": 1, "assets": actifs}), encoding="utf-8"
        )
        return manifeste.relative_to(racine)

    def categories(self, contenu):
        return {
            violation.categorie
            for violation in analyser_contenu(Path("exemple.txt"), contenu)
        }

    def test_detecte_un_hote_ipv4_prive_sans_divulguer_sa_valeur(self):
        adresse = "192.168." + "1.24"
        violations = analyser_contenu(Path("configuration.txt"), adresse)

        self.assertEqual(violations[0].categorie, "hote_ipv4_prive")
        self.assertFalse(hasattr(violations[0], "valeur"))

    def test_accepte_les_reseaux_prives_utiles_aux_listes_de_controle(self):
        contenu = "\n".join(("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))

        self.assertEqual(self.categories(contenu), set())

    def test_une_declaration_reseau_ne_masque_pas_un_hote_sur_la_meme_ligne(self):
        contenu = "hote=192.168." + "1.24 reseau=192.168.0.0/16"

        self.assertEqual(self.categories(contenu), {"hote_ipv4_prive"})

    def test_accepte_les_adresses_ip_documentaires_rfc_5737(self):
        contenu = "192.0.2.24\n198.51.100.7\n203.0.113.9"

        self.assertEqual(self.categories(contenu), set())

    def test_detecte_mac_chemin_tailnet_et_courriel_non_documentaires(self):
        contenu = "\n".join(
            (
                "00:11:" + "22:33:44:55",
                "/home/" + "personne/config",
                "machine.tail" + "1234" + ".ts.net",
                "prenom@" + "domaine.fr",
            )
        )

        self.assertEqual(
            self.categories(contenu),
            {
                "adresse_mac_reelle_possible",
                "chemin_utilisateur_personnel",
                "nom_tailnet_prive_possible",
                "courriel_personnel_possible",
            },
        )

    def test_accepte_les_identifiants_explicites_d_exemple(self):
        contenu = "\n".join(
            (
                "02:00:00:00:00:01",
                "/home/solarpilot/config",
                "solarpilot.exemple.ts.net",
                "contributeur@example.com",
            )
        )

        self.assertEqual(self.categories(contenu), set())

    def test_detecte_des_formats_de_secrets_a_forte_confiance(self):
        contenu = "\n".join(
            (
                "gh" + "p_" + "A" * 24,
                "sk-" + "B" * 24,
                "AKIA" + "C" * 16,
                "-----BEGIN " + "PRIVATE KEY-----",
            )
        )

        self.assertEqual(
            self.categories(contenu),
            {"jeton_github", "jeton_openai", "cle_acces_aws", "cle_privee"},
        )

    def test_audite_uniquement_les_fichiers_demandes(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            (racine / "public.txt").write_text("192.0.2.1", encoding="utf-8")
            (racine / "hors_liste.txt").write_text(
                "10." + "1.2.3", encoding="utf-8"
            )

            violations = auditer_fichiers(racine, [Path("public.txt")])

        self.assertEqual(violations, [])

    def test_signale_un_fichier_binaire_a_qualifier(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            (racine / "actif.bin").write_bytes(b"image\0brute")

            violations = auditer_fichiers(racine, [Path("actif.bin")])

        self.assertEqual(violations[0].categorie, "fichier_binaire_a_qualifier")

    def test_ne_suit_pas_un_lien_symbolique(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            cible = racine / "cible.txt"
            cible.write_text("contenu", encoding="utf-8")
            (racine / "lien.txt").symlink_to(cible)

            violations = auditer_fichiers(racine, [Path("lien.txt")])

        self.assertEqual(violations[0].categorie, "lien_symbolique_a_qualifier")

    def test_accepte_un_actif_public_recense_et_inchange(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            actif = racine / "interface_web/pictogramme.svg"
            actif.parent.mkdir()
            actif.write_text("<svg/>", encoding="utf-8")
            manifeste = self.ecrire_manifeste_actifs(
                racine,
                [
                    {
                        "path": "interface_web/pictogramme.svg",
                        "sha256": hashlib.sha256(actif.read_bytes()).hexdigest(),
                        "origin": "original_project_geometry",
                        "license": "Apache-2.0",
                        "reviewed_on": "2026-09-05",
                    }
                ],
            )

            violations = auditer_actifs_publics(
                racine, [actif.relative_to(racine), manifeste]
            )

        self.assertEqual(violations, [])

    def test_bloque_un_actif_public_non_recense(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            actif = racine / "interface_web/inconnu.png"
            actif.parent.mkdir()
            actif.write_bytes(b"image")
            manifeste = self.ecrire_manifeste_actifs(racine, [])

            violations = auditer_actifs_publics(
                racine, [actif.relative_to(racine), manifeste]
            )

        self.assertEqual(violations[0].categorie, "actif_public_non_recense")

    def test_selection_peut_omettre_un_actif_recense_hors_instantane(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            actif = racine / "interface_web/public.svg"
            actif.parent.mkdir()
            actif.write_text("<svg/>", encoding="utf-8")
            manifeste = self.ecrire_manifeste_actifs(
                racine,
                [
                    {
                        "path": "interface_web/public.svg",
                        "sha256": hashlib.sha256(actif.read_bytes()).hexdigest(),
                        "origin": "original_project_geometry",
                        "license": "Apache-2.0",
                        "reviewed_on": "2026-09-05",
                    },
                    {
                        "path": "interface_web/prive.svg",
                        "sha256": "0" * 64,
                        "origin": "original_project_geometry",
                        "license": "Apache-2.0",
                        "reviewed_on": "2026-09-05",
                    },
                ],
            )

            violations = auditer_actifs_publics(
                racine,
                [actif.relative_to(racine), manifeste],
                exiger_actifs_recenses_absents=False,
            )

        self.assertEqual(violations, [])

    def test_bloque_un_manifeste_d_actifs_absent(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            actif = racine / "interface_web/inconnu.png"
            actif.parent.mkdir()
            actif.write_bytes(b"image")

            violations = auditer_actifs_publics(
                racine, [actif.relative_to(racine)]
            )

        self.assertEqual(
            violations[0].categorie, "manifeste_actifs_publics_absent"
        )

    def test_bloque_un_actif_public_symbolique(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            cible = racine / "cible.svg"
            cible.write_text("<svg/>", encoding="utf-8")
            actif = racine / "interface_web/pictogramme.svg"
            actif.parent.mkdir()
            actif.symlink_to(cible)
            manifeste = self.ecrire_manifeste_actifs(
                racine,
                [
                    {
                        "path": "interface_web/pictogramme.svg",
                        "sha256": hashlib.sha256(cible.read_bytes()).hexdigest(),
                        "origin": "original_project_geometry",
                        "license": "Apache-2.0",
                        "reviewed_on": "2026-09-05",
                    }
                ],
            )

            violations = auditer_actifs_publics(
                racine, [actif.relative_to(racine), manifeste]
            )

        self.assertEqual(violations[0].categorie, "lien_symbolique_a_qualifier")

    def test_bloque_la_modification_non_revue_d_un_actif_public(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            actif = racine / "interface_web/pictogramme.svg"
            actif.parent.mkdir()
            actif.write_text("<svg/>", encoding="utf-8")
            manifeste = self.ecrire_manifeste_actifs(
                racine,
                [
                    {
                        "path": "interface_web/pictogramme.svg",
                        "sha256": "0" * 64,
                        "origin": "original_project_geometry",
                        "license": "Apache-2.0",
                        "reviewed_on": "2026-09-05",
                    }
                ],
            )

            violations = auditer_actifs_publics(
                racine, [actif.relative_to(racine), manifeste]
            )

        self.assertEqual(
            violations[0].categorie, "empreinte_actif_public_inattendue"
        )

    def test_bloque_une_provenance_d_actif_indeterminee(self):
        with tempfile.TemporaryDirectory() as dossier:
            racine = Path(dossier)
            actif = racine / "interface_web/pictogramme.svg"
            actif.parent.mkdir()
            actif.write_text("<svg/>", encoding="utf-8")
            manifeste = self.ecrire_manifeste_actifs(
                racine,
                [
                    {
                        "path": "interface_web/pictogramme.svg",
                        "sha256": hashlib.sha256(actif.read_bytes()).hexdigest(),
                        "origin": "a_qualifier",
                        "license": "unknown",
                        "reviewed_on": "2026-09-05",
                    }
                ],
            )

            violations = auditer_actifs_publics(
                racine, [actif.relative_to(racine), manifeste]
            )

        self.assertEqual(
            {violation.categorie for violation in violations},
            {
                "licence_actif_public_indeterminee",
                "origine_actif_public_indeterminee",
            },
        )

    def test_arbre_de_travail_respecte_la_politique_automatique(self):
        self.assertEqual(auditer_arbre(), [])


if __name__ == "__main__":
    unittest.main()
