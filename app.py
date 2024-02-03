import uvicorn
from bson import ObjectId
from fastapi import FastAPI, Request
from aiogram.types import Update
from aiogram import Bot, Dispatcher

from config import subscribe_amount, banned_users, wait_registration, admins
from database.collection import db_config
from main import dp, bot, on_startup as on_startup_bot



app = FastAPI()


@app.on_event('startup')
async def on_startup():
    await bot.delete_webhook()
    WEBHOOK_HOST = 'https://43f2-193-47-242-96.ngrok-free.app/'
    WEBHOOK_PATH = 'webhook'
    WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
    webhook = await bot.get_webhook_info()
    if webhook.url != WEBHOOK_URL:
        if not webhook.url:
            await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL, allowed_updates=['message','callback_query'])

    conf = db_config.find_one({'_id': ObjectId('659c6a3d1e2c9f558337a9b2')})
    subscribe_amount.append(conf['SUBSCRIBE_AMOUNT'][0])
    for user in conf['banned_users']:
        banned_users.add(user)
    for user in conf['wait_registration']:
        wait_registration.add(user)
    for user in conf['admins']:
        admins.add(user)
    #await send_log(f'Бот -> webhook -> Удалить')


@app.post("/webhook")
async def webhook(request: Request):
    update = await request.json()
    Bot.set_current(dp.bot)
    Dispatcher.set_current(dp)
    await dp.process_update(Update(**update))
    return {"status": "ok"}


@app.get("/")
async def payments(request: Request):
    return {"status": "ok"}



#async def start_aiogram_bot():
    #await main.main()

def start_fastapi_server():
    uvicorn.run(app, host="localhost", port=8000)


if __name__ == '__main__':
    #fastapi_thread = threading.Thread(target=start_fastapi_server)
    #fastapi_thread.start()
    start_fastapi_server()