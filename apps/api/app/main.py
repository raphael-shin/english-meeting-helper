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
