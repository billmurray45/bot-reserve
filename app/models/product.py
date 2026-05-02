from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    price_unit: Mapped[str] = mapped_column(default="/ КГ")
    image_path: Mapped[str | None] = mapped_column(nullable=True)
    icon_name: Mapped[str | None] = mapped_column(nullable=True)
    sort_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    category: Mapped["Category"] = relationship("Category", back_populates="products")
    specs: Mapped[list["ProductSpec"]] = relationship(
        "ProductSpec",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductSpec.sort_order",
    )
