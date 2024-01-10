import logging
from datetime import datetime, timedelta
from config import loop, bot, banned_users, wait_registration, admins, referral_link
import asyncio

from database.collection import archive, events, users
from database.models import Archive
from modules.logger import send_log

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def spreader():
    loop.create_task(events_to_archive())
    loop.create_task(notification())
    while True:
        year, month, day, hour = datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour
        if datetime(year, month, day, 21, 0, 0) < datetime.now() < datetime(year, month, day, 21, 59, 59):
            loop.create_task(events_to_archive())
            for link in referral_link:
                referral_link.remove(link)
        if datetime(year, month, day, 8, 0, 0) < datetime.now() < datetime(year, month, day, 8, 59, 59):
            loop.create_task(check_subscribe())
            loop.create_task(notification())
        if day == 1 and hour == 8 or day == 1 and hour == 16:
            loop.create_task(check_subscribe())
        if day == 2 and hour == 0:
            loop.create_task(check_subscribe(True))
        await asyncio.sleep(3600)


async def notification():
    for event in events.find():
        keyboard = InlineKeyboardMarkup()

        now = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 0, 0, 0)
        date = datetime(int(event['year']), int(event['month']), int(event['day']), 0, 0, 0)

        if date - timedelta(days=7) == now:
            keyboard.add(InlineKeyboardButton(text=f"{event['name']}", callback_data=f"event_calendar:event:{date.year}:{date.month}:{date.day}:{str(event['_id'])}"))
            for user_id in event['users']:
                try:
                    await bot.send_message(user_id, f"🔔 Уважаемые участники мероприятия:\n{event['name']}\n\n⏱ До начала осталось неделя!", reply_markup=keyboard)
                except:
                    pass

        if date - timedelta(days=3) == now:
            keyboard.add(InlineKeyboardButton(text=f"{event['name']}", callback_data=f"event_calendar:event:{date.year}:{date.month}:{date.day}:{str(event['_id'])}"))
            for user_id in event['users']:
                try:
                    await bot.send_message(user_id, f"🔔 Уважаемые участники мероприятия:\n{event['name']}\n\n⏱ До начала осталась 3 дня!", reply_markup=keyboard)
                except:
                    pass

        if date - timedelta(days=1) == now:
            keyboard.add(InlineKeyboardButton(text=f"{event['name']}", callback_data=f"event_calendar:event:{date.year}:{date.month}:{date.day}:{str(event['_id'])}"))
            for user_id in event['users']:
                try:
                    await bot.send_message(user_id, f"🔔 Уважаемые участники мероприятия:\n{event['name']}\n\n🎉 Начало завтра, не пропустите!", reply_markup=keyboard)
                except:
                    pass


async def events_to_archive():
    for event in events.find():
        date = datetime(int(event['year']), int(event['month']), int(event['day']), int(event['hour']), int(event['minute']))
        if date + timedelta(days=event['duration']) < datetime.now():
            if event['public']:
                event_to_archive = Archive(
                    name=event['name'],
                    description=event['description'],
                    year=event['year'],
                    month=event['month'],
                    day=event['day'],
                    users=event['users'],
                    link='')
                archive.insert_one(event_to_archive())
                events.delete_one(event)

                await send_log(f"Мероприятие [{event['name']}] -> Архив")
            else:
                new_date = datetime.now() + timedelta(days=1)
                new = {"$set": {'year': new_date.year, 'month': new_date.month, 'day': new_date.day}}
                events.update_one(event, new)

                await send_log(f"Черновик [{event['name']}] -> {new_date}")


async def check_subscribe(banned = False):
    for user in users.find():
        if user['user_id'] in banned_users or user['user_id'] in wait_registration or user['user_id'] in admins:
            continue
        user_id = user['user_id']
        date_subscribe = datetime(int(user['subscribe_year']), int(user['subscribe_month']), int(user['subscribe_day']))
        if banned:
            if date_subscribe + timedelta(days=2) > datetime.now():
                continue
            banned_users.add(user_id)
            continue
        else:
            if date_subscribe + timedelta(days=1) > datetime.now():
                continue
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text='🎫 Оформить подписку', callback_data=f"user-subscribe"))
            try:
                await bot.send_message(user_id, '😔 Ваша подписка окончена\nПожалуйста, оформите подписку:', reply_markup=keyboard)
            except:
                pass


