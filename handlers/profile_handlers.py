import logging
import re

from config import bot, admins
from database.collection import find_user, update_full_name, update_company_name, update_company_site, events
from modules.bot_states import Menu, ProfileEdit

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from modules.logger import send_log

logging.basicConfig(level=logging.INFO)


async def profile_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Menu.profile)
    user = find_user(callback.from_user.id)

    keyboard = InlineKeyboardMarkup()

    text = f"📋 Ваша анкета:\n\n" \
           f"👤 ФИО: {user['full_name']}\n" \
           f"📞 Номер телефона: +{user['phone_number']}\n" \
           f"🏢 Название компании: {user['company_name']}\n"

    text +=f"\n📋 Описание:\n {user['description']}\n"
    events_data = events.find({'users': {'$in': [user['user_id']]}})
    if events_data:
        text += "\n👤 Вы участвуете в мероприятиях:\n"
        for event in events_data:
            text += f"- {event['name']}\n"

    if user['company_site']:
        keyboard.add(InlineKeyboardButton(text='🌐 Ссылка на сайт', url=user['company_site']))
    if user['video']:
        keyboard.add(InlineKeyboardButton(text='🎬 Видео-карточка', url=user['video']))
    keyboard.add(InlineKeyboardButton(text='📢 Обратная связь', callback_data='send-report'),
                 InlineKeyboardButton(text='🏠 В меню', callback_data='menu'))
    image_path = user['image']
    if image_path:
        await bot.send_photo(callback.from_user.id, photo=types.InputFile(image_path))
    await callback.message.answer(text, parse_mode='HTML', reply_markup=keyboard, disable_web_page_preview=True)
    await callback.message.delete()


async def send_report(callback: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton(text='↩️ Назад', callback_data='profile'))
    await callback.message.edit_text("✉️ Напишите сообщение для администрация:", reply_markup=keyboard)
    await Menu.send_report.set()


async def send_report_send(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='🏠 В меню', callback_data='menu'),
                 InlineKeyboardButton(text='↩️ Назад', callback_data='profile'))
    user = find_user(message.from_user.id)

    keyboard_admin = InlineKeyboardMarkup()
    keyboard_admin.add(InlineKeyboardButton(text='Ответить', callback_data=f"answer-report%{user['_id']}"))

    for admin in admins:
        try:
            await bot.send_message(admin, f"Сообщение от пользователя {user['full_name']}\nНомер телефона: +{user['phone_number']}\n\n" + message.text, reply_markup=keyboard_admin)
            await send_log(f"Пользователь[{user['_id']}] -> [Сообщение] <- {message.text}")
        except:
            pass

    await message.answer("🗣️ Ваше сообщение отправлено администраторам, ожидайте ответ!", reply_markup=keyboard)
    await Menu.main.set()


async def edit_profile_handler(callback: types.CallbackQuery, state: FSMContext):
    edit = InlineKeyboardMarkup(row_width=1)
    full_name = InlineKeyboardButton(text='Изменить ФИО', callback_data='edit_full_name')
    company_name = InlineKeyboardButton(text='Изменить название компании', callback_data='edit_company_name')
    company_site = InlineKeyboardButton(text='Изменить сайт компании', callback_data='edit_company_site')
    back = InlineKeyboardButton(text='В меню', callback_data='menu')
    edit.add(full_name, company_name, company_site, back)

    await callback.message.edit_reply_markup(reply_markup=edit)


async def edit_full_name_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, укажите новое ФИО:")
    await ProfileEdit.full_name.set()


async def edit_full_name(message: types.Message, state: FSMContext):
    pattern = r"^[А-Я][а-я]+\s[А-Я][а-я]+\s[А-Я][а-я]+$"
    if not re.match(pattern, message.text):
        await message.answer('Вы указали неправильно ФИО.\n Пример: Иванов Иван Иванович')
        await ProfileEdit.full_name.set()
        return
    update_full_name(message.from_user.id, message.text)
    await state.set_state(Menu.profile)
    user = find_user(message.from_user.id)

    edit = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text='Редактировать анкету', callback_data='edit_profile')
    back = InlineKeyboardButton(text='В меню', callback_data='menu')
    edit.add(button)
    edit.add(back)

    await message.answer(f"Ваша анкета:\n"
                         f" ФИО: {user['full_name']}\n"
                         f" Номер телефона: {user['phone_number']}\n"
                         f" Название компании: {user['company_name']}\n"
                         f" Сайт компании: <a href='{user['company_site']}'>*клик*</a>\n",
                         parse_mode='HTML', reply_markup=edit, disable_web_page_preview=True)


async def edit_company_name_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, укажите новое название компании:")
    await ProfileEdit.company_name.set()


async def edit_company_name(message: types.Message, state: FSMContext):
    update_company_name(message.from_user.id, message.text)
    await state.set_state(Menu.profile)
    user = find_user(message.from_user.id)

    edit = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text='Редактировать анкету', callback_data='edit_profile')
    back = InlineKeyboardButton(text='В меню', callback_data='menu')
    edit.add(button)
    edit.add(back)

    await message.answer(f"Ваша анкета:\n"
                         f" ФИО: {user['full_name']}\n"
                         f" Номер телефона: {user['phone_number']}\n"
                         f" Название компании: {user['company_name']}\n"
                         f" Сайт компании: <a href='{user['company_site']}'>*перейти*</a>\n",
                         parse_mode='HTML', reply_markup=edit, disable_web_page_preview=True)


async def edit_company_site_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, укажите новую ссылку на сайт:")
    await ProfileEdit.company_site.set()


async def edit_company_site(message: types.Message, state: FSMContext):
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    if not re.match(url_pattern, message.text):
        await message.answer('Вы указали неправильную ссылку, она должна начинаться с http:// или https://.')
        await ProfileEdit.company_site.set()
        return
    update_company_site(message.from_user.id, message.text)
    await state.set_state(Menu.profile)
    user = find_user(message.from_user.id)

    edit = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text='Редактировать анкету', callback_data='edit_profile')
    back = InlineKeyboardButton(text='В меню', callback_data='menu')
    edit.add(button)
    edit.add(back)

    await message.answer(f"Ваша анкета:\n"
                         f" ФИО: {user['full_name']}\n"
                         f" Номер телефона: {user['phone_number']}\n"
                         f" Название компании: {user['company_name']}\n"
                         f" Сайт компании: <a href='{user['company_site']}'>*перейти*</a>\n",
                         parse_mode='HTML', reply_markup=edit, disable_web_page_preview=True)
