"""Daily calorie calculator (Mifflin-St Jeor formula).

Unlike the original version, numeric input is validated at every step, so a
non-numeric answer asks the user to retry instead of crashing the handler.
"""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import reply
from bot.states import CalorieCalc

router = Router(name="calories")

# Activity level -> multiplier applied to the basal metabolic rate.
ACTIVITY_FACTORS = {
    1: 1.2,    # sedentary
    2: 1.375,  # light (1-3 workouts / week)
    3: 1.55,   # moderate (3-5 workouts)
    4: 1.725,  # high (6-7 workouts + physical job)
    5: 1.9,    # extreme (professional athletes)
}

ACTIVITY_PROMPT = """Please indicate your activity level using the following numbers:
1 — minimal (sedentary lifestyle)
2 — light (1–3 workouts per week)
3 — moderate (3–5 workouts)
4 — high (6–7 workouts + physical labor)
5 — extreme (professional athletes)"""


def _parse_positive_int(text: str | None) -> int | None:
    try:
        value = int((text or "").strip())
    except ValueError:
        return None
    return value if value > 0 else None


@router.message(Command("calories"))
async def calories_start(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Select your gender: 1 — male, 2 — female", reply_markup=reply.main_menu()
    )
    await state.set_state(CalorieCalc.sex)


@router.message(CalorieCalc.sex)
async def calories_sex(message: Message, state: FSMContext) -> None:
    if (message.text or "").strip() not in {"1", "2"}:
        await message.answer("Enter 1 (male) or 2 (female).")
        return
    await state.update_data(sex=message.text.strip())
    await message.answer("How old are you?")
    await state.set_state(CalorieCalc.age)


@router.message(CalorieCalc.age)
async def calories_age(message: Message, state: FSMContext) -> None:
    age = _parse_positive_int(message.text)
    if age is None:
        await message.answer("Age must be a positive number.")
        return
    await state.update_data(age=age)
    await message.answer("How tall are you in centimeters?")
    await state.set_state(CalorieCalc.height)


@router.message(CalorieCalc.height)
async def calories_height(message: Message, state: FSMContext) -> None:
    height = _parse_positive_int(message.text)
    if height is None:
        await message.answer("The growth must be a positive number.")
        return
    await state.update_data(height=height)
    await message.answer("How much do you weigh in kilograms?")
    await state.set_state(CalorieCalc.weight)


@router.message(CalorieCalc.weight)
async def calories_weight(message: Message, state: FSMContext) -> None:
    weight = _parse_positive_int(message.text)
    if weight is None:
        await message.answer("The weight must be a positive number.")
        return
    await state.update_data(weight=weight)
    await message.answer(ACTIVITY_PROMPT)
    await state.set_state(CalorieCalc.activity)


@router.message(CalorieCalc.activity)
async def calories_finish(message: Message, state: FSMContext) -> None:
    activity = _parse_positive_int(message.text)
    if activity not in ACTIVITY_FACTORS:
        await message.answer("Enter a number between 1 and 5.")
        return

    data = await state.get_data()
    # Mifflin-St Jeor basal metabolic rate.
    bmr = 10 * data["weight"] + 6.25 * data["height"] - 5 * data["age"]
    bmr += 5 if data["sex"] == "1" else -161
    daily = round(bmr * ACTIVITY_FACTORS[activity])

    await state.clear()
    await message.answer(
        f"Your daily calorie intake: {daily} ккал.",
        reply_markup=reply.main_menu(),
    )
