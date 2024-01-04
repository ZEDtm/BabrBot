from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


class Menu(StatesGroup):
    main = State()
    profile = State()
    calendar = State()
    archive = State()


class ProfileEdit(StatesGroup):
    full_name = State()
    company_name = State()
    company_site = State()


class Registration(StatesGroup):
    full_name = State()
    phone_number = State()
    company_name = State()
    company_site = State()


class EventSubscribe(StatesGroup):
    services = State()

class AdminNewEvent(StatesGroup):
    event_long = State()
    event_duration = State()
    event_name = State()
    event_description = State()
    event_price = State()
    event_services = State()
    event_services_new = State()
    event_add = State()


class AdminArchive(StatesGroup):
    list = State()
    add_images = State()
    add_video = State()
    add_link = State()