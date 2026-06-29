"""Moderation logic: list the queue and approve/reject reviews."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.constants.app_constants import REVIEW_STATUS_PENDING, REVIEW_STATUS_REJECTED
from app.constants.messages import Messages
from app.modules.moderation.schemas import ModerationReviewItem
from app.modules.reviews.models import Review
from app.utils.exceptions import NotFoundError


def _to_item(review: Review) -> ModerationReviewItem:
    return ModerationReviewItem(
        id=review.id,
        product_id=review.product_id,
        product_title=review.product.title,
        user_id=review.user_id,
        user=review.user.name,
        rating=review.rating,
        comment=review.comment,
        images=list(review.images or []),
        status=review.status,
        rejection_reason=review.rejection_reason,
        created_at=review.created_at,
        moderated_at=review.moderated_at,
    )


def count_pending(db: Session) -> int:
    """Number of reviews awaiting moderation (cheap — no rows/images loaded)."""
    return (
        db.scalar(
            select(func.count()).select_from(Review).where(Review.status == REVIEW_STATUS_PENDING)
        )
        or 0
    )


def list_reviews(db: Session, status: str) -> list[ModerationReviewItem]:
    """List reviews for moderation, optionally filtered by status ('all' = no filter)."""
    stmt = (
        select(Review)
        .options(joinedload(Review.user), joinedload(Review.product))
        .order_by(Review.created_at.desc())
    )
    if status != "all":
        stmt = stmt.where(Review.status == status)
    reviews = db.execute(stmt).scalars().all()
    return [_to_item(r) for r in reviews]


def moderate(
    db: Session, review_id: int, status: str, rejection_reason: str | None
) -> ModerationReviewItem:
    """Approve or reject a review, recording the moderation timestamp/reason."""
    review = db.get(Review, review_id)
    if review is None:
        raise NotFoundError(Messages.REVIEW_NOT_FOUND)
    review.status = status
    review.rejection_reason = rejection_reason if status == REVIEW_STATUS_REJECTED else None
    review.moderated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(review)
    return _to_item(review)
