'use strict';
(() => {
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const normal = (v) => String(v || '').toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').trim();
  const nav = $('#main-nav');
  const menu = $('.menu-button');
  function closeMenu() { nav?.classList.remove('open'); menu?.setAttribute('aria-expanded', 'false'); menu?.setAttribute('aria-label', 'Open menu'); }
  menu?.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    menu.setAttribute('aria-expanded', String(open));
    menu.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  });
  document.addEventListener('click', (e) => {
    $$('.nav-dropdown[open]').forEach((el) => { if (!el.contains(e.target)) el.open = false; });
    if (!$('.site-header')?.contains(e.target)) closeMenu();
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { closeMenu(); $$('.nav-dropdown').forEach((el) => { el.open = false; }); } });
  $$('.back-top:not(#reset-catalog)').forEach((b) => b.addEventListener('click', () => window.scrollTo({top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'})));

  // The complete catalogue is rendered in the HTML; filters reuse those same cards.
  const catalogue = $('[data-catalog]');
  if (catalogue) {
    const cards = $$('[data-card]', catalogue);
    const grid = $('#catalog-grid', catalogue);
    const q = $('#catalog-query', catalogue);
    const select = $('#category-filter', catalogue);
    const sort = $('#catalog-sort', catalogue);
    const more = $('#load-more', catalogue);
    const kind = catalogue.dataset.catalog;
    const params = new URLSearchParams(location.search);
    const allowed = new Set(cards.flatMap((c) => JSON.parse(c.dataset.tags)));
    let tag = normal(params.get('category') ?? catalogue.dataset.initialTag);
    if (!allowed.has(tag)) tag = '';
    let limit = kind === 'recipes' ? 12 : Infinity;
    q.value = params.get('q') || '';
    const original = new Map(cards.map((c, i) => [c, i]));
    function update() {
      const terms = normal(q.value).split(/\s+/).filter(Boolean);
      const filtered = cards.filter((c) => (!tag || JSON.parse(c.dataset.tags).includes(tag)) && terms.every((term) => normal(c.dataset.search).includes(term)));
      filtered.sort((a, b) => {
        if (sort.value === 'az') return a.dataset.name.localeCompare(b.dataset.name);
        if (sort.value === 'za') return b.dataset.name.localeCompare(a.dataset.name);
        if (sort.value === 'quickest') return Number(a.dataset.time) - Number(b.dataset.time);
        return original.get(a) - original.get(b);
      });
      cards.forEach((c) => { c.hidden = true; });
      filtered.forEach((c, i) => { grid.appendChild(c); c.hidden = i >= limit; });
      $('#catalog-count').textContent = `${filtered.length} ${filtered.length === 1 ? kind.slice(0, -1) : kind}`;
      $('#catalog-empty').hidden = filtered.length !== 0;
      more.hidden = filtered.length <= limit;
      $$('.pill[data-filter]', catalogue).forEach((b) => { const active = b.dataset.filter === tag; b.classList.toggle('active', active); b.setAttribute('aria-pressed', String(active)); });
      if (select) select.value = [...select.options].some((o) => o.value === tag) ? tag : '';
      return filtered;
    }
    function reset() { tag = ''; q.value = ''; sort.value = 'featured'; limit = kind === 'recipes' ? 12 : Infinity; update(); }
    q.addEventListener('input', () => { limit = kind === 'recipes' ? 12 : Infinity; update(); });
    sort.addEventListener('change', update);
    select?.addEventListener('change', () => { tag = select.value; limit = 12; update(); });
    $$('[data-filter]', catalogue).forEach((b) => b.addEventListener('click', () => { tag = b.dataset.filter; limit = kind === 'recipes' ? 12 : Infinity; update(); }));
    $('#clear-filters')?.addEventListener('click', reset);
    $('#reset-catalog')?.addEventListener('click', reset);
    more.addEventListener('click', () => { const before = limit; limit += 12; const filtered = update(); filtered[before]?.focus({preventScroll: true}); });
    update();
  }

  // Every pack's original gallery is present, including alternate packaging.
  const product = $('[data-product]');
  if (product) {
    const options = $$('[data-variant]', product);
    const galleries = $$('[data-variant-gallery]', product);
    const buyGroups = $$('[data-buy-options]', product);
    const buyNow = $('[data-buy-now]', product);
    const buyNowPlatform = $('[data-buy-now-platform]', product);
    const buyPrice = $('[data-buy-price]', product);
    function syncBuy(index) {
      if (!buyGroups.length) return;
      buyGroups.forEach((group) => { group.hidden = group.dataset.buyOptions !== String(index); });
      const active = buyGroups.find((group) => group.dataset.buyOptions === String(index));
      const first = active?.querySelector('[data-retailer-link]');
      if (!first) return;
      if (buyNow) buyNow.href = first.href;
      if (buyNowPlatform) buyNowPlatform.textContent = first.dataset.platform || 'BigBasket';
      if (buyPrice) buyPrice.textContent = first.querySelector('b')?.textContent || '';
    }
    options.forEach((button) => button.addEventListener('click', () => {
      const index = button.dataset.variant;
      options.forEach((b) => { const chosen = b === button; b.classList.toggle('active', chosen); b.setAttribute('aria-pressed', String(chosen)); });
      galleries.forEach((gallery) => { gallery.hidden = gallery.dataset.variantGallery !== index; });
      syncBuy(index);
    }));
    $$('[data-gallery-image]', product).forEach((button) => button.addEventListener('click', () => {
      const gallery = button.closest('.variant-gallery');
      const image = $('.selected-product-image', gallery);
      image.src = button.dataset.galleryImage;
      image.alt = $('img', button).alt;
      $$('[data-gallery-image]', gallery).forEach((b) => { const chosen = b === button; b.classList.toggle('active', chosen); b.setAttribute('aria-pressed', String(chosen)); });
    }));
    syncBuy('0');
  }

  // The two All Products banners alternate every five seconds.
  const productsCarousel = $('[data-products-carousel]');
  if (productsCarousel) {
    const bannerTrack = $('#products-banner-track', productsCarousel);
    const slides = $$('[data-products-slide]', productsCarousel);
    const counter = $('[data-products-current]', productsCarousel);
    const pause = $('[data-products-pause]', productsCarousel);
    const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
    let current = 0;
    let paused = reducedMotion.matches;
    let focusWithin = false;
    let timer;

    function showBanner(index) {
      current = (index + slides.length) % slides.length;
      bannerTrack.style.transform = `translateX(-${current * 100}%)`;
      slides.forEach((slide, i) => slide.setAttribute('aria-hidden', String(i !== current)));
      counter.textContent = String(current + 1).padStart(2, '0');
    }
    function syncRotation() {
      clearInterval(timer);
      pause.textContent = paused ? 'Play' : 'Pause';
      pause.setAttribute('aria-label', paused ? 'Start automatic banner rotation' : 'Pause automatic banner rotation');
      bannerTrack.setAttribute('aria-live', paused || focusWithin ? 'polite' : 'off');
      if (!paused && !focusWithin && !document.hidden) {
        timer = setInterval(() => showBanner(current + 1), 5000);
      }
    }
    function moveBanner(delta) {
      showBanner(current + delta);
      syncRotation();
    }
    $('[data-products-prev]', productsCarousel).addEventListener('click', () => moveBanner(-1));
    $('[data-products-next]', productsCarousel).addEventListener('click', () => moveBanner(1));
    pause.addEventListener('click', () => {
      paused = !paused;
      if (!paused) focusWithin = false;
      syncRotation();
    });
    productsCarousel.addEventListener('focusin', () => { focusWithin = true; syncRotation(); });
    productsCarousel.addEventListener('focusout', (event) => {
      if (!productsCarousel.contains(event.relatedTarget)) { focusWithin = false; syncRotation(); }
    });
    productsCarousel.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        moveBanner(event.key === 'ArrowLeft' ? -1 : 1);
      }
    });
    document.addEventListener('visibilitychange', syncRotation);
    reducedMotion.addEventListener('change', (event) => { paused = event.matches; syncRotation(); });
    syncRotation();
  }

  const track = $('#campaign-track');
  if (track) {
    function current() { return Math.min(3, Math.max(0, Math.round(track.scrollLeft / track.clientWidth))); }
    function move(delta) { const next = (current() + delta + 4) % 4; track.scrollTo({left: next * track.clientWidth, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'}); }
    $('.campaign-prev').addEventListener('click', () => move(-1));
    $('.campaign-next').addEventListener('click', () => move(1));
    track.addEventListener('scroll', () => { $('#campaign-current').textContent = String(current() + 1).padStart(2, '0'); }, {passive: true});
  }

  // Site search uses a small local index, with no external search service.
  const dialog = $('#search-dialog');
  const searchInput = $('#site-search');
  const results = $('#search-results');
  let indexPromise;
  let searchSequence = 0;
  const getIndex = () => indexPromise ||= fetch('/search.json').then((response) => { if (!response.ok) throw new Error('Search is unavailable.'); return response.json(); }).catch((error) => { indexPromise = null; throw error; });
  async function search(value) {
    const sequence = ++searchSequence;
    const terms = normal(value).split(/\s+/).filter(Boolean);
    if (!terms.length) { results.replaceChildren(Object.assign(document.createElement('p'), {className: 'muted', textContent: 'Try “peanut butter”, “sandwich” or “jam”.'})); return []; }
    try {
      const index = await getIndex();
      if (sequence !== searchSequence) return [];
      const matches = index.filter((item) => terms.every((term) => normal(item.text).includes(term)));
      const heading = Object.assign(document.createElement('p'), {className: 'muted', textContent: `${matches.length} ${matches.length === 1 ? 'result' : 'results'}`});
      results.replaceChildren(heading);
      matches.forEach((item) => {
        const a = Object.assign(document.createElement('a'), {href: item.path, className: 'search-result'});
        const image = Object.assign(document.createElement('img'), {src: item.image, alt: item.name, loading: 'lazy'});
        const box = document.createElement('div');
        const title = Object.assign(document.createElement('strong'), {textContent: item.name});
        const detail = Object.assign(document.createElement('small'), {textContent: `${item.type} · ${item.detail}`});
        box.append(title, detail); a.append(image, box); results.append(a);
      });
      if (!matches.length) results.append(Object.assign(document.createElement('p'), {className: 'more-space muted', textContent: 'Try another product, ingredient or recipe name.'}));
      return matches.map(({name, type, path}) => ({name, type, path}));
    } catch (error) {
      results.replaceChildren(Object.assign(document.createElement('p'), {textContent: 'Search could not load. Please try again, or browse all products and recipes from the menu.'}));
      return {error: 'search_unavailable'};
    }
  }
  $('.search-open')?.addEventListener('click', () => { closeMenu(); dialog.showModal(); searchInput.focus(); getIndex().catch(() => {}); });
  $('.search-close')?.addEventListener('click', () => dialog.close());
  dialog?.addEventListener('click', (e) => { if (e.target === dialog) { const r = dialog.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close(); } });
  searchInput?.addEventListener('input', () => search(searchInput.value));

  $('.print-recipe')?.addEventListener('click', () => window.print());
  $('.share-recipe')?.addEventListener('click', async () => {
    const status = $('.share-status');
    try { await navigator.clipboard.writeText(location.href); status.textContent = 'Recipe link copied'; }
    catch { status.textContent = 'Copy the recipe address from your browser to share it.'; }
  });
  $('#contact-form')?.addEventListener('submit', (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const values = new FormData(form);
    const body = `Hello Kissan team,\n\n${values.get('message')}\n\nName: ${values.get('name')}\nEmail: ${values.get('email')}`;
    location.href = `mailto:lever.care@unilever.com?subject=${encodeURIComponent(values.get('topic'))}&body=${encodeURIComponent(body)}`;
    $('#contact-status').textContent = 'Your email draft is ready to open. Review it in your email app and send when you are ready. If it does not open, email lever.care@unilever.com directly.';
  });
  $('#increase-text')?.addEventListener('click', (event) => {
    const enabled = document.documentElement.classList.toggle('larger-text');
    event.currentTarget.setAttribute('aria-pressed', String(enabled));
    event.currentTarget.textContent = enabled ? 'Standard text size' : 'Larger text';
  });

  // Optional browser support: expose the same visible product/recipe search.
  if (document.modelContext?.registerTool) {
    const lifecycle = new AbortController();
    try {
      Promise.resolve(document.modelContext.registerTool({
        name: 'search_kissan_catalogue', title: 'Search Kissan products and recipes',
        description: 'Open the visible Kissan search and show matching products or recipes. This does not place an order or send a message.',
        inputSchema: {type: 'object', properties: {query: {type: 'string', minLength: 1, maxLength: 200}}, required: ['query'], additionalProperties: false},
        annotations: {readOnlyHint: false, untrustedContentHint: false},
        execute: async (input) => {
          if (!input || typeof input.query !== 'string' || !input.query.trim() || input.query.length > 200 || Object.keys(input).some((k) => k !== 'query')) throw new Error('Provide a search query between 1 and 200 characters.');
          closeMenu(); if (!dialog.open) dialog.showModal(); searchInput.value = input.query; return await search(input.query);
        }
      }, {signal: lifecycle.signal})).catch(() => {});
      window.addEventListener('pagehide', () => lifecycle.abort(), {once: true});
    } catch { /* Unsupported browsers keep the same standard interface. */ }
  }
})();
