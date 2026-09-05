from dataclasses import dataclass
from math import isfinite
from typing import Optional

from modules.modele_energie import InstantaneEnergetique


@dataclass(frozen=True)
class ConfigurationDecisionBatterie:
    age_maximum_mesure_secondes: float = 5.0
    confiance_minimum: float = 0.8
    tolerance_equilibre_kw: float = 1e-9

    def __post_init__(self) -> None:
        for nom, valeur in (
            ("L’âge maximal", self.age_maximum_mesure_secondes),
            ("La confiance minimale", self.confiance_minimum),
            ("La tolérance d’équilibre", self.tolerance_equilibre_kw),
        ):
            try:
                valide = not isinstance(valeur, bool) and isfinite(valeur)
            except TypeError as erreur:
                raise ValueError(f"{nom} doit être un nombre fini.") from erreur
            if not valide:
                raise ValueError(f"{nom} doit être un nombre fini.")

        if self.age_maximum_mesure_secondes < 0:
            raise ValueError("L’âge maximal ne peut pas être négatif.")
        if not 0 <= self.confiance_minimum <= 1:
            raise ValueError(
                "La confiance minimale doit être comprise entre 0 et 1."
            )
        if self.tolerance_equilibre_kw < 0:
            raise ValueError("La tolérance d’équilibre ne peut pas être négative.")


@dataclass(frozen=True)
class DecisionBatterie:
    action: str
    ecart_puissance_kw: float
    raison: str
    simulation_uniquement: bool = True


class MoteurDecisionBatterie:
    """Produit une recommandation simulée sans commander de matériel."""

    def __init__(
        self,
        configuration: Optional[ConfigurationDecisionBatterie] = None,
    ) -> None:
        self.configuration = configuration or ConfigurationDecisionBatterie()

    def evaluer(self, instantane: InstantaneEnergetique) -> DecisionBatterie:
        if not isinstance(instantane, InstantaneEnergetique):
            raise ValueError("Un instantané énergétique valide est nécessaire.")

        blocage = self._raison_attente_donnees(instantane)
        ecart_kw = instantane.production_kw - instantane.consommation_kw
        if blocage is not None:
            return self._decision("attendre", ecart_kw, blocage)

        tolerance = self.configuration.tolerance_equilibre_kw
        if abs(ecart_kw) <= tolerance:
            return self._decision(
                "attendre",
                ecart_kw,
                "Production et consommation sont équilibrées.",
            )

        if ecart_kw > tolerance:
            if instantane.niveau_batterie_pourcent >= 100:
                return self._decision(
                    "attendre",
                    ecart_kw,
                    "La batterie est pleine ; aucun stockage supplémentaire "
                    "n’est proposé.",
                )
            return self._decision(
                "stocker",
                ecart_kw,
                f"La production dépasse la consommation de {ecart_kw:.3f} kW "
                "et la batterie peut encore être chargée.",
            )

        deficit_kw = abs(ecart_kw)
        if instantane.niveau_batterie_pourcent <= 0:
            return self._decision(
                "attendre",
                ecart_kw,
                "La batterie est vide ; elle ne peut pas couvrir le déficit.",
            )
        return self._decision(
            "utiliser_batterie",
            ecart_kw,
            f"La consommation dépasse la production de {deficit_kw:.3f} kW "
            "et la batterie contient encore de l’énergie.",
        )

    def _raison_attente_donnees(
        self,
        instantane: InstantaneEnergetique,
    ) -> Optional[str]:
        if not instantane.mesures_valides:
            return (
                "Les mesures sont invalides ; aucune recommandation de transfert."
            )
        if (
            instantane.age_mesure_secondes
            > self.configuration.age_maximum_mesure_secondes
        ):
            return (
                "Les mesures sont trop anciennes ; aucune recommandation "
                "de transfert."
            )
        if instantane.confiance < self.configuration.confiance_minimum:
            return (
                "La confiance est insuffisante ; aucune recommandation de transfert."
            )
        return None

    @staticmethod
    def _decision(action: str, ecart_kw: float, raison: str) -> DecisionBatterie:
        return DecisionBatterie(
            action=action,
            ecart_puissance_kw=ecart_kw,
            raison=raison,
        )
