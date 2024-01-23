from yookassa import Configuration, Payment
import json


# payment_method_data = [{'name': "Банковская карта", 'method': "bank_card"},
#                            {'name': "YooMoney", 'method': "yoo_money"},
#                            {'name': "СберБанк", 'method': "sberbank"},
#                            {'name': "Тинькофф", 'method': "tinkoff_bank"},
#                            {'name': "B2B", 'method': "b2b_sberbank"}]


async def create_payment(amount, description, payload):
    Configuration.account_id = "301766"
    Configuration.secret_key = "live_APTcp0tYEZDrSIi2p5fQDZCkAnZTZrTM4ke_jXmr47o"

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
        "description": description,
        "metadata": payload,
    })

    payment_data = json.loads(payment.json())
    payment_id = payment_data['id']
    payment_url = (payment_data['confirmation'])['confirmation_url']

    return payment_url


async def create_card_payment(amount, description, payload):
    Configuration.account_id = "301255"
    Configuration.secret_key = "test_2ZNhGkP1iW9oN8d1S8kaJPbmYRaCcw6KdZu_HPXZ9xQ"

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
    payment_url = (payment_data['confirmation'])['confirmation_url']

    return payment_url


async def create_b2b_payment(amount, description, payload):
    Configuration.account_id = "301255"
    Configuration.secret_key = "test_2ZNhGkP1iW9oN8d1S8kaJPbmYRaCcw6KdZu_HPXZ9xQ"

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
    payment_url = (payment_data['confirmation'])['confirmation_url']

    return payment_url