import re

from bson import ObjectId

import handlers.calendar_handlers
from database.collection import db_config
from modules import loop_handler

import admin_handlers.new_event_handlers
from config import dp, logging, loop, bot, DIR, banned_users, wait_registration, referral_link, admins, SUBSCRIBE_AMOUNT
from modules.bot_states import Registration, Menu, ProfileEdit, AdminNewEvent, AdminArchive, EventSubscribe, \
    AdminEditEvent, EditUser

from aiogram import executor, types
from aiogram.dispatcher import FSMContext

from handlers import main_handlers, registration_handlers, profile_handlers, calendar_handlers, residents_handlers
from admin_handlers import new_event_handlers

from aiogram.utils.executor import start_webhook

WEBHOOK_HOST = 'https://zed228.alwaysdata.net/'
WEBHOOK_PATH = ''
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = '::'  # or ip
WEBAPP_PORT = 8350


# ПОДПИСКА
@dp.pre_checkout_query_handler(state=EventSubscribe)
async def event_payment_pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.pre_checkout_query_handler(state='*')
async def event_payment_pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT, state='*')
async def event_payment_checkout(message: types.Message, state: FSMContext):
    if 'event-sub' in message.successful_payment.invoice_payload:
        await handlers.subscribe_handlers.event_payment_checkout(message, state)
    if 'user-sub' in message.successful_payment.invoice_payload:
        await handlers.subscribe_handlers.subscribe_payment_checkout(message, state)


@dp.callback_query_handler(lambda callback: 'user-subscribe' in callback.data, state='*')
async def subscribe_payment_receipt(callback: types.CallbackQuery, state: FSMContext):
    await handlers.subscribe_handlers.subscribe_payment_receipt(callback, state)


