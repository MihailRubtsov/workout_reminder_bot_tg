"""Schedule management: add / view / edit / delete weeks and reminder times."""
from __future__ import annotations

import io
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message

from bot.config import Config
from bot.database.repository import DAYS, PLAN_SEPARATOR, Repository
from bot.keyboards import reply
from bot.services.formatting import format_all_weeks, format_week
from bot.services.plan_parser import parse_template
from bot.services.validators import is_valid_time, is_valid_weekday
from bot.states import (
    AddTimes,
    AddWeek,
    ChangeDayTime,
    ChangeWeekPlan,
    DeleteWeek,
    UploadPlan,
    ViewWeek,
)

logger = logging.getLogger(__name__)
router = Router(name="schedule")

# Ordered prompts reused by the day-by-day plan and time collection flows.
_PLAN_PROMPTS = (
    "Пришли тренировку на понедельник",
    "Пришли тренировку на вторник",
    "Пришли тренировку на среду",
    "Пришли тренировку на четверг",
    "Пришли тренировку на пятницу",
    "Пришли тренировку на субботу",
    "Пришли тренировку на воскресенье",
)
_TIME_PROMPTS = tuple(p.replace("тренировку", "время") for p in _PLAN_PROMPTS)


async def _read_plan_from_document(bot: Bot, message: Message) -> str:
    """Download an uploaded .txt template and return the parsed plan string.

    Raises :class:`ValueError` if there is no document or it is malformed.
    """
    if message.document is None:
        raise ValueError("No document attached")
    buffer = io.BytesIO()
    await bot.download(message.document, destination=buffer)
    text = buffer.getvalue().decode("utf-8")
    return parse_template(text)


# --------------------------------------------------------------------------
# Add a week, one day at a time
# --------------------------------------------------------------------------
@router.message(Command("add_week"))
async def add_week_start(
    message: Message, state: FSMContext, repo: Repository, config: Config
) -> None:
    if repo.get_weeks_count(message.from_user.id) >= config.max_weeks:
        await message.answer(f"Достигнут лимит в {config.max_weeks} недель.")
        return
    await message.answer(_PLAN_PROMPTS[0])
    await state.set_state(AddWeek.monday)


async def _collect_plan_day(
    message: Message, state: FSMContext, field: str,
    next_state, next_index: int,
) -> None:
    await state.update_data(**{field: message.text})
    await message.answer(_PLAN_PROMPTS[next_index])
    await state.set_state(next_state)


@router.message(AddWeek.monday)
async def add_week_mon(message: Message, state: FSMContext) -> None:
    await _collect_plan_day(message, state, "monday", AddWeek.tuesday, 1)


@router.message(AddWeek.tuesday)
async def add_week_tue(message: Message, state: FSMContext) -> None:
    await _collect_plan_day(message, state, "tuesday", AddWeek.wednesday, 2)


@router.message(AddWeek.wednesday)
async def add_week_wed(message: Message, state: FSMContext) -> None:
    await _collect_plan_day(message, state, "wednesday", AddWeek.thursday, 3)


@router.message(AddWeek.thursday)
async def add_week_thu(message: Message, state: FSMContext) -> None:
    await _collect_plan_day(message, state, "thursday", AddWeek.friday, 4)


@router.message(AddWeek.friday)
async def add_week_fri(message: Message, state: FSMContext) -> None:
    await _collect_plan_day(message, state, "friday", AddWeek.saturday, 5)


@router.message(AddWeek.saturday)
async def add_week_sat(message: Message, state: FSMContext) -> None:
    await _collect_plan_day(message, state, "saturday", AddWeek.sunday, 6)


@router.message(AddWeek.sunday)
async def add_week_finish(
    message: Message, state: FSMContext, repo: Repository, config: Config
) -> None:
    await state.update_data(sunday=message.text)
    data = await state.get_data()
    plan = PLAN_SEPARATOR.join(data[day] for day in DAYS)
    added = repo.add_week(message.from_user.id, plan, config.max_weeks)
    await state.clear()
    if added:
        await message.answer(
            "Расписание сохранено!", reply_markup=reply.main_menu()
        )
    else:
        await message.answer(
            f"Достигнут лимит в {config.max_weeks} недель.",
            reply_markup=reply.main_menu(),
        )


# --------------------------------------------------------------------------
# Upload a week from a template file
# --------------------------------------------------------------------------
@router.message(Command("upload_week"))
async def upload_week_start(
    message: Message, state: FSMContext, repo: Repository, config: Config
) -> None:
    if repo.get_weeks_count(message.from_user.id) >= config.max_weeks:
        await message.answer(f"Достигнут лимит в {config.max_weeks} недель.")
        return
    await message.answer("Пришли мне заполненный файл-шаблон.")
    await state.set_state(UploadPlan.file)


