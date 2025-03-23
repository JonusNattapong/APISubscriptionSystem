from fastapi import APIRouter

from app.api.endpoints import auth, models, subscriptions, api_keys, webhooks

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
