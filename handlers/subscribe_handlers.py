import asyncio
import logging
import re
from datetime import datetime, timedelta
from os import path, listdir

import handlers.main_handlers
from database.collection import events, find_event, archive, payments, users
from database.models import Payment
from modules.bot_states import Menu, EventSubscribe
from config import DIR, bot, LOG_CHAT, YOUKASSA, banned_users, subscribe_amount, CHANNEL, CHAT
from bson import ObjectId

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext

from modules.bot_calendar_module import EventCalendar
from modules.logger import send_log


async def event_subscribe(callback: types.CallbackQuery, state: FSMContext):
    await EventSubscribe.services.set()
    event_id = callback.data.split(sep='%')[1]
    event = events.find_one({'_id': ObjectId(event_id)})

    keyboard = InlineKeyboardMarkup()

    services = []
    async with state.proxy() as data:
        data['event_id'] = event_id
        for service, price in zip(event['service_description'], event['service_price']):
            keyboard.add(InlineKeyboardButton(text=f'{service}: {price}₽', callback_data=f"subscribe-event-select%{event['service_description'].index(service)}"))
            services.append(False)
        data['service_select'] = services
    keyboard.add(InlineKeyboardButton(text='💳 Оплатить', callback_data=f"event_payment_receipt"))
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton(text='↩️ Назад',
                                      callback_data=f"event_calendar:event:{event['year']}:{event['month']}:0:{event_id}"))
    text = f"💳 Оплата: {event['name']}\n" \
           f"💰 К оплате: {event['price']}₽\n\n" \
           f"🛒 Выберите услуги или нажмите - 💳 Оплатить"
    await callback.message.edit_text(text, reply_markup=keyboard)


async def event_subscribe_select(callback: types.CallbackQuery, state: FSMContext):
    service_select = callback.data.split(sep='%')[1]

    keyboard = InlineKeyboardMarkup()

    async with state.proxy() as data:
        event = events.find_one({'_id': ObjectId(data['event_id'])})
        services = data['service_select']
        if services[int(service_select)]:
            services[int(service_select)] = False
        else:
            services[int(service_select)] = True

        finish_price = int(event['price'])

        for service, price, select in zip(event['service_description'], event['service_price'], services):
            if select:
                keyboard.add(InlineKeyboardButton(text=f'✅ {service}: {price}₽',
                                                  callback_data=f"subscribe-event-select%{event['service_description'].index(service)}"))
                finish_price += int(price)
            else:
                keyboard.add(InlineKeyboardButton(text=f'{service}: {price}₽',
                                                  callback_data=f"subscribe-event-delete%{event['service_description'].index(service)}"))

        data['service_select'] = services
    keyboard.add(InlineKeyboardButton(text='💳 Оплатить', callback_data=f"event_payment_receipt"))
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton(text='↩️ Назад',
                                      callback_data=f"event_calendar:event:{event['year']}:{event['month']}:0:{str(event['_id'])}"))

    text = f"💳 Оплата: {event['name']}\n" \
           f"💰 К оплате: {finish_price}₽\n\n" \
           f"🛒 Выберите услуги или нажмите - 💳 Оплатить"
    await callback.message.edit_text(text, reply_markup=keyboard)


