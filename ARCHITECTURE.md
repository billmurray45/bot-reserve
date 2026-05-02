# KUR OFF — Архитектура проекта

## Стек
- **Backend**: FastAPI + SQLAlchemy async + PostgreSQL (asyncpg)
- **Bot**: Aiogram 3.x + FSM (MemoryStorage)
- **Шаблоны**: Jinja2 (server-side render каталога)
- **PDF**: Playwright (Chromium headless)
- **Деплой**: Docker Compose (PostgreSQL + App в одном compose)

---

## Структура проекта

```
kuroff-catalog/
├── app/
│   ├── main.py                # FastAPI app, монтирует роутеры + StaticFiles, build_pages()
│   ├── config.py              # Pydantic Settings: DATABASE_URL, BOT_TOKEN, ALLOWED_USER_IDS, BASE_URL
│   ├── database.py            # Async engine, AsyncSessionLocal, Base, init_db()
│   │
│   ├── models/
│   │   ├── category.py        # ORM: Category (id, name, slug, sort_order)
│   │   ├── product.py         # ORM: Product (id, category_id, title, description, price, price_unit, image_path, icon_name, sort_order, is_active)
│   │   └── spec.py            # ORM: ProductSpec (id, product_id, label, value, sort_order)
│   │
│   ├── schemas/
│   │   ├── category.py        # Pydantic: CategoryCreate / CategoryOut / CategoryUpdate
│   │   └── product.py         # Pydantic: ProductCreate / ProductOut / ProductUpdate + SpecItem
│   │
│   ├── crud/
│   │   ├── category.py        # Async DB операции для категорий
│   │   └── product.py         # Async DB операции для товаров + характеристик, set_image(), remove_image()
│   │
│   ├── api/
│   │   ├── router.py          # Объединяет все APIRouter под /api
│   │   ├── categories.py      # /api/categories CRUD
│   │   └── products.py        # /api/products CRUD + загрузка фото (Pillow compression)
│   │
│   ├── templates/
│   │   └── catalog.html       # Jinja2 A4 каталог, поддерживает ?show_prices=false
│   │
│   └── static/
│       └── images/            # Загруженные фото товаров (UUID имена, сжатые через Pillow)
│
├── bot/
│   ├── main.py                # Aiogram Bot + Dispatcher + AuthMiddleware
│   ├── middlewares.py         # AuthMiddleware: проверка user_id по ALLOWED_USER_IDS
│   │
│   ├── handlers/
│   │   ├── start.py           # /start, главное меню, генерация PDF (с ценами / без цен)
│   │   ├── category.py        # Управление категориями (список / добавить / переименовать / удалить)
│   │   └── product.py         # Управление товарами (FSM + быстрые операции)
│   │
│   ├── states/
│   │   ├── product_states.py  # ProductForm (8 состояний) + ProductQuick (price, photo)
│   │   └── category_states.py # CategoryForm (waiting_name)
│   │
│   ├── keyboards/
│   │   ├── main_menu.py       # ReplyKeyboard: Товары | Категории | PDF с ценами | PDF без цен
│   │   ├── category_kb.py     # Inline клавиатуры для категорий
│   │   └── product_kb.py      # Inline клавиатуры для товаров + пагинация (PAGE_SIZE=5)
│   │
│   └── services/
│       ├── api_client.py      # httpx AsyncClient → вызывает FastAPI на localhost:8000
│       └── pdf_generator.py   # Playwright: /catalog → PDF bytes, поддерживает show_prices param
│
├── migrations/                # Alembic async миграции
│   ├── env.py                 # Читает DATABASE_URL из settings, async режим
│   └── versions/              # Файлы миграций
│
├── runner.py                  # asyncio.gather(uvicorn, bot polling) — одна точка запуска
├── seed.py                    # Первичное заполнение БД (4 категории)
├── requirements.txt
├── Dockerfile                 # Python 3.12-slim + Playwright Chromium deps
├── docker-compose.yml         # Сервисы: db (PostgreSQL 16) + app
├── alembic.ini
├── .env                       # Локальные секреты (не в git)
└── .env.example               # Шаблон переменных окружения
```

---

## Модели данных

### Category
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | |
| name | TEXT | "ПТИЦА" |
| slug | TEXT UNIQUE | "ptitsa" |
| sort_order | INTEGER | порядок отображения |
| created_at | DATETIME | |

### Product
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | |
| category_id | INTEGER FK | → categories.id ON DELETE CASCADE |
| title | TEXT | "ТУШКА КУРИНАЯ" (всегда заглавные) |
| description | TEXT | |
| price | REAL | |
| price_unit | TEXT | "/ КГ" по умолчанию |
| image_path | TEXT NULL | UUID файл в /static/images/ |
| icon_name | TEXT NULL | phosphor icon: "ph-fish-simple" |
| sort_order | INTEGER | |
| is_active | BOOLEAN | скрыть без удаления |
| created_at / updated_at | DATETIME | |

