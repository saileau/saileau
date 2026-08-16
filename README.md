# Site Saileau — version multi-pages

Site vitrine statique hébergé sur GitHub Pages. Une page par produit, une page par
rubrique, pages légales complètes, sitemap et données structurées.

---

## 1. Avant la première mise en ligne — il reste 2 champs

Identité, adresse et SIRET  sont déjà renseignés dans `config.json`.
Il reste deux champs entre crochets, qui s'affichent en **surbrillance dorée**
sur le site tant qu'ils ne sont pas remplis :

| Champ | Où le trouver |
|---|---|
| `ape` | Ton code APE / NAF (5 caractères). Sur ton avis de situation INSEE : avis-situation-sirene.insee.fr, en tapant ton SIRET. |
| `mediateur` | Nom + adresse + site du médiateur de la consommation auquel tu adhères. Obligatoire dès qu'une vente est conclue avec un particulier (art. L.616-1 code conso), quel que soit le canal. Liste des médiateurs agréés : economie.gouv.fr → médiation de la consommation. |

Après modification, relance `python3 build.py` : les pages légales sont régénérées.

---

## 2. Structure du dépôt

```
/
├── index.html                  ← généré
├── produits/
│   ├── index.html              ← catalogue, généré
│   └── <slug>/index.html       ← 1 page par produit, générées
├── a-propos/ commander/
├── mentions-legales/ cgv/ confidentialite/
├── 404.html  sitemap.xml  robots.txt  .nojekyll
├── assets/
│   ├── css/style.css
│   ├── js/site.js
│   └── img/produits/*.jpg      ← photos extraites (plus de base64)
├── produits.json               ← LA SOURCE DES PRODUITS
├── config.json                 ← identité, liens, mentions légales
└── build.py                    ← le générateur
```

**Ne modifie jamais les fichiers `index.html` à la main** : ils sont écrasés à chaque
build. Tout se passe dans `produits.json`, `config.json`, `style.css` et `build.py`.

---

## 3. Ajouter ou modifier un produit

1. Dépose les photos dans `assets/img/produits/` (format JPG, 1400 px max, ~150 Ko).
2. Ajoute un bloc dans `produits.json` :

```json
{
 "id": 12,
 "slug": "nom-du-produit-en-minuscules-avec-tirets",
 "nom": "Nom affiché du produit",
 "titre_seo": "Titre de l'onglet Google — 60 caractères max, avec le mot-clé",
 "court": "Résumé d'une ligne, sert aussi de description Google.",
 "desc": ["Premier paragraphe.", "Deuxième paragraphe."],
 "specs": [["Matière", "PETG"], ["Poids", "12 g"]],
 "prix": 15, "unite": "unité", "cat": "impression3d", "dispo": true, "variants": null,
 "imgs": [{"src": "assets/img/produits/mon-produit-1.jpg", "w": 1400, "h": 1400}]
}
```

3. Lance `python3 build.py`, puis commit + push.

`cat` vaut `impression3d` ou `accastillage`. Pour un produit à variantes, voir la
rondelle de transition dans `produits.json` (`imgs` devient un objet indexé `"0"`, `"1"`…).

---

## 4. Mise en ligne

### Option A — la plus simple (aucun outil à installer)

Tout est déjà généré dans le dépôt. Dans **Settings → Pages**, laisse
« Deploy from a branch » → branche `main`, dossier `/ (root)`. Chaque push met le
site à jour. Il faut juste penser à lancer `build.py` avant de pousser.

### Option B — automatique (recommandée à terme)

Le fichier `.github/workflows/deploy.yml` est fourni. Dans **Settings → Pages**,
choisis « **GitHub Actions** » comme source. À partir de là, tu peux éditer
`produits.json` **directement depuis le site github.com**, valider, et le site se
régénère et se publie tout seul en une minute. Aucun outil sur ton PC.

---

## 5. Après la mise en ligne

1. **Search Console** → propriété `https://saileau.github.io/saileau/` → Sitemaps →
   soumettre `sitemap.xml`.
2. Inspecter l'URL de 2-3 fiches produit et demander l'indexation.
3. Vérifier les données structurées : search.google.com/test/rich-results
4. Vérifier la vitesse : pagespeed.web.dev

---

