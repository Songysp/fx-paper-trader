"""Time-related helper functions."""

from __future__ import annotations

from datetime import datetime


def floor_to_minute(value: datetime) -> datetime:
    """Return the same datetime rounded down to the minute."""
    return value.replace(second=0, microsecond=0)
