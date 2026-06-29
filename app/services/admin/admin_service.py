"""Admin logic: review moderation overview and user management."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.constants.messages import Messages
from app.constants.roles import ROLE_ADMIN
from app.modules.admin.schemas import AdminReviewItem, AdminUserDetail, AdminUserItem
from app.modules.reviews.models import Review
from app.modules.users.models import User
from app.utils.exceptions import ForbiddenError, NotFoundError


# --------------------------- reviews ------------------------------------


def list_reviews(db: Session) -> list[AdminReviewItem]:
    """All reviews (every status) with product/user context for oversight."""
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
            images=list(r.images or []),
            status=r.status,
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


# ---------------------------- users -------------------------------------


def _to_user_item(user: User, review_count: int) -> AdminUserItem:
    return AdminUserItem(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar=user.avatar,
        role=user.role,
        review_count=review_count,
        created_at=user.created_at,
    )


def get_user_detail(db: Session, user_id: int) -> AdminUserDetail:
    """A single user's profile plus all their reviews (every status), newest first."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError(Messages.USER_NOT_FOUND)
    stmt = (
        select(Review)
        .options(joinedload(Review.product))
        .where(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
    )
    reviews = db.execute(stmt).scalars().all()
    items = [
        AdminReviewItem(
            id=r.id,
            product_id=r.product_id,
            product_title=r.product.title,
            user_id=r.user_id,
            user=user.name,
            rating=r.rating,
            comment=r.comment,
            images=list(r.images or []),
            status=r.status,
            created_at=r.created_at,
        )
        for r in reviews
    ]
    return AdminUserDetail(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar=user.avatar,
        role=user.role,
        review_count=len(items),
        created_at=user.created_at,
        reviews=items,
    )


def list_users(db: Session) -> list[AdminUserItem]:
    """All users with their review counts (single aggregate query, no N+1)."""
    stmt = (
        select(User, func.count(Review.id))
        .outerjoin(Review, Review.user_id == User.id)
        .group_by(User.id)
        .order_by(User.created_at.desc())
    )
    rows = db.execute(stmt).all()
    return [_to_user_item(user, count) for user, count in rows]


def delete_user(db: Session, user_id: int, acting_admin_id: int) -> None:
    """Delete a user (cascades their reviews). An admin can't delete themselves."""
    if user_id == acting_admin_id:
        raise ForbiddenError(Messages.CANNOT_MODIFY_SELF)
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError(Messages.USER_NOT_FOUND)
    db.delete(user)
    db.commit()


def set_user_role(
    db: Session, user_id: int, role: str, acting_admin_id: int
) -> AdminUserItem:
    """Assign a role. An admin can't demote themselves (lockout guard)."""
    if user_id == acting_admin_id and role != ROLE_ADMIN:
        raise ForbiddenError(Messages.CANNOT_MODIFY_SELF)
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError(Messages.USER_NOT_FOUND)
    user.role = role
    db.commit()
    db.refresh(user)
    count = db.scalar(select(func.count(Review.id)).where(Review.user_id == user.id)) or 0
    return _to_user_item(user, count)
