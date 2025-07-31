from pathlib import Path
from typing import Any

import yaml

from krona.models.mapping import MappingPlan, SymbolGroup
from krona.models.transaction import Transaction
from krona.parsers.base import BaseParser

DEFAULT_CONFIG = {
    "matching_strategies": {
        "fuzzy_match": {
            "ratio": 80,
            "partial_ratio": 80,
            "token_sort_ratio": 80,
            "token_set_ratio": 80,
        },
        "corporate_action": {
            "ratio": 90,
            "partial_ratio": 90,
            "token_sort_ratio": 90,
            "token_set_ratio": 90,
            "min_similarity": 25,
        },
    }
}


def get_config() -> dict[str, Any]:
    """Return the default configuration."""
    return DEFAULT_CONFIG


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


DEFAULT_MAPPING_CONFIG_FILE = "mappings.yml"


def save_mapping_config(plan: MappingPlan, config_file: str = DEFAULT_MAPPING_CONFIG_FILE) -> bool:
    """Save the mapping configuration to a YAML file.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Convert accepted suggestions to symbol mappings
        final_mappings = plan.symbol_mappings.copy()
        for suggestion in plan.accepted_suggestions:
            final_mappings[suggestion.source_symbol] = suggestion.target_symbol

        # Group mappings by canonical symbol
        symbol_groups: dict[str, SymbolGroup] = {}

        for source_symbol, target_symbol in final_mappings.items():
            if target_symbol not in symbol_groups:
                symbol_groups[target_symbol] = SymbolGroup(canonical_symbol=target_symbol)
            symbol_groups[target_symbol].synonyms.append(source_symbol)

        # Add ISIN mappings
        for isin, canonical_symbol in plan.isin_mappings.items():
            if canonical_symbol not in symbol_groups:
                symbol_groups[canonical_symbol] = SymbolGroup(canonical_symbol=canonical_symbol)
            symbol_groups[canonical_symbol].isins.append(isin)

        # Convert to YAML format
        yaml_data = {}
        for canonical_symbol, group in symbol_groups.items():
            yaml_data[canonical_symbol] = group.to_dict()

        # Save to file
        config_path = Path(config_file)
        with open(config_path, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=True)

        return True
    except Exception:
        return False


def load_mapping_config(config_file: str = DEFAULT_MAPPING_CONFIG_FILE) -> MappingPlan | None:
    """Load the mapping configuration from a YAML file."""
    config_path = Path(config_file)

    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            yaml_data = yaml.safe_load(f)

        if not yaml_data:
            return None

        symbol_mappings: dict[str, str] = {}
        isin_mappings: dict[str, str] = {}

        # Parse the YAML data
        for canonical_symbol, group_data in yaml_data.items():
            group = SymbolGroup.from_dict(canonical_symbol, group_data)

            # Add synonyms to symbol mappings
            for synonym in group.synonyms:
                symbol_mappings[synonym] = canonical_symbol

            # Add ISINs to ISIN mappings
            for isin in group.isins:
                isin_mappings[isin] = canonical_symbol

        return MappingPlan(symbol_mappings=symbol_mappings, isin_mappings=isin_mappings, suggestions=[])

    except (yaml.YAMLError, KeyError, ValueError):
        return None
