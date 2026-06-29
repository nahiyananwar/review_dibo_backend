"""Admin endpoints (every route requires an authenticated admin).

    GET    /api/admin/reviews         list all reviews for moderation
    DELETE /api/admin/reviews/{id}    delete any review (admin override)

Admin product add/remove live on the products router (POST/DELETE
/api/products), also admin-guarded.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.middleware.auth import require_admin
from app.modules.admin import controller
from app.modules.admin.schemas import AdminReviewItem

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("/reviews", response_model=list[AdminReviewItem])
def list_reviews(db: Session = Depends(get_db)) -> list[AdminReviewItem]:
    return controller.list_reviews(db)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: Session = Depends(get_db)) -> None:
    controller.delete_review(db, review_id)
