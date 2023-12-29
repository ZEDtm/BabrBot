import logging

from config import bot, dp
from models import users, find_user, User
from aiogram import executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands='start', state='*')
@dp.message_handler(lambda message: message.chat.type == 'private')
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    but1 = InlineKeyboardButton(text='Нет', callback_data='cancel_reg')
    but2 = InlineKeyboardButton(text='Да', callback_data='start_reg')
    button = types.KeyboardButton(text="Share Contact", request_contact=True)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(but1, but2)
    keyboard.add(button)

    print(message.from_user.last_name)
    print(message.from_user.first_name)
    print(message.from_user.username)
    user = find_user(message.from_user.id)
    if user:
        await message.answer(f"Здравствуйте, {user['full_name']}!", reply_markup=keyboard)

    else:
        await message.answer(f'Здравствуйте, сейчас Вам потребуется пройти небольшое анкетирование. Вы готовы?',
                             reply_markup=kb)


@dp.callback_query_handler(lambda callback: 'cancel_reg' in callback.data, state='*')
async def cancel_registration(callback: types.CallbackQuery):
    await callback.message.answer('ok')
    await start(callback.message)


@dp.callback_query_handler(lambda callback: callback.data == 'start_reg')
async def start_registration(callback: types.CallbackQuery):
    await callback.message.answer('ok')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
