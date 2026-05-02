from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.spec import ProductSpec
from app.schemas.product import ProductCreate, ProductUpdate


def _with_specs():
    return selectinload(Product.specs)


async def get_all(
    db: AsyncSession,
    category_id: int | None = None,
    active_only: bool = False,
) -> list[Product]:
    q = select(Product).options(_with_specs()).order_by(Product.sort_order)
    if category_id is not None:
        q = q.where(Product.category_id == category_id)
    if active_only:
        q = q.where(Product.is_active.is_(True))
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, product_id: int) -> Product | None:
    result = await db.execute(
        select(Product).options(_with_specs()).where(Product.id == product_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, data: ProductCreate) -> Product:
    specs_data = data.specs
    product = Product(**data.model_dump(exclude={"specs"}))
    db.add(product)
    await db.flush()

    for i, spec in enumerate(specs_data):
        db.add(ProductSpec(
            product_id=product.id,
            label=spec.label,
            value=spec.value,
            sort_order=spec.sort_order if spec.sort_order else i,
        ))

    await db.commit()
    await db.refresh(product)
    return await get_by_id(db, product.id)


async def update(db: AsyncSession, product: Product, data: ProductUpdate) -> Product:
    specs_data = data.specs
    update_data = data.model_dump(exclude_none=True, exclude={"specs"})

    for field, value in update_data.items():
        setattr(product, field, value)

    if specs_data is not None:
        for spec in product.specs:
            await db.delete(spec)
        await db.flush()
        for i, spec in enumerate(specs_data):
            db.add(ProductSpec(
                product_id=product.id,
                label=spec.label,
                value=spec.value,
                sort_order=spec.sort_order if spec.sort_order else i,
            ))

    await db.commit()
    return await get_by_id(db, product.id)


async def delete(db: AsyncSession, product: Product) -> None:
    await db.delete(product)
    await db.commit()


async def set_image(db: AsyncSession, product: Product, image_path: str) -> Product:
    product.image_path = image_path
    product.icon_name = None
    await db.commit()
    await db.refresh(product)
    return product


async def remove_image(db: AsyncSession, product: Product) -> Product:
    product.image_path = None
    await db.commit()
    await db.refresh(product)
    return product
