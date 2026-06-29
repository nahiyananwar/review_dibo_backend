"""Auth controller — registration, login, current-user, profile, password reset."""

from sqlalchemy.orm import Session

from app.config.config import settings
from app.constants.messages import Messages
from app.modules.auth.schemas import (
    AuthResponse,
    AuthUser,
    ForgotPasswordResponse,
    MyReviewItem,
    ProfileUpdate,
    Token,
)
from app.modules.users.models import User
from app.services.auth import auth_service


def register(db: Session, data) -> AuthResponse:
    user = auth_service.register(db, data)
    token = auth_service.issue_token(user)
    return AuthResponse(access_token=token, user=AuthUser.model_validate(user))


def login(db: Session, email: str, password: str) -> Token:
    user = auth_service.authenticate(db, email, password)
    return Token(access_token=auth_service.issue_token(user))


def me(current_user: User) -> AuthUser:
    return AuthUser.model_validate(current_user)


def update_me(db: Session, current_user: User, data: ProfileUpdate) -> AuthUser:
    user = auth_service.update_profile(db, current_user, data)
    return AuthUser.model_validate(user)


def my_reviews(db: Session, user_id: int) -> list[MyReviewItem]:
    return auth_service.get_my_reviews(db, user_id)


def forgot_password(db: Session, email: str) -> ForgotPasswordResponse:
    """Always returns a generic message (no email enumeration). In development
    the reset token is included for testing; in production it would be emailed."""
    user = auth_service.find_by_email(db, email)
    reset_token = None
    # Returning the token in the response is an explicit dev-only opt-in (default
    # off). In production the token would be emailed, never returned to the client.
    if user is not None and settings.auth_dev_return_reset_token:
        reset_token = auth_service.create_password_reset_token(user)
    return ForgotPasswordResponse(message=Messages.PASSWORD_RESET_SENT, reset_token=reset_token)


def reset_password(db: Session, token: str, password: str) -> None:
    auth_service.reset_password(db, token, password)
