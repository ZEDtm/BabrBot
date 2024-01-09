import os
import random
import re
import logging
import string
from datetime import datetime

from bson import ObjectId

import handlers.main_handlers
from config import LOG_CHAT, bot, wait_registration, admins, DIR, referral_link
from database.collection import users
from database.models import User
from modules.bot_states import Registration, EditUser, Menu
from modules.list_collection import ListUsers, ListAdmins, ListWaiting

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, \
    KeyboardButton

from modules.logger import send_log


async def list_users(callback: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text='Резиденты', callback_data='list-rusers'),
                 InlineKeyboardButton(text='Заявки на добавление', callback_data='list-wusers'),
                 InlineKeyboardButton(text='Администраторы', callback_data='list-ausers'),
                 InlineKeyboardButton(text='Добавить администратора', callback_data='add-admin'),
                 InlineKeyboardButton(text='В меню', callback_data='menu'))
    await callback.message.edit_text('Пользователи:', reply_markup=keyboard)


async def list_residents(callback: types.CallbackQuery, state: FSMContext):
    keyboard = await ListUsers().start_collection(users.find())
    await callback.message.edit_text('Резиденты:', reply_markup=keyboard)


async def list_residents_select(callback: types.CallbackQuery, state: FSMContext):
    collection = users.find()
    print(callback.data)
    select, resident_id, current_page = await ListUsers().processing_selection(callback, callback.data, collection)
    if select:
        await resident_info(callback, resident_id, current_page, state)


async def list_admins(callback: types.CallbackQuery, state: FSMContext):
    keyboard = await ListAdmins().start_collection(users.find())
    await callback.message.edit_text('Администраторы:', reply_markup=keyboard)


async def list_admins_select(callback: types.CallbackQuery, state: FSMContext):
    select, admin_id, current_page = await ListAdmins().processing_selection(callback, callback.data, users.find())
    if select:
        await admin_info(callback, admin_id, current_page, state)


async def list_waiting(callback: types.CallbackQuery, state: FSMContext):
    keyboard = await ListWaiting().start_collection(users.find())
    await callback.message.edit_text('Заявки:', reply_markup=keyboard)


async def list_waiting_select(callback: types.CallbackQuery, state: FSMContext):
    select, wait_id, current_page = await ListWaiting().processing_selection(callback, callback.data, users.find())
    if select:
        await waiting_info(callback, wait_id, current_page, state)


async def resident_info(callback: types.CallbackQuery, resident_id: str, current_page: int, state: FSMContext):
    user = users.find_one({'_id': ObjectId(resident_id)})
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text='Изменить ФИО', callback_data=f"edit-user-full_name%{resident_id}"))
    keyboard.add(InlineKeyboardButton(text='Изменить Номер', callback_data=f"edit-user-phone_number%{resident_id}"))
    keyboard.add(InlineKeyboardButton(text='Изменить Описание', callback_data=f"edit-user-description%{resident_id}"))
    keyboard.add(InlineKeyboardButton(text='Изменить Название компании', callback_data=f"edit-user-company_name%{resident_id}"))
    keyboard.add(InlineKeyboardButton(text='Изменить Сайт', callback_data=f"edit-user-company_site%{resident_id}"))
    keyboard.add(InlineKeyboardButton(text='Изменить Фото', callback_data=f"edit-user-image%{resident_id}"))
    keyboard.add(InlineKeyboardButton(text='Удалить', callback_data=f"delete-user%{resident_id}"))
    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                 InlineKeyboardButton(text='Назад', callback_data=f'rusers_list-n-{current_page}'))

    image_path = user['image']
    text = f"User ID: {user['user_id']}\n" \
           f"Имя в телеграм: {user['telegram_first_name']}\n" \
           f"Фамилия в телеграм: {user['telegram_last_name']}\n" \
           f"Тег: @{user['telegram_user_name']}\n" \
           f"ФИО: {user['full_name']}" \
           f"Номер телефона: {user['phone_number']}\n" \
           f"Описание: {user['description']}\n" \
           f"Название компании: {user['company_name']}\n" \
           f"Сайт: {user['company_site']}"

    if image_path:
        await bot.send_photo(callback.from_user.id, photo=types.InputFile(image_path))
    await callback.message.answer(text, parse_mode='HTML', reply_markup=keyboard, disable_web_page_preview=True)
    await callback.message.delete()

