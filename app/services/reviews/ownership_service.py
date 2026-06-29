"""Authorization rules for modifying reviews."""

from app.constants.messages import Messages
from app.modules.reviews.models import Review
from app.modules.users.models import User
from app.utils.exceptions import ForbiddenError


def assert_can_modify(review: Review, user: User) -> None:
    """Allow only the review's author or an admin to modify/delete it."""
    if user.is_admin or review.user_id == user.id:
        return
    raise ForbiddenError(Messages.NOT_REVIEW_OWNER)
