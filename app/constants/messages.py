"""Human-readable message strings returned in API errors/responses."""


class Messages:
    # ---- Not found ----
    PRODUCT_NOT_FOUND = "Product not found"
    REVIEW_NOT_FOUND = "Review not found"
    USER_NOT_FOUND = "User not found"

    # ---- Auth ----
    EMAIL_ALREADY_REGISTERED = "Email already registered"
    INVALID_CREDENTIALS = "Invalid email or password"
    CURRENT_PASSWORD_INCORRECT = "Your current password is incorrect"
    NOT_AUTHENTICATED = "Not authenticated"
    INVALID_TOKEN = "Could not validate credentials"
    INACTIVE_OR_MISSING_USER = "User for this token no longer exists"

    # ---- Authorization ----
    ADMIN_REQUIRED = "Admin privileges are required for this action"
    PERMISSION_REQUIRED = "You don't have permission to perform this action"
    NOT_REVIEW_OWNER = "You can only modify or delete your own reviews"
    CANNOT_MODIFY_SELF = "You cannot delete or demote your own admin account"
    SIGN_IN_TO_REVIEW = "Please sign in to post a review under this account"
    INVALID_ROLE = "Invalid role"

    # ---- Password reset ----
    INVALID_RESET_TOKEN = "This reset link is invalid or has expired"
    PASSWORD_RESET_SENT = "If that email is registered, a password reset link has been sent."

    # ---- Success acknowledgements ----
    REVIEW_DELETED = "Review deleted successfully"
    PRODUCT_DELETED = "Product deleted successfully"
