
import re
import threading
from modules import loop_handler

import admin_handlers.new_event_handlers
from config import dp, logging, loop, bot, DIR
from modules.bot_states import Registration, Menu, ProfileEdit, AdminNewEvent, AdminArchive

from aiogram import executor, types
from aiogram.dispatcher import FSMContext

from handlers import main_handlers, registration_handlers, profile_handlers, calendar_handlers, residents_handlers
from admin_handlers import new_event_handlers




#  СТРАРТ
@dp.message_handler(commands='start', state='*')
@dp.message_handler(lambda message: message.chat.type == 'private')
async def start(message: types.Message):
    await main_handlers.start(message)
    logging.info(f'start: {message.from_user.id}')


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


# АДМИНКА
# Добавление мероприяия
@dp.callback_query_handler(lambda callback: 'new_event' in callback.data, state=Menu.main)
async def new_event(callback: types.CallbackQuery, state: FSMContext):
    await new_event_handlers.new_event_handler(callback, state)


@dp.callback_query_handler(lambda callback: 'new_event_long' in callback.data or
                                            'new_event_short' in callback.data, state=AdminNewEvent.event_long)
async def new_event_duration(callback: types.CallbackQuery, state: FSMContext):
    await new_event_handlers.new_event_duration(callback, state)


@dp.callback_query_handler(lambda callback: 'start_days' in callback.data, state=AdminNewEvent.event_duration)
async def new_event_name(callback: types.CallbackQuery, state: FSMContext):
    await new_event_handlers.new_event_name(callback, state)


@dp.message_handler(state=AdminNewEvent.event_name)
async def new_event_description(message: types.Message, state: FSMContext):
    await admin_handlers.new_event_handlers.new_event_description(message, state)


@dp.message_handler(state=AdminNewEvent.event_description)
async def new_event_price(message: types.Message, state: FSMContext):
    await admin_handlers.new_event_handlers.new_event_price(message, state)


@dp.message_handler(state=AdminNewEvent.event_services)
async def new_event_services(message: types.Message, state: FSMContext):
    await admin_handlers.new_event_handlers.new_event_services(message, state)


@dp.callback_query_handler(lambda callback: 'add_event_service' in callback.data, state=AdminNewEvent.event_services)
async def new_event_add_service(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.new_event_handlers.new_event_add_service(callback, state)


@dp.message_handler(state=AdminNewEvent.event_services_new)
async def new_event_add_service_price(message: types.Message, state: FSMContext):
    await admin_handlers.new_event_handlers.new_event_add_service_price(message, state)


@dp.message_handler(state=AdminNewEvent.event_add)
async def new_event_add_service_price(message: types.Message, state: FSMContext):
    await admin_handlers.new_event_handlers.new_event_add(message, state)


@dp.callback_query_handler(lambda callback: 'add_event_set_calendar' in callback.data, state=AdminNewEvent.event_services)
async def add_event_set_calendar(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.new_event_handlers.add_event_set_calendar(callback, state)


@dp.callback_query_handler(lambda callback: re.match(r'^new_event_calendar:(.*)', callback.data), state=AdminNewEvent.event_services)
async def add_event_set_calendar(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.new_event_handlers.add_event_set_calendar_process(callback, state)


@dp.callback_query_handler(lambda callback: 'select_time' in callback.data, state=AdminNewEvent.event_services)
async def add_event_set_time(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.new_event_handlers.add_event_set_time(callback, state)

# Список мероприятий
@dp.callback_query_handler(lambda callback: 'list_events' in callback.data, state=Menu.main)
async def list_events(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.list_events_public(callback, state)


@dp.callback_query_handler(lambda callback: 'events_list' in callback.data, state=Menu.main)
async def list_events_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.list_events_select(callback, state)

# Календарь мероприятий
@dp.callback_query_handler(lambda callback: 'admin_calendar' in callback.data, state=Menu.main)
async def admin_calendar(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.admin_calendar(callback, state)


@dp.callback_query_handler(lambda callback: 'admin_event_calendar' in callback.data, state='*')
async def admin_calendar_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.admin_calendar_select(callback, state)


# Архив мероприятий
@dp.callback_query_handler(lambda callback: 'admin_archive' in callback.data, state=Menu.main)
async def archive_list(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.archive_handlers.archive_list(callback, state)


@dp.callback_query_handler(lambda callback: 'archive_list' in callback.data, state=AdminArchive)
async def archive_list_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.archive_handlers.archive_list_select(callback, state)


@dp.callback_query_handler(lambda callback: 'archive-add-images' in callback.data, state=AdminArchive)
async def archive_add_images(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.archive_handlers.archive_add_images(callback, state)


@dp.message_handler(content_types=['photo'], state=AdminArchive.add_images)
async def archive_add_images_download(message: types.Message, state: FSMContext):
    await admin_handlers.archive_handlers.archive_add_images_download(message, state)


@dp.callback_query_handler(lambda callback: 'archive-add-video' in callback.data, state=AdminArchive)
async def archive_add_video(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.archive_handlers.archive_add_video(callback, state)


@dp.message_handler(content_types=['video'], state=AdminArchive.add_video)
async def archive_add_video_download(message: types.Message, state: FSMContext):
    await admin_handlers.archive_handlers.archive_add_video_download(message, state)


@dp.callback_query_handler(lambda callback: 'archive-add-link' in callback.data, state=AdminArchive)
async def archive_add_link(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.archive_handlers.archive_add_link(callback, state)


@dp.message_handler(state=AdminArchive.add_link)
async def archive_add_link_set(message: types.Message, state: FSMContext):
    await admin_handlers.archive_handlers.archive_add_link_set(message, state)

@dp.message_handler(state='*')
async def non_state(message):
    await message.delete()
    print(message.chat.id)

loop.create_task(loop_handler.spreader())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
