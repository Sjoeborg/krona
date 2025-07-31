from datetime import date
from unittest.mock import MagicMock, patch

from krona.models.mapping import MappingPlan
from krona.models.transaction import Transaction, TransactionType
from krona.processor.mapper import Mapper


def test_create_mapping_plan():
    with (
        patch("krona.processor.mapper.FuzzyMatchStrategy") as mock_fuzzy_strategy,
        patch("krona.processor.mapper.ConflictDetectionStrategy") as mock_conflict_strategy,
        patch("krona.ui.cli.CLI.prompt_load_existing_config") as mock_prompt,
    ):
        # Arrange
        mock_fuzzy_instance = MagicMock()
        mock_conflict_instance = MagicMock()
        mock_fuzzy_strategy.return_value = mock_fuzzy_instance
        mock_conflict_strategy.return_value = mock_conflict_instance
        mock_prompt.return_value = None  # No existing config

        mapper = Mapper()
        transactions = [
            Transaction(
                date=date(2023, 1, 1),
                transaction_type=TransactionType.BUY,
                symbol="Evolution",
                ISIN="SE0012673267",
                quantity=10,
                price=100,
                fees=10,
                currency="SEK",
            )
        ]

        # Act
        plan = mapper.create_mapping_plan(transactions)

        # Assert
        assert isinstance(plan, MappingPlan)
        mock_fuzzy_instance.execute.assert_called_once()
        mock_conflict_instance.execute.assert_called_once()
