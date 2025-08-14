from datetime import timedelta

from krona.models.action import Action, ActionType
from krona.models.position import Position
from krona.models.transaction import Transaction, TransactionType
from krona.utils.logger import logger

# Smallest meaningful quantity. Quantities with absolute value below this
# threshold are treated as zero to avoid floating point residue keeping
# positions erroneously open.
QUANTITY_EPSILON = 1e-5


def apply_transaction(position: Position, transaction: Transaction) -> Position:
    """Apply a transaction to the position."""
    logger.debug(f"Applying transaction to position {position.symbol}: {transaction.transaction_type.value}")

    match transaction.transaction_type:
        case TransactionType.BUY:
            position = _handle_buy(position, transaction)
        case TransactionType.SELL:
            position = _handle_sell(position, transaction)
        case TransactionType.DIVIDEND:
            position = _handle_dividend(position, transaction)
        case TransactionType.SPLIT:
            position = _handle_split(position, transaction)
        case TransactionType.MOVE:
            position = _handle_move(position, transaction)

    position.fees += transaction.fees
    position.transactions.append(transaction)
    if position.currency is None:
        # If we don't have a currency yet (e.g. not present for a spin-off), get it from the transaction
        position.currency = transaction.currency
    return position


def _handle_buy(position: Position, transaction: Transaction) -> Position:
    new_quantity = position.quantity + transaction.quantity

    # Clamp tiny float residue to zero to avoid keeping positions open due to rounding errors
    if abs(new_quantity) < QUANTITY_EPSILON:
        new_quantity = 0

    if new_quantity < 0:
        logger.warning(
            f"New quantity would be negative for buy transaction:\n  {transaction}\nto position:\n  {position}\n"
        )
        return position

    if new_quantity == 0:
        logger.warning(f"New quantity would be zero, skipping transaction: {transaction}")
        return position

    if _is_manual_move(position, transaction):
        # Position has recently been closed, reopen it without altering the price, since this is a manual move
        # TODO: handle this gracefully by emitting one MOVE transaction instead of a SELL and a BUY
        position.quantity = new_quantity
        return position

    position.price = (
        transaction.price * transaction.quantity + transaction.fees + position.price * position.quantity
    ) / new_quantity
    position.quantity = new_quantity
    return position


def _handle_sell(position: Position, transaction: Transaction) -> Position:
    new_quantity = position.quantity - transaction.quantity

    # Clamp tiny float residue to zero to avoid keeping positions open due to rounding errors
    if abs(new_quantity) < QUANTITY_EPSILON:
        new_quantity = 0

    if new_quantity < 0:
        logger.warning(
            f"New quantity would be negative for sell transaction:\n  {transaction}\nto position:\n  {position}\n"
        )
        position.quantity = 0
        return position

    position.quantity = new_quantity
    return position


def _handle_dividend(position: Position, transaction: Transaction) -> Position:
    position.dividends += transaction.price * transaction.quantity
    return position


def _handle_split(position: Position, transaction: Transaction) -> Position:
    logger.debug(
        f"Processing split transaction: {transaction.symbol} ({transaction.ISIN}) with quantity {transaction.quantity}"
    )

    previous_transaction = None
    if position.transaction_buffer:
        previous_transaction = position.transaction_buffer.pop(0)

    if previous_transaction is None:
        logger.debug(f"No previous split transaction found, buffering: {transaction.symbol}")
        position.transaction_buffer.append(transaction)
        return position

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

    new_quantity = position.quantity * split.ratio
    new_price = position.price / split.ratio

    new_quantity = 0 if abs(new_quantity) < QUANTITY_EPSILON else round(new_quantity)

    logger.info(
        f"Split {position.symbol} from {position.quantity} @ {position.price:.2f} to {new_quantity} @ {new_price:.2f} (split ratio: {split.ratio})"
    )

    position.price = new_price
    position.quantity = new_quantity

    if split.new_ISIN and split.new_ISIN != position.ISIN:
        position.ISIN = split.new_ISIN

    return position


def _is_manual_move(position: Position, transaction: Transaction) -> bool:
    """Check if the transaction is a manual move between brokers, i.e. a SELL and a BUY"""

    return (
        position.is_closed
        and len(position.transactions) > 0
        and position.transactions[-1].date >= transaction.date - timedelta(days=3)
    )


def _handle_move(position: Position, transaction: Transaction) -> Position:
    """Handle a move transaction. Does nothing for now, since moves are harmless.
    TODO: handle this gracefully by emitting one MOVE transaction instead of one per broker.
    """
    logger.debug(f"Processing move: {transaction.symbol} ({transaction.ISIN}) with quantity {transaction.quantity}")
    return position
