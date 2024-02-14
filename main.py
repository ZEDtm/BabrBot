import re
from datetime import datetime

from aiogram.types import Update
from bson import ObjectId

import handlers.calendar_handlers
import modules.payment_module
from database.collection import db_config, events, users

import admin_handlers.new_event_handlers
from config import logging, bot, DIR, banned_users, wait_registration, referral_link, admins, \
    subscribe_amount, CHAT, CHANNEL, dp
from modules.bot_states import Registration, Menu, ProfileEdit, AdminNewEvent, AdminArchive, EventSubscribe, \
    AdminEditEvent, EditUser, UsersInEvent, PreRegistration

from aiogram import types
from aiogram.dispatcher import FSMContext

from handlers import main_handlers, registration_handlers, profile_handlers, calendar_handlers, residents_handlers
from admin_handlers import new_event_handlers



from modules.logger import send_log



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


@dp.callback_query_handler(lambda callback: 'user-subscribe' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def subscribe_payment_receipt(callback: types.CallbackQuery, state: FSMContext):
    await handlers.subscribe_handlers.subscribe_payment_receipt(callback, state)


#  СТРАРТ
@dp.message_handler(lambda message: message.from_user.id in banned_users, chat_type=types.ChatType.PRIVATE, state='*')
async def handle_banned(message: types.Message):
    #if len(message.text) > 6:
        #payment_id = message.text.split()
        #loop.create_task(modules.payment_module.check_payment(payment_id))
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text='🎫 Оформить на 1 месяц', callback_data=f"user-subscribe%1"),
                 types.InlineKeyboardButton(text='🎫 Оформить на 3 месяца', callback_data=f"user-subscribe%3"),
                 types.InlineKeyboardButton(text='🎫 Оформить на 6 месяцев', callback_data=f"user-subscribe%6"),
                 types.InlineKeyboardButton(text='🎫 Оформить на год', callback_data=f"user-subscribe%12"))
    await message.answer('👇 Вы еще не оплатили подписку..', reply_markup=keyboard)


@dp.message_handler(lambda message: message.from_user.id in wait_registration, chat_type=types.ChatType.PRIVATE, state='*')
async def handle_registration(message: types.Message):
    await message.answer('😔 Вашу заявку еще рассматривают, ожидайте')


@dp.callback_query_handler(lambda callback: callback.message.chat.id in banned_users, chat_type=types.ChatType.PRIVATE, state='*')
async def handle_banned(callback: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text='🎫 Оформить на 1 месяц', callback_data=f"user-subscribe%1"),
                 types.InlineKeyboardButton(text='🎫 Оформить на 3 месяца', callback_data=f"user-subscribe%3"),
                 types.InlineKeyboardButton(text='🎫 Оформить на 6 месяцев', callback_data=f"user-subscribe%6"),
                 types.InlineKeyboardButton(text='🎫 Оформить на год', callback_data=f"user-subscribe%12"))
    await callback.message.answer('👇 Вы еще не оплатили подписку..', reply_markup=keyboard)


@dp.message_handler(commands='start', chat_type=types.ChatType.PRIVATE, state='*')
async def start(message: types.Message):
    await main_handlers.start(message)

@dp.message_handler(commands='start')
async def start(message: types.Message):
    print(message.chat.id)

