import logging

from bson import ObjectId

from config import bot
from database.collection import users, find_user
from modules.list_collection import ListResidents
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def residents_handler(callback: types.CallbackQuery, state: FSMContext):
    all_users = users.find()
    residents = await ListResidents().start_collection(all_users)
    await callback.message.edit_text('Резиденты:', reply_markup=residents)


async def residents_handler_select(callback: types.CallbackQuery, state: FSMContext):
    all_users = users.find()
    select, resident_id, current_page = await ListResidents().processing_selection(callback, callback.data, all_users)
    if select:
        await resident_info(callback, resident_id, current_page, state)


async def resident_info(callback: types.CallbackQuery, resident_id: str, current_page: int, state: FSMContext):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton(text='↩️ Назад', callback_data=f'residents_list-n-{current_page}'))

    user = users.find_one({'_id': ObjectId(resident_id)})
    name = user['full_name'].split()
    telegram_user_name = user['telegram_user_name']
    site = user['company_site']
    image_path = user['image']

    text = f"Информация о {name[0]} {name[1][0]}.{name[2][0]}.:\n"
    if telegram_user_name:
        text += f" Тег: @{telegram_user_name}\n"

    text += f" Номер телефона: +{user['phone_number']}\n" \
            f" Компания: {user['company_name']}\n"
    if site:
        text += f" Сайт компании: <a href='{site}'>*перейти*</a>"
    text += f"Описание: {user['description']}"
    if image_path:
        await bot.send_photo(callback.from_user.id, photo=types.InputFile(image_path))
    await callback.message.answer(text, parse_mode='HTML', reply_markup=keyboard, disable_web_page_preview=True)
    await callback.message.delete()


