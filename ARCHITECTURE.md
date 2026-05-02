# KUR OFF — Архитектура проекта

## Стек
- **Backend**: FastAPI + SQLAlchemy async + SQLite (aiosqlite)
- **Bot**: Aiogram 3.x + FSM (MemoryStorage)
- **Шаблоны**: Jinja2 (server-side render каталога)
- **PDF**: Playwright (Chromium headless)
- **Деплой**: VPS/Linux + systemd

---

## Структура проекта

```
kuroff-catalog/
├── app/
│   ├── main.py                # FastAPI app, монтирует роутеры + StaticFiles
│   ├── config.py              # Settings: BOT_TOKEN, ALLOWED_USER_IDS, DB_PATH, BASE_URL
│   ├── database.py            # Async engine, сессии, Base, init_db()
│   │
│   ├── models/
│   │   ├── category.py        # ORM модель Category
│   │   ├── product.py         # ORM модель Product
│   │   └── spec.py            # ORM модель ProductSpec
│   │
│   ├── schemas/
│   │   ├── category.py        # Pydantic: CategoryCreate / CategoryOut / CategoryUpdate
│   │   └── product.py         # Pydantic: ProductCreate / ProductOut / ProductUpdate + SpecItem
│   │
│   ├── crud/
│   │   ├── category.py        # Async DB операции для категорий
│   │   └── product.py         # Async DB операции для товаров + характеристик
│   │
│   ├── api/
│   │   ├── router.py          # Объединяет все APIRouter
│   │   ├── categories.py      # /api/categories CRUD
│   │   └── products.py        # /api/products CRUD + загрузка фото
│   │
│   ├── templates/
│   │   └── catalog.html       # Jinja2-версия catalog.html (данные из БД)
│   │
│   └── static/
│       └── images/            # Загруженные фото товаров/категорий
│
├── bot/
│   ├── main.py                # Aiogram bot + dispatcher
│   ├── middlewares.py         # Auth: проверка user_id по allowlist
│   │
│   ├── handlers/
│   │   ├── start.py           # /start, /help, главное меню
│   │   ├── category.py        # Управление категориями
│   │   └── product.py         # Управление товарами (FSM)
│   │
│   ├── states/
│   │   ├── product_states.py  # FSM состояния ProductForm
│   │   └── category_states.py # FSM состояния CategoryForm
│   │
│   ├── keyboards/
│   │   ├── main_menu.py       # ReplyKeyboard: Категории | Товары | Сгенерировать PDF
│   │   ├── category_kb.py     # Inline клавиатуры для категорий
│   │   └── product_kb.py      # Inline клавиатуры для товаров + пагинация
│   │
│   └── services/
│       ├── api_client.py      # httpx AsyncClient → вызывает FastAPI
│       └── pdf_generator.py   # Playwright: /catalog → PDF bytes → бот отправляет файл
│
├── runner.py                  # asyncio.gather(uvicorn, bot polling) — одна точка запуска
├── requirements.txt
├── .env                       # BOT_TOKEN, ALLOWED_USER_IDS, BASE_URL
├── kuroff.db                  # SQLite (создаётся при первом запуске)
└── systemd/
    └── kuroff.service         # systemd unit для автостарта на VPS
```

---

## Модели данных

### Category
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | |
| name | TEXT | "КУРИНАЯ ПРОДУКЦИЯ" |
| slug | TEXT UNIQUE | "chicken" |
| icon_path | TEXT NULL | "images/chicken.png" |
| sort_order | INTEGER | порядок отображения |
| created_at | DATETIME | |

### Product
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | |
| category_id | INTEGER FK | → categories.id CASCADE |
| title | TEXT | "ТУШКА КУРИНАЯ" (всегда заглавные) |
| description | TEXT | |
| price | REAL | |
| price_unit | TEXT | "/ КГ" по умолчанию |
| image_path | TEXT NULL | локальный файл в /static/images/ |
| icon_name | TEXT NULL | phosphor icon: "ph-fish-simple" |
| sort_order | INTEGER | |
| is_active | BOOLEAN | скрыть без удаления |
| created_at / updated_at | DATETIME | |

*Заполнено ровно одно из `image_path` / `icon_name`.*

### ProductSpec
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | |
| product_id | INTEGER FK | → products.id CASCADE |
| label | TEXT | "[ ВЕС ]" |
| value | TEXT | "1.6–2.2 КГ" |
| sort_order | INTEGER | |

