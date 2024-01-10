import logging
from datetime import datetime

from database.collection import find_user, users
from database.models import User, Admin
from modules.bot_states import Menu, Registration

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import admins, referral_link
from modules.logger import send_log

logging.basicConfig(level=logging.INFO)


async def start(message: types.Message):
    if len(message.text) > 6:
        if message.text.split()[1] in referral_link:
            admins.add(message.from_user.id)
            referral_link.discard(message.text.split()[1])
            await send_log(f"Пользователь[{message.from_user.id}] -> Администратор")


    user = find_user(message.from_user.id)
    if message.from_user.id in admins:
        if not user:
            await registration_admin(message, message.from_user.id)
        menu = InlineKeyboardMarkup()
        menu.add(InlineKeyboardButton(text="📅 Управление", callback_data='admin_calendar'),
                 InlineKeyboardButton(text="📅 Мероприятия", callback_data='calendar_handler'))
        menu.add(InlineKeyboardButton(text="➕ Добавить мероприятие", callback_data='new_event'))
        menu.add(InlineKeyboardButton(text="📖 Мероприятия", callback_data='list_events'),
                 InlineKeyboardButton(text="🗄️ Архив", callback_data='admin_archive'))
        menu.add(InlineKeyboardButton(text="👥 Группы", callback_data='list-users'),
                 InlineKeyboardButton(text="🏘️ Резиденты", callback_data='list-residents'))
        menu.add(InlineKeyboardButton(text="📢 Сообщение резидентам", callback_data='notify-users'))
        menu.add(InlineKeyboardButton(text="💰 Цена подписки", callback_data='subscribe-amount'))
        await Menu.main.set()
        await message.answer(f"Здравствуйте, {user['full_name'].split()[1]}!", reply_markup=menu)
        await message.delete()
    elif user:
        menu = InlineKeyboardMarkup(row_width=1)
        menu.add(InlineKeyboardButton(text="🌟 Профиль", callback_data='profile'),
                 InlineKeyboardButton(text="📅 Календарь", callback_data='calendar_handler'),
                 InlineKeyboardButton(text="🏘️ Резиденты", callback_data='list-residents'))

        await Menu.main.set()

        await message.answer(f"Здравствуйте, {user['full_name'].split()[1]}!", reply_markup=menu)
        await message.delete()
    else:
        await Registration.phone_number.set()
        sare_contact = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button = types.KeyboardButton(text="Отправить заявку", request_contact=True)
        sare_contact.add(button)

        await message.reply("Здравствуйте, отправьте заявку на регистрацию:", reply_markup=sare_contact)

        await message.delete()


async def menu_handler(callback: types.CallbackQuery, state: FSMContext):
    menu = InlineKeyboardMarkup(row_width=1)
    user = find_user(callback.from_user.id)
    if callback.from_user.id in admins:
        if not user:
            await registration_admin(callback, callback.from_user.id)
        menu = InlineKeyboardMarkup()
        menu.add(InlineKeyboardButton(text="📅 Управление", callback_data='admin_calendar'),
                 InlineKeyboardButton(text="📅 Мероприятия", callback_data='calendar_handler'))
        menu.add(InlineKeyboardButton(text="➕ Добавить мероприятие", callback_data='new_event'))
        menu.add(InlineKeyboardButton(text="📖 Мероприятия", callback_data='list_events'),
                 InlineKeyboardButton(text="🗄️ Архив", callback_data='admin_archive'))
        menu.add(InlineKeyboardButton(text="👥 Группы", callback_data='list-users'),
                 InlineKeyboardButton(text="🏘️ Резиденты", callback_data='list-residents'))
        menu.add(InlineKeyboardButton(text="📢 Сообщение резидентам", callback_data='notify-users'))
        menu.add(InlineKeyboardButton(text="💰 Цена подписки", callback_data='subscribe-amount'))
        await Menu.main.set()
        await callback.message.edit_text(f"Здравствуйте, {user['full_name'].split()[1]}!", reply_markup=menu)
    elif user:
        menu = InlineKeyboardMarkup(row_width=1)
        menu.add(InlineKeyboardButton(text="🌟 Профиль", callback_data='profile'),
                 InlineKeyboardButton(text="📅 Календарь", callback_data='calendar_handler'),
                 InlineKeyboardButton(text="🏘️ Резиденты", callback_data='list-residents'))

        await Menu.main.set()

        await callback.message.edit_text(f"Здравствуйте, {user['full_name'].split()[1]}!", reply_markup=menu)


async def registration_admin(message, user_id):
    user = Admin(user_id=int(user_id),
                 telegram_first_name=message.from_user.first_name,
                 telegram_last_name=message.from_user.last_name,
                 telegram_user_name=message.from_user.username,
                 full_name='АДМИНИСТРАТОР АДМИНИСТРАТОР АДМИНИСТРАТОР',
                 phone_number='АДМИНИСТРАТОР',
                 description='АДМИНИСТРАТОР',
                 image=None,
                 company_name='АДМИНИСТРАТОР',
                 company_site=None,
                 subscribe_year=datetime.now().year,
                 subscribe_month=datetime.now().month,
                 subscribe_day=datetime.now().day)
    users.insert_one(user())
