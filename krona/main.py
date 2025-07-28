import re
from pathlib import Path

from krona.parsers.avanza import AvanzaParser
from krona.parsers.nordnet import NordnetParser
from krona.processor.transaction import TransactionProcessor
from krona.utils.io import identify_broker_files, read_transactions_from_files
from krona.utils.logger import logger


def parse_number_ranges(arg: str) -> list[int]:
    """Parse a string containing numbers and ranges into a list of integers.

    Examples:
        "1,3,5-7,10" -> [1, 3, 5, 6, 7, 10]
        "2-4,6,8-9" -> [2, 3, 4, 6, 8, 9]
        "5" -> [5]
    """
    numbers = []
    parts = arg.split(",")

    for part in parts:
        part = part.strip()
        if "-" in part:
            # Handle range
            try:
                start, end = map(int, part.split("-"))
                if start <= end:
                    numbers.extend(range(start, end + 1))
                else:
                    logger.warning(f"Invalid range: {part} (start > end)")
            except ValueError:
                logger.warning(f"Invalid range format: {part}")
        else:
            # Handle single number
            try:
                numbers.append(int(part))
            except ValueError:
                logger.warning(f"Invalid number: {part}")

    return sorted(set(numbers))  # Remove duplicates and sort


def show_mapping_plan(plan):
    """Display the mapping plan to the user."""
    print("\n" + "=" * 60)
    print("MAPPING PLAN")
    print("=" * 60)

    # Filter out identical mappings
    non_identical_symbol_mappings = {k: v for k, v in plan.symbol_mappings.items() if k != v}
    non_identical_isin_mappings = {k: v for k, v in plan.isin_mappings.items() if k != v}

    if non_identical_symbol_mappings:
        print(f"\nSymbol Mappings ({len(non_identical_symbol_mappings)}):")
        for i, (source, target) in enumerate(sorted(non_identical_symbol_mappings.items()), 1):
            print(f"  {i:2d}. {source} -> {target}")

    if non_identical_isin_mappings:
        print(f"\nISIN Mappings ({len(non_identical_isin_mappings)}):")
        for i, (source, target) in enumerate(
            sorted(non_identical_isin_mappings.items()), len(non_identical_symbol_mappings) + 1
        ):
            print(f"  {i:2d}. {source} -> {target}")

    # Filter out previously accepted/denied suggestions
    active_suggestions = []
    for conflict in plan.conflicts:
        if conflict not in plan.accepted_suggestions and conflict not in plan.denied_suggestions:
            active_suggestions.append(conflict)

    if active_suggestions:
        # Calculate starting number for suggestions (after symbol and ISIN mappings)
        suggestion_start = len(non_identical_symbol_mappings) + len(non_identical_isin_mappings) + 1
        print(f"\nConflicts and suggestions that need resolution ({len(active_suggestions)}):")
        for i, conflict in enumerate(active_suggestions, suggestion_start):
            if conflict.startswith("Fuzzy match"):
                print(f"  {i:2d}. 🔍 {conflict}")
            elif conflict.startswith("Potential corporate action"):
                print(f"  {i:2d}. 🏢 {conflict}")
            else:
                print(f"  {i:2d}. ⚠️  {conflict}")
    else:
        print("\nNo new conflicts or suggestions to resolve.")

    if plan.accepted_suggestions:
        print(f"\nPreviously accepted suggestions ({len(plan.accepted_suggestions)}):")
        for suggestion in plan.accepted_suggestions[:5]:  # Show first 5
            if suggestion.startswith("Fuzzy match"):
                print(f"  ✅ 🔍 {suggestion}")
            elif suggestion.startswith("Potential corporate action"):
                print(f"  ✅ 🏢 {suggestion}")
            else:
                print(f"  ✅ ⚠️  {suggestion}")
        if len(plan.accepted_suggestions) > 5:
            print(f"  ... and {len(plan.accepted_suggestions) - 5} more")

    if plan.denied_suggestions:
        print(f"\nPreviously denied suggestions ({len(plan.denied_suggestions)}):")
        for suggestion in plan.denied_suggestions[:5]:  # Show first 5
            if suggestion.startswith("Fuzzy match"):
                print(f"  ❌ 🔍 {suggestion}")
            elif suggestion.startswith("Potential corporate action"):
                print(f"  ❌ 🏢 {suggestion}")
            else:
                print(f"  ❌ ⚠️  {suggestion}")
        if len(plan.denied_suggestions) > 5:
            print(f"  ... and {len(plan.denied_suggestions) - 5} more")

    print("\n" + "=" * 60)


