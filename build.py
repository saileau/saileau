#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Saileau — générateur de site statique multi-pages.

USAGE :  python3 build.py
Lit produits.json + config.json, écrit toutes les pages HTML,
le sitemap.xml et le robots.txt à la racine du dépôt.

Pour ajouter un produit : ajoute un bloc dans produits.json,
dépose ses photos dans assets/img/produits/, relance le script.
"""

import json, os, re, datetime, html, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(ROOT, 'config.json'), encoding='utf-8'))
PRODUITS = json.load(open(os.path.join(ROOT, 'produits.json'), encoding='utf-8'))

SITE = CFG['site_url'].rstrip('/')          # https://saileau.github.io/saileau
BASE = CFG['base_path']                     # /saileau/
TODAY = datetime.date.today().isoformat()
PAGES = []                                  # pour le sitemap : (url, priorité, changefreq)


def u(p=''):
    """URL absolue interne (pour href/src)."""
    return BASE + p.lstrip('/')


def full(p=''):
    return SITE + '/' + p.lstrip('/')


def e(t):
    return html.escape(str(t), quote=True)


def eur(v):
    return ('%.2f' % v).replace('.', ',').rstrip('0').rstrip(',') + ' €' if v else 'Sur devis'


def todo(txt):
    return '<span class="todo">[À COMPLÉTER : %s]</span>' % txt


V = CFG['identite']
# Tout champ de config resté entre crochets est affiché en surbrillance dorée
for _k, _v in list(V.items()):
    if isinstance(_v, str) and '[' in _v and ']' in _v:
        V[_k] = '<span class="todo">' + _v + '</span>'


# ---------------------------------------------------------------- head / nav / footer

def head(title, desc, path, og_img=None, ld=None, robots='index, follow'):
    canon = full(path)
    img = og_img or u('assets/img/og-saileau.jpg')
    og_abs = img if img.startswith('http') else SITE.rsplit(BASE.rstrip('/'), 1)[0] + img if BASE != '/' else SITE + img
    ldjson = ''
    if ld:
        ldjson = '\n<script type="application/ld+json">%s</script>' % json.dumps(
            ld, ensure_ascii=False, indent=1)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<meta name="author" content="Saileau — Toulon, France">
<link rel="canonical" href="{canon}">
<meta name="google-site-verification" content="{CFG['google_verification']}">
<meta property="og:type" content="{'product' if path.startswith('produits/') and path != 'produits/' else 'website'}">
<meta property="og:site_name" content="Saileau">
<meta property="og:url" content="{canon}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{og_abs}">
<meta property="og:locale" content="fr_FR">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{og_abs}">
<link rel="icon" href="{u('assets/img/favicon.ico')}" sizes="any">
<link rel="icon" href="{u('assets/img/favicon-144.png')}" type="image/png" sizes="144x144">
<link rel="icon" href="{u('assets/img/favicon-96.png')}" type="image/png" sizes="96x96">
<link rel="icon" href="{u('assets/img/favicon-48.png')}" type="image/png" sizes="48x48">
<link rel="apple-touch-icon" href="{u('assets/img/apple-touch-icon.png')}">
<meta name="theme-color" content="#07111F">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{u('assets/css/style.css')}">{ldjson}
</head>
<body>
<a class="skip-link" href="#main">Aller au contenu principal</a>
"""


NAV = f"""<nav>
  <a href="{u('')}" class="nav-logo" aria-label="Saileau — accueil">
    <img class="nav-logo-img" src="{u('assets/img/logo-saileau.png')}" alt="Saileau" width="106" height="32" style="display:block">
  </a>
  <ul class="nav-links" id="navLinks">
    <li><a href="{u('')}" onclick="closeMenu()">Accueil</a></li>
    <li><a href="{u('produits/')}" onclick="closeMenu()">Produits</a></li>
    <li><a href="{u('actualites/')}" onclick="closeMenu()">Conseils</a></li>
    <li><a href="{u('a-propos/')}" onclick="closeMenu()">À propos</a></li>
    <li><a href="{u('commander/')}" onclick="closeMenu()">Commander</a></li>
  </ul>
  <div class="nav-right">
    <button class="cart-btn" onclick="toggleCart()" aria-label="Ouvrir le panier">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 001.99 1.61h9.72a2 2 0 001.98-1.68L23 6H6"></path></svg>
      <span>Panier</span><span class="cart-count" id="cartCount">0</span>
    </button>
    <button class="hamburger" onclick="toggleMenu()" aria-label="Menu"><span></span><span></span><span></span></button>
  </div>
</nav>
"""

FOOTER = f"""<footer>
  <div>
    <img class="footer-logo-img" src="{u('assets/img/logo-saileau.png')}" alt="Saileau" width="146" height="44" style="display:block;margin:0 auto .6rem">
    <div class="footer-tagline">Conception et fabrication de pièces nautiques sur mesure · Toulon, Var</div>
  </div>
  <div class="footer-social">
    <a class="social-btn" href="{CFG['instagram']}" target="_blank" rel="noopener" aria-label="Instagram Saileau">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="2" y="2" width="20" height="20" rx="5"></rect><circle cx="12" cy="12" r="4"></circle><circle cx="17.5" cy="6.5" r=".5" fill="currentColor" stroke="none"></circle></svg>
    </a>
    <a class="social-btn" href="{CFG['vinted']}" target="_blank" rel="noopener" aria-label="Boutique Vinted Saileau">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"></path><line x1="3" y1="6" x2="21" y2="6"></line><path d="M16 10a4 4 0 01-8 0"></path></svg>
    </a>
  </div>
  <div class="footer-links">
    <a href="{u('produits/')}">Produits</a>
    <a href="{u('actualites/')}">Conseils</a>
    <a href="{u('a-propos/')}">À propos</a>
    <a href="{u('commander/')}">Commander</a>
    <a href="{u('mentions-legales/')}">Mentions légales</a>
    <a href="{u('cgv/')}">CGV</a>
    <a href="{u('confidentialite/')}">Données personnelles</a>
    <a href="{CFG['vinted']}" target="_blank" rel="noopener">Vinted</a>
  </div>
  <p class="footer-copy">© {datetime.date.today().year} Saileau — Tous droits réservés · TVA non applicable, art. 293 B du CGI</p>
</footer>
"""

CART = f"""<div class="cart-overlay" id="cartOverlay" onclick="toggleCart()"></div>
<aside class="cart-sidebar" id="cartSidebar" aria-label="Panier">
  <div class="cart-header"><h3>Mon panier</h3><button class="cart-close" onclick="toggleCart()" aria-label="Fermer">×</button></div>
  <div class="cart-body" id="cartBody"></div>
  <div class="cart-footer" id="cartFooter" style="display:none">
    <div class="cart-total"><span>Total</span><span class="cart-total-amount" id="cartTotalAmount">0,00 €</span></div>
    <label class="cgv-check"><input type="checkbox" id="cgvCheck">
      <span>J'ai lu et j'accepte les <a href="{u('cgv/')}" target="_blank">conditions générales de vente</a> et la <a href="{u('confidentialite/')}" target="_blank">politique de confidentialité</a>.</span></label>
    <button class="cart-checkout-wa" onclick="checkoutWa()">Envoyer ma commande via WhatsApp</button>
    <button class="cart-checkout-mail" onclick="checkoutMail()">Envoyer ma commande par email</button>
    <p class="cart-note">Le panier n'est pas un paiement : votre demande est envoyée par message, je confirme la disponibilité et le prix avant tout règlement.</p>
  </div>
</aside>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
"""

FOOT_JS = f"""<script>window.SAILEAU_BASE='{BASE}';</script>
<script src="{u('assets/js/site.js')}" defer></script>
</body>
</html>
"""


def crumb(items):
    out = ['<nav class="breadcrumb" aria-label="Fil d\'Ariane">']
    parts = []
    for i, (label, href) in enumerate(items):
        parts.append('<a href="%s">%s</a>' % (u(href), e(label)) if href is not None else '<span>%s</span>' % e(label))
    out.append('<span>›</span>'.join(parts))
    out.append('</nav>')
    return ''.join(out)


def crumb_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n,
                                 "item": full(h)} for i, (n, h) in enumerate(items)]}


def write(path, content, prio='0.6', freq='monthly', in_sitemap=True):
    dest = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, 'w', encoding='utf-8').write(content)
    if in_sitemap:
        url = path.replace('index.html', '')
        PAGES.append((full(url), prio, freq))
    print('  →', path)


