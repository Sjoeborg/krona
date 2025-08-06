"""Chart widgets inspired by Dolphie for financial data visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotext as plt
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Static, Switch, TabbedContent, TabPane

from krona.utils.logger import logger

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
            yield Static(self._generate_portfolio_chart(), id="portfolio-chart", classes="chart-display")

    def _generate_portfolio_chart(self) -> str:
        """Generate portfolio value chart using plotext."""
        plt.clear_data()
        plt.clear_figure()

        if not self.positions:
            plt.text("No portfolio data available", 0.5, 0.5)
            return plt.build()

        # Calculate portfolio metrics
        total_cost_basis = sum(pos.cost_basis for pos in self.positions if not pos.is_closed)
        total_dividends = sum(pos.dividends for pos in self.positions)

        # Simple bar chart of positions
        symbols = [pos.symbol[:10] for pos in self.positions[:10]]  # Limit to 10 positions
        values = [pos.cost_basis for pos in self.positions[:10]]
        print(total_cost_basis)
        print(total_dividends)

        plt.bar(symbols, values, orientation="h")
        plt.title("Portfolio Positions by Value")
        plt.xlabel("Value (Cost Basis)")
        plt.ylabel("Symbol")

        # Set size for better display in terminal
        plt.plotsize(60, 20)

        return plt.build()

    @on(Switch.Changed)
    def update_chart(self) -> None:
        """Update chart when switches change."""
        chart_display = self.query_one("#portfolio-chart", Static)
        chart_display.update(self._generate_portfolio_chart())


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
            yield Static(self._generate_volume_chart(), id="volume-chart", classes="chart-display")

    def _generate_volume_chart(self) -> str:
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
        plt.plotsize(50, 15)

        return plt.build()

    @on(Switch.Changed)
    def update_chart(self) -> None:
        """Update chart when switches change."""
        chart_display = self.query_one("#volume-chart", Static)
        chart_display.update(self._generate_volume_chart())


class AssetAllocationChart(Widget):
    """Asset allocation pie chart."""

    def __init__(self, positions: list[Position] | None = None) -> None:
        super().__init__()
        self.positions = positions or []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Asset Allocation", classes="chart-title")
            with Horizontal(classes="chart-controls"):
                yield Button("Refresh", id="refresh-allocation", variant="primary")
                yield Switch(value=True, id="show-percentages")
                yield Static("Show %", classes="switch-label")
            yield Static(self._generate_allocation_chart(), id="allocation-chart", classes="chart-display")

    def _generate_allocation_chart(self) -> str:
        """Generate asset allocation chart."""
        plt.clear_data()
        plt.clear_figure()

        if not self.positions:
            plt.text("No allocation data available", 0.5, 0.5)
            return plt.build()

        # Calculate allocation by position
        open_positions = [pos for pos in self.positions if not pos.is_closed]

        if not open_positions:
            plt.text("No open positions for allocation", 0.5, 0.5)
            return plt.build()

        total_value = sum(pos.cost_basis for pos in open_positions)

        # Get top 8 positions and group rest as "Others"
        sorted_positions = sorted(open_positions, key=lambda p: p.cost_basis, reverse=True)
        top_positions = sorted_positions[:8]
        others_value = sum(pos.cost_basis for pos in sorted_positions[8:])

        symbols = [pos.symbol for pos in top_positions]
        values = [pos.cost_basis for pos in top_positions]

        if others_value > 0:
            symbols.append("Others")
            values.append(others_value)

        # Create horizontal bar chart (as pie charts are complex in terminal)
        percentages = [(val / total_value) * 100 for val in values]

        plt.bar(symbols, percentages, orientation="h")
        plt.title("Asset Allocation (%)")
        plt.xlabel("Percentage")
        plt.ylabel("Symbol")
        plt.plotsize(60, len(symbols) + 5)

        return plt.build()

    @on(Button.Pressed, "#refresh-allocation")
    def refresh_allocation(self) -> None:
        """Refresh allocation chart."""
        chart_display = self.query_one("#allocation-chart", Static)
        chart_display.update(self._generate_allocation_chart())

    @on(Switch.Changed)
    def update_chart(self) -> None:
        """Update chart when switches change."""
        chart_display = self.query_one("#allocation-chart", Static)
        chart_display.update(self._generate_allocation_chart())


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
            yield Static(self._generate_performance_chart(), id="performance-chart", classes="chart-display")

    def _generate_performance_chart(self) -> str:
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
        plt.plotsize(60, 15)

        return plt.build()

    @on(Switch.Changed)
    def update_chart(self) -> None:
        """Update chart when switches change."""
        chart_display = self.query_one("#performance-chart", Static)
        chart_display.update(self._generate_performance_chart())


class ChartsView(Widget):
    """Main charts view container inspired by Dolphie."""

    def __init__(self, positions: list[Position] | None = None) -> None:
        super().__init__()
        self.positions = positions or []

    def compose(self) -> ComposeResult:
        with Vertical(classes="charts-view"):
            yield Static("📊 Portfolio Analytics Dashboard", classes="view-title")

            with TabbedContent():
                with TabPane("Portfolio Value", id="portfolio-tab"):
                    yield PortfolioChart(self.positions)

                with TabPane("Transaction Volume", id="volume-tab"):
                    yield TransactionVolumeChart(self.positions)

                with TabPane("Asset Allocation", id="allocation-tab"):
                    yield AssetAllocationChart(self.positions)

                with TabPane("Performance", id="performance-tab"):
                    yield PerformanceChart(self.positions)

    def update_positions(self, positions: list[Position]) -> None:
        """Update all charts with new position data."""
        self.positions = positions

        # Update each chart
        portfolio_chart = self.query_one(PortfolioChart)
        portfolio_chart.positions = positions

        volume_chart = self.query_one(TransactionVolumeChart)
        volume_chart.positions = positions

        allocation_chart = self.query_one(AssetAllocationChart)
        allocation_chart.positions = positions

        performance_chart = self.query_one(PerformanceChart)
        performance_chart.positions = positions

        # Refresh displays
        self._refresh_all_charts()

    def _refresh_all_charts(self) -> None:
        """Refresh all chart displays."""
        try:
            portfolio_chart = self.query_one(PortfolioChart)
            portfolio_display = portfolio_chart.query_one("#portfolio-chart", Static)
            portfolio_display.update(portfolio_chart._generate_portfolio_chart())

            volume_chart = self.query_one(TransactionVolumeChart)
            volume_display = volume_chart.query_one("#volume-chart", Static)
            volume_display.update(volume_chart._generate_volume_chart())

            allocation_chart = self.query_one(AssetAllocationChart)
            allocation_display = allocation_chart.query_one("#allocation-chart", Static)
            allocation_display.update(allocation_chart._generate_allocation_chart())

            performance_chart = self.query_one(PerformanceChart)
            performance_display = performance_chart.query_one("#performance-chart", Static)
            performance_display.update(performance_chart._generate_performance_chart())
        except Exception:
            # Gracefully handle cases where charts aren't ready yet
            logger.info("Error refreshing charts")
