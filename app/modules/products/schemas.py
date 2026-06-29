"""Pydantic schemas for the products feature."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewInProduct(BaseModel):
    """A single review as nested inside the product-detail response.

    Built explicitly by the service (``user`` is the author's name, flattened
    from the related User), so this is not a ``from_attributes`` model.
    """

    id: int
    user: str
    user_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime


class ProductCreate(BaseModel):
    """Body for ``POST /api/products`` (admin)."""

    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = Field(default=None, max_length=1024)


class ProductListItem(BaseModel):
    """An item in ``GET /api/products`` — includes computed aggregates."""

    id: int
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    average_rating: float
    review_count: int
    created_at: datetime


class ProductDetail(BaseModel):
    """``GET /api/products/{id}`` — product plus its nested reviews."""

    id: int
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    average_rating: float
    review_count: int
    reviews: list[ReviewInProduct]
