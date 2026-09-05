from dataclasses import dataclass
from math import isfinite


def _valider_nombre_fini(valeur: float, nom: str) -> None:
    try:
        valide = not isinstance(valeur, bool) and isfinite(valeur)
    except TypeError as erreur:
        raise ValueError(f"{nom} doit être un nombre fini.") from erreur
    if not valide:
        raise ValueError(f"{nom} doit être un nombre fini.")


@dataclass(frozen=True)
class InstantaneEnergetique:
    """Données simulées nécessaires à une recommandation énergétique."""

    production_kw: float
    consommation_kw: float
    niveau_batterie_pourcent: float
    provenance: str = "simulation"
    age_mesure_secondes: float = 0.0
    confiance: float = 1.0
    mesures_valides: bool = True

    def __post_init__(self) -> None:
        for nom, valeur in (
            ("La production", self.production_kw),
            ("La consommation", self.consommation_kw),
            ("Le niveau de batterie", self.niveau_batterie_pourcent),
            ("L’âge des mesures", self.age_mesure_secondes),
            ("La confiance", self.confiance),
        ):
            _valider_nombre_fini(valeur, nom)

        if self.production_kw < 0 or self.consommation_kw < 0:
            raise ValueError(
                "Production et consommation ne peuvent pas être négatives."
            )
        if not 0 <= self.niveau_batterie_pourcent <= 100:
            raise ValueError(
                "Le niveau de batterie doit être compris entre 0 et 100 %."
            )
        if self.age_mesure_secondes < 0:
            raise ValueError("L’âge des mesures ne peut pas être négatif.")
        if not 0 <= self.confiance <= 1:
            raise ValueError("La confiance doit être comprise entre 0 et 1.")
        if not isinstance(self.mesures_valides, bool):
            raise ValueError("mesures_valides doit être un booléen.")
        if not isinstance(self.provenance, str) or not self.provenance.strip():
            raise ValueError("La provenance doit être un texte non vide.")
