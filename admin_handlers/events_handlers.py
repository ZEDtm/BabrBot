import logging
import re
from datetime import datetime
from bson import ObjectId

from admin_handlers import archive_handlers
from config import dp, bot
from database.collection import events, archive, users
from database.models import Event
from modules.list_collection import ListEvents
from modules.bot_states import AdminNewEvent, AdminEditEvent
from modules.bot_calendar_module import SelectDays, NewEventCalendar, SelectTime, AdminEventCalendar
from aiogram import executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from handlers import main_handlers, registration_handlers, profile_handlers, calendar_handlers, residents_handlers
from modules.logger import send_log

logging.basicConfig(level=logging.INFO)


async def list_events_public(callback: types.CallbackQuery, state: FSMContext):
    list_collection = await ListEvents().start_collection(events.find())
    await callback.message.edit_text('Список мероприятий:', reply_markup=list_collection)


async def list_events_select(callback: types.CallbackQuery, state: FSMContext):
    select, event_id, current_page = await ListEvents().processing_selection(callback, callback.data, events.find())
    if event_id:
        await event_handle(callback, state, event_id, current_page=current_page)


async def admin_calendar(callback: types.CallbackQuery, state: FSMContext):
    calendar = await AdminEventCalendar(events.find(), archive.find()).start_calendar()
    await callback.message.edit_text('Календарь мероприятий', reply_markup=calendar)


async def admin_calendar_select(callback: types.CallbackQuery, state: FSMContext):
    event, date, act_id = await AdminEventCalendar(events.find(), archive.find()).process_selection(callback, callback.data)
    if act_id and event:
        await event_handle(callback, state, act_id, date=date)
    elif act_id:
        await archive_handlers.archive_handle(callback, state, archive_id=act_id, date=date)


async def event_handle(callback: types.CallbackQuery, state: FSMContext, event_id: str, current_page: int = None, date: dict = None):
    event = events.find_one({'_id': ObjectId(event_id)})
    keyboard = InlineKeyboardMarkup(row_width=1)
    if event['public']:
        keyboard.add(InlineKeyboardButton(text='Отменить', callback_data=f"public-event-{event_id}"))
    else:
        keyboard.add(InlineKeyboardButton(text='Подтвердить и оповестить', callback_data=f"public-event%{event_id}"))
    keyboard.add(InlineKeyboardButton(text='Изменить название', callback_data=f"event-edit-name%{event_id}"),
                 InlineKeyboardButton(text='Изменить описание', callback_data=f"event-edit-description%{event_id}"),
                 InlineKeyboardButton(text='Изменить стоимость', callback_data=f"event-edit-price%{event_id}"),
                 InlineKeyboardButton(text='Изменить услуги', callback_data=f"event-edit-services%{event_id}"),
                 InlineKeyboardButton(text='Изменить дату и длительность', callback_data=f"event-edit-date%{event_id}"))
    if current_page:
        keyboard.add(InlineKeyboardButton(text='Назад', callback_data=f"events_list-n-{current_page}"))
    if date:
        keyboard.add(InlineKeyboardButton(text='Назад', callback_data=f"admin_event_calendar:CURRENT:{date['year']}:{date['month']}:{date['day']}"))
    if not event['public']:
        keyboard.add(InlineKeyboardButton(text='В черновик', callback_data=f"menu"))

    text = f"[Дата и время]: {datetime(int(event['year']), int(event['month']), int(event['day']), int(event['hour']), int(event['minute']))}\n"
    text += f"[Название]: {event['name']}\n" \
            f"[Описание]:\n{event['description']}\n" \
            f"[Стоимость посещения]: {event['price']}руб.\n" \
            f"[Длительность]: {event['duration']}дн.\n" \
            f"[Услуги]:\n"
    for service, price in zip(event['service_description'], event['service_price']):
        text += f" - {service}: {price}руб.\n"
    text += f"[Участников]: {len(event['users'])} (резид.)"
    await callback.message.edit_text(text, reply_markup=keyboard)


async def publication_event(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one({'_id': ObjectId(event_id)})
    events.update_one(event, {'$set': {'public': True}})
    count_send = 0
    count_blocked = 0

    for user in users.find():
        await callback.message.edit_text(f"Рассылка:\nУспешно: {count_send}\nЗаблокировано: {count_blocked}")
        try:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text='👥 Посмотреть', callback_data=f"event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))
            await bot.send_message(user['user_id'], f"🎉 Вы готовы к участию в новом мероприятии - {event['name']}?\n👇 Присоединитесь!", reply_markup=keyboard)
            count_send += 1
        except:
            count_blocked += 1
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                 InlineKeyboardButton(text='Назад', callback_data=f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))
    await callback.message.edit_reply_markup(reply_markup=keyboard)

    await send_log(f"Черновик[{event['name']}] -> Мероприятия")


async def event_edit_name(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one(ObjectId(event_id))

    await AdminEditEvent.event_name.set()
    async with state.proxy() as data:
        data['event_id'] = event_id
        data['callback_data'] = f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                 InlineKeyboardButton('Назад', callback_data=f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))

    await callback.message.edit_text(f"Мероприятие {event['name']}\n\nВведите новое название:", reply_markup=keyboard)


async def event_edit_name_set(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        event = events.find_one(ObjectId(data['event_id']))
        events.update_one(event, {'$set': {'name': message.text}})
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=data['callback_data']))
    await message.answer('Название изменено', reply_markup=keyboard)

    await send_log(f"Мероприятие[{event['name']}]: Название <- {message.text}")


