"""Moderation controller."""

from sqlalchemy.orm import Session

from app.modules.moderation.schemas import ModerateReview, ModerationReviewItem
from app.services.moderation import moderation_service


def list_reviews(db: Session, status: str) -> list[ModerationReviewItem]:
    return moderation_service.list_reviews(db, status)


def pending_count(db: Session) -> int:
    return moderation_service.count_pending(db)


def moderate(db: Session, review_id: int, data: ModerateReview) -> ModerationReviewItem:
    return moderation_service.moderate(db, review_id, data.status, data.rejection_reason)