# ---------------------------------------------------------------- cartes produit

def first_img(p):
    im = p['imgs']
    return (im['0'][0] if isinstance(im, dict) else im[0]) if im else None


def all_imgs(p):
    im = p['imgs']
    return [x for a in im.values() for x in a] if isinstance(im, dict) else im


def card(p):
    im = first_img(p)
    badge = 'badge-3d' if p['cat'] == 'impression3d' else 'badge-acca'
    lbl = 'Impression 3D' if p['cat'] == 'impression3d' else 'Accastillage'
    nb = len(all_imgs(p))
    return f"""<article class="product-card" data-cat="{p['cat']}">
  <a href="{u('produits/%s/' % p['slug'])}" style="display:block;color:inherit">
    <div class="product-img">
      <img src="{u(im['src'])}" alt="{e(p['nom'])} — Saileau" loading="lazy" width="{im['w']}" height="{im['h']}">
      <span class="product-badge {badge}">{lbl}</span>
      {'<span class="product-img-count">%d photos</span>' % nb if nb > 1 else ''}
    </div>
    <div class="product-info">
      <h3 class="product-name">{e(p['nom'])}</h3>
      <p class="product-desc-short">{e(p['court'])}</p>
      <div class="product-footer">
        <div class="product-price">{eur(p['prix'])}{'<span class="unit">/ %s</span>' % e(p['unite']) if p['unite'] else ''}</div>
        <span class="add-cart" aria-hidden="true">Voir la fiche →</span>
      </div>
    </div>
  </a>
</article>"""


# ---------------------------------------------------------------- 1. ACCUEIL

def build_home():
    vedettes = [p for p in PRODUITS if p['id'] in CFG['produits_accueil']]
    ld = [{
        "@context": "https://schema.org", "@type": "Store",
        "@id": full('#store'),
        "name": "Saileau",
        "description": "Conception et fabrication de pièces nautiques sur mesure : accastillage et pièces imprimées en 3D pour la voile légère, le wingfoil et le catamaran.",
        "url": SITE + '/',
        "logo": full('assets/img/icon-512.png'),
        "image": full('assets/img/og-saileau.jpg'),
        "email": CFG['identite']['email'],
        "telephone": CFG['identite']['tel_intl'],
        "address": {"@type": "PostalAddress", "addressLocality": "Toulon",
                    "addressRegion": "Var", "postalCode": "83000", "addressCountry": "FR"},
        "areaServed": {"@type": "Country", "name": "France"},
        "priceRange": "€", "currenciesAccepted": "EUR",
        "paymentAccepted": "Virement, Wero, PayPal, Vinted",
        "sameAs": [CFG['vinted'], CFG['instagram']] + CFG.get('reseaux_sup', [])
    }, {
        "@context": "https://schema.org", "@type": "WebSite",
        "name": "Saileau", "url": SITE + '/',
        "inLanguage": "fr-FR"
    }]
    h = head("Saileau — Accastillage et pièces nautiques sur mesure à Toulon",
             "Pièces imprimées en 3D et petit accastillage pour la voile légère, le wingfoil et le catamaran. Conception CAO et fabrication à Toulon (Var). Expédition gratuite dès 25 €.",
             '', ld=ld)
    body = f"""{NAV}
<main id="main">
<section id="accueil">
  <div class="hero-bg"></div><div class="hero-grid"></div>
  <div class="hero-content">
    <div class="hero-badge"><span>Accastillage &amp; impression 3D · Toulon</span></div>
    <h1><img class="hero-logo-img" src="{u('assets/img/logo-saileau.png')}" alt="Saileau" width="420" height="127" style="display:block;margin:0 auto"><span class="sr-only">Saileau — accastillage et pièces nautiques sur mesure à Toulon</span></h1>
    <p class="hero-sub">Pièces sur mesure pour la voile légère, conçues, imprimées et expédiées depuis Toulon.</p>
    <div class="hero-ctas">
      <a href="{u('produits/')}" class="btn-primary"><span>Voir les produits</span></a>
      <a href="{u('a-propos/')}" class="btn-outline"><span>En savoir plus</span></a>
    </div>
  </div>
  <svg class="wave-divider" viewBox="0 0 1440 60" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" aria-hidden="true"><path d="M0 60V30C240 0 480 60 720 30C960 0 1200 60 1440 30V60H0Z" fill="#0E1E30"></path></svg>
</section>

<section id="produits">
  <div class="produits-header visible">
    <p class="section-label">Sélection</p>
    <h2>Nos <em>produits</em></h2>
    <p class="section-intro">Pièces imprimées en 3D à la commande et petit accastillage pour la voile légère, le wingfoil et le catamaran.</p>
  </div>
  <div class="products-grid">
    {''.join(card(p) for p in vedettes)}
  </div>
  <div style="text-align:center;margin-top:2.5rem">
    <a href="{u('produits/')}" class="btn-primary"><span>Voir tout le catalogue ({len(PRODUITS)} produits)</span></a>
  </div>
</section>

<section id="apropos" style="padding-top:4rem">
  <div class="apropos-inner">
    <div>
      <p class="section-label">L'atelier</p>
      <h2>Conçu et fabriqué <em>à Toulon</em></h2>
      <p class="section-intro">Saileau conçoit et fabrique des pièces nautiques sur mesure : conception CAO, choix du matériau adapté au milieu marin, fabrication en petite série et contrôle dimensionnel.</p>
      <div class="process-steps">
        <div class="step"><div class="step-num">1</div><div class="step-text"><h4>Conception CAO</h4><p>Chaque pièce est modélisée en 3D avec les contraintes marines : eau salée, UV, charge mécanique.</p></div></div>
        <div class="step"><div class="step-num">2</div><div class="step-text"><h4>Fabrication &amp; contrôle</h4><p>Matériau sélectionné selon l'application. Vérification dimensionnelle et géométrique systématique.</p></div></div>
        <div class="step"><div class="step-num">3</div><div class="step-text"><h4>Expédition</h4><p>Expédition gratuite en France métropolitaine dès 25 € de commande. Hors métropole : me contacter.</p></div></div>
      </div>
      <div class="location-tag"><div class="location-dot"></div><span>Yacht Club de Toulon — Var (83)</span></div>
      <p style="margin-top:1.5rem"><a href="{u('a-propos/')}" class="btn-outline"><span>En savoir plus sur l'atelier</span></a></p>
    </div>
    <div class="apropos-right">
      <div class="apropos-photo-card">
        <div class="apropos-photo-area">
          <img src="{u('assets/img/atelier-saileau.jpg')}" alt="Atelier Saileau à Toulon : impression 3D de pièces nautiques" loading="lazy" style="width:100%;height:100%;object-fit:cover">
        </div>
      </div>
    </div>
  </div>
</section>

<section id="carnet-bord" style="padding:0 5% 4rem;background:var(--navy)">
  <div style="max-width:1200px;margin:0 auto">
    <a href="{u('reglages.html')}" style="display:flex;align-items:center;justify-content:space-between;gap:2rem;background:var(--navy-2);border:1px solid var(--border);border-radius:var(--rl);padding:1.75rem 2rem">
      <div>
        <div style="font-family:var(--fh);font-size:22px;margin-bottom:.2rem">Carnet de bord <em style="color:var(--teal)">réglages</em></div>
        <div style="font-size:13px;color:var(--white-dim);max-width:480px">Enregistrez, comparez et partagez vos réglages de catamaran après chaque sortie. Accès communauté et référence VMG Nacra 15.</div>
      </div>
      <span style="color:var(--teal);font-size:13px;font-weight:500;white-space:nowrap">Accéder →</span>
    </a>
  </div>
</section>
</main>
{FOOTER}{CART}{FOOT_JS}"""
    write('index.html', h + body, prio='1.0', freq='weekly')


# ---------------------------------------------------------------- 2. CATALOGUE

