import re
import logging
from datetime import datetime
from database.collection import users
from database.models import User
from modules.bot_states import Registration

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)


async def cancel_registration(callback: types.CallbackQuery):
    await callback.message.answer('ok')
    await callback.message.delete()


async def registration_full_name(callback: types.CallbackQuery):
    await Registration.full_name.set()
    await callback.message.delete()
    await callback.message.answer("Пожалуйста, укажите ФИО")


async def registration_phone_number(message: types.Message, state: FSMContext):
    pattern = r"^[А-Я][а-я]+\s[А-Я][а-я]+\s[А-Я][а-я]+$"
    if not re.match(pattern, message.text):
        await message.answer('Вы указали неправильно ФИО.\n Пример: Иванов Иван Иванович')
        await Registration.full_name.set()
        return

    async with state.proxy() as data:
        data['full_name'] = message.text
    await Registration.next()

    sare_contact = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton(text="Поделиться контактом", request_contact=True)
    sare_contact.add(button)

    await message.reply("Укажите Ваш номер телефона:", reply_markup=sare_contact)


async def registration_company_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone_number'] = message.contact.phone_number
    await Registration.next()
    remove_keyboard = types.ReplyKeyboardRemove()
    await message.reply("Укажите название Вашей компании:", reply_markup=remove_keyboard)


async def registration_company_site(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['company_name'] = message.text
    await Registration.next()
    await message.reply("Укажите сайт Вашей компании:")


async def end_registration(message: types.Message, state: FSMContext):
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    if not re.match(url_pattern, message.text):
        await message.answer('Вы указали неправильную ссылку, она должна начинаться с http:// или https://.')
        await Registration.company_site.set()
        return

    async with state.proxy() as data:

        data['company_site'] = message.text
    async with state.proxy() as data:
        full_name = data['full_name']
        phone_number = data['phone_number']
        company_name = data['company_name']
        company_site = data['company_site']
    await state.finish()

    user = User(user_id=int(message.from_user.id),
                telegram_first_name=message.from_user.first_name,
                telegram_last_name=message.from_user.last_name,
                telegram_user_name=message.from_user.username,
                full_name=full_name,
                phone_number=phone_number,
                company_name=company_name,
                company_site=company_site,
                events=[],
                admin=False,
                subscribe_year=datetime.now().year,
                subscribe_month=datetime.now().month,
                subscribe_day=datetime.now().day)
    users.insert_one(user())

    edit = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text='Редактировать анкету', callback_data='edit_profile')
    back = InlineKeyboardButton(text='В меню', callback_data='menu')
    edit.add(button)
    edit.add(back)

    await message.answer("📋 Ваша анкета:\n"
                         f"👨‍💼 ФИО: {full_name}\n"
                         f"📞 Номер телефона: {phone_number}\n"
                         f"🏢 Название компании: {company_name}\n"
                         f"📰 Сайт компании: <a href='{company_site}'>*перейти*</a>\n\n"
                         "Спасибо за информацию 🤝!",
                         parse_mode='HTML', reply_markup=edit, disable_web_page_preview=True)
