// ===== Появление блоков при прокрутке =====
(function () {
  var items = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    items.forEach(function (el) { el.classList.add('is-visible'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    items.forEach(function (el) { io.observe(el); });
  }
  document.getElementById('year').textContent = new Date().getFullYear();
})();

// ===== Переключатель RU / EN =====
// Переводы служебных подписей (интерфейс). Тексты контента переводятся через
// поля en в content/*.yml (атрибут data-en в HTML).
var EN = {
  "vp.type": "Type",
  "vp.company": "Shipowner / company",
  "vp.position": "Position",
  "vp.period": "Period",
  "vp.periods": "Periods of service",
  "vp.area": "Sailing area",
  "vp.engaged": "signed on in:",
  "vp.marking": "Hull markings (from photo)",
  "vp.more": "Details →",
  "vp.back": "← All vessels",
  "vp.about": "About the vessel",
  "vp.desc": "[Vessel description, optional]",
  "vp.prev": "← Previous",
  "vp.next": "Next →",
  "skip": "Skip to content",
  "route.danube": "Danube",
  "route.bug": "Southern Bug",
  "route.dnipro": "Dnipro",
  "route.sea": "Black Sea",
  "route.p.izmail": "Izmail",
  "route.p.chornomorsk": "Chornomorsk",
  "route.p.odesa": "Odesa",
  "route.p.yuzhny": "Pivdennyi",
  "route.p.ochakiv": "Ochakiv",
  "route.p.mykolaiv": "Mykolaiv",
  "route.p.kherson": "Kherson"
};
(function () {
  var btn = document.getElementById('langToggle');
  var nodes = document.querySelectorAll('[data-i18n]');
  var RU = {};
  nodes.forEach(function (n) { RU[n.getAttribute('data-i18n')] = n.textContent; });
  // Отдельные значения с атрибутом data-en="..." (например, тип судна)
  var enNodes = document.querySelectorAll('[data-en]');
  enNodes.forEach(function (n) { n.setAttribute('data-ru', n.textContent); });
  function apply(lang) {
    var dict = lang === 'en' ? EN : RU;
    nodes.forEach(function (n) { var k = n.getAttribute('data-i18n'); if (dict[k]) n.textContent = dict[k]; });
    enNodes.forEach(function (n) { n.textContent = n.getAttribute(lang === 'en' ? 'data-en' : 'data-ru'); });
    document.documentElement.lang = lang;
    document.dispatchEvent(new CustomEvent('langchange'));
    btn.textContent = lang === 'en' ? 'RU' : 'EN';
    btn.setAttribute('aria-label', lang === 'en' ? 'Переключить на русский' : 'Switch to English');
    try { localStorage.setItem('lang', lang); } catch (e) {}
  }
  var saved = 'ru';
  try { saved = localStorage.getItem('lang') || 'ru'; } catch (e) {}
  if (saved === 'en') apply('en');
  btn.addEventListener('click', function () { apply(document.documentElement.lang === 'en' ? 'ru' : 'en'); });
})();

// ===== Лайтбокс =====
// Открывается по клику на любой элемент .js-lightbox с атрибутами
// data-full (картинка), data-title / data-title-en, data-meta / data-meta-en.
(function () {
  var lb = document.getElementById('lightbox');
  if (!lb) return;
  var img = lb.querySelector('.lightbox__img');
  var title = lb.querySelector('.lightbox__title');
  var meta = lb.querySelector('.lightbox__meta');
  var count = lb.querySelector('.lightbox__count');
  var btnClose = lb.querySelector('.lightbox__close');
  var current = 0, lastFocus = null;

  function items() { return Array.prototype.slice.call(document.querySelectorAll('.js-lightbox')); }
  function attr(el, name) {
    var en = document.documentElement.lang === 'en' && el.getAttribute(name + '-en');
    return en || el.getAttribute(name) || '';
  }
  function show(i) {
    var list = items(); if (!list.length) return;
    current = (i + list.length) % list.length;
    var el = list[current];
    var thumb = el.querySelector('img');
    img.src = el.getAttribute('data-full') || (thumb && thumb.src) || '';
    img.alt = thumb ? thumb.alt : '';
    title.textContent = attr(el, 'data-title');
    meta.textContent = attr(el, 'data-meta');
    count.textContent = list.length > 1 ? (current + 1) + ' / ' + list.length : '';
    lb.classList.toggle('is-single', list.length < 2);
  }
  function open(i) {
    lastFocus = document.activeElement;
    lb.hidden = false; document.body.classList.add('lb-open');
    show(i); btnClose.focus();
  }
  function close() {
    lb.hidden = true; document.body.classList.remove('lb-open');
    if (lastFocus) lastFocus.focus();
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('.js-lightbox');
    if (b) { e.preventDefault(); open(items().indexOf(b)); }
  });
  btnClose.addEventListener('click', close);
  lb.querySelector('.lightbox__prev').addEventListener('click', function () { show(current - 1); });
  lb.querySelector('.lightbox__next').addEventListener('click', function () { show(current + 1); });
  lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
  document.addEventListener('langchange', function () { if (!lb.hidden) show(current); });
  document.addEventListener('keydown', function (e) {
    if (lb.hidden) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') show(current - 1);
    else if (e.key === 'ArrowRight') show(current + 1);
    else if (e.key === 'Tab') {
      var f = Array.prototype.filter.call(lb.querySelectorAll('button'), function (x) { return x.offsetParent !== null; });
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  var x0 = null, y0 = null;
  lb.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
  lb.addEventListener('touchend', function (e) {
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) show(current + (dx < 0 ? 1 : -1));
    else if (dy > 90 && Math.abs(dy) > Math.abs(dx)) close();
    x0 = y0 = null;
  }, { passive: true });
})();

// ===== Карусель «Мои суда» =====
// Прокрутка — нативная (scroll-snap), поэтому свайп работает сам.
// Стрелки, точки, клавиши ←/→, медленный автоплей с паузой при наведении/фокусе/касании.
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.carousel').forEach(function (c) {
    var track = c.querySelector('.carousel__track');
    var slides = Array.prototype.slice.call(track.children);
    var dotsWrap = c.querySelector('.carousel__dots');
    var dots = [], paused = false, touchPause = null, timer = null;
    if (!slides.length) return;

    function step() { return slides.length > 1 ? slides[1].offsetLeft - slides[0].offsetLeft : track.clientWidth; }
    function maxScroll() { return track.scrollWidth - track.clientWidth; }
    function pages() { return Math.max(1, Math.ceil((maxScroll() - 2) / step()) + 1); }
    function index() {
      if (track.scrollLeft >= maxScroll() - 2) return pages() - 1;
      return Math.round(track.scrollLeft / step());
    }
    function go(i) {
      var p = pages(); i = (i + p) % p;
      track.scrollTo({ left: Math.min(i * step(), maxScroll()), behavior: reduce ? 'auto' : 'smooth' });
    }
    function buildDots() {
      var p = pages();
      if (dots.length === p) return;
      dotsWrap.innerHTML = ''; dots = [];
      for (var i = 0; i < p; i++) {
        var d = document.createElement('button');
        d.type = 'button'; d.className = 'carousel__dot'; d.setAttribute('role', 'tab');
        d.setAttribute('aria-label', (i + 1) + ' / ' + p);
        (function (k) { d.addEventListener('click', function () { go(k); }); })(i);
        dotsWrap.appendChild(d); dots.push(d);
      }
      update();
    }
    function update() {
      var i = index();
      dots.forEach(function (d, k) { d.classList.toggle('is-active', k === i); d.setAttribute('aria-selected', k === i); });
    }
    var raf = null;
    track.addEventListener('scroll', function () {
      if (raf) return; raf = requestAnimationFrame(function () { raf = null; update(); });
    }, { passive: true });
    window.addEventListener('resize', buildDots);
    c.querySelector('.carousel__prev').addEventListener('click', function () { go(index() - 1); });
    c.querySelector('.carousel__next').addEventListener('click', function () { go(index() + 1); });
    c.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { e.preventDefault(); go(index() - 1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); go(index() + 1); }
    });
    // автоплей
    c.addEventListener('mouseenter', function () { paused = true; });
    c.addEventListener('mouseleave', function () { paused = false; });
    c.addEventListener('focusin', function () { paused = true; });
    c.addEventListener('focusout', function () { paused = false; });
    track.addEventListener('touchstart', function () {
      paused = true; clearTimeout(touchPause);
      touchPause = setTimeout(function () { paused = false; }, 10000);
    }, { passive: true });
    if (!reduce) {
      timer = setInterval(function () {
        if (!paused && !document.hidden) go(index() + 1);
      }, 6000);
    }
    buildDots();
  });
})();
