import logging

from database.collection import users, find_user

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)


async def residents_handler(callback: types.CallbackQuery, state: FSMContext):
    all_users = users.find()
    residents = InlineKeyboardMarkup(row_width=1)
    for user in all_users:
        name = user['full_name'].split()
        residents.add(InlineKeyboardButton(text=f"{name[0]} {name[1][0]}.{name[2][0]}.",
                                           callback_data=f"resident-{user['user_id']}"))
    back = InlineKeyboardButton(text='В меню', callback_data='menu')
    residents.add(back)
    await callback.message.edit_text('Резиденты:', reply_markup=residents)


async def resident_info(callback: types.CallbackQuery, state: FSMContext):
    back = InlineKeyboardMarkup(row_width=1)
    back.add(InlineKeyboardButton(text='Назад', callback_data='residents'))

    user_id = callback.data.split('-')[1]
    user = find_user(user_id)
    name = user['full_name'].split()
    telegram_user_name = user['telegram_user_name']
    text = f"Информация о {name[0]} {name[1][0]}.{name[2][0]}.:\n"
    if telegram_user_name:
        text += f" Тег: @{telegram_user_name}\n"
    text += f" Номер телефона: +{user['phone_number']}\n" \
            f" Компания: {user['company_name']}\n" \
            f" Сайт компании: <a href='{user['company_site']}'>*перейти*</a>"

    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=back, disable_web_page_preview=True)



