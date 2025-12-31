from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.domain.models.provider import ProviderMode


class Settings(BaseSettings):
    provider_mode: ProviderMode = Field(ProviderMode.AWS, validation_alias="PROVIDER_MODE")
    aws_region: str = Field("ap-northeast-2", validation_alias="AWS_REGION")
    transcribe_language_code: str = Field("en-US", validation_alias="TRANSCRIBE_LANGUAGE_CODE")
    transcribe_sample_rate: int = 16000
    transcribe_media_encoding: str = "pcm"
    bedrock_translation_fast_model_id: str = Field(
        "apac.anthropic.claude-haiku-4-5-20251001-v1:0", validation_alias="BEDROCK_TRANSLATION_FAST_MODEL_ID"
    )
    bedrock_quick_translate_model_id: str = Field(
        "apac.anthropic.claude-haiku-4-5-20251001-v1:0",
        validation_alias="BEDROCK_QUICK_TRANSLATE_MODEL_ID",
    )
    bedrock_translation_high_model_id: str = Field(
        "global.anthropic.claude-haiku-4-5-20251001-v1:0",
        validation_alias="BEDROCK_TRANSLATION_HIGH_MODEL_ID",
    )
    openai_api_key: str | None = Field(None, validation_alias="OPENAI_API_KEY")
    openai_stt_model: str = Field("gpt-4o-transcribe", validation_alias="OPENAI_STT_MODEL")
    openai_translation_model: str = Field("gpt-4o-mini", validation_alias="OPENAI_TRANSLATION_MODEL")
    openai_stt_language: str | None = Field(None, validation_alias="OPENAI_STT_LANGUAGE")
    openai_commit_interval_ms: int = Field(1000, validation_alias="OPENAI_COMMIT_INTERVAL_MS")
    google_project_id: str | None = Field(None, validation_alias="GOOGLE_PROJECT_ID")
    google_credentials_path: str | None = Field(None, validation_alias="GOOGLE_APPLICATION_CREDENTIALS")
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

    @model_validator(mode="after")
    def validate_provider_settings(self) -> "Settings":
        if self.provider_mode == ProviderMode.OPENAI and not self.openai_api_key:
            raise ValueError("openai_api_key is required when provider_mode is OPENAI")
        if self.provider_mode == ProviderMode.AWS and not self.aws_region:
            raise ValueError("aws_region is required when provider_mode is AWS")
        if self.provider_mode == ProviderMode.OPENAI:
            self.openai_stt_language = self._map_language_code(self.openai_stt_language)
        return self

    def _map_language_code(self, language: str | None) -> str:
        if language:
            return language
        mapping = {
            "en-US": "en",
            "en-GB": "en",
            "ko-KR": "ko",
            "ja-JP": "ja",
        }
        fallback = self.transcribe_language_code or "en-US"
        return mapping.get(fallback, fallback.split("-")[0])
