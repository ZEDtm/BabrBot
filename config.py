import asyncio
import logging
from os import getenv, path

from bson import ObjectId
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares import BaseMiddleware



class LoggingMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message, data):
        logging.info(f"{message}")
        print(message, data)
        return data



load_dotenv()

TOKEN = getenv('TOKEN')
MONGO_LOGIN = getenv('MONGO_LOGIN')
MONGO_PASS = getenv('MONGO_PASS')
YOUKASSA = getenv('YOUKASSA')
LOG_CHAT = '-1001944137028'
SUBSCRIBE_AMOUNT = 1000
DIR = path.dirname(path.abspath(__file__))

storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
loop = asyncio.get_event_loop()

banned_users = set()
wait_registration = set()
admins = set()
referral_link = set()
admins.add(5475217426)

logging.basicConfig(level=logging.INFO)

