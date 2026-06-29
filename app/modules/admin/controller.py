"""Admin controller — moderation operations."""

from sqlalchemy.orm import Session

from app.modules.admin.schemas import AdminReviewItem
from app.services.admin import admin_service


def list_reviews(db: Session) -> list[AdminReviewItem]:
    return admin_service.list_reviews(db)


def delete_review(db: Session, review_id: int) -> None:
    admin_service.delete_review(db, review_id)
