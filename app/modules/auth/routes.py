"""Auth endpoints.

    POST /api/auth/register          create account -> token + user        [public]
    POST /api/auth/login             OAuth2 password flow -> access token   [public]
    GET  /api/auth/me                current user from the bearer token      [auth]
    PUT  /api/auth/me                update current user's profile           [auth]
    GET  /api/auth/me/reviews        reviews authored by the current user    [auth]
    POST /api/auth/forgot-password   request a password reset                [public]
    POST /api/auth/reset-password    set a new password with a reset token   [public]

Login uses the OAuth2 password flow (form fields ``username`` + ``password``),
so the Swagger "Authorize" button works out of the box. Send the user's email
as ``username``.
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.middleware.auth import get_current_user
from app.modules.auth import controller
from app.modules.auth.schemas import (
    AuthResponse,
    AuthUser,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MyReviewItem,
    ProfileUpdate,
    RegisterRequest,
    ResetPasswordRequest,
    Token,
)
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    return controller.register(db, payload)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    return controller.login(db, form_data.username, form_data.password)


@router.get("/me", response_model=AuthUser)
def me(current_user: User = Depends(get_current_user)) -> AuthUser:
    return controller.me(current_user)


@router.put("/me", response_model=AuthUser)
def update_me(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuthUser:
    return controller.update_me(db, current_user, payload)


@router.get("/me/reviews", response_model=list[MyReviewItem])
def my_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MyReviewItem]:
    return controller.my_reviews(db, current_user.id)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest, db: Session = Depends(get_db)
) -> ForgotPasswordResponse:
    return controller.forgot_password(db, payload.email)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> None:
    controller.reset_password(db, payload.token, payload.password)
