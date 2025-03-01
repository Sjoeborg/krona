from datetime import datetime

import pytest

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


@pytest.mark.split
def test_split():
    processor = TransactionProcessor()
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
