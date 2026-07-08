"""
converts saved plans back into text
"""
from __future__ import annotations

import sqlite3

from bot.database.repository import PLAN_SEPARATOR

_DAY_LABELS = (
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday",
)


def format_week(plan: str) -> str:
    """Render one week's plan"""
    days = plan.split(PLAN_SEPARATOR)
    lines = [f"{label}: {days[i] if i < len(days) else ''}"
             for i, label in enumerate(_DAY_LABELS)]
    return "\n\n".join(lines)


def format_all_weeks(weeks: list[sqlite3.Row]) -> str:
    """Render every week, prefixed with the total count."""
    header = f"Number of weeks: {len(weeks)}."
    blocks = [f"№{row['week_number']}\n\n{format_week(row['plan'])}"
              for row in weeks]
    return header + "\n\n" + "\n\n".join(blocks)
