import logging

from database.collection import find_user
from modules.bot_states import Menu

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)


async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(text='❌ Нет', callback_data='cancel_reg'),
                 InlineKeyboardButton(text='✅ Да', callback_data='start_reg'))

    menu = InlineKeyboardMarkup(row_width=1)
    menu.add(InlineKeyboardButton(text="🌟 Профиль", callback_data='profile'),
             InlineKeyboardButton(text="📅 Календарь", callback_data='calendar_handler'),
             InlineKeyboardButton(text="🏘️ Резиденты", callback_data='residents'))

    user = find_user(message.from_user.id)
    if user:
        if user['admin']:
            menu.add(InlineKeyboardButton(text="➕ Добавить мероприятие", callback_data='new_event'),
                     InlineKeyboardButton(text="Список мероприятий", callback_data='list_events'),
                     InlineKeyboardButton(text="Архив", callback_data='admin_archive'),
                     InlineKeyboardButton(text="Календарь мероприятий", callback_data='admin_calendar'))
        await Menu.main.set()
        await message.answer(f"Здравствуйте, {user['full_name'].split()[1]}!", reply_markup=menu)
    else:
        await message.answer(f'Здравствуйте, сейчас Вам потребуется пройти небольшое анкетирование. Вы готовы?',
                             reply_markup=keyboard)
    await message.delete()


async def menu_handler(callback: types.CallbackQuery, state: FSMContext):
    menu = InlineKeyboardMarkup(row_width=1)
    menu.add(InlineKeyboardButton(text="🌟 Профиль", callback_data='profile'),
             InlineKeyboardButton(text="📅 Календарь", callback_data='calendar_handler'),
             InlineKeyboardButton(text="🏘️ Резиденты", callback_data='residents'))

    user = find_user(callback.message.chat.id)
    if user:
        if user['admin']:
            menu.add(InlineKeyboardButton(text="➕ Добавить мероприятие", callback_data='new_event'),
                     InlineKeyboardButton(text="Список мероприятий", callback_data='list_events'),
                     InlineKeyboardButton(text="Архив", callback_data='admin_archive'),
                     InlineKeyboardButton(text="Календарь мероприятий", callback_data='admin_calendar'))

    await state.set_state(Menu.main)
    await callback.message.edit_text('Главное меню:', reply_markup=menu)
