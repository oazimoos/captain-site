# Сайт-портфолио капитана Олега Ерулевича

Одностраничный сайт (RU/EN) + отдельные страницы судов. Статический: HTML, CSS и немного JS,
без фреймворков. Контент хранится в YAML и редактируется либо в файлах, либо через
админку Decap CMS по адресу `/admin`.

## Структура

```
content/
  site.yml              — тексты главной: первый экран, «Обо мне», образование, опыт,
                          навыки, районы плавания, контакты, соцсети, SEO
  vessels/<slug>.yml    — по одному файлу на судно (карусель + страница vessels/<slug>.html)
static/                 — копируется в dist/ как есть
  style.css, main.js
  images/photo.jpg
  images/vessels/*.jpg  — фото судов
templates/route-map.html — схема районов плавания (SVG, статичная)
admin/                  — Decap CMS (index.html + config.yml), копируется в dist/admin/
build.py                — сборка: content/ + static/ → dist/
requirements.txt        — PyYAML
netlify.toml            — настройки сборки на Netlify
```

## Локальная сборка

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 build.py            # результат — в dist/
python3 -m http.server -d dist 8000   # открыть http://localhost:8000
```

## Как править контент

Все тексты — парами `ru` / `en`. Пустой `en` означает «как в RU».
Значения в квадратных скобках (`[компания]`, `[уточнить]` …) — заглушки:
на сайте они видны приглушённым курсивом, их нужно заменить.

**Суда** (`content/vessels/*.yml`):

| Поле | Что это |
|---|---|
| `order` | место в карусели (меньше = раньше; шаг 10) |
| `slug` | адрес страницы: `plutus` → `vessels/plutus.html` (латиница, цифры, дефис) |
| `name`, `name_en` | название RU / EN |
| `type`, `company`, `position`, `period` | тип, компания, должность, краткий период для карточки |
| `contracts` | список контрактов: `dates` (точные даты), `port` (порт приёма на судно, можно пусто) |
| `area` | район плавания |
| `photo` | `/images/vessels/<файл>.jpg` (≈1600 px по ширине, до ~400 КБ) |
| `thumb_pos` | кадрирование карточки, CSS `object-position`, напр. `90% 50%` |
| `marking` | маркировка на борту (по фото), можно пусто |
| `description` | описание судна |
| `note` | служебная заметка, на сайте не показывается |

Добавить судно — создать новый файл `content/vessels/<slug>.yml` (скопировать любой) и
положить фото в `static/images/vessels/`. Удалить — удалить файл.

Служебные подписи интерфейса («Тип», «← Все суда» …) и подписи на схеме — в `static/main.js` (объект `EN`).

## Админка (Decap CMS) — что нужно настроить

Админка открывается по адресу `https://<сайт>/admin/`, вход — через GitHub-аккаунт с доступом
к репозиторию `oazimoos/captain-site`. Изменения сохраняются коммитами в ветку `main`,
Netlify после этого сам пересобирает сайт.

**Перед первым входом нужно один раз настроить авторизацию:**

1. Подключить репозиторий к Netlify (Add new site → Import from Git → GitHub →
   `oazimoos/captain-site`). Настройки сборки подтянутся из `netlify.toml`.
2. На GitHub создать OAuth App: Settings → Developer settings → OAuth Apps → New OAuth App
   - Homepage URL: адрес сайта на Netlify (например `https://<имя>.netlify.app`)
   - Authorization callback URL: `https://api.netlify.com/auth/done`
   - сохранить **Client ID** и сгенерировать **Client Secret**.
3. В Netlify: Site configuration → Access & security → OAuth → Authentication providers →
   Install provider → **GitHub**, вставить Client ID и Client Secret.
4. Открыть `https://<сайт>/admin/` и нажать «Войти через GitHub».

В `admin/config.yml` `base_url` не указан — используется Netlify (`api.netlify.com`).

Для правки без интернета-авторизации можно запустить локально:
`npx decap-server` в корне репозитория и добавить `local_backend: true` в `admin/config.yml`
(только локально, не коммитить).

## Что ещё не заполнено

- рабочие дипломы и сертификаты (категория диплома капитана, ADN, радар …);
- ссылки на соцсети;
- телефон (по желанию: поле `person.phone`, пусто = не показывается);
- `meta.og_url` и `meta.og_image` — после появления адреса сайта;
- суда БАШТАНСЬКИЙ и ОМ-101: компания, должность, период (см. поле `note`).

## Важно

- Не публиковать на сайте домашний адрес, дату рождения, семейное положение и номера документов.
- Часть фото судов взята с fleetphoto.ru / MarineTraffic (водяные знаки сохранены).
  Это чужие снимки: при необходимости получите разрешение авторов или замените своими.
