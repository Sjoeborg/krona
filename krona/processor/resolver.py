"""Resolution functionality for handling unknown attributes.

This module provides a way to interactively resolve unknown attributes by asking the user
to map them to existing attributes or create new ones.
"""

from __future__ import annotations

import logging

from krona.processor.mapper import Mapper

logger = logging.getLogger(__name__)


class Resolver:
    """Handles resolution of unknown symbols by asking the user."""

    def __init__(
        self,
        mapper: Mapper,
        interactive: bool = True,
    ) -> None:
        """Initialize the symbol resolver.

        Args:
            mapper: The mapper to use for resolving attributes
            interactive: Whether to interactively ask the user for resolution
        """
        self.mapper = mapper
        self.interactive = interactive
        # Cache of user resolutions to avoid asking multiple times for the same symbol
        self._resolution_cache: dict[str, str | None] = {}

    def resolve(self, symbol: str, known_symbols: set[str]) -> str | None:
        """Resolve a symbol to a known symbol or None.

        First tries automatic resolution via the symbol mapper. If that fails and
        interactive mode is enabled, asks the user to resolve the symbol.

        Args:
            symbol: The symbol to resolve
            known_symbols: Set of known symbols to match against

        Returns:
            The resolved symbol or None if no resolution is possible
        """
        # First try automatic resolution
        resolved = self.mapper.match_symbol(symbol, known_symbols)
        if resolved is not None:
            return resolved

        # If we're not in interactive mode or we have no known symbols, return None
        if not self.interactive or not known_symbols:
            return None

        # Check if we've already asked the user about this symbol
        if symbol in self._resolution_cache:
            return self._resolution_cache[symbol]

        # Ask the user to resolve the symbol
        user_choice = self._prompt_user_for_resolution(symbol, list(known_symbols))

        # Cache the result
        self._resolution_cache[symbol] = user_choice

        # If the user provided a mapping, add it to the symbol mapper
        if user_choice is not None and user_choice in known_symbols:
            self.mapper.add_mapping(user_choice, [symbol])
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
        return self._default_user_prompt(symbol, known_symbols)

    def _default_user_prompt(self, symbol: str, known_symbols: list[str]) -> str | None:
        """Default implementation of user prompt.

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

    def set_interactive(self, interactive: bool) -> None:
        """Set whether to interactively ask the user for resolution.

        Args:
            interactive: Whether to interactively ask the user for resolution
        """
        self.interactive = interactive

    def clear_cache(self) -> None:
        """Clear the resolution cache."""
        self._resolution_cache.clear()
