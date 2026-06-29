"""Review Dibo API - FastAPI application entrypoint.

Request lifecycle:
    app.py (here) -> routes/index.py (main_router) -> modules/[module]/routes.py
    -> controller -> service.

Run locally:
    python -m app.app           # uses HOST/PORT from .env (defaults to :8011)
    uvicorn app.app:app --reload --port 8011
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import settings
from app.middleware.error_handlers import register_exception_handlers
from app.routes.index import main_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "REST API for the Review Dibo platform: products, reviews, users, "
        "JWT auth, admin moderation, and search/filter."
    ),
)

# ---- CORS: allow the Next.js frontend to call the API ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Centralized error handling ----
register_exception_handlers(app)

# ---- Feature routes (everything under /api) ----
app.include_router(main_router)


@app.get("/", tags=["health"])
def root() -> dict:
    return {"message": f"{settings.app_name} is running", "docs": "/docs"}


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.app:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
