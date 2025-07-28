from krona.parsers.avanza import AvanzaParser
from krona.parsers.nordnet import NordnetParser
from krona.processor.transaction import TransactionProcessor


def test_final_position_matches_expected():
    """
    Test that processing transactions from both Nordnet and Avanza
    results in the expected final position for BAHN B.OLD/X.
    """
    processor = TransactionProcessor()
    processor.mapper.add_mapping("BAHN B", ["BAHN B.OLD/X"], isin="SE0002252296")
    # Parse and process Nordnet and Avanza transactions
    nordnet_parser = NordnetParser()
    avanza_parser = AvanzaParser()
    nordnet_file = "tests/data/transactions-and-notes-export.csv"
    avanza_file = "tests/data/transaktioner_2016-11-17_2024-12-15.csv"

    # Process all transactions
    for transaction in nordnet_parser.parse_file(nordnet_file):
        processor.add_transaction(transaction)
    for transaction in avanza_parser.parse_file(avanza_file):
        processor.add_transaction(transaction)

    # Verify the final position for BAHN B.OLD/X
    expected_position = "BAHN B (SE0010442418): 4961.60 SEK (92 @ 53.93) Dividends: 280.00. Fees: 454.00"

    # Find the position with ISIN SE0002252296
    bahn_position = None
    for _symbol, position in processor.positions.items():
        if position.ISIN == "SE0010442418":  # Use the actual ISIN from the data
            bahn_position = position
            break

    # Assert that the position exists
    assert bahn_position is not None, "Position with ISIN SE0010442418 not found"

    # Assert that the position string matches the expected string
    assert str(bahn_position) == expected_position, f"Expected: {expected_position}, Got: {bahn_position}"
