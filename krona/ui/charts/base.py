from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, ClassVar

from textual import on
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Switch
from textual_plotext import Plot, PlotextPlot

if TYPE_CHECKING:
    from krona.models.position import Position


class Chart(Widget):
    """Abstract base class for Krona charts.

    Provides a standard layout (title + body), life-cycle wiring, and update helpers.
    Subclasses implement `_draw()` to mutate the Plot object.
    """

    # Subclasses should override these
    chart_id: ClassVar[str] = "chart"
    title_text: ClassVar[str] = "Chart Title"

    def __init__(self, positions: list[Position] | None = None) -> None:
        super().__init__()
        self.positions: list[Position] = positions or []

    # Layout
    @abstractmethod
    def compose(self) -> ComposeResult:
        raise NotImplementedError

    # Lifecycle
    def on_mount(self) -> None:
        self.call_after_refresh(self.refresh_chart)

    # Public API
    def refresh_chart(self) -> None:
        """Render and update the chart body using current positions and size."""
        plot: Plot = self.query_one(PlotextPlot).plt
        self._draw(plot)

    def update_positions(self, positions: list[Position]) -> None:
        self.positions = positions
        self.refresh_chart()

    def set_positions(self, positions: list[Position]) -> None:
        self.update_positions(positions)

    # Default interaction
    @on(Switch.Changed)
    def handle_switch_change(self) -> None:
        self.refresh_chart()

    @abstractmethod
    def _draw(self, plot: Plot) -> None:
        """Draw the chart."""
        raise NotImplementedError
