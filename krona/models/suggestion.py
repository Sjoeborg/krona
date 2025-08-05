from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from krona.models.mapping import MappingPlan


class SuggestionStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


@dataclass
class Suggestion:
    """Represents a mapping suggestion for user review."""

    source_symbol: str
    target_symbol: str
    confidence: float | None
    rationale: str
    status: SuggestionStatus = SuggestionStatus.PENDING
    source_isin: str | None = field(default=None)
    target_isin: str | None = field(default=None)

    @classmethod
    def from_mapping_plan(cls, plan: MappingPlan) -> list[Suggestion]:
        """Convert a MappingPlan to a list of suggestions."""
        suggestions = []
        for source, target in plan.symbol_mappings.items():
            suggestions.append(
                cls(
                    source_symbol=source,
                    target_symbol=target,
                    confidence=None,
                    rationale="Loaded from config",
                    status=SuggestionStatus.ACCEPTED,
                )
            )
        return suggestions
