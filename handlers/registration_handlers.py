import re
import logging
from datetime import datetime

from config import LOG_CHAT, bot, wait_registration, admins
from database.collection import users, preusers
from database.models import User
from modules.bot_states import Registration

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from modules.logger import send_log


async def registration_send(message: types.Message, state: FSMContext):
    remove_keyboard = types.ReplyKeyboardRemove()
    if len(message.contact.phone_number) == 12:
        phone = message.contact.phone_number.split(sep='+')[1]
    elif message.contact.phone_number[0] == '8':
        phone = '7' + message.contact.phone_number[1::1]
    else:
        phone = message.contact.phone_number
    pre_user = preusers.find_one({'phone_number': phone})
    if pre_user:
        user = User(user_id=int(message.from_user.id),
                    telegram_first_name=message.from_user.first_name,
                    telegram_last_name=message.from_user.last_name,
                    telegram_user_name=message.from_user.username,
                    full_name=pre_user['full_name'],
                    phone_number=message.contact.phone_number,
                    description=pre_user['description'],
                    image=pre_user['image'],
                    video='',
                    company_name=pre_user['company_name'],
                    company_site=pre_user['company_site'],
                    subscribe=0)
        users.insert_one(user())
        preusers.delete_one(pre_user)
        await send_log(f"Пользователь[{message.contact.phone_number}] -> Пользователь[{message.from_user.id}]")
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'))
        await message.answer('😁 Вы найдены в базе!', reply_markup=remove_keyboard)
        await message.answer('Добро пожаловать в "БАБР" 🐈‍⬛!', reply_markup=keyboard)
        return

    wait_registration.add(message.from_user.id)
    await message.reply("😊 Извините, но я не нашел Вас в своей базе.. Ваша заявка на регистрацию успешно отправлена администраторам, ее рассмотрят в ближайшее время!", reply_markup=remove_keyboard)

    user = User(user_id=int(message.from_user.id),
                telegram_first_name=message.from_user.first_name,
                telegram_last_name=message.from_user.last_name,
                telegram_user_name=message.from_user.username,
                full_name=message.from_user.full_name,
                phone_number=message.contact.phone_number,
                description='',
                image='',
                video='',
                company_name='',
                company_site='',
                subscribe=0)
    user = users.insert_one(user())

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='Добавить', callback_data=f"add-user%{user.inserted_id}"))
    text = "Заявка на регистрацию:\n\n" \
           f"Номер телефона: +{message.contact.phone_number}\n" \
           f"Имя: {message.from_user.first_name}\n"
    if message.from_user.username:
        text += f"Тег: @{message.from_user.username}\n"
    text += f"Полное имя: {message.from_user.full_name}\n" \
            f"User ID: {message.from_user.id}"
    for admin in admins:
        await bot.send_message(admin, text, reply_markup=keyboard)

    await send_log(f"Пользователь[{message.from_user.id}] -> Заявка")