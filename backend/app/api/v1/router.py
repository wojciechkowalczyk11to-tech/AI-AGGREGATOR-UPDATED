from fastapi import APIRouter

from app.api.v1.routes_auth import router as auth_router
from app.api.v1.routes_chat import router as chat_router
from app.api.v1.routes_health import router as health_router
from app.api.v1.routes_payments import router as payments_router
from app.api.v1.routes_usage import router as usage_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(usage_router)
api_router.include_router(payments_router)
