"""Parse an uploaded training-plan template into a storable string.

The template a user fills in looks like this::

    Training schedule template, put your training in brackets.
    Monday(squats 5x5)
    Tuesday(rest)
    ...
    Sunday(long run)

We extract the text inside each day's brackets and join the seven days with
:data:`PLAN_SEPARATOR`. A single regex replaces the original hand-written
string slicing, which was brittle and hard to follow.
"""
from __future__ import annotations

import re

from bot.database.repository import PLAN_SEPARATOR

_DAY_LABELS = (
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday",
)


def parse_template(text: str) -> str:
    """Return the seven daily plans joined by :data:`PLAN_SEPARATOR`.

    Raises :class:`ValueError` if any day's section is missing or malformed.
    """
    plans: list[str] = []
    for day in _DAY_LABELS:
        match = re.search(rf"{day}\s*\((.*?)\)", text, re.DOTALL)
        if match is None:
            raise ValueError(f"Missing or malformed section for {day}")
        plans.append(match.group(1).strip())
    return PLAN_SEPARATOR.join(plans)
