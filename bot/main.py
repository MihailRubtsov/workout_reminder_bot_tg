"""
Entry point: brings everything together and launches the bot. 
This is the only place where the single bot is created and dependencies are resolved.
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import load_config
from bot.database.repository import Repository
from bot.database.schema import init_db
from bot.handlers import admin, calories, common, schedule
from bot.services.scheduler import ReminderScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()
    init_db(config.db_path)
    repo = Repository(config.db_path)

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    dp.include_router(common.router)
    dp.include_router(schedule.router)
    dp.include_router(calories.router)
    dp.include_router(admin.router)

    scheduler = ReminderScheduler(bot, repo, config)
    scheduler_task = asyncio.create_task(scheduler.run(), name="scheduler")

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot, repo=repo, config=config)
    finally:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
