"""Pydantic schemas for the auth feature."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.constants.app_constants import (
    MAX_AVATAR_LENGTH,
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
)


# Avatars must be raster images (matches what the client resizer produces).
# SVG is excluded — it can carry active markup / outbound-request vectors.
_ALLOWED_AVATAR_PREFIXES = ("data:image/png", "data:image/jpeg", "data:image/webp")


def _strip_required(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Name must not be blank")
    return value


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return _strip_required(value)


class Token(BaseModel):
    """OAuth2-style token response (used by ``POST /api/auth/login``)."""

    access_token: str
    token_type: str = "bearer"


class AuthUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    # Plain str on output: the email was validated on input; never re-validate
    # stored data on the way out (would 500 on reserved-TLD/legacy values).
    email: str
    avatar: Optional[str] = None
    role: str
    is_admin: bool
    created_at: datetime


class AuthResponse(Token):
    """Returned by ``POST /api/auth/register`` — token plus the new user."""

    user: AuthUser


class ProfileUpdate(BaseModel):
    """Body for ``PUT /api/auth/me`` — partial profile update (name/email/avatar).

    Only the fields present in the request are applied. ``avatar`` may be sent as
    ``null``/`""` to remove an existing picture.
    """

    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    avatar: Optional[str] = Field(default=None, max_length=MAX_AVATAR_LENGTH)
    # Required only when changing the email (step-up re-authentication).
    current_password: Optional[str] = Field(default=None, max_length=MAX_PASSWORD_LENGTH)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: Optional[str]) -> Optional[str]:
        return _strip_required(value) if value is not None else value

    @field_validator("avatar")
    @classmethod
    def _check_avatar(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None  # explicit empty string => remove the avatar
        if not value.startswith(_ALLOWED_AVATAR_PREFIXES):
            raise ValueError("Avatar must be a PNG, JPEG, or WEBP image")
        if len(value) > MAX_AVATAR_LENGTH:
            raise ValueError("Avatar image is too large")
        return value

    @model_validator(mode="after")
    def _at_least_one(self) -> "ProfileUpdate":
        if not ({"name", "email", "avatar"} & self.model_fields_set):
            raise ValueError("Provide at least one field to update")
        return self


class MyReviewItem(BaseModel):
    """A review authored by the current user, with product context."""

    id: int
    product_id: int
    product_title: str
    rating: int
    comment: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    status: str
    created_at: datetime


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    # Returned ONLY in development (no email service); production emails it.
    reset_token: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
