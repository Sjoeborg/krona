import logging

from krona.models.position import Position
from krona.models.transaction import Transaction, TransactionType
from krona.processor.action import ActionProcessor
from krona.processor.mapper import Mapper
from krona.processor.resolver import Resolver

logger = logging.getLogger(__name__)


class TransactionProcessor:
    """Handles business logic for transactions"""

    def __init__(self) -> None:
        """Initialize the transaction processor.

        Args:
            mapper: Optional custom mapper to use
            interactive: Whether to interactively ask the user to resolve unknown attributes
            user_prompt_func: Optional custom function to prompt the user for attribute resolution
        """
        self.positions: dict[str, Position] = {}
        self.action_processor = ActionProcessor()
        self.mapper = Mapper()
        self.resolver = Resolver(
            mapper=self.mapper,
        )

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
        # First, try to match the symbol to an existing position
        matched_symbol = self._match_attribute(transaction.symbol, transaction.ISIN)

        # If we have an ISIN, try to match by ISIN as well
        if transaction.ISIN and matched_symbol is None:
            # Check if any existing position has this ISIN
            for position_symbol, position in self.positions.items():
                if position.ISIN == transaction.ISIN:
                    matched_symbol = position_symbol
                    # Add the mapping between the transaction symbol and the position symbol
                    if transaction.symbol:
                        self.mapper.add_mapping(position_symbol, [transaction.symbol], transaction.ISIN)
                        logger.debug(
                            f"Added ISIN-based mapping: {transaction.symbol} -> {position_symbol} via ISIN {transaction.ISIN}"
                        )
                    break

        # Process the transaction
        self._upsert_position(transaction, matched_symbol)

        # If this is a new position (matched_symbol is None), add the symbol and ISIN to the mapper
        if matched_symbol is None and transaction.symbol:
            position_symbol = transaction.symbol
            # Add the mapping between the symbol and ISIN if available
            if transaction.ISIN:
                self.mapper.add_mapping(position_symbol, [position_symbol], transaction.ISIN)
                logger.debug(f"Added mapping for new position: {position_symbol} with ISIN {transaction.ISIN}")

        logger.debug(f"Processed transaction {transaction}")
        if matched_symbol:
            logger.debug(f"Position: {self.positions[matched_symbol]}")

    def _match_attribute(self, symbol: str, isin: str | None = None) -> str | None:
        """Match an attribute to an existing position using the mapper.

        This will first try automatic matching using the mapper, and if that fails and interactive mode
        is enabled, it will use the resolver to ask the user to resolve the attribute.

        Args:
            symbol: The symbol to match
            isin: Optional ISIN to help with matching

        Returns:
            The matched symbol or None if no match is found
        """
        # First try automatic matching with the mapper
        matched_symbol = self.mapper.match_symbol(symbol, set(self.positions.keys()), isin)

        # If automatic matching failed, use the resolver
        if matched_symbol is None:
            matched_symbol = self.resolver.resolve(symbol, set(self.positions.keys()))

        return matched_symbol

    def add_mapping(self, ticker: str, alternative_symbols: list[str], isin: str | None = None) -> None:
        """Add a mapping between a ticker and its alternatives.

        Args:
            ticker: The primary/standard ticker symbol to use
            alternative_symbols: List of alternative representations of the same symbol
            isin: The ISIN of the security
        """
        self.mapper.add_mapping(ticker, alternative_symbols, isin)

    def clear_resolution_cache(self) -> None:
        """Clear the attribute resolution cache."""
        self.resolver.clear_cache()
