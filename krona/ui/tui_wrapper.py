"""TUI wrapper that integrates with the existing CLI functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

from krona.models.mapping import MappingPlan
from krona.models.suggestion import Suggestion, SuggestionStatus
from krona.processor.strategies.conflict_detection import ConflictDetectionStrategy
from krona.ui.tui import KronaTUI
from krona.utils.io import (
    DEFAULT_MAPPING_CONFIG_FILE,
    load_mapping_config,
    save_mapping_config,
)

if TYPE_CHECKING:
    from krona.models.position import Position
    from krona.processor.transaction import TransactionProcessor


class TUIWrapper:
    """Wrapper class that integrates TUI with existing CLI functionality."""

    def __init__(
        self,
        plan: MappingPlan | None = None,
        suggestions: list[Suggestion] | None = None,
        processor: TransactionProcessor | None = None,
    ) -> None:
        self.plan = plan
        self.suggestions = suggestions or []
        self.processor = processor
        self.tui_app: KronaTUI | None = None

    @classmethod
    def prompt_load_existing_config(cls, config_file: str = DEFAULT_MAPPING_CONFIG_FILE) -> MappingPlan | None:
        """Load existing mapping configuration if it exists."""
        from pathlib import Path

        config_path = Path(config_file)

        if not config_path.exists():
            return None

        # For now, just load the config without prompting
        # In the future, this could be a modal dialog in the TUI
        existing_plan = load_mapping_config(config_file)
        return existing_plan

    def run(self) -> MappingPlan:
        """Run the TUI and return the final mapping plan."""
        if not self.plan:
            return MappingPlan({}, {}, [])

        # Convert mapping plan to suggestions if no suggestions exist
        if not self.plan.suggestions:
            from krona.models.suggestion import Suggestion

            self.plan.suggestions = Suggestion.from_mapping_plan(self.plan)

        # If there are still no suggestions, create some from existing mappings for display
        if not self.plan.suggestions and self.plan.symbol_mappings:
            from krona.models.suggestion import Suggestion, SuggestionStatus

            # Create suggestions from existing symbol mappings for display
            for source, target in self.plan.symbol_mappings.items():
                if source != target:  # Skip identical mappings
                    suggestion = Suggestion(
                        source_symbol=source,
                        target_symbol=target,
                        confidence=1.0,  # High confidence for existing mappings
                        rationale="Existing mapping",
                        status=SuggestionStatus.ACCEPTED,
                    )
                    self.plan.suggestions.append(suggestion)

        # Create the TUI app
        self.tui_app = KronaTUI(plan=self.plan, wrapper=self)

        # Run the TUI (this will build the DOM and start the app)
        self.tui_app.run()
        return self.plan

    def _finish_mappings(self) -> None:
        """Apply accepted mappings and switch to positions view."""
        if self.plan:
            # Apply accepted suggestions to the plan
            for suggestion in self.plan.suggestions:
                if suggestion.status == SuggestionStatus.ACCEPTED:
                    canonical_symbol = suggestion.target_symbol
                    self.plan.symbol_mappings[suggestion.source_symbol] = canonical_symbol

                    # Map both ISINs to the canonical symbol
                    if suggestion.source_isin:
                        self.plan.isin_mappings[suggestion.source_isin] = canonical_symbol
                    if suggestion.target_isin:
                        self.plan.isin_mappings[suggestion.target_isin] = canonical_symbol

            # Re-run conflict detection to resolve any new circular dependencies
            conflict_detector = ConflictDetectionStrategy()
            conflict_detector.execute(plan=self.plan)

            # Save the mapping configuration
            if save_mapping_config(self.plan):
                # In a real implementation, we'd show a notification
                pass

            # Process transactions and get positions if we have a processor
            if self.processor:
                # Accept the plan in the processor
                self.processor.mapper.accept_plan(self.plan)

                # Get positions to display
                positions = list(self.processor.positions.values())
                if self.tui_app:
                    self.tui_app.update_positions(positions)
                    self.tui_app.switch_tab("positions")

    def _show_transaction_history(self, position: Position) -> None:
        """Show transaction history for a position."""
        if self.tui_app:
            self.tui_app.show_transaction_history(position)

    def display_positions(self, positions: list[Position]) -> None:
        """Display the final positions."""
        if self.tui_app:
            try:
                self.tui_app.update_positions(positions)
                self.tui_app.switch_tab("positions")
            except Exception:
                # TUI is no longer running, just print a summary
                print("\n📊 Portfolio Summary:")
                print(f"Total Positions: {len(positions)}")
                total_value = sum(p.cost_basis for p in positions if not p.is_closed)
                print(f"Total Value: {total_value:.2f}")
                total_dividends = sum(p.dividends for p in positions)
                print(f"Total Dividends: {total_dividends:.2f}")

    def _handle_high_confidence_suggestions(self) -> None:
        """Handle high-confidence suggestions by auto-accepting them."""
        if self.plan:
            AUTO_ACCEPT_CONFIDENCE = 0.9
            for suggestion in self.plan.pending_suggestions:
                if suggestion.confidence is not None and suggestion.confidence >= AUTO_ACCEPT_CONFIDENCE:
                    suggestion.status = SuggestionStatus.ACCEPTED

    def _handle_low_confidence_suggestions(self) -> None:
        """Handle low-confidence suggestions by leaving them for user review."""
        # These will be handled interactively in the TUI
        pass
