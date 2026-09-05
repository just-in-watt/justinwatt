# Provenance des actifs publics

## Objectif

Un instantané open source ne doit inclure aucun logo, pictogramme, image ou
police dont l'origine et la licence sont inconnues. L'absence de fichier
binaire ne suffit pas : un SVG copié depuis une bibliothèque tierce reste un
actif à attribuer.

## Décision

Les actifs graphiques et typographiques suivis par Git sont recensés dans
`public-assets.json`. Chaque entrée indique au minimum :

- le chemin exact dans le dépôt ;
- l'empreinte SHA-256 du contenu revu ;
- son origine vérifiable ;
- sa licence ;
- la date de la revue.

L'audit de publication échoue si un actif public n'est pas recensé, si son
empreinte change sans nouvelle revue, si une entrée désigne un fichier absent
ou si l'origine ou la licence reste indéterminée. Les formats contrôlés sont
SVG, PNG, JPEG, WebP, GIF, ICO, WOFF, WOFF2, TTF et OTF.

## Actif initial

Le seul fichier autonome trouvé dans l'arbre est
`interface_web/voiture.svg`. Son historique Git prouve son ajout le 15 août
2026, mais ne démontre pas sa source de création. Une recherche de ses tracés
exacts n'a retrouvé aucune bibliothèque publique correspondante ; cette
absence de résultat ne constitue pas une preuve de titularité.

Le pictogramme est donc redessiné dans le même changement à partir de primitives
SVG simples, sans reprendre une bibliothèque d'icônes ou un actif externe. Le
nouveau fichier porte une mention SPDX `Apache-2.0` et entre dans la licence du
code et de la documentation originale du projet. La confirmation globale du
titulaire de cette licence demeure une porte séparée de publication.

Le mot-symbole JustInWatt et la boussole visibles dans l'interface sont produits
par le HTML et le CSS du dépôt. Aucune police, photographie ou autre image
autonome n'est actuellement embarquée.

## Évolution et retour arrière

Tout nouvel actif est ajouté au manifeste après vérification de sa source, de
sa licence et des obligations d'attribution. Une modification volontaire d'un
actif met à jour son empreinte et sa revue dans le même commit.

Le retour arrière consiste à restaurer ensemble l'actif, le manifeste et la
version de l'audit correspondants. Retirer seulement le contrôle automatique
rouvrirait silencieusement la porte de provenance et n'est pas un retour arrière
acceptable pour un instantané public.

✅ Transfert recommandé
