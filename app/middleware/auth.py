"""Authentication & authorization dependencies.

These FastAPI dependencies read the ``Authorization: Bearer <jwt>`` header,
resolve it to a ``User`` and enforce roles. They are the single entry point for
auth used by feature routes.

- ``get_current_user``   -> required auth (401 if missing/invalid)
- ``require_admin``      -> requires an authenticated admin (403 otherwise)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.constants.messages import Messages
from app.modules.users.models import User
from app.utils.security import decode_access_token

# tokenUrl points at the login endpoint so Swagger's "Authorize" button works.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def _user_from_token(token: str, db: Session) -> User | None:
    payload = decode_access_token(token)
    if not payload:
        return None
    subject = payload.get("sub")
    if subject is None:
        return None
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        return None
    return db.get(User, user_id)


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


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require that the authenticated user is an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=Messages.ADMIN_REQUIRED,
        )
    return current_user
