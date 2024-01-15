import random
import re
import logging
import string
from datetime import datetime

from bson import ObjectId

from config import LOG_CHAT, bot, wait_registration, admins, DIR, referral_link, CHANNEL, CHAT
from database.collection import users, preusers
from database.models import User, PreUser
from modules.bot_states import Registration

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    KeyboardButton

from modules.logger import send_log


async def registration_phone_number(callback: types.CallbackQuery, state):
    await callback.message.edit_text("✏ Укажите номер телефона резидента. Обратите внимание, номер телефона будет проверяться с номером телеграм-аккаунта!\n\n Начинайте с 7:")
    await Registration.phone_number.set()


async def registration_full_name(message: types.Message, state: FSMContext):
    pattern = r"^7\d{10}$"
    if not re.match(pattern, message.text):
        await message.answer(
            '😔 Вы указали неправильный номер!\nПервая цифра 7, всего 11 цифр.\n\n✏ Пример: 79158252110')
        await Registration.phone_number.set()
        return
    async with state.proxy() as data:
        data['phone_number'] = message.text
    await message.answer("✏ Укажите ФИО резидента:")
    await Registration.full_name.set()
    await send_log(f"Администратор[{message.from_user.id}]: Новый пользователь[{message.text}] -> Пользователь")


async def registration_description(message: types.Message, state: FSMContext):
    pattern = r"^[А-Я][а-я]+\s[А-Я][а-я]+\s[А-Я][а-я]+$"
    if not re.match(pattern, message.text):
        await message.answer('👎 Вы указали неправильно ФИО.\n Пример: Иванов Иван Иванович')
        await Registration.full_name.set()
        return
    async with state.proxy() as data:
        data['full_name'] = message.text
    await Registration.description.set()
    await message.reply("✏ Укажите описание резидента:")


async def registration_company_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text

    await Registration.company_name.set()
    await message.reply("✏ Укажите название компании:")


async def registration_company_site(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['company_name'] = message.text

    await Registration.company_site.set()
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(KeyboardButton(text='🤔 Нет'))
    await message.reply("✏ Укажите сайт компании:", reply_markup=keyboard)


async def registration_video(message: types.Message, state: FSMContext):
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    if message.text == '🤔 Нет':
        async with state.proxy() as data:
            data['company_site'] = ''
    elif not re.match(url_pattern, message.text):
        await message.answer('👎 Вы указали неправильную ссылку, она должна начинаться с http:// или https://.')
        await Registration.company_site.set()
        return
    else:
        async with state.proxy() as data:
            data['company_site'] = message.text

    await Registration.video.set()
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(KeyboardButton(text='🤔 Нет'))
    await message.reply("🎥 Добавьте видео-карточку для профиля:", reply_markup=keyboard)


async def registration_image(message: types.Message, state: FSMContext):
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    if message.text == '🤔 Нет':
        async with state.proxy() as data:
            data['video'] = ''
    elif not re.match(url_pattern, message.text):
        await message.answer('👎 Вы указали неправильную ссылку, она должна начинаться с http:// или https://.')
        await Registration.video.set()
        return
    else:
        async with state.proxy() as data:
            data['video'] = message.text
    await Registration.image.set()
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(KeyboardButton(text='🤔 Нет'))
    await message.reply("📸 Пришлите фотография для профиля:", reply_markup=keyboard)



async def end_registration_no_image(message: types.Message, state: FSMContext):
    remove_keyboard = types.ReplyKeyboardRemove()
    await bot.send_message(message.from_user.id, '😁 Удаление клавиатуры', reply_markup=remove_keyboard)
    async with state.proxy() as data:
        phone_number = data['phone_number']
        full_name = data['full_name']
        description = data['description']
        company_name = data['company_name']
        company_site = data['company_site'] if data['company_site'] != '' else None
        video = data['video'] if data['video'] != '' else None
    await state.finish()

    pre_user = PreUser(full_name=full_name,
                       phone_number=phone_number,
                       description=description,
                       company_name=company_name,
                       company_site=company_site,
                       image='',
                       video=video)

    insert = preusers.insert_one(pre_user())

    admin = InlineKeyboardMarkup()
    admin.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'))

    await message.answer("😁 Пользователь успешно добавлен", reply_markup=admin)

    await send_log(f"Администратор[{message.from_user.id}]: Пользователь[{str(insert.inserted_id)}] -> Пользователи")


async def end_registration(message: types.Message, state: FSMContext):
    remove_keyboard = types.ReplyKeyboardRemove()
    await bot.send_message(message.from_user.id, '😁 Удаление клавиатуры', reply_markup=remove_keyboard)
    photo_sizes = message.photo
    # Получаем последнюю фотографию
    last_photo = photo_sizes[-1]
    async with state.proxy() as data:

        file = await bot.get_file(last_photo.file_id)
        file_name = f'{last_photo.file_id}.jpg'
        await bot.download_file(file.file_path, destination=f"{DIR}/users/{data['phone_number']}/{file_name}")
        image = f"{DIR}/users/{data['phone_number']}/{file_name}"

        phone_number = data['phone_number']
        full_name = data['full_name']
        description = data['description']
        company_name = data['company_name']
        company_site = data['company_site'] if data['company_site'] != '' else None
        video = data['video'] if data['video'] != '' else None
    await state.finish()

    pre_user = PreUser(full_name=full_name,
                       phone_number=phone_number,
                       description=description,
                       company_name=company_name,
                       company_site=company_site,
                       image=image,
                       video=video)

    insert = preusers.insert_one(pre_user())

    admin = InlineKeyboardMarkup()
    admin.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'))

    await message.answer("😁 Пользователь успешно добавлен", reply_markup=admin)

    await send_log(f"Администратор[{message.from_user.id}]: Пользователь[{str(insert.inserted_id)}] -> Пользователи")