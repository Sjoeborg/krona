"""Classes for different transaction types (Buy, Sell, Dividend)
Represents a single transaction, immutable and with minimal logic that's intrinsic to what a transaction is
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TransactionType(Enum):
    BUY = "köp"
    SELL = "sälj"
    DIVIDEND = "utdelning"


@dataclass
class Transaction:
    """Represents a single transaction, immutable and with minimal logic"""

    date: datetime
    symbol: str
    ISIN: str
    transaction_type: TransactionType
    currency: str
    quantity: float
    amount: float
    fees: float

    @property
    def total_amount(self) -> float:
        return self.quantity * self.amount + self.fees
