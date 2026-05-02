from pydantic import BaseModel


class SpecItem(BaseModel):
    label: str
    value: str
    sort_order: int = 0

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    category_id: int
    title: str
    description: str
    price: float
    price_unit: str = "/ КГ"
    icon_name: str | None = None
    sort_order: int = 0
    specs: list[SpecItem] = []


class ProductUpdate(BaseModel):
    category_id: int | None = None
    title: str | None = None
    description: str | None = None
    price: float | None = None
    price_unit: str | None = None
    image_path: str | None = None
    icon_name: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    specs: list[SpecItem] | None = None


class ProductOut(BaseModel):
    id: int
    category_id: int
    title: str
    description: str
    price: float
    price_unit: str
    image_path: str | None
    icon_name: str | None
    sort_order: int
    is_active: bool
    specs: list[SpecItem] = []

    model_config = {"from_attributes": True}
