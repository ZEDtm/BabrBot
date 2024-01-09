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
    phone_number = State()
    full_name = State()
    description = State()
    company_name = State()
    company_site = State()
    image = State()


class EditUser(StatesGroup):
    phone_number = State()
    full_name = State()
    description = State()
    company_name = State()
    company_site = State()
    image = State()
    delete = State()


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


class AdminEditEvent(StatesGroup):
    event_name = State()
    event_description = State()
    event_price = State()
    event_services = State()
    event_service_description = State()
    event_service_price = State()
    event_new_service_description = State()
    event_new_service_price = State()
    event_add = State()
    event_long = State()
    event_duration = State()


class AdminArchive(StatesGroup):
    list = State()
    add_images = State()
    add_video = State()
    add_link = State()