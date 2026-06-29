"""Authentication business logic: registration, login, profile, password reset."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.constants.messages import Messages
from app.modules.auth.schemas import MyReviewItem, ProfileUpdate, RegisterRequest
from app.modules.reviews.models import Review
from app.modules.users.models import User
from app.utils.exceptions import AppError, ConflictError, UnauthorizedError
from app.utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.utils.utils import normalize_email

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_RESET = "reset"
RESET_TOKEN_MINUTES = 30


def register(db: Session, data: RegisterRequest) -> User:
    """Create a credentialed user; 409 if the email is already taken."""
    email = normalize_email(data.email)
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise ConflictError(Messages.EMAIL_ALREADY_REGISTERED)

    user = User(
        name=data.name.strip(),
        email=email,
        password_hash=hash_password(data.password),
    )  # role defaults to "user"
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Lost the race against a concurrent registration with the same email.
        db.rollback()
        raise ConflictError(Messages.EMAIL_ALREADY_REGISTERED)
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
    """Mint a session JWT (sub=user id) scoped as an access token."""
    return create_access_token(
        subject=user.id,
        extra_claims={
            "type": TOKEN_TYPE_ACCESS,
            "tv": user.token_version,
            "role": user.role,
        },
    )


# ----------------------------- profile ----------------------------------


def update_profile(db: Session, user: User, data: ProfileUpdate) -> User:
    """Apply a partial profile update (name / email / avatar).

    Only fields present in the request are touched. A changed email is checked
    for uniqueness (409 on conflict).
    """
    fields = data.model_fields_set
    if "name" in fields and data.name is not None:
        user.name = data.name.strip()
    if "avatar" in fields:
        user.avatar = data.avatar  # validated upstream; may be None to remove
    if "email" in fields and data.email is not None:
        new_email = normalize_email(data.email)
        if new_email != user.email:
            # Changing the identifier is a sensitive action: require the current
            # password (step-up), so a hijacked session alone can't take over the
            # account via the forgot-password flow.
            if (
                not data.current_password
                or not user.password_hash
                or not verify_password(data.current_password, user.password_hash)
            ):
                raise UnauthorizedError(Messages.CURRENT_PASSWORD_INCORRECT)
            existing = db.scalar(
                select(User).where(User.email == new_email, User.id != user.id)
            )
            if existing is not None:
                raise ConflictError(Messages.EMAIL_ALREADY_REGISTERED)
            user.email = new_email
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError(Messages.EMAIL_ALREADY_REGISTERED)
    db.refresh(user)
    return user


def get_my_reviews(db: Session, user_id: int) -> list[MyReviewItem]:
    """All reviews authored by the user, with product context."""
    stmt = (
        select(Review)
        .options(joinedload(Review.product))
        .where(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
    )
    reviews = db.execute(stmt).scalars().all()
    return [
        MyReviewItem(
            id=r.id,
            product_id=r.product_id,
            product_title=r.product.title,
            rating=r.rating,
            comment=r.comment,
            images=list(r.images or []),
            status=r.status,
            created_at=r.created_at,
        )
        for r in reviews
    ]


# -------------------------- password reset ------------------------------


def find_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == normalize_email(email)))


def create_password_reset_token(user: User) -> str:
    """Short-lived JWT scoped to password reset (never a session token)."""
    return create_access_token(
        subject=user.id,
        extra_claims={"type": TOKEN_TYPE_RESET, "tv": user.token_version},
        expires_minutes=RESET_TOKEN_MINUTES,
    )


def reset_password(db: Session, token: str, new_password: str) -> None:
    """Validate a reset token and set the user's new password.

    Bumps ``token_version`` on success, which makes the reset token single-use
    and invalidates every previously issued session token for the account.
    """
    payload = decode_access_token(token)
    if not payload or payload.get("type") != TOKEN_TYPE_RESET:
        raise AppError(Messages.INVALID_RESET_TOKEN)
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise AppError(Messages.INVALID_RESET_TOKEN)
    user = db.get(User, user_id)
    if user is None or payload.get("tv") != user.token_version:
        raise AppError(Messages.INVALID_RESET_TOKEN)
    user.password_hash = hash_password(new_password)
    user.token_version += 1
    db.commit()
