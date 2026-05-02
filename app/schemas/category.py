from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    slug: str
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    sort_order: int | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    sort_order: int

    model_config = {"from_attributes": True}
