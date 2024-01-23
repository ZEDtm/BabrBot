
from datetime import datetime, timedelta
from config import loop, bot, banned_users, wait_registration, admins, referral_link, CHANNEL, CHAT
import asyncio

from database.collection import archive, events, users
from database.models import Archive
from modules.logger import send_log
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def spreader():
    loop.create_task(events_to_archive())
    loop.create_task(notification())
    #oop.create_task(check_subscribe())
    while True:
        await send_log('Бот -> Планирование задач')
        year, month, day, hour = datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour
        if hour == 23:
            await send_log('Бот -> Планирование задач -> Проверка мероприятий')
            loop.create_task(events_to_archive())
            for link in referral_link:
                referral_link.remove(link)
        if hour == 8:
            await send_log('Бот -> Планирование задач -> Уведомления о мероприятиях')
            #loop.create_task(check_subscribe())
            loop.create_task(notification())
        if day == 22 and hour == 8 or day == 1 and hour == 18:
            await send_log('Бот -> Планирование задач -> Проверка подписок')
            loop.create_task(check_subscribe())
        if day == 23 and hour == 0:
            await send_log('Бот -> Планирование задач -> Проверка подписок -> Блокировка доступа')
            loop.create_task(check_subscribe(True))
        await asyncio.sleep(3600)


async def notification():
    for event in events.find({'public': True}):
        keyboard = InlineKeyboardMarkup()

        now = datetime(datetime.now().year, datetime.now().month, datetime.now().day, 0, 0, 0)
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
        if date + timedelta(days=event['duration']) == datetime.now():
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
        if user['user_id'] in banned_users or user['user_id'] in wait_registration or user['user_id'] in admins:
            continue
        user_id = user['user_id']
        month = user['subscribe']
        if month == 1111:
            continue
        if month - 1 == -1:
            if banned:
                banned_users.add(user_id)
                await send_log(f"Блокирую доступ за неоплаченную подписку <- Пользователь[{user_id}]")
                try:
                    await bot.kick_chat_member(CHAT, user_id)
                except:
                    pass
                try:
                    await bot.kick_chat_member(CHANNEL, user_id)
                except:
                    pass
                continue
            else:
                await send_log(f"Уведомление о неоплаченной подписке -> Пользователь[{user_id}]")
                keyboard = InlineKeyboardMarkup(row_width=1)
                keyboard.add(InlineKeyboardButton(text='🎫 Оформить на 1 месяц', callback_data=f"user-subscribe%1"),
                             InlineKeyboardButton(text='🎫 Оформить на 3 месяца', callback_data=f"user-subscribe%3"),
                             InlineKeyboardButton(text='🎫 Оформить на 6 месяцев', callback_data=f"user-subscribe%6"),
                             InlineKeyboardButton(text='🎫 Оформить на год', callback_data=f"user-subscribe%12"))
                try:
                    await bot.send_message(user_id, '😔 Ваша подписка окончена\nПожалуйста, оформите подписку:', reply_markup=keyboard)
                except:
                    pass
        else:
            users.update_one(user, {'$set': {'subscribe': month - 1}})


