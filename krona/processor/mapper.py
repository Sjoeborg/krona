"""Mapping functionality to handle different attribute representations across brokers.

This module provides a way to map attributes between different brokers (e.g., Avanza and Nordnet)
using both explicit mappings and fuzzy matching.
"""

from __future__ import annotations

import logging
from typing import cast

from thefuzz import process  # type: ignore

logger = logging.getLogger(__name__)


class Mapper:
    """Maps attributes between different brokers using explicit mappings and fuzzy matching."""

    def __init__(self) -> None:
        # Dictionary mapping tickers to sets of alternative symbols
        self._mappings: dict[str, set[str]] = {}
        # Dictionary mapping alternative symbols to their ticker
        self._reverse_mappings: dict[str, str] = {}
        # New ISIN mappings
        self._isin_mappings: dict[str, str] = {}  # ISIN -> ticker
        # Default fuzzy match score cutoff
        self._fuzzy_match_cutoff = 80

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

    def add_mappings_from_dict(
        self, mappings: dict[str, list[str]], isin_mappings: dict[str, str] | None = None
    ) -> None:
        """Add multiple mappings from dictionaries.

        Args:
            mappings: Dictionary with tickers as keys and lists of alternatives as values
            isin_mappings: Optional dictionary with ISINs as keys and tickers as values
        """
        for ticker, alternatives in mappings.items():
            self.add_mapping(ticker, alternatives)

        if isin_mappings:
            for isin, ticker in isin_mappings.items():
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

    def match_symbol(self, symbol: str, known_symbols: set[str], isin: str | None = None) -> str | None:
        """Match a symbol to a known symbol using explicit mappings and fuzzy matching.

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

        logger.debug(f"No match found for {symbol}")
        return None

    @classmethod
    def create_default_mapper(cls) -> Mapper:
        """Create a Mapper with some common default mappings.

        Returns:
            A Mapper instance with default mappings
        """
        mapper = cls()

        # Add some common mappings between Avanza and Nordnet
        default_mappings = {
            "Evolution": ["Evolution Gaming Group", "EVO", "Evolution Gaming"],
            "Investor B": ["Investor B", "INVE B", "Investor ser. B"],
            "Volvo B": ["Volvo B", "VOLV B", "Volvo ser. B"],
        }

        # Add ISIN mappings
        default_isin_mappings = {
            "SE0012673267": "Evolution",
            "SE0015811559": "Investor B",
            "SE0000115446": "Volvo B",
        }

        mapper.add_mappings_from_dict(default_mappings, default_isin_mappings)
        return mapper
