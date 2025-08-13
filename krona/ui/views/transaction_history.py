"""Modal overlay to display transaction drill-down for a position."""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotext as plt
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Static

if TYPE_CHECKING:
    from krona.models.position import Position
    from krona.models.transaction import Transaction


class TransactionModal(ModalScreen[None]):
    """A simple modal overlay showing transactions and quick stats for a position."""

    def __init__(self, position: Position) -> None:
        super().__init__()
        self.position = position

    def compose(self) -> ComposeResult:
        with Vertical(classes="tx-modal-outer"), Vertical(classes="tx-modal"):
            with Horizontal(classes="tx-modal-header"):
                yield Static(f"📜 Transactions · {self.position.symbol}", classes="tx-title")
                yield Button("✖ Close", id="tx-close", variant="error")

            # Chart at the top spanning modal width
            chart = Static(id="tx-chart", markup=False)
            yield chart

            # Below: table (left) and stats + mappings (right)
            with Horizontal(classes="tx-modal-content"):
                # Left: Transactions table
                table = DataTable(id="tx-table")
                table.add_columns("Date", "Type", "Qty", "Price", "Fees", "Amount")
                self._populate_transactions_table(table, self.position.transactions)
                yield table

                # Right: Quick stats and mappings
                with Vertical(classes="tx-side-panel"):
                    yield Static(self._render_quick_stats(), id="tx-stats", markup=False)
                    yield Static(self._render_mappings(), id="tx-mappings", markup=False)

            # Render chart after first layout to ensure proper sizing
            self.call_after_refresh(self._update_chart)

    def _populate_transactions_table(self, table: DataTable, txs: list[Transaction]) -> None:
        for i, t in enumerate(txs):
            table.add_row(
                str(t.date),
                t.transaction_type.value,
                f"{t.quantity}",
                f"{t.price:.2f} {t.currency}",
                f"{t.fees:.2f}",
                f"{t.total_amount:.2f} {t.currency}",
                key=str(i),
            )

    def _render_quick_stats(self) -> str:
        total_buys = sum(t.total_amount for t in self.position.transactions if t.transaction_type.value == "BUY")
        total_sells = sum(t.total_amount for t in self.position.transactions if t.transaction_type.value == "SELL")
        dividends = self.position.dividends
        fees = self.position.fees
        realized = self.position.realized_profit

        lines = [
            f"Symbol: {self.position.symbol}",
            f"ISIN: {self.position.ISIN}",
            f"Quantity: {self.position.quantity}",
            f"Cost Basis: {self.position.cost_basis:.2f} {self.position.currency}",
            f"Dividends: {dividends:.2f} {self.position.currency}",
            f"Fees: {fees:.2f} {self.position.currency}",
            f"Total Buys: {total_buys:.2f} {self.position.currency}",
            f"Total Sells: {total_sells:.2f} {self.position.currency}",
            f"Realized P&L: {realized:.2f} {self.position.currency}" if realized is not None else "Realized P&L: N/A",
        ]
        return "\n".join(lines)

    def _render_mappings(self) -> str:
        """Render mapping info: all symbols and ISINs that map to this position's canonical symbol."""
        try:
            # Attempt to fetch mapping plan from app if available
            from krona.ui.tui import KronaTUI  # local import to avoid cycles

            app = self.app
            symbol = self.position.symbol
            isins: set[str] = {self.position.ISIN}
            synonyms: set[str] = {symbol}

            if isinstance(app, KronaTUI) and app.plan is not None:
                plan = app.plan
                # Collect synonyms (alternative symbols) that map to the canonical symbol
                for alt_symbol, canonical in plan.symbol_mappings.items():
                    if canonical == symbol:
                        synonyms.add(alt_symbol)
                # Collect ISINs that map to the canonical symbol
                for isin, canonical in plan.isin_mappings.items():
                    if canonical == symbol:
                        isins.add(isin)

            # Build readable block
            syn_line = "Symbols: " + ", ".join(sorted(synonyms))
            isin_line = "ISINs: " + ", ".join(sorted(isins))
            return "\n".join(["", "Mappings", syn_line, isin_line])
        except Exception:
            return "\nMappings\nSymbols: -\nISINs: -"

    def _render_timeline_chart(self, txs: list[Transaction], width: int = 48, height: int = 14) -> str:
        plt.clear_data()
        plt.clear_figure()

        if not txs:
            plt.text("No transactions", 0.5, 0.5)
            return plt.build()

        # Prepare a simple timeline using ordinal dates for x and string ticks
        txs_sorted = sorted(txs, key=lambda t: t.date)
        x = [t.date.toordinal() for t in txs_sorted]
        x_labels = [t.date.isoformat() for t in txs_sorted]

        prices = [t.price for t in txs_sorted]

        # Cumulative quantity over time
        cumulative_quantity: list[int] = []
        qty = 0
        for t in txs_sorted:
            if t.transaction_type.value == "BUY":
                qty += t.quantity
            elif t.transaction_type.value == "SELL":
                qty -= t.quantity
            cumulative_quantity.append(qty)

        # Plot price line and quantity (scaled) as a second line
        plt.plot(x, prices, label="Price", marker="dot")

        # Scale quantity to price range (roughly) for visualization
        if max(cumulative_quantity) != min(cumulative_quantity):
            q_min, q_max = min(cumulative_quantity), max(cumulative_quantity)
            p_min, p_max = min(prices), max(prices)
            scaled_qty = [(q - q_min) / (q_max - q_min) * (p_max - p_min) + p_min for q in cumulative_quantity]
            plt.plot(x, scaled_qty, label="Qty (scaled)")

        # Reduce x tick density and avoid rotation calls not supported by plotext
        if len(x) > 10:
            step = max(1, len(x) // 10)
            x_ticks = x[::step]
            x_tick_labels = x_labels[::step]
        else:
            x_ticks = x
            x_tick_labels = x_labels
        plt.xticks(x_ticks, x_tick_labels)
        plt.title("Timeline: Price and Quantity")
        plt.xlabel("Date")
        plt.ylabel("Price / Scaled Qty")
        plt.plotsize(max(20, width), max(8, height))
        return plt.build()

    def _update_chart(self) -> None:
        """Update chart widget after initial layout to ensure it renders."""
        chart = self.query_one("#tx-chart", Static)
        # Determine available size inside the widget, subtract a small padding
        width = getattr(chart.size, "width", 48)
        height = getattr(chart.size, "height", 14)
        chart_str = self._render_timeline_chart(self.position.transactions, width=width - 2, height=height - 2)
        # Interpret ANSI produced by plotext so color codes don't render as plain text
        chart.update(Text.from_ansi(chart_str))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "tx-close":
            self.dismiss()
