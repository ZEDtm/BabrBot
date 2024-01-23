import logging
import re
from datetime import datetime
from bson import ObjectId

from admin_handlers import archive_handlers
from config import bot
from database.collection import events, archive, users, payments
from modules.list_collection import ListEvents, ListUsersInEvent
from modules.bot_states import AdminEditEvent, UsersInEvent
from modules.bot_calendar_module import SelectDays, NewEventCalendar, SelectTime, AdminEventCalendar
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from modules.logger import send_log



async def list_events_public(callback: types.CallbackQuery, state: FSMContext):
    list_collection = await ListEvents().start_collection(events.find())
    await callback.message.edit_text('✨ Список: мероприятия', reply_markup=list_collection)


async def list_events_select(callback: types.CallbackQuery, state: FSMContext):
    select, event_id, current_page = await ListEvents().processing_selection(callback, callback.data, events.find())
    if event_id:
        await event_handle(callback, state, event_id, current_page=current_page)


async def admin_calendar(callback: types.CallbackQuery, state: FSMContext):
    calendar = await AdminEventCalendar(events.find(), archive.find()).start_calendar()
    await callback.message.edit_text('🗓 Календарь: Управление: \n\n🟢 - Опубликовано\n🟡 - Черновик\n🔴 - Архив', reply_markup=calendar)


async def admin_calendar_select(callback: types.CallbackQuery, state: FSMContext):
    event, date, act_id = await AdminEventCalendar(events.find(), archive.find()).process_selection(callback,
                                                                                                    callback.data)
    if act_id and event:
        await event_handle(callback, state, act_id, date=date)
    elif act_id:
        await archive_handlers.archive_handle(callback, state, archive_id=act_id, date=date)


async def event_handle(callback: types.CallbackQuery, state: FSMContext, event_id: str, current_page: int = None,
                       date: dict = None):
    event = events.find_one({'_id': ObjectId(event_id)})
    keyboard = InlineKeyboardMarkup()
    if event['public']:
        keyboard.add(InlineKeyboardButton(text='❎ Отменить', callback_data=f"cancel-event%{event_id}"))
    else:
        keyboard.add(InlineKeyboardButton(text='✅ Подтвердить и оповестить', callback_data=f"public-event%{event_id}"))
    keyboard.add(InlineKeyboardButton(text='✏ Название', callback_data=f"event-edit-name%{event_id}"),
                 InlineKeyboardButton(text='✏ Описание', callback_data=f"event-edit-description%{event_id}"))
    keyboard.add(InlineKeyboardButton(text='✏ Стоимость', callback_data=f"event-edit-price%{event_id}"),
                 InlineKeyboardButton(text='✏ Услуги', callback_data=f"event-edit-services%{event_id}"))
    keyboard.add(InlineKeyboardButton(text='✏ Время, дата, длительность', callback_data=f"event-edit-date%{event_id}"))
    keyboard.add(InlineKeyboardButton(text='❌ Удалить', callback_data=f"event-delete%{event_id}"),
                 InlineKeyboardButton(text='👥 Участники', callback_data=f"event-users%{event_id}"),)
    if current_page:
        keyboard.add(InlineKeyboardButton(text='🏠 В Меню', callback_data=f"menu"),
                     InlineKeyboardButton(text='↩ Назад', callback_data=f"events_list-n-{current_page}"))
    else:
        keyboard.add(InlineKeyboardButton(text='🏠 В Меню', callback_data=f"menu"),
                     InlineKeyboardButton(text='↩ Назад',
                                          callback_data=f"admin_event_calendar:CURRENT:{event['year']}:{event['month']}:{event['day']}"))

    text = f"📆 Дата и время: {datetime(int(event['year']), int(event['month']), int(event['day']), int(event['hour']), int(event['minute']))}\n"
    text += f"📝 Название:\n {event['name']}\n\n" \
            f"📖 Описание:\n{event['description']}\n\n" \
            f"💰 Стоимость посещения: {event['price']}₽\n" \
            f"⏳ Длительность: {event['duration']} дн\n" \
            f"📑 Услуги:\n"
    for service, price in zip(event['service_description'], event['service_price']):
        text += f" - {service}: {price}₽\n"
    text += f"\n👥 Участников: {len(event['users'])}"
    await callback.message.edit_text(text, reply_markup=keyboard)


