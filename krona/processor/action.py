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

        if (
            transaction.symbol not in self.transaction_buffer
            and mapper.get_synonyms(transaction.symbol) not in self.transaction_buffer
        ):
            self.transaction_buffer[transaction.symbol] = [transaction]
            return

        try:
            previous_transaction = self.transaction_buffer[transaction.symbol][0]
            self.transaction_buffer.pop(transaction.symbol)
        except KeyError:
            syn = mapper.get_synonyms(transaction.symbol)
            if syn is None:
                raise
            previous_transaction = self.transaction_buffer[syn][0]
            self.transaction_buffer.pop(syn)

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
        logger.info(
            f"Split {position.symbol} from {position.quantity} @ {position.price:.2f} to {int(position.quantity * split.ratio)} @ {(position.price / split.ratio):.2f} (split ratio: {split.ratio})"
        )
        # TODO: handle fractional shares
        position.price = position.price / split.ratio
        position.quantity = int(position.quantity * split.ratio)
