"""
from file template to str to DB
"""
from __future__ import annotations

import re

from bot.database.repository import PLAN_SEPARATOR

_DAY_LABELS = (
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday",
)


def parse_template(text: str) -> str:
    plans: list[str] = []
    for day in _DAY_LABELS:
        match = re.search(rf"{day}\s*\((.*?)\)", text, re.DOTALL)
        if match is None:
            raise ValueError(f"Missing or malformed section for {day}")
        plans.append(match.group(1).strip())
    return PLAN_SEPARATOR.join(plans)
