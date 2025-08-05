from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from krona.models.transaction import Transaction, TransactionType


@dataclass
class Position:
    """Represents a single position with minimal logic"""

    symbol: str
    ISIN: str
    currency: str | None
    quantity: int
    price: float
    dividends: float
    fees: float

    transactions: list[Transaction]
    transaction_buffer: list[Transaction] = field(default_factory=list)

    @property
    def cost_basis(self) -> float:
        return self.quantity * self.price

    @property
    def is_closed(self) -> bool:
        return self.quantity == 0

    @property
    def realized_profit(self) -> float | None:
        if self.is_closed:
            total_bought = sum([t.total_amount for t in self.transactions if t.transaction_type == TransactionType.BUY])
            total_sold = sum([t.total_amount for t in self.transactions if t.transaction_type == TransactionType.SELL])
            return total_sold - total_bought + self.dividends - self.fees
        else:
            return None

    @override
    def __str__(self) -> str:
        # Handle very small quantities to avoid scientific notation
        if abs(self.quantity) < 1e-10:
            quantity_str = "0.0"
        else:
            quantity_str = f"{self.quantity:.1f}" if self.quantity % 1 != 0 else f"{int(self.quantity)}"

        if self.is_closed:
            return f"--CLOSED--{self.symbol} ({self.ISIN}): {self.cost_basis:.2f} {self.currency} ({quantity_str} @ {self.price:.2f}) Dividends: {self.dividends:.2f}. Fees: {self.fees:.2f}. Realized profit: {self.realized_profit:.2f}"
        else:
            return f"{self.symbol} ({self.ISIN}): {self.cost_basis:.2f} {self.currency} ({quantity_str} @ {self.price:.2f}) Dividends: {self.dividends:.2f}. Fees: {self.fees:.2f}"

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
