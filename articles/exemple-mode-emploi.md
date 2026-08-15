---
titre: Mode d'emploi — comment écrire un article
description: Ce fichier n'est pas publié. Il sert de modèle : copie-le, renomme-le, et mets publie sur true.
date: 2026-08-15
publie: false
image: assets/img/atelier-saileau.jpg
produits: cale-rake-wing-foil-boitier-us, cle-serrage-vis-gopro
---

## Comment ça marche

Tout ce qui est entre les deux lignes de tirets, tout en haut, est l'en-tête de l'article. Chaque ligne suit la forme `champ: valeur`.

- **titre** : obligatoire. C'est le titre affiché et le titre de l'onglet Google. Vise 50 à 60 caractères, avec le mot-clé au début.
- **description** : obligatoire. Une phrase de 140 à 155 caractères. C'est le texte gris affiché sous le titre dans Google, donc c'est lui qui donne envie de cliquer.
- **date** : obligatoire, au format année-mois-jour. Elle sert au classement, du plus récent au plus ancien.
- **publie** : mets `false` tant que l'article n'est pas prêt. Il reste dans le dépôt sans jamais apparaître en ligne.
- **image** : facultatif. Le chemin d'une image déjà présente dans `assets/img/`.
- **produits** : facultatif. Les slugs des fiches concernées, séparés par des virgules. Elles s'affichent en bas de l'article.
- **slug** : facultatif. Par défaut, c'est le nom du fichier sans le `.md`. C'est ce qui apparaît dans l'adresse.

## La mise en forme

Une ligne vide sépare deux paragraphes. Pour un sous-titre, deux dièses suivis d'un espace. Pour un sous-sous-titre, trois dièses.

Pour mettre un mot **en gras**, entoure-le de deux étoiles. Pour de l'*italique*, une seule.

Une liste à puces :

- première ligne
- deuxième ligne

Une liste numérotée :

1. première étape
2. deuxième étape

Un lien vers une page du site s'écrit avec le chemin interne : [voir les cales de rake](produits/cale-rake-wing-foil-boitier-us/). Un lien externe s'écrit en entier : [Yacht Club de Toulon](https://www.yctoulon.fr).

> Une citation ou une remarque mise en avant commence par un chevron.

## Trois conseils pour être trouvé sur Google

Écris pour répondre à **une question précise** que quelqu'un taperait vraiment. « Quel angle de rake choisir en wing foil » vaut mieux que « Nos conseils réglages ».

Vise **800 à 1500 mots**. En dessous de 500, Google considère rarement l'article comme une réponse sérieuse.

Place **un lien vers la fiche produit** correspondante dans le corps du texte, pas seulement en bas de page. C'est ce qui transforme un lecteur en client, et c'est aussi ce qui renforce la fiche produit aux yeux de Google.
