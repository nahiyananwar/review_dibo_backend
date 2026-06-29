"""Miscellaneous, dependency-free helper functions."""

from typing import Optional

from app.constants.app_constants import RATING_DECIMALS


def round_rating(value: Optional[float]) -> float:
    """Round an aggregated rating to the configured precision.

    Returns ``0.0`` when there are no reviews (``value`` is ``None``).
    """
    if value is None:
        return 0.0
    return round(float(value), RATING_DECIMALS)


def normalize_email(email: str) -> str:
    """Canonicalize an email for storage/lookup (trim + lowercase)."""
    return email.strip().lower()
