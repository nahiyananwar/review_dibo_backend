"""Reviews endpoints.

    POST   /api/reviews            create (user_id from body)        [public]
    PUT    /api/reviews/{id}       update (owner or admin)           [auth]
    DELETE /api/reviews/{id}       delete (owner or admin)           [auth]
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.middleware.auth import get_current_user
from app.modules.reviews import controller
from app.modules.reviews.schemas import ReviewCreate, ReviewOut, ReviewUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(payload: ReviewCreate, db: Session = Depends(get_db)) -> ReviewOut:
    return controller.create_review(db, payload)


@router.put("/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewOut:
    return controller.update_review(db, review_id, payload, current_user)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    controller.delete_review(db, review_id, current_user)
