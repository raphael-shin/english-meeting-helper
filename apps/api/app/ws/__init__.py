from fastapi import APIRouter

from .meetings import router as meetings_router

ws_router = APIRouter()
ws_router.include_router(meetings_router)
