import logging

from database.collection import events, find_event
from modules.bot_states import Menu

from aiogram import types
from aiogram.dispatcher import FSMContext

from modules.calendar_module import EventCalendar


logging.basicConfig(level=logging.INFO)


async def events_calendar_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Menu.calendar)
    user_id = callback.message.chat.id
    calendar = await EventCalendar(events.find({'public': True}), user_id).start_calendar()
    await callback.message.edit_text('Календарь:\n'
                                     ' 🟢 - Вы участвуете в мероприятии\n'
                                     ' 🟡 - Вы не участвуете в мероприятии\n'
                                     ' 🟠 - архив, Вы участвовали\n'
                                     ' 🔴 - архив, Вы не участвовали', reply_markup=calendar, parse_mode='HTML')


async def event_calendar_selected_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.message.chat.id
    select, date = await EventCalendar(events.find({'public': True}), user_id).process_selection(callback, callback.data)
    if select:
        event = find_event(date)
        await callback.message.answer(event['name'])
