from datetime import date

from krona.models.mapping import MappingPlan
from krona.models.transaction import Transaction, TransactionType
from krona.processor.strategies.conflict_detection import (
    ConflictDetectionStrategy,
)
from krona.processor.strategies.fuzzy_match import FuzzyMatchStrategy


def test_fuzzy_match_strategy_shared_isin():
    strategy = FuzzyMatchStrategy()
    plan = MappingPlan(
        symbol_mappings={},
        isin_mappings={},
        suggestions=[],
    )
    symbol_to_isins = {
        "AMAZON.COM": {"US0231351067"},
        "AMAZON.COM INC": {"US0231351067"},
    }
    isin_to_symbols = {
        "US0231351067": {"AMAZON.COM", "AMAZON.COM INC"},
    }
    transactions = [
        Transaction(
            date=date(2023, 1, 1),
            transaction_type=TransactionType.BUY,
            symbol="AMAZON.COM INC",
            ISIN="US0231351067",
            quantity=1,
            price=1,
            fees=0,
            currency="USD",
        )
    ]

    strategy.execute(
        plan=plan,
        symbol_to_isins=symbol_to_isins,
        isin_to_symbols=isin_to_symbols,
        transactions=transactions,
    )

    assert len(plan.suggestions) > 0
    # You may want to add more specific assertions here based on the expected suggestions


def test_fuzzy_match_strategy_corporate_action():
    strategy = FuzzyMatchStrategy()
    plan = MappingPlan(
        symbol_mappings={},
        isin_mappings={},
        suggestions=[],
    )
    symbol_to_isins = {
        "SAMPO PLC A": {"FI0009003305"},
        "SAMPO AB": {"FI0009003306"},
    }
    isin_to_symbols = {
        "FI0009003305": {"SAMPO PLC A"},
        "FI0009003306": {"SAMPO AB"},
    }
    transactions = [
        Transaction(
            date=date(2023, 1, 1),
            transaction_type=TransactionType.BUY,
            symbol="SAMPO OYJ A",
            ISIN="FI0009003305",
            quantity=1,
            price=1,
            fees=0,
            currency="EUR",
        )
    ]

    strategy.execute(
        plan=plan,
        symbol_to_isins=symbol_to_isins,
        isin_to_symbols=isin_to_symbols,
        transactions=transactions,
    )

    assert len(plan.suggestions) > 0
    assert "isin change" in plan.suggestions[0].rationale.lower()


def test_fuzzy_match_strategy_acronym():
    strategy = FuzzyMatchStrategy()
    plan = MappingPlan(
        symbol_mappings={},
        isin_mappings={},
        suggestions=[],
    )
    symbol_to_isins = {
        "EVOLUTION GAMING GROUP": {"SE0012673267"},
        "EVO": {"SE0012673267"},
    }
    isin_to_symbols = {
        "SE0012673267": {"EVOLUTION GAMING GROUP", "EVO"},
    }
    transactions = [
        Transaction(
            date=date(2023, 1, 1),
            transaction_type=TransactionType.BUY,
            symbol="EVO",
            ISIN="SE0012673267",
            quantity=1,
            price=1,
            fees=0,
            currency="SEK",
        )
    ]

    strategy.execute(
        plan=plan,
        symbol_to_isins=symbol_to_isins,
        isin_to_symbols=isin_to_symbols,
        transactions=transactions,
    )

    assert len(plan.suggestions) > 0
    # You may want to add more specific assertions here based on the expected suggestions


def test_conflict_detection_strategy():
    strategy = ConflictDetectionStrategy()
    plan = MappingPlan(
        symbol_mappings={"a": "b", "b": "a"},
        isin_mappings={},
        suggestions=[],
    )

    strategy.execute(plan=plan)

    assert plan.symbol_mappings == {"a": "b"}
