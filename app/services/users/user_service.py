"""User data/business logic."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.messages import Messages
from app.modules.users.models import User
from app.utils.exceptions import NotFoundError
from app.utils.utils import normalize_email


def get_or_create_user(db: Session, name: str, email: str) -> tuple[User, bool]:
    """Resolve a reviewer to a user, creating one if the email is new.

    Returns ``(user, created)``. Idempotent on email so the guest/name review
    flow can repeatedly resolve the same person to the same ``user_id``.
    """
    normalized = normalize_email(email)
    existing = db.scalar(select(User).where(User.email == normalized))
    if existing is not None:
        return existing, False

    user = User(name=name.strip(), email=normalized)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, True


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError(Messages.USER_NOT_FOUND)
    return user
