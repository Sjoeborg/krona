from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from krona.models.suggestion import Suggestion, SuggestionStatus


@dataclass
class SymbolGroup:
    """Represents a group of symbols and ISINs that map to a canonical symbol."""

    canonical_symbol: str
    synonyms: list[str] = field(default_factory=list)
    isins: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {"synonyms": self.synonyms, "ISINs": self.isins}

    @classmethod
    def from_dict(cls, canonical_symbol: str, data: dict[str, Any]) -> SymbolGroup:
        """Create from dictionary for YAML deserialization."""
        return cls(
            canonical_symbol=canonical_symbol,
            synonyms=data.get("synonyms", []),
            isins=data.get("ISINs", []),
        )


@dataclass
class MappingPlan:
    """Represents a mapping plan with all symbol and ISIN mappings."""

    symbol_mappings: dict[str, str]  # alternative_symbol -> canonical_symbol
    isin_mappings: dict[str, str]  # isin -> canonical_symbol
    suggestions: list[Suggestion]  # unresolved conflicts that need user input

    @property
    def accepted_suggestions(self) -> list[Suggestion]:
        return [s for s in self.suggestions if s.status == SuggestionStatus.ACCEPTED]

    @property
    def declined_suggestions(self) -> list[Suggestion]:
        return [s for s in self.suggestions if s.status == SuggestionStatus.DECLINED]

    @property
    def pending_suggestions(self) -> list[Suggestion]:
        return [s for s in self.suggestions if s.status == SuggestionStatus.PENDING]
