from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from krona.models.mapping import MappingPlan
from krona.models.position import Position
from krona.models.suggestion import Suggestion, SuggestionStatus
from krona.processor.strategies.conflict_detection import ConflictDetectionStrategy
from krona.utils.io import (
    DEFAULT_MAPPING_CONFIG_FILE,
    load_mapping_config,
    save_mapping_config,
)

AUTO_ACCEPT_CONFIDENCE = 0.9


class CLI:
    def __init__(self, plan: MappingPlan | None = None) -> None:
        self.plan = plan
        self.console = Console()

    def display_positions(self, positions: list[Position]) -> None:
        """Display the final positions in a table."""
        table = Table(title="Final Positions", show_header=True, header_style="bold magenta")
        table.add_column("Symbol", style="cyan")
        table.add_column("ISIN", style="blue")
        table.add_column("Quantity", style="yellow")
        table.add_column("Cost Basis", style="green")
        table.add_column("Dividends", style="green")
        table.add_column("Fees", style="red")
        table.add_column("Realized Profit", style="green")

        for position in positions:
            table.add_row(
                position.symbol,
                position.ISIN,
                f"{position.quantity:.2f}",
                f"{position.cost_basis:.2f} {position.currency}",
                f"{position.dividends:.2f} {position.currency}",
                f"{position.fees:.2f} {position.currency}",
                f"{position.realized_profit:.2f} {position.currency}" if position.is_closed else "N/A",
            )
        self.console.print(table)

    @classmethod
    def prompt_load_existing_config(cls, config_file: str = DEFAULT_MAPPING_CONFIG_FILE) -> MappingPlan | None:
        """Prompt the user to load existing mapping configuration if it exists."""
        from pathlib import Path

        config_path = Path(config_file)

        if not config_path.exists():
            return None

        console = Console()
        console.print(f"[bold yellow]Found existing mapping configuration: {config_file}[/bold yellow]")

        if Confirm.ask("Would you like to load the existing mapping configuration?"):
            existing_plan = load_mapping_config(config_file)
            if existing_plan is None:
                console.print(f"[bold red]Error loading mapping configuration from {config_file}[/bold red]")
            return existing_plan

        return None

    def run(self) -> MappingPlan:
        """Run the CLI."""
        if not self.plan:
            return MappingPlan({}, {}, [])
        self._handle_high_confidence_suggestions()
        self._handle_low_confidence_suggestions()
        return self.plan

    def _handle_suggestions(self, suggestions: list[Suggestion], pre_selected: bool) -> None:
        if not suggestions:
            return

        for suggestion in suggestions:
            suggestion.status = SuggestionStatus.ACCEPTED if pre_selected else SuggestionStatus.PENDING

        while True:
            self._display_suggestions(suggestions)
            command = Prompt.ask("Enter command")

            match command.lower().split():
                case ["f"]:
                    self._finish(suggestions)
                    break
                case ["a", id_or_range]:
                    self._accept_suggestions(id_or_range, suggestions)
                case ["d", id_or_range]:
                    self._decline_suggestions(id_or_range, suggestions)
                case ["t", id_or_range]:
                    self._toggle_suggestion(id_or_range, suggestions)
                case ["e", id_or_range]:
                    self._edit_suggestion(id_or_range, suggestions)
                case ["n"]:
                    self._add_new_mapping()
                case _:
                    self.console.print("[bold red]Invalid command[/bold red]")

    def _finish(self, suggestions: list[Suggestion]) -> None:
        """Apply accepted suggestions to the plan"""
        if self.plan:
            for suggestion in suggestions:
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

            # Save the mapping configuration before finishing
            if save_mapping_config(self.plan):
                self.console.print("[bold green]Mapping configuration saved to mappings.yml[/bold green]")
            else:
                self.console.print("[bold red]Error saving mapping configuration[/bold red]")

    def _display_suggestions(self, suggestions: list[Suggestion]) -> None:
        table = Table(title="Mapping Suggestions", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim")
        table.add_column("Status", style="bold")
        table.add_column("Source Name", style="cyan")
        table.add_column("Target Name", style="cyan")
        table.add_column("Source ISIN", style="blue")
        table.add_column("Target ISIN", style="blue")
        table.add_column("Confidence", style="yellow")
        table.add_column("Info", style="green")

        for i, suggestion in enumerate(suggestions):
            if suggestion.status == SuggestionStatus.ACCEPTED:
                status_icon = "[green]✔[/green]"
            elif suggestion.status == SuggestionStatus.DECLINED:
                status_icon = "[red]✖[/red]"
            else:
                status_icon = "[white]☐[/white]"

            isin_color = (
                "yellow"
                if suggestion.source_isin
                and suggestion.target_isin
                and suggestion.source_isin != suggestion.target_isin
                else "green"
            )

            table.add_row(
                str(i),
                status_icon,
                suggestion.source_symbol,
                suggestion.target_symbol,
                f"[{isin_color}]{suggestion.source_isin or 'N/A'}[/]",
                f"[{isin_color}]{suggestion.target_isin or 'N/A'}[/]",
                f"{suggestion.confidence:.0%}",
                suggestion.rationale,
            )

        self.console.print(table)
        self.console.print(
            "\n[bold]Commands:[/] (a)ccept <id>, (d)ecline <id>, (t)oggle <id>, (e)dit <id>, (n)ew, (f)inish"
            "\nid can be a single ID or a range of IDs separated by a dash (e.g. 1-3)."
        )

    def _accept_suggestions(self, id_or_range: str, suggestions: list[Suggestion]) -> None:
        try:
            start, end = self._parse_id_or_range(id_or_range)

            for idx in range(start, end + 1):
                if 0 <= idx < len(suggestions):
                    suggestions[idx].status = SuggestionStatus.ACCEPTED
        except (ValueError, IndexError):
            self.console.print(
                "[bold red]Invalid ID. Please use a single ID or a range of IDs separated by a dash (e.g. 1-3).[/bold red]"
            )

    def _decline_suggestions(self, id_or_range: str, suggestions: list[Suggestion]) -> None:
        try:
            start, end = self._parse_id_or_range(id_or_range)

            for idx in range(start, end + 1):
                if 0 <= idx < len(suggestions):
                    suggestions[idx].status = SuggestionStatus.DECLINED
        except (ValueError, IndexError):
            self.console.print(
                "[bold red]Invalid ID. Please use a single ID or a range of IDs separated by a dash (e.g. 1-3).[/bold red]"
            )

    def _toggle_suggestion(self, id_or_range: str, suggestions: list[Suggestion]) -> None:
        try:
            start, end = self._parse_id_or_range(id_or_range)

            for idx in range(start, end + 1):
                if 0 <= idx < len(suggestions):
                    if suggestions[idx].status == SuggestionStatus.ACCEPTED:
                        suggestions[idx].status = SuggestionStatus.DECLINED
                    else:
                        suggestions[idx].status = SuggestionStatus.ACCEPTED
        except (ValueError, IndexError):
            self.console.print(
                "[bold red]Invalid ID. Please use a single ID or a range of IDs separated by a dash (e.g. 1-3).[/bold red]"
            )

    def _edit_suggestion(self, id_or_range: str, suggestions: list[Suggestion]) -> None:
        try:
            start, end = self._parse_id_or_range(id_or_range)

            for idx in range(start, end + 1):
                if 0 <= idx < len(suggestions):
                    new_target = Prompt.ask(f"Enter new target for '{suggestions[idx].source_symbol}'")
                    suggestions[idx].target_symbol = new_target
                    suggestions[idx].status = SuggestionStatus.ACCEPTED
        except (ValueError, IndexError):
            self.console.print(
                "[bold red]Invalid ID. Please use a single ID or a range of IDs separated by a dash (e.g. 1-3).[/bold red]"
            )

    def _add_new_mapping(self) -> None:
        if self.plan:
            source = Prompt.ask("Enter source symbol")
            target = Prompt.ask("Enter target symbol")
            self.plan.symbol_mappings[source] = target
            self.console.print(f"[bold green]Added new mapping: {source} -> {target}[/bold green]")

    def _handle_high_confidence_suggestions(self) -> None:
        """Handle high-confidence suggestions."""
        if self.plan:
            high_confidence_suggestions = [
                s for s in self.plan.pending_suggestions if s.confidence >= AUTO_ACCEPT_CONFIDENCE
            ]
            self.console.print("[bold green]High-confidence suggestions[/bold green]")
            self._handle_suggestions(high_confidence_suggestions, pre_selected=True)

    def _handle_low_confidence_suggestions(self) -> None:
        """Handle low-confidence suggestions."""
        if self.plan:
            low_confidence_suggestions = [
                s for s in self.plan.pending_suggestions if s.confidence < AUTO_ACCEPT_CONFIDENCE
            ]
            self.console.print("[bold yellow]Low-confidence suggestions[/bold yellow]")
            self._handle_suggestions(low_confidence_suggestions, pre_selected=False)

    def _parse_id_or_range(self, id_or_range: str) -> tuple[int, int]:
        """Parse a single numerical ID or a range of IDs separated by a dash.

        Returns a tuple of the start and end indices for us to loop over.
        """
        if "-" in id_or_range:
            start, end = id_or_range.split("-")
            start = int(start)
            end = int(end)
        else:
            start = int(id_or_range)
            end = start
        return start, end
