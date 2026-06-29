"""Pydantic schemas for the moderation feature."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.constants.app_constants import REVIEW_STATUS_APPROVED, REVIEW_STATUS_REJECTED


class ModerationReviewItem(BaseModel):
    """A review in the moderation queue, with product/user context + status."""

    id: int
    product_id: int
    product_title: str
    user_id: int
    user: str
    rating: int
    comment: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    status: str
    rejection_reason: Optional[str] = None
    created_at: datetime
    moderated_at: Optional[datetime] = None


class PendingCount(BaseModel):
    count: int


class ModerateReview(BaseModel):
    """Body for ``PATCH /api/moderation/reviews/{id}`` — approve or reject."""

    status: str
    rejection_reason: Optional[str] = Field(default=None, max_length=500)

    @field_validator("status")
    @classmethod
    def _valid_status(cls, value: str) -> str:
        if value not in (REVIEW_STATUS_APPROVED, REVIEW_STATUS_REJECTED):
            raise ValueError("status must be 'approved' or 'rejected'")
        return value
