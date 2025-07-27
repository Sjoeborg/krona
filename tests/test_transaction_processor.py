from datetime import datetime

from krona.models.transaction import Transaction, TransactionType
from krona.processor.transaction import TransactionProcessor


def test_transaction_processor():
    processor = TransactionProcessor()
    transactions = [
        Transaction(
            date=datetime.strptime("2017-09-15", "%Y-%m-%d"),
            symbol="Bahnhof B",
            transaction_type=TransactionType.BUY,
            currency="SEK",
            ISIN="SE0002252296",
            quantity=92,
            price=53,
            fees=12.0,
        ),
        Transaction(
            date=datetime.strptime("2017-10-17", "%Y-%m-%d"),
            symbol="Bahnhof B",
            transaction_type=TransactionType.SELL,
            currency="SEK",
            ISIN="SE0002252296",
            quantity=26,
            price=41.2,
            fees=3,
        ),
        Transaction(
            date=datetime.strptime("2017-10-17", "%Y-%m-%d"),
            symbol="Bahnhof B",
            transaction_type=TransactionType.BUY,
            currency="SEK",
            ISIN="SE0010442418",
            quantity=25,
            price=39.45,
            fees=19,
        ),
    ]

    processor.add_transaction(transactions[0])
    assert processor.positions["Bahnhof B"].quantity == transactions[0].quantity
    assert (
        round(processor.positions["Bahnhof B"].cost_basis, 2)
        == transactions[0].quantity * transactions[0].price + transactions[0].fees
    )
    assert round(processor.positions["Bahnhof B"].price, 2) == round(
        (transactions[0].quantity * transactions[0].price + transactions[0].fees) / transactions[0].quantity, 2
    )
    assert round(processor.positions["Bahnhof B"].fees, 2) == transactions[0].fees
    assert round(processor.positions["Bahnhof B"].dividends, 2) == 0

    processor.add_transaction(transactions[1])
    processor.add_transaction(transactions[2])

    # after 3 transactions
    assert processor.positions["Bahnhof B"].quantity == 91
    assert round(processor.positions["Bahnhof B"].price, 2) == round(
        ((92 * 53 + 12) / 92 * 66 + 25 * 39.45 + 19) / (92 - 26 + 25), 2
    )
    assert round(processor.positions["Bahnhof B"].fees, 2) == 34.0
    assert round(processor.positions["Bahnhof B"].dividends, 2) == 0.00


def test_isin_matching():
    """Test that transactions with different symbols but the same ISIN are matched correctly."""
    processor = TransactionProcessor()

    # First transaction with a specific symbol and ISIN
    transaction1 = Transaction(
        date=datetime.strptime("2023-01-15", "%Y-%m-%d"),
        symbol="Evolution Gaming",
        transaction_type=TransactionType.BUY,
        currency="SEK",
        ISIN="SE0012673267",
        quantity=10,
        price=1000,
        fees=39.0,
    )

    # Second transaction with a different symbol but the same ISIN
    transaction2 = Transaction(
        date=datetime.strptime("2023-02-15", "%Y-%m-%d"),
        symbol="EVO",
        transaction_type=TransactionType.BUY,
        currency="SEK",
        ISIN="SE0012673267",
        quantity=5,
        price=1100,
        fees=39.0,
    )

    # Process the first transaction
    processor.add_transaction(transaction1)
    assert "Evolution Gaming" in processor.positions
    assert processor.positions["Evolution Gaming"].quantity == 10

    # Process the second transaction - it should be matched to the first position
    processor.add_transaction(transaction2)

    # Verify that we still have only one position
    assert len(processor.positions) == 1
    assert "Evolution Gaming" in processor.positions

    # Verify that the quantities have been combined
    assert processor.positions["Evolution Gaming"].quantity == 15

    # Verify that the price has been updated correctly
    expected_price = (10 * 1000 + 39 + 5 * 1100 + 39) / 15
    assert round(processor.positions["Evolution Gaming"].price, 2) == round(expected_price, 2)


