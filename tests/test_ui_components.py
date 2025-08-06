"""Tests for Krona UI components."""

from unittest.mock import Mock

from krona.models.position import Position
from krona.ui.state.app_state import AppState, StateChanged
from krona.ui.utils.chart_cache import ChartCache
from krona.ui.utils.error_handler import ErrorDisplayMixin, UIErrorHandler
from krona.ui.views.dashboard_stats import DashboardStats


class TestDashboardStats:
    """Test DashboardStats widget."""

    def test_compose_with_empty_positions(self):
        """Test dashboard stats with no positions."""
        stats = DashboardStats([])

        # Test that the widget can be created
        assert stats is not None
        assert stats.positions == []

        # Note: We can't test compose() without a proper Textual app context
        # The actual widget testing would require a running Textual app

    def test_compose_with_positions(self):
        """Test dashboard stats with positions."""
        # Create mock positions
        positions = [
            Position(
                symbol="AAPL",
                quantity=10,
                price=150.0,
                currency="USD",
                ISIN="US0378331005",
                dividends=0.0,
                fees=0.0,
                transactions=[],
            ),
            Position(
                symbol="MSFT",
                quantity=0,  # Closed position
                price=300.0,
                currency="USD",
                ISIN="US5949181045",
                dividends=0.0,
                fees=0.0,
                transactions=[],
            ),
        ]

        stats = DashboardStats(positions)

        # Test that the widget can be created
        assert stats is not None
        assert len(stats.positions) == 2

        # Note: We can't test compose() without a proper Textual app context
        # The actual widget testing would require a running Textual app

    def test_update_stats(self):
        """Test updating stats with new positions."""
        stats = DashboardStats([])

        # Create mock positions
        positions = [
            Position(
                symbol="AAPL",
                quantity=10,
                price=150.0,
                currency="USD",
                ISIN="US0378331005",
                dividends=0.0,
                fees=0.0,
                transactions=[],
            )
        ]

        # Update stats
        stats.update_stats(positions)

        # Note: We can't test widget querying without a proper Textual app context
        # The actual widget testing would require a running Textual app


class TestErrorHandler:
    """Test error handling utilities."""

    def test_handle_widget_error(self):
        """Test error handling for widgets."""
        mock_widget = Mock()
        mock_widget.app = Mock()
        mock_widget.app.show_error = Mock()

        error = ValueError("Test error")
        UIErrorHandler.handle_widget_error(mock_widget, error, "test operation")

        # Should call show_error on the app
        mock_widget.app.show_error.assert_called_once()

    def test_safe_widget_operation_success(self):
        """Test safe widget operation with success."""
        mock_widget = Mock()

        def test_func(a, b):
            return a + b

        result = UIErrorHandler.safe_widget_operation(mock_widget, "test", test_func, 2, 3)
        assert result == 5

    def test_safe_widget_operation_failure(self):
        """Test safe widget operation with failure."""
        mock_widget = Mock()
        mock_widget.app = Mock()
        mock_widget.app.show_error = Mock()

        def test_func():
            raise ValueError("Test error")

        result = UIErrorHandler.safe_widget_operation(mock_widget, "test", test_func)
        assert result is None
        mock_widget.app.show_error.assert_called_once()


class TestErrorDisplayMixin:
    """Test error display mixin."""

    def test_show_error(self):
        """Test showing error messages."""

        # Create a mock widget with the mixin
        class TestWidget(ErrorDisplayMixin):
            def __init__(self):
                self.children = []

            def mount(self, widget):
                self.children.append(widget)

            def query_one(self, selector, widget_type):
                if selector == ".error-display":
                    return self.children[0] if self.children else None
                raise Exception("Not found")

        widget = TestWidget()
        widget.show_error("Test error message")

        # Should have added an error display widget
        assert len(widget.children) == 1

    def test_clear_error(self):
        """Test clearing error messages."""

        class TestWidget(ErrorDisplayMixin):
            def __init__(self):
                self.children = []
                self.removed_count = 0

            def query(self, selector):
                return self.children if selector == ".error-display" else []

            def remove(self):
                self.removed_count += 1

        widget = TestWidget()
        mock_display = Mock()
        mock_display.remove = widget.remove
        widget.children = [mock_display]
        widget.clear_error()

        # The clear_error method should have called remove() on the display
        assert widget.removed_count == 1


