import logging
from datetime import datetime, timedelta
from os import path, listdir

from database.collection import events, find_event, archive, payments
from database.models import Payment
from modules.bot_states import Menu, EventSubscribe
from config import DIR, bot, LOG_CHAT
from bson import ObjectId

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext

from modules.calendar_module import EventCalendar
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
            keyboard.add(InlineKeyboardButton(text=f'{service}: {price}', callback_data=f"subscribe-event-select%{event['service_description'].index(service)}"))
            services.append(False)
        data['service_select'] = services
    keyboard.add(InlineKeyboardButton(text='Сформировать', callback_data=f"event_payment_receipt"))
    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                 InlineKeyboardButton(text='Назад', callback_data=f"event_calendar:event:{event['year']}:{event['month']}:0:{event_id}"))
    text = f"Оплата [{event['name']}]\nК оплате: {event['price']}₽\n\nВыберите услуги или нажмите [Сформировать]"
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
                keyboard.add(InlineKeyboardButton(text=f'✅ {service}: {price}₽',callback_data=f"subscribe-event-select%{event['service_description'].index(service)}"))
                finish_price += int(price)
            else:
                keyboard.add(InlineKeyboardButton(text=f'{service}: {price}₽', callback_data=f"subscribe-event-delete%{event['service_description'].index(service)}"))

        data['service_select'] = services
    keyboard.add(InlineKeyboardButton(text='Сформировать', callback_data=f"event_payment_receipt"))
    keyboard.add(InlineKeyboardButton(text='В меню', callback_data='menu'),
                 InlineKeyboardButton(text='Назад', callback_data=f"event_calendar:event:{event['year']}:{event['month']}:0:{str(event['_id'])}"))

    text = f"Оплата [{event['name']}]\nК оплате: {finish_price}₽\n\nВыберите услуги или нажмите [Сформировать]"
    await callback.message.edit_text(text, reply_markup=keyboard)


async def event_payment_receipt(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        event = events.find_one(ObjectId(data['event_id']))

        title = f"Оплата [{event['name']}]"
        description = f"{event['description']}\n"

        prices = [{'label': 'Базовая стоимость', 'amount': int(event['price'])*100}]

        for service, price, select in zip(event['service_description'], event['service_price'], data['service_select']):
            if select:
                prices.append({'label': service, 'amount': int(price)*100})

        await bot.send_invoice(callback.message.chat.id,
                               title=title,
                               description=description,
                               payload=f"event-sub%{callback.message.chat.id}%{data['event_id']}",
                               provider_token='381764678:TEST:74809',
                               currency='RUB',
                               prices=prices)
        await callback.message.delete()


async def event_payment_checkout(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        event = events.find_one({'_id': ObjectId(data['event_id'])})
        info = [{'label': f"Участие в {event['name']}", 'amount': int(event['price'])}]
        for service, price, select in zip(event['service_description'], event['service_price'], data['service_select']):
            if select:
                info.append({'label': service, 'amount': int(price)})
    date = datetime.now()

    payment = Payment(user_id=message.from_user.id,
                      info=info,
                      total_amount=message.successful_payment.total_amount/100,
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

    await send_log(f"{date.strftime('%Y.%m.%d %H:%M:%S')} Чек [{str(new_payment.inserted_id)}] -> Платежи")


async def payment_info(user_id: str, payment_id: str, admin: bool = False):
    payment = payments.find_one({'_id': ObjectId(payment_id)})
    date_form = datetime(int(payment['year']), int(payment['month']), int(payment['day']), int(payment['hour']), int(payment['minute']), int(payment['second'])).strftime('%Y.%m.%d %H:%M:%S')
    check = f"Чек [{payment_id}]\n\n" \
            f"Дата: {date_form}\n" \
            f"Сумма платежа: {payment['total_amount']}₽\n" \
            f"Пользователь: {payment['user_id']}\n" \
            f"Информация:\n"
    for service in payment['info']:
        check += f"*{service['label']}-{service['amount']}₽\n"
    if admin:
        check += f"\nИнформация о платеже:\n" \
                 f"[invoice_payload]:\n{payment['invoice_payload']}\n" \
                 f"[telegram_payment_charge_id]:\n{payment['telegram_payment_charge_id']}\n" \
                 f"[provider_payment_charge_id]:\n{payment['provider_payment_charge_id']}\n"
    await bot.send_message(user_id, check)