@router.message(UploadPlan.file, F.document)
async def upload_week_finish(
    message: Message, state: FSMContext, bot: Bot,
    repo: Repository, config: Config,
) -> None:
    try:
        plan = await _read_plan_from_document(bot, message)
    except (ValueError, UnicodeDecodeError):
        await message.answer(
            "Не получилось прочитать файл. Проверь, что это .txt по шаблону.",
            reply_markup=reply.main_menu(),
        )
        await state.clear()
        return
    added = repo.add_week(message.from_user.id, plan, config.max_weeks)
    await state.clear()
    text = "Расписание добавлено!" if added else "Достигнут лимит недель."
    await message.answer(text, reply_markup=reply.main_menu())


@router.message(UploadPlan.file)
async def upload_week_not_a_file(message: Message) -> None:
    await message.answer("Нужен файл-документ. Пришли .txt по шаблону.")


# --------------------------------------------------------------------------
# View schedule
# --------------------------------------------------------------------------
@router.message(Command("all_weeks"))
async def all_weeks(message: Message, repo: Repository) -> None:
    weeks = repo.get_all_weeks(message.from_user.id)
    if not weeks:
        await message.answer(
            "Ты ещё не добавил расписание.", reply_markup=reply.main_menu()
        )
        return
    await message.answer(
        format_all_weeks(weeks), reply_markup=reply.main_menu()
    )


@router.message(Command("view_week"))
async def view_week_start(
    message: Message, state: FSMContext, repo: Repository
) -> None:
    total = repo.get_weeks_count(message.from_user.id)
    if total == 0:
        await message.answer(
            "Ты ещё не добавил расписание.", reply_markup=reply.main_menu()
        )
        return
    await message.answer(
        f"Пришли номер недели (всего у тебя {total}).",
        reply_markup=reply.main_menu(),
    )
    await state.set_state(ViewWeek.number)


@router.message(ViewWeek.number)
async def view_week_show(
    message: Message, state: FSMContext, repo: Repository
) -> None:
    total = repo.get_weeks_count(message.from_user.id)
    try:
        number = int(message.text)
    except (ValueError, TypeError):
        await message.answer("Нужно число. Попробуй ещё раз.")
        return
    if not 1 <= number <= total:
        await message.answer(f"Неверный номер. Всего недель: {total}.")
        return
    plan = repo.get_week_plan(message.from_user.id, number)
    await state.clear()
    await message.answer(
        f"Тренировочная неделя №{number}\n\n{format_week(plan)}",
        reply_markup=reply.main_menu(),
    )


# --------------------------------------------------------------------------
# Delete last week
# --------------------------------------------------------------------------
@router.message(Command("delete_week"))
async def delete_week_start(
    message: Message, state: FSMContext, repo: Repository
) -> None:
    if repo.get_weeks_count(message.from_user.id) == 0:
        await message.answer(
            "Удалять нечего.", reply_markup=reply.main_menu()
        )
        return
    await message.answer(
        "Удалить последнюю неделю? Напиши «да» или «yes» для подтверждения."
    )
    await state.set_state(DeleteWeek.confirm)


@router.message(DeleteWeek.confirm)
async def delete_week_confirm(
    message: Message, state: FSMContext, repo: Repository
) -> None:
    await state.clear()
    if (message.text or "").strip().lower() in {"да", "yes"}:
        repo.delete_last_week(message.from_user.id)
        await message.answer(
            "Последняя неделя удалена.", reply_markup=reply.main_menu()
        )
    else:
        await message.answer(
            "Удаление отменено.", reply_markup=reply.main_menu()
        )


# --------------------------------------------------------------------------
# Set reminder times for all days
# --------------------------------------------------------------------------
@router.message(Command("set_times"))
async def set_times_start(message: Message, state: FSMContext) -> None:
    await message.answer(_TIME_PROMPTS[0] + " (формат ЧЧ:ММ)")
    await state.set_state(AddTimes.monday)


async def _collect_time_day(
    message: Message, state: FSMContext, field: str,
    next_state, next_index: int,
) -> bool:
    """Store one day's time. Returns False (and ends the flow) if invalid."""
    if not is_valid_time(message.text or ""):
        await message.answer(
            "Некорректное время. Начни заново командой /set_times.",
            reply_markup=reply.main_menu(),
        )
        await state.clear()
        return False
    await state.update_data(**{field: message.text})
    if next_state is not None:
        await message.answer(_TIME_PROMPTS[next_index])
        await state.set_state(next_state)
    return True


@router.message(AddTimes.monday)
async def set_time_mon(message: Message, state: FSMContext) -> None:
    await _collect_time_day(message, state, "monday", AddTimes.tuesday, 1)


@router.message(AddTimes.tuesday)
async def set_time_tue(message: Message, state: FSMContext) -> None:
    await _collect_time_day(message, state, "tuesday", AddTimes.wednesday, 2)