def test_split():
    processor = TransactionProcessor()
    processor.mapper.add_mapping("BAHN B.OLD/X", ["BAHN B", "BAHN B.OLD/X"], isin="SE0002252296")
    # Manually create transactions
    transactions = [
        Transaction(
            date=datetime.strptime("2017-09-15", "%Y-%m-%d"),
            symbol="BAHN B.OLD/X",
            transaction_type=TransactionType.BUY,
            currency="SEK",
            ISIN="SE0002252296",
            quantity=23,
            price=214.5,
            fees=19.0,
        ),
        Transaction(
            date=datetime.strptime("2017-10-17", "%Y-%m-%d"),
            symbol="BAHN B.OLD/X",
            transaction_type=TransactionType.SPLIT,
            currency="SEK",
            ISIN="SE0002252296",
            quantity=23,
            price=0.0,
            fees=0.0,
        ),
        Transaction(
            date=datetime.strptime("2017-10-17", "%Y-%m-%d"),
            symbol="BAHN B",
            transaction_type=TransactionType.SPLIT,
            currency="SEK",
            ISIN="SE0010442418",
            quantity=230,
            price=0.0,
            fees=0.0,
        ),
        Transaction(
            date=datetime.strptime("2018-11-29", "%Y-%m-%d"),
            symbol="BAHN B",
            transaction_type=TransactionType.BUY,
            currency="SEK",
            ISIN="SE0010442418",
            quantity=30,
            price=30.1,
            fees=19.0,
        ),
    ]
    for transaction in transactions[0:3]:
        print(f"Processing {transaction}")
        processor.add_transaction(transaction)
        print(f"Positions: {processor.positions["BAHN B.OLD/X"]}")

    assert processor.positions["BAHN B.OLD/X"].quantity == 230
    assert processor.positions["BAHN B.OLD/X"].fees == 19.0
    assert round(processor.positions["BAHN B.OLD/X"].price, 2) == round((214.5 * 23 + 19) / 230, 2)

    processor.add_transaction(transactions[3])

    assert processor.positions["BAHN B.OLD/X"].quantity == 230 + 30
    assert processor.positions["BAHN B.OLD/X"].fees == 19 * 2
    assert round(processor.positions["BAHN B.OLD/X"].price, 2) == round((214.5 * 23 + 19 + 30.1 * 30 + 19) / 260, 2)


def test_different_symbols_same_isin():
    """Test that transactions with completely different symbols but the same ISIN are automatically mapped.

    This test verifies that the mapper can automatically map transactions with different symbols
    but the same ISIN without requiring fuzzy matching or explicit mappings.
    """
    processor = TransactionProcessor()

    # First transaction with a specific symbol and ISIN
    transaction1 = Transaction(
        date=datetime.strptime("2023-01-15", "%Y-%m-%d"),
        symbol="Bahnhof Series B",  # Completely different from standard format
        transaction_type=TransactionType.BUY,
        currency="SEK",
        ISIN="SE0010442418",  # BAHN B ISIN
        quantity=50,
        price=35.5,
        fees=19.0,
    )

    # Second transaction with a different symbol but the same ISIN
    transaction2 = Transaction(
        date=datetime.strptime("2023-02-15", "%Y-%m-%d"),
        symbol="BAHNHOF B",  # Different capitalization and format
        transaction_type=TransactionType.BUY,
        currency="SEK",
        ISIN="SE0010442418",  # Same ISIN
        quantity=25,
        price=36.8,
        fees=19.0,
    )

    # Process the first transaction
    processor.add_transaction(transaction1)
    assert "Bahnhof Series B" in processor.positions
    assert processor.positions["Bahnhof Series B"].quantity == 50
    assert processor.positions["Bahnhof Series B"].ISIN == "SE0010442418"

    # Process the second transaction - it should be matched to the first position
    processor.add_transaction(transaction2)

    # Verify that we still have only one position
    assert len(processor.positions) == 1
    assert "Bahnhof Series B" in processor.positions

    # Verify that the quantities have been combined
    assert processor.positions["Bahnhof Series B"].quantity == 75

    # Verify that the price has been updated correctly
    expected_price = (50 * 35.5 + 19 + 25 * 36.8 + 19) / 75
    assert round(processor.positions["Bahnhof Series B"].price, 2) == round(expected_price, 2)

    # Verify that the ISIN is still correct
    assert processor.positions["Bahnhof Series B"].ISIN == "SE0010442418"

    # Verify that the mapper now has the correct mappings
    assert processor.mapper._isin_mappings["SE0010442418"] == "Bahnhof Series B"

    # Create a third transaction with yet another symbol variation but same ISIN
    transaction3 = Transaction(
        date=datetime.strptime("2023-03-15", "%Y-%m-%d"),
        symbol="Bahnhof B Aktie",  # Another variation
        transaction_type=TransactionType.BUY,
        currency="SEK",
        ISIN="SE0010442418",  # Same ISIN
        quantity=15,
        price=38.2,
        fees=19.0,
    )

    # Process the third transaction
    processor.add_transaction(transaction3)

    # Verify that we still have only one position
    assert len(processor.positions) == 1

    # Verify that the quantities have been combined
    assert processor.positions["Bahnhof Series B"].quantity == 90

    # Verify the updated price
    expected_price = (50 * 35.5 + 25 * 36.8 + 15 * 38.2 + 19 * 3) / 90
    assert round(processor.positions["Bahnhof Series B"].price, 2) == round(expected_price, 2)
