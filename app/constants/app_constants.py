"""Project-wide constant values."""

# Global API prefix; every feature router is mounted under this.
API_PREFIX = "/api"

# Review rating bounds (inclusive), per the brief.
RATING_MIN = 1
RATING_MAX = 5

# Review moderation lifecycle.
REVIEW_STATUS_PENDING = "pending"
REVIEW_STATUS_APPROVED = "approved"
REVIEW_STATUS_REJECTED = "rejected"
REVIEW_STATUSES: tuple[str, ...] = (
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_REJECTED,
)

# How aggregated ratings are rounded for API responses.
RATING_DECIMALS = 1

# Fallback image used by the frontend when a product has no image_url.
DEFAULT_PLACEHOLDER_IMAGE = "https://placehold.co/600x400?text=No+Image"

# bcrypt only consumes the first 72 bytes of a password; cap input accordingly.
MAX_PASSWORD_LENGTH = 72
MIN_PASSWORD_LENGTH = 8

# Review photo attachments (stored as data URLs / image URLs).
MAX_REVIEW_IMAGES = 6
# Per-image cap (~4MB). Images are resized/compressed client-side before upload.
MAX_IMAGE_LENGTH = 4_000_000
# Profile avatars are resized client-side to a small square data URL (~1.5MB cap).
MAX_AVATAR_LENGTH = 1_500_000