async def admin_info(callback: types.CallbackQuery, admin_id: str, current_page: int, state: FSMContext):
    user = users.find_one({'_id': ObjectId(admin_id)})
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text='Разжаловать', callback_data=f"delete-user%{admin_id}"))
    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                 InlineKeyboardButton(text='Назад', callback_data=f'admins_list-n-{current_page}'))

    image_path = user['image']
    text = f"User ID: {user['user_id']}\n" \
           f"Имя в телеграм: {user['telegram_first_name']}\n" \
           f"Фамилия в телеграм: {user['telegram_last_name']}\n" \
           f"Тег: @{user['telegram_user_name']}\n" \

    if image_path:
        await bot.send_photo(callback.from_user.id, photo=types.InputFile(image_path), caption=text, parse_mode='HTML', reply_markup=keyboard)
    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard, disable_web_page_preview=True)


async def waiting_info(callback: types.CallbackQuery, wait_id: str, current_page: int, state: FSMContext):
    user = users.find_one({'_id': ObjectId(wait_id)})
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text='Рассмотреть', callback_data=f"add-user%{wait_id}"))
    keyboard.add(InlineKeyboardButton(text='Удалить', callback_data=f"delete-user%{wait_id}"))
    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                 InlineKeyboardButton(text='Назад', callback_data=f'waiting_list-n-{current_page}'))

    text = f"User ID: {user['user_id']}\n" \
           f"Имя в телеграм: {user['telegram_first_name']}\n" \
           f"Фамилия в телеграм: {user['telegram_last_name']}\n" \
           f"Тег: @{user['telegram_user_name']}\n" \
           f"Номер телефона: {user['phone_number']}\n"

    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard, disable_web_page_preview=True)


async def edit_user_full_name(callback: types.CallbackQuery, state):
    keyboard = InlineKeyboardMarkup()
    user = callback.data.split(sep='%')[1]
    async with state.proxy() as data:
        data['user_db_id'] = user
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{user}-1"))

    await callback.message.edit_text("Укажите ФИО резидента:", reply_markup=keyboard)
    await EditUser.full_name.set()


async def edit_user_full_name_set(message: types.Message, state):
    pattern = r"^[А-Я][а-я]+\s[А-Я][а-я]+\s[А-Я][а-я]+$"
    if not re.match(pattern, message.text):
        await message.answer('Вы указали неправильно ФИО.\n Пример: Иванов Иван Иванович')
        await EditUser.full_name.set()
        return
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{data['user_db_id']}-1"))

        users.update_one({'_id': ObjectId(data['user_db_id'])}, {'$set': {'full_name': message.text}})

        await message.answer("ФИО изменено:", reply_markup=keyboard)
        await send_log(f"Администратор[{message.from_user.id}]: Пользователь[{data['user_db_id']}] <- {message.text}")
    await Menu.main.set()

async def edit_user_phone_number(callback: types.CallbackQuery, state):
    keyboard = InlineKeyboardMarkup()
    user = callback.data.split(sep='%')[1]
    async with state.proxy() as data:
        data['user_db_id'] = user
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{user}-1"))

    await callback.message.edit_text("Укажите номер телефона резидента, первая цифра 7:", reply_markup=keyboard)
    await EditUser.phone_number.set()


async def edit_user_phone_number_set(message: types.Message, state):
    pattern = r"^7\d{10}$"
    if not re.match(pattern, message.text):
        await message.answer('Вы указали неправильный номер первая цифра 7, всего 11 цифр.\n Пример: 79158252110')
        await EditUser.phone_number.set()
        return
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{data['user_db_id']}-1"))

        users.update_one({'_id': ObjectId(data['user_db_id'])}, {'$set': {'phone_number': message.text}})

        await message.answer("Номер изменен:", reply_markup=keyboard)
        await send_log(f"Администратор[{message.from_user.id}]: Пользователь[{data['user_db_id']}] <- {message.text}")
    await Menu.main.set()

async def edit_user_description(callback: types.CallbackQuery, state):
    keyboard = InlineKeyboardMarkup()
    user = callback.data.split(sep='%')[1]
    async with state.proxy() as data:
        data['user_db_id'] = user
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{user}-1"))

    await callback.message.edit_text("Укажите описание резидента:", reply_markup=keyboard)
    await EditUser.description.set()


