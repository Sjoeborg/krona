"""Chart widgets inspired by Dolphie for financial data visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotext as plt
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static, Switch

if TYPE_CHECKING:
    from krona.models.position import Position


class PortfolioChart(Widget):
    """Portfolio value chart widget."""

    def __init__(self, positions: list[Position] | None = None) -> None:
        super().__init__()
        self.positions = positions or []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Portfolio Value Over Time", classes="chart-title")
            with Horizontal(classes="chart-controls"):
                yield Switch(value=True, id="show-cost-basis")
                yield Static("Cost Basis", classes="switch-label")
                yield Switch(value=True, id="show-market-value")
                yield Static("Market Value", classes="switch-label")
                yield Switch(value=False, id="show-dividends")
                yield Static("Dividends", classes="switch-label")
            yield Static(id="portfolio-chart", classes="chart-display", markup=False)

    def on_mount(self) -> None:
        self.call_after_refresh(self._refresh_chart)

    def _generate_portfolio_chart(self, width: int = 60, height: int = 20) -> str:
        """Generate portfolio value chart using plotext."""
        plt.clear_data()
        plt.clear_figure()

        if not self.positions:
            plt.text("No portfolio data available", 0.5, 0.5)
            return plt.build()

        # Calculate portfolio metrics (kept for future toggles)

        # Simple bar chart of positions
        symbols = [pos.symbol[:10] for pos in self.positions[:10]]  # Limit to 10 positions
        values = [pos.cost_basis for pos in self.positions[:10]]
        # Avoid printing to stdout inside widgets

        plt.bar(symbols, values, orientation="h")
        plt.title("Portfolio Positions by Value")
        plt.xlabel("Value (Cost Basis)")
        plt.ylabel("Symbol")

        # Set size for better display in terminal
        plt.plotsize(max(20, width), max(10, height))

        return plt.build()

    @on(Switch.Changed)
    def update_chart(self) -> None:
        """Update chart when switches change."""
        self._refresh_chart()

    def _refresh_chart(self) -> None:
        chart_display = self.query_one("#portfolio-chart", Static)
        width = getattr(chart_display.size, "width", 60) - 2
        height = getattr(chart_display.size, "height", 20) - 2
        chart_display.update(Text.from_ansi(self._generate_portfolio_chart(width=width, height=height)))


class TransactionVolumeChart(Widget):
    """Transaction volume over time chart."""

    def __init__(self, positions: list[Position] | None = None) -> None:
        super().__init__()
        self.positions = positions or []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Transaction Volume Analysis", classes="chart-title")
            with Horizontal(classes="chart-controls"):
                yield Switch(value=True, id="show-buys")
                yield Static("Buy Orders", classes="switch-label")
                yield Switch(value=True, id="show-sells")
                yield Static("Sell Orders", classes="switch-label")
                yield Switch(value=False, id="show-dividends-vol")
                yield Static("Dividend Payments", classes="switch-label")
            yield Static(id="volume-chart", classes="chart-display", markup=False)

    def on_mount(self) -> None:
        self.call_after_refresh(self._refresh_chart)

    def _generate_volume_chart(self, width: int = 60, height: int = 20) -> str:
        """Generate transaction volume chart."""
        plt.clear_data()
        plt.clear_figure()

        if not self.positions:
            plt.text("No transaction data available", 0.5, 0.5)
            return plt.build()

        # Count transactions by type
        buy_count = 0
        sell_count = 0
        dividend_count = 0

        for position in self.positions:
            for transaction in position.transactions:
                if transaction.transaction_type.value == "BUY":
                    buy_count += 1
                elif transaction.transaction_type.value == "SELL":
                    sell_count += 1
                elif transaction.transaction_type.value == "DIVIDEND":
                    dividend_count += 1

        # Create bar chart
        categories = ["Buy", "Sell", "Dividend"]
        counts = [buy_count, sell_count, dividend_count]

        plt.bar(categories, counts)
        plt.title("Transaction Volume by Type")
        plt.xlabel("Transaction Type")
        plt.ylabel("Count")
        plt.plotsize(max(20, width), max(10, height))

        return plt.build()

    @on(Switch.Changed)
    def update_chart(self) -> None:
        """Update chart when switches change."""
        self._refresh_chart()

    def _refresh_chart(self) -> None:
        chart_display = self.query_one("#volume-chart", Static)
        width = getattr(chart_display.size, "width", 60) - 2
        height = getattr(chart_display.size, "height", 20) - 2
        chart_display.update(Text.from_ansi(self._generate_volume_chart(width=width, height=height)))


class PerformanceChart(Widget):
    """Performance metrics chart."""

    def __init__(self, positions: list[Position] | None = None) -> None:
        super().__init__()
        self.positions = positions or []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Performance Metrics", classes="chart-title")
            with Horizontal(classes="chart-controls"):
                yield Switch(value=True, id="show-realized")
                yield Static("Realized P&L", classes="switch-label")
                yield Switch(value=True, id="show-dividends-perf")
                yield Static("Dividends", classes="switch-label")
                yield Switch(value=True, id="show-fees")
                yield Static("Fees", classes="switch-label")
            yield Static(id="performance-chart", classes="chart-display", markup=False)

    def on_mount(self) -> None:
        self.call_after_refresh(self._refresh_chart)

    def _generate_performance_chart(self, width: int = 60, height: int = 20) -> str:
        """Generate performance metrics chart."""
        plt.clear_data()
        plt.clear_figure()

        if not self.positions:
            plt.text("No performance data available", 0.5, 0.5)
            return plt.build()

        # Calculate performance metrics
        closed_positions = [pos for pos in self.positions if pos.is_closed and pos.realized_profit is not None]

        if not closed_positions:
            plt.text("No closed positions for performance analysis", 0.5, 0.5)
            return plt.build()

        symbols = [pos.symbol for pos in closed_positions[:10]]  # Top 10
        profits = [pos.realized_profit for pos in closed_positions[:10]]

        plt.bar(symbols, profits)
        plt.title("Realized P&L by Position")
        plt.xlabel("Symbol")
        plt.ylabel("Realized Profit/Loss")
        plt.plotsize(max(20, width), max(10, 15))

        return plt.build()

    @on(Switch.Changed)
    def update_chart(self) -> None:
        """Update chart when switches change."""
        self._refresh_chart()

    def _refresh_chart(self) -> None:
        chart_display = self.query_one("#performance-chart", Static)
        width = getattr(chart_display.size, "width", 60) - 2
        height = getattr(chart_display.size, "height", 20) - 2
        chart_display.update(Text.from_ansi(self._generate_performance_chart(width=width, height=height)))
