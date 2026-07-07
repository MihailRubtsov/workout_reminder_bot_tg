"""Admin-only commands.

The :class:`IsAdmin` filter checks the sender against the ``ADMIN_IDS`` list
from configuration, so these commands are ignored for everyone else. In the
original code admin commands had no such check — anyone who guessed the command
could pull the whole database.
"""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import BaseFilter, Command
from aiogram.types import Message

from bot.config import Config
from bot.database.repository import Repository

router = Router(name="admin")


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message, config: Config) -> bool:
        return message.from_user.id in config.admin_ids


@router.message(Command("stats"), IsAdmin())
async def cmd_stats(message: Message, repo: Repository) -> None:
    users = repo.get_all_users()
    active = sum(1 for user in users if user["weeks_count"] > 0)
    await message.answer(
        f"Total number of users: {len(users)}\n"
        f"With a full schedule: {active}"
    )
