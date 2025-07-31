from pathlib import Path

from krona.parsers.avanza import AvanzaParser
from krona.parsers.nordnet import NordnetParser
from krona.processor.transaction import TransactionProcessor
from krona.ui.cli import CLI
from krona.utils.io import identify_broker_files, read_transactions_from_files


def main(path: Path):
    """Main function to process transaction files."""
    processor = TransactionProcessor()
    nordnet_parser = NordnetParser()
    avanza_parser = AvanzaParser()

    broker_files = identify_broker_files(path, [nordnet_parser, avanza_parser])
    transactions = read_transactions_from_files(broker_files, [nordnet_parser, avanza_parser])

    print(f"Found {len(transactions)} transactions")

    # Phase 1: Create mapping plan
    print("\nCreating mapping plan...")
    plan = processor.mapper.create_mapping_plan(transactions)

    # Run the CLI
    cli = CLI(plan)
    plan = cli.run()

    # Accept the plan
    processor.mapper.accept_plan(plan)

    for transaction in transactions:
        processor.add_transaction(transaction)

    # Display final positions
    cli.display_positions(list(processor.positions.values()))


if __name__ == "__main__":
    main(path=Path("files"))