def build_catalogue():
    items = [{"@type": "ListItem", "position": i + 1,
              "url": full('produits/%s/' % p['slug'])} for i, p in enumerate(PRODUITS)]
    ld = [crumb_ld([("Accueil", ""), ("Produits", "produits/")]),
          {"@context": "https://schema.org", "@type": "ItemList",
           "name": "Catalogue Saileau", "numberOfItems": len(PRODUITS),
           "itemListElement": items}]
    h = head("Catalogue — accastillage et pièces 3D pour la voile | Saileau",
             "Tout le catalogue Saileau : caches d'écrou de ridoire, cales de rake wing foil, poulies et anneaux de friction inox, pièces sur mesure. Fabriqué à Toulon, expédition gratuite dès 25 €.",
             'produits/', ld=ld)
    body = f"""{NAV}
<main id="main">
<div class="page-head">
  {crumb([("Accueil", ""), ("Produits", None)])}
  <p class="section-label">Catalogue</p>
  <h1>Nos <em>produits</em></h1>
  <p class="section-intro">Pièces imprimées en 3D à la commande et petit accastillage pour la voile légère, le wingfoil et le catamaran. Chaque fiche détaille la matière, les cotes et les compatibilités.</p>
  <div class="filters" style="margin-top:1.6rem">
    <button class="filter-btn active" aria-pressed="true" onclick="filterProducts('all',this)">Tout voir</button>
    <button class="filter-btn" aria-pressed="false" onclick="filterProducts('impression3d',this)">Impression 3D</button>
    <button class="filter-btn" aria-pressed="false" onclick="filterProducts('accastillage',this)">Accastillage</button>
  </div>
</div>
<section style="padding-top:1rem">
  <div class="products-grid">
    {''.join(card(p) for p in PRODUITS)}
  </div>
</section>
</main>
{FOOTER}{CART}{FOOT_JS}"""
    write('produits/index.html', h + body, prio='0.9', freq='weekly')


# ---------------------------------------------------------------- 3. FICHES PRODUIT

def build_produit(p):
    imgs = all_imgs(p)
    im0 = imgs[0]
    is_var = isinstance(p['imgs'], dict)
    gal = p['imgs']['0'] if is_var else p['imgs']
    lbl = 'Impression 3D' if p['cat'] == 'impression3d' else 'Accastillage'
    badge = 'badge-3d' if p['cat'] == 'impression3d' else 'badge-acca'

    offer = {
        "@type": "Offer",
        "price": "%.2f" % p['prix'],
        "priceCurrency": "EUR",
        "priceValidUntil": (datetime.date.today() + datetime.timedelta(days=365)).isoformat(),
        "availability": "https://schema.org/InStock" if p['dispo'] else "https://schema.org/OutOfStock",
        "itemCondition": "https://schema.org/NewCondition",
        "url": full('produits/%s/' % p['slug']),
        "seller": {"@type": "Organization", "name": "Saileau", "@id": full('#store')},
        "shippingDetails": {
            "@type": "OfferShippingDetails",
            "shippingRate": {"@type": "MonetaryAmount", "value": "0", "currency": "EUR"},
            "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "FR"},
            "deliveryTime": {"@type": "ShippingDeliveryTime",
                             "handlingTime": {"@type": "QuantitativeValue", "minValue": 1, "maxValue": 5, "unitCode": "DAY"},
                             "transitTime": {"@type": "QuantitativeValue", "minValue": 2, "maxValue": 5, "unitCode": "DAY"}}
        },
        "hasMerchantReturnPolicy": {
            "@type": "MerchantReturnPolicy", "applicableCountry": "FR",
            "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
            "merchantReturnDays": 14, "returnMethod": "https://schema.org/ReturnByMail",
            "returnFees": "https://schema.org/ReturnShippingFees"}
    }
    ld = [crumb_ld([("Accueil", ""), ("Produits", "produits/"), (p['nom'], 'produits/%s/' % p['slug'])]),
          {"@context": "https://schema.org", "@type": "Product",
           "name": p['nom'],
           "description": p['court'],
           "image": [full(x['src']) for x in imgs],
           "brand": {"@type": "Brand", "name": "Saileau"},
           "category": lbl,
           "material": next((s[1] for s in p['specs'] if s[0].lower().startswith('mati')), None),
           "offers": offer}]
    ld[1] = {k: v for k, v in ld[1].items() if v is not None}
    if p['prix'] == 0:
        ld[1].pop('offers')

    # galerie
    thumbs = ''.join(
        f'<button class="pp-thumb{" active" if i == 0 else ""}" onclick="ppSet({i})" aria-label="Photo {i+1}">'
        f'<img src="{u(im["src"])}" alt="" loading="lazy" width="{im["w"]}" height="{im["h"]}"></button>'
        for i, im in enumerate(gal))

    variant_html = ''
    if p['variants']:
        opts = ''.join('<option value="%d">%s</option>' % (i, e(v)) for i, v in enumerate(p['variants']))
        variant_html = ('<label for="ppVariant" style="font-size:13px;color:var(--white-dim)">Modèle</label>'
                        '<select class="pp-variant" id="ppVariant" onchange="ppVariantChange(this)" '
                        "data-imgs='%s'>%s</select>" % (json.dumps(p['imgs']), opts))

    specs = ''.join('<div class="spec-row"><span>%s</span><span>%s</span></div>' % (e(k), e(v))
                    for k, v in p['specs'])
    desc = ''.join('<p>%s</p>' % e(t) for t in p['desc'])

    btn = (f'<button class="modal-add-btn" onclick="addToCart(this)" data-id="{p["id"]}" '
           f'data-nom="{e(p["nom"])}" data-prix="{p["prix"]}" data-img="{im0["src"]}">'
           f'{"Demander un devis" if p["prix"] == 0 else "Ajouter au panier"}</button>')

    related = [x for x in PRODUITS if x['cat'] == p['cat'] and x['id'] != p['id']][:3]

    h = head(f"{p['titre_seo']} | Saileau",
             p['court'][:158],
             'produits/%s/' % p['slug'],
             og_img=u(im0['src']), ld=ld)
    body = f"""{NAV}
<main id="main">
<div class="page-head" style="padding-bottom:0">
  {crumb([("Accueil", ""), ("Produits", "produits/"), (p['nom'], None)])}
</div>
<div class="produit-page">
  <div class="pp-gallery">
    <div class="pp-main">
      <img id="ppMainImg" src="{u(gal[0]['src'])}" alt="{e(p['nom'])} — Saileau" width="{gal[0]['w']}" height="{gal[0]['h']}" fetchpriority="high">
      {'<div class="pp-nav"><button onclick="ppSlide(-1)" aria-label="Photo précédente">‹</button><button onclick="ppSlide(1)" aria-label="Photo suivante">›</button></div>' if len(gal) > 1 else ''}
    </div>
    <div class="pp-thumbs" id="ppThumbs">{thumbs}</div>
    <script type="application/json" id="ppGalleryData">{json.dumps(gal)}</script>
  </div>
  <div class="pp-info">
    <span class="pp-badge {badge}">{lbl}</span>
    <h1>{e(p['nom'])}</h1>
    <div class="pp-price"><strong>{eur(p['prix'])}</strong>{'<span>/ %s</span>' % e(p['unite']) if p['unite'] else ''}</div>
    <p class="pp-tva">Prix net — TVA non applicable, article 293 B du CGI. Expédition gratuite en France métropolitaine dès 25 € d'achat.</p>
    <div class="pp-desc">{desc}</div>
    <div class="pp-actions">
      {variant_html}
      {btn}
    </div>
    <div class="modal-specs"><h5>Caractéristiques</h5>{specs}</div>
    <div class="pp-reassure">
      <div><strong>Fabrication :</strong>&nbsp;à Toulon (Var), à la commande.</div>
      <div><strong>Délai :</strong>&nbsp;généralement 1 à 5 jours ouvrés avant expédition.</div>
      <div><strong>Rétractation :</strong>&nbsp;14 jours (hors pièces réalisées sur mesure) — voir <a href="{u('cgv/')}" style="color:var(--teal)">CGV</a>.</div>
      <div><strong>Une question ?</strong>&nbsp;<a href="{u('commander/')}" style="color:var(--teal)">Me contacter</a></div>
    </div>
  </div>
</div>
<section class="related">
  <h2>Dans la même catégorie</h2>
  <div class="products-grid">{''.join(card(x) for x in related)}</div>
</section>
</main>
{FOOTER}{CART}{FOOT_JS}"""
    write('produits/%s/index.html' % p['slug'], h + body, prio='0.8', freq='monthly')


# ---------------------------------------------------------------- 4. À PROPOS

