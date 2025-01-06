import logging

from thefuzz import process  # type: ignore

from krona.models.action import Action, ActionType
from krona.models.position import Position
from krona.models.transaction import Transaction, TransactionType

logger = logging.getLogger(__name__)


class TransactionProcessor:
    """Handles business logic for transactions"""

    def __init__(self) -> None:
        self.positions: dict[str, Position] = {}
        self.buffer: list[Transaction] = []
        self.actions: list[Action] = []

    def _insert_position(self, transaction: Transaction) -> None:
        """Insert a new transaction into the positions"""
        self.positions[transaction.symbol] = Position(
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
            _split = self._handle_split(transaction)

    def _update_position(self, transaction: Transaction, symbol: str) -> None:
        """Update an existing position with a new transaction"""
        position = self.positions[symbol]

        match transaction.transaction_type:
            case TransactionType.BUY:
                # TODO: Rethink quantity and buy_quantity
                position.price = (transaction.price * transaction.quantity + position.price * position.buy_quantity) / (
                    position.buy_quantity + transaction.quantity
                )
                position.quantity += transaction.quantity
                position.buy_quantity += transaction.quantity
            case TransactionType.SELL:
                position.quantity -= transaction.quantity
            case TransactionType.DIVIDEND:
                position.dividends += transaction.total_amount
            case TransactionType.SPLIT:
                split = self._handle_split(transaction)
                if split is not None:
                    logger.debug(
                        f"Split {position.symbol} from {position.quantity} @ {position.price} to {int(position.quantity / split.ratio)} @ {(position.price * split.ratio):.2f}"
                    )
                    # TODO: handle fractional shares
                    position.price = position.price * split.ratio
                    position.quantity = int(position.quantity / split.ratio)
                    position.buy_quantity = int(position.buy_quantity / split.ratio)

            case _:
                raise ValueError(f"Unknown transaction type: {transaction.transaction_type}")
        position.fees += transaction.fees
        position.transactions.append(transaction)

    def add_transaction(self, transaction: Transaction) -> None:
        """Process a new transaction and upsert position"""
        # TODO: implement fuzzy matching for symbols
        matched_symbol = self._match_symbol(transaction.symbol)
        if matched_symbol is None:
            self._insert_position(transaction)
        else:
            self._update_position(transaction, matched_symbol)

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

    def _handle_split(self, transaction: Transaction) -> Action | None:
        """Complex logic for handling stock splits"""
        # TODO: should we buffer the transaction or the action?
        if len(self.buffer) == 0:
            self.buffer.append(transaction)
            return None
        else:
            previous_transaction = self.buffer.pop()
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
            self.actions.append(split)
            return split
