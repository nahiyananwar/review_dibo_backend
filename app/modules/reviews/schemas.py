"""Pydantic schemas for the reviews feature."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.constants.app_constants import (
    MAX_IMAGE_LENGTH,
    MAX_REVIEW_IMAGES,
    RATING_MAX,
    RATING_MIN,
)


def _validate_images(images: list[str]) -> list[str]:
    """Bound the number and size of attached images."""
    if len(images) > MAX_REVIEW_IMAGES:
        raise ValueError(f"A review can have at most {MAX_REVIEW_IMAGES} images")
    for image in images:
        if not isinstance(image, str) or not image.strip():
            raise ValueError("Each image must be a non-empty string")
        if len(image) > MAX_IMAGE_LENGTH:
            raise ValueError("One of the images is too large")
        if not image.startswith(("data:image/", "http://", "https://")):
            raise ValueError("Each image must be an image data URL or an http(s) URL")
    return images


class ReviewCreate(BaseModel):
    """Body for ``POST /api/reviews`` (matches the brief contract)."""

    product_id: int
    user_id: int
    rating: int = Field(ge=RATING_MIN, le=RATING_MAX)
    comment: Optional[str] = Field(default=None, max_length=2000)
    images: list[str] = Field(default_factory=list)

    @field_validator("images")
    @classmethod
    def _check_images(cls, value: list[str]) -> list[str]:
        return _validate_images(value)


class ReviewUpdate(BaseModel):
    """Body for ``PUT /api/reviews/{id}`` — partial update."""

    rating: Optional[int] = Field(default=None, ge=RATING_MIN, le=RATING_MAX)
    comment: Optional[str] = Field(default=None, max_length=2000)
    images: Optional[list[str]] = None

    @field_validator("images")
    @classmethod
    def _check_images(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        return None if value is None else _validate_images(value)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "ReviewUpdate":
        if self.rating is None and self.comment is None and self.images is None:
            raise ValueError("Provide at least one of 'rating', 'comment', or 'images'")
        return self


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    user_id: int
    rating: int
    comment: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    status: str
    created_at: datetime
