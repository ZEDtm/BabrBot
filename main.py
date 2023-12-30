import logging
import re

from config import dp
from modules.bot_states import Registration, Menu, ProfileEdit

from aiogram import executor, types
from aiogram.dispatcher import FSMContext

from handlers import main_handlers, registration_handlers, profile_handlers, calendar_handlers, residents_handlers

logging.basicConfig(level=logging.INFO)


#  СТРАРТ
@dp.message_handler(commands='start', state='*')
@dp.message_handler(lambda message: message.chat.type == 'private')
async def start(message: types.Message):
    await main_handlers.start(message)


#  РЕГИСТРАЦИЯ
@dp.callback_query_handler(lambda callback: 'cancel_reg' in callback.data)
async def cancel_registration(callback: types.CallbackQuery):
    await registration_handlers.cancel_registration(callback)


@dp.callback_query_handler(lambda callback: callback.data == 'start_reg')
async def registration_full_name(callback: types.CallbackQuery):
    await registration_handlers.registration_full_name(callback)


@dp.message_handler(state=Registration.full_name)
async def registration_phone_number(message: types.Message, state: FSMContext):
    await registration_handlers.registration_phone_number(message, state)


@dp.message_handler(content_types=types.ContentType.CONTACT, state=Registration.phone_number)
async def registration_company_name(message: types.Message, state: FSMContext):
    await registration_handlers.registration_company_name(message, state)


@dp.message_handler(state=Registration.company_name)
async def registration_company_site(message: types.Message, state: FSMContext):
    await registration_handlers.registration_company_site(message, state)


@dp.message_handler(state=Registration.company_site)
async def end_registration(message: types.Message, state: FSMContext):
    await registration_handlers.end_registration(message, state)


#   ПРОФИЛЬ И РЕДАКТИРОВАНИЕ
@dp.callback_query_handler(lambda callback: 'profile' in callback.data, state=Menu.main)
async def profile_handler(callback: types.CallbackQuery, state: FSMContext):
    await profile_handlers.profile_handler(callback, state)


@dp.callback_query_handler(lambda callback: 'edit_profile' in callback.data, state=Menu.profile)
async def edit_profile_handler(callback: types.CallbackQuery, state: FSMContext):
    await profile_handlers.edit_profile_handler(callback, state)


@dp.callback_query_handler(lambda callback: 'edit_full_name' in callback.data, state=Menu.profile)
async def edit_full_name_handler(callback: types.CallbackQuery, state: FSMContext):
    await profile_handlers.edit_full_name_handler(callback, state)


@dp.message_handler(state=ProfileEdit.full_name)
async def edit_full_name(message: types.Message, state: FSMContext):
    await profile_handlers.edit_full_name(message, state)


@dp.callback_query_handler(lambda callback: 'edit_company_name' in callback.data, state=Menu.profile)
async def edit_company_name_handler(callback: types.CallbackQuery, state: FSMContext):
    await profile_handlers.edit_company_name_handler(callback, state)


@dp.message_handler(state=ProfileEdit.company_name)
async def edit_company_name(message: types.Message, state: FSMContext):
    await profile_handlers.edit_company_name(message, state)


@dp.callback_query_handler(lambda callback: 'edit_company_site' in callback.data, state=Menu.profile)
async def edit_company_site_handler(callback: types.CallbackQuery, state: FSMContext):
    await profile_handlers.edit_company_site_handler(callback, state)


@dp.message_handler(state=ProfileEdit.company_site)
async def edit_company_site(message: types.Message, state: FSMContext):
    await profile_handlers.edit_company_site(message, state)


#   КАЛЕНДАРЬ
@dp.callback_query_handler(lambda callback: 'calendar_handler' in callback.data, state=Menu.main)
async def calendar_handler(callback: types.CallbackQuery, state: FSMContext):
    await calendar_handlers.events_calendar_handler(callback, state)


@dp.callback_query_handler(lambda callback: re.match(r'^event_calendar:(.*)', callback.data), state=Menu.calendar)
async def event_calendar_selected_handler(callback: types.CallbackQuery, state: FSMContext):
    await calendar_handlers.event_calendar_selected_handler(callback, state)


#  РЕЗИДЕНТ
@dp.callback_query_handler(lambda callback: 'residents' in callback.data, state=Menu.main)
async def residents_handler(callback: types.CallbackQuery, state: FSMContext):
    await residents_handlers.residents_handler(callback, state)


@dp.callback_query_handler(lambda callback: re.match(r'^resident-\d+$', callback.data), state=Menu.main)
async def resident_info(callback: types.CallbackQuery, state: FSMContext):
    await residents_handlers.resident_info(callback, state)


# МЕНЮ
@dp.callback_query_handler(lambda callback: 'menu' in callback.data, state='*')
async def menu_handler(callback: types.CallbackQuery, state: FSMContext):
    await main_handlers.menu_handler(callback, state)


@dp.message_handler(state='*')
async def non_state(message):
    await message.delete()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
