from fastapi import APIRouter

from app.api.categories import router as categories_router
from app.api.products import router as products_router

router = APIRouter(prefix="/api")

router.include_router(categories_router)
router.include_router(products_router)
