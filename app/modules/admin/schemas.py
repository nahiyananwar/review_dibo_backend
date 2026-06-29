"""Pydantic schemas for the admin feature."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AdminReviewItem(BaseModel):
    """A review row for the admin moderation table (flattened with context)."""

    id: int
    product_id: int
    product_title: str
    user_id: int
    user: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime
