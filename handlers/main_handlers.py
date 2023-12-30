import logging
import re

from config import bot, dp
from database.collection import users, find_user, update_full_name, update_company_name, update_company_site, events, find_event
from database.models import User
from modules.bot_states import Registration, Menu, ProfileEdit

from aiogram import executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from modules.calendar_module import EventCalendar
from handlers import registration_handlers, profile_handlers, calendar_handlers, residents_handlers

logging.basicConfig(level=logging.INFO)


async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    no = InlineKeyboardButton(text='Нет', callback_data='cancel_reg')
    yes = InlineKeyboardButton(text='Да', callback_data='start_reg')
    keyboard.add(no, yes)

    menu = InlineKeyboardMarkup(row_width=1)
    profile = InlineKeyboardButton(text="Профиль", callback_data='profile')
    calendar = InlineKeyboardButton(text="Календарь", callback_data='calendar_handler')
    residents = InlineKeyboardButton(text="Резиденты", callback_data='residents')
    menu.add(profile, calendar, residents)

    user = find_user(message.from_user.id)
    if user:
        await Menu.main.set()
        await message.answer(f"Здравствуйте, {user['full_name'].split()[1]}!", reply_markup=menu)
    else:
        await message.answer(f'Здравствуйте, сейчас Вам потребуется пройти небольшое анкетирование. Вы готовы?',
                             reply_markup=keyboard)
    await message.delete()


async def menu_handler(callback: types.CallbackQuery, state: FSMContext):
    menu = InlineKeyboardMarkup(row_width=1)
    profile = InlineKeyboardButton(text="Профиль", callback_data='profile')
    calendar = InlineKeyboardButton(text="Календарь", callback_data='calendar_handler')
    residents = InlineKeyboardButton(text="Резиденты", callback_data='residents')
    menu.add(profile, calendar, residents)

    await state.set_state(Menu.main)
    await callback.message.edit_text('Главное меню:', reply_markup=menu)
