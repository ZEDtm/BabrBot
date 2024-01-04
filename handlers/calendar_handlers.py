import logging
from datetime import datetime, timedelta
from os import path, listdir

from database.collection import events, find_event, archive
from modules.bot_states import Menu
from config import DIR, bot
from bson import ObjectId

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext

from modules.calendar_module import EventCalendar


logging.basicConfig(level=logging.INFO)


async def events_calendar_handler(callback: types.CallbackQuery, state: FSMContext):
    await Menu.calendar.set()
    user_id = callback.message.chat.id
    calendar = await EventCalendar(events.find({'public': True}), archive.find(), user_id).start_calendar()
    await callback.message.edit_text('Календарь:\n'
                                     ' 🟢 - Вы участвуете в мероприятии\n'
                                     ' 🟡 - Вы не участвуете в мероприятии\n'
                                     ' 🟠 - архив, Вы участвовали\n'
                                     ' 🔴 - архив, Вы не участвовали', reply_markup=calendar)


async def event_calendar_selected_handler(callback: types.CallbackQuery, state: FSMContext):
    await Menu.calendar.set()
    user_id = callback.message.chat.id
    select, date, act_id = await EventCalendar(events.find({'public': True}), archive.find(), user_id).process_selection(callback, callback.data)
    if select and act_id:
        await event_selected(callback, state, act_id)
    elif act_id:
        await archive_selected(callback, state, act_id)


async def event_selected(callback: types.CallbackQuery, state: FSMContext, event_id):
    print(callback.data)
    await Menu.calendar.set()
    event = events.find_one({'_id': ObjectId(event_id)})
    keyboard = InlineKeyboardMarkup()
    if str(callback.message.chat.id) in event['users']:
        pass
    else:
        keyboard.add(InlineKeyboardButton(text='Учавствовать', callback_data=f'subscribe-event%{event_id}'))

    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                 InlineKeyboardButton(text='Назад', callback_data=f"event_calendar:CURRENT:{event['year']}:{event['month']}:{event['day']}: "))

    start_event = datetime(int(event['year']), int(event['month']), int(event['day']), int(event['hour']), int(event['minute']))
    end_event = start_event + timedelta(days=int(event['duration']))
    text = f"Мероприятие [{event['name']}]\n" \
           f"[{start_event.strftime('%Y.%m.%d')}->{end_event.strftime('%Y.%m.%d')}]\n\n" \
           f"{event['description']}\n\n" \
           f"Начало: {start_event.strftime('%H:%M')}\n" \
           f"Участников: {len(event['users'])}\n" \
           f"Стоимость: {event['price']}₽\n"
    for service, price in zip(event['service_description'], event['service_price']):
        text += f"*{service}: {price}₽\n"
    await callback.message.edit_text(text, reply_markup=keyboard)




async def archive_selected(callback: types.CallbackQuery, state: FSMContext, archive_id, edit=True):
    arch = archive.find_one({'_id': ObjectId(archive_id)})
    await Menu.archive.set()
    async with state.proxy() as data:
        data['callback_data'] = callback.data

    keyboard = InlineKeyboardMarkup()
    if len(arch['link']) > 0:
        keyboard.add(InlineKeyboardButton(text='Облако', url=arch['link']))
    if path.isdir(f"{DIR}/archive/{archive_id}/images"):
        keyboard.add(InlineKeyboardButton(text='Посмотреть фото', callback_data=f'archive-images%{archive_id}'))
    if path.isdir(f"{DIR}/archive/{archive_id}/video"):
        keyboard.add(InlineKeyboardButton(text='Посмотреть видео', callback_data=f'archive-video%{archive_id}'))

    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                 InlineKeyboardButton(text='Назад', callback_data=f"event_calendar:CURRENT:{arch['year']}:{arch['month']}:{arch['day']}: "))

    date_format = datetime(int(arch['year']), int(arch['month']), int(arch['day'])).strftime('%Y.%m.%d')

    text = f"Архив [{date_format}]\n" \
           f"--{arch['name']}--\n" \
           f"{arch['description']}\n" \
           f"Участников: {len(arch['users'])}"
    if edit:
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.message.answer(text, reply_markup=keyboard)


async def archive_selected_images(callback: types.CallbackQuery, state: FSMContext):
    await types.ChatActions.upload_photo()

    archive_id = callback.data.split(sep='%')[1]

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'))
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='Назад', callback_data=data['callback_data']))

    media = types.MediaGroup()
    files = listdir(f"{DIR}/archive/{archive_id}/images")
    for file in files:
        media.attach_photo(types.InputFile(f"{DIR}/archive/{archive_id}/images/{file}"))

    await callback.message.answer_media_group(media=media)
    await archive_selected(callback, state, archive_id, False)
    await callback.message.delete()


async def archive_selected_video(callback: types.CallbackQuery, state: FSMContext):
    await types.ChatActions.upload_video()

    archive_id = callback.data.split(sep='%')[1]

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'))
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='Назад', callback_data=data['callback_data']))

    media = types.MediaGroup()
    files = listdir(f"{DIR}/archive/{archive_id}/video")
    for file in files:
        media.attach_video(types.InputFile(f"{DIR}/archive/{archive_id}/video/{file}"))

    await callback.message.answer_media_group(media=media)
    await archive_selected(callback, state, archive_id, False)
    await callback.message.delete()