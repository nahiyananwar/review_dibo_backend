"""Pydantic schemas for the users feature."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Body for ``POST /api/users`` — resolves a reviewer name -> user_id."""

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    created_at: datetime
