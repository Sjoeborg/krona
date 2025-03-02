from unittest.mock import patch

from krona.processor.mapper import Mapper


def test_symbol_mapper_exact_match():
    mapper = Mapper()
    known_symbols = {"Evolution", "Investor B", "Volvo B"}

    # Test exact match
    assert mapper.match_symbol("Evolution", known_symbols) == "Evolution"
    assert mapper.match_symbol("Investor B", known_symbols) == "Investor B"
    assert mapper.match_symbol("Volvo B", known_symbols) == "Volvo B"


def test_symbol_mapper_ticker_mapping():
    mapper = Mapper()

    # Add mappings
    mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO", "Evolution Gaming"])
    mapper.add_mapping("Investor B", ["INVE B", "Investor ser. B"])

    known_symbols = {"Evolution", "Investor B", "Volvo B"}

    # Test ticker mapping
    assert mapper.match_symbol("Evolution Gaming Group", known_symbols) == "Evolution"
    assert mapper.match_symbol("EVO", known_symbols) == "Evolution"
    assert mapper.match_symbol("INVE B", known_symbols) == "Investor B"


def test_symbol_mapper_no_match():
    mapper = Mapper()
    known_symbols = {"Evolution", "Investor B", "Volvo B"}

    # Test no match - mock the interactive resolution to return None
    with patch.object(mapper, "_prompt_user_for_resolution", return_value=None):
        assert mapper.match_symbol("Microsoft", known_symbols) is None


def test_get_ticker():
    mapper = Mapper()
    mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO"])

    # Test getting ticker
    assert mapper.get_ticker("Evolution") == "Evolution"
    assert mapper.get_ticker("Evolution Gaming Group") == "Evolution"
    assert mapper.get_ticker("EVO") == "Evolution"
    assert mapper.get_ticker("Unknown") == "Unknown"  # Returns the input if not found


def test_symbol_mapper_automatic_resolution():
    # Create a symbol mapper with some mappings
    symbol_mapper = Mapper()
    symbol_mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO"])

    # Test automatic resolution
    known_symbols = {"Evolution", "Investor B"}
    assert symbol_mapper.match_symbol("Evolution", known_symbols) == "Evolution"
    assert symbol_mapper.match_symbol("Evolution Gaming Group", known_symbols) == "Evolution"
    assert symbol_mapper.match_symbol("EVO", known_symbols) == "Evolution"


def test_symbol_mapper_isin_resolution():
    # Create a symbol mapper with some mappings including ISINs
    symbol_mapper = Mapper()
    symbol_mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO"], isin="SE0012673267")

    # Test ISIN resolution
    known_symbols = {"Evolution", "Investor B"}
    assert symbol_mapper.match_symbol("Evo", known_symbols, "SE0012673267") == "Evolution"


def test_symbol_mapper_fuzzy_matching():
    # Create a symbol mapper
    symbol_mapper = Mapper()

    # Test fuzzy matching
    known_symbols = {"Evolution", "Investor B"}
    # This should match "Evolution" with a high score
    assert symbol_mapper.match_symbol("Evoluton", known_symbols) == "Evolution"
    # This should not match anything (score too low)
    with patch.object(symbol_mapper, "_prompt_user_for_resolution", return_value=None):
        assert symbol_mapper.match_symbol("XYZ", known_symbols) is None


def test_symbol_mapper_get_ticker():
    # Create a symbol mapper with some mappings
    symbol_mapper = Mapper()
    symbol_mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO"], isin="SE0012673267")

    # Test get_ticker with ISIN
    assert symbol_mapper.get_ticker("Unknown", "SE0012673267") == "Evolution"
    # Test get_ticker without ISIN
    assert symbol_mapper.get_ticker("Evolution Gaming Group") == "Evolution"
