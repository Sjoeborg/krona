from dataclasses import dataclass
from typing import override

from krona.models.transaction import Transaction


@dataclass
class Position:
    """Represents a single position, immutable and with minimal logic"""

    symbol: str
    ISIN: str
    currency: str
    quantity: int
    buy_quantity: int
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
