"""Users endpoints.

    POST /api/users    create or resolve a reviewer (name + email)   [public]

Idempotent on email: returns 201 when a new user is created, 200 when an
existing user with that email is returned.
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.modules.users import controller
from app.modules.users.schemas import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate, response: Response, db: Session = Depends(get_db)
) -> UserOut:
    user, created = controller.create_user(db, payload)
    if not created:
        response.status_code = status.HTTP_200_OK
    return user
