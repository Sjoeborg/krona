from typing import TYPE_CHECKING, Any

from krona.processor.strategies.base import BaseStrategy
from krona.processor.strategies.fuzzy_match import _fuzzy_match
from krona.utils.io import get_config

if TYPE_CHECKING:
    from krona.models.position import Position
    from krona.models.transaction import Transaction


class FuzzyMatchPositionStrategy(BaseStrategy):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        if config is None:
            config = get_config()
        self.config = config["matching_strategies"]

    def execute(self, plan: None = None, **kwargs: Any) -> str | None:
        """Find potential fuzzy matches for a transaction in a list of positions."""
        transaction: Transaction = kwargs["transaction"]
        positions: dict[str, Position] = kwargs["positions"]
        canonical_symbol: str = kwargs["canonical_symbol"]

        # Try exact match first
        if canonical_symbol in positions:
            return canonical_symbol

        # Try case-insensitive match
        for position_symbol in positions:
            if position_symbol.lower() == canonical_symbol.lower():
                return position_symbol

        # Try fuzzy matching as fallback
        for position_symbol in positions:
            if _fuzzy_match(canonical_symbol, position_symbol, self.config["fuzzy_match"]):
                return position_symbol

        # Try direct ISIN matching if transaction has an ISIN
        if transaction.ISIN:
            for position_symbol, position in positions.items():
                if position.ISIN == transaction.ISIN:
                    return position_symbol

        return None
