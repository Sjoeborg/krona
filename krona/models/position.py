from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from krona.models.action import Action, ActionType
from krona.models.transaction import Transaction, TransactionType
from krona.utils.logger import logger


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

    def apply_transaction(self, transaction: Transaction) -> None:
        """Apply a transaction to the position."""
        logger.debug(f"Applying transaction to position {self.symbol}: {transaction.transaction_type.value}")

        match transaction.transaction_type:
            case TransactionType.BUY:
                self._handle_buy(transaction)
            case TransactionType.SELL:
                self._handle_sell(transaction)
            case TransactionType.DIVIDEND:
                self._handle_dividend(transaction)
            case TransactionType.SPLIT:
                self._handle_split(transaction)
            case TransactionType.MOVE:
                self._handle_move(transaction)

        self.fees += transaction.fees
        self.transactions.append(transaction)

    def _handle_buy(self, transaction: Transaction) -> None:
        new_quantity = self.quantity + transaction.quantity

        if new_quantity < 0:
            logger.warning(
                f"New quantity would be negative for buy transaction:\n  {transaction}\nto position:\n  {self}\n"
            )
            return

        if new_quantity == 0:
            logger.warning(f"New quantity would be zero, skipping transaction: {transaction}")
            return

        self.price = (
            transaction.price * transaction.quantity + transaction.fees + self.price * self.quantity
        ) / new_quantity
        self.quantity = new_quantity

    def _handle_sell(self, transaction: Transaction) -> None:
        new_quantity = self.quantity - transaction.quantity

        if new_quantity < 0:
            logger.warning(
                f"New quantity would be negative for sell transaction:\n  {transaction}\nto position:\n  {self}\n"
            )
            self.quantity = 0
            return

        self.quantity = new_quantity

    def _handle_dividend(self, transaction: Transaction) -> None:
        self.dividends += transaction.price * transaction.quantity

    def _handle_split(self, transaction: Transaction) -> None:
        logger.debug(
            f"Processing split transaction: {transaction.symbol} ({transaction.ISIN}) with quantity {transaction.quantity}"
        )

        previous_transaction = None
        if self.transaction_buffer:
            previous_transaction = self.transaction_buffer.pop(0)

        if previous_transaction is None:
            logger.debug(f"No previous split transaction found, buffering: {transaction.symbol}")
            self.transaction_buffer.append(transaction)
            return

        if previous_transaction.date == transaction.date and transaction.quantity / previous_transaction.quantity < 1:
            logger.warning(
                f"Assuming split ratio is {previous_transaction.quantity / transaction.quantity} for {transaction.symbol} at {transaction.date}. No reverse split is supported."
            )
            transaction, previous_transaction = previous_transaction, transaction

        split_ratio = transaction.quantity / previous_transaction.quantity

        split = Action(
            date=transaction.date,
            new_symbol=transaction.symbol,
            old_symbol=previous_transaction.symbol,
            new_ISIN=transaction.ISIN,
            old_ISIN=previous_transaction.ISIN,
            type=ActionType.SPLIT,
            ratio=split_ratio,
        )

        new_quantity = self.quantity * split.ratio
        new_price = self.price / split.ratio

        new_quantity = 0 if abs(new_quantity) < 1e-10 else round(new_quantity)

        logger.info(
            f"Split {self.symbol} from {self.quantity} @ {self.price:.2f} to {new_quantity} @ {new_price:.2f} (split ratio: {split.ratio})"
        )

        self.price = new_price
        self.quantity = new_quantity

        if split.new_ISIN and split.new_ISIN != self.ISIN:
            self.ISIN = split.new_ISIN

    def _handle_move(self, transaction: Transaction) -> None:
        # Logic to be moved from TransactionProcessor
        pass

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
