"""Users controller."""

from sqlalchemy.orm import Session

from app.modules.users.models import User
from app.modules.users.schemas import UserCreate
from app.services.users import user_service


def create_user(db: Session, data: UserCreate) -> tuple[User, bool]:
    """Resolve/create a user. Returns ``(user, created)``."""
    return user_service.get_or_create_user(db, data.name, data.email)
