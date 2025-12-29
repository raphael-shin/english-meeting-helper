from fastapi import APIRouter

from .health import router as health_router
from .translate import router as translate_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(translate_router)
