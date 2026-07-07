"""Reply keyboards shown to the user.

Every builder returns a fresh :class:`ReplyKeyboardMarkup` so keyboards are
never accidentally shared or mutated between users.
"""
from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

WEEKDAYS = (
    ("Monday", "Tuesday", "Wednesday"),
    ("Thursday", "Friday", "Saturday"),
    ("Sunday",),
)


def _markup(rows: list[list[str]]) -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=text) for text in row] for row in rows]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def main_menu() -> ReplyKeyboardMarkup:
    return _markup([
        ["/start", "/help"],
        ["/manage_schedule"],
        ["/view_schedule"],
        ["/calories"],
    ])


def manage_menu() -> ReplyKeyboardMarkup:
    return _markup([
        ["/add_week", "/upload_week", "/set_times"],
        ["/change_time", "/change_week", "/delete_week"],
        ["/back"],
    ])


def view_menu() -> ReplyKeyboardMarkup:
    return _markup([
        ["/all_weeks", "/view_week"],
        ["/back"],
    ])


def weekday_picker() -> ReplyKeyboardMarkup:
    return _markup([list(row) for row in WEEKDAYS])
