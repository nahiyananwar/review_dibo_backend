"""Product data/business logic: listing (with aggregates + search/filter),
detail (with nested reviews), and admin create/delete.
"""

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.constants.app_constants import REVIEW_STATUS_APPROVED
from app.constants.messages import Messages
from app.modules.products.models import Product
from app.modules.products.schemas import (
    ProductCreate,
    ProductDetail,
    ProductListItem,
    ReviewInProduct,
)
from app.modules.reviews.models import Review
from app.services.products.rating_service import (
    avg_rating_expr,
    review_count_expr,
    summarize,
)
from app.utils.exceptions import NotFoundError
from app.utils.utils import round_rating


def list_products(
    db: Session,
    search: Optional[str] = None,
    min_rating: Optional[float] = None,
) -> list[ProductListItem]:
    """List products with computed ``average_rating`` and ``review_count``.

    Single query (LEFT JOIN + GROUP BY aggregates) so there is no N+1.
    Optional case-insensitive ``search`` over title/description and
    ``min_rating`` filter on the aggregated average.
    """
    avg_expr = avg_rating_expr()
    count_expr = review_count_expr()

    stmt = (
        select(Product, avg_expr.label("avg_rating"), count_expr.label("review_count"))
        # Only approved reviews count toward the aggregates.
        .outerjoin(
            Review,
            (Review.product_id == Product.id) & (Review.status == REVIEW_STATUS_APPROVED),
        )
        .group_by(Product.id)
        .order_by(Product.created_at.desc())
    )

    if search and search.strip():
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(Product.title.ilike(like), Product.description.ilike(like))
        )

    rows = db.execute(stmt).all()
    items = [
        ProductListItem(
            id=product.id,
            title=product.title,
            description=product.description,
            image_url=product.image_url,
            average_rating=round_rating(avg_rating),
            review_count=review_count,
            created_at=product.created_at,
        )
        for product, avg_rating, review_count in rows
    ]

    if min_rating is not None:
        # Filter on the SAME rounded value the API exposes, so the filtered set
        # is always consistent with the displayed average_rating (a product
        # shown as "4.0" is never hidden by a "4+" filter, and vice-versa).
        items = [item for item in items if item.average_rating >= min_rating]

    return items


def get_product_detail(db: Session, product_id: int) -> ProductDetail:
    """Return a product with its nested reviews and aggregate rating."""
    product = db.get(Product, product_id)
    if product is None:
        raise NotFoundError(Messages.PRODUCT_NOT_FOUND)

    stmt = (
        select(Review)
        # Public detail shows only approved reviews; aggregates match.
        .where(
            (Review.product_id == product_id)
            & (Review.status == REVIEW_STATUS_APPROVED)
        )
        .options(joinedload(Review.user))  # eager-load authors -> no N+1
        .order_by(Review.created_at.desc())
    )
    reviews = db.execute(stmt).scalars().all()
    average_rating, review_count = summarize([r.rating for r in reviews])

    return ProductDetail(
        id=product.id,
        title=product.title,
        description=product.description,
        image_url=product.image_url,
        created_at=product.created_at,
        average_rating=average_rating,
        review_count=review_count,
        reviews=[
            ReviewInProduct(
                id=r.id,
                user=r.user.name,
                user_id=r.user_id,
                rating=r.rating,
                comment=r.comment,
                images=list(r.images or []),
                created_at=r.created_at,
            )
            for r in reviews
        ],
    )


def create_product(db: Session, data: ProductCreate) -> ProductListItem:
    """Create a product (admin). A new product has no reviews yet."""
    product = Product(
        title=data.title.strip(),
        description=data.description,
        image_url=data.image_url,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return ProductListItem(
        id=product.id,
        title=product.title,
        description=product.description,
        image_url=product.image_url,
        average_rating=0.0,
        review_count=0,
        created_at=product.created_at,
    )


def delete_product(db: Session, product_id: int) -> None:
    """Delete a product (admin); cascades to its reviews."""
    product = db.get(Product, product_id)
    if product is None:
        raise NotFoundError(Messages.PRODUCT_NOT_FOUND)
    db.delete(product)
    db.commit()
