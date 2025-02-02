from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import override  # noqa: UP035

from krona.models.transaction import Transaction


@dataclass
class Position:
    """Represents a single position with minimal logic"""

    symbol: str
    ISIN: str
    currency: str
    quantity: int
    price: float
    dividends: float
    fees: float

    transactions: list[Transaction]

    @property
    def cost_basis(self) -> float:
        return self.quantity * self.price

    @override
    def __str__(self) -> str:
        return f"{self.symbol} ({self.ISIN}) - {self.cost_basis:.2f} {self.currency} ({self.quantity} @ {self.price:.2f}) Dividends: {self.dividends:.2f}. Fees: {self.fees:.2f}"

    @classmethod
    def new(cls, transaction: Transaction) -> Position:
        return Position(
            symbol=transaction.symbol,
            ISIN=transaction.ISIN,
            currency=transaction.currency,
            quantity=0,
            price=0,
            dividends=0,
            fees=0,
            transactions=[],
        )
