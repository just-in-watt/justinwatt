# Contribuer à JustInWatt

Merci de contribuer à JustInWatt. Le projet coordonne des équipements
énergétiques réels : une modification apparemment anodine peut affecter la vie
privée, la sécurité ou la durée de vie d'un appareil.

## Avant de commencer

1. Lire `AGENTS.md`, `docs/DEVELOPER_GUIDE.md`, `docs/CONSTITUTION.md` et les
   références qu'ils imposent pour le domaine modifié.
2. Ouvrir une issue pour une nouvelle capacité ou une décision durable afin de
   vérifier son périmètre et ses risques.
3. Travailler sur une branche dédiée et garder chaque contribution ciblée.
4. Documenter une décision validée avant son implémentation.

## Données et équipements interdits dans une contribution

Ne joignez jamais de secret, jeton, cookie, credential, coordonnée, adresse
domestique, MAC réelle, numéro de série, nom de tailnet, chemin nominatif,
capture personnelle ou journal brut. Utilisez les plages RFC 5737 et des données
fictives explicites dans les exemples et les tests.

Une pull request ne doit pas appeler une installation réelle, déclencher une
commande physique, contourner une protection constructeur ou augmenter un
niveau d'autonomie. Les tests doivent employer des doubles, simulateurs ou
traces assainies. Une qualification matérielle reste une procédure privée,
supervisée et séparée.

## Qualité attendue

- conserver les frontières `observer → comprendre → décider → expliquer →
  agir` ;
- représenter les capacités par contrat plutôt que par marque ;
- fermer prudemment en cas de donnée absente, périmée ou ambiguë ;
- ajouter les tests proportionnés au risque et exécuter la suite complète ;
- mettre à jour la documentation, la couverture fonctionnelle et le changelog
  lorsque leur contrat change ;
- déclarer la provenance et la licence de toute dépendance ou de tout actif.

Commandes de vérification courantes :

```bash
python3 -m modules.audit_publication
python3 -m modules.audit_securite
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

## Pull request

Décrivez le problème, la décision, les risques, le retour arrière, les fichiers
touchés et les tests réellement exécutés. Une CI verte ne remplace pas la revue
humaine. Les mainteneurs peuvent demander une preuve supplémentaire ou refuser
un changement qui élargit implicitement les autorisations.

En soumettant une contribution destinée à être incluse, vous acceptez qu'elle
soit fournie sous la licence Apache-2.0 du projet, sauf mention écrite explicite
contraire avant sa soumission.