async def publication_event(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one({'_id': ObjectId(event_id)})
    events.update_one(event, {'$set': {'public': True}})
    count_send = 0
    count_blocked = 0

    for user in users.find():
        await callback.message.edit_text(f"📤 Рассылка:\n 👍 Успешно: {count_send}\n 👎 Заблокировано: {count_blocked}")
        try:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text='👀 Посмотреть',
                                              callback_data=f"event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))
            await bot.send_message(user['user_id'],
                                   f"🎉 Вы готовы к участию в новом мероприятии - {event['name']}?\n👇 Присоединитесь!",
                                   reply_markup=keyboard)
            count_send += 1
        except:
            count_blocked += 1
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton(text='↩ Назад',
                                      callback_data=f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))
    await callback.message.edit_reply_markup(reply_markup=keyboard)

    await send_log(f"Черновик[{event['name']}] -> Мероприятия")


async def event_cancel(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one(ObjectId(event_id))
    events.update_one(event, {'$set': {'public': False}})

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton(text='↩ Назад', callback_data=f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))
    await callback.message.edit_text('😖 Мероприятие отменено', reply_markup=keyboard)

    await send_log(f"Мероприятие[{event['name']}] -> Черновик")


async def event_edit_name(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one(ObjectId(event_id))

    await AdminEditEvent.event_name.set()
    async with state.proxy() as data:
        data['event_id'] = event_id
        data['callback_data'] = f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton('↩ Назад',
                                      callback_data=f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))

    await callback.message.edit_text(f"✨ Мероприятие {event['name']}\n\n✏ Введите новое название:", reply_markup=keyboard)


async def event_edit_name_set(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        event = events.find_one(ObjectId(data['event_id']))
        events.update_one(event, {'$set': {'name': message.text}})
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))
    await message.answer('📝 Название изменено', reply_markup=keyboard)

    await send_log(f"Мероприятие[{event['name']}]: Название <- {message.text}")


async def event_edit_description(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one(ObjectId(event_id))

    await AdminEditEvent.event_description.set()
    async with state.proxy() as data:
        data['event_id'] = event_id
        data['callback_data'] = f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton('↩ Назад',
                                      callback_data=f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))

    await callback.message.edit_text(f"📖 Описание\n {event['description']}\n\n✏ Введите новое описание:",
                                     reply_markup=keyboard)


async def event_edit_description_set(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        event = events.find_one(ObjectId(data['event_id']))
        events.update_one(event, {'$set': {'description': message.text}})
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))
    await message.answer('📝 Описание изменено', reply_markup=keyboard)

    await send_log(f"Мероприятие[{event['name']}]: Описание <- {message.text}")


async def event_edit_price(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one(ObjectId(event_id))

    await AdminEditEvent.event_price.set()
    async with state.proxy() as data:
        data['event_id'] = event_id
        data['callback_data'] = f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton('↩ Назад',
                                      callback_data=f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))

    await callback.message.edit_text(
        f"💰 Стоимость\n {event['price']}\n\n✏ Введите новую стоимость:",
        reply_markup=keyboard)


async def event_edit_price_set(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        event = events.find_one(ObjectId(data['event_id']))
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))
        if not re.match(r'^\d+$', message.text):
            await AdminEditEvent.event_price.set()
            await message.answer('✏ Введите новую стоимость:', reply_markup=keyboard)
            return
    events.update_one(event, {'$set': {'price': int(message.text)}})
    await message.answer('📝 Стоимость изменена', reply_markup=keyboard)

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
            keyboard.add(InlineKeyboardButton(text=f"{service}: {price}",
                                              callback_data=f"event-edit-service%{event_id}%{event['service_description'].index(service)}"))

    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton('↩ Назад',
                                      callback_data=f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))

    await callback.message.edit_text(f"👇 Выберите услугу или действие:", reply_markup=keyboard)


async def event_edit_service_description(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    service_index = callback.data.split(sep='%')[2]

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='❌ Удалить', callback_data=f"event-delete-service%{event_id}%{service_index}"))
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))
        data['event_id'] = event_id
        data['service_index'] = service_index

    await AdminEditEvent.event_service_description.set()
    await callback.message.edit_text('✏ Введите новое описание услуги:', reply_markup=keyboard)


async def event_edit_service_description_set(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(
            InlineKeyboardButton(text='❌ Удалить',
                                 callback_data=f"event-delete-service%{data['event_id']}%{data['service_index']}"))
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))
        events.update_one({'_id': ObjectId(data['event_id'])},
                          {'$set': {f'service_description.{data["service_index"]}': message.text}})
        await send_log(f"Мероприятие[{data['event_id']}]: Изменение услуги описание <- {message.text}")
    await AdminEditEvent.event_service_price.set()
    await message.answer('✏ Введите новую стоимость услуги:', reply_markup=keyboard)


