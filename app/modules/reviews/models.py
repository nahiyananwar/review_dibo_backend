"""Review ORM model.

A review links a user to a product with a 1-5 rating and an optional comment.
Foreign keys cascade on delete (DB-level for PostgreSQL, ORM-level for any
backend) so removing a product or user removes their reviews.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.constants.app_constants import RATING_MAX, RATING_MIN, REVIEW_STATUS_PENDING

if TYPE_CHECKING:
    from app.modules.products.models import Product
    from app.modules.users.models import User


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint(
            f"rating >= {RATING_MIN} AND rating <= {RATING_MAX}",
            name="ck_reviews_rating_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Attached photos as data URLs / image URLs. JSON works on SQLite + Postgres.
    images: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # Moderation lifecycle: pending | approved | rejected.
    status: Mapped[str] = mapped_column(
        String(20), default=REVIEW_STATUS_PENDING, nullable=False, index=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    moderated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")
