from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery, InputMediaPhoto

from config import wait_registration, admins


class ListEvents:
    async def start_collection(self, collection_data, current_page: int = 1):
        collection = [item for item in collection_data]
        keyboard = InlineKeyboardMarkup()
        start_with = current_page * 10
        lenght = len(collection)
        for i in range(start_with - 10, min(start_with, lenght)):
            name = collection[i]['name']
            if collection[i]['public']:
                date = datetime(int(collection[i]['year']), int(collection[i]['month']), int(collection[i]['day']))
                form = date.strftime('%d.%m.%Y')
            else:
                form = 'Черновик'
            keyboard.add(InlineKeyboardButton(text=f"✏ [{form}] {name}", callback_data=f"events_list-y-{str(collection[i]['_id'])}-{current_page}"))
        if current_page > 1 and start_with < lenght:
            keyboard.add(InlineKeyboardButton(text="➡", callback_data=f'events_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text="⬅", callback_data=f'events_list-n-{current_page + 1}'))
        elif start_with < lenght:
            keyboard.add(InlineKeyboardButton(text=" ", callback_data=f'events_list-i-{current_page}'),
                         InlineKeyboardButton(text="⬅", callback_data=f'events_list-n-{current_page + 1}'))
        elif current_page > 1:
            keyboard.add(InlineKeyboardButton(text="➡", callback_data=f'events_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text=" ", callback_data=f'events_list-i-{current_page}'))
        keyboard.add(InlineKeyboardButton(text="🏠 В меню", callback_data='menu'))

        return keyboard

    async def processing_selection(self, callback: CallbackQuery, callback_data, collection_data):
        select = callback_data.split(sep='-')[1]
        return_data = (False, None, None)
        if select == 'i':
            await callback.answer(cache_time=60)
        elif select == 'n':
            await callback.message.edit_text('✨ Список: мероприятия', reply_markup=await self.start_collection(collection_data, int(callback_data.split(sep='-')[2])))
        elif select == 'y':
            return_data = True, callback_data.split(sep='-')[2], int(callback_data.split(sep='-')[3])
        return return_data


class ListArchive:
    async def start_collection(self, collection_data, current_page: int = 1):
        collection = [item for item in collection_data]
        keyboard = InlineKeyboardMarkup()
        start_with = current_page * 10
        lenght = len(collection)
        for i in range(start_with - 10, min(start_with, lenght)):
            name = collection[i]['name']
            date_format = datetime(int(collection[i]['year']), int(collection[i]['month']), int(collection[i]['day'])).strftime('%d.%m.%Y')
            keyboard.add(InlineKeyboardButton(text=f"📆 [{date_format}] {name}", callback_data=f"archive_list-y-{str(collection[i]['_id'])}-{current_page}"))
        if current_page > 1 and start_with < lenght:
            keyboard.add(InlineKeyboardButton(text="⬅", callback_data=f'archive_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text="➡", callback_data=f'archive_list-n-{current_page + 1}'))
        elif start_with < lenght:
            keyboard.add(InlineKeyboardButton(text=" ", callback_data=f'archive_list-i-{current_page}'),
                         InlineKeyboardButton(text="➡", callback_data=f'archive_list-n-{current_page + 1}'))
        elif current_page > 1:
            keyboard.add(InlineKeyboardButton(text="⬅", callback_data=f'archive_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text=" ", callback_data=f'archive_list-i-{current_page}'))
        keyboard.add(InlineKeyboardButton(text="🏠 В меню", callback_data='menu'))

        return keyboard

    async def processing_selection(self, callback: CallbackQuery, callback_data, collection_data):
        select = callback_data.split(sep='-')[1]
        return_data = (False, None, None)
        if select == 'i':
            await callback.answer(cache_time=60)
        elif select == 'n':
            await callback.message.edit_text('🗄 Архив: список', reply_markup=await self.start_collection(collection_data, int(callback_data.split(sep='-')[2])))
        elif select == 'y':
            return_data = True, callback_data.split(sep='-')[2], int(callback_data.split(sep='-')[3])
        return return_data


class ListResidents:
    async def start_collection(self, collection_data, current_page: int = 1):
        collection = []
        for item in collection_data:
            if item['user_id'] in wait_registration or item['user_id'] in admins:
                continue
            collection.append(item)
        keyboard = InlineKeyboardMarkup()
        start_with = current_page * 10
        lenght = len(collection)
        for i in range(start_with - 10, min(start_with, lenght)):
            name = collection[i]['full_name'].split()
            full_name = f"{name[0]} {name[1][0]}.{name[2][0]}"

            keyboard.add(InlineKeyboardButton(text=f"🏢 {collection[i]['full_name']} 👤 {full_name}", callback_data=f"residents_list-y-{str(collection[i]['_id'])}-{current_page}"))
        if current_page > 1 and start_with < lenght:
            keyboard.add(InlineKeyboardButton(text="⬅️", callback_data=f'residents_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text="➡", callback_data=f'residents_list-n-{current_page + 1}'))
        elif start_with < lenght:
            keyboard.add(InlineKeyboardButton(text=" ", callback_data=f'residents_list-i-{current_page}'),
                         InlineKeyboardButton(text="➡", callback_data=f'residents_list-n-{current_page + 1}'))
        elif current_page > 1:
            keyboard.add(InlineKeyboardButton(text="⬅️", callback_data=f'residents_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text=" ", callback_data=f'residents_list-i-{current_page}'))
        keyboard.add(InlineKeyboardButton(text="🏠 В меню", callback_data='menu'))

        return keyboard

    async def processing_selection(self, callback: CallbackQuery, callback_data, collection_data):
        select = callback_data.split(sep='-')[1]
        return_data = (False, None, None)
        if select == 'i':
            await callback.answer(cache_time=60)
        elif select == 'n':
            await callback.message.edit_text('👥 Список резидентов:', reply_markup=await self.start_collection(collection_data, int(callback_data.split(sep='-')[2])))
        elif select == 'y':
            return_data = True, callback_data.split(sep='-')[2], int(callback_data.split(sep='-')[3])
        return return_data


class ListUsers:
    async def start_collection(self, collection_data, current_page: int = 1):
        collection = []
        for item in collection_data:
            if item['user_id'] in wait_registration or item['user_id'] in admins:
                continue
            collection.append(item)
        keyboard = InlineKeyboardMarkup()
        start_with = current_page * 10
        lenght = len(collection)
        for i in range(start_with - 10, min(start_with, lenght)):
            keyboard.add(InlineKeyboardButton(text=f"👤 {collection[i]['full_name']}", callback_data=f"rusers_list-y-{str(collection[i]['_id'])}-{current_page}"))
        if current_page > 1 and start_with < lenght:
            keyboard.add(InlineKeyboardButton(text="⬅", callback_data=f'rusers_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text="➡", callback_data=f'rusers_list-n-{current_page + 1}'))
        elif start_with < lenght:
            keyboard.add(InlineKeyboardButton(text=" ", callback_data=f'rusers_list-i-{current_page}'),
                         InlineKeyboardButton(text="➡", callback_data=f'rusers_list-n-{current_page + 1}'))
        elif current_page > 1:
            keyboard.add(InlineKeyboardButton(text="⬅", callback_data=f'rusers_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text=" ", callback_data=f'rusers_list-i-{current_page}'))
        keyboard.add(InlineKeyboardButton(text="↩ Назад", callback_data='list-users'))

        return keyboard

    async def processing_selection(self, callback: CallbackQuery, callback_data, collection_data):
        select = callback_data.split(sep='-')[1]
        return_data = (False, None, None)
        if select == 'i':
            await callback.answer(cache_time=60)
        elif select == 'n':
            await callback.message.edit_text(text='🏘 Резиденты:', reply_markup=await self.start_collection(collection_data, int(callback_data.split(sep='-')[2])))

        elif select == 'y':
            return_data = True, callback_data.split(sep='-')[2], int(callback_data.split(sep='-')[3])
        return return_data


class ListAdmins:
    async def start_collection(self, collection_data, current_page: int = 1):
        collection = []
        for item in collection_data:
            if not item['user_id'] in admins:
                continue
            collection.append(item)
        keyboard = InlineKeyboardMarkup()
        start_with = current_page * 10
        lenght = len(collection)
        for i in range(start_with - 10, min(start_with, lenght)):

            keyboard.add(InlineKeyboardButton(text=f"{collection[i]['telegram_first_name']}", callback_data=f"admins_list-y-{str(collection[i]['_id'])}-{current_page}"))
        if current_page > 1 and start_with < lenght:
            keyboard.add(InlineKeyboardButton(text="⬅", callback_data=f'admins_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text="➡", callback_data=f'admins_list-n-{current_page + 1}'))
        elif start_with < lenght:
            keyboard.add(InlineKeyboardButton(text=" ", callback_data=f'admins_list-i-{current_page}'),
                         InlineKeyboardButton(text="➡", callback_data=f'admins_list-n-{current_page + 1}'))
        elif current_page > 1:
            keyboard.add(InlineKeyboardButton(text="⬅", callback_data=f'admins_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text=" ", callback_data=f'admins_list-i-{current_page}'))
        keyboard.add(InlineKeyboardButton(text="↩ Назад", callback_data='list-users'))

        return keyboard

    async def processing_selection(self, callback: CallbackQuery, callback_data, collection_data):
        select = callback_data.split(sep='-')[1]
        return_data = (False, None, None)
        if select == 'i':
            await callback.answer(cache_time=60)
        elif select == 'n':
            await callback.message.edit_text(text='🔑 Администраторы:', reply_markup=await self.start_collection(collection_data, int(callback_data.split(sep='-')[2])))
        elif select == 'y':
            return_data = True, callback_data.split(sep='-')[2], int(callback_data.split(sep='-')[3])
        return return_data


class ListWaiting:
    async def start_collection(self, collection_data, current_page: int = 1):
        collection = []
        for item in collection_data:
            if not item['user_id'] in wait_registration:
                continue
            collection.append(item)
        keyboard = InlineKeyboardMarkup()
        start_with = current_page * 10
        lenght = len(collection)
        for i in range(start_with - 10, min(start_with, lenght)):
            if collection[i]['user_id'] not in wait_registration:
                continue

            keyboard.add(InlineKeyboardButton(text=f"+{collection[i]['phone_number']}", callback_data=f"waiting_list-y-{str(collection[i]['_id'])}-{current_page}"))
        if current_page > 1 and start_with < lenght:
            keyboard.add(InlineKeyboardButton(text="⬅", callback_data=f'waiting_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text="➡", callback_data=f'waiting_list-n-{current_page + 1}'))
        elif start_with < lenght:
            keyboard.add(InlineKeyboardButton(text=" ", callback_data=f'waiting_list-i-{current_page}'),
                         InlineKeyboardButton(text="➡", callback_data=f'waiting_list-n-{current_page + 1}'))
        elif current_page > 1:
            keyboard.add(InlineKeyboardButton(text="⬅", callback_data=f'waiting_list-n-{current_page - 1}'),
                         InlineKeyboardButton(text=" ", callback_data=f'waiting_list-i-{current_page}'))
        keyboard.add(InlineKeyboardButton(text="↩ Назад", callback_data='list-users'))

        return keyboard

    async def processing_selection(self, callback: CallbackQuery, callback_data, collection_data):
        select = callback_data.split(sep='-')[1]
        return_data = (False, None, None)
        if select == 'i':
            await callback.answer(cache_time=60)
        elif select == 'n':
            await callback.message.edit_text(text='📝 Заявки:', reply_markup=await self.start_collection(collection_data, int(callback_data.split(sep='-')[2])))
        elif select == 'y':
            return_data = True, callback_data.split(sep='-')[2], int(callback_data.split(sep='-')[3])
        return return_data


class ListUsersInEvent:
    async def start_collection(self, collection, callback_data, current_page: int = 1):
        keyboard = InlineKeyboardMarkup()
        start_with = current_page * 10
        lenght = len(collection)
        for i in range(start_with - 10, min(start_with, lenght)):
            keyboard.add(InlineKeyboardButton(text=f"👤 {collection[i]['full_name']}", callback_data=f"event_users-y-{str(collection[i]['_id'])}-{current_page}"))
        if current_page > 1 and start_with < lenght:
            keyboard.add(InlineKeyboardButton(text="⬅", callback_data=f'event_users-n-{current_page - 1}'),
                         InlineKeyboardButton(text="➡", callback_data=f'event_users-n-{current_page + 1}'))
        elif start_with < lenght:
            keyboard.add(InlineKeyboardButton(text=" ", callback_data=f'event_users-i-{current_page}'),
                         InlineKeyboardButton(text="➡", callback_data=f'event_users-n-{current_page + 1}'))
        elif current_page > 1:
            keyboard.add(InlineKeyboardButton(text="⬅", callback_data=f'event_users-n-{current_page - 1}'),
                         InlineKeyboardButton(text=" ", callback_data=f'event_users-i-{current_page}'))
        event_id = callback_data.split(sep=':')[5]
        keyboard.add(InlineKeyboardButton(text="📢 Оповестить участников", callback_data=f'notify-users%{event_id}'))
        keyboard.add(InlineKeyboardButton(text="🏠 В меню", callback_data='menu'),
                     InlineKeyboardButton(text='↩ Назад', callback_data=callback_data))

        return keyboard

    async def processing_selection(self, callback: CallbackQuery, callback_data, collection_data, call):
        select = callback_data.split(sep='-')[1]
        return_data = (False, None, None)
        if select == 'i':
            await callback.answer(cache_time=60)
        elif select == 'n':
            await callback.message.edit_text(text='👥 Участники мероприятия мероприятия:', reply_markup=await self.start_collection(collection_data, call, int(callback_data.split(sep='-')[2])))

        elif select == 'y':
            return_data = True, callback_data.split(sep='-')[2], int(callback_data.split(sep='-')[3])
        return return_data
