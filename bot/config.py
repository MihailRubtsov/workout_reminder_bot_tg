"""
Loads project settings from the environment file (.env) and returns them as a single object. 
This is the only place where the token, admins, time zone, and database path are read.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root (two levels up from this file: bot/config.py -> project root).
BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    """Immutable container for all runtime settings."""

    bot_token: str
    admin_ids: tuple[int, ...]
    timezone: str
    db_path: Path
    template_path: Path
    max_weeks: int = 5


def _parse_admin_ids(raw: str) -> tuple[int, ...]:
    """Turn a comma-separated string like ``"111, 222"`` into ``(111, 222)``."""
    if not raw.strip():
        return ()
    return tuple(int(part) for part in raw.replace(" ", "").split(",") if part)


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN is not set. Copy .env.example to .env and fill it in."
        )
    return Config(
        bot_token=token,
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        timezone=os.getenv("TIMEZONE", "Europe/Vienna"),
        db_path=BASE_DIR / os.getenv("DB_PATH", "workout_bot.db"),
        template_path=BASE_DIR / "data" / "template.txt",
    )
