from datetime import datetime, timedelta

from config import bot, banned_users, wait_registration, admins, referral_link, CHANNEL, CHAT, tasks

from database.collection import archive, events, users
from database.models import Archive
from modules.logger import send_log
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

tz = timezone('Asia/Irkutsk')


async def spreader():
    await events_to_archive()
    scheduler = AsyncIOScheduler(timezone=tz)
    scheduler.add_job(spreader_, 'cron', day='*', hour='*')
    tasks.append("scheduler.add_job(spreader_, 'cron', day='*', hour='*')")
    scheduler.start()


async def spreader_():
    referral_link.clear()
    date_now = datetime.now(tz)
    if date_now.day in [1, 25, 26, 27, 28, 29, 30, 31] and date_now.hour in [8, 18]:
        await check_subscribe()
        tasks.append(f"checking subscribe at {date_now}")
    if date_now.hour == 23:
        tasks.clear()
        await events_to_archive()
        tasks.append(f"checking events at {date_now}")
    if date_now.day == 2 and date_now.hour == 0:
        await check_subscribe(True)
        tasks.append(f"checking subscribe and block at {date_now}")
    if date_now.hour == 8 or date_now.hour == 18:
        await notification()
        tasks.append(f"checking notification at {date_now}")



async def notification():
    for event in events.find({'public': True}):
        keyboard = InlineKeyboardMarkup()
        date_now = datetime.now(tz)
        now = datetime(date_now.year, date_now.month, date_now.day, 0, 0, 0)
        date = datetime(int(event['year']), int(event['month']), int(event['day']), 0, 0, 0)

        if date - timedelta(days=7) == now:
            await send_log(f"Пользователи <- уведомление о предстоящем мероприятии <- Мероприятие[{event['name']}]")
            keyboard.add(InlineKeyboardButton(text=f"{event['name']}", callback_data=f"event_calendar:event:{date.year}:{date.month}:{date.day}:{str(event['_id'])}"))
            for user_id in event['users']:
                try:
                    await bot.send_message(user_id, f"🔔 Уважаемые участники мероприятия:\n{event['name']}\n\n⏱ До начала осталась неделя!", reply_markup=keyboard)
                except:
                    pass

        if date - timedelta(days=3) == now:
            await send_log(f"Пользователи <- уведомление о предстоящем мероприятии <- Мероприятие[{event['name']}]")
            keyboard.add(InlineKeyboardButton(text=f"{event['name']}", callback_data=f"event_calendar:event:{date.year}:{date.month}:{date.day}:{str(event['_id'])}"))
            for user_id in event['users']:
                try:
                    await bot.send_message(user_id, f"🔔 Уважаемые участники мероприятия:\n{event['name']}\n\n⏱ До начала осталось 3 дня!", reply_markup=keyboard)
                except:
                    pass

        if date - timedelta(days=1) == now:
            await send_log(f"Пользователи <- уведомление о предстоящем мероприятии <- Мероприятие[{event['name']}]")
            keyboard.add(InlineKeyboardButton(text=f"{event['name']}", callback_data=f"event_calendar:event:{date.year}:{date.month}:{date.day}:{str(event['_id'])}"))
            for user_id in event['users']:
                try:
                    await bot.send_message(user_id, f"🔔 Уважаемые участники мероприятия:\n{event['name']}\n\n🎉 Начало завтра, не пропустите!", reply_markup=keyboard)
                except:
                    pass


async def events_to_archive():
    for event in events.find():
        date = datetime(int(event['year']), int(event['month']), int(event['day']), int(event['hour']), int(event['minute']))
        date_now = datetime.now()
        if date + timedelta(days=event['duration']) < date_now:
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
                events.delete_one(event)

                await send_log(f"Черновик [{event['name']}] -> Удален")


async def check_subscribe(banned=False):
    for user in users.find():
        user_id = user['user_id']
        month = user['subscribe']
        if user_id in banned_users or user_id in wait_registration or user_id in admins:
            continue
        if month == 1111:
            continue
        if month - 1 == -1:
            if banned:
                banned_users.add(user_id)
                await send_log(f"Блокирую доступ за неоплаченную подписку <- Пользователь[{user_id}]")
                try:
                    await bot.kick_chat_member(CHAT, user_id)
                    await bot.kick_chat_member(CHANNEL, user_id)
                except:
                    pass
                continue
            else:
                await send_log(f"Уведомление о неоплаченной подписке -> Пользователь[{user_id}]")
                keyboard = InlineKeyboardMarkup(row_width=1)
                keyboard.add(InlineKeyboardButton(text='🎫 Оформить на 1 месяц', callback_data=f"user-subscribe%1"))

                try:
                    await bot.send_message(user_id, 'Уважаемый резидент клуба, к сожалению, мы вынуждены ограничить ваш доступ к ресурсам сообщества с 1-го числа. Пожалуйста, оплатите членский взнос.\n\n Долгосрочная подписка: @pawlofff', reply_markup=keyboard)
                except:
                    pass
        else:
            users.update_one(user, {'$set': {'subscribe': month - 1}})


