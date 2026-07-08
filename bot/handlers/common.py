"""Basic commands"""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.database.repository import Repository
from bot.keyboards import reply

router = Router(name="common")

HELP_TEXT = """Main bot commands:

/manage_schedule — manage the schedule:
  /add_week — add a training week
  /upload_week — add a week using a template file
  /set_times — set reminder times for each day
  /change_time — change the time for a single day
  /change_week — replace the weekly schedule (with a file)
  /delete_week — delete the last week

/view_schedule — view the schedule:
  /all_weeks — show the entire schedule
  /view_week — show a specific week

/calories — calculate daily calorie intake
/template — get a template file to fill in workouts"""


@router.message(Command("start"))
async def cmd_start(message: Message, repo: Repository) -> None:
    if not repo.user_exists(message.from_user.id):
        repo.create_user(message.from_user.id)
    await message.answer(
        "Hi! I'm a workout reminder bot.\n"
        "Every day, I'll send you a plan for the day.\n"
        "First, fill out the schedule—click /help to learn about the commands.",
        reply_markup=reply.main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=reply.main_menu())


@router.message(Command("manage_schedule"))
async def cmd_manage(message: Message) -> None:
    await message.answer(
        "Schedule Management", reply_markup=reply.manage_menu()
    )


@router.message(Command("view_schedule"))
async def cmd_view(message: Message) -> None:
    await message.answer(
        "View Schedule", reply_markup=reply.view_menu()
    )


@router.message(Command("back"))
async def cmd_back(message: Message) -> None:
    await message.answer("Main Menu", reply_markup=reply.main_menu())
