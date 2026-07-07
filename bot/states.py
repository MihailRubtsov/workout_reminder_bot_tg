"""Finite-state-machine states, grouped by the flow they belong to."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AddWeek(StatesGroup):
    """Collecting a training plan day by day."""

    monday = State()
    tuesday = State()
    wednesday = State()
    thursday = State()
    friday = State()
    saturday = State()
    sunday = State()


class AddTimes(StatesGroup):
    """Collecting reminder times day by day."""

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
