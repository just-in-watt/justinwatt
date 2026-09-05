# ADR 0178 — Préparer une publication open source assainie

- Statut : Accepté
- Date : 2026-09-03

## Contexte

SolarPilot prévoit un SDK public et des contributions communautaires, mais le
dépôt sert aussi de mémoire à une installation domestique réelle. Une
publication directe de son historique confondrait ces deux rôles.

L'audit initial du commit `3ebb7d58c7a1eb5e1bb70325bb43beda1cc190b4`
constate notamment :

- aucune licence ni politique publique de sécurité ou de contribution ;
- des adresses privées, chemins personnels, identifiants matériels et un nom de
  tailnet présents dans l'arbre courant ;
- 44 commits touchant au moins une donnée de topologie locale et trois commits
  touchant des adresses matérielles ;
- des adresses électroniques personnelles dans les métadonnées Git ;
- une seule dépendance d'exécution, `pymodbus==3.8.6`, déclarée sous licence
  BSD-3-Clause par ses métadonnées installées ;
- un projet open source antérieur nommé `SolarPILOT`, sans lien avec ce projet,
  qui impose une vérification séparée du nom et de la marque avant publication.

Le code contient par ailleurs des laboratoires et des exécuteurs physiques
fortement verrouillés. Les rendre lisibles ne doit ni les activer, ni faire
croire que l'autonomie matérielle est disponible par défaut.

## Décision

SolarPilot prépare son code et sa documentation originale sous licence
Apache-2.0. Les dépendances et contenus tiers conservent leurs licences propres.
La marque, le nom et l'identité visuelle ne sont pas concédés au-delà de ce que
permet la licence ; leur disponibilité juridique doit être vérifiée avant toute
annonce publique.

Le dépôt privé et son historique ne sont pas rendus publics tels quels. La
première publication doit provenir d'un instantané assaini, sans parents Git ni
métadonnées historiques privées. Cet instantané est créé à partir d'un commit
explicitement qualifié et seulement après les portes suivantes :

1. arbre courant sans secret, donnée personnelle ou identifiant domestique ;
2. tests complets et audit de sécurité réussis hors ligne ;
3. licences des dépendances et provenance des actifs vérifiées ;
4. nom du projet et règles de marque examinés ;
5. canaux de contribution et de divulgation responsable prêts ;
6. validation humaine du contenu public et autorisation explicite de publier.

Les exemples réseau utilisent les plages documentaires RFC 5737, des adresses
MAC localement administrées et des chemins génériques. Les vrais comptes,
secrets, coordonnées, identifiants, adresses d'équipement, journaux, preuves
brutes et paramètres de déploiement restent hors Git.

La publication ne modifie aucun niveau d'autorisation. Les exemples, tests et
CI n'appellent aucun équipement réel. Toute contribution qui touche un
transport de commande, un verrou, une capability ou une preuve de déploiement
reste soumise aux mêmes contrats et tests que dans le dépôt privé.

Les contributions passent par des pull requests visibles, relues et testées.
Une contribution n'est jamais déployée automatiquement sur l'installation de
référence et n'est pas réputée officielle du seul fait qu'elle existe.

## Alternatives écartées

- Rendre le dépôt actuel public en un clic : l'historique conserverait les
  données retirées de la dernière révision.
- Réécrire et forcer l'historique privé : opération destructive, fragile pour
  les worktrees et les tâches concurrentes, sans avantage par rapport à un
  instantané initial propre.
- Publier uniquement le moteur sans sa documentation : les verrous et limites
  deviendraient difficiles à comprendre et à revoir.
- Reporter toute préparation : cela prolongerait les valeurs domestiques dans
  le code et rendrait chaque future extraction plus risquée.

## Conséquences et retour arrière

La préparation peut être fusionnée dans le dépôt privé sans publication. Elle
réduit les données domestiques codées en dur, ajoute des contrôles reproductibles
et rend les contributions préparables. Elle ne crée aucun dépôt public, aucune
release et aucun déploiement.

Renoncer à la publication reste possible en retirant les seuls fichiers de
gouvernance publique. Les substitutions de valeurs domestiques par des exemples
documentaires restent souhaitables indépendamment de l'ouverture du projet.

## Impacts

- Architecture : frontière explicite entre sources publiques et exploitation
  privée.
- Sécurité et vie privée : publication fermée en cas de doute et historique
  privé non exporté.
- Plugins : même contrat public, aucune confiance implicite envers une origine
  communautaire.
- Tests : ajout d'un audit de publication sans réseau ni commande physique.
- Documentation : politique, contribution, sécurité, conduite, licence et
  attributions deviennent des portes de release.
