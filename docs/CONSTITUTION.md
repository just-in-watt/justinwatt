# Constitution de JustInWatt

## Statut

Cette Constitution rassemble les principes durables du projet. Elle prévaut
sur les choix d’implémentation et les habitudes de travail. Une modification
exige une décision explicite, documentée et revue.

## Mission

Permettre à chacun de tirer le meilleur parti de son énergie, simplement,
intelligemment et durablement.

## 1. Le dépôt est la mémoire officielle

Une décision validée ne reste jamais uniquement dans une conversation. Elle
est inscrite dans le dépôt avant son implémentation, dans le document adapté :
architecture, ADR, Handbook ou Constitution.

Les conversations servent à explorer et décider. La documentation explique
pourquoi, le code réalise comment, et les tests démontrent l’application.

## 2. La sécurité prévaut

JustInWatt reste prudent face à une mesure inconnue, périmée ou incohérente.
Une absence de preuve ne devient jamais une autorisation. Le pilotage physique
reste verrouillé tant que les validations électriques, matérielles et
fonctionnelles nécessaires ne sont pas réunies.

Les recommandations des fabricants et les limites de l’installation doivent
être respectées. Une charge de véhicule électrique ne doit pas être coupée par
un organe de puissance sans validation explicite de cette méthode.

## 3. Observer avant de décider, décider avant d’agir

Toute intégration progresse par étapes distinctes : observation en lecture
seule, validation des mesures, simulation des décisions, puis seulement essais
de commande encadrés. Le passage d’une étape à la suivante exige des preuves
traçables.

## 4. Les faits restent distingués des hypothèses

JustInWatt distingue les données confirmées, les résultats simulés, les
estimations et les éléments encore en attente. Une compatibilité ou une mesure
n’est déclarée validée que dans son périmètre réellement testé.

## 5. Les décisions doivent survivre aux conversations

Un nouveau développeur doit pouvoir comprendre l’état du projet, ses choix et
ses limites à partir du dépôt seul. À chaque fin de session, les décisions
importantes sont confrontées à la documentation afin de repérer tout oubli.

## 6. La simplicité utile est recherchée

La documentation et le code répondent à un besoin réel du projet. Les outils,
processus et abstractions sans bénéfice concret sont évités. La gouvernance ne
doit pas devenir une fin en soi.

Avant de retenir une évolution, JustInWatt pose son serment de décision :
« Cette décision rend-elle la maison plus intelligente sans rendre la vie de
l’utilisateur plus compliquée ? » Une réponse négative impose de revoir la
solution ou de ne pas la retenir. La simplicité d’usage ne masque toutefois
jamais une alerte, un consentement ou une exigence de sécurité.

## 7. L’architecture protège le long terme

Chaque évolution est examinée au regard de la cohérence globale du projet, de
sa robustesse, de sa maintenabilité et de son évolution sur plusieurs années.
Une solution rapide est refusée lorsqu’elle crée une dette durable ou contourne
une décision existante.

JustInWatt privilégie les protocoles ouverts, les interfaces officielles et le
fonctionnement local avant une dépendance au cloud lorsque cela est possible,
tout en isolant les particularités des fabricants. Les choix doivent faciliter
l’ajout de nouveaux matériels, les mises à jour et une expérience utilisateur
compréhensible.

Une demande en conflit avec la Constitution ou une décision acceptée est
suspendue le temps d’expliquer le conflit et de proposer une solution cohérente.
Une décision existante peut évoluer, mais uniquement de manière explicite et
traçable.

## 8. Les décisions sont challengées avec discernement

Une proposition est évaluée selon ses avantages, ses inconvénients, ses
risques, ses alternatives et ses effets futurs. L’esprit critique sert à
améliorer JustInWatt, sans ajouter de complexité théorique ni retarder une
correction sûre et évidente.

## 9. Les équipements et l’utilisateur sont protégés

Les décisions prennent en compte la durée de vie des équipements, pas seulement
leur fonctionnement immédiat. Les limites, incertitudes et modes dégradés sont
expliqués à l’utilisateur ; une automatisation ne doit pas masquer son origine
ni les raisons de son action.

Les changements importants prévoient une méthode de retour arrière réaliste.
Une dépendance propriétaire ou distante n’est acceptée que lorsque sa valeur,
ses limites et sa stratégie de remplacement sont explicites.

## 10. L’utilisateur reste maître

JustInWatt recherche un équilibre entre confort, intentions de l’utilisateur,
coût de l’électricité, production disponible, économies et durée de vie des
équipements. L’intérêt de l’utilisateur ne se réduit pas au coût minimal.

Chaque automatisation importante doit être compréhensible, explicable et
désactivable. JustInWatt peut assister et recommander, mais ne retire jamais à
l’utilisateur la décision finale.

Lorsqu’une information fiable peut améliorer concrètement le confort, les
économies, la sécurité, la fiabilité ou la durée de vie des équipements,
JustInWatt la rend utile à l’utilisateur. Cette assistance reste proportionnée,
évite le bruit de notification et demeure dans le périmètre énergétique et
domestique du projet.

Lorsqu’un équipement dispose déjà d’une intelligence sûre et documentée,
JustInWatt la coordonne plutôt que de la remplacer ou de contourner ses
protections.

## 11. L’Energy Brain arbitre pour toute la maison

L’Energy Brain porte l’intelligence décisionnelle globale de JustInWatt. Il
évalue le bénéfice à long terme en conciliant économie, écologie, confort,
intentions, usure et confiance. La sécurité et les contraintes fabricants ne
sont jamais compensées par un gain économique.

Les plugins ne prennent aucune décision énergétique globale. Ils exposent des
capacités, contraintes et états confirmés, puis exécutent les ordres autorisés.
Les équipements conservent leur intelligence spécialisée et leurs protections.

Le modèle du cœur repose sur des capacités cumulables plutôt que sur des types
exclusifs d’équipements.

## 12. La qualité est démontrée dans le temps

Les tests sont une composante permanente de l’architecture. Tout bug corrigé
devient, lorsque c’est techniquement possible, une preuve automatisée empêchant
sa réapparition. Aucun contrôle déclaré obligatoire ne peut être ignoré pour
publier une version.

JustInWatt vérifie non seulement que son code fonctionne, mais aussi que les
décisions de l’Energy Brain restent sûres, explicables et volontairement
modifiées. Les simulations et scénarios automatisés complètent les validations
matérielles ; ils ne les remplacent jamais et n’autorisent aucun pilotage réel.
