import datetime
import re

from bson import ObjectId
from datetime import datetime

import admin_handlers.events_handlers
from config import dp
from database.collection import events, archive
from database.models import Event
from modules.bot_states import AdminNewEvent
from modules.calendar_module import SelectDays, NewEventCalendar, SelectTime
from modules.list_collection import ListArchive
from modules.logger import send_log

from aiogram import executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from handlers import main_handlers, registration_handlers, profile_handlers, calendar_handlers, residents_handlers


async def archive_list(callback: types.CallbackQuery, state: FSMContext):
    keyboard = await ListArchive().start_collection(archive.find())
    await callback.message.answer('Архив', reply_markup=keyboard)


async def archive_list_select(callback: types.CallbackQuery, state: FSMContext):
    select, archive_id, current_page = await ListArchive().processing_selection(callback, callback.data, archive.find())
    if archive_id:
        await archive_handle(callback, state, archive_id=archive_id, current_page=current_page)


async def archive_handle(callback: types.CallbackQuery, state: FSMContext, archive_id: str, current_page: int = None, date: dict = None):
    arch = archive.find_one({'_id': ObjectId(archive_id)})

    keyboard = InlineKeyboardMarkup()

    keyboard.add(InlineKeyboardButton(text='Добавить фото', callback_data=f"archive-add-images-{archive_id}"))
    keyboard.add(InlineKeyboardButton(text='Добавить видео', callback_data=f"archive-add-video-{archive_id}"))
    keyboard.add(InlineKeyboardButton(text='Добавить ссылку', callback_data=f"archive-add-link-{archive_id}"))

    if current_page:
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data=f"menu"),
                     InlineKeyboardButton(text='Назад', callback_data=f"archive_list-n-{current_page}"))
    if date:
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data=f"menu"),
                     InlineKeyboardButton(text='Назад', callback_data=f"admin_event_calendar:CURRENT:{date['year']}:{date['month']}:{date['day']}"))

    date_format = datetime(int(arch['year']), int(arch['month']), int(arch['day'])).strftime('%Y.%m.%d')
    text = f"[{date_format}]" \
           f"[Архив]: {arch['name']}\n" \
           f"[Описание]:\n{arch['description']}\n"
    await callback.message.edit_text(text, reply_markup=keyboard)