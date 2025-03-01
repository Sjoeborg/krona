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


def test_symbol_mapper_fuzzy_matching():
    mapper = Mapper()
    known_symbols = {"Evolution", "Investor B", "Volvo B"}

    # Test fuzzy matching with default cutoff (80)
    assert mapper.match_symbol("Evolutio", known_symbols) == "Evolution"
    assert mapper.match_symbol("Investor", known_symbols) == "Investor B"


def test_symbol_mapper_no_match():
    mapper = Mapper()
    known_symbols = {"Evolution", "Investor B", "Volvo B"}

    # Test no match
    assert mapper.match_symbol("Microsoft", known_symbols) is None
    assert mapper.match_symbol("Apple", known_symbols) is None


def test_symbol_mapper_default_mappings():
    mapper = Mapper.create_default_mapper()

    # Test that default mapper has some mappings
    assert len(mapper._mappings) > 0
    assert "Evolution" in mapper._mappings

    # Test that default mappings work
    known_symbols = {"Evolution"}
    assert mapper.match_symbol("Evolution Gaming Group", known_symbols) == "Evolution"


def test_get_ticker():
    mapper = Mapper()
    mapper.add_mapping("Evolution", ["Evolution Gaming Group", "EVO"])

    # Test getting ticker
    assert mapper.get_ticker("Evolution") == "Evolution"
    assert mapper.get_ticker("Evolution Gaming Group") == "Evolution"
    assert mapper.get_ticker("EVO") == "Evolution"

    # Test getting ticker for unknown symbol
    assert mapper.get_ticker("Microsoft") == "Microsoft"
