from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


class Registration(StatesGroup):
    full_name = State()
    surname = State()
    company_name = State()
    number = State()


class Calendar(StatesGroup):
    pass