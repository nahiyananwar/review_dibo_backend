"""Review data/business logic: CRUD with FK validation."""

from sqlalchemy.orm import Session

from app.constants.messages import Messages
from app.modules.products.models import Product
from app.modules.reviews.models import Review
from app.modules.reviews.schemas import ReviewCreate, ReviewUpdate
from app.modules.users.models import User
from app.utils.exceptions import NotFoundError


def get_review(db: Session, review_id: int) -> Review:
    review = db.get(Review, review_id)
    if review is None:
        raise NotFoundError(Messages.REVIEW_NOT_FOUND)
    return review


def create_review(db: Session, data: ReviewCreate) -> Review:
    """Create a review, validating that the product and user both exist.

    The ``user_id`` comes from the request body (resolved client-side), per the
    brief's contract.
    """
    if db.get(Product, data.product_id) is None:
        raise NotFoundError(Messages.PRODUCT_NOT_FOUND)
    if db.get(User, data.user_id) is None:
        raise NotFoundError(Messages.USER_NOT_FOUND)

    review = Review(
        product_id=data.product_id,
        user_id=data.user_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def update_review(db: Session, review: Review, data: ReviewUpdate) -> Review:
    """Apply a partial update (rating and/or comment) to an existing review."""
    if data.rating is not None:
        review.rating = data.rating
    if data.comment is not None:
        review.comment = data.comment
    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review: Review) -> None:
    db.delete(review)
    db.commit()
