"""Auth controller — registration, login, current-user."""

from sqlalchemy.orm import Session

from app.modules.auth.schemas import AuthResponse, AuthUser, RegisterRequest, Token
from app.modules.users.models import User
from app.services.auth import auth_service


def register(db: Session, data: RegisterRequest) -> AuthResponse:
    user = auth_service.register(db, data)
    token = auth_service.issue_token(user)
    return AuthResponse(access_token=token, user=AuthUser.model_validate(user))


def login(db: Session, email: str, password: str) -> Token:
    user = auth_service.authenticate(db, email, password)
    return Token(access_token=auth_service.issue_token(user))


def me(current_user: User) -> AuthUser:
    return AuthUser.model_validate(current_user)
