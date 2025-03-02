"""Mapping functionality to handle different attribute representations across brokers.

This module provides a way to map attributes between different brokers (e.g., Avanza and Nordnet)
using both explicit mappings, fuzzy matching, and interactive user resolution.
"""

from __future__ import annotations

import logging
from typing import cast

from thefuzz import process

from krona.models.position import Position
from krona.models.transaction import Transaction  # type: ignore

logger = logging.getLogger(__name__)


class Mapper:
    """Maps attributes between different brokers using explicit mappings, fuzzy matching, and interactive resolution."""

    def __init__(self) -> None:
        # Dictionary mapping tickers to sets of alternative symbols
        self._mappings: dict[str, set[str]] = {}
        # Dictionary mapping alternative symbols to their ticker
        self._reverse_mappings: dict[str, str] = {}
        # New ISIN mappings
        self._isin_mappings: dict[str, str] = {}  # ISIN -> ticker
        # Default fuzzy match score cutoff
        self._fuzzy_match_cutoff = 80
        # Cache of user resolutions to avoid asking multiple times for the same symbol
        self._resolution_cache: dict[str, str | None] = {}

    def add_mapping(self, ticker: str, alternative_symbols: list[str], isin: str | None = None) -> None:
        """Add a mapping between a ticker and its alternatives.

        Args:
            ticker: The primary/standard ticker symbol to use
            alternative_symbols: List of alternative representations of the same symbol
            isin: Optional ISIN code for the security
        """
        # Ensure ticker is in mappings
        if ticker not in self._mappings:
            self._mappings[ticker] = set()

        # Add all alternative symbols
        for alt_symbol in alternative_symbols:
            self._mappings[ticker].add(alt_symbol)
            self._reverse_mappings[alt_symbol] = ticker

        # Add ticker to its own alternatives for completeness
        self._mappings[ticker].add(ticker)
        self._reverse_mappings[ticker] = ticker

        # Add ISIN mapping if provided
        if isin:
            self._isin_mappings[isin] = ticker

    def get_ticker(self, symbol: str, isin: str | None = None) -> str:
        """Get the ticker for a symbol or ISIN.

        If the symbol is not in the explicit mappings or ISIN mappings, it is returned unchanged.
        If an ISIN is provided, it will be checked first before checking the symbol.

        Args:
            symbol: The symbol to get the ticker for
            isin: Optional ISIN to check for mappings

        Returns:
            The ticker for the symbol
        """
        # Check ISIN mappings first if an ISIN is provided
        if isin and isin in self._isin_mappings:
            logger.debug(f"Matched ISIN {isin} to {self._isin_mappings[isin]}")
            return self._isin_mappings[isin]

        # Fall back to regular mappings
        return self._reverse_mappings.get(symbol, symbol)

    def match_transaction_to_position(self, transaction: Transaction, positions: dict[str, Position]) -> str | None:
        """Match a transaction to an existing position using symbol, ISIN, and interactive resolution if needed.

        This method first tries to match the transaction symbol to an existing position.
        If that fails and an ISIN is provided, it tries to match by ISIN.
        If both fail, it will try interactive resolution.

        Args:
            transaction: The transaction to match
            positions: Dictionary of existing positions (symbol -> position)

        Returns:
            The matched position symbol or None if no match is found
        """
        transaction_symbol = transaction.symbol
        transaction_isin = transaction.ISIN

        # First, try to match the symbol to an existing position
        matched_symbol = self.match_symbol(transaction_symbol, set(positions.keys()), transaction_isin)

        # If we have an ISIN and no match yet, try to match by ISIN directly
        if transaction_isin and matched_symbol is None:
            # Check if any existing position has this ISIN
            for position_symbol, position in positions.items():
                if transaction_isin == position.ISIN:
                    matched_symbol = position_symbol
                    # Add the mapping between the transaction symbol and the position symbol
                    if transaction_symbol:
                        self.add_mapping(position_symbol, [transaction_symbol], transaction_isin)
                        logger.debug(
                            f"Added ISIN-based mapping: {transaction_symbol} -> {position_symbol} via ISIN {transaction_isin}"
                        )
                    break

        return matched_symbol

    def match_symbol(self, symbol: str, known_symbols: set[str], isin: str | None = None) -> str | None:
        """Match a symbol to a known symbol using explicit mappings, fuzzy matching, and interactive resolution.

        This method first tries automatic matching using explicit mappings and fuzzy matching.
        If automatic matching fails, it will try to resolve the symbol interactively by asking the user.

        Args:
            symbol: The symbol to match
            known_symbols: Set of known symbols to match against
            isin: Optional ISIN to help with matching

        Returns:
            The matched symbol or None if no match is found
        """
        # First try automatic matching
        matched_symbol = self._automatic_match(symbol, known_symbols, isin)

        # If automatic matching failed, try interactive resolution
        if matched_symbol is None:
            matched_symbol = self._interactive_resolve(symbol, known_symbols)

        return matched_symbol

    def _automatic_match(self, symbol: str, known_symbols: set[str], isin: str | None = None) -> str | None:
        """Automatically match a symbol using explicit mappings and fuzzy matching.

        Args:
            symbol: The symbol to match
            known_symbols: Set of known symbols to match against
            isin: Optional ISIN to help with matching

        Returns:
            The matched symbol or None if no match is found
        """
        # First check if we have an exact match
        if symbol in known_symbols:
            return symbol

        # Then check if we have a ticker mapping
        ticker = self.get_ticker(symbol, isin)
        if ticker in known_symbols:
            logger.debug(f"Mapped {symbol} to ticker {ticker}")
            return ticker

        # Check if any of the known symbols have a ticker that matches
        for known in known_symbols:
            known_ticker = self.get_ticker(known)
            if known_ticker == ticker:
                logger.debug(f"Matched {symbol} to {known} via ticker {ticker}")
                return known

        # Finally, try fuzzy matching
        matches = process.extractOne(symbol, known_symbols, score_cutoff=self._fuzzy_match_cutoff)
        if matches is not None:
            matched_symbol = cast(str, matches[0])
            score = cast(int, matches[1])
            logger.debug(f"Fuzzy matched {symbol} to {matched_symbol} with score {score}")
            return matched_symbol

        logger.debug(f"No automatic match found for {symbol}")
        return None

    def _interactive_resolve(self, symbol: str, known_symbols: set[str]) -> str | None:
        """Interactively resolve a symbol with user input.

        This method is called when automatic resolution has failed.

        Args:
            symbol: The symbol to resolve
            known_symbols: Set of known symbols to match against

        Returns:
            The resolved symbol or None if no resolution is possible
        """
        # If we have no known symbols, return None
        if not known_symbols:
            return None

        # Check if we've already asked the user about this symbol
        if symbol in self._resolution_cache:
            return self._resolution_cache[symbol]

        # Ask the user to resolve the symbol
        user_choice = self._prompt_user_for_resolution(symbol, list(known_symbols))

        # Cache the result
        self._resolution_cache[symbol] = user_choice

        # If the user provided a mapping, add it to the mappings
        if user_choice is not None and user_choice in known_symbols:
            self.add_mapping(user_choice, [symbol])
            logger.info(f"Added user-defined mapping: {symbol} -> {user_choice}")

        return user_choice

    def _prompt_user_for_resolution(self, symbol: str, known_symbols: list[str]) -> str | None:
        """Prompt the user to resolve a symbol.

        Args:
            symbol: The symbol to resolve
            known_symbols: List of known symbols to choose from

        Returns:
            The user's choice or None if they chose to create a new position
        """
        print(f"\nUnknown symbol: {symbol}")
        print("Choose an existing position to map to, or select 0 to create a new position:")

        for i, known in enumerate(known_symbols, 1):
            print(f"{i}. {known}")
        print("0. Create new position")

        while True:
            try:
                choice = input(f"Enter your choice (0-{len(known_symbols)}): ")
                choice_num = int(choice)

                if 0 <= choice_num <= len(known_symbols):
                    if choice_num == 0:
                        return None  # Create new position
                    else:
                        return known_symbols[choice_num - 1]
                else:
                    print(f"Invalid choice. Please enter a number between 0 and {len(known_symbols)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