async def event_edit_service_price_set(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='❌ Удалить',
                                          callback_data=f"event-delete-service%{data['event_id']}%{data['service_index']}"))
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))
        if not re.match(r'^\d+$', message.text):
            await AdminEditEvent.event_service_price.set()
            await message.answer('✏ Введите новую стоимость услуги:', reply_markup=keyboard)
            return
        events.update_one({'_id': ObjectId(data['event_id'])},
                          {'$set': {f'service_price.{data["service_index"]}': message.text}})
        await send_log(f"Мероприятие[{data['event_id']}]: Изменение услуги стоимость <- {message.text}")
    await message.answer('📝 Услуга изменена', reply_markup=keyboard)


async def event_edit_service_add(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        data['event_id'] = event_id
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))
    await AdminEditEvent.event_new_service_description.set()
    await callback.message.edit_text('✏ Введите описание услуги:', reply_markup=keyboard)


async def event_edit_service_add_description(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        data['service_description'] = message.text
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))
    await AdminEditEvent.event_new_service_price.set()
    await message.answer('✏ Введите стоимость услуги:', reply_markup=keyboard)


async def event_edit_service_add_price(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))
        if not re.match(r'^\d+$', message.text):
            await AdminEditEvent.event_new_service_price.set()
            await message.answer('✏ Введите стоимость услуги:', reply_markup=keyboard)
            return
        events.update_one({'_id': ObjectId(data['event_id'])},
                          {'$push': {'service_description': data['service_description']}})
        events.update_one({'_id': ObjectId(data['event_id'])}, {'$push': {'service_price': message.text}})

        await send_log(f"Мероприятие[{data['event_id']}]: Услуги <- {data['service_description']}")
    await message.answer('📝 Услуга добавлена', reply_markup=keyboard)


async def event_edit_service_delete(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    service_index = callback.data.split(sep='%')[2]
    event = events.find_one(ObjectId(event_id))
    keyboard = InlineKeyboardMarkup()
    async with state.proxy() as data:
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                     InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))
    events.update_one({'_id': ObjectId(event_id)},
                      {'$pull': {'service_description': event['service_description'][int(service_index)]}})
    events.update_one({'_id': ObjectId(event_id)},
                      {'$pull': {'service_price': event['service_price'][int(service_index)]}})
    await send_log(f"Мероприятие[{event_id}]: Услуга[{event['service_description'][int(service_index)]}] -> Удалена")
    await callback.message.edit_text('🗑 Услуга удалена', reply_markup=keyboard)


async def event_edit_time(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one(ObjectId(event_id))

    await AdminEditEvent.event_date.set()
    async with state.proxy() as data:
        data['event_id'] = event_id
        data['callback_data'] = f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"

        keyboard = await SelectTime().start_time(event['hour'], event['minute'])
        keyboard.add(InlineKeyboardButton('🏠 Меню', callback_data='menu'),
                     InlineKeyboardButton('↩ Назад',
                                          callback_data=f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"))
    await callback.message.edit_text('⌚ Установите время', reply_markup=keyboard)


async def event_edit_duration(callback: types.CallbackQuery, state: FSMContext):
    select, time = await SelectTime().process_selection(callback, callback.data)
    if select:
        async with state.proxy() as data:
            event = events.find_one(ObjectId(data['event_id']))
            keyboard = await SelectDays().start_days(day=event['duration'], edit=True)
            keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                         InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))
        events.update_one(event, {'$set': {'hour': time['hour'], 'minute': time['minute']}})

        await callback.message.edit_text('⌚ Время установлено!\n\n⏱ Установите длительность', reply_markup=keyboard)

        await send_log(f"Мероприятие[{event['name']}]: Время <- {time['hour']}:{time['minute']}")


async def event_edit_date(callback: types.CallbackQuery, state: FSMContext):
    select, day = await SelectDays().process_selection(callback, callback.data)
    if select:
        async with state.proxy() as data:
            event = events.find_one(ObjectId(data['event_id']))
            keyboard = await NewEventCalendar(events.find()).start_calendar()
            keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                         InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))

        events.update_one(event, {'$set': {'duration': day}})

        await callback.message.edit_text('⏱ Длительность установлена!\n\n🗓 Установите дату', reply_markup=keyboard)

        await send_log(f"Мероприятие[{event['name']}]: Длительность <- {day}")