def build_apropos():
    ld = [crumb_ld([("Accueil", ""), ("À propos", "a-propos/")]),
          {"@context": "https://schema.org", "@type": "AboutPage",
           "name": "À propos de Saileau", "url": full('a-propos/')}]
    h = head("À propos — l'atelier Saileau à Toulon | Conception et fabrication nautique",
             "Saileau conçoit et fabrique des pièces nautiques sur mesure à Toulon : conception CAO, matériaux adaptés au milieu marin, petites séries et contrôle dimensionnel.",
             'a-propos/', ld=ld)
    chips = ''.join('<span class="chip%s">%s</span>' % (' hi' if i < 3 else '', e(c))
                    for i, c in enumerate(CFG['chips']))
    body = f"""{NAV}
<main id="main">
<div class="page-head">
  {crumb([("Accueil", ""), ("À propos", None)])}
  <p class="section-label">L'atelier</p>
  <h1>Conçu et fabriqué <em>à Toulon</em></h1>
  <p class="section-intro">Saileau est né sur l'eau : pratiquant la compétition en catamaran et en wing foil au Yacht Club de Toulon, j'ai commencé par fabriquer les pièces qui me manquaient à bord. Elles sont aujourd'hui proposées à d'autres coureurs.</p>
</div>
<section id="apropos" style="padding-top:1rem">
  <div class="apropos-inner">
    <div>
      <div class="process-steps">
        <div class="step"><div class="step-num">1</div><div class="step-text"><h4>Conception CAO</h4><p>Chaque pièce est modélisée en 3D en tenant compte des contraintes marines : eau salée, UV, charge mécanique, et des cotes réelles du support.</p></div></div>
        <div class="step"><div class="step-num">2</div><div class="step-text"><h4>Fabrication &amp; contrôle</h4><p>Matériau choisi selon l'application : TPU souple, PETG technique, ABS ou ASA pour la tenue aux UV. Vérification dimensionnelle et géométrique de chaque pièce avant envoi.</p></div></div>
        <div class="step"><div class="step-num">3</div><div class="step-text"><h4>Sur mesure</h4><p>Une pièce introuvable, cassée ou à adapter ? Envoyez vos cotes, un croquis ou une photo : je vous propose une solution et un devis gratuit.</p></div></div>
        <div class="step"><div class="step-num">4</div><div class="step-text"><h4>Expédition</h4><p>Expédition gratuite en France métropolitaine dès 25 € de commande. Hors métropole : me contacter ou passer par Vinted.</p></div></div>
      </div>
      <div class="location-tag"><div class="location-dot"></div><span>Yacht Club de Toulon — Var (83)</span></div>
      <p style="margin-top:1.6rem"><a href="{u('commander/')}" class="btn-primary"><span>Discuter d'un projet</span></a></p>
    </div>
    <div class="apropos-right">
      <div class="chips-block"><h5>Profil</h5><div class="chips">{chips}</div></div>
      <div class="apropos-photo-card">
        <div class="apropos-photo-area">
          <img src="{u('assets/img/atelier-saileau.jpg')}" alt="Atelier Saileau : impression 3D de pièces nautiques à Toulon" loading="lazy" style="width:100%;height:100%;object-fit:cover">
        </div>
      </div>
    </div>
  </div>
</section>
</main>
{FOOTER}{CART}{FOOT_JS}"""
    write('a-propos/index.html', h + body, prio='0.7')


# ---------------------------------------------------------------- 5. COMMANDER

def build_commander():
    ld = [crumb_ld([("Accueil", ""), ("Commander", "commander/")]),
          {"@context": "https://schema.org", "@type": "ContactPage",
           "name": "Commander chez Saileau", "url": full('commander/')}]
    h = head("Commander — Saileau | Accastillage sur mesure, Toulon",
             "Comment commander chez Saileau : ajout au panier, envoi de la commande par WhatsApp ou email, paiement sécurisé après confirmation, expédition gratuite dès 25 €.",
             'commander/', ld=ld)
    body = f"""{NAV}
<main id="main">
<div class="page-head">
  {crumb([("Accueil", ""), ("Commander", None)])}
  <p class="section-label">Commander</p>
  <h1>Simple et <em>rapide</em></h1>
  <p class="section-intro">Le site n'encaisse aucun paiement : il sert de vitrine et de portail. Vous composez votre panier, vous l'envoyez, je confirme la disponibilité et le prix avant tout règlement.</p>
</div>
<section id="commande" style="padding-top:1rem">
  <div class="commande-inner">
    <div>
      <div class="commande-step"><div class="step-icon">🛒</div><div class="step-info"><h4>1. Ajoutez au panier</h4><p>Ouvrez la fiche du produit pour voir les détails, choisir la variante s'il y en a une, puis ajoutez-le au panier.</p></div></div>
      <div class="commande-step"><div class="step-icon">📱</div><div class="step-info"><h4>2. Envoyez votre commande</h4><p>Via WhatsApp, par email, ou directement sur Vinted. Je confirme la disponibilité, le délai et le montant définitif.</p></div></div>
      <div class="commande-step"><div class="step-icon">💳</div><div class="step-info"><h4>3. Paiement</h4><p>Virement, Wero, PayPal ou paiement Vinted. Le lien ou les coordonnées de paiement sont envoyés à la confirmation — jamais avant.</p></div></div>
      <div class="commande-step"><div class="step-icon">📦</div><div class="step-info"><h4>4. Expédition</h4><p>Gratuite en France métropolitaine dès 25 €. En dessous, les frais réels sont indiqués avant paiement. Hors métropole : me contacter ou commander via Vinted.</p></div></div>
      <p style="margin-top:1.5rem;font-size:13px;color:var(--white-dim)">Les conditions détaillées (délais, rétractation, garanties) figurent dans les <a href="{u('cgv/')}" style="color:var(--teal)">conditions générales de vente</a>.</p>
    </div>
    <div class="contact-card">
      <h3>Me contacter</h3>
      <p>Pour toute question sur un produit, une commande ou un projet sur mesure.</p>
      <button class="btn-whatsapp" onclick="contactWa()">WhatsApp</button>
      <div class="contact-divider">ou</div>
      <a href="mailto:{CFG['identite']['email']}" class="btn-email">{CFG['identite']['email']}</a>
      <div class="contact-divider">ou directement sur</div>
      <a href="{CFG['vinted']}" target="_blank" rel="noopener" class="btn-vinted"><span>Ma boutique Vinted</span></a>
      <p class="contact-note">Expédition gratuite dès 25 € en France métropolitaine. Hors métropole : me contacter.</p>
    </div>
  </div>
</section>
</main>
{FOOTER}{CART}{FOOT_JS}"""
    write('commander/index.html', h + body, prio='0.8')


# ---------------------------------------------------------------- 6. PAGES LÉGALES

def legal_page(slug, title, desc, h1, inner, prio='0.3'):
    ld = [crumb_ld([("Accueil", ""), (h1, slug + '/')])]
    h = head(title, desc, slug + '/', ld=ld, robots='index, follow')
    body = f"""{NAV}
<main id="main">
<div class="page-head">
  {crumb([("Accueil", ""), (h1, None)])}
  <h1>{h1}</h1>
</div>
<div class="legal">
{inner}
<p class="legal-maj">Dernière mise à jour : {TODAY}</p>
</div>
</main>
{FOOTER}{CART}{FOOT_JS}"""
    write('%s/index.html' % slug, h + body, prio=prio, freq='yearly')


