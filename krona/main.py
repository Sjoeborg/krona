import argparse
from pathlib import Path

from krona.parsers.avanza import AvanzaParser
from krona.parsers.nordnet import NordnetParser
from krona.processor.transaction import TransactionProcessor
from krona.ui.cli import CLI
from krona.ui.tui_wrapper import TUIWrapper
from krona.utils.io import identify_broker_files, read_transactions_from_files

DEBUG_SYMBOLS = {
    "SWEDISH MATCH",
    "SWEDISH MATCH AB",
    "SWMA",
}


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="KRONA - Rapidly Organizes Nordic Assets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "path",
        type=Path,
        default=Path("files"),
        nargs="?",
        help="Path to directory containing transaction files (default: files)",
    )

    parser.add_argument(
        "--ui",
        choices=["cli", "tui"],
        default="tui",
        help="User interface mode: cli (Rich CLI), tui (Textual TUI) (default: tui)",
    )
    return parser.parse_args()


def main(path: Path, ui_mode: str = "tui"):
    """Main function to process transaction files."""
    processor = TransactionProcessor()
    nordnet_parser = NordnetParser()
    avanza_parser = AvanzaParser()

    broker_files = identify_broker_files(path, [nordnet_parser, avanza_parser])
    transactions = read_transactions_from_files(broker_files, [nordnet_parser, avanza_parser])

    print(f"Found {len(transactions)} transactions")

    # Phase 1: Create mapping plan
    print("\nCreating mapping plan...")
    # Handle existing mapping configuration based on UI mode
    if ui_mode == "cli":
        existing_plan = CLI.prompt_load_existing_config()
        plan = existing_plan if existing_plan else processor.mapper.create_mapping_plan(transactions)
        ui = CLI(plan)
    elif ui_mode == "tui":
        # For TUI, load existing config silently and let TUI handle the display
        plan = processor.mapper.create_mapping_plan(transactions)
        ui = TUIWrapper(plan, suggestions=[], processor=processor, transactions=transactions)
    else:
        raise ValueError(f"Unknown UI mode: {ui_mode}")

    # Run the UI and get the updated plan
    plan = ui.run()

    if ui_mode == "cli":
        # Accept the plan and process transactions
        processor.mapper.accept_plan(plan)
        processor.clear_positions()
        for transaction in transactions:
            processor.add_transaction(transaction)
            if DEBUG_SYMBOLS is not None and transaction.symbol in DEBUG_SYMBOLS:
                print(transaction)
                print(processor.positions.get(transaction.symbol))

        positions = list(processor.positions.values())
        # Show interactive positions view
        if isinstance(ui, CLI):
            # Re-initialize CLI with processor and transactions to allow future reuse if needed
            ui = CLI(plan=plan, processor=processor, transactions=transactions)
            ui.run_positions_view(positions)
        else:
            # Fallback to simple display if not CLI instance
            print("\n📊 Portfolio Summary:")
            print(f"Total Positions: {len(positions)}")


if __name__ == "__main__":
    args = parse_arguments()
    main(path=args.path, ui_mode=args.ui)
