import logging

from krona.models.position import Position
from krona.models.transaction import Transaction, TransactionType
from krona.processor.action import ActionProcessor
from krona.processor.mapper import Mapper

logger = logging.getLogger(__name__)


class TransactionProcessor:
    """Handles business logic for transactions"""

    def __init__(self) -> None:
        """Initialize the transaction processor."""
        self.positions: dict[str, Position] = {}
        self.action_processor = ActionProcessor()
        self.mapper = Mapper()

    def _upsert_position(self, transaction: Transaction, symbol: str | None) -> None:
        """Upsert a position with a new transaction"""

        # Create a new position if symbol does not exist, otherwise update the existing position
        position = Position.new(transaction) if symbol is None else self.positions[symbol]

        # If this is a new position and it has an ISIN, add the mapping
        if symbol is None and transaction.ISIN and position.symbol:
            # Add the mapping between the position symbol and ISIN
            self.mapper.add_mapping(position.symbol, [position.symbol], transaction.ISIN)
            logger.debug(f"Added mapping for new position: {position.symbol} with ISIN {transaction.ISIN}")

        match transaction.transaction_type:
            case TransactionType.BUY:
                self._handle_buy(transaction, position)
            case TransactionType.SELL:
                self._handle_sell(transaction, position)
            case TransactionType.DIVIDEND:
                self._handle_dividend(transaction, position)
            case TransactionType.SPLIT:
                self._handle_split(transaction, position)
        position.fees += transaction.fees
        position.transactions.append(transaction)
        self.positions[position.symbol] = position

    def _handle_buy(self, transaction: Transaction, position: Position) -> None:
        position.price = (
            transaction.price * transaction.quantity + transaction.fees + position.price * position.quantity
        ) / (position.quantity + transaction.quantity)
        position.quantity += transaction.quantity

    def _handle_sell(self, transaction: Transaction, position: Position) -> None:
        position.quantity -= transaction.quantity

    def _handle_dividend(self, transaction: Transaction, position: Position) -> None:
        position.dividends += transaction.price * transaction.quantity

    def _handle_split(self, transaction: Transaction, position: Position) -> None:
        """Handle a split transaction and update the mapper with the new ISIN if needed."""
        # Process the split using the action processor
        self.action_processor.handle_split(transaction, position)

        # If the transaction has a different ISIN than the position, add a mapping
        if transaction.ISIN and transaction.ISIN != position.ISIN:
            # Add the new symbol and ISIN to the mapper, mapping to the position's symbol
            self.mapper.add_mapping(position.symbol, [transaction.symbol], transaction.ISIN)
            logger.debug(
                f"Added mapping for split: {transaction.symbol} with ISIN {transaction.ISIN} -> {position.symbol}"
            )

            # Update the position's ISIN
            position.ISIN = transaction.ISIN

    def add_transaction(self, transaction: Transaction) -> None:
        """Process a new transaction and upsert position"""
        # Use the mapper to match the transaction to an existing position
        matched_symbol = self.mapper.match_transaction_to_position(transaction, self.positions)

        # Process the transaction
        self._upsert_position(transaction, matched_symbol)

        logger.debug(f"Processed transaction {transaction}")