async def event_payment_receipt(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        event = events.find_one(ObjectId(data['event_id']))

        title = f"💳 Оплата: {event['name']}"
        description = f"{event['description']}\n"

        prices = [{'label': '🛒 Базовая стоимость', 'amount': int(event['price']) * 100}]
        amount = int(event['price'])
        services = ''
        for service, price, select in zip(event['service_description'], event['service_price'], data['service_select']):
            if select:
                services += '1'
                prices.append({'label': '🛒 '+service, 'amount': int(price) * 100})
                amount += int(price)
                continue
            services += '0'
        if amount > 0:
            await bot.send_invoice(callback.from_user.id,
                                   title=title,
                                   description=description,
                                   payload=f"event-sub%{callback.from_user.id}%{data['event_id']}%{services}",
                                   provider_token=YOUKASSA,
                                   currency='RUB',
                                   prices=prices)
        else:
            await event_free_checkout(callback, state, data['event_id'], services, amount)


async def event_free_checkout(callback: types.CallbackQuery, state: FSMContext, event_id, services, amount):
    event = events.find_one({'_id': ObjectId(event_id)})
    info = [{'label': f"Участие в {event['name']}", 'amount': int(event['price'])}]
    for service, price, select in zip(event['service_description'], event['service_price'], services):
        if select == '1':
            info.append({'label': service, 'amount': int(price)})
    date = datetime.now()

    payment = Payment(user_id=callback.from_user.id,
                      binding=event_id,
                      info=info,
                      total_amount=amount,
                      invoice_payload=f'event-sub%{callback.from_user.id}%{event_id}%{services}',
                      telegram_payment_charge_id='FREE',
                      provider_payment_charge_id='FREE',
                      year=date.year,
                      month=date.month,
                      day=date.day,
                      hour=date.hour,
                      minute=date.minute,
                      second=date.second)
    new_payment = payments.insert_one(payment())
    await payment_info(callback.from_user.id, str(new_payment.inserted_id))
    await payment_info(LOG_CHAT, str(new_payment.inserted_id), True)

    events.update_one({'_id': ObjectId(event_id)}, {'$set': {'users': [callback.from_user.id]}})

    await callback.message.delete()

    await send_log(f"Чек [{str(new_payment.inserted_id)}] -> Платежи")


async def event_payment_checkout(message: types.Message, state: FSMContext):
    event_id = message.successful_payment.invoice_payload.split(sep='%')[2]
    services = list(message.successful_payment.invoice_payload.split(sep='%')[3])
    event = events.find_one({'_id': ObjectId(event_id)})
    info = [{'label': f"Участие в {event['name']}", 'amount': int(event['price'])}]
    for service, price, select in zip(event['service_description'], event['service_price'], services):
        if select == '1':
            info.append({'label': service, 'amount': int(price)})
    date = datetime.now()

    payment = Payment(user_id=message.from_user.id,
                      binding=event_id,
                      info=info,
                      total_amount=message.successful_payment.total_amount / 100,
                      invoice_payload=message.successful_payment.invoice_payload,
                      telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id,
                      provider_payment_charge_id=message.successful_payment.provider_payment_charge_id,
                      year=date.year,
                      month=date.month,
                      day=date.day,
                      hour=date.hour,
                      minute=date.minute,
                      second=date.second)
    new_payment = payments.insert_one(payment())
    await payment_info(message.from_user.id, str(new_payment.inserted_id))
    await payment_info(LOG_CHAT, str(new_payment.inserted_id), True)

    events.update_one({'_id': ObjectId(event_id)}, {'$set': {'users': [message.from_user.id]}})


    await send_log(f"Чек [{str(new_payment.inserted_id)}] -> Платежи")


async def subscribe_payment_receipt(callback: types.CallbackQuery, state: FSMContext):
    months = int(callback.data.split(sep='%')[1])
    amount = months * (subscribe_amount[0])*100

    await bot.send_invoice(callback.from_user.id,
                           title='Подписка на БАБР',
                           description=f'Оформление подписки на {months} месяц.',
                           payload=f"user-sub%{callback.from_user.id}%{months}",
                           provider_token=YOUKASSA,
                           currency='RUB',
                           prices=[{'label': 'Подписка на БАБР', 'amount': amount}])
    await callback.message.delete()


async def subscribe_payment_checkout(message: types.Message, state: FSMContext):
    user_id = int(message.successful_payment.invoice_payload.split(sep='%')[1])
    months = int(message.successful_payment.invoice_payload.split(sep='%')[2])
    user = users.find_one({'user_id': user_id})
    new_subscribe = user['subscribe'] + months
    await send_log(f'Пользователь[{user_id}] -> Подписка <- {new_subscribe}')
    users.update_one(user, {'$set': {'subscribe': new_subscribe}})
    banned_users.discard(user_id)
    try:
        await bot.unban_chat_member(CHAT, user_id)
    except:
        pass
    try:
        await bot.unban_chat_member(CHANNEL, user_id)
    except:
        pass
    await send_log(f'Пользователь[{user_id}] -> Доступ <- Канал, Чат, Бот')


    now = datetime.now()

    payment = Payment(user_id=message.from_user.id,
                      binding=user['user_id'],
                      info=[{'label': f'Подписка на {months} месяц.', 'amount': message.successful_payment.total_amount / 100}],
                      total_amount=message.successful_payment.total_amount / 100,
                      invoice_payload=message.successful_payment.invoice_payload,
                      telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id,
                      provider_payment_charge_id=message.successful_payment.provider_payment_charge_id,
                      year=now.year,
                      month=now.month,
                      day=now.day,
                      hour=now.hour,
                      minute=now.minute,
                      second=now.second)
    new_payment = payments.insert_one(payment())
    await payment_info(message.from_user.id, str(new_payment.inserted_id))
    await payment_info(LOG_CHAT, str(new_payment.inserted_id), True)

    await send_log(f"Чек [{str(new_payment.inserted_id)}] -> Платежи")


async def payment_check(callback: types.CallbackQuery, state: FSMContext):
    payment_id = callback.data.split(sep='%')[1]
    await payment_info(callback.from_user.id, payment_id)


async def payment_info(user_id: str, payment_id: str, admin: bool = False):
    payment = payments.find_one({'_id': ObjectId(payment_id)})
    date_form = datetime(int(payment['year']), int(payment['month']), int(payment['day']), int(payment['hour']),
                         int(payment['minute']), int(payment['second'])).strftime('%Y.%m.%d %H:%M:%S')
    check = f"🧾 Чек [{payment_id}]\n\n" \
            f"📅 Дата: {date_form}\n" \
            f"💰 Сумма платежа: {payment['total_amount']}₽\n" \
            f"📬 Пользователь: {payment['user_id']}\n" \
            f"📑 Информация:\n"
    for service in payment['info']:
        check += f"- {service['label']}: {service['amount']}₽\n"
    if admin:
        check += f"\nИнформация о платеже:\n" \
                 f"Триггер:\n{payment['invoice_payload']}\n" \
                 f"ID платежа телеграмм:\n{payment['telegram_payment_charge_id']}\n" \
                 f"ID чека Yokassa:\n{payment['provider_payment_charge_id']}\n"
        await bot.send_message(user_id, check)
    else:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'))
        await bot.send_message(user_id, check, reply_markup=keyboard)


async def subscribe_amount_new(callback: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'))
    await Menu.admin_amount.set()
    await callback.message.edit_text(f'Стоимость подписки: {subscribe_amount[0]}\nУстановите новую стоимость подписки:', reply_markup=keyboard)


async def subscribe_amount_set(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'))
    pattern = r'^\d+$'
    if re.match(pattern, message.text):
        await message.answer(f'Новая стоимость подписки установлена', reply_markup=keyboard)
        await Menu.main.set()
    else:
        await message.answer(f'Установите новую стоимость подписки:', reply_markup=keyboard)
        await Menu.admin_amount.set()
        return
    await send_log(f"Стоимость подписки: {subscribe_amount[0]} -> {message.text}")
    subscribe_amount.remove(subscribe_amount[0])
    subscribe_amount.append(int(message.text))


async def get_payments_from_user(message: types.Message, state: FSMContext):
    user_id = message.text.split()[1]
    try:
        payments_data = payments.find({'user_id': int(user_id)})
        if payments_data:
            for payment in payments_data:
                await payment_info(message.from_user.id, payment['_id'], True)
    except:
        await message.answer('😖 Не найдено..')
