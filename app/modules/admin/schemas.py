"""Pydantic schemas for the admin feature."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.constants.roles import ASSIGNABLE_ROLES


class AdminReviewItem(BaseModel):
    """A review row for the admin moderation table (flattened with context)."""

    id: int
    product_id: int
    product_title: str
    user_id: int
    user: str
    rating: int
    comment: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    status: str
    created_at: datetime


class AdminUserItem(BaseModel):
    """A user row for the admin user-management table."""

    id: int
    name: str
    email: str
    avatar: Optional[str] = None
    role: str
    review_count: int
    created_at: datetime


class AdminUserDetail(AdminUserItem):
    """A single user's full profile for admin view: details + their reviews."""

    reviews: list[AdminReviewItem] = Field(default_factory=list)


class AdminUserUpdate(BaseModel):
    """Body for ``PATCH /api/admin/users/{id}`` — assign a role."""

    role: str

    @field_validator("role")
    @classmethod
    def _valid_role(cls, value: str) -> str:
        if value not in ASSIGNABLE_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(ASSIGNABLE_ROLES)}")
        return value
