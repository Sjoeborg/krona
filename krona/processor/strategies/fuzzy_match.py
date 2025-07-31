from typing import TYPE_CHECKING, Any

from thefuzz import fuzz

from krona.models.suggestion import Suggestion
from krona.models.transaction import Transaction
from krona.processor.strategies.base import BaseStrategy
from krona.utils.io import get_config

if TYPE_CHECKING:
    from krona.processor.mapper import MappingPlan


def _generate_rationale(
    source_isin: str | None,
    target_isin: str | None,
    transactions: list[Transaction],
) -> str:
    """Generate a rationale for the suggestion."""
    if source_isin and target_isin and source_isin != target_isin:
        # Find the earliest transaction date for the new ISIN to approximate split date
        split_date = None
        for t in sorted(transactions, key=lambda x: x.date):
            if target_isin == t.ISIN:
                split_date = t.date
                break
        if split_date:
            return f"ISIN change on {split_date.strftime('%Y-%m-%d')}"
        return "ISIN change"
    # ISINs are the same, but names are different
    return ""


def _fuzzy_match(symbol1: str, symbol2: str, config: dict[str, Any]) -> bool:
    """Enhanced fuzzy matching for symbols using multiple strategies."""
    # Try exact match first (case insensitive)
    if symbol1.lower() == symbol2.lower():
        return True

    # Use multiple fuzzy matching strategies
    ratio = fuzz.ratio(symbol1.lower(), symbol2.lower())
    partial_ratio = fuzz.partial_ratio(symbol1.lower(), symbol2.lower())
    token_sort_ratio = fuzz.token_sort_ratio(symbol1.lower(), symbol2.lower())
    token_set_ratio = fuzz.token_set_ratio(symbol1.lower(), symbol2.lower())

    # Check if any of the ratios are high enough
    return bool(
        ratio >= config["ratio"]
        or partial_ratio >= config["partial_ratio"]
        or token_sort_ratio >= config["token_sort_ratio"]
        or token_set_ratio >= config["token_set_ratio"]
    )


class FuzzyMatchStrategy(BaseStrategy):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        if config is None:
            config = get_config()
        self.config = config["matching_strategies"]

    def execute(self, **kwargs: Any) -> None:
        """Find potential fuzzy matches for symbols."""
        plan: MappingPlan = kwargs["plan"]
        symbol_to_isins: dict[str, set[str]] = kwargs["symbol_to_isins"]
        symbol_mappings: dict[str, str] = plan.symbol_mappings
        transactions: list[Transaction] = kwargs["transactions"]
        min_confidence = self.config.get("min_confidence", 0.1)

        suggestions: list[Suggestion] = []
        all_symbols = list(symbol_to_isins.keys())
        for i, symbol1 in enumerate(all_symbols):
            for symbol2 in all_symbols[i + 1 :]:
                if symbol1 in symbol_mappings or symbol2 in symbol_mappings:
                    continue

                if _fuzzy_match(symbol1, symbol2, self.config["fuzzy_match"]):
                    similarity = fuzz.ratio(symbol1.lower(), symbol2.lower()) / 100
                    if similarity < min_confidence:
                        continue

                    source_isins = symbol_to_isins.get(symbol1)
                    target_isins = symbol_to_isins.get(symbol2)

                    source_isin = next(iter(source_isins)) if source_isins else None
                    target_isin = next(iter(target_isins)) if target_isins else None

                    suggestions.append(
                        Suggestion(
                            source_symbol=symbol1,
                            target_symbol=symbol2,
                            source_isin=source_isin,
                            target_isin=target_isin,
                            confidence=similarity,
                            rationale=_generate_rationale(source_isin, target_isin, transactions),
                        )
                    )

        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        plan.suggestions.extend(suggestions)
