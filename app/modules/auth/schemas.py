"""Pydantic schemas for the auth feature."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.constants.app_constants import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)


class Token(BaseModel):
    """OAuth2-style token response (used by ``POST /api/auth/login``)."""

    access_token: str
    token_type: str = "bearer"


class AuthUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    is_admin: bool
    created_at: datetime


class AuthResponse(Token):
    """Returned by ``POST /api/auth/register`` — token plus the new user."""

    user: AuthUser
