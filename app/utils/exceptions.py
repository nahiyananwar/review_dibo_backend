"""Domain exception hierarchy.

Services and controllers raise these instead of HTTP details, keeping business
logic decoupled from the web layer. ``middleware/error_handlers.py`` maps each
one to a JSON response with the right status code.
"""


class AppError(Exception):
    """Base class for all expected, client-facing errors."""

    status_code: int = 400
    default_message: str = "Bad request"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    default_message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    default_message = "Conflict"


class UnauthorizedError(AppError):
    status_code = 401
    default_message = "Not authenticated"


class ForbiddenError(AppError):
    status_code = 403
    default_message = "Forbidden"
