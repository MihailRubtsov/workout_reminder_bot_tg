"""
All of the project's SQL is here. 
The rest of the code interacts with the database only through the methods of this class.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional


DAYS: tuple[str, ...] = (
    "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday",
)

# Separator between the seven daily plans stored inside a single plan cell.
PLAN_SEPARATOR = "@#@"


class Repository:
    """all methods to work with DB"""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self._db_path)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def user_exists(self, telegram_id: int) -> bool:
        with self._connect() as con:
            row = con.execute(
                "SELECT 1 FROM users WHERE telegram_id = ?", (telegram_id,)
            ).fetchone()
        return row is not None

    def create_user(self, telegram_id: int) -> None:
        with self._connect() as con:
            con.execute(
                "INSERT OR IGNORE INTO users (telegram_id) VALUES (?)",
                (telegram_id,),
            )

    def get_weeks_count(self, telegram_id: int) -> int:
        with self._connect() as con:
            row = con.execute(
                "SELECT weeks_count FROM users WHERE telegram_id = ?",
                (telegram_id,),
            ).fetchone()
        return row["weeks_count"] if row else 0

    def get_all_users(self) -> list[sqlite3.Row]:
        with self._connect() as con:
            return con.execute("SELECT * FROM users").fetchall()


    def set_all_times(self, telegram_id: int, times: dict[str, str]) -> None:
        """
        set time to all days in week
        """
        assignments = ", ".join(f"{day}_time = ?" for day in DAYS)
        values = [times[day] for day in DAYS]
        values.append(telegram_id)
        with self._connect() as con:
            con.execute(
                f"UPDATE users SET {assignments} WHERE telegram_id = ?",
                values,
            )

    def set_day_time(self, telegram_id: int, day: str, time: str) -> None:
        """Set the send-time for a single day."""
        day = day.lower()
        if day not in DAYS:
            raise ValueError(f"Unknown day: {day!r}")
        with self._connect() as con:
            con.execute(
                f"UPDATE users SET {day}_time = ? WHERE telegram_id = ?",
                (time, telegram_id),
            )

    def add_week(self, telegram_id: int, plan: str, max_weeks: int) -> bool:
        """Append a new training week. Returns False if the limit is hit."""
        current = self.get_weeks_count(telegram_id)
        if current >= max_weeks:
            return False
        with self._connect() as con:
            con.execute(
                "INSERT INTO training_weeks (telegram_id, week_number, plan) "
                "VALUES (?, ?, ?)",
                (telegram_id, current + 1, plan),
            )
            con.execute(
                "UPDATE users SET weeks_count = ? WHERE telegram_id = ?",
                (current + 1, telegram_id),
            )
        return True

    def delete_last_week(self, telegram_id: int) -> None:
        weeks = self.get_weeks_count(telegram_id)
        if weeks <= 0:
            return
        with self._connect() as con:
            con.execute(
                "DELETE FROM training_weeks "
                "WHERE telegram_id = ? AND week_number = ?",
                (telegram_id, weeks),
            )
            con.execute(
                "UPDATE users SET weeks_count = ? WHERE telegram_id = ?",
                (weeks - 1, telegram_id),
            )

    def update_week_plan(
        self, telegram_id: int, week_number: int, plan: str
    ) -> None:
        with self._connect() as con:
            con.execute(
                "UPDATE training_weeks SET plan = ? "
                "WHERE telegram_id = ? AND week_number = ?",
                (plan, telegram_id, week_number),
            )

    def get_week_plan(
        self, telegram_id: int, week_number: int
    ) -> Optional[str]:
        with self._connect() as con:
            row = con.execute(
                "SELECT plan FROM training_weeks "
                "WHERE telegram_id = ? AND week_number = ?",
                (telegram_id, week_number),
            ).fetchone()
        return row["plan"] if row else None

    def get_all_weeks(self, telegram_id: int) -> list[sqlite3.Row]:
        with self._connect() as con:
            return con.execute(
                "SELECT week_number, plan FROM training_weeks "
                "WHERE telegram_id = ? ORDER BY week_number",
                (telegram_id,),
            ).fetchall()

    def get_day_plan(
        self, telegram_id: int, week_number: int, day_index: int
    ) -> Optional[str]:
        """Return a single day's plan """
        plan = self.get_week_plan(telegram_id, week_number)
        if plan is None:
            return None
        parts = plan.split(PLAN_SEPARATOR)
        if 0 <= day_index < len(parts):
            return parts[day_index]
        return None


    def advance_all_weeks(self) -> None:
        """Move every user to their next week, wrapping back to week 1."""
        with self._connect() as con:
            con.execute(
                "UPDATE users SET current_week = CASE "
                "WHEN current_week >= weeks_count THEN 1 "
                "ELSE current_week + 1 END "
                "WHERE weeks_count > 0"
            )

    def reset_all_reminders(self) -> None:
        """Mark every user as 'reminder not yet sent today'."""
        with self._connect() as con:
            con.execute("UPDATE users SET reminder_pending = 1")

    def mark_reminder_sent(self, telegram_id: int) -> None:
        with self._connect() as con:
            con.execute(
                "UPDATE users SET reminder_pending = 0 WHERE telegram_id = ?",
                (telegram_id,),
            )
