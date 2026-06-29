"""Application settings.

All backend configuration lives here, loaded from environment variables / `.env`
via pydantic-settings. Import the singleton `settings` anywhere it is needed.
"""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Environments treated as non-production (relaxed security checks).
DEV_ENVIRONMENTS = {"development", "dev", "local", "test", "testing"}
# Placeholder secret shipped in .env.example; must never be used in production.
INSECURE_SECRET_DEFAULT = "change-me-to-a-long-random-secret-string"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    app_name: str = "Review Dibo API"
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8011

    # ---- Database ----
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/review_dibo"
    )

    # ---- Auth / JWT ----
    secret_key: str = INSECURE_SECRET_DEFAULT
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # ---- CORS ----
    cors_origins: str = "http://localhost:3000"

    # ---- Seed ----
    seed_admin_name: str = "Admin"
    seed_admin_email: str = "admin@reviewdibo.local"
    seed_admin_password: str = "admin12345"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse the comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def is_dev_env(self) -> bool:
        return self.app_env.lower() in DEV_ENVIRONMENTS

    @model_validator(mode="after")
    def _enforce_production_secret(self) -> "Settings":
        """Refuse to boot in a non-dev environment with an insecure JWT secret."""
        if not self.is_dev_env and (
            self.secret_key == INSECURE_SECRET_DEFAULT or len(self.secret_key) < 32
        ):
            raise ValueError(
                f"SECRET_KEY must be a strong (>=32 char) value when APP_ENV='{self.app_env}'. "
                "Refusing to start with the insecure default."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
