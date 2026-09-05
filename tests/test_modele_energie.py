import unittest

from modules.modele_energie import InstantaneEnergetique


class TestInstantaneEnergetique(unittest.TestCase):
    def test_accepte_un_instantane_simule_valide(self):
        instantane = InstantaneEnergetique(3.2, 2.1, 65.0)

        self.assertEqual(instantane.production_kw, 3.2)
        self.assertEqual(instantane.provenance, "simulation")
        self.assertEqual(instantane.confiance, 1.0)

    def test_refuse_une_puissance_negative(self):
        with self.assertRaisesRegex(ValueError, "ne peuvent pas être négatives"):
            InstantaneEnergetique(-0.1, 2.1, 65.0)

    def test_refuse_un_niveau_de_batterie_hors_limites(self):
        for niveau in (-0.1, 100.1):
            with self.subTest(niveau=niveau):
                with self.assertRaisesRegex(ValueError, "entre 0 et 100"):
                    InstantaneEnergetique(3.2, 2.1, niveau)

    def test_refuse_les_nombres_non_finis(self):
        for valeur in (float("nan"), float("inf"), True):
            with self.subTest(valeur=valeur):
                with self.assertRaisesRegex(ValueError, "nombre fini"):
                    InstantaneEnergetique(valeur, 2.1, 65.0)

    def test_refuse_un_age_negatif(self):
        with self.assertRaisesRegex(ValueError, "âge.*négatif"):
            InstantaneEnergetique(3.2, 2.1, 65.0, age_mesure_secondes=-1)

    def test_refuse_une_confiance_hors_limites(self):
        with self.assertRaisesRegex(ValueError, "confiance.*entre 0 et 1"):
            InstantaneEnergetique(3.2, 2.1, 65.0, confiance=1.1)

    def test_refuse_un_faux_booleen_de_validite(self):
        with self.assertRaisesRegex(ValueError, "booléen"):
            InstantaneEnergetique(3.2, 2.1, 65.0, mesures_valides="oui")

    def test_refuse_une_provenance_vide(self):
        with self.assertRaisesRegex(ValueError, "provenance"):
            InstantaneEnergetique(3.2, 2.1, 65.0, provenance=" ")


if __name__ == "__main__":
    unittest.main()
