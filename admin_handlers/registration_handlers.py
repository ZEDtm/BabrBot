import random
import re
import logging
import string
from datetime import datetime

from bson import ObjectId

from config import LOG_CHAT, bot, wait_registration, admins, DIR, referral_link, CHANNEL, CHAT
from database.collection import users
from database.models import User
from modules.bot_states import Registration

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    KeyboardButton

from modules.logger import send_log


async def registration_full_name(callback: types.CallbackQuery, state):
    if callback.from_user.id not in admins:
        return
    user = callback.data.split(sep='%')[1]
    if int(users.find_one({'_id': ObjectId(user)})['user_id']) not in wait_registration:
        await callback.message.edit_text('😖 Этот пользователь уже добавлен')
        return
    async with state.proxy() as data:
        data['user_db_id'] = user
    await callback.message.answer("✏ Укажите ФИО резидента:")
    await Registration.full_name.set()
    await send_log(f"Администратор[{callback.from_user.id}]: Заявка[{user}] -> Редактирование")


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
        user_db_id = data['user_db_id']
        full_name = data['full_name']
        description = data['description']
        company_name = data['company_name']
        company_site = data['company_site'] if data['company_site'] != '' else None
        video = data['video'] if data['video'] != '' else None
    await state.finish()

    user = users.find_one({'_id': ObjectId(user_db_id)})

    users.update_one(user, {'$set': {'full_name': full_name,
                                     'description': description,
                                     'image': None,
                                     'company_name': company_name,
                                     'company_site': company_site,
                                     'video': video}})

    keyboard = InlineKeyboardMarkup()
    admin = InlineKeyboardMarkup()

    wait_registration.discard(user['user_id'])
    try:
        link_channel = await bot.export_chat_invite_link(CHANNEL)
        link_chat = await bot.export_chat_invite_link(CHAT)
        keyboard.add(InlineKeyboardButton(text='📣 Наш канал', url=link_channel))
        keyboard.add(InlineKeyboardButton(text='💬 Наш чат', url=link_chat))
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'))
        await bot.send_message(user['user_id'], '😁 Вы успешно зарегистрированы!', reply_markup=keyboard)
    except:
        admin.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'))
        await message.answer('😖 Пользователь заблокировал бота')
    await message.answer("😁 Пользователь успешно добавлен", reply_markup=admin)

    await send_log(f"Администратор[{message.from_user.id}]: Пользователь[{user['user_id']}] -> Пользователи")


async def end_registration(message: types.Message, state: FSMContext):
    remove_keyboard = types.ReplyKeyboardRemove()
    await bot.send_message(message.from_user.id, '😁 Удаление клавиатуры', reply_markup=remove_keyboard)
    photo_sizes = message.photo
    # Получаем последнюю фотографию
    last_photo = photo_sizes[-1]
    async with state.proxy() as data:
        user_db_id = data['user_db_id']
        user = users.find_one({'_id': ObjectId(user_db_id)})

        file = await bot.get_file(last_photo.file_id)
        file_name = f'{last_photo.file_id}.jpg'
        await bot.download_file(file.file_path, destination=f"{DIR}/users/{user['user_id']}/{file_name}")
        image = f"{DIR}/users/{user['user_id']}/{file_name}"

        full_name = data['full_name']
        description = data['description']
        company_name = data['company_name']
        company_site = data['company_site'] if data['company_site'] != '' else None
        video = data['video'] if data['video'] != '' else None
    await state.finish()

    users.update_one(user, {'$set': {'full_name': full_name,
                                     'description': description,
                                     'image': image,
                                     'company_name': company_name,
                                     'company_site': company_site,
                                     'video': video}})

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'))

    wait_registration.discard(user['user_id'])
    try:
        await bot.send_message(user['user_id'], '😁 Вы успешно зарегистрированы!', reply_markup=keyboard)
    except:
        await message.answer('😖 Пользователь заблокировал бота')
    await message.answer("😁 Пользователь успешно добавлен", reply_markup=keyboard)

    await send_log(f"Администратор[{message.from_user.id}]: Пользователь[{user['user_id']}] -> Пользователи")


async def new_admin(callback: types.CallbackQuery, state: FSMContext):
    letters = string.ascii_lowercase
    rand_string = ''.join(random.choice(letters) for i in range(20))
    referral_link.add(rand_string)
    link = f"https://t.me/{callback.message.from_user.username}?start={rand_string}"
    text = f"🤔 Вы создали ссылку для добавления Администратора:\n\n" \
           f"{link}\n\n" \
           f"🤫 Не отправляйте ее в чаты и незнакомым людям!\n🛎 Ссылка действительна только 1 раз!"
    await callback.message.answer(text)

    await send_log(f"Администратор[{callback.from_user.id}]: Добавить администратора <- Ссылка")