def edit_mapping_plan(plan):
    """Allow user to edit the mapping plan interactively."""

    print("\n" + "=" * 60)
    print("EDIT MAPPING PLAN")
    print("=" * 60)
    print("Commands:")
    print("  <number> <new_target>  - Edit mapping (e.g., '5 Investor B')")
    print("  d <numbers>            - Delete mapping(s) or deny suggestion(s) (e.g., 'd 5', 'd 1-3', 'd 1,3,5-7')")
    print("  add <source> <target>  - Add new mapping (e.g., 'add OLD_SYMBOL NEW_SYMBOL')")
    print("  c <canonical> <synonym> - Add synonym to canonical (e.g., 'c Investor A INVESTOR C')")
    print("  i <canonical> <isin>   - Add ISIN to canonical (e.g., 'i Investor A SE0000123456')")
    print("  a <numbers>            - Accept suggestion(s) (e.g., 'a 3', 'a 1-5', 'a 1,3,5-7')")
    print("  s                      - Show current plan")
    print("  done                   - Finish editing")
    print("  cancel                 - Cancel all changes")
    print("=" * 60)

    # Create working copies
    symbol_mappings = dict(plan.symbol_mappings)
    isin_mappings = dict(plan.isin_mappings)

    # Create numbered lists for easy reference
    symbol_items = sorted(symbol_mappings.items())
    isin_items = sorted(isin_mappings.items())

    def show_current_state():
        """Show the current state of mappings being edited."""
        print("\n" + "=" * 60)
        print("CURRENT MAPPING STATE")
        print("=" * 60)

        # Filter out identical mappings
        non_identical_symbol_mappings = {k: v for k, v in symbol_mappings.items() if k != v}
        non_identical_isin_mappings = {k: v for k, v in isin_mappings.items() if k != v}

        if non_identical_symbol_mappings:
            print(f"\nSymbol Mappings ({len(non_identical_symbol_mappings)}):")
            for i, (source, target) in enumerate(sorted(non_identical_symbol_mappings.items()), 1):
                print(f"  {i:2d}. {source} -> {target}")

        if non_identical_isin_mappings:
            print(f"\nISIN Mappings ({len(non_identical_isin_mappings)}):")
            for i, (source, target) in enumerate(
                sorted(non_identical_isin_mappings.items()), len(non_identical_symbol_mappings) + 1
            ):
                print(f"  {i:2d}. {source} -> {target}")

        # Show remaining active suggestions (not accepted/denied)
        active_suggestions = []
        for conflict in plan.conflicts:
            if conflict not in plan.accepted_suggestions and conflict not in plan.denied_suggestions:
                active_suggestions.append(conflict)

        if active_suggestions:
            # Calculate starting number for suggestions (after symbol and ISIN mappings)
            suggestion_start = len(non_identical_symbol_mappings) + len(non_identical_isin_mappings) + 1
            print(f"\nRemaining Suggestions ({len(active_suggestions)}):")
            for i, suggestion in enumerate(active_suggestions, suggestion_start):
                if suggestion.startswith("Fuzzy match"):
                    print(f"  {i:2d}. 🔍 {suggestion}")
                elif suggestion.startswith("Potential corporate action"):
                    print(f"  {i:2d}. 🏢 {suggestion}")
                else:
                    print(f"  {i:2d}. ⚠️  {suggestion}")
        else:
            print("\nNo remaining suggestions to resolve.")

        # Show accepted suggestions
        if plan.accepted_suggestions:
            print(f"\nAccepted Suggestions ({len(plan.accepted_suggestions)}):")
            for suggestion in plan.accepted_suggestions[:5]:  # Show first 5
                if suggestion.startswith("Fuzzy match"):
                    print(f"  ✅ 🔍 {suggestion}")
                elif suggestion.startswith("Potential corporate action"):
                    print(f"  ✅ 🏢 {suggestion}")
                else:
                    print(f"  ✅ ⚠️  {suggestion}")
            if len(plan.accepted_suggestions) > 5:
                print(f"  ... and {len(plan.accepted_suggestions) - 5} more")

        # Show denied suggestions
        if plan.denied_suggestions:
            print(f"\nDenied Suggestions ({len(plan.denied_suggestions)}):")
            for suggestion in plan.denied_suggestions[:5]:  # Show first 5
                if suggestion.startswith("Fuzzy match"):
                    print(f"  ❌ 🔍 {suggestion}")
                elif suggestion.startswith("Potential corporate action"):
                    print(f"  ❌ 🏢 {suggestion}")
                else:
                    print(f"  ❌ ⚠️  {suggestion}")
            if len(plan.denied_suggestions) > 5:
                print(f"  ... and {len(plan.denied_suggestions) - 5} more")

        print("=" * 60)

    while True:
        try:
            command = input("\nEdit command: ").strip()

            if command.lower() == "done":
                break
            elif command.lower() == "cancel":
                return None
            elif command.lower() == "s":
                show_current_state()
                continue
            elif command.startswith("d "):
                # Delete mapping(s) - can be single number, range, or multiple numbers/ranges
                try:
                    arg = command[2:].strip()
                    numbers = parse_number_ranges(arg)

                    if not numbers:
                        print("No valid numbers found")
                        continue

                    # Get active suggestions (not previously accepted/denied)
                    active_suggestions = []
                    for conflict in plan.conflicts:
                        if conflict not in plan.accepted_suggestions and conflict not in plan.denied_suggestions:
                            active_suggestions.append(conflict)

                    # Calculate the starting number for suggestions (after symbol and ISIN mappings)
                    suggestion_start = (
                        len([k for k, v in symbol_mappings.items() if k != v])
                        + len([k for k, v in isin_mappings.items() if k != v])
                        + 1
                    )

                    denied_count = 0
                    deleted_mappings = []

                    for num in numbers:
                        if 1 <= num <= len(symbol_items):
                            # Delete symbol mapping and add back to suggestions
                            source, target = symbol_items[num - 1]
                            del symbol_mappings[source]
                            deleted_mappings.append(f"{source} -> {target}")

                            # Add a suggestion back to conflicts so it can be reconsidered
                            suggestion = f"Fuzzy match (100%): '{source}' and '{target}' share ISIN (to be determined)"
                            if (
                                suggestion not in plan.conflicts
                                and suggestion not in plan.accepted_suggestions
                                and suggestion not in plan.denied_suggestions
                            ):
                                plan.conflicts.append(suggestion)

                        elif len(symbol_items) < num <= len(symbol_items) + len(isin_items):
                            # Delete ISIN mapping and add back to suggestions
                            isin_num = num - len(symbol_items) - 1
                            source, target = isin_items[isin_num]
                            del isin_mappings[source]
                            deleted_mappings.append(f"ISIN {source} -> {target}")

                            # Add a suggestion back to conflicts so it can be reconsidered
                            suggestion = f"ISIN mapping: '{source}' -> '{target}' (to be reconsidered)"
                            if (
                                suggestion not in plan.conflicts
                                and suggestion not in plan.accepted_suggestions
                                and suggestion not in plan.denied_suggestions
                            ):
                                plan.conflicts.append(suggestion)

                        elif suggestion_start <= num <= suggestion_start + len(active_suggestions) - 1:
                            # Deny suggestion
                            suggestion = active_suggestions[num - suggestion_start]
                            plan.denied_suggestions.append(suggestion)
                            denied_count += 1
                        else:
                            print(f"Invalid mapping or suggestion number: {num}")

                    # Update sorted items after all deletions
                    symbol_items = sorted(symbol_mappings.items())
                    isin_items = sorted(isin_mappings.items())

                    # Print summary
                    if deleted_mappings:
                        print(f"Deleted {len(deleted_mappings)} mappings: {', '.join(deleted_mappings)}")
                    if denied_count > 0:
                        print(f"Denied {denied_count} suggestions")
                except ValueError:
                    print("Invalid number format")
            elif command.startswith("add "):
                # Add new mapping
                parts = command[4:].split()
                if len(parts) >= 2:
                    source = parts[0]
                    target = " ".join(parts[1:])
                    # Determine if it's an ISIN (alphanumeric, typically 12 chars)
                    if source.replace("-", "").isalnum() and len(source.replace("-", "")) >= 10:
                        isin_mappings[source] = target
                        isin_items = sorted(isin_mappings.items())
                        print(f"Added ISIN mapping: {source} -> {target}")
                    else:
                        symbol_mappings[source] = target
                        symbol_items = sorted(symbol_mappings.items())
                        print(f"Added symbol mapping: {source} -> {target}")
                else:
                    print("Usage: add <source> <target>")
            elif command.startswith("c "):
                # Add synonym to canonical symbol
                parts = command[2:].split()
                if len(parts) >= 2:
                    # Find the last word as the synonym, rest is canonical
                    synonym = parts[-1]
                    canonical = " ".join(parts[:-1])
                    symbol_mappings[synonym] = canonical
                    symbol_items = sorted(symbol_mappings.items())
                    print(f"Added synonym '{synonym}' to canonical '{canonical}'")
                else:
                    print("Usage: c <canonical> <synonym>")
            elif command.startswith("i "):
                # Add ISIN to canonical symbol
                parts = command[2:].split()
                if len(parts) >= 2:
                    # Find the last word as the ISIN, rest is canonical
                    isin = parts[-1]
                    canonical = " ".join(parts[:-1])
                    isin_mappings[isin] = canonical
                    isin_items = sorted(isin_mappings.items())
                    print(f"Added ISIN '{isin}' to canonical '{canonical}'")
                else:
                    print("Usage: i <canonical> <isin>")
            elif command.startswith("a "):
                # Accept suggestion(s) - can be single number, range, or multiple numbers/ranges
                try:
                    arg = command[2:].strip()
                    numbers = parse_number_ranges(arg)

                    if not numbers:
                        print("No valid numbers found")
                        continue

                    # Get active suggestions (not previously accepted/denied)
                    active_suggestions = []
                    for conflict in plan.conflicts:
                        if conflict not in plan.accepted_suggestions and conflict not in plan.denied_suggestions:
                            active_suggestions.append(conflict)

                    # Calculate the starting number for suggestions (after symbol and ISIN mappings)
                    suggestion_start = (
                        len([k for k, v in symbol_mappings.items() if k != v])
                        + len([k for k, v in isin_mappings.items() if k != v])
                        + 1
                    )

                    accepted_count = 0

                    for num in numbers:
                        # Check if the number is within the active suggestions range
                        if suggestion_start <= num <= suggestion_start + len(active_suggestions) - 1:
                            suggestion = active_suggestions[num - suggestion_start]

                            # Handle fuzzy match suggestions
                            if suggestion.startswith("Fuzzy match"):
                                # Parse the suggestion to extract symbols
                                # Format: "Fuzzy match (XX%): 'SYMBOL1' and 'SYMBOL2' share ISIN XXXX"
                                match = re.search(r"'([^']+)' and '([^']+)'", suggestion)
                                if match:
                                    symbol1, symbol2 = match.groups()
                                    # Use the longer symbol as canonical (more descriptive)
                                    if len(symbol1) >= len(symbol2):
                                        canonical, synonym = symbol1, symbol2
                                    else:
                                        canonical, synonym = symbol2, symbol1
                                    symbol_mappings[synonym] = canonical
                                    plan.accepted_suggestions.append(suggestion)
                                    accepted_count += 1
                                else:
                                    print(f"Could not parse fuzzy match suggestion: {suggestion}")

                            # Handle corporate action suggestions
                            elif suggestion.startswith("Potential corporate action"):
                                # Parse the suggestion to extract symbols
                                # Format: "Potential corporate action (XX%): 'SYMBOL1' (ISIN1) and 'SYMBOL2' (ISIN2)"
                                match = re.search(r"'([^']+)' \([^)]+\) and '([^']+)'", suggestion)
                                if match:
                                    symbol1, symbol2 = match.groups()
                                    # Use the longer symbol as canonical (more descriptive)
                                    if len(symbol1) >= len(symbol2):
                                        canonical, synonym = symbol1, symbol2
                                    else:
                                        canonical, synonym = symbol2, symbol1
                                    symbol_mappings[synonym] = canonical
                                    plan.accepted_suggestions.append(suggestion)
                                    accepted_count += 1
                                else:
                                    print(f"Could not parse corporate action suggestion: {suggestion}")

                            # Handle other types of suggestions (like circular mappings)
                            else:
                                print(f"Cannot automatically resolve suggestion: {suggestion}")
                        else:
                            print(f"Invalid suggestion number: {num}")

                    # Update sorted items after all acceptances
                    symbol_items = sorted(symbol_mappings.items())

                    # Print summary
                    if accepted_count > 0:
                        print(f"Accepted {accepted_count} suggestions")
                except ValueError:
                    print("Invalid number format")

            else:
                # Edit existing mapping
                parts = command.split()
                if len(parts) >= 2:
                    try:
                        num = int(parts[0])
                        new_target = " ".join(parts[1:])

                        if 1 <= num <= len(symbol_items):
                            source, _ = symbol_items[num - 1]
                            symbol_mappings[source] = new_target
                            symbol_items = sorted(symbol_mappings.items())
                            print(f"Updated: {source} -> {new_target}")
                        elif len(symbol_items) < num <= len(symbol_items) + len(isin_items):
                            isin_num = num - len(symbol_items) - 1
                            source, _ = isin_items[isin_num]
                            isin_mappings[source] = new_target
                            isin_items = sorted(isin_mappings.items())
                            print(f"Updated: {source} -> {new_target}")
                        else:
                            print("Invalid mapping number")
                    except ValueError:
                        print("Invalid number format")
                else:
                    print("Usage: <number> <new_target>")

        except KeyboardInterrupt:
            print("\nCancelled by user")
            return None
        except EOFError:
            print("\nCancelled by user")
            return None

    # Create new plan with edited mappings
    from krona.processor.mapper import MappingPlan

    return MappingPlan(
        symbol_mappings=symbol_mappings,
        isin_mappings=isin_mappings,
        conflicts=plan.conflicts,
        accepted_suggestions=plan.accepted_suggestions,
        denied_suggestions=plan.denied_suggestions,
    )


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

    # Check if there are previous decisions
    if plan.accepted_suggestions or plan.denied_suggestions:
        print(
            f"\nFound {len(plan.accepted_suggestions)} previously accepted and {len(plan.denied_suggestions)} previously denied suggestions."
        )
        while True:
            response = input("Do you want to reuse these previous decisions? (y/n): ").strip().lower()
            if response in ["y", "yes"]:
                print("Reusing previous decisions.")
                break
            elif response in ["n", "no"]:
                print("Clearing previous decisions.")
                plan.accepted_suggestions.clear()
                plan.denied_suggestions.clear()
                break
            else:
                print("Please enter 'y' or 'n'")

    # Show the plan
    show_mapping_plan(plan)

    # Allow multiple editing sessions until user is satisfied
    edit_session = 0
    while True:
        response = input("\nDo you want to edit the plan? (y/n): ").strip().lower()
        if response in ["y", "yes"]:
            edit_session += 1
            if edit_session > 1:
                print(f"\n--- Editing Session {edit_session} ---")
            edited_plan = edit_mapping_plan(plan)
            if edited_plan is None:
                print("Editing cancelled. Exiting.")
                return
            plan = edited_plan
            print("\nUpdated plan:")
            show_mapping_plan(plan)
            # Continue the loop to allow more editing
        elif response in ["n", "no"]:
            break
        else:
            print("Please enter 'y' or 'n'")

    # Ask for final acceptance
    while True:
        response = input("\nAccept this plan? (y/n): ").strip().lower()
        if response in ["y", "yes"]:
            break
        elif response in ["n", "no"]:
            print("Plan rejected. Exiting.")
            return
        else:
            print("Please enter 'y' or 'n'")

    # Accept the plan
    processor.mapper.accept_plan(plan)

    for transaction in transactions:
        processor.add_transaction(transaction)

    # Save the final mappings and decisions
    processor.mapper.save_mappings(Path("mappings.yml"))
    processor.mapper.save_decisions(plan.accepted_suggestions, plan.denied_suggestions, Path("mappings.yml"))

    print("--------------------------------")
    for position in processor.positions.values():
        print(position)


if __name__ == "__main__":
    main(path=Path("files"))
