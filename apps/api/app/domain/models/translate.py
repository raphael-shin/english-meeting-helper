from __future__ import annotations

from .base import CamelModel


class TranslateRequest(CamelModel):
    text: str | None = None


class TranslateResponse(CamelModel):
    translated_text: str