*Заполнено одно из `image_path` / `icon_name`, либо ни одно.*

### ProductSpec
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | |
| product_id | INTEGER FK | → products.id ON DELETE CASCADE |
| label | TEXT | "ВЕС" |
| value | TEXT | "1.6–2.2 КГ" |
| sort_order | INTEGER | |

---

## API эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Редирект → `/catalog` |
| GET | `/catalog?show_prices=true` | Jinja2 HTML каталог (A4, print-ready) |
| GET | `/api/categories` | Список категорий |
| POST | `/api/categories` | Создать категорию |
| PATCH | `/api/categories/{id}` | Обновить категорию |
| DELETE | `/api/categories/{id}` | Удалить (каскад на товары) |
| GET | `/api/products` | Список товаров (`?category_id=`, `?active_only=true`) |
| POST | `/api/products` | Создать товар (JSON + характеристики) |
| GET | `/api/products/{id}` | Один товар с характеристиками |
| PATCH | `/api/products/{id}` | Обновить поля товара |
| DELETE | `/api/products/{id}` | Удалить товар |
| POST | `/api/products/{id}/image` | Загрузить фото (multipart, Pillow сжатие max 800px) |
| DELETE | `/api/products/{id}/image` | Удалить фото |
| GET | `/static/images/{filename}` | Отдать загруженное изображение |

---

## Бот — сценарии

### Auth
`AuthMiddleware` проверяет `user_id` по `ALLOWED_USER_IDS`. Чужие — тихий ignore.

### Главное меню (`/start`)
```
[ 📦 Товары ]      [ 🗂 Категории ]
[ 📄 PDF с ценами ] [ 📄 PDF без цен ]
```

### FSM: CategoryForm
```
waiting_name
```
Название → POST /api/categories (создать) или PATCH /api/categories/{id} (переименовать)

### FSM: ProductForm
```
waiting_title → waiting_description → waiting_specs →
waiting_price → waiting_price_unit → waiting_image → confirm
```
- Категория выбирается через inline кнопку до старта FSM
- Характеристики: строки `МЕТКА: ЗНАЧЕНИЕ`, накапливаются до "готово"
- Фото: загрузка фото ИЛИ текст иконки ИЛИ "пропустить"
- Confirm: сводка + [Сохранить] [Отмена]
- Редактирование: тот же FSM, данные из GET /api/products/{id}, шлёт PATCH

### Быстрые операции
- **[Цена]** → `ProductQuick.waiting_price` → один промпт → PATCH price
- **[Фото]** → `ProductQuick.waiting_photo` → загрузка → POST image
- **[Скрыть/Показать]** → PATCH is_active (без FSM)

---

## Пагинация каталога

`build_pages()` в `app/main.py` делит товары на страницы:
- Максимум 3 товара на странице (`PRODUCTS_PER_PAGE = 3`)
- Новая категория всегда начинается с новой страницы
- Страница с 1-2 товарами получает закрывающую линию снизу
- Фиксированная высота карточки: `91mm`

---

## PDF генерация

`bot/services/pdf_generator.py`:
1. Playwright запускает Chromium headless
2. Открывает `http://localhost:8000/catalog` (или `?show_prices=false`)
3. Ждёт `networkidle`
4. `page.pdf(format="A4", print_background=True)` → bytes
5. Бот отправляет `BufferedInputFile` в чат

---

## Деплой через Docker Compose

```bash
# Первый запуск
cp .env.example .env          # вписать секреты
docker compose up --build -d

# Миграции (один раз)
docker compose exec app alembic upgrade head

# Seed (один раз, опционально)
docker compose exec app python seed.py
```

### Контейнеры
| Сервис | Образ | Порт |
|--------|-------|------|
| db | postgres:16-alpine | ${DB_PORT}:5432 |
| app | ./Dockerfile | 8000:8000 |

- `app` зависит от `db` (healthcheck)
- `DATABASE_URL` внутри контейнера использует хост `db` (задан в compose `environment`)
- `app/static/images` смонтирован как volume — фото сохраняются между пересборками

---

## Переменные окружения (.env)

```env
DB_NAME=kuroff_db
DB_USER=kuroff_admin
DB_PASSWORD=...
DB_PORT=5432
DATABASE_URL=postgresql+asyncpg://...@localhost:5432/kuroff_db  # для локального alembic
BOT_TOKEN=...
ALLOWED_USER_IDS=[123456789]
BASE_URL=http://localhost:8000
STATIC_DIR=app/static
```
