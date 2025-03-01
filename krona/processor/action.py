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
        """Handle stock split by calculating the split ratio from two SPLIT transactions.

        If the two SPLIT transactions have the same date, we assume that the split is NOT a reverse split.
        TODO: implement user resolution for reverse splits.
        """

        if len(self.transaction_buffer) == 0:
            self.transaction_buffer.append(transaction)
            return

        previous_transaction = self.transaction_buffer.pop()

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

        logger.debug(
            f"Split {position.symbol} from {position.quantity} @ {position.price:.2f} to {int(position.quantity * split.ratio)} @ {(position.price / split.ratio):.2f} (split ratio: {split.ratio})"
        )
        # TODO: handle fractional shares
        position.price = position.price / split.ratio
        position.quantity = int(position.quantity * split.ratio)
