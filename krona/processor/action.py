import logging

from krona.models.action import Action, ActionType
from krona.models.position import Position
from krona.models.transaction import Transaction

logger = logging.getLogger(__name__)


class ActionProcessor:
    """Handles business logic for corporate actions"""

    def __init__(self) -> None:
        self.transaction_buffer: list[Transaction] = []

    def handle_split(self, transaction: Transaction, position: Position) -> None:
        """Complex logic for handling stock splits"""
        # TODO: should we buffer the transaction or the action?
        if len(self.transaction_buffer) == 0:
            self.transaction_buffer.append(transaction)
        else:
            previous_transaction = self.transaction_buffer.pop()
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
            logger.debug(
                f"Split {position.symbol} from {position.quantity} @ {position.price} to {int(position.quantity / split.ratio)} @ {(position.price * split.ratio):.2f}"
            )
            # TODO: handle fractional shares
            position.price = position.price / split.ratio
            position.quantity = int(position.quantity * split.ratio)
