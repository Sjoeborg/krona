from datetime import datetime

import pytest

from krona.parsers.nordnet import NordnetParser
from krona.processor.transaction import Transaction, TransactionProcessor, TransactionType


def test_avanza_processor(capfd):
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
    assert processor._positions["Bahnhof B"].quantity == transactions[0].quantity
    assert round(processor._positions["Bahnhof B"].cost_basis, 2) == transactions[0].quantity * transactions[0].price
    assert round(processor._positions["Bahnhof B"].price, 2) == transactions[0].price
    assert round(processor._positions["Bahnhof B"].fees, 2) == transactions[0].fees
    assert (
        round(processor._positions["Bahnhof B"].dividends, 2) == 0
        if transactions[0].transaction_type != TransactionType.DIVIDEND
        else transactions[0].total_amount
    )

    processor.add_transaction(transactions[1])
    processor.add_transaction(transactions[2])

    # after 3 transactions
    assert processor._positions["Bahnhof B"].quantity == 91
    # assert round(processor._positions["Bahnhof B"].cost_basis, 2) == transactions[0].quantity * transactions[0].price + transactions[2].quantity * transactions[2].price
    assert round(processor._positions["Bahnhof B"].price, 2) == 50.1
    assert round(processor._positions["Bahnhof B"].fees, 2) == 34.0
    assert round(processor._positions["Bahnhof B"].dividends, 2) == 0.00

    # Capture and print the output
    out, err = capfd.readouterr()
    print(out)


def test_nordnet_processor(nordnet_file: str, nordnet_parser: NordnetParser, capfd):
    transactions = nordnet_parser.parse_file(nordnet_file)
    processor = TransactionProcessor()
    for transaction in transactions:
        processor.add_transaction(transaction)
        print(transaction)

    # print(processor._positions["BAHN B.OLD/X"])
    assert processor._positions["BAHN B.OLD/X"].quantity == 300
    # Capture and print the output
    out, err = capfd.readouterr()
    print(out)


@pytest.mark.split
def test_split(capfd):
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
        processor.add_transaction(transaction)

    assert processor._positions["BAHN B.OLD/X"].quantity == int(transactions[0].quantity * 10)
    assert processor._positions["BAHN B.OLD/X"].fees == transactions[0].fees
    assert round(processor._positions["BAHN B.OLD/X"].price, 2) == round(transactions[0].price / 10, 2)

    processor.add_transaction(transactions[3])

    assert (
        processor._positions["BAHN B.OLD/X"].quantity == int(transactions[0].quantity * 10) + transactions[3].quantity
    )
    assert processor._positions["BAHN B.OLD/X"].fees == transactions[0].fees + transactions[3].fees
    assert round(processor._positions["BAHN B.OLD/X"].price, 2) == round(
        (
            transactions[0].price / 10 * int(transactions[0].quantity * 10)
            + transactions[3].price * transactions[3].quantity
        )
        / (int(transactions[0].quantity * 10) + transactions[3].quantity),
        2,
    )
    print(processor._positions["BAHN B.OLD/X"])
    # Capture and print the output
    out, err = capfd.readouterr()
    print(out)
