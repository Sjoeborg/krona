"""Centralized state management for Krona UI."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from textual.app import App
from textual.message import Message

if TYPE_CHECKING:
    from krona.models.mapping import MappingPlan
    from krona.models.position import Position
    from krona.models.suggestion import Suggestion


class StateChanged(Message):
    """Message sent when app state changes."""

    def __init__(self, state_type: str, data: Any) -> None:
        super().__init__()
        self.state_type = state_type
        self.data = data


class AppState:
    """Centralized state management for the Krona application."""

    def __init__(self, app: App) -> None:
        self.app = app
        self._positions: list[Position] = []
        self._suggestions: list[Suggestion] = []
        self._mapping_plan: MappingPlan | None = None
        self._listeners: list[Callable[[StateChanged], None]] = []

    @property
    def positions(self) -> list[Position]:
        """Get current positions."""
        return self._positions.copy()

    @positions.setter
    def positions(self, positions: list[Position]) -> None:
        """Set positions and notify listeners."""
        self._positions = positions.copy()
        self._notify_listeners("positions", positions)

    @property
    def suggestions(self) -> list[Suggestion]:
        """Get current suggestions."""
        return self._suggestions.copy()

    @suggestions.setter
    def suggestions(self, suggestions: list[Suggestion]) -> None:
        """Set suggestions and notify listeners."""
        self._suggestions = suggestions.copy()
        self._notify_listeners("suggestions", suggestions)

    @property
    def mapping_plan(self) -> MappingPlan | None:
        """Get current mapping plan."""
        return self._mapping_plan

    @mapping_plan.setter
    def mapping_plan(self, plan: MappingPlan | None) -> None:
        """Set mapping plan and notify listeners."""
        self._mapping_plan = plan
        self._notify_listeners("mapping_plan", plan)

    def add_listener(self, listener: Callable[[StateChanged], None]) -> None:
        """Add a state change listener."""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[StateChanged], None]) -> None:
        """Remove a state change listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self, state_type: str, data: Any) -> None:
        """Notify all listeners of state changes."""
        message = StateChanged(state_type, data)
        for listener in self._listeners:
            try:
                listener(message)
            except Exception as e:
                # Log error but don't break other listeners
                self.app.log.error(f"Error in state listener: {e}")

    def update_position(self, position: Position) -> None:
        """Update a specific position in the list."""
        for i, existing_pos in enumerate(self._positions):
            if existing_pos.symbol == position.symbol:
                self._positions[i] = position
                self._notify_listeners("positions", self._positions)
                return

        # Position not found, add it
        self._positions.append(position)
        self._notify_listeners("positions", self._positions)

    def update_suggestion(self, suggestion: Suggestion) -> None:
        """Update a specific suggestion in the list."""
        for i, existing_sugg in enumerate(self._suggestions):
            if (
                existing_sugg.source_symbol == suggestion.source_symbol
                and existing_sugg.target_symbol == suggestion.target_symbol
            ):
                self._suggestions[i] = suggestion
                self._notify_listeners("suggestions", self._suggestions)
                return

        # Suggestion not found, add it
        self._suggestions.append(suggestion)
        self._notify_listeners("suggestions", self._suggestions)

    def clear(self) -> None:
        """Clear all state."""
        self._positions.clear()
        self._suggestions.clear()
        self._mapping_plan = None
        self._notify_listeners("clear", None)
