"""Classes for different transaction types (Buy, Sell, Dividend)
Represents a single transaction, immutable and with minimal logic that's intrinsic to what a transaction is
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import override

SYNONYMS: dict[str, set[str]] = {
    "BUY": {"köp", "köpt"},
    "SELL": {"sälj", "sålt"},
    "DIVIDEND": {"utdelning"},
    "SPLIT": {"byte inlägg vp", "byte uttag vp"},
}


class TransactionType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    SPLIT = "SPLIT"

    @classmethod
    def from_term(cls, term: str) -> TransactionType:
        """Convert any recognized term to a TransactionType."""
        term = term.strip().lower()

        for type_name, synonyms in SYNONYMS.items():
            if term in synonyms:
                return cls[type_name]

        raise ValueError(f"Unknown transaction type: '{term}'. Valid terms are: {cls.get_valid_terms()}")

    @classmethod
    def get_valid_terms(cls) -> set[str]:
        """Get all valid transaction terms."""
        return set().union(*SYNONYMS.values())


@dataclass
class Transaction:
    """Represents a single transaction, immutable and with minimal logic"""

    date: datetime
    symbol: str
    ISIN: str
    transaction_type: TransactionType
    currency: str
    quantity: int
    price: float
    fees: float

    @property
    def total_amount(self) -> float:
        # TODO: Check if the fee addition here is correct
        return self.quantity * self.price  # + self.fees

    @override
    def __str__(self) -> str:
        return f"{self.date} - {self.symbol} ({self.ISIN}) - {self.transaction_type.value} {self.total_amount:.2f} {self.currency} ({self.quantity} @ {self.price:.2f}) Fees: {self.fees:.2f}"
