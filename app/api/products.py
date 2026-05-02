import io
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crud import product as crud
from app.database import get_db
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 800


def compress_image(content: bytes) -> bytes:
    img = Image.open(io.BytesIO(content))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    if img.width > MAX_SIZE or img.height > MAX_SIZE:
        img.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)

    buf = io.BytesIO()
    if img.mode == "RGBA":
        img.save(buf, format="PNG", optimize=True, compress_level=9)
    else:
        img.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()


@router.get("", response_model=list[ProductOut])
async def list_products(
    category_id: int | None = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_all(db, category_id=category_id, active_only=active_only)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud.get_by_id(db, product_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return obj


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create(db, data)


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db)
):
    obj = await crud.get_by_id(db, product_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return await crud.update(db, obj, data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud.get_by_id(db, product_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await crud.delete(db, obj)


@router.post("/{product_id}/image", response_model=ProductOut)
async def upload_image(
    product_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    obj = await crud.get_by_id(db, product_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type: {file.content_type}",
        )

    content = await file.read()
    compressed = compress_image(content)

    img = Image.open(io.BytesIO(compressed))
    ext = ".png" if img.mode == "RGBA" else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = Path(settings.STATIC_DIR) / "images" / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(compressed)

    image_path = f"images/{filename}"
    return await crud.set_image(db, obj, image_path)


@router.delete("/{product_id}/image", response_model=ProductOut)
async def remove_image(product_id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud.get_by_id(db, product_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return await crud.remove_image(db, obj)
