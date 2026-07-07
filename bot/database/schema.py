"""
Describes the database schema: SQL statements to create the `users` and `training_weeks` tables. 
reates the tables once at startup.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id      INTEGER NOT NULL UNIQUE,
    weeks_count      INTEGER NOT NULL DEFAULT 0,
    current_week     INTEGER NOT NULL DEFAULT 1,
    monday_time      TEXT NOT NULL DEFAULT '10:00',
    tuesday_time     TEXT NOT NULL DEFAULT '10:00',
    wednesday_time   TEXT NOT NULL DEFAULT '10:00',
    thursday_time    TEXT NOT NULL DEFAULT '10:00',
    friday_time      TEXT NOT NULL DEFAULT '10:00',
    saturday_time    TEXT NOT NULL DEFAULT '10:00',
    sunday_time      TEXT NOT NULL DEFAULT '10:00',
    reminder_pending INTEGER NOT NULL DEFAULT 1
);
"""

CREATE_TRAINING_WEEKS = """
CREATE TABLE IF NOT EXISTS training_weeks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    plan        TEXT NOT NULL,
    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
);
"""


def init_db(db_path: Path) -> None:
    """Create tables if they do not exist yet."""
    with sqlite3.connect(db_path) as con:
        con.execute(CREATE_USERS)
        con.execute(CREATE_TRAINING_WEEKS)
        con.commit()
