"""
The largest processor: everything related to the schedule—adding, viewing, editing, and deleting weeks and times. 
It operates through FSM dialogs and calls the Repository.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime

import pytz
from aiogram import Bot

from bot.config import Config
from bot.database.repository import DAYS, Repository

logger = logging.getLogger(__name__)

_TICK_SECONDS = 30


class ReminderScheduler:
    def __init__(self, bot: Bot, repo: Repository, config: Config) -> None:
        self._bot = bot
        self._repo = repo
        self._config = config
        self._tz = pytz.timezone(config.timezone)
        self._last_reset_day: date | None = None

    async def run(self) -> None:
        """Run the scheduler until the task is cancelled."""
        while True:
            try:
                await self._tick()
            except asyncio.CancelledError:
                logger.info("Scheduler stopped")
                raise
            except Exception:  # noqa: BLE001 - log and keep the loop alive
                logger.exception("Error inside scheduler tick")
            await asyncio.sleep(_TICK_SECONDS)

    async def _tick(self) -> None:
        now = datetime.now(self._tz)

        # Midnight housekeeping, guaranteed to run once per calendar day.
        if now.hour == 0 and now.minute == 0:
            await self._daily_reset(now)
            return

        await self._send_due_reminders(now)

    async def _daily_reset(self, now: datetime) -> None:
        if self._last_reset_day == now.date():
            return
        self._last_reset_day = now.date()

        # Monday (weekday() == 0) starts a new training week for everyone.
        if now.weekday() == 0:
            self._repo.advance_all_weeks()
            await self._notify_admins("The Start of a New Week")
        else:
            await self._notify_admins("The Start of a New Day")

        self._repo.reset_all_reminders()

    async def _send_due_reminders(self, now: datetime) -> None:
        day_index = now.weekday()          # 0 = Monday
        day_column = f"{DAYS[day_index]}_time"

        for user in self._repo.get_all_users():
            if not user["reminder_pending"] or user["weeks_count"] == 0:
                continue
            if not self._is_due(user[day_column], now):
                continue

            plan = self._repo.get_day_plan(
                user["telegram_id"], user["current_week"], day_index
            )
            if plan is None:
                continue

            await self._send_plan(user, day_index, plan)

    @staticmethod
    def _is_due(scheduled: str, now: datetime) -> bool:
        """True if ``now`` is at or after the ``"HH:MM"`` scheduled time."""
        try:
            hour, minute = (int(part) for part in scheduled.split(":"))
        except (ValueError, AttributeError):
            return False
        return (now.hour, now.minute) >= (hour, minute)

    async def _send_plan(self, user, day_index: int, plan: str) -> None:
        weekday_name = DAYS[day_index].capitalize()
        text = (
            "Here is your workout plan for today\n\n"
            f"Week Number {user['current_week']}\n\n"
            f"Day: {weekday_name}\n\n{plan}"
        )
        try:
            await self._bot.send_message(user["telegram_id"], text)
            self._repo.mark_reminder_sent(user["telegram_id"])
        except Exception:  # noqa: BLE001 - one bad chat must not stop the rest
            logger.exception(
                "Failed to send reminder to %s", user["telegram_id"]
            )

    async def _notify_admins(self, text: str) -> None:
        for admin_id in self._config.admin_ids:
            try:
                await self._bot.send_message(admin_id, text)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to notify admin %s", admin_id)