def build_mentions():
    inner = f"""
<p>Conformément à l'article 6 III de la loi n° 2004-575 du 21 juin 2004 pour la confiance dans l'économie numérique (LCEN), les informations suivantes sont portées à la connaissance des utilisateurs du site.</p>

<h2>1. Éditeur du site</h2>
<table>
<tr><th>Éditeur</th><td>{V['nom_legal']}, entrepreneur individuel exerçant sous le nom commercial « Saileau »</td></tr>
<tr><th>Adresse du siège</th><td>{V['adresse']}</td></tr>
<tr><th>Email</th><td><a href="mailto:{V['email']}">{V['email']}</a></td></tr>
<tr><th>Téléphone</th><td>{V['tel']}</td></tr>
<tr><th>SIRET</th><td>{V['siret']}</td></tr>
<tr><th>Code APE / NAF</th><td>{V['ape']}</td></tr>
<tr><th>Immatriculation</th><td>Registre National des Entreprises (RNE){V['rcs_extra']}</td></tr>
<tr><th>TVA</th><td>TVA non applicable — article 293 B du Code général des impôts. Les prix affichés sont des prix nets, sans TVA.</td></tr>
<tr><th>Directeur de la publication</th><td>{V['nom_legal']}</td></tr>
</table>

<h2>2. Hébergement</h2>
<p>Le site est hébergé par&nbsp;:</p>
<div class="legal-box">
<p><strong>GitHub, Inc.</strong> (service GitHub Pages)<br>
88 Colin P. Kelly Jr Street, San Francisco, CA 94107, États-Unis<br>
Site&nbsp;: <a href="https://github.com" target="_blank" rel="noopener">github.com</a></p>
</div>
<p>L'hébergeur assure le stockage et la mise à disposition des fichiers du site. Les transferts de données vers les États-Unis liés à cet hébergement sont décrits dans la <a href="{u('confidentialite/')}">politique de confidentialité</a>.</p>

<h2>3. Activité</h2>
<p>Saileau conçoit et fabrique des pièces nautiques sur mesure et en petite série (accastillage et pièces techniques), destinées à la voile légère, au wing foil et au catamaran. Le site est un site vitrine&nbsp;: <strong>aucun paiement n'y est encaissé</strong>. Le panier permet uniquement de préparer une demande de commande, transmise ensuite par messagerie ou par email. La vente peut également intervenir via la boutique Vinted de Saileau.</p>

<h2>4. Propriété intellectuelle</h2>
<p>L'ensemble des éléments du site (structure, textes, photographies, modèles 3D, logo, identité graphique) est la propriété de {V['nom_legal']}, sauf mention contraire, et est protégé par le Code de la propriété intellectuelle.</p>
<p>Toute reproduction, représentation, adaptation ou exploitation, totale ou partielle, par quelque procédé que ce soit, sans autorisation écrite préalable, est interdite et susceptible de constituer une contrefaçon au sens des articles L.335-2 et suivants du Code de la propriété intellectuelle.</p>
<p>Les marques et dénominations citées à titre de compatibilité (Harken, GoPro, WASZP, BirdyFish, Nacra, Magic Marine, etc.) appartiennent à leurs titulaires respectifs. Elles sont mentionnées à des fins strictement descriptives et informatives&nbsp;: les produits Saileau ne sont ni fabriqués, ni distribués, ni approuvés par ces marques.</p>
<p>Crédits photographiques&nbsp;: {V['credits_photos']}</p>

<h2>5. Responsabilité</h2>
<p>Les informations publiées sur le site sont fournies à titre indicatif et mises à jour régulièrement. {V['nom_legal']} ne saurait être tenu responsable des erreurs, omissions ou indisponibilités du site, ni des dommages résultant d'une utilisation non conforme des produits (notamment le dépassement des charges d'utilisation, un montage inadapté ou un usage détourné).</p>
<p>Les pièces proposées sont des pièces techniques&nbsp;: il appartient à l'acheteur de vérifier leur compatibilité et leur adéquation à son usage. En cas de doute, me contacter avant commande.</p>

<h2>6. Assurance professionnelle</h2>
<p>{V['assurance']}</p>

<h2>7. Médiation de la consommation</h2>
<p>Conformément à l'article L.612-1 du Code de la consommation, tout consommateur a le droit de recourir gratuitement à un médiateur de la consommation en vue de la résolution amiable d'un litige l'opposant à un professionnel, après avoir tenté au préalable de résoudre le litige directement auprès de Saileau par une réclamation écrite.</p>
<p>Cette obligation d'information s'applique dès lors qu'une vente est conclue avec un consommateur, quel que soit le canal utilisé (site, messagerie, plateforme tierce).</p>
<div class="legal-box">
<p><strong>Médiateur compétent&nbsp;:</strong><br>{V['mediateur']}</p>
</div>
<p><em>Note&nbsp;: la plateforme européenne de règlement en ligne des litiges (RLL/ODR) a définitivement fermé le 20 juillet 2025 en application du règlement (UE) 2024/3228. Aucun lien vers cette plateforme ne doit donc plus figurer sur un site marchand. Pour les litiges transfrontaliers, le Centre Européen des Consommateurs France reste compétent.</em></p>

<h2>8. Données personnelles et cookies</h2>
<p>Le traitement des données personnelles est décrit dans la <a href="{u('confidentialite/')}">politique de confidentialité</a>, qui précise également l'usage du stockage local (panier) et l'absence de cookies publicitaires ou de mesure d'audience.</p>

<h2>9. Droit applicable</h2>
<p>Le présent site et les mentions légales sont soumis au droit français. En cas de litige et à défaut de résolution amiable, les tribunaux français sont compétents dans les conditions prévues par le Code de la consommation pour les consommateurs, et par le Code de commerce pour les professionnels.</p>
"""
    legal_page('mentions-legales', "Mentions légales | Saileau",
               "Mentions légales du site Saileau : éditeur, hébergeur, propriété intellectuelle, médiation de la consommation.",
               "Mentions légales", inner)


def build_confidentialite():
    inner = f"""
<p>La présente politique décrit la manière dont {V['nom_legal']} (« Saileau ») traite les données personnelles des visiteurs et des clients, conformément au Règlement (UE) 2016/679 (RGPD) et à la loi « Informatique et Libertés » modifiée.</p>

<h2>1. Responsable de traitement</h2>
<p>{V['nom_legal']} — {V['adresse']} — <a href="mailto:{V['email']}">{V['email']}</a>. Aucun délégué à la protection des données (DPO) n'a été désigné, la désignation n'étant pas obligatoire au regard de l'activité.</p>

<h2>2. Principe général</h2>
<div class="legal-box">
<p>Le site <strong>ne comporte aucun formulaire, aucun compte client, aucun paiement en ligne et aucun outil de mesure d'audience</strong>. Il est hébergé en pages statiques&nbsp;: Saileau ne collecte donc <strong>aucune donnée à votre insu</strong> lors de la simple consultation du site.</p>
</div>

<h2>3. Données traitées et finalités</h2>
<table>
<tr><th>Donnée</th><th>Finalité</th><th>Base légale (art. 6 RGPD)</th><th>Conservation</th></tr>
<tr><td>Contenu de votre panier (stocké dans votre navigateur)</td><td>Mémoriser votre sélection entre deux pages</td><td>Intérêt légitime — fonctionnement du service demandé</td><td>Jusqu'à effacement par vos soins ; reste sur votre appareil</td></tr>
<tr><td>Numéro de téléphone, nom, contenu du message (WhatsApp)</td><td>Traiter et suivre votre demande de commande</td><td>Mesures précontractuelles / exécution du contrat</td><td>3 ans après le dernier contact (prospect) </td></tr>
<tr><td>Adresse email et contenu du message</td><td>Répondre à votre demande, établir un devis</td><td>Mesures précontractuelles / exécution du contrat</td><td>3 ans après le dernier contact</td></tr>
<tr><td>Nom, adresse postale, coordonnées de livraison</td><td>Exécuter la commande et l'expédition</td><td>Exécution du contrat</td><td>Durée de la relation commerciale</td></tr>
<tr><td>Données de facturation</td><td>Obligations comptables et fiscales</td><td>Obligation légale</td><td>10 ans (art. L.123-22 du Code de commerce)</td></tr>
<tr><td>Adresse IP et données techniques de connexion</td><td>Journalisation et sécurité par l'hébergeur</td><td>Intérêt légitime de l'hébergeur</td><td>Selon la politique de GitHub</td></tr>
</table>

<h2>4. Stockage local (panier) et cookies</h2>
<p>Le site n'utilise <strong>aucun cookie publicitaire, de mesure d'audience ou de réseau social</strong>. Il utilise uniquement le <em>stockage local</em> (<code>localStorage</code>) de votre navigateur pour conserver le contenu de votre panier d'une page à l'autre.</p>
<p>Ce stockage est <strong>strictement nécessaire</strong> à la fourniture du service que vous demandez expressément&nbsp;: conformément à l'article 82 de la loi Informatique et Libertés et aux lignes directrices de la CNIL, il est dispensé de recueil du consentement. <strong>Aucun bandeau cookies n'est donc requis</strong> sur ce site en l'état.</p>
<p>Vous pouvez effacer ces données à tout moment en vidant le panier ou en supprimant les données de site de votre navigateur. Si un outil de statistiques ou de publicité était ajouté ultérieurement, un bandeau de consentement conforme deviendrait obligatoire.</p>

<h2>5. Destinataires et sous-traitants</h2>
<ul>
<li><strong>GitHub, Inc. (GitHub Pages)</strong> — hébergement du site. Données techniques de connexion. Transfert vers les États-Unis encadré par les clauses contractuelles types de la Commission européenne et le cadre de protection des données UE–États-Unis (<em>Data Privacy Framework</em>).</li>
<li><strong>Google Ireland Ltd. / Google LLC (Google Fonts)</strong> — les polices d'écriture du site sont chargées depuis les serveurs Google&nbsp;; votre adresse IP est alors transmise à Google. Voir le point 9 pour l'alternative envisagée.</li>
<li><strong>Meta Platforms Ireland Ltd. (WhatsApp)</strong> — si vous choisissez d'envoyer votre commande via WhatsApp, l'échange est soumis aux conditions et à la politique de confidentialité de WhatsApp, dont Saileau n'est pas responsable.</li>
<li><strong>Google Ireland Ltd. (Gmail)</strong> — messagerie utilisée pour les échanges par email.</li>
<li><strong>Vinted UAB</strong> — si la commande passe par la boutique Vinted, les données sont traitées par Vinted selon sa propre politique.</li>
<li><strong>La Poste / transporteurs</strong> — coordonnées nécessaires à l'expédition.</li>
</ul>
<p>Aucune donnée n'est vendue, louée ou cédée à des tiers à des fins commerciales.</p>

<h2>6. Vos droits</h2>
<p>Vous disposez des droits d'accès, de rectification, d'effacement, de limitation, d'opposition et de portabilité, ainsi que du droit de définir des directives relatives au sort de vos données après votre décès.</p>
<p>Pour les exercer&nbsp;: <a href="mailto:{V['email']}">{V['email']}</a>. Une réponse vous sera apportée dans un délai d'un mois. Une pièce justificative d'identité peut être demandée en cas de doute raisonnable sur votre identité.</p>
<p>Vous pouvez également introduire une réclamation auprès de la CNIL — 3 place de Fontenoy, TSA 80715, 75334 Paris Cedex 07 — <a href="https://www.cnil.fr" target="_blank" rel="noopener">www.cnil.fr</a>.</p>

<h2>7. Sécurité</h2>
<p>Le site est diffusé en HTTPS. Les échanges commerciaux transitent par des services tiers disposant de leurs propres mesures de sécurité. Saileau conserve les documents commerciaux sur des supports protégés par mot de passe.</p>

<h2>8. Mineurs</h2>
<p>Les produits et le site ne sont pas destinés spécifiquement aux mineurs. Toute commande passée par un mineur suppose l'accord de son représentant légal.</p>

<h2>9. Évolutions</h2>
<p>Cette politique peut être modifiée pour tenir compte des évolutions du site ou de la réglementation. Une version auto-hébergée des polices d'écriture est envisagée afin de supprimer tout appel aux serveurs de Google lors de la consultation du site.</p>
"""
    legal_page('confidentialite', "Politique de confidentialité et données personnelles | Saileau",
               "Comment Saileau traite vos données personnelles : finalités, durées de conservation, destinataires, absence de cookies publicitaires et exercice de vos droits RGPD.",
               "Politique de confidentialité", inner)


