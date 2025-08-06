"""Error handling utilities for Krona UI."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from textual.widget import Widget
from textual.widgets import Static

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class UIErrorHandler:
    """Centralized error handling for UI components."""

    @staticmethod
    def handle_widget_error(widget: Widget, error: Exception, context: str = "") -> None:
        """Handle errors in widget operations with proper logging and user feedback."""
        error_msg = f"Error in {widget.__class__.__name__}: {error}"
        if context:
            error_msg = f"{context} - {error_msg}"

        logger.error(error_msg, exc_info=True)

        # Show user-friendly error message
        try:
            # Try to find a status area or create a temporary error display
            app = widget.app
            if hasattr(app, "show_error"):
                app.show_error(f"Operation failed: {error}")
        except Exception:
            # Fallback: just log the error
            logger.error("Could not display error to user", exc_info=True)

    @staticmethod
    def safe_widget_operation(widget: Widget, operation: str, func, *args, **kwargs):
        """Safely execute a widget operation with error handling."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            UIErrorHandler.handle_widget_error(widget, e, operation)
            return None

    @staticmethod
    def create_error_display(message: str) -> Static:
        """Create a user-friendly error display widget."""
        return Static(f"⚠️ {message}", classes="error-display")


class ErrorDisplayMixin:
    """Mixin for widgets that need error display capabilities."""

    def show_error(self, message: str) -> None:
        """Show an error message to the user."""
        try:
            # Try to find existing error display
            error_display = self.query_one(".error-display", Static)
            error_display.update(f"⚠️ {message}")
        except Exception:
            # Create new error display if none exists
            error_widget = UIErrorHandler.create_error_display(message)
            self.mount(error_widget)

    def clear_error(self) -> None:
        """Clear any displayed error messages."""
        error_displays = self.query(".error-display")
        for display in error_displays:
            display.remove()
