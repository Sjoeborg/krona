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
        logger.debug(
            f"Processing transaction: {transaction.symbol} ({transaction.ISIN}) - {transaction.transaction_type.value} - {transaction.quantity}"
        )

        # Use the mapper to match the transaction to an existing position
        matched_symbol = self.mapper.match_transaction_to_position(transaction, self.positions)
        if matched_symbol:
            transaction.symbol = matched_symbol
            logger.debug(f"Mapped transaction to existing position: {matched_symbol}")

        # Process the transaction
        self._upsert_position(transaction, matched_symbol)

        # Update position names if mappings have changed
        self._update_position_names()

        logger.debug(f"Processed transaction {transaction}")

    def _update_position_names(self) -> None:
        """Update position names based on current mappings."""
        # Create a mapping from old names to new names
        name_updates = {}

        for old_name in list(self.positions.keys()):
            # Check if this position should be renamed based on mappings
            canonical = self.mapper._get_canonical_symbol_from_position(old_name)
            if canonical and canonical != old_name:
                name_updates[old_name] = canonical

        # Apply the name updates
        for old_name, new_name in name_updates.items():
            if new_name not in self.positions:  # Only rename if new name doesn't exist
                position = self.positions.pop(old_name)
                position.symbol = new_name
                self.positions[new_name] = position
                logger.debug(f"Renamed position from {old_name} to {new_name}")

    def _upsert_position(self, transaction: Transaction, symbol: str | None) -> None:
        """Upsert a position with a new transaction"""

        # For split transactions, try to find an existing position with the same ISIN
        if transaction.transaction_type == TransactionType.SPLIT and transaction.ISIN:
            # Look for existing positions with the same ISIN
            matching_positions = []
            for existing_symbol, existing_position in self.positions.items():
                if existing_position.ISIN == transaction.ISIN:
                    matching_positions.append((existing_symbol, existing_position))

            if matching_positions:
                # If multiple positions exist with the same ISIN, prefer the one that's not the old symbol
                # (i.e., prefer the current symbol over the old symbol from before the split)
                current_symbol = None

                for existing_symbol, _existing_position in matching_positions:
                    if "OLD" in existing_symbol or ".OLD" in existing_symbol:
                        pass  # old_symbol was unused
                    else:
                        current_symbol = existing_symbol

                # Prefer the current symbol over the old symbol
                if current_symbol:
                    symbol = current_symbol
                    logger.debug(
                        f"Found existing position with same ISIN for split (preferring current): {current_symbol}"
                    )
                else:
                    symbol = matching_positions[0][0]
                    logger.debug(f"Found existing position with same ISIN for split: {symbol}")

        # Always check for existing positions with the same ISIN, regardless of mapper result
        existing_position_with_isin = None
        existing_symbol_with_isin = None

        if transaction.ISIN:
            for existing_symbol, existing_position in self.positions.items():
                if existing_position.ISIN == transaction.ISIN:
                    existing_position_with_isin = existing_position
                    existing_symbol_with_isin = existing_symbol
                    break

        # Create a new position if symbol does not exist, otherwise update the existing position
        if symbol is None or symbol not in self.positions:
            # Check if there's an existing position with the same ISIN that should be merged
            if existing_position_with_isin and existing_symbol_with_isin:
                # Found an existing position with the same ISIN, merge them
                logger.debug(
                    f"Merging new position {transaction.symbol} with existing position {existing_symbol_with_isin} (same ISIN: {transaction.ISIN})"
                )
                symbol = existing_symbol_with_isin
                position = existing_position_with_isin
                # Update the position symbol to the new symbol if it's more current
                if "OLD" in existing_symbol_with_isin or ".OLD" in existing_symbol_with_isin:
                    # Remove the old position and create a new one with the current symbol
                    del self.positions[existing_symbol_with_isin]
                    position = Position.new(transaction)
                    position.symbol = transaction.symbol
                    symbol = transaction.symbol
                    logger.debug(
                        f"Replaced old position {existing_symbol_with_isin} with new position {transaction.symbol}"
                    )
            else:
                # No existing position with same ISIN, create new position
                position = Position.new(transaction)
        else:
            position = self.positions[symbol]

            # If we have a position with the same ISIN but different symbol, merge them
            if existing_position_with_isin and existing_symbol_with_isin and existing_symbol_with_isin != symbol:
                logger.debug(
                    f"Merging position {symbol} with existing position {existing_symbol_with_isin} (same ISIN: {transaction.ISIN})"
                )
                # Use the existing position with the same ISIN
                del self.positions[symbol]
                symbol = existing_symbol_with_isin
                position = existing_position_with_isin
                # Update the position symbol to the new symbol if it's more current
                if "OLD" in existing_symbol_with_isin or ".OLD" in existing_symbol_with_isin:
                    # Remove the old position and create a new one with the current symbol
                    del self.positions[existing_symbol_with_isin]
                    position = Position.new(transaction)
                    position.symbol = transaction.symbol
                    symbol = transaction.symbol
                    logger.debug(
                        f"Replaced old position {existing_symbol_with_isin} with new position {transaction.symbol}"
                    )

        # If this is a new position and it has an ISIN, add the mapping
        if symbol is None and transaction.ISIN and position.symbol:
            # self.mapper.add_mapping(position.symbol, [position.symbol], transaction.ISIN)
            logger.debug(f"Added mapping for new position: {position.symbol} with ISIN {transaction.ISIN}")

        # If we found an existing position with the same ISIN, create an ISIN mapping
        if (
            existing_position_with_isin
            and existing_symbol_with_isin
            and transaction.ISIN
            and transaction.ISIN not in self.mapper._isin_mappings
        ):
            self.mapper._isin_mappings[transaction.ISIN] = existing_symbol_with_isin
            logger.debug(f"Created automatic ISIN mapping: {transaction.ISIN} -> {existing_symbol_with_isin}")

        logger.debug(f"Processing {transaction.transaction_type.value} transaction for {transaction.symbol}")

        match transaction.transaction_type:
            case TransactionType.BUY:
                self._handle_buy(transaction, position)
            case TransactionType.SELL:
                self._handle_sell(transaction, position)
            case TransactionType.DIVIDEND:
                self._handle_dividend(transaction, position)
            case TransactionType.SPLIT:
                logger.debug(f"Handling split transaction: {transaction.symbol} -> {transaction.quantity}")
                # TODO: make more lenient by triggering this on any transaction type?
                self._handle_split(transaction, position)
            case TransactionType.MOVE:
                self._handle_move(transaction, position)
        position.fees += transaction.fees
        position.transactions.append(transaction)
        self.positions[position.symbol] = position
        self.history[position.symbol] = [*self.history.get(position.symbol, []), transaction]

    def _handle_buy(self, transaction: Transaction, position: Position) -> None:
        new_quantity = position.quantity + transaction.quantity

        # Check if the new quantity would be negative (which shouldn't happen for buys)
        if new_quantity < 0:
            logger.warning(
                "New quantity would be negative for buy transaction:\n"
                f"  {transaction}\n"
                "to position:\n"
                f"  {position}\n"
                "History:\n"
                f"  {'\n  '.join([str(t) for t in self.history.get(position.symbol, [])])}"
            )
            # Skip this transaction as it would create an invalid state
            return

        # Check for division by zero
        if new_quantity == 0:
            logger.warning(f"New quantity would be zero, skipping transaction: {transaction}")
            return

        # Calculate new average price
        position.price = (
            transaction.price * transaction.quantity + transaction.fees + position.price * position.quantity
        ) / new_quantity
        position.quantity = new_quantity

    def _handle_sell(self, transaction: Transaction, position: Position) -> None:
        new_quantity = position.quantity - transaction.quantity

        # Check if the new quantity would be negative
        if new_quantity < 0:
            logger.warning(
                "New quantity would be negative for sell transaction:\n"
                f"  {transaction}\n"
                "to position:\n"
                f"  {position}\n"
                "History:\n"
                f"  {'\n  '.join([str(t) for t in self.history.get(position.symbol, [])])}"
            )
            position.quantity = 0  # Close the position
            return

        position.quantity = new_quantity

    def _handle_dividend(self, transaction: Transaction, position: Position) -> None:
        position.dividends += transaction.price * transaction.quantity

    def _handle_split(self, transaction: Transaction, position: Position) -> None:
        """Handle a split transaction and update the mapper with the new ISIN if needed."""
        # Process the split using the action processor
        self.action_processor.handle_split(transaction, position, self.mapper)

    def _handle_move(self, transaction: Transaction, position: Position) -> None:
        """Handle a move transaction and update the mapper with the new ISIN if needed."""
        # TODO: how do we distinguish between a split and a move from another account? Do we need to do it?
        # Check for unresolved splits if we have/get a negative quantity?
        # Example: 2016-11-01;ISK;Övrigt;CORRECTIONS CORP COM
        # print(transaction)
        # print(position.transactions)
        # raise
        pass
