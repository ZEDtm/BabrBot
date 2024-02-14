import uvicorn
from aiogram.utils.exceptions import TelegramAPIError
from bson import ObjectId
from fastapi import FastAPI, Request
from aiogram.types import Update
from aiogram import Bot, Dispatcher

import handlers
import modules.loop_handler
from config import subscribe_amount, banned_users, wait_registration, admins, WEBHOOK_URL, tasks
from database.collection import db_config
from main import dp, bot
from modules.logger import send_log

app = FastAPI()


@app.on_event('startup')
async def on_startup():
    conf = db_config.find_one({'_id': ObjectId('659c6a3d1e2c9f558337a9b2')})
    subscribe_amount.append(conf['SUBSCRIBE_AMOUNT'][0])
    for user in conf['banned_users']:
        banned_users.add(user)
    for user in conf['wait_registration']:
        wait_registration.add(user)
    for user in conf['admins']:
        admins.add(user)
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        if not webhook_info.url:
            await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL, allowed_updates=['message', 'callback_query'])
    await modules.loop_handler.spreader()


@app.on_event('shutdown')
async def on_shutdown():
    db_config.update_one({'_id': ObjectId('659c6a3d1e2c9f558337a9b2')}, {
        '$set': {'banned_users': [user for user in banned_users],
                 'wait_registration': [user for user in wait_registration],
                 'admins': [user for user in admins],
                 'SUBSCRIBE_AMOUNT': subscribe_amount}})
    await send_log('Бот -> webhook -> Удалить')
    await bot.delete_webhook()
    Bot.set_current(dp.bot)
    Dispatcher.set_current(dp)
    await dp.storage.close()
    await dp.storage.wait_closed()


@app.post("/webhook")
async def webhook(request: Request):
    try:
        update = await request.json()
        Bot.set_current(dp.bot)
        Dispatcher.set_current(dp)
        await dp.process_update(Update(**update))
    except TelegramAPIError as e:
        tasks.append(f"Telegram API error: {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        tasks.append(f"Unexpected error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        return {"status": "ok"}


@app.post("/payments")
async def payments(request: Request):
    payment = await request.json()
    payment = payment['object']
    await send_log(f'Yookassa -> {payment} -> Бот')
    if payment['metadata']['trigger'].split(sep='%')[0] == 'user-sub':
        await handlers.subscribe_handlers.subscribe_payment_checkout(payment)
    if payment['metadata']['trigger'].split(sep='%')[0] == 'event-sub':
        await handlers.subscribe_handlers.event_payment_checkout(payment)
    return {"status": "ok"}


@app.get("/")
async def hello(request: Request):
    return {"status": tasks}


def start_fastapi_server():
    uvicorn.run(app, host="localhost", port=8000)


if __name__ == '__main__':
    start_fastapi_server()