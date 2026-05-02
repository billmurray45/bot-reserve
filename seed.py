import asyncio
from app.database import AsyncSessionLocal, init_db
from app.models.category import Category


CATEGORIES = [
    Category(name="ПТИЦА", slug="chicken", sort_order=0),
    Category(name="МЯСО", slug="meat", sort_order=1),
    Category(name="РЫБА И МОРЕПРОДУКТЫ", slug="fish", sort_order=2),
    Category(name="ДОПОЛНИТЕЛЬНЫЕ ПРОДУКТЫ", slug="extras", sort_order=3),
]


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        for cat in CATEGORIES:
            db.add(cat)
        await db.commit()
    print("Seeded 4 categories.")


asyncio.run(seed())
