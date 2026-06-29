"""Products controller — orchestrates requests, delegates to the service layer."""

from typing import Optional

from sqlalchemy.orm import Session

from app.modules.products.schemas import ProductCreate, ProductDetail, ProductListItem
from app.services.products import product_service


def list_products(
    db: Session,
    search: Optional[str],
    min_rating: Optional[float],
) -> list[ProductListItem]:
    return product_service.list_products(db, search=search, min_rating=min_rating)


def get_product(db: Session, product_id: int) -> ProductDetail:
    return product_service.get_product_detail(db, product_id)


def create_product(db: Session, data: ProductCreate) -> ProductListItem:
    return product_service.create_product(db, data)


def delete_product(db: Session, product_id: int) -> None:
    product_service.delete_product(db, product_id)