def build_cgv():
    inner = f"""
<div class="legal-box">
<p><strong>En résumé&nbsp;:</strong> le site ne prend aucun paiement. Vous envoyez votre panier par WhatsApp ou email, je confirme le prix, le délai et la disponibilité, puis vous réglez par virement, Wero, PayPal ou via Vinted. Vous disposez de 14 jours de rétractation, sauf pour les pièces fabriquées sur mesure.</p>
</div>

<h2>Article 1 — Objet et champ d'application</h2>
<p>Les présentes conditions générales de vente (CGV) régissent les ventes de produits conclues entre {V['nom_legal']}, entrepreneur individuel exerçant sous le nom commercial « Saileau » (ci-après « le Vendeur »), et toute personne physique ou morale passant commande (ci-après « le Client »).</p>
<p>Elles s'appliquent à toute commande transmise depuis le site, par WhatsApp, par email ou par tout autre moyen convenu. Les ventes réalisées via la plateforme Vinted sont en outre soumises aux conditions propres à cette plateforme.</p>
<p>Toute commande implique l'acceptation sans réserve des présentes CGV. Le Vendeur se réserve le droit de les modifier&nbsp;; les CGV applicables sont celles en vigueur à la date de la commande.</p>

<h2>Article 2 — Produits</h2>
<p>Les produits proposés sont des pièces techniques destinées à la voile légère, au wing foil et au catamaran, fabriquées en petite série ou sur mesure, notamment par fabrication additive (impression 3D), ainsi que du petit accastillage.</p>
<p>Les photographies et illustrations n'ont pas de valeur contractuelle&nbsp;: la couleur, la finition de surface et de légères variations dimensionnelles peuvent exister, la fabrication étant réalisée pièce par pièce.</p>
<p>Les compatibilités indiquées (Harken, GoPro, boîtier US, etc.) sont fournies à titre informatif. Il appartient au Client de vérifier l'adéquation du produit à son besoin et à son matériel. Les pièces ne sont pas destinées à un usage de sécurité critique ni au gréement dormant sous charge, sauf indication contraire expresse.</p>

<h2>Article 3 — Prix</h2>
<p>Les prix sont indiqués en euros, <strong>prix nets&nbsp;: TVA non applicable, article 293 B du Code général des impôts</strong>. Ils s'entendent hors frais de livraison, lesquels sont précisés à l'article 5.</p>
<p>Le Vendeur se réserve le droit de modifier ses prix à tout moment&nbsp;; les produits sont facturés sur la base du tarif confirmé au Client lors de la validation de la commande.</p>
<p>Pour les pièces sur mesure, le prix est établi sur devis gratuit, valable 30 jours.</p>

<h2>Article 4 — Commande et formation du contrat</h2>
<p>Le panier du site ne constitue ni une commande ferme, ni un paiement. Le processus est le suivant&nbsp;:</p>
<ol>
<li>le Client compose son panier et l'envoie par WhatsApp ou par email&nbsp;;</li>
<li>le Vendeur confirme par écrit la disponibilité, le prix total, les frais de livraison et le délai&nbsp;;</li>
<li>le contrat est formé à réception du paiement, ou de l'accord exprès du Client sur le devis lorsqu'un règlement différé est convenu.</li>
</ol>
<p>Le Vendeur se réserve le droit de refuser ou d'annuler toute commande présentant un caractère anormal, une demande manifestement incompatible avec ses moyens de production, ou émanant d'un Client avec lequel un litige de paiement est en cours.</p>

<h2>Article 5 — Livraison</h2>
<p>Les produits sont expédiés à l'adresse indiquée par le Client.</p>
<ul>
<li><strong>France métropolitaine&nbsp;:</strong> expédition offerte à partir de 25 € de commande. En dessous de ce montant, les frais réels d'expédition sont indiqués avant paiement.</li>
<li><strong>Hors France métropolitaine&nbsp;:</strong> nous consulter avant commande, ou passer par la boutique Vinted.</li>
</ul>
<p>Le délai indicatif de préparation est de 1 à 5 jours ouvrés, auquel s'ajoute le délai d'acheminement du transporteur. Pour les pièces sur mesure, le délai est précisé au devis.</p>
<p>Conformément à l'article L.216-1 du Code de la consommation, la livraison intervient au plus tard 30 jours après la conclusion du contrat, sauf délai différent convenu. En cas de retard, le Client peut, après mise en demeure restée sans effet dans un délai raisonnable, résoudre le contrat et être remboursé sous 14 jours.</p>
<p>Le transfert des risques s'opère à la remise physique du produit au Client (art. L.216-4). Le Client est invité à vérifier l'état du colis à la réception et à émettre toute réserve auprès du transporteur.</p>

<h2>Article 6 — Paiement</h2>
<p>Les moyens de paiement acceptés sont&nbsp;: virement bancaire, Wero, PayPal, ou paiement via la plateforme Vinted. Aucun paiement n'est encaissé directement sur le site, qui ne stocke aucune coordonnée bancaire.</p>
<p>Sauf accord contraire, la commande est expédiée après encaissement complet.</p>
<p>Entre professionnels, tout retard de paiement entraîne de plein droit des pénalités au taux d'intérêt de la BCE majoré de 10 points, ainsi qu'une indemnité forfaitaire de recouvrement de 40 € (art. L.441-10 et D.441-5 du Code de commerce).</p>

<h2>Article 7 — Droit de rétractation</h2>
<p>Conformément à l'article L.221-18 du Code de la consommation, le Client consommateur dispose d'un délai de <strong>quatorze (14) jours</strong> à compter de la réception du produit pour exercer son droit de rétractation, sans avoir à motiver sa décision ni à supporter de pénalité.</p>
<p>Pour l'exercer, le Client informe le Vendeur de sa décision par une déclaration dénuée d'ambiguïté, adressée à <a href="mailto:{V['email']}">{V['email']}</a>, ou en utilisant le formulaire type figurant à l'article 12.</p>
<p>Le produit doit être retourné au plus tard 14 jours après communication de la décision, dans son état d'origine et complet. <strong>Les frais de retour sont à la charge du Client.</strong> Le Vendeur rembourse la totalité des sommes versées, y compris les frais de livraison standard, au plus tard 14 jours après récupération du produit ou preuve de son expédition, par le même moyen de paiement que celui utilisé lors de la commande.</p>
<div class="legal-box">
<p><strong>Exception importante&nbsp;:</strong> conformément à l'article L.221-28 3° du Code de la consommation, le droit de rétractation <strong>ne s'applique pas</strong> aux biens confectionnés selon les spécifications du Client ou nettement personnalisés. Sont notamment concernés&nbsp;: les pièces sur mesure, les cales de rake réalisées dans un angle précisé à la commande, et toute pièce adaptée aux cotes fournies par le Client. Cette information est rappelée avant validation de ce type de commande.</p>
</div>

<h2>Article 8 — Garanties légales</h2>
<p>Tous les produits bénéficient des garanties légales, indépendamment de toute garantie commerciale&nbsp;:</p>
<h3>Garantie légale de conformité (art. L.217-3 et suivants du Code de la consommation)</h3>
<ul>
<li>Le Client dispose de <strong>2 ans à compter de la délivrance</strong> du bien pour agir.</li>
<li>Il peut choisir entre la réparation et le remplacement, sous réserve des conditions de coût de l'article L.217-12.</li>
<li>Il est dispensé de prouver l'existence du défaut de conformité pendant <strong>24 mois</strong> suivant la délivrance (12 mois pour les biens d'occasion).</li>
<li>La garantie s'applique sans frais et n'exclut pas la mise en œuvre de la garantie des vices cachés.</li>
<li>Toute période d'immobilisation d'au moins 7 jours pour réparation s'ajoute à la durée de garantie restante.</li>
</ul>
<h3>Garantie des vices cachés (art. 1641 et suivants du Code civil)</h3>
<p>Le Client peut agir dans un délai de 2 ans à compter de la découverte du vice et obtenir la résolution de la vente ou une réduction du prix.</p>
<p>Sont exclues des garanties&nbsp;: l'usure normale, les dommages résultant d'un montage non conforme, d'une modification de la pièce, d'un dépassement des charges d'utilisation, d'un usage détourné, d'un choc ou d'un défaut d'entretien.</p>
<p>Toute demande au titre des garanties&nbsp;: <a href="mailto:{V['email']}">{V['email']}</a>, avec photos et description du problème.</p>

<h2>Article 9 — Responsabilité</h2>
<p>Les pièces sont conçues pour un usage nautique de loisir et de compétition dans des conditions normales d'utilisation. Le Vendeur ne saurait être tenu responsable des dommages résultant d'un usage non conforme, d'un montage inadapté ou d'un défaut de vérification préalable de compatibilité par le Client.</p>
<p>La responsabilité du Vendeur ne saurait excéder le montant de la commande concernée, sauf en cas de dommage corporel ou de faute lourde ou intentionnelle.</p>

<h2>Article 10 — Réclamations et médiation</h2>
<p>Toute réclamation doit d'abord être adressée au Vendeur&nbsp;: <a href="mailto:{V['email']}">{V['email']}</a>.</p>
<p>À défaut de solution amiable dans un délai d'un an à compter de la réclamation écrite, le Client consommateur peut saisir gratuitement le médiateur de la consommation&nbsp;:</p>
<div class="legal-box"><p>{V['mediateur']}</p></div>

<h2>Article 11 — Droit applicable et litiges</h2>
<p>Les présentes CGV sont soumises au droit français. En cas de litige, une solution amiable sera recherchée en priorité. À défaut, le Client consommateur peut saisir la juridiction de son choix parmi celles prévues par le Code de procédure civile, ou la juridiction du lieu de son domicile.</p>

<h2>Article 12 — Formulaire type de rétractation</h2>
<p>(À compléter et renvoyer uniquement si vous souhaitez vous rétracter du contrat — annexe à l'article R.221-1 du Code de la consommation.)</p>
<div class="legal-box">
<p>À l'attention de {V['nom_legal']} — {V['adresse']} — {V['email']}&nbsp;:</p>
<p>Je vous notifie par la présente ma rétractation du contrat portant sur la vente du bien ci-dessous&nbsp;:</p>
<p>Commandé le : …………………… / Reçu le : ……………………<br>
Référence(s) du ou des produits : ……………………………………<br>
Nom du consommateur : ……………………………………<br>
Adresse du consommateur : ……………………………………<br>
Signature (uniquement en cas de notification sur papier) : ……………………<br>
Date : ……………………</p>
</div>
"""
    legal_page('cgv', "Conditions générales de vente | Saileau",
               "CGV Saileau : commande, prix, livraison, paiement, droit de rétractation de 14 jours, garanties légales de conformité et des vices cachés, médiation de la consommation.",
               "Conditions générales de vente", inner, prio='0.4')



