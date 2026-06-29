"""Pytest fixtures.

Points the app at a throwaway SQLite database *before* anything from ``app`` is
imported, so the same code path (models, services, routes) runs end-to-end
without needing a live PostgreSQL.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./_pytest.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
# Make the dev-only reset-token visible to tests.
os.environ.setdefault("AUTH_DEV_RETURN_RESET_TOKEN", "true")

import pytest
from fastapi.testclient import TestClient

from app.app import app
from app.config.database import Base, SessionLocal, engine, import_models
from app.constants.roles import ROLE_ADMIN, ROLE_MODERATOR
from app.services.auth.auth_service import issue_token
from app.utils.security import hash_password


@pytest.fixture(scope="session", autouse=True)
def _prepare_database():
    import_models()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _token_for(email: str, name: str, role: str) -> str:
    from sqlalchemy import select

    from app.modules.users.models import User
    from app.utils.utils import normalize_email

    db = SessionLocal()
    try:
        normalized = normalize_email(email)
        user = db.scalar(select(User).where(User.email == normalized))
        if user is None:
            user = User(
                name=name,
                email=normalized,
                password_hash=hash_password("password123"),
                role=role,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return issue_token(user)
    finally:
        db.close()


@pytest.fixture()
def admin_token() -> str:
    return _token_for("admintest@reviewdibo.com", "Admin Test", ROLE_ADMIN)


@pytest.fixture()
def moderator_token() -> str:
    return _token_for("modtest@reviewdibo.com", "Mod Test", ROLE_MODERATOR)


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
