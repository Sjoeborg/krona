from dataclasses import dataclass, field
from enum import Enum


class SuggestionStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


@dataclass
class Suggestion:
    """Represents a mapping suggestion for user review."""

    source_symbol: str
    target_symbol: str
    confidence: float
    rationale: str
    status: SuggestionStatus = SuggestionStatus.PENDING
    source_isin: str | None = field(default=None)
    target_isin: str | None = field(default=None)
