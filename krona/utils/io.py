from pathlib import Path

from krona.models.transaction import Transaction
from krona.parsers.base import BaseParser


def identify_broker_files(path: Path, parsers: list[BaseParser]) -> dict[str, list[str]]:
    """
    Identify exported transaction files from all brokers in a given directory.
    Returns a dictionary with the broker name as the key and a list of file names as the value.
    """
    files: dict[str, list[str]] = {parser.name: [] for parser in parsers}

    for file in path.iterdir():
        if file.name.endswith(".csv"):
            for parser in parsers:
                if parser.is_valid_file(str(file)):
                    files[parser.name].append(str(file))
                    break

    return files


def read_transactions_from_files(broker_files: dict[str, list[str]], parsers: list[BaseParser]) -> list[Transaction]:
    """
    Parse the broker files and return a sorted list of transactions.
    Transactions are sorted by date, and then by transaction type. This ensures that BUY transactions are processed before SELL transactions on the same day.
    """
    transactions: list[Transaction] = []

    for parser in parsers:
        for file in broker_files[parser.name]:
            for transaction in parser.parse_file(file):
                transactions.append(transaction)

    return sorted(transactions, key=lambda x: (x.date, x.transaction_type.value != "BUY"))
