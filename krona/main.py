from pathlib import Path

from krona.parsers.avanza import AvanzaParser
from krona.parsers.nordnet import NordnetParser
from krona.processor.transaction import TransactionProcessor
from krona.utils.io import identify_broker_files, read_transactions_from_files

DEBUG_SYMBOLS = ["BAHN B", "BAHNHOF AK B", "Bahnhof B"]


def main(path: Path):
    processor = TransactionProcessor()
    processor.mapper.load_mappings(Path("mappings.csv"))
    nordnet_parser = NordnetParser()
    avanza_parser = AvanzaParser()

    broker_files = identify_broker_files(path, [nordnet_parser, avanza_parser])
    transactions = read_transactions_from_files(broker_files, [nordnet_parser, avanza_parser])

    for transaction in transactions:
        processor.add_transaction(transaction)
        if transaction.symbol in DEBUG_SYMBOLS:
            print(transaction)
            print(
                processor.positions.get("BAHN B")
                or processor.positions.get("BAHNHOF AK B")
                or processor.positions.get("Bahnhof B")
            )
    processor.mapper.save_mappings(Path("mappings.csv"))
    # for position in processor.positions.values():
    #     print(position)


if __name__ == "__main__":
    main(path=Path("files"))