@router.message(AddTimes.wednesday)
async def set_time_wed(message: Message, state: FSMContext) -> None:
    await _collect_time_day(message, state, "wednesday", AddTimes.thursday, 3)


@router.message(AddTimes.thursday)
async def set_time_thu(message: Message, state: FSMContext) -> None:
    await _collect_time_day(message, state, "thursday", AddTimes.friday, 4)


@router.message(AddTimes.friday)
async def set_time_fri(message: Message, state: FSMContext) -> None:
    await _collect_time_day(message, state, "friday", AddTimes.saturday, 5)


@router.message(AddTimes.saturday)
async def set_time_sat(message: Message, state: FSMContext) -> None:
    await _collect_time_day(message, state, "saturday", AddTimes.sunday, 6)


@router.message(AddTimes.sunday)
async def set_time_finish(
    message: Message, state: FSMContext, repo: Repository
) -> None:
    if not await _collect_time_day(message, state, "sunday", None, 0):
        return
    data = await state.get_data()
    repo.set_all_times(message.from_user.id, data)
    await state.clear()
    await message.answer(
        "Время напоминаний сохранено!", reply_markup=reply.main_menu()
    )


# --------------------------------------------------------------------------
# Change the time for a single day
# --------------------------------------------------------------------------
@router.message(Command("change_time"))
async def change_time_start(
    message: Message, state: FSMContext, repo: Repository
) -> None:
    if repo.get_weeks_count(message.from_user.id) == 0:
        await message.answer(
            "Сначала добавь расписание.", reply_markup=reply.main_menu()
        )
        return
    await message.answer(
        "Выбери день недели", reply_markup=reply.weekday_picker()
    )
    await state.set_state(ChangeDayTime.day)


@router.message(ChangeDayTime.day)
async def change_time_day(message: Message, state: FSMContext) -> None:
    if not is_valid_weekday(message.text or ""):
        await message.answer(
            "Это не название дня недели.", reply_markup=reply.main_menu()
        )
        await state.clear()
        return
    await state.update_data(day=message.text)
    await message.answer("Пришли время для этого дня (ЧЧ:ММ)")
    await state.set_state(ChangeDayTime.time)


@router.message(ChangeDayTime.time)
async def change_time_finish(
    message: Message, state: FSMContext, repo: Repository
) -> None:
    if not is_valid_time(message.text or ""):
        await message.answer(
            "Некорректное время.", reply_markup=reply.main_menu()
        )
        await state.clear()
        return
    data = await state.get_data()
    repo.set_day_time(message.from_user.id, data["day"], message.text)
    await state.clear()
    await message.answer(
        "Время обновлено!", reply_markup=reply.main_menu()
    )


# --------------------------------------------------------------------------
# Replace an existing week's plan with an uploaded file
# --------------------------------------------------------------------------
@router.message(Command("change_week"))
async def change_week_start(
    message: Message, state: FSMContext, repo: Repository
) -> None:
    total = repo.get_weeks_count(message.from_user.id)
    if total == 0:
        await message.answer(
            "Сначала добавь расписание.", reply_markup=reply.main_menu()
        )
        return
    await message.answer(
        f"Пришли номер недели для замены (всего {total}).",
        reply_markup=reply.main_menu(),
    )
    await state.set_state(ChangeWeekPlan.number)


@router.message(ChangeWeekPlan.number)
async def change_week_number(
    message: Message, state: FSMContext, repo: Repository
) -> None:
    total = repo.get_weeks_count(message.from_user.id)
    try:
        number = int(message.text)
    except (ValueError, TypeError):
        await message.answer("Нужно число. Попробуй ещё раз.")
        return
    if not 1 <= number <= total:
        await message.answer(f"Неверный номер. Всего недель: {total}.")
        return
    await state.update_data(number=number)
    await message.answer("Теперь пришли файл-шаблон с новым планом.")
    await state.set_state(ChangeWeekPlan.file)


@router.message(ChangeWeekPlan.file, F.document)
async def change_week_finish(
    message: Message, state: FSMContext, bot: Bot, repo: Repository
) -> None:
    data = await state.get_data()
    try:
        plan = await _read_plan_from_document(bot, message)
    except (ValueError, UnicodeDecodeError):
        await message.answer(
            "Файл заполнен неправильно.", reply_markup=reply.main_menu()
        )
        await state.clear()
        return
    repo.update_week_plan(message.from_user.id, data["number"], plan)
    await state.clear()
    await message.answer(
        "Неделя обновлена!", reply_markup=reply.main_menu()
    )


@router.message(ChangeWeekPlan.file)
async def change_week_not_a_file(message: Message) -> None:
    await message.answer("Нужен файл-документ. Пришли .txt по шаблону.")


# --------------------------------------------------------------------------
# Template file
# --------------------------------------------------------------------------
@router.message(Command("template"))
async def send_template(message: Message, config: Config) -> None:
    await message.answer_document(FSInputFile(config.template_path))
