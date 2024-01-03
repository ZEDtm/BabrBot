import logging

from config import LOG_CHAT, bot


async def send_log(info: str):
    logging.info(info)
    await bot.send_message(LOG_CHAT, info)
