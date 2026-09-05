import tempfile
import unittest
from pathlib import Path

from modules.audit_securite import (
    FICHIER_ACTION_SHELLY_PISCINE,
    FICHIER_LABORATOIRE_SHELLY,
    analyser_fichier,
    auditer_code,
)


class TestAuditSecurite(unittest.TestCase):

    def test_projet_ne_contient_aucune_ecriture_modbus(self):
        self.assertEqual(auditer_code(), [])

    def test_detecte_une_ecriture_de_registre(self):
        source = "client.write_register(address=10, value=1)\n"

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "dangereux.py"
            chemin.write_text(source, encoding="utf-8")
            violations = analyser_fichier(chemin)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].methode, "write_register")
        self.assertEqual(violations[0].ligne, 1)

    def test_n_interdit_pas_l_ecriture_des_csv(self):
        source = "ecrivain.writerow({'mesure': 1})\n"

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "journal.py"
            chemin.write_text(source, encoding="utf-8")
            violations = analyser_fichier(chemin)

        self.assertEqual(violations, [])

    def analyser_source(self, source):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "dangereux.py"
            chemin.write_text(source, encoding="utf-8")
            return analyser_fichier(chemin)

    def test_detecte_une_ecriture_de_bobine(self):
        violations = self.analyser_source("client.write_coil(1, True)\n")

        self.assertEqual(violations[0].methode, "write_coil")

    def test_detecte_un_alias_de_methode_interdite(self):
        source = "ecrire = client.write_register\necrire(10, 1)\n"
        violations = self.analyser_source(source)

        self.assertEqual(violations[0].methode, "ecrire")

    def test_detecte_getattr_sur_une_ecriture(self):
        source = 'getattr(client, "write_register")(10, 1)\n'
        violations = self.analyser_source(source)

        self.assertEqual(violations[0].methode, "write_register")

    def test_detecte_une_requete_d_ecriture_bas_niveau(self):
        source = "WriteSingleRegisterRequest(address=10, value=1)\n"
        violations = self.analyser_source(source)

        self.assertEqual(
            violations[0].methode,
            "WriteSingleRegisterRequest",
        )

    def test_detecte_execute_bas_niveau(self):
        violations = self.analyser_source("client.execute(requete)\n")

        self.assertEqual(violations[0].methode, "execute")

    def test_detecte_une_route_api_d_ecriture(self):
        source = 'route = "/api/writeModbus"\n'
        violations = self.analyser_source(source)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].methode, "route API /api/writeModbus")

    def test_accepte_les_routes_api_de_lecture_du_laboratoire(self):
        source = (
            'connexion = "/api/login"\n'
            'lecture = "/api/readInverterData"\n'
        )

        self.assertEqual(self.analyser_source(source), [])

    def test_detecte_une_commande_rpc_shelly(self):
        source = 'route = "/rpc/Switch.Set?id=0&on=true"\n'
        violations = self.analyser_source(source)

        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0].methode,
            "commande RPC Shelly /rpc/Switch.Set?id=0&on=true",
        )

    def test_autorise_switch_set_uniquement_dans_le_laboratoire_nomme(self):
        source = 'route = "/rpc/Switch.Set"\n'

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / FICHIER_LABORATOIRE_SHELLY
            chemin.write_text(source, encoding="utf-8")
            violations = auditer_code(dossier)

        self.assertEqual(violations, [])

    def test_toggle_reste_interdit_dans_le_laboratoire(self):
        source = 'route = "/rpc/Switch.Toggle"\n'

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / FICHIER_LABORATOIRE_SHELLY
            chemin.write_text(source, encoding="utf-8")
            violations = auditer_code(dossier)

        self.assertEqual(len(violations), 1)
        self.assertIn("Switch.Toggle", violations[0].methode)

    def test_detecte_un_appel_indirect_de_commande_hors_modules_nommes(self):
        source = "envoyer_etat_shelly(True)\n"

        violations = self.analyser_source(source)

        self.assertEqual(len(violations), 1)
        self.assertIn("envoyer_etat_shelly", violations[0].methode)

    def test_autorise_l_appel_indirect_dans_l_action_piscine_nommee(self):
        source = "envoyer_etat_shelly(True)\n"

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / FICHIER_ACTION_SHELLY_PISCINE
            chemin.write_text(source, encoding="utf-8")
            violations = auditer_code(dossier)

        self.assertEqual(violations, [])

    def test_un_nom_proche_ne_beneficie_pas_de_l_exception(self):
        source = 'route = "/rpc/Switch.Set"\n'

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / (
                "qualification_commande_shelly_piscine_copie.py"
            )
            chemin.write_text(source, encoding="utf-8")
            violations = auditer_code(dossier)

        self.assertEqual(len(violations), 1)
        self.assertIn("Switch.Set", violations[0].methode)

    def test_accepte_la_lecture_rpc_shelly(self):
        source = 'route = "/rpc/Switch.GetStatus?id=0"\n'

        self.assertEqual(self.analyser_source(source), [])


if __name__ == "__main__":
    unittest.main()
