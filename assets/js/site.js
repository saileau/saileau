/* =========================================================
   Saileau — script commun à toutes les pages
   Panier persistant (localStorage), menu, galerie, filtres.
   ========================================================= */
(function () {
  'use strict';

  var CFG = {
    wa: '33617259570',
    email: 'saileau.prod@gmail.com',
    base: window.SAILEAU_BASE || ''
  };

  /* ---------- utilitaires ---------- */
  function $(s, c) { return (c || document).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); }
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function eur(n) { return n.toFixed(2).replace('.', ',') + ' €'; }

  var _t;
  function showToast(msg) {
    var el = $('#toast'); if (!el) return;
    el.textContent = msg; el.classList.add('show');
    clearTimeout(_t); _t = setTimeout(function () { el.classList.remove('show'); }, 2600);
  }

  /* ---------- menu mobile ---------- */
  window.toggleMenu = function () { $('#navLinks').classList.toggle('open'); };
  window.closeMenu = function () { $('#navLinks').classList.remove('open'); };

  /* ---------- panier ---------- */
  var panier = [];
  try { panier = JSON.parse(lsGet('sc') || '[]'); } catch (e) { panier = []; }

  function saveCart() { lsSet('sc', JSON.stringify(panier)); }
  function getTotal() { return panier.reduce(function (s, i) { return s + i.prix * i.qty; }, 0); }

  function updCart() {
    var n = panier.reduce(function (s, i) { return s + i.qty; }, 0);
    var el = $('#cartCount');
    if (el) { el.textContent = n; el.classList.toggle('visible', n > 0); }
    var t = $('#cartTotalAmount'); if (t) t.textContent = eur(getTotal());
    var f = $('#cartFooter'); if (f) f.style.display = panier.length ? 'block' : 'none';
  }

  function renderCart() {
    var body = $('#cartBody'); if (!body) return;
    if (!panier.length) {
      body.innerHTML = '<div class="cart-empty"><p>Votre panier est vide</p></div>';
      updCart(); return;
    }
    body.innerHTML = panier.map(function (i) {
      var img = i.img ? '<img src="' + CFG.base + i.img + '" alt="" loading="lazy">' : '';
      return '<div class="cart-item"><div class="cart-item-img">' + img + '</div>' +
        '<div class="cart-item-info"><div class="cart-item-name">' + i.nom + '</div>' +
        '<div class="cart-item-price">' + (i.prix ? eur(i.prix) : 'Sur devis') + '</div>' +
        '<div class="cart-item-qty"><button class="qty-btn" data-qty="-1" data-cid="' + i.cid + '" aria-label="Retirer un exemplaire">−</button>' +
        '<span class="qty-num">' + i.qty + '</span>' +
        '<button class="qty-btn" data-qty="1" data-cid="' + i.cid + '" aria-label="Ajouter un exemplaire">+</button>' +
        '<button class="cart-item-remove" data-rem="' + i.cid + '" aria-label="Supprimer la ligne">Supprimer</button></div></div></div>';
    }).join('');
    updCart();
  }

  document.addEventListener('click', function (e) {
    var q = e.target.closest('[data-qty]');
    if (q) {
      var it = panier.find(function (i) { return i.cid === q.dataset.cid; });
      if (it) { it.qty = Math.max(1, it.qty + parseInt(q.dataset.qty, 10)); saveCart(); renderCart(); }
      return;
    }
    var r = e.target.closest('[data-rem]');
    if (r) {
      panier = panier.filter(function (i) { return i.cid !== r.dataset.rem; });
      saveCart(); renderCart();
    }
  });

  window.toggleCart = function () {
    $('#cartSidebar').classList.toggle('open');
    $('#cartOverlay').classList.toggle('open');
    renderCart();
  };

  window.addToCart = function (btn) {
    var d = btn.dataset;
    var sel = document.getElementById('ppVariant');
    var variant = sel ? sel.options[sel.selectedIndex].text : (d.variant || null);
    var cid = variant ? d.id + '_' + variant : String(d.id);
    var nom = variant ? d.nom + ' — ' + variant : d.nom;
    var ex = panier.find(function (i) { return i.cid === cid; });
    if (ex) ex.qty++;
    else panier.push({ cid: cid, id: d.id, nom: nom, prix: parseFloat(d.prix) || 0, img: d.img || '', qty: 1 });
    saveCart(); updCart();
    showToast(nom + ' ajouté au panier');
  };

  function buildMsg() {
    var m = 'Bonjour, je souhaite commander :\n\n';
    panier.forEach(function (i) {
      m += '• ' + i.nom + ' × ' + i.qty + (i.prix ? ' — ' + eur(i.prix * i.qty) : ' — sur devis') + '\n';
    });
    var t = getTotal();
    if (t > 0) m += '\nTotal indicatif : ' + eur(t) + '\n';
    m += '\n(Commande envoyée depuis saileau.fr)';
    return m;
  }

  function cgvOk() {
    var c = $('#cgvCheck');
    if (c && !c.checked) { showToast('Merci d\u2019accepter les conditions générales de vente'); return false; }
    return true;
  }

  window.checkoutWa = function () {
    if (!panier.length || !cgvOk()) return;
    window.open('https://wa.me/' + CFG.wa + '?text=' + encodeURIComponent(buildMsg()), '_blank', 'noopener');
  };
  window.checkoutMail = function () {
    if (!panier.length || !cgvOk()) return;
    window.location.href = 'mailto:' + CFG.email + '?subject=Commande%20Saileau&body=' + encodeURIComponent(buildMsg());
  };
  window.contactWa = function () {
    window.open('https://wa.me/' + CFG.wa + '?text=' +
      encodeURIComponent('Bonjour, j\u2019ai une question sur vos produits Saileau.'), '_blank', 'noopener');
  };

  /* ---------- filtres catalogue (les cartes sont dans le HTML : aucun impact SEO) ---------- */
  window.filterProducts = function (cat, btn) {
    $$('.filter-btn').forEach(function (b) { b.classList.remove('active'); b.setAttribute('aria-pressed', 'false'); });
    btn.classList.add('active'); btn.setAttribute('aria-pressed', 'true');
    $$('.product-card').forEach(function (c) {
      c.style.display = (cat === 'all' || c.dataset.cat === cat) ? '' : 'none';
    });
  };

  /* ---------- galerie fiche produit ---------- */
  var G = { imgs: [], i: 0 };
  function paint() {
    var main = $('#ppMainImg'); if (!main || !G.imgs.length) return;
    main.src = CFG.base + G.imgs[G.i].src;
    main.width = G.imgs[G.i].w; main.height = G.imgs[G.i].h;
    $$('.pp-thumb').forEach(function (t, k) { t.classList.toggle('active', k === G.i); });
  }
  window.ppSlide = function (d) {
    if (!G.imgs.length) return;
    G.i = (G.i + d + G.imgs.length) % G.imgs.length; paint();
  };
  window.ppSet = function (k) { G.i = k; paint(); };
  window.ppVariantChange = function (sel) {
    var data = JSON.parse(sel.dataset.imgs || '{}');
    var arr = data[sel.value] || [];
    if (arr.length) {
      G.imgs = arr; G.i = 0;
      $('#ppThumbs').innerHTML = arr.map(function (im, k) {
        return '<button class="pp-thumb' + (k === 0 ? ' active' : '') + '" onclick="ppSet(' + k + ')" aria-label="Photo ' + (k + 1) + '">' +
          '<img src="' + CFG.base + im.src + '" alt="" loading="lazy" width="' + im.w + '" height="' + im.h + '"></button>';
      }).join('');
      paint();
    }
  };

  /* ---------- init ---------- */
  document.addEventListener('DOMContentLoaded', function () {
    updCart();
    var g = $('#ppGalleryData');
    if (g) { G.imgs = JSON.parse(g.textContent); G.i = 0; }
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        var cs = $('#cartSidebar');
        if (cs && cs.classList.contains('open')) window.toggleCart();
      }
      if ($('#ppMainImg')) {
        if (e.key === 'ArrowLeft') window.ppSlide(-1);
        if (e.key === 'ArrowRight') window.ppSlide(1);
      }
    });
  });
})();
