from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bedrock import BedrockService
    from .suggestion import SuggestionService
    from .transcribe import TranscribeService

__all__ = ["BedrockService", "SuggestionService", "TranscribeService"]


def __getattr__(name: str):
    if name == "BedrockService":
        from .bedrock import BedrockService

        return BedrockService
    if name == "SuggestionService":
        from .suggestion import SuggestionService

        return SuggestionService
    if name == "TranscribeService":
        from .transcribe import TranscribeService

        return TranscribeService
    raise AttributeError(f"module {__name__} has no attribute {name}")
