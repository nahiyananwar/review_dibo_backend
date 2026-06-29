"""Admin controller — moderation and user-management operations."""

from sqlalchemy.orm import Session

from app.modules.admin.schemas import AdminReviewItem, AdminUserDetail, AdminUserItem
from app.services.admin import admin_service


def list_reviews(db: Session) -> list[AdminReviewItem]:
    return admin_service.list_reviews(db)


def delete_review(db: Session, review_id: int) -> None:
    admin_service.delete_review(db, review_id)


def list_users(db: Session) -> list[AdminUserItem]:
    return admin_service.list_users(db)


def get_user_detail(db: Session, user_id: int) -> AdminUserDetail:
    return admin_service.get_user_detail(db, user_id)


def delete_user(db: Session, user_id: int, acting_admin_id: int) -> None:
    admin_service.delete_user(db, user_id, acting_admin_id)


def set_user_role(
    db: Session, user_id: int, role: str, acting_admin_id: int
) -> AdminUserItem:
    return admin_service.set_user_role(db, user_id, role, acting_admin_id)
