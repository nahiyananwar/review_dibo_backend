"""Reviews controller — orchestrates CRUD and ownership checks."""

from sqlalchemy.orm import Session

from app.modules.reviews.models import Review
from app.modules.reviews.schemas import ReviewCreate, ReviewUpdate
from app.modules.users.models import User
from app.services.reviews import ownership_service, review_service


def create_review(db: Session, data: ReviewCreate) -> Review:
    return review_service.create_review(db, data)


def update_review(
    db: Session, review_id: int, data: ReviewUpdate, current_user: User
) -> Review:
    review = review_service.get_review(db, review_id)
    ownership_service.assert_can_modify(review, current_user)
    return review_service.update_review(db, review, data)


def delete_review(db: Session, review_id: int, current_user: User) -> None:
    review = review_service.get_review(db, review_id)
    ownership_service.assert_can_modify(review, current_user)
    review_service.delete_review(db, review)
