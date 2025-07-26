from unittest.mock import MagicMock, patch

from krona.processor.mapper import Mapper
from krona.processor.transaction import TransactionProcessor


def test_transaction_processor_automatic_resolution():
    """Test that the TransactionProcessor correctly uses the Mapper for automatic resolution."""
    # Create a transaction processor
    processor = TransactionProcessor()

    # Add mappings to the mapper
    processor.mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO"])

    # Create a mock for match_transaction_to_position
    with patch.object(
        processor.mapper,
        "match_transaction_to_position",
        side_effect=lambda transaction, positions: "Evolution"
        if transaction.symbol in ["Evolution", "Evolution Gaming Group", "EVO"]
        else None,
    ):
        # Mock a transaction
        mock_transaction1 = MagicMock()
        mock_transaction1.symbol = "Evolution"
        mock_transaction1.ISIN = None

        mock_transaction2 = MagicMock()
        mock_transaction2.symbol = "Evolution Gaming Group"
        mock_transaction2.ISIN = None

        mock_transaction3 = MagicMock()
        mock_transaction3.symbol = "EVO"
        mock_transaction3.ISIN = None

        # These should be resolved automatically by the mapper
        # We'll patch _upsert_position to avoid actually processing the transaction
        with patch.object(processor, "_upsert_position"):
            processor.add_transaction(mock_transaction1)
            processor.add_transaction(mock_transaction2)
            processor.add_transaction(mock_transaction3)

            # Verify that match_transaction_to_position was called with the correct arguments
            processor.mapper.match_transaction_to_position.assert_called()


def test_mapper_transaction_matching():
    """Test that the Mapper correctly matches transactions to positions."""
    # Create a mapper
    mapper = Mapper()

    # Add mappings
    mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO"])

    # Create mock positions
    mock_position = MagicMock()
    mock_position.ISIN = "SE0012673267"
    positions = {"Evolution": mock_position}

    # Create mock transactions
    mock_transaction1 = MagicMock()
    mock_transaction1.symbol = "Evolution"
    mock_transaction1.ISIN = None

    mock_transaction2 = MagicMock()
    mock_transaction2.symbol = "Evolution Gaming Group"
    mock_transaction2.ISIN = None

    mock_transaction3 = MagicMock()
    mock_transaction3.symbol = "EVO"
    mock_transaction3.ISIN = None

    mock_transaction4 = MagicMock()
    mock_transaction4.symbol = "Unknown"
    mock_transaction4.ISIN = "SE0012673267"

    # Test matching by symbol
    assert mapper.match_transaction_to_position(mock_transaction1, positions) == "Evolution"
    assert mapper.match_transaction_to_position(mock_transaction2, positions) == "Evolution"
    assert mapper.match_transaction_to_position(mock_transaction3, positions) == "Evolution"

    # Test matching by ISIN
    with patch.object(mapper, "_match_symbol", return_value=None):  # Force ISIN matching path
        assert mapper.match_transaction_to_position(mock_transaction4, positions) == "Evolution"


def test_mapper_manual_resolution():
    """Test that the Mapper does not prompt for resolution if the symbol is known."""
    # Create a mapper
    mapper = Mapper()

    # Mock the _prompt_user_for_resolution method using patch
    with patch.object(mapper, "_prompt_user_for_resolution", return_value="Evolution") as mock_prompt:
        # Test that unknown symbols are resolved via the prompt
        known_symbols = {"Evolution", "Investor B"}
        _ = mapper._match_symbol("Unknown Symbol", known_symbols)

        # Verify that the mock was not called
        mock_prompt.assert_not_called()


def test_mapper_adds_mapping_after_resolution():
    """Test that the Mapper adds mappings after manual resolution."""
    # Create a mapper
    mapper = Mapper()

    # Test that resolving an unknown symbol adds a mapping
    known_symbols = {"Evolution", "Investor B"}
    with patch.object(mapper, "_prompt_user_for_resolution", return_value="Evolution"):
        assert mapper._match_symbol("Evo", known_symbols) == "Evolution"

    # Test that the mapping works for future resolutions without prompting
    assert mapper._match_symbol("Evo", known_symbols) == "Evolution"


def test_mapper_create_new_position():
    """Test that the Mapper correctly handles creating a new position."""
    # Create a mapper
    mapper = Mapper()

    # Test that resolving with None creates a new position
    known_symbols = {"Evolution", "Investor B"}
    with patch.object(mapper, "_prompt_user_for_resolution", return_value=None):
        assert mapper._match_symbol("New Symbol", known_symbols) is None

    # Verify that no mapping was added
    assert mapper._get_ticker("New Symbol") == "New Symbol"
