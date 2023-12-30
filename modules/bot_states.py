from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


class Menu(StatesGroup):
    main = State()
    profile = State()
    calendar = State()


class ProfileEdit(StatesGroup):
    full_name = State()
    company_name = State()
    company_site = State()


class Registration(StatesGroup):
    full_name = State()
    phone_number = State()
    company_name = State()
    company_site = State()


class Calendar(StatesGroup):
    pass