"""Review data/business logic: CRUD with FK validation."""

from sqlalchemy.orm import Session

from app.config.config import settings
from app.constants.app_constants import REVIEW_STATUS_APPROVED, REVIEW_STATUS_PENDING
from app.constants.messages import Messages
from app.modules.products.models import Product
from app.modules.reviews.models import Review
from app.modules.reviews.schemas import ReviewCreate, ReviewUpdate
from app.modules.users.models import User
from app.utils.exceptions import ForbiddenError, NotFoundError


def get_review(db: Session, review_id: int) -> Review:
    review = db.get(Review, review_id)
    if review is None:
        raise NotFoundError(Messages.REVIEW_NOT_FOUND)
    return review


def create_review(db: Session, data: ReviewCreate, current_user: User | None) -> Review:
    """Create a review.

    The author is derived from the authenticated session when present (so the
    body ``user_id`` can never be used to impersonate another account). An
    unauthenticated request may only post as a *guest* user (one without a
    password) and is never auto-approved — closing the moderation-bypass and
    impersonation vectors.
    """
    if db.get(Product, data.product_id) is None:
        raise NotFoundError(Messages.PRODUCT_NOT_FOUND)

    if current_user is not None:
        # Authenticated member: author is the session user, regardless of body.
        author_id = current_user.id
        is_member = True
    else:
        user = db.get(User, data.user_id)
        if user is None:
            raise NotFoundError(Messages.USER_NOT_FOUND)
        if user.password_hash is not None:
            # Posting under a credentialed account requires authenticating as it.
            raise ForbiddenError(Messages.SIGN_IN_TO_REVIEW)
        author_id = user.id
        is_member = False

    # Hybrid moderation: authenticated members are auto-approved when enabled;
    # guest submissions are always held for moderation.
    status = (
        REVIEW_STATUS_APPROVED
        if (settings.review_auto_approve and is_member)
        else REVIEW_STATUS_PENDING
    )

    review = Review(
        product_id=data.product_id,
        user_id=author_id,
        rating=data.rating,
        comment=data.comment,
        images=data.images,
        status=status,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def update_review(db: Session, review: Review, data: ReviewUpdate, editor: User) -> Review:
    """Apply a partial update. A non-moderator editing already-moderated content
    sends the review back to the queue (so edits can't bypass moderation)."""
    changed = False
    if data.rating is not None:
        review.rating = data.rating
        changed = True
    if data.comment is not None:
        review.comment = data.comment
        changed = True
    if data.images is not None:
        review.images = data.images
        changed = True

    if changed and not editor.is_moderator and review.status != REVIEW_STATUS_PENDING:
        review.status = REVIEW_STATUS_PENDING
        review.moderated_at = None
        review.rejection_reason = None

    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review: Review) -> None:
    db.delete(review)
    db.commit()
