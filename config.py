import asyncio
import logging
from os import getenv, path
from dotenv import load_dotenv

from aiogram import types, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

subscribe_amount = []

load_dotenv()

TOKEN = getenv('TOKEN')
MONGO_LOGIN = getenv('MONGO_LOGIN')
MONGO_PASS = getenv('MONGO_PASS')
YOOKASSA = getenv('YOOKASSA')
YOOKASSA_account_id = "301766"
YOKASSA_secret_key = "live_APTcp0tYEZDrSIi2p5fQDZCkAnZTZrTM4ke_jXmr47o"


LOG_CHAT = getenv('LOG_CHAT')
CHAT = getenv('CHAT')
CHANNEL = getenv('CHANNEL')

DIR = path.dirname(path.abspath(__file__))

storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)
loop = asyncio.get_event_loop()

banned_users = set()
wait_registration = set()
admins = set()
referral_link = set()

logging.basicConfig(level=logging.INFO)

