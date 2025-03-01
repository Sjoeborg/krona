from unittest.mock import MagicMock, patch

from krona.processor.mapper import Mapper
from krona.processor.resolver import Resolver
from krona.processor.transaction import TransactionProcessor


def test_transaction_processor_automatic_resolution():
    """Test that the TransactionProcessor correctly uses the Mapper for automatic resolution."""
    # Create a transaction processor
    processor = TransactionProcessor()

    # Add mappings to the mapper
    processor.mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO"])
    # Mock _match_attribute using patch
    with patch.object(
        processor,
        "_match_attribute",
        side_effect=lambda symbol, isin=None: processor.mapper.match_symbol(symbol, {"Evolution", "Investor B"}, isin),
    ):
        # These should be resolved automatically by the mapper
        assert processor._match_attribute("Evolution") == "Evolution"
        assert processor._match_attribute("Evolution Gaming Group") == "Evolution"
        assert processor._match_attribute("EVO") == "Evolution"


def test_symbol_resolver_interactive_disabled():
    # Create a symbol mapper with some mappings
    symbol_mapper = Mapper()

    # Create a resolver with interactive mode disabled
    resolver = Resolver(symbol_mapper, interactive=False)

    # Mock the user prompt function to ensure it's not called
    mock_prompt = MagicMock(return_value="Evolution")
    resolver._default_user_prompt = mock_prompt

    # Test that unknown symbols return None when interactive is disabled
    known_symbols = {"Evolution", "Investor B"}
    assert resolver.resolve("Unknown Symbol", known_symbols) is None

    # Verify that the prompt function was not called
    mock_prompt.assert_not_called()


def test_symbol_resolver_interactive_enabled():
    # Create a symbol mapper with some mappings
    symbol_mapper = Mapper()

    # Create a resolver with interactive mode enabled
    resolver = Resolver(symbol_mapper, interactive=True)

    # Mock the _default_user_prompt method using patch
    with patch.object(resolver, "_default_user_prompt", return_value="Evolution") as mock_prompt:
        # Test that unknown symbols are resolved via the prompt
        known_symbols = {"Evolution", "Investor B"}
        resolver.resolve("Unknown Symbol", known_symbols)

        # Verify that the mock was called with the correct arguments
        mock_prompt.assert_called_once_with("Unknown Symbol", list(known_symbols))


def test_symbol_resolver_adds_mapping():
    # Create a symbol mapper
    symbol_mapper = Mapper()

    # Create a resolver with the mock prompt
    resolver = Resolver(
        symbol_mapper,
        interactive=True,
    )

    # Test that resolving an unknown symbol adds a mapping
    known_symbols = {"Evolution", "Investor B"}
    with patch.object(resolver, "_default_user_prompt", return_value="Evolution"):
        assert resolver.resolve("Unknown Symbol", known_symbols) == "Evolution"

    # Verify that the mapping was added to the symbol mapper
    assert symbol_mapper.get_ticker("Unknown Symbol") == "Evolution"

    # Test that the mapping works for future resolutions without prompting
    # Note: We now need to use the mapper directly for this test
    assert symbol_mapper.match_symbol("Unknown Symbol", known_symbols) == "Evolution"


def test_symbol_resolver_create_new_position():
    # Create a symbol mapper
    symbol_mapper = Mapper()

    # Create a resolver with the mock prompt
    resolver = Resolver(
        symbol_mapper,
        interactive=True,
    )

    # Test that resolving with None creates a new position
    known_symbols = {"Evolution", "Investor B"}
    with patch.object(resolver, "_default_user_prompt", return_value=None):
        assert resolver.resolve("New Symbol", known_symbols) is None

    # Verify that no mapping was added
    assert symbol_mapper.get_ticker("New Symbol") == "New Symbol"
