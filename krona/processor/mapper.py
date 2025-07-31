"""Mapping functionality to handle different attribute representations across brokers.

This module provides a two-phase approach:
1. Preprocessing: Analyze all transactions, identify conflicts, create resolution plan
2. Processing: Execute the accepted plan
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

from krona.models.mapping import MappingPlan, SymbolGroup
from krona.models.position import Position
from krona.models.suggestion import Suggestion
from krona.models.transaction import Transaction  # type: ignore
from krona.processor.strategies.conflict_detection import ConflictDetectionStrategy
from krona.processor.strategies.fuzzy_match import FuzzyMatchStrategy
from krona.processor.strategies.fuzzy_match_position import FuzzyMatchPositionStrategy
from krona.utils.logger import logger


class Mapper:
    """Handles mapping of alternative symbols and ISINs to canonical symbols."""

    def __init__(self) -> None:
        self._symbol_groups: dict[str, SymbolGroup] = {}
        self._symbol_mappings: dict[str, str] = {}
        self._isin_mappings: dict[str, str] = {}

    def add_mapping(self, canonical: str, synonyms: list[str], isin: str | None = None) -> None:
        """Add a mapping from synonyms to a canonical symbol."""
        # Create or get the symbol group
        if canonical not in self._symbol_groups:
            self._symbol_groups[canonical] = SymbolGroup(canonical_symbol=canonical, synonyms=[], isins=[])

        group = self._symbol_groups[canonical]

        # Add synonyms
        for synonym in synonyms:
            if synonym != canonical and synonym not in group.synonyms:
                group.synonyms.append(synonym)
                self._symbol_mappings[synonym] = canonical

        # Add ISIN if provided
        if isin and isin not in group.isins:
            group.isins.append(isin)
            self._isin_mappings[isin] = canonical

    def _prompt_user_for_resolution(self, symbol: str, known_symbols: set[str]) -> str | None:
        """Prompt user for resolution of an unknown symbol. This is a stub for testing."""
        # This is a stub method for testing - in real usage, this would prompt the user
        # For now, return None to indicate no resolution
        return None

    def create_mapping_plan(self, transactions: list[Transaction]) -> MappingPlan:
        """Create a mapping plan from transactions."""
        # Group transactions by symbol and ISIN
        symbol_to_isins: dict[str, set[str]] = defaultdict(set)
        isin_to_symbols: dict[str, set[str]] = defaultdict(set)

        for transaction in transactions:
            if transaction.symbol and transaction.ISIN:
                symbol = transaction.symbol.strip()
                isin = transaction.ISIN.strip()
                symbol_to_isins[symbol].add(isin)
                isin_to_symbols[isin].add(symbol)

        # Load existing mappings first
        self._load_existing_mappings()

        # Create symbol mappings based on existing groups
        symbol_mappings = {}
        isin_mappings = {}

        # Use existing symbol groups to create mappings
        for canonical_symbol, group in self._symbol_groups.items():
            # Map all synonyms to canonical symbol
            for synonym in group.synonyms:
                symbol_mappings[synonym] = canonical_symbol

            # Map all ISINs to canonical symbol
            for isin in group.isins:
                isin_mappings[isin] = canonical_symbol

        # Find fuzzy matches for symbols that share ISINs
        plan = MappingPlan(
            symbol_mappings=symbol_mappings,
            isin_mappings=isin_mappings,
            suggestions=[],  # Initialize suggestions as empty
        )
        fuzzy_match_strategy = FuzzyMatchStrategy()
        fuzzy_match_strategy.execute(
            plan=plan,
            symbol_to_isins=symbol_to_isins,
            isin_to_symbols=isin_to_symbols,
            transactions=transactions,
        )

        # Add fuzzy matches to conflicts for user review
        conflict_detection_strategy = ConflictDetectionStrategy()
        conflict_detection_strategy.execute(plan=plan)

        # Load previously accepted/denied suggestions
        self._load_previous_decisions()

        return plan

    def accept_plan(self, plan: MappingPlan) -> None:
        """Accept a mapping plan and convert to symbol groups."""
        # Convert flat mappings to symbol groups
        self._convert_mappings_to_groups(plan.symbol_mappings, plan.isin_mappings)

        # Update internal mappings for backward compatibility
        self._symbol_mappings = plan.symbol_mappings
        self._isin_mappings = plan.isin_mappings

    def match_transaction_to_position(self, transaction: Transaction, positions: dict[str, Position]) -> str | None:
        """Match a transaction to an existing position."""
        canonical_symbol = self._get_canonical_symbol(transaction)
        strategy = FuzzyMatchPositionStrategy()
        return strategy.execute(
            transaction=transaction,
            positions=positions,
            canonical_symbol=canonical_symbol,
        )

    def _get_canonical_symbol(self, transaction: Transaction) -> str:
        """Get the canonical symbol for a transaction."""
        symbol = transaction.symbol or ""

        # Apply symbol mappings with cycle detection
        seen_symbols = set()
        max_iterations = 100  # Prevent infinite loops

        for _ in range(max_iterations):
            if symbol not in self._symbol_mappings:
                break
            if symbol in seen_symbols:
                logger.warning(f"Circular mapping detected for symbol: {symbol}")
                break
            seen_symbols.add(symbol)
            symbol = self._symbol_mappings[symbol]

        # If we have an ISIN, also check ISIN mappings
        if transaction.ISIN and transaction.ISIN in self._isin_mappings:
            isin_symbol = self._isin_mappings[transaction.ISIN]
            # If ISIN maps to a different symbol, use that
            if isin_symbol != symbol:
                symbol = isin_symbol

        return symbol

    def _get_ticker(self, symbol: str, isin: str | None = None) -> str:
        """Get the canonical ticker for a symbol."""
        # Try direct symbol mapping first
        if symbol in self._symbol_mappings:
            return self._symbol_mappings[symbol]

        # Try ISIN mapping if ISIN is provided
        if isin and isin in self._isin_mappings:
            return self._isin_mappings[isin]

        # Return the original symbol if no mapping found
        return symbol

    def _get_canonical_symbol_from_position(self, position_name: str) -> str | None:
        """Get the canonical symbol for a position name."""
        # Try direct symbol mapping first
        if position_name in self._symbol_mappings:
            return self._symbol_mappings[position_name]

        # Check if this position name is a canonical symbol
        if position_name in self._symbol_groups:
            return position_name

        # Check if any synonym maps to this position name
        for canonical, group in self._symbol_groups.items():
            if position_name in group.synonyms:
                return canonical

        return None

    def _convert_mappings_to_groups(self, symbol_mappings: dict[str, str], isin_mappings: dict[str, str]) -> None:
        """Convert flat mappings to symbol groups."""
        self._symbol_groups.clear()

        # Group by canonical symbols
        canonical_groups: dict[str, SymbolGroup] = {}

        # Process symbol mappings
        for source, target in symbol_mappings.items():
            if source != target:  # Skip identical mappings
                if target not in canonical_groups:
                    canonical_groups[target] = SymbolGroup(canonical_symbol=target, synonyms=[], isins=[])
                canonical_groups[target].synonyms.append(source)

        # Process ISIN mappings
        for isin, canonical_symbol in isin_mappings.items():
            if canonical_symbol not in canonical_groups:
                canonical_groups[canonical_symbol] = SymbolGroup(
                    canonical_symbol=canonical_symbol, synonyms=[], isins=[]
                )
            canonical_groups[canonical_symbol].isins.append(isin)

        # Consolidate related groups to avoid circular dependencies and merge synonyms
        self._symbol_groups = self._consolidate_symbol_groups(canonical_groups)

    def _consolidate_symbol_groups(self, groups: dict[str, SymbolGroup]) -> dict[str, SymbolGroup]:
        """Consolidate related symbol groups to avoid circular dependencies and merge synonyms."""
        if not groups:
            return groups

        # Create a mapping from any symbol to its canonical group
        symbol_to_group: dict[str, str] = {}
        for canonical, group in groups.items():
            symbol_to_group[canonical] = canonical
            for synonym in group.synonyms:
                symbol_to_group[synonym] = canonical

        # Find all connected components (groups that should be merged)
        merged_groups: dict[str, SymbolGroup] = {}
        processed_symbols = set()

        for canonical, _group in groups.items():
            if canonical in processed_symbols:
                continue

            # Find all related symbols using a more comprehensive approach
            related_symbols = set()
            to_process = {canonical}

            while to_process:
                current = to_process.pop()
                if current in related_symbols:
                    continue

                related_symbols.add(current)

                # Add all synonyms of current symbol
                if current in groups:
                    for synonym in groups[current].synonyms:
                        if synonym not in related_symbols:
                            to_process.add(synonym)

                # Add the canonical symbol that this symbol maps to
                if current in symbol_to_group:
                    target = symbol_to_group[current]
                    if target not in related_symbols:
                        to_process.add(target)

                # Add all symbols that map to current symbol
                for sym, target in symbol_to_group.items():
                    if target == current and sym not in related_symbols:
                        to_process.add(sym)

            # Choose the best canonical symbol from the related group
            # Prefer the one with the most descriptive name (longer, more mixed case)
            best_canonical = max(related_symbols, key=lambda s: (len(s), sum(1 for c in s if c.islower())))

            # Create a consolidated group
            consolidated_group = SymbolGroup(canonical_symbol=best_canonical, synonyms=[], isins=[])

            # Collect all synonyms and ISINs from related groups
            for symbol in related_symbols:
                if symbol in groups:
                    source_group = groups[symbol]
                    # Add synonyms (excluding the canonical symbol itself)
                    for synonym in source_group.synonyms:
                        if synonym != best_canonical and synonym not in consolidated_group.synonyms:
                            consolidated_group.synonyms.append(synonym)
                    # Add ISINs
                    for isin in source_group.isins:
                        if isin not in consolidated_group.isins:
                            consolidated_group.isins.append(isin)

            # Add the other canonical symbols as synonyms if they're not the chosen canonical
            for symbol in related_symbols:
                if symbol != best_canonical and symbol not in consolidated_group.synonyms:
                    consolidated_group.synonyms.append(symbol)

            merged_groups[best_canonical] = consolidated_group
            processed_symbols.update(related_symbols)

        return merged_groups

    def _load_existing_mappings(self) -> None:
        """Load existing mappings from the mappings.yml file with user prompt."""
        from krona.ui.cli import CLI

        existing_plan = CLI.prompt_load_existing_config()
        if not existing_plan:
            return

        try:
            # Load from the existing plan
            for source_symbol, canonical_symbol in existing_plan.symbol_mappings.items():
                self._symbol_mappings[source_symbol] = canonical_symbol

                # Update symbol groups
                if canonical_symbol not in self._symbol_groups:
                    self._symbol_groups[canonical_symbol] = SymbolGroup(canonical_symbol=canonical_symbol)
                if source_symbol not in self._symbol_groups[canonical_symbol].synonyms:
                    self._symbol_groups[canonical_symbol].synonyms.append(source_symbol)

            for isin, canonical_symbol in existing_plan.isin_mappings.items():
                self._isin_mappings[isin] = canonical_symbol

                # Update symbol groups
                if canonical_symbol not in self._symbol_groups:
                    self._symbol_groups[canonical_symbol] = SymbolGroup(canonical_symbol=canonical_symbol)
                if isin not in self._symbol_groups[canonical_symbol].isins:
                    self._symbol_groups[canonical_symbol].isins.append(isin)

        except Exception as e:
            logger.warning(f"Failed to load existing mappings: {e}")

    def save_mappings(self, path: Path) -> None:
        """Save current mappings to a YAML file."""
        # Convert current mappings to groups if not already done
        if not self._symbol_groups:
            self._convert_mappings_to_groups(self._symbol_mappings, self._isin_mappings)

        # Convert to YAML format
        yaml_data = {}
        for canonical_symbol, group in self._symbol_groups.items():
            yaml_data[canonical_symbol] = group.to_dict()

        with open(path, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=True)

    def save_decisions(
        self,
        accepted_suggestions: list[Suggestion],
        denied_suggestions: list[Suggestion],
        path: Path,
    ) -> None:
        """Save accepted and denied suggestions to a YAML file."""
        # Load existing data if it exists
        existing_data = {}
        if path.exists():
            try:
                with open(path) as f:
                    existing_data = yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load existing mappings.yml: {e}")

        # Update with new decisions
        existing_data["accepted_suggestions"] = [s.rationale for s in accepted_suggestions]
        existing_data["denied_suggestions"] = [s.rationale for s in denied_suggestions]

        with open(path, "w") as f:
            yaml.dump(existing_data, f, default_flow_style=False, sort_keys=True)

    def _load_previous_decisions(self) -> tuple[list[str], list[str]]:
        """Load previously accepted and denied suggestions from mappings.yml."""
        return [], []

    def _select_canonical_isin(self, isins: set[str], transactions: list[Transaction]) -> str | None:
        """Select the canonical ISIN from a set of ISINs."""
        # Simple heuristic: use the ISIN with the most recent transaction
        isin_latest_dates = {}
        for isin in isins:
            if not isin:  # Skip empty ISINs
                continue
            isin_transactions = [t for t in transactions if isin == t.ISIN]
            if isin_transactions:
                latest_date = max(t.date for t in isin_transactions)
                isin_latest_dates[isin] = latest_date

        if isin_latest_dates:
            return max(isin_latest_dates.keys(), key=lambda isin: isin_latest_dates[isin])

        return None

    def _select_canonical_symbol(self, symbols: set[str], transactions: list[Transaction]) -> str | None:
        """Select the canonical symbol from a set of symbols."""
        # Simple heuristic: use the most common symbol
        symbol_counts = defaultdict(int)
        for transaction in transactions:
            if transaction.symbol:
                symbol_counts[transaction.symbol.strip()] += 1

        if symbol_counts:
            return max(symbol_counts.keys(), key=lambda symbol: symbol_counts[symbol])

        return None
