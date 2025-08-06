"""Chart caching utilities for improved performance."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from krona.models.position import Position


class ChartCache:
    """Cache for chart data to avoid unnecessary regeneration."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[str, float]] = {}  # key -> (chart_data, timestamp)
        self._cache_ttl = 300  # 5 minutes TTL

    def _generate_cache_key(self, chart_type: str, positions: list[Position], **kwargs) -> str:
        """Generate a cache key based on chart type and position data."""
        # Create a hash of the relevant position data
        position_data = []
        for pos in positions:
            position_data.append(
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "cost_basis": pos.cost_basis,
                    "dividends": pos.dividends,
                    "is_closed": pos.is_closed,
                    "realized_profit": pos.realized_profit,
                }
            )

        # Add kwargs to the hash
        data_to_hash = {"chart_type": chart_type, "positions": position_data, "kwargs": kwargs}

        data_str = json.dumps(data_to_hash, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode(), usedforsecurity=False).hexdigest()

    def get(self, chart_type: str, positions: list[Position], **kwargs) -> str | None:
        """Get cached chart data if available and fresh."""
        import time

        cache_key = self._generate_cache_key(chart_type, positions, **kwargs)
        current_time = time.time()

        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if current_time - timestamp < self._cache_ttl:
                return cached_data

        return None

    def set(self, chart_type: str, positions: list[Position], chart_data: str, **kwargs) -> None:
        """Cache chart data."""
        import time

        cache_key = self._generate_cache_key(chart_type, positions, **kwargs)
        self._cache[cache_key] = (chart_data, time.time())

        # Clean up old entries if cache gets too large
        if len(self._cache) > 100:
            self._cleanup_old_entries()

    def _cleanup_old_entries(self) -> None:
        """Remove old cache entries."""
        import time

        current_time = time.time()
        keys_to_remove = [
            key for key, (_, timestamp) in self._cache.items() if current_time - timestamp > self._cache_ttl
        ]

        for key in keys_to_remove:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()


# Global chart cache instance
chart_cache = ChartCache()
