"""User ORM model.

A user authors reviews. Auth columns (``password_hash``, ``role``) are additive
over the brief's base fields. ``role`` drives RBAC; ``is_admin``/``is_moderator``
are derived properties so the rest of the app reads capabilities, not columns.
``token_version`` invalidates issued tokens (bumped on password reset).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.constants.roles import ROLE_ADMIN, ROLE_MODERATOR, ROLE_USER, role_has_permission

if TYPE_CHECKING:
    from app.modules.reviews.models import Review


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    # Nullable so brief/demo users can exist without credentials.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Optional profile picture, stored as a compact image data URL.
    avatar: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(String(20), default=ROLE_USER, nullable=False)
    # Bumped on password reset to invalidate all previously issued tokens.
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    reviews: Mapped[list["Review"]] = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def is_moderator(self) -> bool:
        return self.role in (ROLE_MODERATOR, ROLE_ADMIN)

    def has_permission(self, permission: str) -> bool:
        return role_has_permission(self.role, permission)
