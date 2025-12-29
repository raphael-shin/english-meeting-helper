from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    aws_region: str = Field("ap-northeast-2", validation_alias="AWS_REGION")
    transcribe_language_code: str = Field("en-US", validation_alias="TRANSCRIBE_LANGUAGE_CODE")
    transcribe_sample_rate: int = 16000
    transcribe_media_encoding: str = "pcm"
    bedrock_translation_model_id: str = Field(
        "apac.anthropic.claude-haiku-4-5-20251001-v1:0", validation_alias="BEDROCK_TRANSLATION_MODEL_ID"
    )
    bedrock_quick_translate_model_id: str = Field(
        "apac.anthropic.claude-haiku-4-5-20251001-v1:0",
        validation_alias="BEDROCK_QUICK_TRANSLATE_MODEL_ID",
    )
    bedrock_translation_history_model_id: str = Field(
        "",
        validation_alias="BEDROCK_TRANSLATION_HISTORY_MODEL_ID",
    )
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"], validation_alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        return ["http://localhost:5173"]
