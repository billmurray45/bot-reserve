from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


async def get_all(db: AsyncSession) -> list[Category]:
    result = await db.execute(select(Category).order_by(Category.sort_order))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, category_id: int) -> Category | None:
    return await db.get(Category, category_id)


async def create(db: AsyncSession, data: CategoryCreate) -> Category:
    category = Category(**data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def update(
    db: AsyncSession, category: Category, data: CategoryUpdate
) -> Category:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(category, field, value)
    await db.commit()
    await db.refresh(category)
    return category


async def delete(db: AsyncSession, category: Category) -> None:
    await db.delete(category)
    await db.commit()
