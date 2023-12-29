import logging
import re

from config import bot, dp
from models import users, find_user, update_full_name, update_company_name, update_company_site, User
from bot_states import Registration, Menu, ProfileEdit

from aiogram import executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)


#  СТРАРТ
@dp.message_handler(commands='start', state='*')
@dp.message_handler(lambda message: message.chat.type == 'private')
async def start(message: types.Message):
    await message.delete()

    keyboard = InlineKeyboardMarkup(row_width=2)
    no = InlineKeyboardButton(text='Нет', callback_data='cancel_reg')
    yes = InlineKeyboardButton(text='Да', callback_data='start_reg')
    keyboard.add(no, yes)

    menu = InlineKeyboardMarkup(row_width=1)
    profile = InlineKeyboardButton(text="Профиль", callback_data='profile')
    calendar = InlineKeyboardButton(text="Календарь", callback_data='calendar')
    residents = InlineKeyboardButton(text="Резиденты", callback_data='residents')
    menu.add(profile, calendar, residents)

    user = find_user(message.from_user.id)
    if user:
        await Menu.main.set()
        await message.answer(f"Здравствуйте, {user['full_name'].split()[1]}!", reply_markup=menu)
    else:
        await message.answer(f'Здравствуйте, сейчас Вам потребуется пройти небольшое анкетирование. Вы готовы?',
                             reply_markup=keyboard)


@dp.callback_query_handler(lambda callback: 'cancel_reg' in callback.data)
async def cancel_registration(callback: types.CallbackQuery):
    await callback.message.answer('ok')
    await callback.message.delete()
    await start(callback.message)


#  РЕГИСТРАЦИЯ
@dp.callback_query_handler(lambda callback: callback.data == 'start_reg')
async def registration_full_name(callback: types.CallbackQuery):
    await Registration.full_name.set()
    await callback.message.delete()
    await callback.message.answer("Пожалуйста, укажите ФИО")


@dp.message_handler(state=Registration.full_name)
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


@dp.message_handler(content_types=types.ContentType.CONTACT, state=Registration.phone_number)
async def registration_company_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone_number'] = message.contact.phone_number
    await Registration.next()
    remove_keyboard = types.ReplyKeyboardRemove()
    await message.reply("Укажите название Вашей компании:", reply_markup=remove_keyboard)


@dp.message_handler(state=Registration.company_name)
async def registration_company_site(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['company_name'] = message.text
    await Registration.next()
    await message.reply("Укажите сайт Вашей компании:")


@dp.message_handler(state=Registration.company_site)
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

    user = User(int(message.from_user.id),
                message.from_user.first_name,
                message.from_user.last_name,
                message.from_user.username,
                full_name,
                phone_number,
                company_name,
                company_site)
    users.insert_one(user())

    await message.answer("Ваша анкета:\n"
                         f" ФИО: {full_name}\n"
                         f" Номер телефона: {phone_number}\n"
                         f" Название компании: {company_name}\n"
                         f" Сайт компании: <a href='{company_site}'>*клик*</a>\n\n"
                         "Спасибо за информацию!",
                         parse_mode='HTML')


#   ПРОФИЛЬ И РЕДАКТИРОВАНИЕ
@dp.callback_query_handler(lambda callback: 'profile' in callback.data, state=Menu.main)
async def profile_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Menu.profile)
    user = find_user(callback.message.chat.id)

    edit = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text='Редактировать анкету', callback_data='edit_profile')
    back = InlineKeyboardButton(text='В меню', callback_data='menu')
    edit.add(button)
    edit.add(back)

    await callback.message.edit_text(f"Ваша анкета:\n"
                                     f" ФИО: {user['full_name']}\n"
                                     f" Номер телефона: {user['phone_number']}\n"
                                     f" Название компании: {user['company_name']}\n"
                                     f" Сайт компании: <a href='{user['company_site']}'>*клик*</a>\n",
                                     parse_mode='HTML', reply_markup=edit)