# ================================================================
#  ARTICLES — /articles/*.md  →  /actualites/<slug>/
# ================================================================

def md_inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)\)',
               lambda m: '<img src="%s" alt="%s" loading="lazy">' % (
                   u(m.group(2)) if not m.group(2).startswith('http') else m.group(2), m.group(1)), t)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',
               lambda m: '<a href="%s"%s>%s</a>' % (
                   m.group(2) if m.group(2).startswith(('http', '#')) else u(m.group(2)),
                   ' target="_blank" rel="noopener"' if m.group(2).startswith('http') else '',
                   m.group(1)), t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![*\w])\*([^*]+)\*(?!\w)', r'<em>\1</em>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return t


def md_to_html(md):
    """Markdown minimal : titres, paragraphes, listes, citations, images, tableaux simples."""
    out, buf_ul, buf_ol = [], [], []

    def flush():
        if buf_ul:
            out.append('<ul>' + ''.join('<li>%s</li>' % md_inline(x) for x in buf_ul) + '</ul>')
            buf_ul.clear()
        if buf_ol:
            out.append('<ol>' + ''.join('<li>%s</li>' % md_inline(x) for x in buf_ol) + '</ol>')
            buf_ol.clear()

    for raw in md.split('\n'):
        line = raw.rstrip()
        if not line.strip():
            flush(); continue
        m = re.match(r'^(#{2,4})\s+(.*)$', line)
        if m:
            flush(); n = len(m.group(1))
            out.append('<h%d>%s</h%d>' % (n, md_inline(m.group(2)), n)); continue
        if re.match(r'^\s*[-*]\s+', line):
            buf_ul.append(re.sub(r'^\s*[-*]\s+', '', line)); continue
        if re.match(r'^\s*\d+[.)]\s+', line):
            buf_ol.append(re.sub(r'^\s*\d+[.)]\s+', '', line)); continue
        if line.startswith('>'):
            flush(); out.append('<blockquote>%s</blockquote>' % md_inline(line.lstrip('> '))); continue
        if re.match(r'^-{3,}$', line):
            flush(); out.append('<hr>'); continue
        flush(); out.append('<p>%s</p>' % md_inline(line))
    flush()
    return '\n'.join(out)


MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
        'août', 'septembre', 'octobre', 'novembre', 'décembre']


def date_fr(iso):
    d = datetime.date.fromisoformat(iso)
    return '%d %s %d' % (d.day, MOIS[d.month - 1], d.year)


