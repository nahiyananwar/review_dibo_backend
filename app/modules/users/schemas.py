"""Pydantic schemas for the users feature."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Body for ``POST /api/users`` — resolves a reviewer name -> user_id."""

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name must not be blank")
        return value


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    # Plain str on output (validated on input via UserCreate); avoids re-validating
    # stored data on the way out.
    email: str
    created_at: datetime
