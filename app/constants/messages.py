"""Human-readable message strings returned in API errors/responses."""


class Messages:
    # ---- Not found ----
    PRODUCT_NOT_FOUND = "Product not found"
    REVIEW_NOT_FOUND = "Review not found"
    USER_NOT_FOUND = "User not found"

    # ---- Auth ----
    EMAIL_ALREADY_REGISTERED = "Email already registered"
    INVALID_CREDENTIALS = "Invalid email or password"
    NOT_AUTHENTICATED = "Not authenticated"
    INVALID_TOKEN = "Could not validate credentials"
    INACTIVE_OR_MISSING_USER = "User for this token no longer exists"

    # ---- Authorization ----
    ADMIN_REQUIRED = "Admin privileges are required for this action"
    NOT_REVIEW_OWNER = "You can only modify or delete your own reviews"

    # ---- Success acknowledgements ----
    REVIEW_DELETED = "Review deleted successfully"
    PRODUCT_DELETED = "Product deleted successfully"
