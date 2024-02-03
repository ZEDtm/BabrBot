import datetime
import re

from bson import ObjectId
from datetime import datetime


import admin_handlers.events_handlers
from config import bot, DIR
from database.collection import events, archive
from database.models import Event
from modules.bot_states import AdminNewEvent, AdminArchive
from modules.list_collection import ListArchive
from modules.logger import send_log

from aiogram import executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from handlers import main_handlers, registration_handlers, profile_handlers, calendar_handlers, residents_handlers


async def archive_list(callback: types.CallbackQuery, state: FSMContext):
    await AdminArchive.list.set()
    keyboard = await ListArchive().start_collection(archive.find())
    await callback.message.edit_text('🗄 Архив: список', reply_markup=keyboard)


async def archive_list_select(callback: types.CallbackQuery, state: FSMContext):
    select, archive_id, current_page = await ListArchive().processing_selection(callback, callback.data, archive.find())
    if archive_id:
        await archive_handle(callback, state, archive_id=archive_id, current_page=current_page)


async def archive_handle(callback: types.CallbackQuery, state: FSMContext, archive_id: str, current_page: int = None, date: dict = None):
    await AdminArchive.list.set()
    arch = archive.find_one({'_id': ObjectId(archive_id)})

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='📷 Добавить фото', callback_data=f"archive-add-images%{archive_id}"))
    keyboard.add(InlineKeyboardButton(text='🎥 Добавить видео', callback_data=f"archive-add-video%{archive_id}"))
    keyboard.add(InlineKeyboardButton(text='☁ Добавить ссылку', callback_data=f"archive-add-link%{archive_id}"))

    if current_page:
        async with state.proxy() as data:
            data['callback_data'] = f"archive_list-y-{archive_id}-{current_page}"
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data=f"menu"),
                     InlineKeyboardButton(text='↩ Назад', callback_data=f"archive_list-n-{current_page}"))
    if date:
        async with state.proxy() as data:
            data['callback_data'] = f"admin_event_calendar:archive:{date['year']}:{date['month']}:{date['day']}:{archive_id}"
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data=f"menu"),
                     InlineKeyboardButton(text='↩ Назад', callback_data=f"admin_event_calendar:CURRENT:{date['year']}:{date['month']}:{date['day']}"))

    date_format = datetime(int(arch['year']), int(arch['month']), int(arch['day'])).strftime('%d.%m.%Y')
    text = f"📆 Дата: {date_format}\n🗄 Название: {arch['name']}\n\n" \
           f"📖 Описание:\n{arch['description']}\n"
    await callback.message.edit_text(text, reply_markup=keyboard)


async def archive_add_images(callback: types.CallbackQuery, state: FSMContext):
    await AdminArchive.add_images.set()
    keyboard = InlineKeyboardMarkup()

    async with state.proxy() as data:
        data['archive_id'] = callback.data.split(sep='%')[1]

        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data=f"menu"),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))

    await callback.message.edit_text('📷 Пришлите фотографии:', reply_markup=keyboard)


async def archive_add_images_download(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()

    photo_sizes = message.photo
    # Получаем последнюю фотографию
    last_photo = photo_sizes[-1]
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data=f"menu"),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))

        file = await bot.get_file(last_photo.file_id)
        file_name = f'{last_photo.file_id}.jpg'
        await bot.download_file(file.file_path, destination=f"{DIR}/archive/{data['archive_id']}/images/{file_name}")
    await message.reply('💾 Успешно загружено', reply_markup=keyboard)


async def archive_add_video(callback: types.CallbackQuery, state: FSMContext):
    await AdminArchive.add_video.set()
    keyboard = InlineKeyboardMarkup()

    async with state.proxy() as data:
        data['archive_id'] = callback.data.split(sep='%')[1]

        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data=f"menu"),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))

    await callback.message.edit_text('🎥 Пришлите видео:', reply_markup=keyboard)


async def archive_add_video_download(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()

    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data=f"menu"),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))

    file_id = message.video.file_id
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, f"{DIR}/archive/{data['archive_id']}/video/{file_id}.mp4")
    await message.reply('💾 Успешно загружено', reply_markup=keyboard)


async def archive_add_link(callback: types.CallbackQuery, state: FSMContext):
    await AdminArchive.add_link.set()
    keyboard = InlineKeyboardMarkup()

    async with state.proxy() as data:
        data['archive_id'] = callback.data.split(sep='%')[1]
        print(data['callback_data'])

        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data=f"menu"),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))

    await callback.message.edit_text('☁ Пришлите ссылку:', reply_markup=keyboard)


async def archive_add_link_set(message: types.Message, state: FSMContext):
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    if not re.match(url_pattern, message.text):
        await AdminArchive.add_link.set()
        await message.answer('Вы указали неправильную ссылку, она должна начинаться с http:// или https://.')
    keyboard = InlineKeyboardMarkup()

    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data=f"menu"),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))

        archive.update_one({'_id': ObjectId(data['archive_id'])},  {"$set": {'link': message.text}})
    await AdminArchive.list.set()
    await message.answer('💾 Ссылка обновлена', reply_markup=keyboard)