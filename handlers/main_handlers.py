import logging

from database.collection import find_user
from modules.bot_states import Menu

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
