"""Admin moderation logic: list all reviews and delete any review."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.constants.messages import Messages
from app.modules.admin.schemas import AdminReviewItem
from app.modules.reviews.models import Review
from app.utils.exceptions import NotFoundError


def list_reviews(db: Session) -> list[AdminReviewItem]:
    """All reviews with product/user context for the moderation table."""
    stmt = (
        select(Review)
        .options(joinedload(Review.user), joinedload(Review.product))
        .order_by(Review.created_at.desc())
    )
    reviews = db.execute(stmt).scalars().all()
    return [
        AdminReviewItem(
            id=r.id,
            product_id=r.product_id,
            product_title=r.product.title,
            user_id=r.user_id,
            user=r.user.name,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
        )
        for r in reviews
    ]


def delete_review(db: Session, review_id: int) -> None:
    """Admin override: delete any review regardless of ownership."""
    review = db.get(Review, review_id)
    if review is None:
        raise NotFoundError(Messages.REVIEW_NOT_FOUND)
    db.delete(review)
    db.commit()
