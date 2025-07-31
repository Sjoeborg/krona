from typing import TYPE_CHECKING, Any

from krona.processor.strategies.base import BaseStrategy
from krona.utils.logger import logger

if TYPE_CHECKING:
    from krona.processor.mapper import MappingPlan


class ConflictDetectionStrategy(BaseStrategy):
    def execute(self, **kwargs: Any) -> None:
        """Detect and resolve conflicts in mappings."""
        plan: MappingPlan = kwargs["plan"]
        processed_symbols = set()

        # Convert to list to allow modification during iteration
        for source, target in list(plan.symbol_mappings.items()):
            if source in processed_symbols:
                continue

            # Check for circular mappings
            if target in plan.symbol_mappings and plan.symbol_mappings[target] == source:
                # Resolve circular mapping by choosing a canonical symbol
                symbols = [source, target]
                canonical_symbol = max(
                    symbols,
                    key=lambda s: (len(s), sum(1 for c in s if c.islower()), s),
                )
                synonym = target if source == canonical_symbol else source

                # Enforce the mapping and remove the circular dependency
                plan.symbol_mappings[synonym] = canonical_symbol
                if plan.symbol_mappings.get(canonical_symbol) == synonym:
                    del plan.symbol_mappings[canonical_symbol]

                logger.info(f"Resolved circular mapping: {synonym} -> {canonical_symbol}")

                processed_symbols.add(source)
                processed_symbols.add(target)
