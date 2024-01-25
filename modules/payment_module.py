import asyncio

from yookassa import Configuration, Payment
import json

import handlers
from config import loop, YOOKASSA_account_id, YOKASSA_secret_key
from modules.logger import send_log

Configuration.account_id = YOOKASSA_account_id
Configuration.secret_key = YOKASSA_secret_key

# payment_method_data = [{'name': "Банковская карта", 'method': "bank_card"},
#                            {'name': "YooMoney", 'method': "yoo_money"},
#                            {'name': "СберБанк", 'method': "sberbank"},
#                            {'name': "Тинькофф", 'method': "tinkoff_bank"},
#                            {'name': "B2B", 'method': "b2b_sberbank"}]


async def create_payment(amount, description, payload):

    payment = Payment.create({
        "amount": {
            "value": f"{amount}.00",
            "currency": "RUB"
        },
        "payment_method_data": {
            #"type": "sberbank"
            "type": "bank_card"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/BabrClub38Bot"
        },
        "description": description,
        "metadata": payload,
    })

    payment_data = json.loads(payment.json())
    payment_id = payment_data['id']
    loop.create_task(check_payment(payment_id))
    payment_url = (payment_data['confirmation'])['confirmation_url']

    return payment_url


async def create_card_payment(amount, description, payload):

    payment = Payment.create({
        "amount": {
            "value": f"{amount}.00",
            "currency": "RUB"
        },
        "payment_method_data": {
            "type": "bank_card"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/BabrClub38Bot"
        },
        "description": description,
        "metadata": payload,
    })

    payment_data = json.loads(payment.json())
    payment_id = payment_data['id']
    loop.create_task(check_payment(payment_id))
    payment_url = (payment_data['confirmation'])['confirmation_url']

    return payment_url


async def create_b2b_payment(amount, description, payload):

    payment = Payment.create({
        "amount": {
            "value": f"{amount}.00",
            "currency": "RUB"
        },
        "payment_method_data": {
            "type": "b2b_sberbank"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/BabrClub38Bot"
        },
        "description": description,
        "metadata": payload,
    })

    payment_data = json.loads(payment.json())
    payment_id = payment_data['id']
    loop.create_task(check_payment(payment_id))
    payment_url = (payment_data['confirmation'])['confirmation_url']

    return payment_url


async def check_payment(payment_id):
    payment = json.loads((Payment.find_one(payment_id)).json())
    while payment['status'] == 'pending':
        payment = json.loads((Payment.find_one(payment_id)).json())
        await asyncio.sleep(10)
    Payment.capture(payment_id)
    while payment['status'] == 'waiting_for_capture':
        payment = json.loads((Payment.find_one(payment_id)).json())
        await asyncio.sleep(10)
    if payment['status'] == 'succeeded':
        await send_log(f'Ответ -> {payment} -> Бот')
        if payment['metadata']['trigger'].split(sep='%')[0] == 'user-sub':
            await handlers.subscribe_handlers.subscribe_payment_checkout(payment)
        if payment['metadata']['trigger'].split(sep='%')[0] == 'event-sub':
            await handlers.subscribe_handlers.event_payment_checkout(payment)
        return True
    else:
        return False