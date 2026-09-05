import unittest
from io import StringIO
from unittest.mock import patch

from modules import simulateur_batterie


class TestSimulateurBatterie(unittest.TestCase):
    def test_couvre_les_trois_actions(self):
        actions = {
            etape.decision.action
            for etape in simulateur_batterie.simuler_scenarios()
        }

        self.assertEqual(actions, {"stocker", "utiliser_batterie", "attendre"})

    def test_affiche_le_caractere_simule(self):
        sortie = StringIO()
        with patch("sys.stdout", sortie):
            code = simulateur_batterie.main()

        self.assertEqual(code, 0)
        self.assertIn("aucune connexion ni commande physique", sortie.getvalue())
        self.assertIn("Aucune action physique", sortie.getvalue())


if __name__ == "__main__":
    unittest.main()
