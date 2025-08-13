from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual_plotext import Plot, PlotextPlot

from krona.ui.charts.base import Chart

if TYPE_CHECKING:
    pass


class PortfolioChart(Chart):
    """Timeline of average trade price and cumulative quantity across all positions."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Portfolio Timeline", classes="chart-title")
            yield PlotextPlot(id="timeline-chart")

    def _draw(self, plot: Plot) -> None:
        plot.clear_data()
        plot.clear_figure()

        dates, avg_prices, cum_qty = self._compute_time_series()
        if not dates:
            plot.text("No portfolio data available", 0.5, 0.5)
            return

        scaled_qty = self._scale_to_price_range(cum_qty, avg_prices)

        plot.plot(dates, avg_prices, label="Avg Price", marker="dot")
        plot.plot(dates, scaled_qty, label="Qty (scaled)")
        plot.title("Portfolio Timeline")
        plot.xlabel("Date")
        plot.ylabel("Price / Scaled Qty")

        # Size hint derived from container, with sane bounds
        width_hint = getattr(self.size, "width", 80) or 80
        height_hint = getattr(self.size, "height", 16) or 16
        plot_width = max(40, min(120, int(width_hint) - 4))
        plot_height = max(10, min(24, int(height_hint) - 2))
        plot.plotsize(plot_width, plot_height)

    def _compute_time_series(self) -> tuple[list[int], list[float], list[int]]:
        from collections import defaultdict

        if not self.positions:
            return [], [], []

        by_date_qty: dict[int, int] = defaultdict(int)
        by_date_price_sum: dict[int, float] = defaultdict(float)
        by_date_price_count: dict[int, int] = defaultdict(int)

        for position in self.positions:
            for tx in position.transactions:
                day = tx.date.toordinal()
                if tx.transaction_type.value == "BUY":
                    by_date_qty[day] += tx.quantity
                elif tx.transaction_type.value == "SELL":
                    by_date_qty[day] -= tx.quantity
                by_date_price_sum[day] += tx.price
                by_date_price_count[day] += 1

        if not by_date_qty:
            return [], [], []

        dates: list[int] = sorted(by_date_qty.keys())
        cumulative_qty: list[int] = []
        running = 0
        for d in dates:
            running += by_date_qty[d]
            cumulative_qty.append(running)

        avg_prices: list[float] = [by_date_price_sum[d] / by_date_price_count[d] for d in dates]
        return dates, avg_prices, cumulative_qty

    def _scale_to_price_range(self, quantities: list[int], prices: list[float]) -> list[float]:
        if not quantities or not prices:
            return []
        q_min, q_max = min(quantities), max(quantities)
        if q_max == q_min:
            return [min(prices) for _ in quantities]
        p_min, p_max = min(prices), max(prices)
        if p_max == p_min:
            p_max = p_min + 1.0
        return [(q - q_min) / (q_max - q_min) * (p_max - p_min) + p_min for q in quantities]
