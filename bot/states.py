"""all states"""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AddWeek(StatesGroup):
    monday = State()
    tuesday = State()
    wednesday = State()
    thursday = State()
    friday = State()
    saturday = State()
    sunday = State()


class AddTimes(StatesGroup):
    monday = State()
    tuesday = State()
    wednesday = State()
    thursday = State()
    friday = State()
    saturday = State()
    sunday = State()


class ChangeDayTime(StatesGroup):
    day = State()
    time = State()


class ViewWeek(StatesGroup):
    number = State()


class DeleteWeek(StatesGroup):
    confirm = State()


class ChangeWeekPlan(StatesGroup):
    number = State()
    file = State()


class UploadPlan(StatesGroup):
    file = State()


class CalorieCalc(StatesGroup):
    sex = State()
    age = State()
    height = State()
    weight = State()
    activity = State()
