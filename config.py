import asyncio
import logging
from os import getenv, path

from aiogram import Bot
from dotenv import load_dotenv
from aiogram import types, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

load_dotenv()
TOKEN = getenv('TOKEN')
MONGO_LOGIN = getenv('MONGO_LOGIN')
MONGO_PASS = getenv('MONGO_PASS')
YOOKASSA = getenv('YOOKASSA')
YOOKASSA_account_id = '301255'#"301766"
YOKASSA_secret_key = 'test_2ZNhGkP1iW9oN8d1S8kaJPbmYRaCcw6KdZu_HPXZ9xQ'#"live_APTcp0tYEZDrSIi2p5fQDZCkAnZTZrTM4ke_jXmr47o"

HOST = getenv('HOST')
WEBHOOK_PATH = getenv('WEBHOOK_PATH')
WEBHOOK_URL = f"{HOST}{WEBHOOK_PATH}"
PAYMENT_PATH = getenv('PAYMENT_PATH')
PAYMENT_URL = f"{HOST}{PAYMENT_PATH}"


LOG_CHAT = getenv('LOG_CHAT')
CHAT = getenv('CHAT')
CHANNEL = getenv('CHANNEL')

DIR = path.dirname(path.abspath(__file__))

storage = RedisStorage2(host="127.0.0.1", port=6379)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

subscribe_amount = []
banned_users = set()
wait_registration = set()
admins = set()
referral_link = set()

loop = asyncio.get_event_loop()

logging.basicConfig(level=logging.INFO)

