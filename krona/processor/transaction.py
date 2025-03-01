import logging

from krona.models.position import Position
from krona.models.transaction import Transaction, TransactionType
from krona.processor.action import ActionProcessor
from krona.processor.mapper import Mapper
from krona.processor.resolver import Resolver

logger = logging.getLogger(__name__)


class TransactionProcessor:
    """Handles business logic for transactions"""

    def __init__(
        self,
        interactive: bool = False,
    ) -> None:
        """Initialize the transaction processor.

        Args:
            mapper: Optional custom mapper to use
            interactive: Whether to interactively ask the user to resolve unknown attributes
            user_prompt_func: Optional custom function to prompt the user for attribute resolution
        """
        self.positions: dict[str, Position] = {}
        self.action_processor: ActionProcessor = ActionProcessor()
        self.mapper: Mapper = Mapper.create_default_mapper()
        self.resolver = Resolver(
            mapper=self.mapper,
            interactive=interactive,
        )

    def _upsert_position(self, transaction: Transaction, symbol: str | None) -> None:
        """Upsert a position with a new transaction"""

        # Create a new position if symbol does not exist, otherwise update the existing position
        position = Position.new(transaction) if symbol is None else self.positions[symbol]

        match transaction.transaction_type:
            case TransactionType.BUY:
                self._handle_buy(transaction, position)
            case TransactionType.SELL:
                self._handle_sell(transaction, position)
            case TransactionType.DIVIDEND:
                self._handle_dividend(transaction, position)
            case TransactionType.SPLIT:
                self.action_processor.handle_split(transaction, position)
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

    def add_transaction(self, transaction: Transaction) -> None:
        """Process a new transaction and upsert position"""
        matched_symbol = self._match_attribute(transaction.symbol)
        self._upsert_position(transaction, matched_symbol)
        logger.debug(f"Processed transaction {transaction}")
        if matched_symbol:
            logger.debug(f"Position: {self.positions[matched_symbol]}")

    def _match_attribute(self, symbol: str) -> str | None:
        """Match an attribute to an existing position using the resolver.

        This will first try automatic matching, and if that fails and interactive mode
        is enabled, it will ask the user to resolve the attribute.
        """
        return self.resolver.resolve(symbol, set(self.positions.keys()))

    def add_mapping(self, ticker: str, alternative_symbols: list[str], isin: str | None = None) -> None:
        """Add a mapping between a ticker and its alternatives.

        Args:
            ticker: The primary/standard ticker symbol to use
            alternative_symbols: List of alternative representations of the same symbol
            isin: The ISIN of the security
        """
        self.mapper.add_mapping(ticker, alternative_symbols, isin)

    def add_mappings_from_dict(
        self, mappings: dict[str, list[str]], isin_mappings: dict[str, str] | None = None
    ) -> None:
        """Add multiple attribute mappings from a dictionary.

        Args:
            mappings: Dictionary with tickers as keys and lists of alternatives as values
        """
        self.mapper.add_mappings_from_dict(mappings, isin_mappings)

    def set_interactive(self, interactive: bool) -> None:
        """Set whether to interactively ask the user to resolve unknown attributes.

        Args:
            interactive: Whether to interactively ask the user
        """
        self.resolver.set_interactive(interactive)

    def clear_resolution_cache(self) -> None:
        """Clear the attribute resolution cache."""
        self.resolver.clear_cache()
