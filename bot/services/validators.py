"""Small input validators shared across handlers."""
from __future__ import annotations

WEEKDAY_NAMES = (
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday",
)


def is_valid_time(value: str) -> bool:
    """Validate an ``"HH:MM"`` string (00:00 .. 23:59)."""
    parts = value.split(":")
    if len(parts) != 2:
        return False
    try:
        hours = int(parts[0])
        minutes = int(parts[1])
    except ValueError:
        return False
    return 0 <= hours <= 23 and 0 <= minutes <= 59


def is_valid_weekday(value: str) -> bool:
    return value in WEEKDAY_NAMES