async def event_edit_description(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one(ObjectId(event_id))

    await AdminEditEvent.event_description.set()
    async with state.proxy() as data:
        data['event_id'] = event_id
        data['callback_data'] = f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                 InlineKeyboardButton('Назад', callback_data=f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))

    await callback.message.edit_text(f"Описание\n {event['description']}\n\nВведите новое описание:", reply_markup=keyboard)


async def event_edit_description_set(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        event = events.find_one(ObjectId(data['event_id']))
        events.update_one(event, {'$set': {'description': message.text}})
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=data['callback_data']))
    await message.answer('Описание изменено', reply_markup=keyboard)

    await send_log(f"Мероприятие[{event['name']}]: Описание <- {message.text}")


async def event_edit_price(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one(ObjectId(event_id))

    await AdminEditEvent.event_price.set()
    async with state.proxy() as data:
        data['event_id'] = event_id
        data['callback_data'] = f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                 InlineKeyboardButton('Назад', callback_data=f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))

    await callback.message.edit_text(f"Стоимость\n {event['price']}\n\nВведите новую стоимость в рублях (без дополнительных услуг):", reply_markup=keyboard)


async def event_edit_price_set(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        event = events.find_one(ObjectId(data['event_id']))
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=data['callback_data']))
        if not re.match(r'^\d+$', message.text):
            await AdminEditEvent.event_price.set()
            await message.answer('Введите новую стоимость в рублях (без дополнительных услуг):', reply_markup=keyboard)
            return
    events.update_one(event, {'$set': {'price': int(message.text)}})
    await message.answer('Стоимость изменена', reply_markup=keyboard)

    await send_log(f"Мероприятие[{event['name']}]: Стоимость <- {message.text}")


async def event_edit_services(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one(ObjectId(event_id))
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='Добавить', callback_data=f"event-edit-add-service%{event_id}"))
    await AdminEditEvent.event_services.set()
    async with state.proxy() as data:
        data['callback_data'] = f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"
        for service, price in zip(event['service_description'], event['service_price']):
            keyboard.add(InlineKeyboardButton(text=f"{service}: {price}", callback_data=f"event-edit-service%{event_id}%{event['service_description'].index(service)}"))

    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                 InlineKeyboardButton('Назад', callback_data=f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))

    await callback.message.edit_text(f"Выберите действие:", reply_markup=keyboard)


async def event_edit_service_description(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    service_index = callback.data.split(sep='%')[2]

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='Удалить', callback_data=f"event-delete-service%{event_id}%{service_index}"))
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=data['callback_data']))
        data['event_id'] = event_id
        data['service_index'] = service_index

    await AdminEditEvent.event_service_description.set()
    await callback.message.edit_text('Введите новое описание услуги:', reply_markup=keyboard)


async def event_edit_service_description_set(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(
            InlineKeyboardButton(text='Удалить', callback_data=f"event-delete-service%{data['event_id']}%{data['service_index']}"))
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=data['callback_data']))
        events.update_one({'_id': ObjectId(data['event_id'])}, {'$set': {f'service_description.{data["service_index"]}': message.text}})
        await send_log(f"Мероприятие[{data['event_id']}]: Изменение услуги описание <- {message.text}")
    await AdminEditEvent.event_service_price.set()
    await message.answer('Введите новую стоимость услуги:', reply_markup=keyboard)


async def event_edit_service_price_set(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='Удалить', callback_data=f"event-delete-service%{data['event_id']}%{data['service_index']}"))
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=data['callback_data']))
        if not re.match(r'^\d+$', message.text):
            await AdminEditEvent.event_service_price.set()
            await message.answer('Введите новую стоимость услуги:', reply_markup=keyboard)
            return
        events.update_one({'_id': ObjectId(data['event_id'])}, {'$set': {f'service_price.{data["service_index"]}': message.text}})
        await send_log(f"Мероприятие[{data['event_id']}]: Изменение услуги стоимость <- {message.text}")
    await message.answer('Услуга изменена', reply_markup=keyboard)


async def event_edit_service_add(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        data['event_id'] = event_id
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=data['callback_data']))
    await AdminEditEvent.event_new_service_description.set()
    await callback.message.edit_text('Введите описание услуги:', reply_markup=keyboard)


async def event_edit_service_add_description(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        data['service_description'] = message.text
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=data['callback_data']))
    await AdminEditEvent.event_new_service_price.set()
    await message.answer('Введите стоимость услуги:', reply_markup=keyboard)


async def event_edit_service_add_price(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=data['callback_data']))
        if not re.match(r'^\d+$', message.text):
            await AdminEditEvent.event_new_service_price.set()
            await message.answer('Введите стоимость услуги:', reply_markup=keyboard)
            return
        events.update_one({'_id': ObjectId(data['event_id'])}, {'$push': {'service_description': data['service_description']}})
        events.update_one({'_id': ObjectId(data['event_id'])}, {'$push': {'service_price': message.text}})

        await send_log(f"Мероприятие[{data['event_id']}]: Услуги <- {data['service_description']}")
    await message.answer('Услуга добавлена', reply_markup=keyboard)


async def event_edit_service_delete(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    service_index = callback.data.split(sep='%')[2]
    event = events.find_one(ObjectId(event_id))
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                     InlineKeyboardButton(text='Назад', callback_data=data['callback_data']))
    events.update_one({'_id': ObjectId(event_id)}, {'$pull': {'service_description': event['service_description'][int(service_index)]}})
    events.update_one({'_id': ObjectId(event_id)}, {'$pull': {'service_price': event['service_price'][int(service_index)]}})
    await send_log(f"Мероприятие[{event_id}]: Услуга[{event['service_description'][int(service_index)]}] -> Удалена")
    await callback.message.edit_text('Услуга удалена', reply_markup=keyboard)