## 6. Points restés en suspens

- **Logo** : intégré (`assets/img/logo-saileau.png`) dans la barre de navigation,
  la page d'accueil et le pied de page. Favicons générés depuis le logo rond
  (`favicon.ico`, `favicon.png`, `apple-touch-icon.png`, `icon-512.png`).
- **Image de partage** `assets/img/og-saileau.jpg` (1200 × 630) : générée à partir
  du logo et d'une photo produit. Remplaçable par un visuel photo si tu en fais un.
- **Version anglaise** : l'ancien bouton FR/EN traduisait via JavaScript, ce qui
  n'apporte rien au référencement (Google n'indexe que la version FR). La bonne
  approche est un dossier `/en/` avec des pages statiques et des balises `hreflang`.
- **Google Fonts** : les polices sont chargées depuis les serveurs Google, ce qui
  transmet l'IP des visiteurs (mentionné dans la politique de confidentialité).
  Pour supprimer ce point : télécharger les `.woff2` dans `assets/fonts/` et
  remplacer le `<link>` par une règle `@font-face`.

---

## 7. Favicon dans les résultats Google

Google n'utilise **qu'un seul favicon par nom d'hôte**. Les sous-dossiers ne peuvent pas
avoir le leur : `saileau.github.io/saileau/` partage donc le favicon de
`saileau.github.io`. Si aucun dépôt `saileau.github.io` n'existe, la racine renvoie une
erreur, Google ne trouve pas d'icône et affiche un globe gris à côté du résultat.

Trois façons de régler ça, de la plus simple à la meilleure :

1. **Renommer le dépôt en `saileau.github.io`** (Settings → Repository name). Le site
   passe à la racine du domaine. Il faut alors changer dans `config.json` :
   `"site_url": "https://saileau.github.io"` et `"base_path": "/"`, puis relancer
   `build.py`. Les URL raccourcissent au passage. À faire tant que le site est peu indexé.
2. **Créer un second dépôt `saileau.github.io`** contenant seulement un `favicon.ico`
   et une page `index.html` qui redirige vers `/saileau/`. Solution de rattrapage.
3. **Acheter un nom de domaine** (saileau.fr, ~8 €/an) et le pointer sur GitHub Pages
   via Settings → Pages → Custom domain. Meilleure option pour l'image de marque et
   le référencement à long terme.

Dans tous les cas, Google met **plusieurs jours à plusieurs semaines** à mettre à jour
le favicon des résultats, et le rafraîchit lors de l'exploration de la page d'accueil :
demander l'indexation de l'accueil dans Search Console accélère les choses.

---

## 8. Écrire un article (page « Conseils & actualités »)

Les articles sont des fichiers Markdown dans le dossier `articles/`. Un fichier = un
article = une page `/actualites/<nom-du-fichier>/`, avec son titre, sa description,
son fil d'Ariane et ses données structurées BlogPosting.

`articles/exemple-mode-emploi.md` contient le modèle complet et la syntaxe. Il est en
`publie: false`, donc jamais mis en ligne : copie-le plutôt que de l'écraser.

### Publier sans rien réuploader

Une fois le workflow GitHub Actions activé (Settings → Pages → Source : **GitHub
Actions**), la procédure complète tient dans le navigateur, même depuis un téléphone :

1. Sur github.com, ouvre le dossier `articles/`
2. « Add file » → « Create new file », nomme-le `mon-sujet.md`
3. Colle l'en-tête et écris le texte
4. « Commit changes »

Une minute plus tard, l'article est en ligne, il apparaît dans la liste, dans le menu,
et le `sitemap.xml` est régénéré automatiquement. Pour corriger une faute : ouvre le
fichier, clique sur le crayon, corrige, valide.

Tant que le workflow n'est pas activé, il faut lancer `build.py` puis pousser les
fichiers générés, comme pour les produits.

### Ce qui rend un article utile pour le référencement

- Un article = **une question précise** que quelqu'un tape vraiment dans Google
- 800 à 1500 mots ; en dessous de 500, l'effet est quasi nul
- Le mot-clé dans le titre, dans la description et dans le premier paragraphe
- Au moins un lien vers la fiche produit concernée **dans le corps du texte**
- Mieux vaut un bon article par mois que quatre articles bâclés
