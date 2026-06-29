"""Routes Index - central route aggregation.

All routes flow through this file.
Request path: app.py -> routes/index.py -> modules/[module]/routes.py
              -> controller -> service.

Every feature router is mounted under the global ``/api`` prefix. Unlike a
service-to-service API, this app is public-facing: some endpoints are open
(product browsing, register/login, review create) while others require a JWT or
admin role. Auth is therefore declared per-endpoint in each module's routes
rather than as a single global dependency here.
"""

from fastapi import APIRouter

from app.constants.app_constants import API_PREFIX
from app.modules.admin.routes import router as admin_router
from app.modules.auth.routes import router as auth_router
from app.modules.moderation.routes import router as moderation_router
from app.modules.products.routes import router as products_router
from app.modules.reviews.routes import router as reviews_router
from app.modules.users.routes import router as users_router

# Main router aggregates all sub-routers from the feature modules.
main_router = APIRouter(prefix=API_PREFIX)
main_router.include_router(products_router)
main_router.include_router(reviews_router)
main_router.include_router(users_router)
main_router.include_router(auth_router)
main_router.include_router(admin_router)
main_router.include_router(moderation_router)
