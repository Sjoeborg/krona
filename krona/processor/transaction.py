from krona.models.position import Position
from krona.models.transaction import Transaction
from krona.processor.mapper import Mapper
from krona.utils.logger import logger


class TransactionProcessor:
    """Handles business logic for transactions"""

    def __init__(self) -> None:
        """Initialize the transaction processor."""
        self.positions: dict[str, Position] = {}
        self.history: dict[str, list[Transaction]] = {}
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

    def _find_or_create_position(self, transaction: Transaction, symbol: str | None) -> tuple[Position, str]:
        # Try to find a position by symbol first
        if symbol and symbol in self.positions:
            return self.positions[symbol], symbol

        # If no position is found by symbol, try to find one by ISIN
        if transaction.ISIN:
            for pos_symbol, position in self.positions.items():
                if position.ISIN == transaction.ISIN:
                    logger.debug(
                        f"Found position by ISIN ({transaction.ISIN}) for transaction "
                        f"{transaction.symbol}, mapping to {pos_symbol}"
                    )
                    return position, pos_symbol

        # If no position is found by symbol or ISIN, create a new one
        logger.debug(f"Creating new position for {transaction.symbol}")
        return Position.new(transaction), transaction.symbol

    def _upsert_position(self, transaction: Transaction, symbol: str | None) -> None:
        """Upsert a position with a new transaction"""
        position, symbol = self._find_or_create_position(transaction, symbol)
        position.apply_transaction(transaction)
        self.positions[symbol] = position
        self.history[symbol] = [*self.history.get(symbol, []), transaction]