async def event_edit_date_set(callback: types.CallbackQuery, state: FSMContext):
    select, date = await NewEventCalendar(events.find()).process_selection(callback, callback.data)
    if select:
        async with state.proxy() as data:
            event = events.find_one(ObjectId(data['event_id']))
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                         InlineKeyboardButton(text='↩ Назад', callback_data=data['callback_data']))

        events.update_one(event, {'$set': {'year': date['year'], 'month': date['month'], 'day': date['day']}})

        await callback.message.edit_text('🗓 Дата установлена', reply_markup=keyboard)

        await send_log(f"Мероприятие[{event['name']}]: Дата <- {date['day']}.{date['month']}.{date['year']}")


async def event_users(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one({'_id': ObjectId(event_id)})
    users_data = []
    for user_id in event['users']:
        users_data.append(users.find_one({'user_id': user_id}))
    callback_data = f"admin_event_calendar:event:{event['year']}:{event['month']}:{event['day']}:{event_id}"
    keyboard = await ListUsersInEvent().start_collection(users_data, callback_data)
    await UsersInEvent.list.set()
    async with state.proxy() as data:
        data['callback_data'] = callback_data
        data['event_id'] = event_id
    await callback.message.edit_text('👥 Участники мероприятия:', reply_markup=keyboard)


async def event_users_select(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        event_id = data['event_id']
        callback_data = data['callback_data']
        event = events.find_one({'_id': ObjectId(event_id)})
        users_data = []
        for user in event['users']:
            users_data.append(users.find_one({'user_id': user}))
    select, user_db_id, current_page = await ListUsersInEvent().processing_selection(callback, callback.data, users_data, callback_data)
    if select:
        await event_user_select(callback, state, user_db_id, current_page)


async def event_user_select(callback: types.CallbackQuery, state: FSMContext, user_db_id, current_page):
    async with state.proxy() as data:
        event_id = data['event_id']
    user = users.find_one({'_id': ObjectId(user_db_id)})
    payment = payments.find_one({'user_id': user['user_id'], 'binding': event_id})
    text = f"👤 Пользователь:\n {user['full_name']}\n\n" \
           f"📑 Выбранные услуги:\n"
    for info in payment['info']:
        text += f"- {info['label']}: {info['amount']}₽"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='📌 Открепить', callback_data=f"user-del-event%{user['user_id']}%{event_id}%{current_page}"))
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton(text='↩ Назад', callback_data=f'event_users-n-{current_page}'))
    await callback.message.edit_text(text, reply_markup=keyboard)


async def user_del_event(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(sep='%')[1])
    event_id = callback.data.split(sep='%')[2]
    current_page = callback.data.split(sep='%')[3]
    payments.delete_one({'user_id': user_id, 'binding': event_id})
    events.update_one({'_id': ObjectId(event_id)}, {'$pull': {'users': user_id}})
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton(text='↩ Назад', callback_data=f"event_users-n-{current_page}"))

    await callback.message.edit_text('📌 Пользователь откреплен', reply_markup=keyboard)
    await send_log(f"Мероприятие[{event_id}]:Пользователь[{user_id}] -> Открепить")


async def notify_users(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['event_id'] = callback.data.split(sep='%')[1]
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton('🏠 В меню', callback_data='menu'),
                     InlineKeyboardButton('↩ Назад', callback_data=data['callback_data']))
    await callback.message.edit_text('📩 Напишите сообщение для участников:', reply_markup=keyboard)


async def notify_users_send(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        event = events.find_one({'_id': ObjectId(data['event_id'])})
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton('🏠 В меню', callback_data='menu'),
                     InlineKeyboardButton('↩ Назад', callback_data=data['callback_data']))
    send = 0
    blocked = 0
    for user in event['users']:
        try:
            await bot.send_message(user, f"📢 Уважаемые участники мероприятия!\n {event['name']}\n\n" + message.text)
            send += 1
        except:
            blocked += 1
    await send_log(f"Мероприятие[{event['name']}]:Пользователи -> [Рассылка] <- {message.text}")
    await message.answer(f'Рассылка:\nОтправлено: {send}\nЗаблокировано:{blocked}', reply_markup=keyboard)


async def event_delete(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(sep='%')[1]
    events.delete_one({'_id': ObjectId(event_id)})
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('🏠 В меню', callback_data='menu'))
    await callback.message.edit_text('😖 Успешно удалено')