async def edit_user_description_set(message: types.Message, state):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{data['user_db_id']}-1"))

        users.update_one({'_id': ObjectId(data['user_db_id'])}, {'$set': {'description': message.text}})

        await message.answer("Описание изменено:", reply_markup=keyboard)
        await send_log(f"Администратор[{message.from_user.id}]: Пользователь[{data['user_db_id']}] <- {message.text}")
    await Menu.main.set()


async def edit_user_company_name(callback: types.CallbackQuery, state):
    keyboard = InlineKeyboardMarkup()
    user = callback.data.split(sep='%')[1]
    async with state.proxy() as data:
        data['user_db_id'] = user
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{user}-1"))

        await callback.message.edit_text("Укажите название компании:", reply_markup=keyboard)


async def edit_user_company_name_set(message: types.Message, state):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{data['user_db_id']}-1"))

        users.update_one({'_id': ObjectId(data['user_db_id'])}, {'$set': {'company_name': message.text}})

        await message.answer("Название компании изменено:", reply_markup=keyboard)
        await send_log(f"Администратор[{message.from_user.id}]: Пользователь[{data['user_db_id']}] <- {message.text}")
    await Menu.main.set()


async def edit_user_company_site(callback: types.CallbackQuery, state):
    keyboard = InlineKeyboardMarkup()
    user = callback.data.split(sep='%')[1]
    async with state.proxy() as data:
        data['user_db_id'] = user
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{user}-0"))

    await callback.message.edit_text("Укажите новую ссылку:", reply_markup=keyboard)
    await EditUser.company_site.set()


async def edit_user_company_site_set(message: types.Message, state):
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    if not re.match(url_pattern, message.text):
        await message.answer('Вы указали неправильную ссылку, она должна начинаться с http:// или https://.')
        await EditUser.company_site.set()
        return
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{data['user_db_id']}-1"))

        users.update_one({'_id': ObjectId(data['user_db_id'])}, {'$set': {'company_site': message.text}})

        await message.answer("Cылка изменена:", reply_markup=keyboard)
        await send_log(f"Администратор[{message.from_user.id}]: Пользователь[{data['user_db_id']}] <- {message.text}")
    await Menu.main.set()


async def edit_user_image(callback: types.CallbackQuery, state):
    keyboard = InlineKeyboardMarkup()
    user = callback.data.split(sep='%')[1]
    async with state.proxy() as data:
        data['user_db_id'] = user
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{user}-1"))

    await callback.message.edit_text("Пришлите картинку:", reply_markup=keyboard)

    await EditUser.image.set()


async def edit_user_image_set(message: types.Message, state):
    keyboard = InlineKeyboardMarkup()
    photo_sizes = message.photo
    # Получаем последнюю фотографию
    last_photo = photo_sizes[-1]
    async with state.proxy() as data:
        user_db_id = data['user_db_id']
        user = users.find_one({'_id': ObjectId(user_db_id)})

        file = await bot.get_file(last_photo.file_id)
        file_name = f'{last_photo.file_id}.jpg'
        await bot.download_file(file.file_path, destination=f"{DIR}/users/{user['user_id']}/{file_name}")
        image = user['image']
        try:
            os.remove(image)
        except:
            pass
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{data['user_db_id']}-1"))

        users.update_one({'_id': ObjectId(data['user_db_id'])}, {'$set': {'image': f"{DIR}/users/{user['user_id']}/{file_name}"}})

        await message.answer("Фото изменено:", reply_markup=keyboard)
        await send_log(f"Администратор[{message.from_user.id}]: Пользователь[{data['user_db_id']}] <- Фото")
    await Menu.main.set()


async def delete_user(callback: types.CallbackQuery, state):
    keyboard = InlineKeyboardMarkup()
    user = callback.data.split(sep='%')[1]
    async with state.proxy() as data:
        data['user_db_id'] = user
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{user}-0"))
        user_id = users.find_one({'_id': ObjectId(user)})['user_id']

    await callback.message.edit_text(f"Напишите {user_id} для подтверждения:", reply_markup=keyboard)
    await EditUser.delete.set()


async def delete_user_set(message: types.Message, state):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=f"rusers_list-y-{data['user_db_id']}-1"))
        user = users.find_one({'_id': ObjectId(data['user_db_id'])})
        if int(message.text) == user['user_id']:
            users.delete_one({'_id': ObjectId(data['user_db_id'])})
            await send_log(f"Администратор[{message.from_user.id}]: Пользователь[{data['user_db_id']}] -> Удалить")
        else:
            pass
        await state.finish()
    message.text = '/start'
    await handlers.main_handlers.start(message)