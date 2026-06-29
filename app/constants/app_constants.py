"""Project-wide constant values."""

# Global API prefix; every feature router is mounted under this.
API_PREFIX = "/api"

# Review rating bounds (inclusive), per the brief.
RATING_MIN = 1
RATING_MAX = 5

# How aggregated ratings are rounded for API responses.
RATING_DECIMALS = 1

# Fallback image used by the frontend when a product has no image_url.
DEFAULT_PLACEHOLDER_IMAGE = "https://placehold.co/600x400?text=No+Image"

# bcrypt only consumes the first 72 bytes of a password; cap input accordingly.
MAX_PASSWORD_LENGTH = 72
MIN_PASSWORD_LENGTH = 8
