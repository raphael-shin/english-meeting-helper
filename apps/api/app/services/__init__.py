from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .suggestion import SuggestionService

__all__ = ["SuggestionService"]


def __getattr__(name: str):
    if name == "SuggestionService":
        from .suggestion import SuggestionService

        return SuggestionService
    raise AttributeError(f"module {__name__} has no attribute {name}")
