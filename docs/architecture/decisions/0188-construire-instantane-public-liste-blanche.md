# ADR 0188 — Construire l'instantané public depuis une liste blanche exacte

- Statut : Accepté
- Date : 2026-09-05

## Contexte

L'ADR 0178 sépare le futur dépôt public du dépôt privé et de son historique.
Les audits automatiques du dépôt courant détectent les principaux secrets et
identifiants techniques, mais la revue humaine du 5 septembre 2026 a montré
qu'un export intégral conserverait des informations opérationnelles trop
précises sur l'installation de référence.

Une liste noire serait fragile : tout nouveau fichier entrerait dans le futur
instantané jusqu'à ce qu'une personne pense à l'exclure. La sélection publique
doit donc être indépendante de l'arborescence privée et échouer fermée.

## Décision

Un manifeste JSON versionné énumère chaque chemin public exact. Les motifs,
jokers et inclusions récursives sont interdits. Un fichier nouvellement ajouté
au dépôt privé reste ainsi absent de l'instantané tant qu'une revue humaine ne
l'ajoute pas au manifeste.

Le manifeste possède deux états :

- `draft` permet de préparer et contrôler la sélection, sans produire un
  instantané qualifié ;
- `qualified` autorise seulement la construction locale après enregistrement
  de la date et de la référence de revue humaine.

Le constructeur :

1. refuse tout manifeste invalide, chemin absolu, traversal, doublon, fichier
   absent, non suivi ou symbolique ;
2. refuse de construire depuis un manifeste `draft` ;
3. audite uniquement les contenus sélectionnés et vérifie séparément les
   actifs inclus contre le manifeste de provenance du dépôt privé ;
4. vérifie statiquement que les imports Python internes résolus dans le dépôt
   appartiennent eux aussi à la sélection ;
5. copie les fichiers dans une destination nouvelle, sans `.git`, sans
   historique et sans écraser un résultat existant ;
6. produit dans la destination un inventaire déterministe des chemins inclus,
   de leur empreinte et du nombre de fichiers privés exclus ;
7. vérifie à nouveau le contenu et les liens Markdown de la destination, puis
   refuse la copie si la sélection source a changé pendant l'opération.

Le manifeste initial reste `draft`. Son contenu exact, le document d'accueil
public et tout passage à `qualified` exigent une revue séparée. La construction
locale ne crée aucun dépôt distant et ne vaut jamais autorisation de publier.

## Alternatives écartées

- Une liste noire : un nouveau fichier privé pourrait être publié par défaut.
- Des jokers sur `modules/`, `tests/` ou `docs/` : un ajout futur hériterait
  silencieusement du statut public de son dossier.
- Supprimer ou appauvrir les preuves du dépôt privé : cela détruirait sa mémoire
  de qualification sans améliorer la séparation des responsabilités.
- Maintenir manuellement un second arbre public : la dérive entre les deux
  arbres serait difficile à détecter et à reproduire.

## Conséquences et retour arrière

La liste exacte est plus longue et demande une revue à chaque ajout public.
Ce coût est volontaire : il rend visible la décision de publier un fichier. Le
constructeur reste hors ligne, déterministe et sans effet sur le dépôt source.

Le retour arrière consiste à retirer le constructeur et son manifeste. Aucun
fichier privé n'est modifié et aucun historique public n'est créé par cette
fonction.

## Impacts

- **Architecture** : séparation reproductible entre mémoire privée et cœur
  public ; aucun changement du moteur énergétique ou des plugins.
- **Sécurité et vie privée** : ajout fail-closed, refus des liens symboliques,
  de l'écrasement et des sélections ambiguës.
- **Commandes physiques** : aucune ; le constructeur ne connaît aucun
  adaptateur d'équipement et n'effectue aucun accès réseau.
- **Tests** : validation du manifeste, refus du brouillon, audit de contenu,
  contrôle des actifs, fermeture des imports Python, liens Markdown et copie
  déterministe.
- **Documentation** : procédure de publication et revue humaine alignées sur le
  manifeste versionné.
