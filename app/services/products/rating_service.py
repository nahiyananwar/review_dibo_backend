"""Rating aggregation helpers for products.

Kept separate from ``product_service`` so the average/count logic has a single
home, used both by the list query (SQL) and the detail view (in-Python).
"""

from sqlalchemy import func

from app.modules.reviews.models import Review
from app.utils.utils import round_rating


def avg_rating_expr():
    """SQL expression: average rating, 0 when a product has no reviews."""
    return func.coalesce(func.avg(Review.rating), 0.0)


def review_count_expr():
    """SQL expression: number of reviews for a product."""
    return func.count(Review.id)


def summarize(ratings: list[int]) -> tuple[float, int]:
    """Compute ``(average_rating, review_count)`` from in-memory ratings."""
    count = len(ratings)
    if count == 0:
        return 0.0, 0
    return round_rating(sum(ratings) / count), count
