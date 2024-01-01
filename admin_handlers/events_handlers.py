import logging
import re

from config import dp
from database.collection import events
from database.models import Event
from modules.list_collection import ListEvents
from modules.bot_states import AdminNewEvent
from modules.calendar_module import SelectDays, NewEventCalendar, SelectTime

from aiogram import executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from handlers import main_handlers, registration_handlers, profile_handlers, calendar_handlers, residents_handlers

logging.basicConfig(level=logging.INFO)


async def list_events(callback: types.CallbackQuery, state: FSMContext):
    list_collection = await ListEvents().start_collection(events.find())
    await callback.message.edit_text('Список мероприятий:', reply_markup=list_collection)


async def list_events_select(callback: types.CallbackQuery, state: FSMContext):
    select, event_id = await ListEvents().processing_selection(callback, callback.data, events.find())
