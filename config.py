from os import getenv
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

load_dotenv()

TOKEN = getenv('TOKEN')
MONGO_LOGIN = getenv('MONGO_LOGIN')
MONGO_PASS = getenv('MONGO_PASS')

storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)
