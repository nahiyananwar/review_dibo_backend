"""Products endpoints.

    GET    /api/products            list (search + min_rating)   [public]
    GET    /api/products/{id}       detail with reviews          [public]
    POST   /api/products            create                       [admin]
    DELETE /api/products/{id}       delete (cascades reviews)    [admin]
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.constants.app_constants import RATING_MAX, RATING_MIN
from app.middleware.auth import require_admin
from app.modules.products import controller
from app.modules.products.schemas import ProductCreate, ProductDetail, ProductListItem

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductListItem])
def list_products(
    search: Optional[str] = Query(default=None, description="Match title/description"),
    min_rating: Optional[float] = Query(
        default=None, ge=0, le=RATING_MAX, description="Minimum average rating"
    ),
    db: Session = Depends(get_db),
) -> list[ProductListItem]:
    return controller.list_products(db, search, min_rating)


@router.get("/{product_id}", response_model=ProductDetail)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductDetail:
    return controller.get_product(db, product_id)


@router.post(
    "",
    response_model=ProductListItem,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_product(
    payload: ProductCreate, db: Session = Depends(get_db)
) -> ProductListItem:
    return controller.create_product(db, payload)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> None:
    controller.delete_product(db, product_id)
