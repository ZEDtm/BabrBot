import logging
from datetime import datetime

from config import LOG_CHAT, bot


async def send_log(info: str):
    time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    logging.info(time + info)
    await bot.send_message(LOG_CHAT, f'[{time}]: {info}')
