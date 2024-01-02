from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
class ListEvents:
    async def start_collection(self, collection_data, current_page: int = 1):
        collection = [item for item in collection_data]
        keyboard = InlineKeyboardMarkup()
        start_with = current_page * 10
        lenght = len(collection)
        print(lenght)
        for i in range(start_with - 10, min(start_with, lenght)):
            name = collection[i]['name']
            if collection[i]['public']:
                date = datetime(int(collection[i]['year']), int(collection[i]['month']), int(collection[i]['day']))
                form = date.strftime('%Y.%m.%d')
            else:
                form = 'Черновик'
            keyboard.add(InlineKeyboardButton(text=f"[{form}] {name}", callback_data=f"events_list-y-{collection[i]['id']}-{current_page}"))
        if current_page > 1 and start_with < lenght:
            keyboard.add(InlineKeyboardButton(text="<", callback_data=f'events_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text=">", callback_data=f'events_list-n-{current_page + 1}'))
        elif start_with < lenght:
            keyboard.add(InlineKeyboardButton(text=" ", callback_data=f'events_list-i-{current_page}'),
                         InlineKeyboardButton(text=">", callback_data=f'events_list-n-{current_page + 1}'))
        elif current_page > 1:
            keyboard.add(InlineKeyboardButton(text="<", callback_data=f'events_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text=" ", callback_data=f'events_list-i-{current_page}'))
        keyboard.add(InlineKeyboardButton(text="В меню", callback_data='menu'))

        return keyboard

    async def processing_selection(self, callback: CallbackQuery, callback_data, collection_data):
        select = callback_data.split(sep='-')[1]
        return_data = (False, None, None)
        if select == 'i':
            await callback.answer(cache_time=60)
        elif select == 'n':
            await callback.message.edit_reply_markup(reply_markup=await self.start_collection(collection_data, int(callback_data.split(sep='-')[2])))
        elif select == 'y':
            return_data = True, int(callback_data.split(sep='-')[2]), int(callback_data.split(sep='-')[3])
        return return_data
