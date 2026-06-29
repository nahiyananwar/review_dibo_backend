"""Authentication business logic: registration, credential checks, tokens."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.messages import Messages
from app.modules.auth.schemas import RegisterRequest
from app.modules.users.models import User
from app.utils.exceptions import ConflictError, UnauthorizedError
from app.utils.security import create_access_token, hash_password, verify_password
from app.utils.utils import normalize_email


def register(db: Session, data: RegisterRequest) -> User:
    """Create a credentialed user; 409 if the email is already taken."""
    email = normalize_email(data.email)
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise ConflictError(Messages.EMAIL_ALREADY_REGISTERED)

    user = User(
        name=data.name.strip(),
        email=email,
        password_hash=hash_password(data.password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    """Verify email/password, returning the user or raising 401."""
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    if user is None or not user.password_hash or not verify_password(
        password, user.password_hash
    ):
        raise UnauthorizedError(Messages.INVALID_CREDENTIALS)
    return user


def issue_token(user: User) -> str:
    """Mint a JWT carrying the user's id (sub) plus convenience claims."""
    return create_access_token(
        subject=user.id,
        extra_claims={"is_admin": user.is_admin, "email": user.email},
    )
