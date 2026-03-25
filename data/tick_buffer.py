"""In-memory storage for recent tick data."""

from __future__ import annotations

from collections import deque
from typing import Deque, List, Optional

from models.state import Tick


class TickBuffer:
    """Store a recent history of ticks for debugging and trading decisions."""

    def __init__(self, max_size: int = 1000) -> None:
        """Create a fixed-size deque for ticks."""
        self._ticks: Deque[Tick] = deque(maxlen=max_size)

    def add_tick(self, tick: Tick) -> None:
        """Append a new tick to the buffer."""
        self._ticks.append(tick)

    def latest(self) -> Optional[Tick]:
        """Return the most recent tick if one exists."""
        if not self._ticks:
            return None
        return self._ticks[-1]

    def to_list(self) -> List[Tick]:
        """Return all buffered ticks as a normal list."""
        return list(self._ticks)