---

## API эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Редирект → `/catalog` |
| GET | `/catalog` | Jinja2 HTML каталог (A4, print-ready) |
| GET | `/api/categories` | Список категорий |
| POST | `/api/categories` | Создать категорию |
| PATCH | `/api/categories/{id}` | Обновить категорию |
| DELETE | `/api/categories/{id}` | Удалить (каскад на товары) |
| GET | `/api/products` | Список товаров (`?category_id=`, `?active_only=true`) |
| POST | `/api/products` | Создать товар (JSON + характеристики) |
| GET | `/api/products/{id}` | Один товар с характеристиками |
| PATCH | `/api/products/{id}` | Обновить поля товара |
| DELETE | `/api/products/{id}` | Удалить товар |
| POST | `/api/products/{id}/image` | Загрузить фото (multipart) |
| DELETE | `/api/products/{id}/image` | Удалить фото |
| GET | `/static/images/{filename}` | Отдать загруженное изображение |

---

## Бот — сценарии (FSM)

### Auth
`middlewares.py` проверяет `user_id` по `ALLOWED_USER_IDS`. Чужие — тихий ignore.

### Главное меню (`/start`)
```
[ Категории ]  [ Товары ]  [ Сгенерировать PDF ]
```
- **Сгенерировать PDF** → Playwright рендерит `/catalog` → бот отправляет `.pdf` файл в чат

### FSM: CategoryForm
```
waiting_name → waiting_icon
```
Название → фото иконки (или "пропустить") → POST /api/categories

### FSM: ProductForm
```
waiting_category → waiting_title → waiting_description →
waiting_specs → waiting_price → waiting_price_unit →
waiting_image → confirm
```
- Характеристики: пользователь шлёт строки `МЕТКА: ЗНАЧЕНИЕ`, накапливает до "готово"
- Фото: загрузка фото ИЛИ текст иконки ИЛИ "пропустить"
- Экран подтверждения: сводка + [Сохранить] [Отмена]
- Редактирование: тот же FSM, данные подгружаются из GET /api/products/{id}, шлёт PATCH

### Быстрые операции (без полного FSM)
- **[Цена]** → один промпт → PATCH price
- **[Фото]** → загрузка фото → POST image
- **[Скрыть/Показать]** → PATCH is_active

---

## Интеграция каталога

`catalog.html` → `app/templates/catalog.html` (Jinja2):

```jinja2
{% for category in categories %}
<div class="page">
  {% for product in category.products if product.is_active %}
  <div class="prod-block">
    {% if product.image_path %}
      <img src="/static/{{ product.image_path }}">
    {% else %}
      <i class="ph-light {{ product.icon_name }}"></i>
    {% endif %}
    <h3>{{ product.title }}</h3>
    <div class="prod-desc">{{ product.description }}</div>
    <table>
      {% for spec in product.specs %}
      <tr><td>{{ spec.label }}</td><td>{{ spec.value }}</td></tr>
      {% endfor %}
    </table>
    <div class="price">{{ product.price }} ₸<span>{{ product.price_unit }}</span></div>
  </div>
  {% endfor %}
</div>
{% endfor %}
```

`window.print()` убран — PDF генерирует Playwright.

---

## PDF генерация (`bot/services/pdf_generator.py`)

1. Playwright запускает Chromium (headless)
2. Открывает `http://localhost:8000/catalog`
3. Ждёт `networkidle` (загрузка шрифтов)
4. `page.pdf(format="A4", print_background=True)` → bytes
5. Бот: `send_document(chat_id, BufferedInputFile(pdf_bytes, "kuroff-catalog.pdf"))`

---

## Деплой (VPS)

### Первый запуск
```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env        # вписать BOT_TOKEN, ALLOWED_USER_IDS, BASE_URL
python runner.py             # создаёт kuroff.db, сидит 2 категории + 6 товаров
```

### runner.py
```python
async def main():
    await init_db()          # создать таблицы + seed если БД пустая
    server = uvicorn.Server(Config("app.main:app", host="0.0.0.0", port=8000))
    await asyncio.gather(
        server.serve(),
        dp.start_polling(bot),
    )
```

### Автостарт (systemd)
```bash
sudo systemctl enable kuroff
sudo systemctl start kuroff
```

---

## Зависимости

```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
aiosqlite
aiogram>=3.0
httpx
jinja2
aiofiles
python-multipart
playwright
python-dotenv
```
