import logging

from krona.parsers.avanza import AvanzaParser
from krona.parsers.nordnet import NordnetParser
from krona.processor.transaction import TransactionProcessor

logging.basicConfig(level=logging.DEBUG)


def main():
    # Create a transaction processor with default symbol mappings and interactive mode enabled
    processor = TransactionProcessor(interactive=True)

    # Parse and process Avanza transactions
    avanza_parser = AvanzaParser()
    nordnet_parser = NordnetParser()
    nordnet_file = "tests/data/transactions-and-notes-export.csv"
    avanza_file = "tests/data/transaktioner_2016-11-17_2024-12-15.csv"
    print("Processing transactions...")
    for transaction in nordnet_parser.parse_file(nordnet_file):
        processor.add_transaction(transaction)
    for transaction in avanza_parser.parse_file(avanza_file):
        processor.add_transaction(transaction)

    # Print the final positions
    print("\nFinal positions:")
    for _, position in processor.positions.items():
        print(position)


if __name__ == "__main__":
    main()
