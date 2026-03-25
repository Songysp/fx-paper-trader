"""CSV loader for historical OHLC bar data."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import List

from models.state import Bar


def load_bars_from_csv(csv_path: str) -> List[Bar]:
    """Load OHLC bars from a CSV file.

    Expected columns:
    - timestamp
    - open
    - high
    - low
    - close
    """
    rows: List[Bar] = []
    path = Path(csv_path)

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(
                Bar(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                )
            )

    return rows
