"""Auth endpoints.

    POST /api/auth/register   create account -> token + user           [public]
    POST /api/auth/login      OAuth2 password flow -> access token      [public]
    GET  /api/auth/me         current user from the bearer token        [auth]

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
from app.modules.auth.schemas import AuthResponse, AuthUser, RegisterRequest, Token
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
