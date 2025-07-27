from krona.models.position import Position
from krona.models.transaction import Transaction, TransactionType
from krona.processor.action import ActionProcessor
from krona.processor.mapper import Mapper
from krona.utils.logger import logger


class TransactionProcessor:
    """Handles business logic for transactions"""

    def __init__(self) -> None:
        """Initialize the transaction processor."""
        self.positions: dict[str, Position] = {}
        self.history: dict[str, list[Transaction]] = {}
        self.action_processor = ActionProcessor()
        self.mapper = Mapper()

    def add_transaction(self, transaction: Transaction) -> None:
        """Process a new transaction and upsert position"""
        # Use the mapper to match the transaction to an existing position
        matched_symbol = self.mapper.match_transaction_to_position(transaction, self.positions)

        # Process the transaction
        self._upsert_position(transaction, matched_symbol)

        logger.debug(f"Processed transaction {transaction}")

    def _upsert_position(self, transaction: Transaction, symbol: str | None) -> None:
        """Upsert a position with a new transaction"""

        # Create a new position if symbol does not exist, otherwise update the existing position
        position = (
            Position.new(transaction) if symbol is None or symbol not in self.positions else self.positions[symbol]
        )

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
                # TODO: make more lenient by triggering this on any transaction type?
                self._handle_split(transaction, position)
        position.fees += transaction.fees
        position.transactions.append(transaction)
        self.positions[position.symbol] = position
        self.history[position.symbol] = [*self.history.get(position.symbol, []), transaction]

    def _handle_buy(self, transaction: Transaction, position: Position) -> None:
        if position.quantity + transaction.quantity <= 0:
            logger.warning(
                "New quantity is not positive for adding transaction:\n"
                f"  {transaction}\n"
                "to position:\n"
                f"  {position}\n"
                "History:\n"
                f"  {'\n  '.join([str(t) for t in self.history[position.symbol]])}"
            )
            if position.quantity + transaction.quantity == 0:
                logger.warning(f"Was trying to divide by zero, skipping transaction: {transaction}")
                return
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

    def _handle_move_from_unknown_account(self, transaction: Transaction) -> None:
        """Handle a move from an unknown account."""
        # TODO: how do we distinguish between a split and a move from another account? Do we need to do it?
        # Check for unresolved splits if we have/get a negative quantity?
        # Example: 2016-11-01;ISK;Övrigt;CORRECTIONS CORP COM
        if transaction.transaction_type == TransactionType.SPLIT and transaction.price == 0:
            logger.warning("Transaction is probably a move from another account:\n %s", transaction)