#  СТРАРТ
@dp.message_handler(lambda message: message.from_user.id in banned_users, state='*')
async def handle_banned(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Оформить подписку', callback_data='user-subscribe'))
    await message.answer('Оформить подписку', reply_markup=keyboard)


@dp.message_handler(lambda message: message.from_user.id in wait_registration, state='*')
async def handle_registration(message: types.Message):
    await message.answer('Вашу заявку еще рассматривают, ожидайте')


@dp.callback_query_handler(lambda callback: callback.message.chat.id in banned_users, state='*')
async def handle_banned(callback: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Оформить подписку', callback_data='user-subscribe'))
    await callback.message.edit_text('Оформить подписку', reply_markup=keyboard)


@dp.message_handler(commands='start', state='*')
async def start(message: types.Message):
    await main_handlers.start(message)


#  РЕГИСТРАЦИЯ

@dp.message_handler(content_types=types.ContentType.CONTACT, state=Registration.phone_number)
async def registration_send(message: types.Message, state: FSMContext):
    await registration_handlers.registration_send(message, state)

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


@dp.callback_query_handler(lambda callback: re.match(r'^event_calendar:(.*)', callback.data), state='*')
async def event_calendar_selected_handler(callback: types.CallbackQuery, state: FSMContext):
    await calendar_handlers.event_calendar_selected_handler(callback, state)


#  РЕЗИДЕНТ
@dp.callback_query_handler(lambda callback: 'list-residents' in callback.data, state=Menu.main)
async def residents_handler(callback: types.CallbackQuery, state: FSMContext):
    await residents_handlers.residents_handler(callback, state)


@dp.callback_query_handler(lambda callback: 'residents_list' in callback.data, state=Menu)
async def residents_handler_select(callback: types.CallbackQuery, state: FSMContext):
    await residents_handlers.residents_handler_select(callback, state)


# МЕНЮ
@dp.callback_query_handler(lambda callback: 'menu' in callback.data, state='*')
async def menu_handler(callback: types.CallbackQuery, state: FSMContext):
    await main_handlers.menu_handler(callback, state)


# ПОДПИСКА НА ИВЕНТ
@dp.callback_query_handler(lambda callback: 'subscribe-event' in callback.data, state=Menu)
async def event_subscribe(callback: types.CallbackQuery, state: FSMContext):
    await handlers.subscribe_handlers.event_subscribe(callback, state)


@dp.callback_query_handler(lambda callback: 'subscribe-event-select' in callback.data
                                            or 'subscribe-event-delete' in callback.data, state=EventSubscribe)
async def event_subscribe_select(callback: types.CallbackQuery, state: FSMContext):
    await handlers.subscribe_handlers.event_subscribe_select(callback, state)


@dp.callback_query_handler(lambda callback: 'event_payment_receipt' in callback.data, state=EventSubscribe)
async def event_payment_receipt(callback: types.CallbackQuery, state: FSMContext):
    await handlers.subscribe_handlers.event_payment_receipt(callback, state)


@dp.callback_query_handler(lambda callback: 'payment-check' in callback.data, state='*')
async def event_payment_receipt(callback: types.CallbackQuery, state: FSMContext):
    await handlers.subscribe_handlers.payment_check(callback, state)


# АРХИВ
@dp.callback_query_handler(lambda callback: 'archive-images' in callback.data, state=Menu.archive)
async def archive_selected_images(callback: types.CallbackQuery, state: FSMContext):
    await handlers.calendar_handlers.archive_selected_images(callback, state)


@dp.callback_query_handler(lambda callback: 'archive-video' in callback.data, state=Menu.archive)
async def archive_selected_video(callback: types.CallbackQuery, state: FSMContext):
    await handlers.calendar_handlers.archive_selected_video(callback, state)


# АДМИНКА
#Пользователи
@dp.callback_query_handler(lambda callback: 'list-users' in callback.data, state=Menu.main)
async def list_users(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_users(callback, state)


@dp.callback_query_handler(lambda callback: 'list-rusers' in callback.data, state=Menu.main)
async def list_residents(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_residents(callback, state)


@dp.callback_query_handler(lambda callback: 'rusers_list' in callback.data, state='*')
async def list_residents_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_residents_select(callback, state)


@dp.callback_query_handler(lambda callback: 'list-ausers' in callback.data, state=Menu.main)
async def list_admins(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_admins(callback, state)


@dp.callback_query_handler(lambda callback: 'admins_list' in callback.data, state=Menu.main)
async def list_admins_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_admins_select(callback, state)


@dp.callback_query_handler(lambda callback: 'list-wusers' in callback.data, state=Menu.main)
async def list_waiting(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_waiting(callback, state)


@dp.callback_query_handler(lambda callback: 'waiting_list' in callback.data, state=Menu.main)
async def list_waiting_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_waiting_select(callback, state)


@dp.callback_query_handler(lambda callback: 'add-admin' in callback.data, state='*')
async def new_admin(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.registration_handlers.new_admin(callback, state)


#Редактирование пользователя
@dp.callback_query_handler(lambda callback: 'edit-user-full_name' in callback.data, state='*')
async def edit_user_full_name(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_full_name(callback, state)


@dp.message_handler(state=EditUser.full_name)
async def edit_user_full_name_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_full_name_set(message, state)


@dp.callback_query_handler(lambda callback: 'edit-user-phone_number' in callback.data, state='*')
async def edit_user_phone_number(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_phone_number(callback, state)


@dp.message_handler(state=EditUser.phone_number)
async def edit_user_phone_number_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_phone_number_set(message, state)


@dp.callback_query_handler(lambda callback: 'edit-user-description' in callback.data, state='*')
async def edit_user_description(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_description(callback, state)


@dp.message_handler(state=EditUser.description)
async def edit_user_description_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_description_set(message, state)


@dp.callback_query_handler(lambda callback: 'edit-user-company_name' in callback.data, state='*')
async def edit_user_company_name(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_company_name(callback, state)


@dp.message_handler(state=EditUser.company_name)
async def edit_user_company_name_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_company_name_set(message, state)


@dp.callback_query_handler(lambda callback: 'edit-user-company_site' in callback.data, state='*')
async def edit_user_company_site(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_company_site(callback, state)


@dp.message_handler(state=EditUser.company_site)
async def edit_user_company_site_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_company_site_set(message, state)


@dp.callback_query_handler(lambda callback: 'edit-user-image' in callback.data, state='*')
async def edit_user_image(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_image(callback, state)


@dp.message_handler(content_types=['photo'], state=EditUser.image)
async def edit_user_image_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_image_set(message, state)


@dp.callback_query_handler(lambda callback: 'delete-user' in callback.data, state='*')
async def delete_user(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.delete_user(callback, state)


@dp.message_handler(state=EditUser.delete)
async def delete_user_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.delete_user_set(message, state)


#Регистрация
@dp.callback_query_handler(lambda callback: 'add-user' in callback.data, state='*')
async def new_user(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.registration_handlers.registration_full_name(callback, state)


@dp.message_handler(state=Registration.full_name)
async def registration_description(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.registration_description(message, state)


@dp.message_handler(state=Registration.description)
async def registration_company_name(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.registration_company_name(message, state)


@dp.message_handler(state=Registration.company_name)
async def registration_company_site(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.registration_company_site(message, state)


@dp.message_handler(state=Registration.company_site)
async def registration_image(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.registration_image(message, state)


@dp.message_handler(content_types=['photo'], state=Registration.image)
async def end_registration(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.end_registration(message, state)


@dp.message_handler(state=Registration.image)
async def end_registration_no_image(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.end_registration_no_image(message, state)


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


@dp.callback_query_handler(lambda callback: 'add_event_set_calendar' in callback.data,
                           state=AdminNewEvent.event_services)
async def add_event_set_calendar(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.new_event_handlers.add_event_set_calendar(callback, state)


@dp.callback_query_handler(lambda callback: re.match(r'^new_event_calendar:(.*)', callback.data),
                           state=AdminNewEvent.event_services)
async def add_event_set_calendar(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.new_event_handlers.add_event_set_calendar_process(callback, state)


@dp.callback_query_handler(lambda callback: 'select_time' in callback.data, state=AdminNewEvent.event_services)
async def add_event_set_time(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.new_event_handlers.add_event_set_time(callback, state)


# Редактирование мероприятия
@dp.callback_query_handler(lambda callback: 'public-event' in callback.data, state='*')
async def publication_event(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.publication_event(callback, state)


@dp.callback_query_handler(lambda callback: 'event-edit-name' in callback.data, state='*')
async def event_edit_name(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_name(callback, state)


@dp.message_handler(state=AdminEditEvent.event_name)
async def event_edit_name_set(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_name_set(message, state)


@dp.callback_query_handler(lambda callback: 'event-edit-description' in callback.data, state='*')
async def event_edit_description(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_description(callback, state)


@dp.message_handler(state=AdminEditEvent.event_description)
async def event_edit_description_set(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_description_set(message, state)


@dp.callback_query_handler(lambda callback: 'event-edit-price' in callback.data, state='*')
async def event_edit_price(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_price(callback, state)


@dp.message_handler(state=AdminEditEvent.event_price)
async def event_edit_price_set(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_price_set(message, state)


@dp.callback_query_handler(lambda callback: 'event-edit-services' in callback.data, state='*')
async def event_edit_services(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_services(callback, state)


@dp.callback_query_handler(lambda callback: 'event-edit-service' in callback.data, state=AdminEditEvent.event_services)
async def event_edit_service_description(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_description(callback, state)


@dp.message_handler(state=AdminEditEvent.event_service_description)
async def event_edit_service_description_set(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_description_set(message, state)


@dp.message_handler(state=AdminEditEvent.event_service_price)
async def event_edit_service_price_set(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_price_set(message, state)


@dp.callback_query_handler(lambda callback: 'event-delete-service' in callback.data, state='*')
async def event_edit_service_delete(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_delete(callback, state)


@dp.callback_query_handler(lambda callback: 'event-edit-add-service' in callback.data, state=AdminEditEvent.event_services)
async def event_edit_service_add(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_add(callback, state)


@dp.message_handler(state=AdminEditEvent.event_new_service_description)
async def event_edit_service_add_description(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_add_description(message, state)


@dp.message_handler(state=AdminEditEvent.event_new_service_price)
async def event_edit_service_add_price(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_price_set(message, state)

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


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    conf = db_config.find_one({'_id': ObjectId('659c6a3d1e2c9f558337a9b2')})
    SUBSCRIBE_AMOUNT = conf['SUBSCRIBE_AMOUNT']
    for user in conf['banned_users']:
        banned_users.add(user)
    for user in conf['wait_registration']:
        wait_registration.add(user)
    for user in conf['admins']:
        admins.add(user)
    # insert code here to run it after start


async def on_shutdown(dp):
    db_config.update_one({'_id': ObjectId('659c6a3d1e2c9f558337a9b2')}, {
        '$set': {'banned_users': [user for user in banned_users],
                 'wait_registration': [user for user in wait_registration],
                 'admins': [user for user in admins],
                 'SUBSCRIBE_AMOUNT': SUBSCRIBE_AMOUNT}})
    logging.warning('Shutting down..')
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()

    logging.warning('Bye!')


if __name__ == '__main__':
    loop.create_task(loop_handler.spreader())
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)

    #start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown,
                  #skip_updates=True, host=WEBAPP_HOST, port=WEBAPP_PORT)
