from datetime import date

from krona.models.position import Position
from krona.models.transaction import Transaction, TransactionType
from krona.processor.transaction import TransactionProcessor


def test_add_transaction():
    processor = TransactionProcessor()
    transaction = Transaction(
        date=date(2023, 1, 1),
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        ISIN="US0378331005",
        quantity=10,
        price=150,
        fees=10,
        currency="USD",
    )
    processor.add_transaction(transaction)

    assert "AAPL" in processor.positions
    assert processor.positions["AAPL"].quantity == 10


def test_find_or_create_position_existing_by_symbol():
    processor = TransactionProcessor()
    processor.positions["AAPL"] = Position.new(
        Transaction(
            date=date(2023, 1, 1),
            transaction_type=TransactionType.BUY,
            symbol="AAPL",
            ISIN="US0378331005",
            quantity=10,
            price=150,
            fees=10,
            currency="USD",
        )
    )
    transaction = Transaction(
        date=date(2023, 1, 2),
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        ISIN="US0378331005",
        quantity=5,
        price=160,
        fees=5,
        currency="USD",
    )
    position, symbol = processor._find_or_create_position(transaction, "AAPL")

    assert symbol == "AAPL"
    assert position is not None
    assert position.ISIN == "US0378331005"


def test_find_or_create_position_existing_by_isin():
    processor = TransactionProcessor()
    processor.positions["Apple"] = Position.new(
        Transaction(
            date=date(2023, 1, 1),
            transaction_type=TransactionType.BUY,
            symbol="Apple",
            ISIN="US0378331005",
            quantity=10,
            price=150,
            fees=10,
            currency="USD",
        )
    )
    transaction = Transaction(
        date=date(2023, 1, 2),
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        ISIN="US0378331005",
        quantity=5,
        price=160,
        fees=5,
        currency="USD",
    )
    position, symbol = processor._find_or_create_position(transaction, "AAPL")

    assert symbol == "Apple"
    assert position is not None
    assert position.ISIN == "US0378331005"


def test_find_or_create_position_new():
    processor = TransactionProcessor()
    transaction = Transaction(
        date=date(2023, 1, 1),
        transaction_type=TransactionType.BUY,
        symbol="AAPL",
        ISIN="US0378331005",
        quantity=10,
        price=150,
        fees=10,
        currency="USD",
    )
    position, symbol = processor._find_or_create_position(transaction, "AAPL")

    assert symbol == "AAPL"
    assert position is not None
    assert position.ISIN == "US0378331005"
    assert position.quantity == 0  # Position is new
