"""Pydantic schemas for the reviews feature."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.constants.app_constants import RATING_MAX, RATING_MIN


class ReviewCreate(BaseModel):
    """Body for ``POST /api/reviews`` (matches the brief contract)."""

    product_id: int
    user_id: int
    rating: int = Field(ge=RATING_MIN, le=RATING_MAX)
    comment: Optional[str] = Field(default=None, max_length=2000)


class ReviewUpdate(BaseModel):
    """Body for ``PUT /api/reviews/{id}`` — partial update."""

    rating: Optional[int] = Field(default=None, ge=RATING_MIN, le=RATING_MAX)
    comment: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "ReviewUpdate":
        if self.rating is None and self.comment is None:
            raise ValueError("Provide at least one of 'rating' or 'comment'")
        return self


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    user_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime
