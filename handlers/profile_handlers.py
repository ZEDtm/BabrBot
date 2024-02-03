import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, admins
from database.collection import find_user, events
from modules.bot_states import Menu
from modules.logger import send_log

logging.basicConfig(level=logging.INFO)


async def profile_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Menu.profile)
    user = find_user(callback.from_user.id)

    keyboard = InlineKeyboardMarkup()

    # Формируем текст сообщения с анкетой пользователя
    text = f"📋 Ваша анкета:\n\n" \
           f"👤 ФИО: {user['full_name']}\n" \
           f"📞 Номер телефона: +{user['phone_number']}\n" \
           f"🏢 Название компании: {user['company_name']}\n"

    text += f"\n📋 Описание:\n {user['description']}\n"
    events_data = events.find({'users': {'$in': [user['user_id']]}})
    if events_data:
        text += "\n👤 Вы участвуете в мероприятиях:\n"
        for event in events_data:
            text += f"- {event['name']}\n"

    # Добавляем кнопки в клавиатуру, если есть ссылка на сайт или видео
    if user['company_site']:
        keyboard.add(InlineKeyboardButton(text='🌐 Ссылка на сайт', url=user['company_site']))
    if user['video']:
        keyboard.add(InlineKeyboardButton(text='🎬 Видео-карточка', url=user['video']))

    # Добавляем общие кнопки в клавиатуру
    keyboard.add(InlineKeyboardButton(text='📢 Обратная связь', callback_data='send-report'),
                 InlineKeyboardButton(text='🏠 В меню', callback_data='menu'))

    # Отправляем фото, если оно есть
    image_path = user['image']
    if image_path:
        await bot.send_photo(callback.from_user.id, photo=types.InputFile(image_path))

    # Отправляем сообщение с анкетой и клавиатурой
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

    # Отправляем сообщение администраторам
    for admin in admins:
        try:
            await bot.send_message(admin, f"Сообщение от пользователя {user['full_name']}\nНомер телефона: +{user['phone_number']}\n\n" + message.text, reply_markup=keyboard_admin)
            await send_log(f"Пользователь[{user['_id']}] -> [Сообщение] <- {message.text}")
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения администратору {admin}: {e}")

    # Отправляем подтверждение отправки сообщения
    await message.answer("🗣️ Ваше сообщение отправлено администраторам, ожидайте ответ!", reply_markup=keyboard)
    await Menu.main.set()