def load_articles():
    """Lit /articles/*.md. En-tête entre --- puis le contenu Markdown."""
    d = os.path.join(ROOT, 'articles')
    arts = []
    if not os.path.isdir(d):
        return arts
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.md'):
            continue
        txt = open(os.path.join(d, fn), encoding='utf-8').read()
        m = re.match(r'^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$', txt)
        if not m:
            print('  !! en-tête manquant, article ignoré :', fn); continue
        meta, body = {}, m.group(2)
        for line in m.group(1).split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip()
        if meta.get('publie', 'true').lower() in ('false', 'non', '0'):
            print('  (brouillon ignoré :', fn + ')'); continue
        for champ in ('titre', 'description', 'date'):
            if not meta.get(champ):
                print('  !! champ "%s" manquant, article ignoré : %s' % (champ, fn)); meta = None; break
        if not meta:
            continue
        meta['slug'] = meta.get('slug') or fn[:-3]
        meta['produits'] = [x.strip() for x in meta.get('produits', '').split(',') if x.strip()]
        meta['body'] = body
        meta['fichier'] = fn
        arts.append(meta)
    arts.sort(key=lambda a: a['date'], reverse=True)
    return arts


def build_articles(arts):
    if not arts:
        # aucun article publié : on génère quand même la page pour éviter un lien mort,
        # en noindex tant qu'elle est vide
        h = head("Conseils & actualités | Saileau",
                 "Conseils sur les réglages, les matériaux et l'entretien du matériel de voile légère.",
                 'actualites/', robots='noindex, follow')
        body = """%s
<main id="main">
<div class="page-head">
  %s
  <p class="section-label">Le carnet</p>
  <h1>Conseils &amp; <em>actualités</em></h1>
  <p class="section-intro">Les premiers articles arrivent bientôt : réglages, choix des matériaux et entretien du matériel.</p>
  <p style="margin-top:1.5rem"><a href="%s" class="btn-primary"><span>Voir les produits</span></a></p>
</div>
</main>
%s%s%s""" % (NAV, crumb([("Accueil", ""), ("Conseils & actualités", None)]), u('produits/'),
             FOOTER, CART, FOOT_JS)
        write('actualites/index.html', h + body, in_sitemap=False)
        print('  (aucun article publié — page vitrine générée en noindex)')
        return

    # --- page liste ---
    liste = ''.join("""<article class="post-card">
  <a href="%s">
    %s
    <div class="post-body">
      <time datetime="%s">%s</time>
      <h2>%s</h2>
      <p>%s</p>
      <span class="post-more">Lire la suite →</span>
    </div>
  </a>
</article>""" % (u('actualites/%s/' % a['slug']),
                 '<div class="post-img"><img src="%s" alt="%s" loading="lazy"></div>' % (
                     u(a['image']), e(a['titre'])) if a.get('image') else '',
                 a['date'], date_fr(a['date']), e(a['titre']), e(a['description'])) for a in arts)

    ld = [crumb_ld([("Accueil", ""), ("Conseils & actualités", "actualites/")]),
          {"@context": "https://schema.org", "@type": "Blog",
           "name": "Conseils & actualités Saileau", "url": full('actualites/'),
           "inLanguage": "fr-FR",
           "blogPost": [{"@type": "BlogPosting", "headline": a['titre'],
                         "datePublished": a['date'],
                         "url": full('actualites/%s/' % a['slug'])} for a in arts]}]
    h = head("Conseils & actualités — réglages, matériaux et pièces nautiques | Saileau",
             "Conseils pratiques sur les réglages, les matériaux et l'entretien du matériel de voile légère, de wing foil et de catamaran, par l'atelier Saileau à Toulon.",
             'actualites/', ld=ld)
    body = """%s
<main id="main">
<div class="page-head">
  %s
  <p class="section-label">Le carnet</p>
  <h1>Conseils &amp; <em>actualités</em></h1>
  <p class="section-intro">Réglages, choix des matériaux, entretien du matériel : ce que j'apprends sur l'eau et à l'atelier, partagé ici.</p>
</div>
<section style="padding-top:1rem">
  <div class="posts-grid">%s</div>
</section>
</main>
%s%s%s""" % (NAV, crumb([("Accueil", ""), ("Conseils & actualités", None)]), liste, FOOTER, CART, FOOT_JS)
    write('actualites/index.html', h + body, prio='0.8', freq='weekly')

    # --- pages articles ---
    for i, a in enumerate(arts):
        contenu = md_to_html(a['body'])
        lies = [p for p in PRODUITS if p['slug'] in a['produits']]
        bloc_produits = ''
        if lies:
            bloc_produits = ('<section class="related"><h2>Les produits concernés</h2>'
                             '<div class="products-grid">%s</div></section>'
                             % ''.join(card(p) for p in lies))
        autres = [x for x in arts if x['slug'] != a['slug']][:2]
        bloc_autres = ''
        if autres:
            bloc_autres = ('<div class="post-nav"><h3>À lire aussi</h3>%s</div>'
                           % ''.join('<a href="%s">%s</a>' % (u('actualites/%s/' % x['slug']), e(x['titre']))
                                     for x in autres))
        img_abs = full(a['image']) if a.get('image') else full('assets/img/og-saileau.jpg')
        ld = [crumb_ld([("Accueil", ""), ("Conseils & actualités", "actualites/"),
                        (a['titre'], 'actualites/%s/' % a['slug'])]),
              {"@context": "https://schema.org", "@type": "BlogPosting",
               "headline": a['titre'], "description": a['description'],
               "datePublished": a['date'], "dateModified": a.get('maj', a['date']),
               "image": img_abs, "inLanguage": "fr-FR",
               "author": {"@type": "Person", "name": CFG['identite']['nom_legal'].replace('<span class="todo">', '').replace('</span>', '')},
               "publisher": {"@type": "Organization", "name": "Saileau", "@id": full('#store')},
               "mainEntityOfPage": full('actualites/%s/' % a['slug'])}]
        h = head("%s | Saileau" % a['titre'], a['description'],
                 'actualites/%s/' % a['slug'],
                 og_img=u(a['image']) if a.get('image') else None, ld=ld)
        body = """%s
<main id="main">
<div class="page-head" style="padding-bottom:0">
  %s
  <p class="post-meta"><time datetime="%s">%s</time></p>
  <h1>%s</h1>
  <p class="section-intro">%s</p>
</div>
<article class="legal article">
%s
%s
</article>
%s
</main>
%s%s%s""" % (NAV,
             crumb([("Accueil", ""), ("Conseils & actualités", "actualites/"), (a['titre'], None)]),
             a['date'], date_fr(a['date']), e(a['titre']), e(a['description']),
             ('<figure class="article-hero"><img src="%s" alt="%s"></figure>'
              % (u(a['image']), e(a['titre']))) if a.get('image') else '',
             contenu + bloc_autres, bloc_produits, FOOTER, CART, FOOT_JS)
        write('actualites/%s/index.html' % a['slug'], h + body, prio='0.7', freq='monthly')


# ---------------------------------------------------------------- 7. 404 / robots / sitemap

def build_404():
    h = head("Page introuvable — Saileau", "La page demandée n'existe pas ou a été déplacée.",
             '404.html', robots='noindex, follow')
    body = f"""{NAV}
<main id="main" class="notfound">
  <h1>404</h1>
  <p class="section-intro">Cette page n'existe pas ou a changé d'adresse.</p>
  <div class="hero-ctas" style="justify-content:center">
    <a href="{u('produits/')}" class="btn-primary"><span>Voir le catalogue</span></a>
    <a href="{u('')}" class="btn-outline"><span>Retour à l'accueil</span></a>
  </div>
</main>
{FOOTER}{CART}{FOOT_JS}"""
    write('404.html', h + body, in_sitemap=False)


def build_sitemap():
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, prio, freq in PAGES:
        xml.append('  <url><loc>%s</loc><lastmod>%s</lastmod>'
                   '<changefreq>%s</changefreq><priority>%s</priority></url>' % (url, TODAY, freq, prio))
    xml.append('</urlset>')
    open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(xml))
    print('  → sitemap.xml (%d URL)' % len(PAGES))

    robots = ("User-agent: *\nAllow: /\n\n"
              "Sitemap: %s\n" % full('sitemap.xml'))
    open(os.path.join(ROOT, 'robots.txt'), 'w', encoding='utf-8').write(robots)
    print('  → robots.txt')
    open(os.path.join(ROOT, '.nojekyll'), 'w').write('')


# ---------------------------------------------------------------- main

if __name__ == '__main__':
    print('Génération du site Saileau…')
    build_home()
    build_catalogue()
    for p in PRODUITS:
        build_produit(p)
    build_articles(load_articles())
    build_apropos()
    build_commander()
    build_mentions()
    build_confidentialite()
    build_cgv()
    build_404()
    build_sitemap()
    print('Terminé — %d pages.' % (len(PAGES) + 1))
