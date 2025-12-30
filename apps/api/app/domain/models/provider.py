from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class ProviderMode(str, Enum):
    AWS = "AWS"
    OPENAI = "OPENAI"
    GOOGLE = "GOOGLE"


class TranscriptResult(BaseModel):
    is_partial: bool
    text: str
    speaker: str = "spk_1"

    model_config = ConfigDict(extra="forbid")