@dp.callback_query_handler(lambda callback: 'start-search' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def start_search(callback: types.CallbackQuery, state: FSMContext):
    await handlers.main_handlers.start_search(callback, state)


@dp.message_handler(commands='payments', chat_type=types.ChatType.PRIVATE, state='*')
async def get_payment(message: types.Message, state: FSMContext):
    if message.from_user.id in admins:
        await handlers.subscribe_handlers.get_payments_from_user(message, state)


#  РЕГИСТРАЦИЯ

@dp.message_handler(content_types=types.ContentType.CONTACT, chat_type=types.ChatType.PRIVATE, state=Registration.phone_number)
async def registration_send(message: types.Message, state: FSMContext):
    await registration_handlers.registration_send(message, state)

#   ПРОФИЛЬ И РЕДАКТИРОВАНИЕ


@dp.callback_query_handler(lambda callback: 'send-report' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu)
async def send_report(callback: types.CallbackQuery, state: FSMContext):
    await handlers.profile_handlers.send_report(callback, state)


@dp.message_handler(state=Menu.send_report, chat_type=types.ChatType.PRIVATE)
async def send_report_send(message: types.Message, state: FSMContext):
    await handlers.profile_handlers.send_report_send(message, state)


@dp.callback_query_handler(lambda callback: 'answer-report' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def send_report(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.answer_report(callback, state)


@dp.message_handler(state=Menu.answer_report,  chat_type=types.ChatType.PRIVATE)
async def send_report_send(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.answer_report_send(message, state)


@dp.callback_query_handler(lambda callback: 'profile' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def profile_handler(callback: types.CallbackQuery, state: FSMContext):
    await profile_handlers.profile_handler(callback, state)


@dp.callback_query_handler(lambda callback: 'edit_profile' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.profile)
async def edit_profile_handler(callback: types.CallbackQuery, state: FSMContext):
    await profile_handlers.edit_profile_handler(callback, state)


@dp.callback_query_handler(lambda callback: 'edit_full_name' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.profile)
async def edit_full_name_handler(callback: types.CallbackQuery, state: FSMContext):
    await profile_handlers.edit_full_name_handler(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=ProfileEdit.full_name)
async def edit_full_name(message: types.Message, state: FSMContext):
    await profile_handlers.edit_full_name(message, state)


@dp.callback_query_handler(lambda callback: 'edit_company_name' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.profile)
async def edit_company_name_handler(callback: types.CallbackQuery, state: FSMContext):
    await profile_handlers.edit_company_name_handler(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=ProfileEdit.company_name)
async def edit_company_name(message: types.Message, state: FSMContext):
    await profile_handlers.edit_company_name(message, state)


@dp.callback_query_handler(lambda callback: 'edit_company_site' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.profile)
async def edit_company_site_handler(callback: types.CallbackQuery, state: FSMContext):
    await profile_handlers.edit_company_site_handler(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=ProfileEdit.company_site)
async def edit_company_site(message: types.Message, state: FSMContext):
    await profile_handlers.edit_company_site(message, state)


#   КАЛЕНДАРЬ
@dp.callback_query_handler(lambda callback: 'calendar_handler' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def calendar_handler(callback: types.CallbackQuery, state: FSMContext):
    await calendar_handlers.events_calendar_handler(callback, state)


@dp.callback_query_handler(lambda callback: re.match(r'^event_calendar:(.*)', callback.data), chat_type=types.ChatType.PRIVATE, state='*')
async def event_calendar_selected_handler(callback: types.CallbackQuery, state: FSMContext):
    await calendar_handlers.event_calendar_selected_handler(callback, state)


#  РЕЗИДЕНТ
@dp.callback_query_handler(lambda callback: 'list-residents' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def residents_handler(callback: types.CallbackQuery, state: FSMContext):
    await residents_handlers.residents_handler(callback, state)


@dp.callback_query_handler(lambda callback: 'residents_list' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu)
async def residents_handler_select(callback: types.CallbackQuery, state: FSMContext):
    await residents_handlers.residents_handler_select(callback, state)


# МЕНЮ
@dp.callback_query_handler(lambda callback: 'menu' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def menu_handler(callback: types.CallbackQuery, state: FSMContext):
    await main_handlers.menu_handler(callback, state)


# ПОДПИСКА НА ИВЕНТ

@dp.callback_query_handler(lambda callback: 'subscribe-amount' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu)
async def subscribe_amount_new(callback: types.CallbackQuery, state: FSMContext):
    await handlers.subscribe_handlers.subscribe_amount_new(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=Menu.admin_amount)
async def subscribe_amount_set(message: types.Message, state: FSMContext):
    await handlers.subscribe_handlers.subscribe_amount_set(message, state)


@dp.callback_query_handler(lambda callback: 'subscribe-event' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu)
async def event_subscribe(callback: types.CallbackQuery, state: FSMContext):
    await handlers.subscribe_handlers.event_subscribe(callback, state)


@dp.callback_query_handler(lambda callback: 'subscribe-event-select' in callback.data
                                            or 'subscribe-event-delete' in callback.data, chat_type=types.ChatType.PRIVATE, state=EventSubscribe)
async def event_subscribe_select(callback: types.CallbackQuery, state: FSMContext):
    await handlers.subscribe_handlers.event_subscribe_select(callback, state)


@dp.callback_query_handler(lambda callback: 'event_payment_receipt' in callback.data, chat_type=types.ChatType.PRIVATE, state=EventSubscribe)
async def event_payment_receipt(callback: types.CallbackQuery, state: FSMContext):
    await handlers.subscribe_handlers.event_payment_receipt(callback, state)


@dp.callback_query_handler(lambda callback: 'payment-check' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def event_payment_receipt(callback: types.CallbackQuery, state: FSMContext):
    await handlers.subscribe_handlers.payment_check(callback, state)


# АРХИВ
@dp.callback_query_handler(lambda callback: 'archive-images' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.archive)
async def archive_selected_images(callback: types.CallbackQuery, state: FSMContext):
    await handlers.calendar_handlers.archive_selected_images(callback, state)


@dp.callback_query_handler(lambda callback: 'archive-video' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.archive)
async def archive_selected_video(callback: types.CallbackQuery, state: FSMContext):
    await handlers.calendar_handlers.archive_selected_video(callback, state)


# АДМИНКА
@dp.callback_query_handler(lambda callback: 'notify-all-users' == callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def notify_all_users(callback: types.CallbackQuery, state: FSMContext):
    print(callback.data)
    await admin_handlers.users_handlers.notify_all_users(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=Menu.admin_notify)
async def notify_all_users_send(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.notify_all_users_send(message, state)
#Пользователи

@dp.callback_query_handler(lambda callback: 'notify-user' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def notify_user(callback: types.CallbackQuery, state: FSMContext):
    print(callback.data)
    await admin_handlers.users_handlers.notify_user(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=Menu.admin_notify_user)
async def notify_user_send(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.notify_user_send(message, state)

@dp.callback_query_handler(lambda callback: 'list-users' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def list_users(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_users(callback, state)


@dp.callback_query_handler(lambda callback: 'list-rusers' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def list_residents(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_residents(callback, state)


@dp.callback_query_handler(lambda callback: 'rusers_list' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def list_residents_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_residents_select(callback, state)


@dp.callback_query_handler(lambda callback: 'list-ausers' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def list_admins(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_admins(callback, state)


@dp.callback_query_handler(lambda callback: 'admins_list' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def list_admins_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_admins_select(callback, state)


@dp.callback_query_handler(lambda callback: 'list-wusers' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def list_waiting(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_waiting(callback, state)


@dp.callback_query_handler(lambda callback: 'waiting_list' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def list_waiting_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.list_waiting_select(callback, state)


@dp.callback_query_handler(lambda callback: 'add-admin' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def new_admin(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.registration_handlers.new_admin(callback, state)


#Редактирование пользователя
@dp.callback_query_handler(lambda callback: 'edit-user-full_name' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def edit_user_full_name(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_full_name(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=EditUser.full_name)
async def edit_user_full_name_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_full_name_set(message, state)


@dp.callback_query_handler(lambda callback: 'edit-user-sub' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def edit_user_subscribe(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_subscribe(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=EditUser.subscribe)
async def edit_user_subscribe_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_subscribe_set(message, state)



@dp.callback_query_handler(lambda callback: 'edit-user-phone_number' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def edit_user_phone_number(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_phone_number(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=EditUser.phone_number)
async def edit_user_phone_number_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_phone_number_set(message, state)


@dp.callback_query_handler(lambda callback: 'edit-user-description' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def edit_user_description(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_description(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=EditUser.description)
async def edit_user_description_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_description_set(message, state)


@dp.callback_query_handler(lambda callback: 'edit-user-company_name' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def edit_user_company_name(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_company_name(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=EditUser.company_name)
async def edit_user_company_name_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_company_name_set(message, state)


@dp.callback_query_handler(lambda callback: 'edit-user-company_site' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def edit_user_company_site(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_company_site(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=EditUser.company_site)
async def edit_user_company_site_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_company_site_set(message, state)


@dp.callback_query_handler(lambda callback: 'edit-user-image' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def edit_user_image(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_image(callback, state)


@dp.message_handler(content_types=['photo'], chat_type=types.ChatType.PRIVATE, state=EditUser.image)
async def edit_user_image_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_image_set(message, state)


@dp.callback_query_handler(lambda callback: 'edit-user-video' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def edit_user_video(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_video(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=EditUser.video)
async def edit_user_video_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.edit_user_video_set(message, state)


@dp.callback_query_handler(lambda callback: 'delete-user' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def delete_user(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.users_handlers.delete_user(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=EditUser.delete)
async def delete_user_set(message: types.Message, state: FSMContext):
    await admin_handlers.users_handlers.delete_user_set(message, state)


#Регистрация
@dp.callback_query_handler(lambda callback: 'add-new-user' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def new_user(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.pre_registration_handlers.registration_phone_number(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=PreRegistration.phone_number)
async def registration_full_name(message: types.Message, state: FSMContext):
    await admin_handlers.pre_registration_handlers.registration_full_name(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=PreRegistration.full_name)
async def registration_description(message: types.Message, state: FSMContext):
    await admin_handlers.pre_registration_handlers.registration_description(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=PreRegistration.description)
async def registration_company_name(message: types.Message, state: FSMContext):
    await admin_handlers.pre_registration_handlers.registration_company_name(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=PreRegistration.company_name)
async def registration_company_site(message: types.Message, state: FSMContext):
    await admin_handlers.pre_registration_handlers.registration_company_site(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=PreRegistration.company_site)
async def registration_video(message: types.Message, state: FSMContext):
    await admin_handlers.pre_registration_handlers.registration_video(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=PreRegistration.video)
async def registration_image(message: types.Message, state: FSMContext):
    await admin_handlers.pre_registration_handlers.registration_image(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, content_types=['photo'], state=PreRegistration.image)
async def end_registration(message: types.Message, state: FSMContext):
    await admin_handlers.pre_registration_handlers.end_registration(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=PreRegistration.image)
async def end_registration_no_image(message: types.Message, state: FSMContext):
    await admin_handlers.pre_registration_handlers.end_registration_no_image(message, state)



@dp.callback_query_handler(lambda callback: 'add-user' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def new_user(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.registration_handlers.registration_full_name(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=Registration.full_name)
async def registration_description(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.registration_description(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=Registration.description)
async def registration_company_name(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.registration_company_name(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=Registration.company_name)
async def registration_company_site(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.registration_company_site(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=Registration.company_site)
async def registration_video(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.registration_video(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=Registration.video)
async def registration_image(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.registration_image(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, content_types=['photo'], state=Registration.image)
async def end_registration(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.end_registration(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=Registration.image)
async def end_registration_no_image(message: types.Message, state: FSMContext):
    await admin_handlers.registration_handlers.end_registration_no_image(message, state)


# Добавление мероприяия
@dp.callback_query_handler(lambda callback: 'new_event' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def new_event(callback: types.CallbackQuery, state: FSMContext):
    await new_event_handlers.new_event_handler(callback, state)


@dp.callback_query_handler(lambda callback: 'new_event_long' in callback.data or
                                            'new_event_short' in callback.data, chat_type=types.ChatType.PRIVATE, state=AdminNewEvent.event_long)
async def new_event_duration(callback: types.CallbackQuery, state: FSMContext):
    await new_event_handlers.new_event_duration(callback, state)


@dp.callback_query_handler(lambda callback: 'start_days' in callback.data, chat_type=types.ChatType.PRIVATE, state=AdminNewEvent.event_duration)
async def new_event_name(callback: types.CallbackQuery, state: FSMContext):
    await new_event_handlers.new_event_name(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminNewEvent.event_name)
async def new_event_description(message: types.Message, state: FSMContext):
    await admin_handlers.new_event_handlers.new_event_description(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminNewEvent.event_description)
async def new_event_price(message: types.Message, state: FSMContext):
    await admin_handlers.new_event_handlers.new_event_price(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminNewEvent.event_services)
async def new_event_services(message: types.Message, state: FSMContext):
    await admin_handlers.new_event_handlers.new_event_services(message, state)


@dp.callback_query_handler(lambda callback: 'add_event_service' in callback.data, chat_type=types.ChatType.PRIVATE, state=AdminNewEvent.event_services)
async def new_event_add_service(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.new_event_handlers.new_event_add_service(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE,state=AdminNewEvent.event_services_new)
async def new_event_add_service_price(message: types.Message, state: FSMContext):
    await admin_handlers.new_event_handlers.new_event_add_service_price(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminNewEvent.event_add)
async def new_event_add_service_price(message: types.Message, state: FSMContext):
    await admin_handlers.new_event_handlers.new_event_add(message, state)


@dp.callback_query_handler(lambda callback: 'add_event_set_calendar' in callback.data, chat_type=types.ChatType.PRIVATE,
                           state=AdminNewEvent.event_services)
async def add_event_set_calendar(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.new_event_handlers.add_event_set_calendar(callback, state)


@dp.callback_query_handler(lambda callback: re.match(r'^new_event_calendar:(.*)', callback.data), chat_type=types.ChatType.PRIVATE,
                           state=AdminNewEvent.event_services)
async def add_event_set_calendar(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.new_event_handlers.add_event_set_calendar_process(callback, state)


@dp.callback_query_handler(lambda callback: 'select_time' in callback.data, chat_type=types.ChatType.PRIVATE, state=AdminNewEvent.event_services)
async def add_event_set_time(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.new_event_handlers.add_event_set_time(callback, state)


# Редактирование мероприятия
@dp.callback_query_handler(lambda callback: 'public-event' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def publication_event(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.publication_event(callback, state)


@dp.callback_query_handler(lambda callback: 'event-edit-name' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def event_edit_name(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_name(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminEditEvent.event_name)
async def event_edit_name_set(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_name_set(message, state)


@dp.callback_query_handler(lambda callback: 'event-edit-description' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def event_edit_description(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_description(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminEditEvent.event_description)
async def event_edit_description_set(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_description_set(message, state)


@dp.callback_query_handler(lambda callback: 'event-edit-price' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def event_edit_price(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_price(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminEditEvent.event_price)
async def event_edit_price_set(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_price_set(message, state)


@dp.callback_query_handler(lambda callback: 'event-edit-services' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def event_edit_services(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_services(callback, state)


@dp.callback_query_handler(lambda callback: 'event-edit-service' in callback.data, chat_type=types.ChatType.PRIVATE, state=AdminEditEvent.event_services)
async def event_edit_service_description(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_description(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminEditEvent.event_service_description)
async def event_edit_service_description_set(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_description_set(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminEditEvent.event_service_price)
async def event_edit_service_price_set(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_price_set(message, state)


@dp.callback_query_handler(lambda callback: 'event-delete-service' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def event_edit_service_delete(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_delete(callback, state)


@dp.callback_query_handler(lambda callback: 'event-edit-add-service' in callback.data, chat_type=types.ChatType.PRIVATE, state=AdminEditEvent.event_services)
async def event_edit_service_add(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_add(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminEditEvent.event_new_service_description)
async def event_edit_service_add_description(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_add_description(message, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminEditEvent.event_new_service_price)
async def event_edit_service_add_price(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_service_add_price(message, state)


@dp.callback_query_handler(lambda callback: 'event-edit-date' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def event_edit_time(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_time(callback, state)


@dp.callback_query_handler(lambda callback: 'select_time' in callback.data, chat_type=types.ChatType.PRIVATE, state=AdminEditEvent.event_date)
async def event_edit_duration(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_duration(callback, state)


@dp.callback_query_handler(lambda callback: 'start_days' in callback.data, chat_type=types.ChatType.PRIVATE, state=AdminEditEvent.event_date)
async def event_edit_date(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_date(callback, state)


@dp.callback_query_handler(lambda callback: re.match(r'^new_event_calendar:(.*)', callback.data), chat_type=types.ChatType.PRIVATE, state=AdminEditEvent.event_date)
async def event_edit_date_set(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_edit_date_set(callback, state)


@dp.callback_query_handler(lambda callback: 'cancel-event' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def event_cancel(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_cancel(callback, state)


@dp.callback_query_handler(lambda callback: 'event-users' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def event_users(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_users(callback, state)


@dp.callback_query_handler(lambda callback: 'event_users' in callback.data, chat_type=types.ChatType.PRIVATE, state=UsersInEvent.list)
async def event_users_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_users_select(callback, state)


@dp.callback_query_handler(lambda callback: 'user-del-event' in callback.data, chat_type=types.ChatType.PRIVATE, state=UsersInEvent.list)
async def user_del_event(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.user_del_event(callback, state)


@dp.callback_query_handler(lambda callback: 'notify-e-users' in callback.data, chat_type=types.ChatType.PRIVATE, state=UsersInEvent.list)
async def notify_users(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.notify_users(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=UsersInEvent.list)
async def notify_users_send(message: types.Message, state: FSMContext):
    await admin_handlers.events_handlers.notify_users_send(message, state)


@dp.callback_query_handler(lambda callback: 'event-delete' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def event_delete(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.event_delete(callback, state)


# Список мероприятий
@dp.callback_query_handler(lambda callback: 'list_events' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def list_events(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.list_events_public(callback, state)


@dp.callback_query_handler(lambda callback: 'events_list' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def list_events_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.list_events_select(callback, state)


# Календарь мероприятий
@dp.callback_query_handler(lambda callback: 'admin_calendar' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def admin_calendar(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.admin_calendar(callback, state)


@dp.callback_query_handler(lambda callback: 'admin_event_calendar' in callback.data, chat_type=types.ChatType.PRIVATE, state='*')
async def admin_calendar_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.events_handlers.admin_calendar_select(callback, state)



# Архив мероприятий
@dp.callback_query_handler(lambda callback: 'admin_archive' in callback.data, chat_type=types.ChatType.PRIVATE, state=Menu.main)
async def archive_list(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.archive_handlers.archive_list(callback, state)


@dp.callback_query_handler(lambda callback: 'archive_list' in callback.data, chat_type=types.ChatType.PRIVATE, state=AdminArchive)
async def archive_list_select(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.archive_handlers.archive_list_select(callback, state)


@dp.callback_query_handler(lambda callback: 'archive-add-images' in callback.data, chat_type=types.ChatType.PRIVATE, state=AdminArchive)
async def archive_add_images(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.archive_handlers.archive_add_images(callback, state)


@dp.message_handler(content_types=['photo'], chat_type=types.ChatType.PRIVATE, state=AdminArchive.add_images)
async def archive_add_images_download(message: types.Message, state: FSMContext):
    await admin_handlers.archive_handlers.archive_add_images_download(message, state)


@dp.callback_query_handler(lambda callback: 'archive-add-video' in callback.data, chat_type=types.ChatType.PRIVATE, state=AdminArchive)
async def archive_add_video(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.archive_handlers.archive_add_video(callback, state)


@dp.message_handler(content_types=['video'], chat_type=types.ChatType.PRIVATE, state=AdminArchive.add_video)
async def archive_add_video_download(message: types.Message, state: FSMContext):
    await admin_handlers.archive_handlers.archive_add_video_download(message, state)


@dp.callback_query_handler(lambda callback: 'archive-add-link' in callback.data, chat_type=types.ChatType.PRIVATE, state=AdminArchive)
async def archive_add_link(callback: types.CallbackQuery, state: FSMContext):
    await admin_handlers.archive_handlers.archive_add_link(callback, state)


@dp.message_handler(chat_type=types.ChatType.PRIVATE, state=AdminArchive.add_link)
async def archive_add_link_set(message: types.Message, state: FSMContext):
    await admin_handlers.archive_handlers.archive_add_link_set(message, state)


@dp.message_handler(commands=['prereg'], chat_type=types.ChatType.PRIVATE, state='*')
async def prereg_handler(message):
    from database.collection import preusers
    prereg_data = preusers.find()
    if prereg_data:
        text = 'Ожидает подтверждения регистрации:\n\n'
        for user in prereg_data:
            text += f"{user['full_name']}\n{user['phone_number']}\n{user['description']}\n{user['company_name']}\n\n"
        await message.answer(text)
    else:
        await message.answer('Пусто')



@dp.message_handler(commands=['clear'], chat_type=types.ChatType.PRIVATE, state='*')
async def clear_handler(message):
    remove_keyboard = types.ReplyKeyboardRemove()
    await message.answer('..', reply_markup=remove_keyboard)

@dp.message_handler(commands=['events'], chat_type=types.ChatType.SUPERGROUP, state='*')
async def chat_handler(message):
    if message.chat.id != int(CHAT):
        return
    if message.from_user.id in banned_users:
        await bot.kick_chat_member(CHAT, message.from_user.id)
    events_data = events.find({'public': True})
    text = '🗓 Мероприятия:\n\n'

    for event in events_data:
        date = datetime(int(event['year']), int(event['month']), int(event['day']))
        text += f"✨{date.strftime('%d.%m.%Y')} {event['name']}\n📖 {event['description']}\n\n"

    await message.answer(text)



@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS, chat_type=types.ChatType.SUPERGROUP, state='*')
async def check_new_user(message: types.Message):
    if message.chat.id != int(CHAT):
        return
    if message.from_user.id in banned_users:
        await bot.kick_chat_member(CHAT, message.from_user.id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='🎥 Видео Babr', url='https://disk.yandex.ru/d/_1G5zkyCbW5t3Q'),
    types.InlineKeyboardButton(text='👍 Полезные ссылки',
                         url='https://docs.google.com/spreadsheets/d/1BdqC6wMGKos8AxQrwobNbspLGhPB8x9-mhqfgfDAE6s/edit?usp=sharing'))

    user = users.find_one({'user_id': message.new_chat_members[0].id})
    if user:
        full_name = user['full_name'].split()
        text = f"🤝 Здравствуйте, {full_name[1]} {full_name[2]}!\nДобро пожаловать в наш чат! 🎉\n\n"
    else:
        text = f"🤝 Здравствуйте, {message.new_chat_members[0].full_name}, добро пожаловать в чат! 🎉\n\n"

    text += f"🤖 Команда /events - список доступных мероприятий"
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(chat_type=types.ChatType.SUPERGROUP, state='*')
async def non_state(message):
    if message.chat.id != int(CHAT):
        return
    if message.from_user.id in banned_users:
        await bot.kick_chat_member(CHAT, message.from_user.id)
        try:
            await bot.kick_chat_member(CHANNEL, message.from_user.id)
        except:
            pass
        await message.delete()
