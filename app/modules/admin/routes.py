"""Admin endpoints (every route requires an authenticated admin).

    GET    /api/admin/reviews         list all reviews for moderation
    DELETE /api/admin/reviews/{id}    delete any review (admin override)
    GET    /api/admin/users           list all users
    GET    /api/admin/users/{id}      a user's profile + their reviews
    DELETE /api/admin/users/{id}      delete a user (cascades reviews)
    PATCH  /api/admin/users/{id}      promote/demote a user

Admin product add/remove live on the products router (POST/DELETE
/api/products), also admin-guarded.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.modules.admin import controller
from app.modules.admin.schemas import (
    AdminReviewItem,
    AdminUserDetail,
    AdminUserItem,
    AdminUserUpdate,
)
from app.modules.users.models import User

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


@router.get("/users", response_model=list[AdminUserItem])
def list_users(db: Session = Depends(get_db)) -> list[AdminUserItem]:
    return controller.list_users(db)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def get_user(user_id: int, db: Session = Depends(get_db)) -> AdminUserDetail:
    return controller.get_user_detail(db, user_id)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_user),
) -> None:
    controller.delete_user(db, user_id, current_admin.id)


@router.patch("/users/{user_id}", response_model=AdminUserItem)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_user),
) -> AdminUserItem:
    return controller.set_user_role(db, user_id, payload.role, current_admin.id)
