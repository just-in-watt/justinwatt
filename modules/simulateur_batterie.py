from dataclasses import dataclass
from typing import Iterator, Tuple

from modules.decision_batterie import DecisionBatterie, MoteurDecisionBatterie
from modules.modele_energie import InstantaneEnergetique


SCENARIOS: Tuple[Tuple[str, InstantaneEnergetique], ...] = (
    (
        "Surplus solaire",
        InstantaneEnergetique(3.2, 2.1, 65.0),
    ),
    (
        "Déficit couvert par la batterie",
        InstantaneEnergetique(0.8, 1.6, 65.0),
    ),
    (
        "Batterie pleine",
        InstantaneEnergetique(3.2, 2.1, 100.0),
    ),
    (
        "Mesures périmées",
        InstantaneEnergetique(3.2, 2.1, 65.0, age_mesure_secondes=30.0),
    ),
)


@dataclass(frozen=True)
class EtapeSimulationBatterie:
    nom: str
    instantane: InstantaneEnergetique
    decision: DecisionBatterie


def simuler_scenarios() -> Iterator[EtapeSimulationBatterie]:
    moteur = MoteurDecisionBatterie()
    for nom, instantane in SCENARIOS:
        yield EtapeSimulationBatterie(
            nom=nom,
            instantane=instantane,
            decision=moteur.evaluer(instantane),
        )


def main() -> int:
    print()
    print("========================================")
    print(" Simulation consultative de batterie")
    print("========================================")
    print()
    print("🧪 Hors ligne : aucune connexion ni commande physique.")

    for etape in simuler_scenarios():
        instantane = etape.instantane
        decision = etape.decision
        print()
        print(etape.nom)
        print(f"  Production : {instantane.production_kw:.3f} kW")
        print(f"  Maison     : {instantane.consommation_kw:.3f} kW")
        print(f"  Batterie   : {instantane.niveau_batterie_pourcent:.1f} %")
        print(f"  Proposition: {decision.action}")
        print(f"  Raison     : {decision.raison}")

    print()
    print("Aucune action physique n’a été effectuée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
