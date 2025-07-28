from krona.models.action import Action, ActionType
from krona.models.position import Position
from krona.models.transaction import Transaction
from krona.processor.mapper import Mapper
from krona.utils.logger import logger


class ActionProcessor:
    """Handles business logic for corporate actions"""

    def __init__(self) -> None:
        self.transaction_buffer: dict[str, list[Transaction]] = {}

    def handle_split(self, transaction: Transaction, position: Position, mapper: Mapper) -> None:
        """Handle stock split by calculating the split ratio from two SPLIT transactions.

        If the two SPLIT transactions have the same date, we assume that the split is NOT a reverse split.
        TODO: implement user resolution for reverse splits.
        """

        logger.debug(
            f"Processing split transaction: {transaction.symbol} ({transaction.ISIN}) with quantity {transaction.quantity}"
        )

        # Check if we have a previous split transaction for this symbol or its synonyms
        previous_transaction = None
        buffer_key = None

        # First try to find a previous transaction for the same symbol
        if transaction.symbol in self.transaction_buffer:
            previous_transaction = self.transaction_buffer[transaction.symbol][0]
            buffer_key = transaction.symbol
            logger.debug(f"Found previous transaction for same symbol: {previous_transaction.symbol}")
        else:
            for key, buffered_transactions in self.transaction_buffer.items():
                if buffered_transactions and buffered_transactions[0].date == transaction.date:
                    previous_transaction = buffered_transactions[0]
                    buffer_key = key
                    logger.debug(f"Found previous split transaction with same date: {previous_transaction.symbol}")
                    break

            if previous_transaction is None:
                # If no previous transaction found, buffer this one and return
                logger.debug(f"No previous split transaction found, buffering: {transaction.symbol}")
                self.transaction_buffer[transaction.symbol] = [transaction]
                return

        # Remove the previous transaction from buffer
        if buffer_key is not None:
            self.transaction_buffer.pop(buffer_key)

        # If dates are the same, ensure split ratio is greater than 1 by swapping transactions
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

        # Calculate new quantity and price
        new_quantity = position.quantity * split.ratio
        new_price = position.price / split.ratio

        # Handle floating-point precision issues
        new_quantity = 0 if abs(new_quantity) < 1e-10 else round(new_quantity)

        logger.info(
            f"Split {position.symbol} from {position.quantity} @ {position.price:.2f} to {new_quantity} @ {new_price:.2f} (split ratio: {split.ratio})"
        )

        position.price = new_price
        position.quantity = new_quantity

        # Add mappings between old and new symbols
        if split.old_symbol != split.new_symbol:
            logger.debug(f"Added split mapping: {split.old_symbol} -> {split.new_symbol} with ISIN {split.new_ISIN}")

        # Update the position's ISIN to the new ISIN
        if split.new_ISIN and split.new_ISIN != position.ISIN:
            # Add mapping for the new ISIN
            logger.debug(f"Added mapping for split: {split.new_symbol} with ISIN {split.new_ISIN} -> {position.symbol}")
            position.ISIN = split.new_ISIN

            # Also add mapping from old ISIN to new symbol for future transactions
            if split.old_ISIN and split.old_ISIN != split.new_ISIN:
                logger.debug(f"Added mapping from old ISIN {split.old_ISIN} to {split.new_symbol}")
