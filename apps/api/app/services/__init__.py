from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .suggestion import SuggestionService
    from .summary import SummaryService

__all__ = ["SuggestionService", "SummaryService"]


def __getattr__(name: str):
    if name == "SuggestionService":
        from .suggestion import SuggestionService

        return SuggestionService
    if name == "SummaryService":
        from .summary import SummaryService

        return SummaryService
    raise AttributeError(f"module {__name__} has no attribute {name}")
