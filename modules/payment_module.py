from yookassa import Configuration, Payment
import json

from config import YOOKASSA_account_id, YOKASSA_secret_key



# payment_method_data = [{'name': "Банковская карта", 'method': "bank_card"},
#                            {'name': "YooMoney", 'method': "yoo_money"},
#                            {'name': "СберБанк", 'method': "sberbank"},
#                            {'name': "Тинькофф", 'method': "tinkoff_bank"},
#                            {'name': "B2B", 'method': "b2b_sberbank"}]


async def create_payment(amount, description, payload):
    Configuration.account_id = YOOKASSA_account_id
    Configuration.secret_key = YOKASSA_secret_key
    payment = Payment.create({
        "amount": {
            "value": f"{amount}.00",
            "currency": "RUB"
        },
        "payment_method_data": {
            "type": "sberbank"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/BabrClub38Bot"
        },
        "capture": True,
        "description": description,
        "metadata": payload,
    })

    payment_data = json.loads(payment.json())
    payment_url = (payment_data['confirmation'])['confirmation_url']

    return payment_url


async def create_card_payment(amount, description, payload):
    Configuration.account_id = YOOKASSA_account_id
    Configuration.secret_key = YOKASSA_secret_key
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
        "capture": True,
        "description": description,
        "metadata": payload,
    })

    payment_data = json.loads(payment.json())
    payment_url = (payment_data['confirmation'])['confirmation_url']

    return payment_url


async def create_b2b_payment(amount, description, payload):
    Configuration.account_id = YOOKASSA_account_id
    Configuration.secret_key = YOKASSA_secret_key
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
        "capture": True,
        "description": description,
        "metadata": payload,
    })

    payment_data = json.loads(payment.json())
    payment_url = (payment_data['confirmation'])['confirmation_url']

    return payment_url
