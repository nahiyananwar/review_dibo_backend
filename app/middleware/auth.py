"""Authentication & authorization dependencies.

These FastAPI dependencies read the ``Authorization: Bearer <jwt>`` header,
resolve it to a ``User`` and enforce capabilities.

- ``get_current_user``        -> required auth (401 if missing/invalid)
- ``require_admin``           -> requires an admin (403 otherwise)
- ``require_permission(perm)``-> requires a specific capability
- ``require_moderator``       -> requires the moderate-reviews capability

Session tokens must have ``type == "access"`` and a ``tv`` matching the user's
current ``token_version`` — so password resets (which bump it) and reset tokens
(``type == "reset"``) can never act as a session.
"""

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.constants.messages import Messages
from app.constants.roles import PERM_MODERATE_REVIEWS
from app.modules.users.models import User
from app.utils.security import decode_access_token

# tokenUrl points at the login endpoint so Swagger's "Authorize" button works.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
# Same scheme but optional — for endpoints that work for guests but personalize
# (and tighten trust) when a valid session is present.
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def _user_from_token(token: str, db: Session) -> User | None:
    payload = decode_access_token(token)
    # Only genuine session tokens authenticate (not reset/other token types).
    if not payload or payload.get("type") != "access":
        return None
    subject = payload.get("sub")
    if subject is None:
        return None
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        return None
    user = db.get(User, user_id)
    if user is None:
        return None
    # Reject tokens issued before the user's current version (post password reset).
    if payload.get("tv") != user.token_version:
        return None
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user or raise 401."""
    user = _user_from_token(token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=Messages.INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> User | None:
    """Resolve the user if a valid session token is present, else None."""
    if not token:
        return None
    return _user_from_token(token, db)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require that the authenticated user is an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=Messages.ADMIN_REQUIRED,
        )
    return current_user


def require_permission(permission: str) -> Callable[[User], User]:
    """Build a dependency that requires a specific capability."""

    def checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=Messages.PERMISSION_REQUIRED,
            )
        return current_user

    return checker


# Convenience dependency for the moderation surface (moderator or admin).
require_moderator = require_permission(PERM_MODERATE_REVIEWS)
