import logging
from datetime import datetime

from database.collection import find_user, users
from database.models import User, Admin
from modules.bot_states import Menu, Registration

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import admins, referral_link, CHAT, CHANNEL, bot, DIR
from modules.logger import send_log



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
                 InlineKeyboardButton(text="📅 Просмотр", callback_data='calendar_handler'))
        menu.add(InlineKeyboardButton(text="➕ Добавить мероприятие", callback_data='new_event'))
        menu.add(InlineKeyboardButton(text="📖 Список", callback_data='list_events'),
                 InlineKeyboardButton(text="🗄️ Архив", callback_data='admin_archive'))
        menu.add(InlineKeyboardButton(text="👥 Группы", callback_data='list-users'),
                 InlineKeyboardButton(text="🏘️ Резиденты", callback_data='list-residents'))
        menu.add(InlineKeyboardButton(text="📢 Сообщение резидентам", callback_data='notify-all-users'))
        menu.add(InlineKeyboardButton(text="💰 Цена подписки", callback_data='subscribe-amount'))
        await Menu.main.set()
        await message.answer(f"Здравствуйте, {user['full_name'].split()[1]}!", reply_markup=menu)
        await message.delete()
    elif user:
        link_channel = await bot.export_chat_invite_link(CHANNEL)
        link_chat = await bot.export_chat_invite_link(CHAT)
        menu = InlineKeyboardMarkup()
        menu.add(InlineKeyboardButton(text="🌟 Профиль", callback_data='profile'))
        menu.add(InlineKeyboardButton(text="📅 Календарь", callback_data='calendar_handler'))
        menu.add(InlineKeyboardButton(text="🏘️ Резиденты", callback_data='list-residents'))
        menu.add(InlineKeyboardButton(text='🎥 Видео Babr', url='https://disk.yandex.ru/d/_1G5zkyCbW5t3Q'))
        menu.add(InlineKeyboardButton(text='👍 Полезные ссылки', url='https://docs.google.com/spreadsheets/d/1BdqC6wMGKos8AxQrwobNbspLGhPB8x9-mhqfgfDAE6s/edit?usp=sharing'))
        menu.add(InlineKeyboardButton(text='📣 Наш канал', url=link_channel),
                 InlineKeyboardButton(text='💬 Наш чат', url=link_chat))

        await Menu.main.set()

        await message.answer(f"Здравствуйте, {user['full_name'].split()[1]}!", reply_markup=menu)
        await message.delete()
    else:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton('👉 Начать 👈', callback_data='start-search'))

        text = ' Здравствуй, я бот бизнес-клуба "БАБР"\n\n Вы еще не зарегистрированы, я попробую найти Вас в своей базе..\n\n\n👇 Нажмите кнопку ниже'
        await bot.send_photo(message.from_user.id, caption=text, photo=types.InputFile(f'{DIR}/hello.jpg'), reply_markup=keyboard)

        await message.delete()


async def start_search(callback: types.CallbackQuery, state: FSMContext):
    await Registration.phone_number.set()
    sare_contact = types.ReplyKeyboardMarkup(resize_keyboard=False, one_time_keyboard=True, input_field_placeholder='Нажмите на кнопку', is_persistent=True)
    sare_contact.add(types.KeyboardButton(text="👉 Отправить контакт 👈", request_contact=True))

    await callback.message.answer('👍 Отлично!\n\n\nА теперь нажмите <b>кнопку ниже</b>, она позволит мне проверить Вас по номеру телефона 👇' , reply_markup=sare_contact, parse_mode='HTML')


async def menu_handler(callback: types.CallbackQuery, state: FSMContext):
    user = find_user(callback.from_user.id)
    if callback.from_user.id in admins:
        if not user:
            await registration_admin(callback, callback.from_user.id)
        menu = InlineKeyboardMarkup()
        menu.add(InlineKeyboardButton(text="📅 Управление", callback_data='admin_calendar'),
                 InlineKeyboardButton(text="📅 Просмотр", callback_data='calendar_handler'))
        menu.add(InlineKeyboardButton(text="➕ Добавить мероприятие", callback_data='new_event'))
        menu.add(InlineKeyboardButton(text="📖 Список", callback_data='list_events'),
                 InlineKeyboardButton(text="🗄️ Архив", callback_data='admin_archive'))
        menu.add(InlineKeyboardButton(text="👥 Группы", callback_data='list-users'),
                 InlineKeyboardButton(text="🏘️ Резиденты", callback_data='list-residents'))
        menu.add(InlineKeyboardButton(text="📢 Сообщение резидентам", callback_data='notify-all-users'))
        menu.add(InlineKeyboardButton(text="💰 Цена подписки", callback_data='subscribe-amount'))
        await Menu.main.set()
        await callback.message.edit_text(f"Здравствуйте, {user['full_name'].split()[1]}!", reply_markup=menu)
    elif user:
        link_channel = await bot.export_chat_invite_link(CHANNEL)
        link_chat = await bot.export_chat_invite_link(CHAT)

        menu = InlineKeyboardMarkup()
        menu.add(InlineKeyboardButton(text="🌟 Профиль", callback_data='profile'))
        menu.add(InlineKeyboardButton(text="📅 Календарь", callback_data='calendar_handler'))
        menu.add(InlineKeyboardButton(text="🏘️ Резиденты", callback_data='list-residents'))
        menu.add(InlineKeyboardButton(text='🎥 Видео Babr', url='https://disk.yandex.ru/d/_1G5zkyCbW5t3Q'))
        menu.add(InlineKeyboardButton(text='👍 Полезные ссылки',
                                      url='https://docs.google.com/spreadsheets/d/1BdqC6wMGKos8AxQrwobNbspLGhPB8x9-mhqfgfDAE6s/edit?usp=sharing'))
        menu.add(InlineKeyboardButton(text='📣 Наш канал', url=link_channel),
                 InlineKeyboardButton(text='💬 Наш чат', url=link_chat))
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
                 video='',
                 company_name='АДМИНИСТРАТОР',
                 company_site=None,
                 subscribe=1111)
    users.insert_one(user())
