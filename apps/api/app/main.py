from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core import Settings, configure_logging
from app.ws import ws_router

configure_logging()
settings = Settings()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.settings = settings
app.include_router(api_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "service": "English Meeting Helper API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/v1/health",
            "websocket": "/ws/v1/meetings/{sessionId}",
            "quick_translate": "/api/v1/translate/quick",
        },
    }
