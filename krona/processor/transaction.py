import logging

from thefuzz import process  # type: ignore

from krona.models.position import Position
from krona.models.transaction import Transaction, TransactionType
from krona.processor.action import ActionProcessor

logger = logging.getLogger(__name__)


class TransactionProcessor:
    """Handles business logic for transactions"""

    def __init__(self) -> None:
        self.positions: dict[str, Position] = {}
        self.action_processor: ActionProcessor = ActionProcessor()

    def _insert_position(self, transaction: Transaction) -> None:
        """Insert a new transaction into the positions"""
        position = Position(
            symbol=transaction.symbol,
            ISIN=transaction.ISIN,
            currency=transaction.currency,
            quantity=transaction.quantity,
            buy_quantity=transaction.quantity if transaction.transaction_type == TransactionType.BUY else 0,
            price=transaction.price,
            dividends=0 if transaction.transaction_type != TransactionType.DIVIDEND else transaction.total_amount,
            transactions=[transaction],
            fees=transaction.fees,
        )
        if transaction.transaction_type == TransactionType.SPLIT:
            self.action_processor.handle_split(transaction, position)
        self.positions[position.symbol] = position

    def _update_position(self, transaction: Transaction, symbol: str) -> None:
        """Update an existing position with a new transaction"""
        position = self.positions[symbol]

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

    def _upsert_position(self, transaction: Transaction, symbol: str | None) -> None:
        """Upsert a position with a new transaction"""
        if symbol is None:
            position = Position(
                symbol=transaction.symbol,
                ISIN=transaction.ISIN,
                currency=transaction.currency,
                quantity=0,
                buy_quantity=0,
                price=0,
                dividends=0,
                fees=0,
                transactions=[],
            )
        else:
            position = self.positions[symbol]

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

    def _handle_buy(self, transaction: Transaction, position: Position) -> None:
        position.price = (transaction.price * transaction.quantity + position.price * position.buy_quantity) / (
            position.buy_quantity + transaction.quantity
        )
        position.quantity += transaction.quantity
        position.buy_quantity += transaction.quantity

    def _handle_sell(self, transaction: Transaction, position: Position) -> None:
        position.quantity -= transaction.quantity

    def _handle_dividend(self, transaction: Transaction, position: Position) -> None:
        position.dividends += transaction.total_amount

    def add_transaction(self, transaction: Transaction) -> None:
        """Process a new transaction and upsert position"""
        # TODO: implement fuzzy matching for symbols
        matched_symbol = self._match_symbol(transaction.symbol)
        self._upsert_position(transaction, matched_symbol)
        # if matched_symbol is None:
        #    self._insert_position(transaction)
        # else:
        #    self._update_position(transaction, matched_symbol)

    def _match_symbol(self, symbol: str) -> str | None:
        """Fuzzy matching for symbols"""
        if symbol in self.positions:
            return symbol
        matches: tuple[str, int] | None = process.extractOne(symbol, self.positions.keys(), score_cutoff=80)
        if matches is None:
            logger.debug(f"No match for {symbol}")
            return None
        logger.debug(f"Matched {symbol} to {matches}")
        return matches[0]
