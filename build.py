#!/usr/bin/env python3
"""Сборка статического сайта из content/*.yml в dist/.

  pip install -r requirements.txt
  python3 build.py

Данные:   content/site.yml (главная), content/vessels/*.yml (суда)
Статика:  static/ (style.css, main.js, images/) — копируется в dist/
Админка:  admin/ (Decap CMS) — копируется в dist/admin/
"""
import html, json, os, re, shutil, sys
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, 'dist')


# ---------- helpers ----------
def load(path):
    with open(os.path.join(ROOT, path), encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def esc(s):
    return html.escape('' if s is None else str(s), quote=True)

def ru(v):
    if isinstance(v, dict):
        return '' if v.get('ru') is None else str(v.get('ru'))
    return '' if v is None else str(v)

def en(v):
    """EN-значение; пустое = как RU."""
    if isinstance(v, dict):
        return str(v.get('en') or '') or ru(v)
    return '' if v is None else str(v)

def T(v, tag='span', cls=None, attrs=''):
    """Элемент с RU-текстом и data-en (если EN отличается). «[...]» = заглушка (.ph)."""
    r, e = str(ru(v) or ''), str(en(v) or '')
    classes = [c for c in [cls, 'ph' if str(r).startswith('[') else None] if c]
    a = f' class="{" ".join(classes)}"' if classes else ''
    if e and e != r:
        a += f' data-en="{esc(e)}"'
    return f'<{tag}{a}{attrs}>{esc(r)}</{tag}>'

def img_path(p, prefix):
    """'/images/x.jpg' -> 'images/x.jpg' (главная) или '../images/x.jpg' (страницы судов)."""
    p = (p or '').strip()
    if re.match(r'^(https?:)?//', p):
        return p
    return prefix + p.lstrip('/')


# ---------- data ----------
site = load('content/site.yml')
vessels = []
vdir = os.path.join(ROOT, 'content', 'vessels')
for fn in sorted(os.listdir(vdir)):
    if fn.endswith(('.yml', '.yaml')):
        v = load(os.path.join('content', 'vessels', fn))
        v.setdefault('slug', os.path.splitext(fn)[0])
        if not re.fullmatch(r'[a-z0-9-]+', v['slug']):
            sys.exit(f'Ошибка: slug "{v["slug"]}" в {fn} — только латиница, цифры и дефис')
        vessels.append(v)
vessels.sort(key=lambda v: (v.get('order') is None, v.get('order') or 0, v['slug']))

P = site['person']
M = site['meta']

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230b1d3a'/%3E%3Cg stroke='%23d4a64a' stroke-width='4' fill='none' stroke-linecap='round'%3E%3Ccircle cx='32' cy='32' r='14'/%3E%3Cpath d='M32 8v48M8 32h48M15 15l34 34M49 15L15 49'/%3E%3C/g%3E%3Ccircle cx='32' cy='32' r='5' fill='%23d4a64a'/%3E%3C/svg%3E")
WHEEL = ('<svg viewBox="0 0 64 64" width="28" height="28" aria-hidden="true"><g stroke="currentColor" stroke-width="4" fill="none" stroke-linecap="round">'
         '<circle cx="32" cy="32" r="14"/><path d="M32 8v48M8 32h48M15 15l34 34M49 15L15 49"/></g><circle cx="32" cy="32" r="5" fill="currentColor"/></svg>')


def head_common(prefix):
    return f'''  <meta name="theme-color" content="#0b1d3a">
  <link rel="icon" type="image/svg+xml" href="{FAVICON}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap&subset=cyrillic" rel="stylesheet">
  <link rel="stylesheet" href="{prefix}style.css">'''


def header(home):
    """home = '' для главной, '../index.html' для страниц судов."""
    N = site['nav']
    links = [('about', 'about'), ('qualifications', 'education'), ('experience', 'experience'),
             ('vessels', 'vessels'), ('route', 'route'), ('contact', 'contact')]
    lis = '\n'.join(f'          <li>{T(N[k], "a", attrs=f" href=\"{home}#{a}\"")}</li>' for a, k in links)
    top = f' id="top"' if not home else ''
    brand_href = '#top' if not home else home
    return f'''  <header class="nav"{top}>
    <div class="container nav__inner">
      <a href="{brand_href}" class="nav__brand" aria-label="На главную">
        {WHEEL}
        {T(P['brand'])}
      </a>
      <nav aria-label="Основное меню">
        <ul class="nav__links">
{lis}
        </ul>
      </nav>
      <button class="lang-toggle" id="langToggle" type="button" aria-label="Switch to English">EN</button>
    </div>
  </header>'''


def footer():
    return f'''  <footer class="footer">
    <div class="container">
      <p>© <span id="year"></span> {T(P['name'])} · {T(P['job_title'])}</p>
    </div>
  </footer>'''


def section_head(d, sub_key=None):
    sub = f'\n          {T(d[sub_key], "p", "section__sub")}' if sub_key and d.get(sub_key) else ''
    return f'''        <div class="section__head reveal">
          {T(d['eyebrow'], 'p', 'eyebrow')}
          {T(d['heading'], 'h2')}{sub}
        </div>'''


# ---------- index ----------
def render_index():
    H, A, E, X = site['hero'], site['about'], site['education'], site['experience']
    V, S, R, C = site['vessels_section'], site['skills'], site['route'], site['contact']

    stats = '\n'.join(f'          <li>{T(s["value"], "strong")}{T(s["label"])}</li>' for s in A['stats'])
    paras = '\n'.join(f'        {T(p, "p")}' for p in A['paragraphs'])

    cards = []
    for it in E['items']:
        cards.append(f'''          <article class="card reveal">
            <div class="card__icon" aria-hidden="true">{esc(it.get('icon') or '⚓')}</div>
            <p class="card__date">{esc(it['years'])}</p>
            {T(it['title'], 'h3')}
            {T(it['specialization'], 'p')}
            {T(it['institution'], 'p', 'card__meta')}
          </article>''')
    cert = E.get('certificates')
    if cert:
        cards.append(f'''          <article class="card card--todo reveal">
            <div class="card__icon" aria-hidden="true">✎</div>
            {T(cert['date'], 'p', 'card__date')}
            {T(cert['title'], 'h3')}
            {T(cert['text'], 'p')}
          </article>''')

    tl = '\n'.join(f'''          <li class="timeline__item reveal">
            {T(it['dates'], 'span', 'timeline__date')}
            {T(it['title'], 'h3')}
            {T(it['text'], 'p')}
          </li>''' for it in X['items'])

    slides = []
    for v in vessels:
        pos = f' style="object-position:{esc(v["thumb_pos"])}"' if v.get('thumb_pos') else ''
        alt = f"{v['name']} — {ru(v['type'])}"
        name = {'ru': v['name'], 'en': v.get('name_en') or ''}
        slides.append(f'''            <a class="vslide" href="vessels/{v['slug']}.html">
              <div class="vslide__media"><img src="{esc(img_path(v.get('photo'), ''))}" alt="{esc(alt)}" loading="lazy" width="1200" height="900"{pos}></div>
              <div class="vslide__info">
                {T(name, 'h3', 'vslide__name')}
                <dl class="vslide__facts">
                  <div><dt data-i18n="vp.type">Тип</dt><dd>{T(v['type'])}</dd></div>
                  <div><dt data-i18n="vp.company">Компания</dt><dd>{T(v.get('company'))}</dd></div>
                  <div><dt data-i18n="vp.position">Должность</dt><dd>{T(v.get('position'))}</dd></div>
                  <div><dt data-i18n="vp.period">Период</dt><dd>{T(v.get('period'))}</dd></div>
                </dl>
                <span class="vslide__more" data-i18n="vp.more">Подробнее →</span>
              </div>
            </a>''')

    def skill_list(block, cls=''):
        c = f' class="{cls}"' if cls else ''
        return f'<ul{c}>\n' + '\n'.join(f'              {T(i, "li")}' for i in block['items']) + '\n            </ul>'

    areas = '\n'.join(f'            <li>{T(a["name"], "strong")} · {T(a.get("ports"))}</li>' for a in R['areas'])
    route_map = open(os.path.join(ROOT, 'templates', 'route-map.html'), encoding='utf-8').read()
    route_map = re.sub(r'^<!--.*?-->\n', '', route_map, flags=re.S).rstrip('\n')

    phone = (P.get('phone') or '').strip()
    phone_html = (f'\n        <p class="phone"><a href="tel:{esc(re.sub(r"[^0-9+]", "", phone))}">☎ {esc(phone)}</a></p>'
                  if phone else '')
    socials = '\n'.join(
        f'          <li><a href="{esc(s.get("url") or "#")}" aria-label="{esc(s["name"])}">{esc(s["name"])} {T(s.get("handle") or "")}</a></li>'
        for s in C.get('socials') or [])

    edu_names = [ru(it['institution']) for it in E['items']]
    ld = {"@context": "https://schema.org", "@type": "Person", "name": ru(P['name']), "alternateName": en(P['name']),
          "jobTitle": ru(P['job_title'])}
    if P.get('works_for'):
        ld["worksFor"] = {"@type": "Organization", "name": P['works_for']}
    ld["email"] = "mailto:" + P['email']
    if P.get('language_codes'):
        ld["knowsLanguage"] = P['language_codes']
    ld["alumniOf"] = [{"@type": "CollegeOrUniversity", "name": n} for n in edu_names]

    return f'''<!DOCTYPE html>
<!-- Сгенерировано build.py из content/*.yml — правьте данные там (или через /admin). -->
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(M['title'])}</title>
  <meta name="description" content="{esc(M['description'])}">
  <meta name="author" content="{esc(ru(P['name']))}">
  <meta property="og:type" content="profile">
  <meta property="og:title" content="{esc(M.get('og_title') or M['title'])}">
  <meta property="og:description" content="{esc(M.get('og_description') or M['description'])}">
  <meta property="og:locale" content="ru_RU">
  <meta property="og:locale:alternate" content="en_US">
  <meta property="og:url" content="{esc(M.get('og_url', ''))}">
  <meta property="og:image" content="{esc(M.get('og_image', ''))}">
  <meta name="twitter:card" content="summary">
{head_common('')}
  <script type="application/ld+json">
  {json.dumps(ld, ensure_ascii=False, separators=(',', ':'))}
  </script>
</head>
<body>
  <a class="skip-link" href="#main" data-i18n="skip">Перейти к содержанию</a>

{header('')}

  <main id="main">
    <section class="hero">
      <div class="hero__waves" aria-hidden="true">
        <svg viewBox="0 0 1440 120" preserveAspectRatio="none"><path d="M0 60 C 240 110 480 10 720 60 S 1200 110 1440 60 V120 H0Z" fill="#f7f4ec"/></svg>
      </div>
      <div class="container hero__inner">
        <div class="hero__text reveal">
          {T(H['eyebrow'], 'p', 'eyebrow')}
          {T(P['name'], 'h1')}
          {T(H['title'], 'p', 'hero__title')}
          {T(H['lead'], 'p', 'hero__lead')}
          <div class="hero__cta">
            {T(H['cta_contact'], 'a', 'btn btn--gold', ' href="#contact"')}
            {T(H['cta_experience'], 'a', 'btn btn--ghost', ' href="#experience"')}
          </div>
        </div>
        <div class="hero__photo reveal">
          <img src="{esc(img_path(P['photo'], ''))}" alt="{esc(ru(P['name']))}" class="photo" width="207" height="281">
        </div>
      </div>
    </section>

    <section class="section" id="about">
      <div class="container narrow reveal">
        {T(A['eyebrow'], 'p', 'eyebrow')}
        {T(A['heading'], 'h2')}
{paras}
        <ul class="stats">
{stats}
        </ul>
      </div>
    </section>

    <section class="section section--navy" id="qualifications">
      <div class="container">
{section_head(E)}
        <div class="cards">
{chr(10).join(cards)}
        </div>
      </div>
    </section>

    <section class="section" id="experience">
      <div class="container narrow">
{section_head(X)}
        <ol class="timeline">
{tl}
        </ol>
      </div>
    </section>

    <section class="section section--navy" id="vessels">
      <div class="container">
{section_head(V, 'subtitle')}
        <div class="carousel reveal" role="region" aria-roledescription="carousel" aria-label="{esc(ru(V['heading']))}">
          <div class="carousel__track" tabindex="0">
{chr(10).join(slides)}
          </div>
          <div class="carousel__controls">
            <button type="button" class="carousel__btn carousel__prev" aria-label="Назад">&#8249;</button>
            <div class="carousel__dots" role="tablist"></div>
            <button type="button" class="carousel__btn carousel__next" aria-label="Вперёд">&#8250;</button>
          </div>
        </div>
      </div>
    </section>

    <section class="section section--sand" id="skills">
      <div class="container">
{section_head(S)}
        <div class="skills">
          <div class="skill reveal">
            {T(S['professional']['title'], 'h3')}
            {skill_list(S['professional'])}
          </div>
          <div class="skill reveal">
            {T(S['qualities']['title'], 'h3')}
            {skill_list(S['qualities'], 'tags')}
          </div>
          <div class="skill reveal">
            {T(S['languages']['title'], 'h3')}
            {skill_list(S['languages'])}
            {T(S['hobby']['title'], 'h3', 'skill__h2')}
            {skill_list(S['hobby'])}
          </div>
        </div>
      </div>
    </section>

    <section class="section section--navy" id="route">
      <div class="container">
{section_head(R, 'subtitle')}
        <figure class="route reveal">
{route_map}
          <ul class="areas-list">
{areas}
          </ul>
          {T(R['caption'], 'figcaption')}
        </figure>
      </div>
    </section>

    <section class="section" id="contact">
      <div class="container narrow center reveal">
        {T(C['eyebrow'], 'p', 'eyebrow')}
        {T(C['heading'], 'h2')}
        {T(C['text'], 'p')}
        <a class="btn btn--gold btn--lg" href="mailto:{esc(P['email'])}">✉ {esc(P['email'])}</a>{phone_html}
        <ul class="socials">
{socials}
        </ul>
      </div>
    </section>
  </main>

{footer()}

  <script src="main.js"></script>
</body>
</html>
'''


# ---------- vessel pages ----------
LIGHTBOX = '''  <div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Просмотр фото" hidden>
    <button type="button" class="lightbox__btn lightbox__close" aria-label="Закрыть (Esc)">&times;</button>
    <button type="button" class="lightbox__btn lightbox__prev" aria-label="Предыдущее фото">&#8249;</button>
    <figure class="lightbox__figure">
      <img class="lightbox__img" alt="">
      <figcaption class="lightbox__caption"><strong class="lightbox__title"></strong><span class="lightbox__meta"></span><span class="lightbox__count"></span></figcaption>
    </figure>
    <button type="button" class="lightbox__btn lightbox__next" aria-label="Следующее фото">&#8250;</button>
  </div>'''


def render_vessel(i, v):
    n = len(vessels)
    prev_v = vessels[i - 1] if i > 0 else None
    next_v = vessels[i + 1] if i < n - 1 else None
    name = {'ru': v['name'], 'en': v.get('name_en') or ''}
    name_en = v.get('name_en') or v['name']
    photo = img_path(v.get('photo'), '../')
    meta_ru = f"{ru(v['type'])} · {ru(v['position'])} · {ru(v['period'])}"
    meta_en = f"{en(v['type'])} · {en(v['position'])} · {en(v['period'])}"

    contracts = []
    for c in v.get('contracts') or []:
        port = ''
        if ru(c.get('port')):
            port = f' <span class="contract__port">· <span data-i18n="vp.engaged">приём на судно:</span> {T(c["port"])}</span>'
        contracts.append(f'                  <li>{T(c["dates"])}{port}</li>')
    rows = [
        f'<div><dt data-i18n="vp.type">Тип</dt><dd>{T(v["type"])}</dd></div>',
        f'<div><dt data-i18n="vp.company">Судовладелец / компания</dt><dd>{T(v.get("company"))}</dd></div>',
        f'<div><dt data-i18n="vp.position">Должность</dt><dd>{T(v.get("position"))}</dd></div>',
        '<div><dt data-i18n="vp.periods">Периоды работы</dt><dd><ul class="contracts">\n' + '\n'.join(contracts) + '\n                </ul></dd></div>',
        f'<div><dt data-i18n="vp.area">Район плавания</dt><dd>{T(v.get("area"))}</dd></div>',
    ]
    if ru(v.get('marking')):
        rows.append(f'<div><dt data-i18n="vp.marking">Маркировка на борту (по фото)</dt><dd>{T(v["marking"])}</dd></div>')
    rows_html = '\n                '.join(rows)

    def link(o, cls, key, label):
        if not o:
            return '<span></span>'
        return (f'<a class="vnav__link {cls}" href="{o["slug"]}.html"><small data-i18n="{key}">{label}</small>'
                f'{T({"ru": o["name"], "en": o.get("name_en") or ""}, "strong")}</a>')

    desc = v.get('description') or {'ru': '[Описание судна, по желанию]', 'en': '[Vessel description, optional]'}
    return f'''<!DOCTYPE html>
<!-- Страница судна. Сгенерировано build.py из content/vessels/{v['slug']}.yml — правьте данные там. -->
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(v['name'])} — {esc(ru(v['type']))} · {esc(ru(P['name']))}, {esc(ru(P['job_title']).lower())}</title>
  <meta name="description" content="{esc(v['name'])}: {esc(ru(v['type']))}, {esc(ru(v['company']))}. {esc(ru(v['position']))} — {esc(ru(v['period']))}. {esc(ru(P['name']))}.">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{esc(v['name'])} — {esc(ru(P['name']))}, {esc(ru(P['job_title']).lower())}">
  <meta property="og:description" content="{esc(meta_ru)}">
{head_common('../')}
</head>
<body>
  <a class="skip-link" href="#main" data-i18n="skip">Перейти к содержанию</a>

{header('../index.html')}

  <main id="main">
    <section class="vpage section--navy">
      <div class="container">
        <a class="vpage__back" href="../index.html#vessels" data-i18n="vp.back">← Все суда</a>
        <div class="vpage__grid">
          <button type="button" class="vpage__photo js-lightbox" data-full="{esc(photo)}"
                  data-title="{esc(v['name'])}" data-title-en="{esc(name_en)}" data-meta="{esc(meta_ru)}" data-meta-en="{esc(meta_en)}"
                  aria-label="Открыть фото в полном размере">
            <img src="{esc(photo)}" alt="{esc(v['name'])} — {esc(ru(v['type']))}">
            <span class="vpage__zoom" aria-hidden="true">⤢</span>
          </button>
          <div class="vpage__info">
            <p class="eyebrow">{T(v['type'])}</p>
            {T(name, 'h1', 'vpage__name')}
            <dl class="vfacts">
                {rows_html}
            </dl>
          </div>
        </div>
      </div>
    </section>

    <section class="section vpage__desc">
      <div class="container narrow">
        <h2 data-i18n="vp.about">О судне</h2>
        {T(desc, 'p')}
        <nav class="vnav" aria-label="Другие суда">
          {link(prev_v, 'vnav__prev', 'vp.prev', '← Предыдущее')}
          <a class="vnav__all" href="../index.html#vessels" data-i18n="vp.back">← Все суда</a>
          {link(next_v, 'vnav__next', 'vp.next', 'Следующее →')}
        </nav>
      </div>
    </section>
  </main>

{footer()}

{LIGHTBOX}

  <script src="../main.js"></script>
</body>
</html>
'''


def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    shutil.copytree(os.path.join(ROOT, 'static'), DIST)
    shutil.copytree(os.path.join(ROOT, 'admin'), os.path.join(DIST, 'admin'))
    with open(os.path.join(DIST, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(render_index())
    os.makedirs(os.path.join(DIST, 'vessels'), exist_ok=True)
    for i, v in enumerate(vessels):
        with open(os.path.join(DIST, 'vessels', v['slug'] + '.html'), 'w', encoding='utf-8') as f:
            f.write(render_vessel(i, v))
    # проверка: все фото на месте
    missing = [v['photo'] for v in vessels
               if v.get('photo') and not re.match(r'^(https?:)?//', v['photo'])
               and not os.path.exists(os.path.join(DIST, v['photo'].lstrip('/')))]
    if missing:
        sys.exit('Ошибка: нет файлов фото: ' + ', '.join(missing))
    print(f'OK: dist/index.html + {len(vessels)} страниц судов')


if __name__ == '__main__':
    main()
