import unittest

from modules.decision_batterie import (
    ConfigurationDecisionBatterie,
    MoteurDecisionBatterie,
)
from modules.modele_energie import InstantaneEnergetique


class TestDecisionBatterie(unittest.TestCase):
    def setUp(self):
        self.moteur = MoteurDecisionBatterie()

    def test_propose_de_stocker_un_surplus(self):
        decision = self.moteur.evaluer(InstantaneEnergetique(3.2, 2.1, 65.0))

        self.assertEqual(decision.action, "stocker")
        self.assertAlmostEqual(decision.ecart_puissance_kw, 1.1)
        self.assertIn("1.100 kW", decision.raison)
        self.assertTrue(decision.simulation_uniquement)

    def test_attend_si_la_batterie_est_pleine(self):
        decision = self.moteur.evaluer(InstantaneEnergetique(3.2, 2.1, 100.0))

        self.assertEqual(decision.action, "attendre")
        self.assertIn("pleine", decision.raison)

    def test_propose_d_utiliser_la_batterie_en_deficit(self):
        decision = self.moteur.evaluer(InstantaneEnergetique(0.8, 1.6, 65.0))

        self.assertEqual(decision.action, "utiliser_batterie")
        self.assertAlmostEqual(decision.ecart_puissance_kw, -0.8)
        self.assertIn("0.800 kW", decision.raison)

    def test_attend_si_la_batterie_est_vide(self):
        decision = self.moteur.evaluer(InstantaneEnergetique(0.8, 1.6, 0.0))

        self.assertEqual(decision.action, "attendre")
        self.assertIn("vide", decision.raison)

    def test_attend_a_l_equilibre(self):
        decision = self.moteur.evaluer(InstantaneEnergetique(1.5, 1.5, 50.0))

        self.assertEqual(decision.action, "attendre")
        self.assertIn("équilibrées", decision.raison)

    def test_attend_si_les_mesures_sont_invalides(self):
        decision = self.moteur.evaluer(
            InstantaneEnergetique(3.2, 2.1, 65.0, mesures_valides=False)
        )

        self.assertEqual(decision.action, "attendre")
        self.assertIn("invalides", decision.raison)

    def test_attend_si_les_mesures_sont_perimees(self):
        decision = self.moteur.evaluer(
            InstantaneEnergetique(3.2, 2.1, 65.0, age_mesure_secondes=6.0)
        )

        self.assertEqual(decision.action, "attendre")
        self.assertIn("trop anciennes", decision.raison)

    def test_attend_si_la_confiance_est_insuffisante(self):
        decision = self.moteur.evaluer(
            InstantaneEnergetique(3.2, 2.1, 65.0, confiance=0.79)
        )

        self.assertEqual(decision.action, "attendre")
        self.assertIn("confiance", decision.raison)

    def test_refuse_un_objet_qui_n_est_pas_un_instantane(self):
        with self.assertRaisesRegex(ValueError, "instantané"):
            self.moteur.evaluer({"production_kw": 3.2})

    def test_refuse_une_configuration_invalide(self):
        with self.assertRaisesRegex(ValueError, "entre 0 et 1"):
            ConfigurationDecisionBatterie(confiance_minimum=1.1)


if __name__ == "__main__":
    unittest.main()
