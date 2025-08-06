"""Dashboard statistics widget for portfolio overview."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static

if TYPE_CHECKING:
    from krona.models.position import Position


class DashboardStats(Widget):
    """Dashboard statistics widget inspired by Dolphie."""

    def __init__(self, positions: list[Position] | None = None) -> None:
        super().__init__()
        self.positions = positions or []

    def compose(self) -> ComposeResult:
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
