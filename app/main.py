from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.router import router
from app.config import settings
from app.database import AsyncSessionLocal, init_db
from app.models.category import Category
from app.models.product import Product

PRODUCTS_PER_PAGE = 3


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="KUR OFF Catalog API", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(router)


def build_pages(categories):
    """
    Returns list of page dicts:
      {"category": Category, "products": [...], "is_first": bool}
    Each page holds max PRODUCTS_PER_PAGE products.
    New category always starts on a new page.
    """
    pages = []
    for category in categories:
        active = [p for p in category.products if p.is_active]
        if not active:
            pages.append({"category": category, "products": [], "is_first": True})
            continue
        chunks = [active[i:i + PRODUCTS_PER_PAGE] for i in range(0, len(active), PRODUCTS_PER_PAGE)]
        for idx, chunk in enumerate(chunks):
            pages.append({
                "category": category,
                "products": chunk,
                "is_first": idx == 0,
            })
    return pages


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/catalog")


@app.get("/catalog", include_in_schema=False)
async def catalog(request: Request, show_prices: bool = True):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Category)
            .options(
                selectinload(Category.products).selectinload(Product.specs)
            )
            .order_by(Category.sort_order)
        )
        categories = result.scalars().all()

    pages = build_pages(categories)
    total_pages = len(pages) + 2  # cover + info page

    return templates.TemplateResponse(
        request,
        "catalog.html",
        {
            "pages": pages,
            "total_pages": total_pages,
            "show_prices": show_prices,
            "contact": {
                "name": "АЙЗАТ УНЕРХАНОВ",
                "company": "ИП УНЕРХАНОВ А.",
                "phone": "+7 702 358 2718",
                "telegram": "@kuroff",
                "email": "kuroff@mail.ru",
            },
            "generated_at": date.today().isoformat(),
        },
    )
