from krona.models.transaction import Transaction, TransactionType
from krona.processor.transaction import TransactionProcessor


class ActionProcessor:
    """Handles business logic for corporate actions"""

    def __init__(self, transaction_processor: TransactionProcessor) -> None:
        self._transaction_processor = transaction_processor
        self._actions: list[Transaction] = []

    def process_action(self, action: Transaction) -> None:
        """Apply corporate action to existing positions"""
        match action.transaction_type:
            case TransactionType.SPLIT:
                self._handle_split(action)
            case _:
                raise ValueError(f"Unknown action type: {action.transaction_type}")

    def _handle_split(self, action: Transaction) -> None:
        """Complex logic for handling stock splits"""
        pass
