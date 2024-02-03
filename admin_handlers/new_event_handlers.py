import re

import admin_handlers.events_handlers
from database.collection import events
from database.models import Event
from modules.bot_states import AdminNewEvent
from modules.bot_calendar_module import SelectDays, NewEventCalendar, SelectTime
from modules.logger import send_log

from aiogram import executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from handlers import main_handlers, registration_handlers, profile_handlers, calendar_handlers, residents_handlers


async def new_event_handler(callback: types.CallbackQuery, state: FSMContext):
    await AdminNewEvent.event_long.set()

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(text='⌛ Длинное', callback_data='new_event_long'),
                 InlineKeyboardButton(text='⏳ Короткое', callback_data='new_event_short'))

    await callback.message.edit_text('⏱ Установите тип мероприятия:', reply_markup=keyboard)


async def new_event_duration(callback: types.CallbackQuery, state: FSMContext):
    await AdminNewEvent.event_duration.set()
    async with state.proxy() as data:
        data['long'] = True if callback.data == 'new_event_long' else False
    if callback.data == 'new_event_short':
        async with state.proxy() as data:
            data['duration'] = 1
        await AdminNewEvent.event_name.set()
        await callback.message.edit_text('✏ Введите короткое название мероприятия:')
    else:
        days = await SelectDays().start_days()
        await callback.message.edit_text('⏳ Выберите длительность мероприятия', reply_markup=days)


async def new_event_name(callback: types.CallbackQuery, state: FSMContext):
    select, day = await SelectDays().process_selection(callback, callback.data)
    if select:
        await AdminNewEvent.event_name.set()
        async with state.proxy() as data:
            data['duration'] = day

        await callback.message.edit_text('✏ Введите короткое название мероприятия:')


async def new_event_description(message: types.Message, state: FSMContext):
    await AdminNewEvent.event_description.set()
    async with state.proxy() as data:
        data['name'] = message.text

    await message.answer('✏ Введите описание мероприятия:')


async def new_event_price(message: types.Message, state: FSMContext):
    await AdminNewEvent.event_services.set()
    async with state.proxy() as data:
        data['description'] = message.text

    await message.answer('✏ Введите стоимость посещения мероприятия:')


async def new_event_services(message: types.Message, state: FSMContext):
    if not re.match(r'^\d+$', message.text):
        await AdminNewEvent.event_services.set()
        await message.answer('✏ Введите стоимость посещения мероприятия:')
    else:
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton(text='📑 Добавить услугу', callback_data='add_event_service'),
                     InlineKeyboardButton(text='🗑 Отменить мероприятие', callback_data='menu'),
                     InlineKeyboardButton(text='📝 Создать мероприятие', callback_data='add_event_set_calendar'))

        async with state.proxy() as data:
            data['price'] = message.text
            data['service_description'] = []
            data['service_price'] = []
            text = f"📝 Информацию о мероприятии:\n\n" \
                   f" ✨ Название:\n {data['name']}\n\n" \
                   f" 📖 Описание:\n {data['description']}\n\n" \
                   f" ⏱ Длительность: {data['duration']} дн.\n" \
                   f" 💰 Стоимость: {data['price']} руб.\n"
            await message.answer(text, reply_markup=keyboard)


async def new_event_add_service(callback: types.CallbackQuery, state: FSMContext):
    await AdminNewEvent.event_services_new.set()
    await callback.message.edit_text('✏ Введите описание услуги:')


async def new_event_add_service_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['service_description'].append(message.text)
    await AdminNewEvent.event_add.set()
    await message.answer('✏ Введите стоимость услуги:')


async def new_event_add(message: types.Message, state: FSMContext):
    if not re.match(r'^\d+$', message.text):
        await AdminNewEvent.event_services_new.set()
        await message.answer('✏ Введите стоимость услуги:')
    else:
        await AdminNewEvent.event_services.set()

        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton(text='📑 Добавить услугу', callback_data='add_event_service'),
                     InlineKeyboardButton(text='🗑 Отменить мероприятие', callback_data='menu'),
                     InlineKeyboardButton(text='📝 Создать мероприятие', callback_data='add_event_set_calendar'))

        async with state.proxy() as data:
            data['service_price'].append(message.text)
            text = f"📝 Информацию о мероприятии:\n\n" \
                   f" ✨ Название:\n {data['name']}\n\n" \
                   f" 📖 Описание:\n {data['description']}\n\n" \
                   f" ⏱ Длительность: {data['duration']} дн.\n" \
                   f" 💰 Стоимость: {data['price']} руб.\n"
            for service, price in zip(data['service_description'], data['service_price']):
                text += f'📑 Услуга: {service}: {price}₽\n'

        await message.answer(text, reply_markup=keyboard)


async def add_event_set_calendar(callback: types.CallbackQuery, state: FSMContext):
    calendar = await NewEventCalendar(events.find()).start_calendar()
    await callback.message.edit_text('📆 Установите дату начала мероприятия:', reply_markup=calendar)


async def add_event_set_calendar_process(callback: types.CallbackQuery, state: FSMContext):
    select, date = await NewEventCalendar(events.find()).process_selection(callback, callback.data)
    if date:
        select_time = await SelectTime().start_time()
        async with state.proxy() as data:
            data['year'] = date['year']
            data['month'] = date['month']
            data['day'] = date['day']
        await callback.message.edit_text(f"📆 Дата: {date['day']}:{date['month']}:{date['year']}\n"
                                         f"🕛 Установите время начала мероприятия:", reply_markup=select_time)


async def add_event_set_time(callback: types.CallbackQuery, state: FSMContext):
    select, time = await SelectTime().process_selection(callback, callback.data)
    if time:
        await AdminNewEvent.event_add.set()
        async with state.proxy() as data:
            event = Event(data['name'],
                          data['description'],
                          data['price'],
                          data['service_description'],
                          data['service_price'],
                          data['duration'],
                          data['year'],
                          data['month'],
                          data['day'],
                          time['hour'],
                          time['minute'],
                          False,
                          [])
            new_event = events.insert_one(event())
        await admin_handlers.events_handlers.event_handle(callback, state, str(new_event.inserted_id))

        await send_log(f"Новое мероприятие [{data['name']}] -> Черновик")

