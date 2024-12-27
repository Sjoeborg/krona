from collections import defaultdict

from krona.models.transaction import Transaction, TransactionType


class TransactionProcessor:
    """Handles business logic for transactions"""

    def __init__(self) -> None:
        self._positions: dict[str, list[Transaction]] = defaultdict(list)

    def add_transaction(self, transaction: Transaction) -> None:
        """Process a new transaction and update positions"""
        self._positions[transaction.symbol].append(transaction)

    def get_position(self, symbol: str) -> float | None:
        """Calculate current position for a symbol"""
        position = 0.0
        for t in self._positions[symbol]:
            if t.transaction_type == TransactionType.BUY:
                position += t.quantity
            elif t.transaction_type == TransactionType.SELL:
                position -= t.quantity
        return position if position != 0 else None

    def calculate_profit_loss(self, symbol: str) -> None:
        """Complex business logic for P&L calculation"""
        # Implementation of FIFO/average cost/etc.
        pass