class TestChartCache:
    """Test chart caching functionality."""

    def test_cache_key_generation(self):
        """Test cache key generation."""
        cache = ChartCache()

        # Create mock positions
        positions = [
            Position(
                symbol="AAPL",
                quantity=10,
                price=150.0,
                currency="USD",
                ISIN="US0378331005",
                dividends=0.0,
                fees=0.0,
                transactions=[],
            )
        ]

        key1 = cache._generate_cache_key("test_chart", positions, param1="value1")
        key2 = cache._generate_cache_key("test_chart", positions, param1="value1")
        key3 = cache._generate_cache_key("test_chart", positions, param1="value2")

        # Same parameters should generate same key
        assert key1 == key2

        # Different parameters should generate different key
        assert key1 != key3

    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        cache = ChartCache()

        positions = [
            Position(
                symbol="AAPL",
                quantity=10,
                price=150.0,
                currency="USD",
                ISIN="US0378331005",
                dividends=0.0,
                fees=0.0,
                transactions=[],
            )
        ]

        chart_data = "test chart data"

        # Initially should be None
        assert cache.get("test_chart", positions) is None

        # Set cache
        cache.set("test_chart", positions, chart_data)

        # Should get cached data
        assert cache.get("test_chart", positions) == chart_data

    def test_cache_clear(self):
        """Test clearing cache."""
        cache = ChartCache()

        positions = [
            Position(
                symbol="AAPL",
                quantity=10,
                price=150.0,
                currency="USD",
                ISIN="US0378331005",
                dividends=0.0,
                fees=0.0,
                transactions=[],
            )
        ]

        # Set some data
        cache.set("test_chart", positions, "test data")
        assert cache.get("test_chart", positions) is not None

        # Clear cache
        cache.clear()
        assert cache.get("test_chart", positions) is None


class TestAppState:
    """Test application state management."""

    def test_initial_state(self):
        """Test initial state values."""
        mock_app = Mock()
        state = AppState(mock_app)

        assert len(state.positions) == 0
        assert len(state.suggestions) == 0
        assert state.mapping_plan is None

    def test_positions_setter(self):
        """Test setting positions."""
        mock_app = Mock()
        state = AppState(mock_app)

        positions = [
            Position(
                symbol="AAPL",
                quantity=10,
                price=150.0,
                currency="USD",
                ISIN="US0378331005",
                dividends=0.0,
                fees=0.0,
                transactions=[],
            )
        ]

        # Add listener
        listener_called = False

        def test_listener(message):
            nonlocal listener_called
            listener_called = True
            assert message.state_type == "positions"
            assert message.data == positions

        state.add_listener(test_listener)

        # Set positions
        state.positions = positions

        # Should notify listener
        assert listener_called
        assert len(state.positions) == 1

    def test_update_position(self):
        """Test updating a specific position."""
        mock_app = Mock()
        state = AppState(mock_app)

        position1 = Position(
            symbol="AAPL",
            quantity=10,
            price=150.0,
            currency="USD",
            ISIN="US0378331005",
            dividends=0.0,
            fees=0.0,
            transactions=[],
        )

        position2 = Position(
            symbol="MSFT",
            quantity=5,
            price=300.0,
            currency="USD",
            ISIN="US5949181045",
            dividends=0.0,
            fees=0.0,
            transactions=[],
        )

        # Add initial positions
        state.positions = [position1, position2]

        # Update AAPL position
        updated_position = Position(
            symbol="AAPL",
            quantity=15,  # Changed quantity
            price=150.0,
            currency="USD",
            ISIN="US0378331005",
            dividends=0.0,
            fees=0.0,
            transactions=[],
        )

        state.update_position(updated_position)

        # Should have updated the position
        assert len(state.positions) == 2
        aapl_position = next(p for p in state.positions if p.symbol == "AAPL")
        assert aapl_position.quantity == 15

    def test_clear_state(self):
        """Test clearing all state."""
        mock_app = Mock()
        state = AppState(mock_app)

        # Add some data
        state.positions = [Mock()]
        state.suggestions = [Mock()]

        # Clear state
        state.clear()

        # Should be empty
        assert len(state.positions) == 0
        assert len(state.suggestions) == 0
        assert state.mapping_plan is None


class TestStateChanged:
    """Test state change messages."""

    def test_state_changed_message(self):
        """Test StateChanged message creation."""
        data = {"test": "data"}
        message = StateChanged("test_type", data)

        assert message.state_type == "test_type"
        assert message.data == data