@dp.callback_query_handler(lambda callback: 'edit_profile' in callback.data, state=Menu.profile)
async def edit_profile_handler(callback: types.CallbackQuery, state: FSMContext):
    edit = InlineKeyboardMarkup(row_width=1)
    full_name = InlineKeyboardButton(text='Изменить ФИО', callback_data='edit_full_name')
    company_name = InlineKeyboardButton(text='Изменить название компании', callback_data='edit_company_name')
    company_site = InlineKeyboardButton(text='Изменить сайт компании', callback_data='edit_company_site')
    back = InlineKeyboardButton(text='В меню', callback_data='menu')
    edit.add(full_name, company_name, company_site, back)

    await callback.message.edit_reply_markup(reply_markup=edit)


@dp.callback_query_handler(lambda callback: 'edit_full_name' in callback.data, state=Menu.profile)
async def edit_full_name_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, укажите новое ФИО:")
    await ProfileEdit.full_name.set()


@dp.message_handler(state=ProfileEdit.full_name)
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
                         parse_mode='HTML', reply_markup=edit)


@dp.callback_query_handler(lambda callback: 'edit_company_name' in callback.data, state=Menu.profile)
async def edit_company_name_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, укажите новое название компании:")
    await ProfileEdit.company_name.set()


@dp.message_handler(state=ProfileEdit.company_name)
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
                         f" Сайт компании: <a href='{user['company_site']}'>*клик*</a>\n",
                         parse_mode='HTML', reply_markup=edit)


@dp.callback_query_handler(lambda callback: 'edit_company_site' in callback.data, state=Menu.profile)
async def edit_company_site_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, укажите новую ссылку на сайт:")
    await ProfileEdit.company_site.set()


@dp.message_handler(state=ProfileEdit.company_site)
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
                         f" Сайт компании: <a href='{user['company_site']}'>*клик*</a>\n",
                         parse_mode='HTML', reply_markup=edit)


#   КАЛЕНДАРЬ
@dp.message_handler(text="Календарь", state=Menu.main)
async def calendar_handler(message: types.Message, state: FSMContext):
    await state.set_state(Menu.calendar)
    pass


#  РЕЗИДЕНТЫ
@dp.callback_query_handler(lambda callback: 'residents' in callback.data, state=Menu.main)
async def residents_handler(callback: types.CallbackQuery, state: FSMContext):
    all_users = users.find()
    residents = InlineKeyboardMarkup(row_width=1)
    for user in all_users:
        name = user['full_name'].split()
        residents.add(InlineKeyboardButton(text=f"{name[0]} {name[1][0]}.{name[2][0]}.",
                                           callback_data=f"resident-{user['user_id']}"))
    back = InlineKeyboardButton(text='В меню', callback_data='menu')
    residents.add(back)
    await callback.message.edit_text('Резиденты:', reply_markup=residents)


@dp.callback_query_handler(lambda callback: re.match(r'^resident-\d+$', callback.data), state=Menu.main)
async def resident_info(callback: types.CallbackQuery, state: FSMContext):
    back = InlineKeyboardMarkup(row_width=1)
    back.add(InlineKeyboardButton(text='Назад', callback_data='residents'))

    user_id = callback.data.split('-')[1]
    user = find_user(user_id)
    name = user['full_name'].split()
    telegram_user_name = user['telegram_user_name']
    text = f"Информация о {name[0]} {name[1][0]}.{name[2][0]}.:\n"
    if telegram_user_name:
        text += f" Тег: @{telegram_user_name}\n"
    text += f" Номер телефона: +{user['phone_number']}\n" \
            f" Компания: {user['company_name']}\n" \
            f" Сайт компании: <a href='{user['company_site']}'>*клик*</a>"

    await callback.message.edit_text(text, parse_mode='HTML', reply_markup=back)


@dp.callback_query_handler(lambda callback: 'menu' in callback.data, state='*')
async def menu_handler(callback: types.CallbackQuery, state: FSMContext):
    menu = InlineKeyboardMarkup(row_width=1)
    profile = InlineKeyboardButton(text="Профиль", callback_data='profile')
    calendar = InlineKeyboardButton(text="Календарь", callback_data='calendar')
    residents = InlineKeyboardButton(text="Резиденты", callback_data='residents')
    menu.add(profile, calendar, residents)

    await state.set_state(Menu.main)
    await callback.message.edit_text('Главное меню:', reply_markup=menu)


@dp.message_handler(state='*')
async def non_state(message):
    await message.delete()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
