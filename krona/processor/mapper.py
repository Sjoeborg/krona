"""Mapping functionality to handle different attribute representations across brokers.

This module provides a two-phase approach:
1. Preprocessing: Analyze all transactions, identify conflicts, create resolution plan
2. Processing: Execute the accepted plan
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from thefuzz import fuzz

from krona.models.position import Position
from krona.models.transaction import Transaction  # type: ignore
from krona.utils.logger import logger


@dataclass
class SymbolGroup:
    """Represents a group of symbols and ISINs that map to a canonical symbol."""

    canonical_symbol: str
    synonyms: list[str]
    isins: list[str]

    def __post_init__(self):
        # Ensure lists are initialized
        if self.synonyms is None:
            self.synonyms = []
        if self.isins is None:
            self.isins = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {"synonyms": self.synonyms, "ISINs": self.isins}

    @classmethod
    def from_dict(cls, canonical_symbol: str, data: dict[str, Any]) -> SymbolGroup:
        """Create from dictionary for YAML deserialization."""
        return cls(canonical_symbol=canonical_symbol, synonyms=data.get("synonyms", []), isins=data.get("ISINs", []))


@dataclass
class MappingPlan:
    """Represents a mapping plan with all symbol and ISIN mappings."""

    symbol_mappings: dict[str, str]  # alternative_symbol -> canonical_symbol
    isin_mappings: dict[str, str]  # isin -> canonical_symbol
    conflicts: list[str]  # unresolved conflicts that need user input
    accepted_suggestions: list[str]  # suggestions that have been accepted
    denied_suggestions: list[str]  # suggestions that have been denied


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

    def _match_symbol(self, symbol: str, known_symbols: set[str], isin: str | None = None) -> str | None:
        """Match a symbol to a known symbol using exact and fuzzy matching."""
        # Try exact match first
        if symbol in known_symbols:
            return symbol

        # Try symbol mapping first
        if symbol in self._symbol_mappings:
            canonical = self._symbol_mappings[symbol]
            if canonical in known_symbols:
                return canonical

        # Try case-insensitive match
        for known_symbol in known_symbols:
            if known_symbol.lower() == symbol.lower():
                return known_symbol

        # Try fuzzy matching
        for known_symbol in known_symbols:
            if self._fuzzy_match(symbol, known_symbol):
                return known_symbol

        # Try ISIN matching if ISIN is provided
        if isin and isin in self._isin_mappings:
            canonical = self._isin_mappings[isin]
            if canonical in known_symbols:
                return canonical

        return None

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
        fuzzy_suggestions = self._find_fuzzy_matches(symbol_to_isins, isin_to_symbols)

        # Add fuzzy matches to conflicts for user review
        conflicts = self._detect_conflicts(symbol_mappings, isin_mappings)
        conflicts.extend(fuzzy_suggestions)

        # Load previously accepted/denied suggestions
        accepted_suggestions, denied_suggestions = self._load_previous_decisions()

        return MappingPlan(
            symbol_mappings=symbol_mappings,
            isin_mappings=isin_mappings,
            conflicts=conflicts,
            accepted_suggestions=accepted_suggestions,
            denied_suggestions=denied_suggestions,
        )

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

        # Try exact match first
        if canonical_symbol in positions:
            return canonical_symbol

        # Try case-insensitive match
        for position_symbol in positions:
            if position_symbol.lower() == canonical_symbol.lower():
                return position_symbol

        # Try fuzzy matching as fallback
        for position_symbol in positions:
            if self._fuzzy_match(canonical_symbol, position_symbol):
                return position_symbol

        # Try direct ISIN matching if transaction has an ISIN
        if transaction.ISIN:
            for position_symbol, position in positions.items():
                if position.ISIN == transaction.ISIN:
                    return position_symbol

        return None

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
        """Load existing mappings from the mappings.yml file."""
        mappings_path = Path("mappings.yml")
        if not mappings_path.exists():
            return

        try:
            with open(mappings_path) as f:
                data = yaml.safe_load(f)
                if not data:
                    return

                for canonical_symbol, group_data in data.items():
                    group = SymbolGroup.from_dict(canonical_symbol, group_data)
                    self._symbol_groups[canonical_symbol] = group

                    # Create backward-compatible mappings
                    for synonym in group.synonyms:
                        self._symbol_mappings[synonym] = canonical_symbol
                    for isin in group.isins:
                        self._isin_mappings[isin] = canonical_symbol
        except Exception as e:
            logger.warning(f"Failed to load mappings.yml: {e}")

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

    def save_decisions(self, accepted_suggestions: list[str], denied_suggestions: list[str], path: Path) -> None:
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
        existing_data["accepted_suggestions"] = accepted_suggestions
        existing_data["denied_suggestions"] = denied_suggestions

        with open(path, "w") as f:
            yaml.dump(existing_data, f, default_flow_style=False, sort_keys=True)

    def _load_previous_decisions(self) -> tuple[list[str], list[str]]:
        """Load previously accepted and denied suggestions from mappings.yml."""
        decisions_path = Path("mappings.yml")
        if not decisions_path.exists():
            return [], []

        try:
            with open(decisions_path) as f:
                data = yaml.safe_load(f)
                if not data:
                    return [], []

                # Check if this is the new format with decisions
                if isinstance(data, dict) and ("accepted_suggestions" in data or "denied_suggestions" in data):
                    return data.get("accepted_suggestions", []), data.get("denied_suggestions", [])
                else:
                    # Old format - no previous decisions
                    return [], []
        except Exception as e:
            logger.warning(f"Failed to load decisions from mappings.yml: {e}")
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

    def _detect_conflicts(self, symbol_mappings: dict[str, str], isin_mappings: dict[str, str]) -> list[str]:
        """Detect conflicts in mappings."""
        conflicts = []

        # Check for circular mappings
        for source, target in symbol_mappings.items():
            if target in symbol_mappings and symbol_mappings[target] == source:
                conflicts.append(f"Circular mapping: {source} <-> {target}")

        return conflicts

    def _fuzzy_match(self, symbol1: str, symbol2: str) -> bool:
        """Enhanced fuzzy matching for symbols using multiple strategies."""
        # Remove common suffixes and prefixes
        s1 = symbol1.replace("_OLD", "").replace("_NEW", "").replace(".OLD/X", "").strip()
        s2 = symbol2.replace("_OLD", "").replace("_NEW", "").replace(".OLD/X", "").strip()

        # Try exact match first (case insensitive)
        if s1.lower() == s2.lower():
            return True

        # Use multiple fuzzy matching strategies
        ratio = fuzz.ratio(s1.lower(), s2.lower())
        partial_ratio = fuzz.partial_ratio(s1.lower(), s2.lower())
        token_sort_ratio = fuzz.token_sort_ratio(s1.lower(), s2.lower())
        token_set_ratio = fuzz.token_set_ratio(s1.lower(), s2.lower())

        # Check if any of the ratios are high enough
        if ratio >= 80 or partial_ratio >= 80 or token_sort_ratio >= 80 or token_set_ratio >= 80:
            return True

        # Special cases for common patterns
        # Handle cases like "SWEDISH MATCH" vs "SWMA" (acronyms)
        return (len(s1) <= 4 and len(s2) > 4 and self._is_acronym(s1, s2)) or (
            len(s2) <= 4 and len(s1) > 4 and self._is_acronym(s2, s1)
        )

    def _is_acronym(self, short: str, long: str) -> bool:
        """Check if short string could be an acronym of long string."""
        # Remove common words that are often omitted in acronyms
        common_words = {
            "AB",
            "AKTIEBOLAG",
            "GAMING",
            "GROUP",
            "GR",
            "HOLDING",
            "HLD",
            "INTERNATIONAL",
            "INT",
            "CORPORATION",
            "CORP",
        }

        # Split long string into words
        words = long.upper().split()

        # Filter out common words
        filtered_words = [word for word in words if word not in common_words]

        # Check if short string matches first letters of filtered words
        if len(filtered_words) >= len(short):
            acronym = "".join(word[0] for word in filtered_words[: len(short)])
            return acronym == short.upper()

        return False

    def _find_fuzzy_matches(
        self, symbol_to_isins: dict[str, set[str]], isin_to_symbols: dict[str, set[str]]
    ) -> list[str]:
        """Find potential fuzzy matches for symbols that share ISINs or are similar with different ISINs."""
        suggestions = []

        # Group symbols by ISIN
        for isin, symbols in isin_to_symbols.items():
            if len(symbols) > 1:
                symbol_list = list(symbols)

                # Check each pair of symbols for fuzzy matches
                for i, symbol1 in enumerate(symbol_list):
                    for symbol2 in symbol_list[i + 1 :]:
                        # Skip if already mapped
                        if symbol1 in self._symbol_mappings or symbol2 in self._symbol_mappings:
                            continue

                        # Check fuzzy match
                        if self._fuzzy_match(symbol1, symbol2):
                            similarity = fuzz.ratio(symbol1.lower(), symbol2.lower())
                            suggestions.append(
                                (
                                    similarity,
                                    f"Fuzzy match ({similarity}%): '{symbol1}' and '{symbol2}' share ISIN {isin}",
                                )
                            )

        # Also check for potential corporate actions (similar symbols with different ISINs)
        all_symbols = list(symbol_to_isins.keys())
        for i, symbol1 in enumerate(all_symbols):
            for symbol2 in all_symbols[i + 1 :]:
                # Skip if already mapped
                if symbol1 in self._symbol_mappings or symbol2 in self._symbol_mappings:
                    continue

                # Check if symbols are very similar (higher threshold for different ISINs)
                if self._fuzzy_match_corporate_action(symbol1, symbol2):
                    similarity = fuzz.ratio(symbol1.lower(), symbol2.lower())
                    # Only suggest if similarity is above minimum threshold
                    if similarity >= 25:
                        isin1 = next(iter(symbol_to_isins[symbol1])) if symbol_to_isins[symbol1] else "Unknown"
                        isin2 = next(iter(symbol_to_isins[symbol2])) if symbol_to_isins[symbol2] else "Unknown"
                        suggestions.append(
                            (
                                similarity,
                                f"Potential corporate action ({similarity}%): '{symbol1}' ({isin1}) and '{symbol2}' ({isin2})",
                            )
                        )

        # Sort by similarity (highest first) and return only the suggestion strings
        suggestions.sort(key=lambda x: x[0], reverse=True)
        return [suggestion[1] for suggestion in suggestions]

    def _fuzzy_match_corporate_action(self, symbol1: str, symbol2: str) -> bool:
        """Enhanced fuzzy matching for potential corporate actions."""
        # Remove common suffixes and prefixes
        s1 = symbol1.replace("_OLD", "").replace("_NEW", "").replace(".OLD/X", "").strip()
        s2 = symbol2.replace("_OLD", "").replace("_NEW", "").replace(".OLD/X", "").strip()

        # Try exact match first (case insensitive)
        if s1.lower() == s2.lower():
            return True

        # Use multiple fuzzy matching strategies with higher threshold for corporate actions
        ratio = fuzz.ratio(s1.lower(), s2.lower())
        partial_ratio = fuzz.partial_ratio(s1.lower(), s2.lower())
        token_sort_ratio = fuzz.token_sort_ratio(s1.lower(), s2.lower())
        token_set_ratio = fuzz.token_set_ratio(s1.lower(), s2.lower())

        # Higher threshold for corporate actions (90% instead of 85%)
        if ratio > 90 or partial_ratio > 90 or token_sort_ratio > 90 or token_set_ratio > 90:
            return True

        # Special cases for corporate actions
        # Handle cases like "EVOLUTION GAMING GR" vs "Evolution"
        return bool(self._is_corporate_action_match(s1, s2))

    def _is_corporate_action_match(self, symbol1: str, symbol2: str) -> bool:
        """Check if two symbols might be related through a corporate action."""
        s1_lower = symbol1.lower()
        s2_lower = symbol2.lower()

        # Handle Evolution Gaming case
        if (
            "evolution" in s1_lower
            and "evolution" in s2_lower
            and (
                ("gaming gr" in s1_lower and "gaming gr" not in s2_lower)
                or ("gaming gr" in s2_lower and "gaming gr" not in s1_lower)
            )
        ):
            return True

        # Handle other common corporate action patterns
        # Remove common corporate suffixes and compare
        suffixes_to_remove = [" gaming gr", " group", " gr", " ab", " aktiebolag", " corp", " corporation"]

        s1_clean = s1_lower
        s2_clean = s2_lower

        for suffix in suffixes_to_remove:
            s1_clean = s1_clean.replace(suffix, "")
            s2_clean = s2_clean.replace(suffix, "")

        return bool(s1_clean == s2_clean and s1_clean)
