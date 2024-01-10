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
YOUKASSA = getenv('YOUKASSA')
LOG_CHAT = '-1001944137028'

DIR = path.dirname(path.abspath(__file__))

storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)
loop = asyncio.get_event_loop()

banned_users = set()
wait_registration = set()
admins = set()
referral_link = set()
admins.add(5475217426)

logging.basicConfig(level=logging.INFO)

