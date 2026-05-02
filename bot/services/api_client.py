import httpx

from app.config import settings

BASE = settings.BASE_URL


async def get_categories() -> list[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/categories")
        r.raise_for_status()
        return r.json()


async def get_category(category_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/categories/{category_id}")
        r.raise_for_status()
        return r.json()


async def create_category(data: dict) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE}/api/categories", json=data)
        r.raise_for_status()
        return r.json()


async def update_category(category_id: int, data: dict) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.patch(f"{BASE}/api/categories/{category_id}", json=data)
        r.raise_for_status()
        return r.json()


async def delete_category(category_id: int) -> None:
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{BASE}/api/categories/{category_id}")
        r.raise_for_status()


async def get_products(category_id: int | None = None) -> list[dict]:
    async with httpx.AsyncClient() as client:
        params = {}
        if category_id is not None:
            params["category_id"] = category_id
        r = await client.get(f"{BASE}/api/products", params=params)
        r.raise_for_status()
        return r.json()


async def get_product(product_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/products/{product_id}")
        r.raise_for_status()
        return r.json()


async def create_product(data: dict) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE}/api/products", json=data)
        r.raise_for_status()
        return r.json()


async def update_product(product_id: int, data: dict) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.patch(f"{BASE}/api/products/{product_id}", json=data)
        r.raise_for_status()
        return r.json()


async def delete_product(product_id: int) -> None:
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{BASE}/api/products/{product_id}")
        r.raise_for_status()


async def upload_product_image(product_id: int, filename: str, content: bytes) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE}/api/products/{product_id}/image",
            files={"file": (filename, content, "image/jpeg")},
        )
        r.raise_for_status()
        return r.json()


async def remove_product_image(product_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{BASE}/api/products/{product_id}/image")
        r.raise_for_status()
        return r.json()
