"""Moderation endpoints (require the moderate-reviews capability: moderator/admin).

    GET   /api/moderation/reviews?status=pending   queue (pending|approved|rejected|all)
    PATCH /api/moderation/reviews/{id}             approve or reject a review
"""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.middleware.auth import require_moderator
from app.modules.moderation import controller
from app.modules.moderation.schemas import ModerateReview, ModerationReviewItem, PendingCount

router = APIRouter(
    prefix="/moderation",
    tags=["moderation"],
    dependencies=[Depends(require_moderator)],
)


@router.get("/pending-count", response_model=PendingCount)
def pending_count(db: Session = Depends(get_db)) -> PendingCount:
    return PendingCount(count=controller.pending_count(db))


@router.get("/reviews", response_model=list[ModerationReviewItem])
def list_reviews(
    status: Literal["pending", "approved", "rejected", "all"] = Query("pending"),
    db: Session = Depends(get_db),
) -> list[ModerationReviewItem]:
    return controller.list_reviews(db, status)


@router.patch("/reviews/{review_id}", response_model=ModerationReviewItem)
def moderate(
    review_id: int, payload: ModerateReview, db: Session = Depends(get_db)
) -> ModerationReviewItem:
    return controller.moderate(db, review_id, payload)
