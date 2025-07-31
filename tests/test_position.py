from datetime import date

from pytest import approx

from krona.models.position import Position
from krona.models.transaction import Transaction, TransactionType


def test_position_apply_buy_transaction():
    position = Position.new(
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
    position.quantity = 10
    position.price = 150

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
    position.apply_transaction(transaction)

    assert position.quantity == 15
    assert position.price == approx((10 * 150 + 5 * 160 + 5) / 15)
    assert position.fees == 5


def test_position_apply_sell_transaction():
    position = Position.new(
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
    position.quantity = 10
    position.price = 150

    transaction = Transaction(
        date=date(2023, 1, 2),
        transaction_type=TransactionType.SELL,
        symbol="AAPL",
        ISIN="US0378331005",
        quantity=5,
        price=160,
        fees=5,
        currency="USD",
    )
    position.apply_transaction(transaction)

    assert position.quantity == 5
    assert position.price == approx(150)
    assert position.fees == 5


def test_position_apply_dividend_transaction():
    position = Position.new(
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
    position.quantity = 10
    position.price = 150

    transaction = Transaction(
        date=date(2023, 1, 2),
        transaction_type=TransactionType.DIVIDEND,
        symbol="AAPL",
        ISIN="US0378331005",
        quantity=10,
        price=0.23,
        fees=0,
        currency="USD",
    )
    position.apply_transaction(transaction)

    assert position.dividends == approx(2.3)
    assert position.fees == 0


def test_position_apply_split_transaction():
    position = Position.new(
        Transaction(
            date=date(2017, 9, 15),
            transaction_type=TransactionType.BUY,
            symbol="BAHN B",
            ISIN="SE0002252296",
            quantity=23,
            price=214.5,
            fees=19.0,
            currency="SEK",
        )
    )
    position.quantity = 23
    position.price = 214.5

    split1 = Transaction(
        date=date(2017, 10, 17),
        transaction_type=TransactionType.SPLIT,
        symbol="BAHN B",
        ISIN="SE0002252296",
        quantity=23,
        price=0,
        fees=0,
        currency="SEK",
    )
    position.apply_transaction(split1)

    assert len(position.transaction_buffer) == 1

    split2 = Transaction(
        date=date(2017, 10, 17),
        transaction_type=TransactionType.SPLIT,
        symbol="BAHN B",
        ISIN="SE0010442418",
        quantity=230,
        price=0,
        fees=0,
        currency="SEK",
    )
    position.apply_transaction(split2)

    assert position.quantity == 230
    assert position.price == approx(214.5 / 10)
    assert len(position.transaction_buffer) == 0
