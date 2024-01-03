import logging
from datetime import datetime, timedelta
from config import loop
import asyncio

from database.collection import archive, events
from database.models import Archive
from modules.logger import send_log


async def spreader():
    while True:
        await send_log(f'Обработчик задач запущен {datetime.now()}')
        if datetime(datetime.now().year, datetime.now().month, datetime.now().day, 19, 0, 0)\
                < datetime.now()\
                < datetime(datetime.now().year, datetime.now().month, datetime.now().day, 19, 59, 59):

            loop.create_task(events_to_archive())
        await asyncio.sleep(3600)


async def events_to_archive():
    for event in events.find():
        date = datetime(int(event['year']), int(event['month']), int(event['day']), int(event['hour']), int(event['minute']))
        if date < datetime.now():
            if event['public']:
                event_to_archive = Archive(
                    name=event['name'],
                    description=event['description'],
                    year=event['year'],
                    month=event['month'],
                    day=event['day'],
                    users=event['users'],
                    link=[],
                    images=[],
                    video=[])
                archive.insert_one(event_to_archive())
                events.delete_one(event)

                await send_log(f"Мероприятие [{event['name']}] -> Архив")
            else:
                new_date = datetime.now() + timedelta(days=1)
                new = {"$set": {'year': new_date.year, 'month': new_date.month, 'day': new_date.day}}
                events.update_one(event, new)

                await send_log(f"Черновик [{event['name']}] -> {new_date}")