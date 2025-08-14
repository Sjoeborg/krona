"""Classes for different transaction types (Buy, Sell, Dividend)
Represents a single transaction, immutable and with minimal logic that's intrinsic to what a transaction is
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

SYNONYMS: dict[str, set[str]] = {
    "BUY": {"köp", "köpt"},
    "SELL": {"sälj", "sålt"},
    "DIVIDEND": {"utdelning"},
    "SPLIT": {"byte inlägg vp", "byte uttag vp", "Övrigt"},
    "MOVE": {"Värdepappersöverföring", "INLÄGG VP"},
}


class TransactionType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    SPLIT = "SPLIT"
    MOVE = "MOVE"

    @classmethod
    def from_term(cls, term: str) -> TransactionType:
        """Convert any recognized term to a TransactionType."""
        term = term.strip().lower()

        for type_name, synonyms in SYNONYMS.items():
            # TODO: make SYNONYMS better
            if term in [synonym.strip().lower() for synonym in synonyms]:
                return cls[type_name]

        raise ValueError(f"Unknown transaction type: '{term}'. Valid terms are: {SYNONYMS.values()}")


@dataclass
class Transaction:
    """Represents a single transaction, immutable and with minimal logic"""

    date: date
    symbol: str
    ISIN: str
    transaction_type: TransactionType
    currency: str
    quantity: int
    price: float
    fees: float

    @property
    def total_amount(self) -> float:
        return self.quantity * self.price + self.fees

    def __str__(self) -> str:
        return f"{self.date} - {self.symbol} ({self.ISIN}): {self.transaction_type.value} {self.total_amount:.2f} {self.currency} ({self.quantity} @ {self.price:.2f}) Fees: {self.fees:.2f}"
