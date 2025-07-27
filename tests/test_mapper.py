from unittest.mock import patch

from krona.processor.mapper import Mapper


def test_mapper_exact_match():
    mapper = Mapper()
    known_symbols = {"Evolution", "Investor B", "Volvo B"}

    # Test exact match
    assert mapper._match_symbol("Evolution", known_symbols) == "Evolution"
    assert mapper._match_symbol("Investor B", known_symbols) == "Investor B"
    assert mapper._match_symbol("Volvo B", known_symbols) == "Volvo B"


def test_mapper_ticker_mapping():
    mapper = Mapper()

    # Add mappings
    mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO", "Evolution Gaming"])
    mapper.add_mapping("Investor B", ["INVE B", "Investor ser. B"])

    known_symbols = {"Evolution", "Investor B", "Volvo B"}

    # Test ticker mapping
    assert mapper._match_symbol("Evolution Gaming Group", known_symbols) == "Evolution"
    assert mapper._match_symbol("EVO", known_symbols) == "Evolution"
    assert mapper._match_symbol("INVE B", known_symbols) == "Investor B"


def test_mapper_no_match():
    mapper = Mapper()
    known_symbols = {"Evolution", "Investor B", "Volvo B"}

    # Test no match - mock the interactive resolution to return None
    with patch.object(mapper, "_prompt_user_for_resolution", return_value=None):
        assert mapper._match_symbol("Microsoft", known_symbols) is None


def test_get_ticker():
    mapper = Mapper()
    mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO"])

    # Test getting ticker
    assert mapper._get_ticker("Evolution") == "Evolution"
    assert mapper._get_ticker("Evolution Gaming Group") == "Evolution"
    assert mapper._get_ticker("EVO") == "Evolution"
    assert mapper._get_ticker("Unknown") == "Unknown"  # Returns the input if not found


def test_mapper_automatic_resolution():
    mapper = Mapper()
    mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO"])

    # Test automatic resolution
    known_symbols = {"Evolution", "Investor B"}
    assert mapper._match_symbol("Evolution", known_symbols) == "Evolution"
    assert mapper._match_symbol("Evolution Gaming Group", known_symbols) == "Evolution"
    assert mapper._match_symbol("EVO", known_symbols) == "Evolution"


def test_mapper_isin_resolution():
    mapper = Mapper()
    mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO"], isin="SE0012673267")

    # Test ISIN resolution
    known_symbols = {"Evolution", "Investor B"}
    assert mapper._match_symbol("Evo", known_symbols, "SE0012673267") == "Evolution"


def test_mapper_fuzzy_matching():
    mapper = Mapper()

    # Test fuzzy matching
    known_symbols = {"Evolution", "Investor B"}
    # This should match "Evolution" with a high score

    assert mapper._match_symbol("Evolution AB", known_symbols) == "Evolution"
    # This should not match anything (score too low)
    with patch.object(mapper, "_prompt_user_for_resolution", return_value=None):
        assert mapper._match_symbol("XYZ", known_symbols) is None


def test_mapper_get_ticker():
    # Create a mapper with some mappings
    mapper = Mapper()
    mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO"], isin="SE0012673267")

    # Test get_ticker with ISIN
    assert mapper._get_ticker("Unknown", "SE0012673267") == "Evolution"
    # Test get_ticker without ISIN
    assert mapper._get_ticker("Evolution Gaming Group") == "Evolution"
