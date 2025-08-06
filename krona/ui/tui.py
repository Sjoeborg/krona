"""Textual TUI for Krona transaction processing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Footer, Header, ProgressBar, Static, TabbedContent, TabPane

if TYPE_CHECKING:
    from krona.models.mapping import MappingPlan
    from krona.models.position import Position
    from krona.models.suggestion import Suggestion

from krona.models.suggestion import SuggestionStatus
from krona.utils.logger import logger


class KronaTUI(App):
    """Main Krona TUI application."""

    if TYPE_CHECKING:
        from krona.ui.tui_wrapper import TUIWrapper

    CSS_PATH = "styles/tui.tcss"
    wrapper: TUIWrapper | None = None

    def __init__(
        self,
        wrapper: TUIWrapper,
        plan: MappingPlan | None = None,
        positions: list[Position] | None = None,
    ) -> None:
        super().__init__()
        self.plan = plan
        self.positions = positions or []
        self.suggestions = plan.suggestions if plan else []
        self.wrapper = wrapper

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with TabbedContent():
            with TabPane("Symbol Mappings", id="mappings"):
                yield Static("🔗 Symbol Mapping Management", classes="view-title")

                # Control buttons
                with Horizontal(classes="controls"):
                    yield Button("✅ Accept All", id="accept-all", variant="success")
                    yield Button("❌ Decline All", id="decline-all", variant="error")
                    yield Button("🏁 Finish", id="finish", variant="default")

                # Progress indicator
                if self.suggestions:
                    accepted = len([s for s in self.suggestions if s.status.value == "accepted"])
                    total = len(self.suggestions)
                    with Horizontal(classes="progress-container"):
                        yield Static(f"Progress: {accepted}/{total}", classes="progress-label")
                        progress = ProgressBar(total=total, show_eta=False)
                        progress.advance(accepted)
                        yield progress

                # Check if there are pending suggestions
                pending_suggestions = [s for s in self.suggestions if s.status.value == "pending"]

                if not self.suggestions:
                    # No suggestions at all
                    yield Static(
                        "No mapping suggestions found. All symbols are already mapped or no conflicts detected.",
                        classes="settings-placeholder",
                    )
                elif not pending_suggestions:
                    # All suggestions are accepted/declined
                    yield Static(
                        "✅ All mapping suggestions have been processed. You can click 'Finish' to apply the mappings.",
                        classes="settings-placeholder",
                    )

                # Always show the suggestions table to display existing mappings
                table = DataTable(classes="suggestions-table", cursor_type="row")
                table.add_columns(
                    "ID", "Status", "Source", "Target", "Source ISIN", "Target ISIN", "Confidence", "Rationale"
                )
                self._populate_suggestions_table(table)

                yield table

            with TabPane("Portfolio", id="positions"):
                yield Static("💼 Portfolio Positions", classes="view-title")

                # Dashboard stats
                with Vertical(classes="dashboard-stats"):
                    yield Static("Portfolio Overview", classes="stats-title")

                    with Horizontal(classes="stats-row"):
                        with Vertical(classes="stat-card"):
                            yield Static("Total Positions", classes="stat-label")
                            yield Static(str(len([p for p in self.positions if not p.is_closed])), classes="stat-value")

                        with Vertical(classes="stat-card"):
                            yield Static("Total Value", classes="stat-label")
                            total_value = sum(p.cost_basis for p in self.positions if not p.is_closed)
                            yield Static(f"{total_value:.2f}", classes="stat-value")

                        with Vertical(classes="stat-card"):
                            yield Static("Total Dividends", classes="stat-label")
                            total_dividends = sum(p.dividends for p in self.positions)
                            yield Static(f"{total_dividends:.2f}", classes="stat-value")

                        with Vertical(classes="stat-card"):
                            yield Static("Closed Positions", classes="stat-label")
                            closed_count = len([p for p in self.positions if p.is_closed])
                            yield Static(str(closed_count), classes="stat-value")

                # Filter controls
                with Horizontal(classes="filter-controls"):
                    yield Button("🔄 Refresh", id="refresh-positions", variant="primary")
                    yield Button("📈 Show Open Only", id="filter-open", variant="default")
                    yield Button("📉 Show Closed Only", id="filter-closed", variant="default")
                    yield Button("📋 Show All", id="show-all", variant="default")

                # Positions table
                table = DataTable(classes="positions-table")
                table.add_columns(
                    "Symbol", "ISIN", "Quantity", "Avg Price", "Cost Basis", "Dividends", "Fees", "Status", "P&L"
                )
                self._populate_positions_table(table)
                yield table

            with TabPane("Analytics", id="charts"):
                yield Static("📈 Portfolio Analytics", classes="view-title")
                yield Static("Analytics charts coming soon...", classes="settings-placeholder")

                # Add some mock analytics content to fill the space
                with Vertical(classes="analytics-content"):
                    yield Static("📊 Portfolio Performance")
                    yield Static("Total Return: +15.3%")
                    yield Static("Annualized Return: +8.2%")
                    yield Static("Sharpe Ratio: 1.45")
                    yield Static("")
                    yield Static("📈 Asset Allocation")
                    yield Static("Stocks: 65%")
                    yield Static("Bonds: 25%")
                    yield Static("Cash: 10%")
                    yield Static("")
                    yield Static("🎯 Top Holdings")
                    yield Static("1. Bahnhof B: 25.3%")
                    yield Static("2. Investor A: 18.7%")
                    yield Static("3. Evolution: 12.1%")

            with TabPane("Settings", id="settings"):
                # Simple settings view without custom CSS classes
                yield Static("⚙️ Settings & Configuration", classes="view-title")
                yield Static("Settings panel is working!", classes="settings-placeholder")

                # Data Processing Section
                yield Static("📊 Data Processing")
                yield Static("Auto-accept high confidence mappings: ✅ Enabled")
                yield Static("Minimum confidence threshold: 90%")
                yield Static("Default currency: SEK")

                # Interface Section
                yield Static("🎨 Interface")
                yield Static("Theme: 🌙 Dark")
                yield Static("Show transaction details: ✅ Enabled")
                yield Static("Auto-refresh interval: 30 seconds")

                # Data Management Section
                yield Static("💾 Data Management")
                yield Static("Backup mappings automatically: ✅ Enabled")
                yield Static("Export format: CSV")
                yield Static("Data directory: /Users/sjoborg/krona/data")

                # Action buttons
                yield Button("💾 Save Settings", id="save-settings", variant="success")
                yield Button("🔄 Reset to Defaults", id="reset-settings", variant="warning")
                yield Button("📤 Export Configuration", id="export-config", variant="primary")

        yield Footer()

    # Suggestions table
    def _refresh_suggestions_table(self, table: DataTable) -> None:
        """Refresh the suggestions table."""
        table.clear()
        self._populate_suggestions_table(table)

    @on(DataTable.RowSelected)
    def toggle_suggestion(self, event: DataTable.RowSelected) -> None:
        """Toggle suggestion status when row is selected."""
        if event.row_key is not None and event.row_key.value is not None:
            idx = int(event.row_key.value)
            if 0 <= idx < len(self.suggestions):
                suggestion = self.suggestions[idx]
                if suggestion.status == SuggestionStatus.ACCEPTED:
                    suggestion.status = SuggestionStatus.DECLINED
                else:
                    suggestion.status = SuggestionStatus.ACCEPTED
                self.suggestions[idx] = suggestion
                self._refresh_suggestions_table(event.data_table)
                self.update_progress_bar(
                    len([s for s in self.suggestions if s.status.value == "accepted"]), len(self.suggestions)
                )

    @on(Button.Pressed, "#accept-all")
    def accept_all_suggestions(self) -> None:
        """Accept all suggestions."""

        for suggestion in self.suggestions:
            suggestion.status = SuggestionStatus.ACCEPTED
        table = self.query_one(DataTable)
        self._refresh_suggestions_table(table)

    @on(Button.Pressed, "#decline-all")
    def decline_all_suggestions(self) -> None:
        """Decline all suggestions."""

        for suggestion in self.suggestions:
            suggestion.status = SuggestionStatus.DECLINED
        table = self.query_one(DataTable)
        self._refresh_suggestions_table(table)

    @on(Button.Pressed, "#finish")
    def finish_mappings(self) -> None:
        """Finish and apply accepted mappings."""
        if self.wrapper:
            self.wrapper._finish_mappings()

    def _populate_suggestions_table(self, table: DataTable) -> None:
        """Populate the suggestions table with current suggestions."""
        for i, suggestion in enumerate(self.suggestions):
            status_icon = self._get_status_icon(suggestion)
            confidence_str = f"{suggestion.confidence:.0%}" if suggestion.confidence is not None else "N/A"

            table.add_row(
                str(i),
                status_icon,
                suggestion.source_symbol,
                suggestion.target_symbol,
                suggestion.source_isin or "N/A",
                suggestion.target_isin or "N/A",
                confidence_str,
                suggestion.rationale,
                key=str(i),
            )

    def _get_status_icon(self, suggestion: Suggestion) -> str:
        """Get status icon for suggestion."""
        if suggestion.status == SuggestionStatus.ACCEPTED:
            return "✓"
        elif suggestion.status == SuggestionStatus.DECLINED:
            return "✗"
        else:
            return "○"

    def update_progress_bar(self, accepted: int, total: int) -> None:
        """Update the progress bar."""
        progress_bar = self.query_one(ProgressBar)
        progress_bar.advance(accepted)

    def update_suggestions(self, suggestions: list[Suggestion]) -> None:
        """Update the suggestions in the mappings view."""
        self.suggestions = suggestions
        table = self.query_one(DataTable)
        table.clear()
        self._populate_suggestions_table(table)
        self.update_progress_bar(
            len([s for s in self.suggestions if s.status.value == "accepted"]), len(self.suggestions)
        )

    # General

    def switch_tab(self, tab_id: str) -> None:
        """Switch to the specified tab."""
        tabbed_content = self.query_one(TabbedContent)
        tabbed_content.active = tab_id

    # Positions
    def _populate_positions_table(self, table: DataTable) -> None:
        """Populate the positions table."""
        logger.info(f"Populating positions table with {len(self.positions)} positions")
        for i, position in enumerate(self.positions):
            status = "🔴 CLOSED" if position.is_closed else "🟢 OPEN"
            realized_profit = f"{position.realized_profit:.2f}" if position.realized_profit is not None else "N/A"
            print(realized_profit)
            # Color code P&L
            if position.realized_profit is not None:
                if position.realized_profit > 0:
                    pl_display = f"💚 +{position.realized_profit:.2f}"
                elif position.realized_profit < 0:
                    pl_display = f"❤️ {position.realized_profit:.2f}"
                else:
                    pl_display = f"⚪ {position.realized_profit:.2f}"
            else:
                pl_display = "⚪ N/A"

            table.add_row(
                f"📊 {position.symbol}",
                position.ISIN,
                f"{int(position.quantity)}",
                f"{position.price:.2f} {position.currency}",
                f"{position.cost_basis:.2f} {position.currency}",
                f"{position.dividends:.2f} {position.currency}",
                f"{position.fees:.2f} {position.currency}",
                status,
                pl_display,
                key=str(i),
            )

    @on(DataTable.RowSelected)
    def show_transactions(self, event: DataTable.RowSelected) -> None:
        """Show transaction history for selected position."""
        if event.row_key is not None and event.row_key.value is not None:
            idx = int(event.row_key.value)
            if 0 <= idx < len(self.positions):
                position = self.positions[idx]
                self.show_transaction_history(position)

    def update_positions(self, positions: list[Position]) -> None:
        """Update the positions in the positions view."""
        self.positions = positions

        # Check if the app is still running and widgets are available
        # Update positions view
        positions_tab = self.query_one("#positions", TabPane)
        positions_table = positions_tab.query_one(DataTable)

        positions_table.clear()
        self._populate_positions_table(positions_table)

        # Update dashboard stats
        # dashboard_stats = positions_tab.query_one(DashboardStats)
        # dashboard_stats.update_stats(positions)

        # # Update charts view
        # charts_view = self.query_one(ChartsView)
        # charts_view.update_positions(positions)

    def show_transaction_history(self, position: Position) -> None:
        """Show transaction history for a position."""
        tabbed_content = self.query_one(TabbedContent)

        # Remove existing transaction history tab if it exists
        existing_pane = tabbed_content.get_pane("transaction-history")
        if existing_pane:
            tabbed_content.remove_pane("transaction-history")

        # Add new transaction history tab
        # transaction_view = TransactionHistoryView(position)
        # tab_pane = TabPane(f"Transactions: {position.symbol}", transaction_view, id="transaction-history")
        # tabbed_content.add_pane(tab_pane)
        # tabbed_content.active = "transaction-history"

    # Dashboard
    def update_stats(self, positions: list[Position]) -> None:
        """Update dashboard statistics."""
        self.positions = positions
        stats = self.query(".stat-value")
        if len(stats) >= 4:
            stats[0].update(str(len([p for p in positions if not p.is_closed])))
            total_value = sum(p.cost_basis for p in positions if not p.is_closed)
            stats[1].update(f"{total_value:.2f}")
            total_dividends = sum(p.dividends for p in positions)
            stats[2].update(f"{total_dividends:.2f}")
            closed_count = len([p for p in positions if p.is_closed])
            stats[3].update(str(closed_count))

    # Transactions
    @on(Button.Pressed, "#back-to-positions")
    def back_to_positions(self) -> None:
        """Return to positions view."""
        self.app.call_from_thread(self.switch_to_positions)

    def switch_to_positions(self) -> None:
        """Switch to positions view."""
        tui_app = self.app
        if hasattr(tui_app, "switch_tab"):
            tui_app.switch_tab("positions")
