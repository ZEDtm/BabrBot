import logging
import re
from datetime import datetime
from bson import ObjectId

from admin_handlers import archive_handlers
from config import dp
from database.collection import events, archive
from database.models import Event
from modules.list_collection import ListEvents
from modules.bot_states import AdminNewEvent
from modules.bot_calendar_module import SelectDays, NewEventCalendar, SelectTime, AdminEventCalendar

from aiogram import executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from handlers import main_handlers, registration_handlers, profile_handlers, calendar_handlers, residents_handlers

logging.basicConfig(level=logging.INFO)


async def list_events_public(callback: types.CallbackQuery, state: FSMContext):
    list_collection = await ListEvents().start_collection(events.find())
    await callback.message.edit_text('Список мероприятий:', reply_markup=list_collection)


async def list_events_select(callback: types.CallbackQuery, state: FSMContext):
    select, event_id, current_page = await ListEvents().processing_selection(callback, callback.data, events.find())
    if event_id:
        await event_handle(callback, state, event_id, current_page=current_page)


async def admin_calendar(callback: types.CallbackQuery, state: FSMContext):
    calendar = await AdminEventCalendar(events.find(), archive.find()).start_calendar()
    await callback.message.edit_text('Календарь мероприятий', reply_markup=calendar)


async def admin_calendar_select(callback: types.CallbackQuery, state: FSMContext):
    event, date, act_id = await AdminEventCalendar(events.find(), archive.find()).process_selection(callback, callback.data)
    if act_id and event:
        await event_handle(callback, state, act_id, date=date)
    elif act_id:
        await archive_handlers.archive_handle(callback, state, archive_id=act_id, date=date)


async def event_handle(callback: types.CallbackQuery, state: FSMContext, event_id: str, current_page: int = None, date: dict = None):
    event = events.find_one({'_id': ObjectId(event_id)})

    keyboard = InlineKeyboardMarkup(row_width=1)
    if event['public']:
        keyboard.add(InlineKeyboardButton(text='Отменить', callback_data=f"public-event-{event_id}"))
    else:
        keyboard.add(InlineKeyboardButton(text='Подтвердить', callback_data=f"public-event-{event_id}"))
    keyboard.add(InlineKeyboardButton(text='Изменить название', callback_data=f"event-edit-name-{event_id}"),
                 InlineKeyboardButton(text='Изменить описание', callback_data=f"event-edit-description-{event_id}"),
                 InlineKeyboardButton(text='Изменить стоимость', callback_data=f"event-edit-price-{event_id}"),
                 InlineKeyboardButton(text='Изменить дату и длительность', callback_data=f"event-edit-date-{event_id}"),
                 InlineKeyboardButton(text='Изменить услуги', callback_data=f"event-edit-service-{event_id}"))
    if current_page:
        keyboard.add(InlineKeyboardButton(text='Назад', callback_data=f"events_list-n-{current_page}"))
    if date:
        keyboard.add(InlineKeyboardButton(text='Назад', callback_data=f"admin_event_calendar:CURRENT:{date['year']}:{date['month']}:{date['day']}"))
    if not event['public']:
        keyboard.add(InlineKeyboardButton(text='В черновик', callback_data=f"menu"))

    text = f"[Дата и время]: {datetime(int(event['year']), int(event['month']), int(event['day']), int(event['hour']), int(event['minute']))}\n"
    text += f"[Название]: {event['name']}\n" \
            f"[Описание]:\n{event['description']}\n" \
            f"[Стоимость посещения]: {event['price']}руб.\n" \
            f"[Длительность]: {event['duration']}дн.\n" \
            f"[Услуги]:\n"
    for service, price in zip(event['service_description'], event['service_price']):
        text += f" * {service} | {price}руб.\n"
    text += f"[Участников]: {len(event['users'])} (резид.)"
    await callback.message.edit_text(text, reply_markup=keyboard)
