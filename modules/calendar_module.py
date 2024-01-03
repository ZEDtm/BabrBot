import calendar
from datetime import datetime, timedelta

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.types import CallbackQuery

# setting callback_data prefix and parts
event_calendar_callback = CallbackData('event_calendar', 'act', 'year', 'month', 'day')
new_event_callback = CallbackData('new_event_calendar', 'act', 'year', 'month', 'day')
admin_event_calendar_callback = CallbackData('admin_event_calendar', 'act', 'year', 'month', 'day')
calendar_callback = CallbackData('new_event_calendar', 'act', 'year', 'month', 'day')
months_names = ['', 'Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']


class EventCalendar:
    def __init__(self, events, user_id):
        self.events = events
        self.user_id = user_id

    async def start_calendar(
            self,
            year: int = datetime.now().year,
            month: int = datetime.now().month,
    ) -> InlineKeyboardMarkup:
        """
        Creates an inline keyboard with the provided year and month
        :param int year: Year to use in the calendar_handler, if None the current year is used.
        :param int month: Month to use in the calendar_handler, if None the current month is used.
        :return: Returns InlineKeyboardMarkup object with the calendar_handler.
        """
        #  check events in db
        current_events = []
        users_events = []
        for event in self.events:
            if int(event['year']) == year:
                if int(event['month']) == month:
                    if str(self.user_id) in event['users']:
                        users_events.append(int(event['day']))
                    else:
                        current_events.append(int(event['day']))



        inline_kb = InlineKeyboardMarkup(row_width=7)
        ignore_callback = event_calendar_callback.new("IGNORE", year, month, 0)  # for buttons with no answer
        # First row - Month and Year
        inline_kb.row()
        inline_kb.insert(InlineKeyboardButton(
            "<<",
            callback_data=event_calendar_callback.new("PREV-YEAR", year, month, 1)
        ))
        inline_kb.insert(InlineKeyboardButton(
            f'{months_names[month]} {str(year)}',
            callback_data=ignore_callback
        ))
        inline_kb.insert(InlineKeyboardButton(
            ">>",
            callback_data=event_calendar_callback.new("NEXT-YEAR", year, month, 1)
        ))
        # Second row - Week Days
        inline_kb.row()
        for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
            inline_kb.insert(InlineKeyboardButton(day, callback_data=ignore_callback))

        # Calendar rows - Days of month
        month_calendar = calendar.monthcalendar(year, month)
        for week in month_calendar:
            inline_kb.row()
            for day in week:
                if (day == 0):
                    inline_kb.insert(InlineKeyboardButton("  ", callback_data=ignore_callback))
                    continue

                elif day in users_events:
                    if datetime(year, month, day) < datetime.now():
                        inline_kb.insert(InlineKeyboardButton(
                            str(day)+'🟠', callback_data=event_calendar_callback.new("DAY", year, month, day)
                        ))
                        continue

                    inline_kb.insert(InlineKeyboardButton(
                        str(day)+'🟢', callback_data=event_calendar_callback.new("DAY", year, month, day)
                    ))
                    continue

                elif day in current_events:
                    if datetime(year, month, day) < datetime.now():
                        inline_kb.insert(InlineKeyboardButton(
                            str(day)+'🔴', callback_data=event_calendar_callback.new("DAY", year, month, day)
                        ))
                        continue

                    inline_kb.insert(InlineKeyboardButton(
                        str(day)+'🟡', callback_data=event_calendar_callback.new("DAY", year, month, day)
                    ))
                    continue
                inline_kb.insert(InlineKeyboardButton(str(day)+' ', callback_data=ignore_callback))

        # Last row - Buttons
        inline_kb.row()
        inline_kb.insert(InlineKeyboardButton(
            "<", callback_data=event_calendar_callback.new("PREV-MONTH", year, month, day)
        ))
        inline_kb.insert(InlineKeyboardButton("В меню", callback_data='menu'))
        inline_kb.insert(InlineKeyboardButton(
            ">", callback_data=event_calendar_callback.new("NEXT-MONTH", year, month, day)
        ))

        return inline_kb

    async def process_selection(self, query: CallbackQuery, data) -> tuple:
        """
        Process the callback_query. This method generates a new calendar_handler if forward or
        backward is pressed. This method should be called inside a CallbackQueryHandler.
        :param query: callback_query, as provided by the CallbackQueryHandler
        :param data: callback_data, dictionary, set by calendar_callback
        :return: Returns a tuple (Boolean,datetime), indicating if a date is selected
                    and returning the date if so.
        """
        return_data = (False, None)
        new_data = {'simple_calendar': data.split(sep=':')[0],
                    'act': data.split(sep=':')[1],
                    'year': data.split(sep=':')[2],
                    'month': data.split(sep=':')[3],
                    'day': data.split(sep=':')[4]}

        year = int(new_data['year'])
        month = int(new_data['month'])
        day = int(new_data['day'])

        temp_date = datetime(year, month, 1)
        # processing empty buttons, answering with no action
        if new_data['act'] == "IGNORE":
            await query.answer(cache_time=60)
        # user picked a day button, return date
        if new_data['act'] == "DAY":
            await query.message.delete_reply_markup()  # removing inline keyboard
            return_data = True, {'year': year, 'month': month, 'day': day}
            #return_data = True, datetime(year, month, day)
        # user navigates to previous year, editing message with new calendar_handler
        if new_data['act'] == "PREV-YEAR":
            prev_date = temp_date - timedelta(days=365)
            await query.message.edit_reply_markup(await self.start_calendar(int(prev_date.year), int(prev_date.month)))
        # user navigates to next year, editing message with new calendar_handler
        if new_data['act'] == "NEXT-YEAR":
            next_date = temp_date + timedelta(days=365)
            await query.message.edit_reply_markup(await self.start_calendar(int(next_date.year), int(next_date.month)))
        # user navigates to previous month, editing message with new calendar_handler
        if new_data['act'] == "PREV-MONTH":
            prev_date = temp_date - timedelta(days=1)
            await query.message.edit_reply_markup(await self.start_calendar(int(prev_date.year), int(prev_date.month)))
        # user navigates to next month, editing message with new calendar_handler
        if new_data['act'] == "NEXT-MONTH":
            next_date = temp_date + timedelta(days=31)
            await query.message.edit_reply_markup(await self.start_calendar(int(next_date.year), int(next_date.month)))
        # at some point user clicks DAY button, returning date
        return return_data


class AdminEventCalendar:
    def __init__(self, events, archive):
        self.events = events
        self.archive = archive

    async def start_calendar(
            self,
            year: int = datetime.now().year,
            month: int = datetime.now().month
    ) -> InlineKeyboardMarkup:
        """
        Creates an inline keyboard with the provided year and month
        :param int year: Year to use in the calendar_handler, if None the current year is used.
        :param int month: Month to use in the calendar_handler, if None the current month is used.
        :return: Returns InlineKeyboardMarkup object with the calendar_handler.
        """
        current_events_public = []
        current_events_no_public = []
        events_id = []
        for event in self.events:
            if int(event['year']) == year:
                if int(event['month']) == month:
                    if event['public']:
                        current_events_public.append(int(event['day']))
                    else:
                        current_events_no_public.append(int(event['day']))
                    events_id.append(str(event['_id']))

        archive_data = []
        archive_id = []
        for arch in self.archive:
            if int(arch['year']) == year:
                if int(arch['month']) == month:
                    archive_data.append(int(arch['day']))
                    archive_id.append(str(arch['_id']))

        inline_kb = InlineKeyboardMarkup(row_width=7)
        ignore_callback = admin_event_calendar_callback.new("IGNORE", year, month, 0)  # for buttons with no answer
        # First row - Month and Year
        inline_kb.row()
        inline_kb.insert(InlineKeyboardButton(
            "<<",
            callback_data=admin_event_calendar_callback.new("PREV-YEAR", year, month, 1)
        ))
        inline_kb.insert(InlineKeyboardButton(
            f'{months_names[month]} {str(year)}',
            callback_data=ignore_callback
        ))
        inline_kb.insert(InlineKeyboardButton(
            ">>",
            callback_data=admin_event_calendar_callback.new("NEXT-YEAR", year, month, 1)
        ))
        # Second row - Week Days
        inline_kb.row()
        for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
            inline_kb.insert(InlineKeyboardButton(day, callback_data=ignore_callback))

        # Calendar rows - Days of month
        month_calendar = calendar.monthcalendar(year, month)
        for week in month_calendar:
            inline_kb.row()
            for day in week:
                if day == 0:
                    inline_kb.insert(InlineKeyboardButton(" ", callback_data=ignore_callback))
                    continue
                if day in current_events_public:
                    i = current_events_public.index(day)
                    inline_kb.insert(InlineKeyboardButton(str(day)+'🟢', callback_data=admin_event_calendar_callback.new("DAY", year, month, day)+f':{events_id[i]}'))
                    continue
                if day in current_events_no_public:
                    i = current_events_no_public.index(day)
                    inline_kb.insert(InlineKeyboardButton(str(day)+'🟡', callback_data=admin_event_calendar_callback.new("event", year, month, day)+f':{events_id[i]}'))
                    continue
                if day in archive_data:
                    i = archive_data.index(day)
                    inline_kb.insert(InlineKeyboardButton(str(day) + '🔴', callback_data=admin_event_calendar_callback.new("archive", year, month, day) + f':{archive_id[i]}'))
                    continue
                inline_kb.insert(InlineKeyboardButton(str(day), callback_data=ignore_callback))

        # Last row - Buttons
        inline_kb.row()
        inline_kb.insert(InlineKeyboardButton(
            "<", callback_data=admin_event_calendar_callback.new("PREV-MONTH", year, month, day)
        ))
        inline_kb.insert(InlineKeyboardButton("В меню", callback_data='menu'))
        inline_kb.insert(InlineKeyboardButton(
            ">", callback_data=admin_event_calendar_callback.new("NEXT-MONTH", year, month, day)
        ))

        return inline_kb

    async def process_selection(self, query: CallbackQuery, data) -> tuple:
        """
        Process the callback_query. This method generates a new calendar_handler if forward or
        backward is pressed. This method should be called inside a CallbackQueryHandler.
        :param query: callback_query, as provided by the CallbackQueryHandler
        :param data: callback_data, dictionary, set by calendar_callback
        :return: Returns a tuple (Boolean,datetime), indicating if a date is selected
                    and returning the date if so.
        """
        return_data = (None, None, None)
        new_data = {'admin_event_calendar_callback': data.split(sep=':')[0],
                    'act': data.split(sep=':')[1],
                    'year': data.split(sep=':')[2],
                    'month': data.split(sep=':')[3],
                    'day': data.split(sep=':')[4]}

        year = int(new_data['year'])
        month = int(new_data['month'])
        day = int(new_data['day'])

        temp_date = datetime(year, month, 1)
        # processing empty buttons, answering with no action
        if new_data['act'] == "IGNORE":
            await query.answer(cache_time=60)
        # user picked a day button, return date
        if new_data['act'] == "archive":
            await query.message.delete_reply_markup()  # removing inline keyboard
            return_data = False, {'year': year, 'month': month, 'day': day}, str(data.split(sep=':')[5])
        if new_data['act'] == "event":
            await query.message.delete_reply_markup()  # removing inline keyboard
            return_data = True, {'year': year, 'month': month, 'day': day}, str(data.split(sep=':')[5])
        # user navigates to previous year, editing message with new calendar_handler
        if new_data['act'] == "PREV-YEAR":
            prev_date = temp_date - timedelta(days=365)
            await query.message.edit_reply_markup(await self.start_calendar(int(prev_date.year), int(prev_date.month)))
        # user navigates to next year, editing message with new calendar_handler
        if new_data['act'] == "NEXT-YEAR":
            next_date = temp_date + timedelta(days=365)
            await query.message.edit_reply_markup(await self.start_calendar(int(next_date.year), int(next_date.month)))
        # user navigates to previous month, editing message with new calendar_handler
        if new_data['act'] == "PREV-MONTH":
            prev_date = temp_date - timedelta(days=1)
            await query.message.edit_reply_markup(await self.start_calendar(int(prev_date.year), int(prev_date.month)))
        # user navigates to next month, editing message with new calendar_handler
        if new_data['act'] == "NEXT-MONTH":
            next_date = temp_date + timedelta(days=31)
            await query.message.edit_reply_markup(await self.start_calendar(int(next_date.year), int(next_date.month)))
        if new_data['act'] == "CURRENT":
            await query.message.edit_reply_markup(await self.start_calendar(int(year), int(month)))
        # at some point user clicks DAY button, returning date
        return return_data


class SimpleCalendar:

    async def start_calendar(
            self,
            year: int = datetime.now().year,
            month: int = datetime.now().month
    ) -> InlineKeyboardMarkup:
        """
        Creates an inline keyboard with the provided year and month
        :param int year: Year to use in the calendar_handler, if None the current year is used.
        :param int month: Month to use in the calendar_handler, if None the current month is used.
        :return: Returns InlineKeyboardMarkup object with the calendar_handler.
        """

        inline_kb = InlineKeyboardMarkup(row_width=7)
        ignore_callback = calendar_callback.new("IGNORE", year, month, 0)  # for buttons with no answer
        # First row - Month and Year
        inline_kb.row()
        inline_kb.insert(InlineKeyboardButton(
            "<<",
            callback_data=calendar_callback.new("PREV-YEAR", year, month, 1)
        ))
        inline_kb.insert(InlineKeyboardButton(
            f'{months_names[month]} {str(year)}',
            callback_data=ignore_callback
        ))
        inline_kb.insert(InlineKeyboardButton(
            ">>",
            callback_data=calendar_callback.new("NEXT-YEAR", year, month, 1)
        ))
        # Second row - Week Days
        inline_kb.row()
        for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
            inline_kb.insert(InlineKeyboardButton(day, callback_data=ignore_callback))

        # Calendar rows - Days of month
        month_calendar = calendar.monthcalendar(year, month)
        for week in month_calendar:
            inline_kb.row()
            for day in week:
                print(day)
                if (day == 0):
                    inline_kb.insert(InlineKeyboardButton(" ", callback_data=ignore_callback))
                    continue
                inline_kb.insert(InlineKeyboardButton(
                    str(day), callback_data=calendar_callback.new("DAY", year, month, day)
                ))

        # Last row - Buttons
        inline_kb.row()
        inline_kb.insert(InlineKeyboardButton(
            "<", callback_data=calendar_callback.new("PREV-MONTH", year, month, day)
        ))
        inline_kb.insert(InlineKeyboardButton("В меню", callback_data='menu'))
        inline_kb.insert(InlineKeyboardButton(
            ">", callback_data=calendar_callback.new("NEXT-MONTH", year, month, day)
        ))

        return inline_kb

    async def process_selection(self, query: CallbackQuery, data) -> tuple:
        """
        Process the callback_query. This method generates a new calendar_handler if forward or
        backward is pressed. This method should be called inside a CallbackQueryHandler.
        :param query: callback_query, as provided by the CallbackQueryHandler
        :param data: callback_data, dictionary, set by calendar_callback
        :return: Returns a tuple (Boolean,datetime), indicating if a date is selected
                    and returning the date if so.
        """
        return_data = (False, None)
        new_data = {'admin_event_calendar': data.split(sep=':')[0],
                    'act': data.split(sep=':')[1],
                    'year': data.split(sep=':')[2],
                    'month': data.split(sep=':')[3],
                    'day': data.split(sep=':')[4]}

        year = int(new_data['year'])
        month = int(new_data['month'])
        day = int(new_data['day'])

        temp_date = datetime(year, month, 1)
        # processing empty buttons, answering with no action
        if new_data['act'] == "IGNORE":
            await query.answer(cache_time=60)
        # user picked a day button, return date
        if new_data['act'] == "DAY":
            await query.message.delete_reply_markup()  # removing inline keyboard
            return_data = True, datetime(year, month, day)
        # user navigates to previous year, editing message with new calendar_handler
        if new_data['act'] == "PREV-YEAR":
            prev_date = temp_date - timedelta(days=365)
            await query.message.edit_reply_markup(await self.start_calendar(int(prev_date.year), int(prev_date.month)))
        # user navigates to next year, editing message with new calendar_handler
        if new_data['act'] == "NEXT-YEAR":
            next_date = temp_date + timedelta(days=365)
            await query.message.edit_reply_markup(await self.start_calendar(int(next_date.year), int(next_date.month)))
        # user navigates to previous month, editing message with new calendar_handler
        if new_data['act'] == "PREV-MONTH":
            prev_date = temp_date - timedelta(days=1)
            await query.message.edit_reply_markup(await self.start_calendar(int(prev_date.year), int(prev_date.month)))
        # user navigates to next month, editing message with new calendar_handler
        if new_data['act'] == "NEXT-MONTH":
            next_date = temp_date + timedelta(days=31)
            await query.message.edit_reply_markup(await self.start_calendar(int(next_date.year), int(next_date.month)))
        # at some point user clicks DAY button, returning date
        return return_data


class NewEventCalendar:
    def __init__(self, events):
        self.events = events

    async def start_calendar(
            self,
            year: int = datetime.now().year,
            month: int = datetime.now().month,
    ) -> InlineKeyboardMarkup:
        """
        Creates an inline keyboard with the provided year and month
        :param int year: Year to use in the calendar_handler, if None the current year is used.
        :param int month: Month to use in the calendar_handler, if None the current month is used.
        :return: Returns InlineKeyboardMarkup object with the calendar_handler.
        """
        current_events = []
        for event in self.events:
            if int(event['year']) == year and int(event['month']) == month:
                current_events.append(int(event['day']))

        inline_kb = InlineKeyboardMarkup(row_width=7)
        ignore_callback = new_event_callback.new("IGNORE", year, month, 0)  # for buttons with no answer
        # First row - Month and Year
        inline_kb.row()
        if year <= datetime.now().year:
            inline_kb.insert(InlineKeyboardButton(" ", callback_data=ignore_callback))
        else:
            inline_kb.insert(InlineKeyboardButton(
                "<<",
                callback_data=new_event_callback.new("PREV-YEAR", year, month, 1)
            ))
        inline_kb.insert(InlineKeyboardButton(
            f'{months_names[month]} {str(year)}',
            callback_data=ignore_callback
        ))
        inline_kb.insert(InlineKeyboardButton(
            ">>",
            callback_data=new_event_callback.new("NEXT-YEAR", year, month, 1)
        ))
        # Second row - Week Days
        inline_kb.row()
        for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
            inline_kb.insert(InlineKeyboardButton(day, callback_data=ignore_callback))

        # Calendar rows - Days of month
        month_calendar = calendar.monthcalendar(year, month)
        for week in month_calendar:
            inline_kb.row()
            for day in week:
                if day == 0:
                    inline_kb.insert(InlineKeyboardButton(" ", callback_data=ignore_callback))
                    continue
                if year == datetime.now().year and month == datetime.now().month:
                    current_day = datetime.now().day
                    if day < current_day:
                        inline_kb.insert(InlineKeyboardButton(" ", callback_data=ignore_callback))
                        continue
                if day in current_events:
                    inline_kb.insert(InlineKeyboardButton("❌", callback_data=ignore_callback))
                    continue
                inline_kb.insert(InlineKeyboardButton(
                    str(day), callback_data=new_event_callback.new("DAY", year, month, day)
                ))

        # Last row - Buttons
        inline_kb.row()
        if year <= datetime.now().year and month <= datetime.now().month:
            inline_kb.insert(InlineKeyboardButton(" ", callback_data=ignore_callback))
        else:
            inline_kb.insert(InlineKeyboardButton(
                "<", callback_data=new_event_callback.new("PREV-MONTH", year, month, day)
            ))
        inline_kb.insert(InlineKeyboardButton("В меню", callback_data='menu'))
        inline_kb.insert(InlineKeyboardButton(
            ">", callback_data=new_event_callback.new("NEXT-MONTH", year, month, day)
        ))

        return inline_kb

    async def process_selection(self, query: CallbackQuery, data) -> tuple:
        """
        Process the callback_query. This method generates a new calendar_handler if forward or
        backward is pressed. This method should be called inside a CallbackQueryHandler.
        :param query: callback_query, as provided by the CallbackQueryHandler
        :param data: callback_data, dictionary, set by calendar_callback
        :return: Returns a tuple (Boolean,datetime), indicating if a date is selected
                    and returning the date if so.
        """
        return_data = (False, None)
        new_data = {'new_event_calendar': data.split(sep=':')[0],
                    'act': data.split(sep=':')[1],
                    'year': data.split(sep=':')[2],
                    'month': data.split(sep=':')[3],
                    'day': data.split(sep=':')[4]}

        year = int(new_data['year'])
        month = int(new_data['month'])
        day = int(new_data['day'])

        temp_date = datetime(year, month, 1)
        # processing empty buttons, answering with no action
        if new_data['act'] == "IGNORE":
            await query.answer(cache_time=60)
        # user picked a day button, return date
        if new_data['act'] == "DAY":
            await query.message.delete_reply_markup()  # removing inline keyboard
            return_data = True, {'year': year, 'month': month, 'day': day}
        # user navigates to previous year, editing message with new calendar_handler
        if new_data['act'] == "PREV-YEAR":
            prev_date = temp_date - timedelta(days=365)
            await query.message.edit_reply_markup(await self.start_calendar(int(prev_date.year), int(prev_date.month)))
        # user navigates to next year, editing message with new calendar_handler
        if new_data['act'] == "NEXT-YEAR":
            next_date = temp_date + timedelta(days=365)
            await query.message.edit_reply_markup(await self.start_calendar(int(next_date.year), int(next_date.month)))
        # user navigates to previous month, editing message with new calendar_handler
        if new_data['act'] == "PREV-MONTH":
            prev_date = temp_date - timedelta(days=1)
            await query.message.edit_reply_markup(await self.start_calendar(int(prev_date.year), int(prev_date.month)))
        # user navigates to next month, editing message with new calendar_handler
        if new_data['act'] == "NEXT-MONTH":
            next_date = temp_date + timedelta(days=31)
            await query.message.edit_reply_markup(await self.start_calendar(int(next_date.year), int(next_date.month)))
        # at some point user clicks DAY button, returning date
        return return_data


class SelectDays:
    async def start_days(self, day: int = 2):
        keyboard = InlineKeyboardMarkup()
        if day == 2:
            keyboard.add(InlineKeyboardButton(text=f'{day} дня', callback_data=f'start_days-y-{day}'),
                         InlineKeyboardButton(text='>', callback_data=f'start_days-n-{day + 1}'))
        elif 2 < day < 5:
            keyboard.add(InlineKeyboardButton(text='<', callback_data=f'start_days-n-{day-1}'),
                         InlineKeyboardButton(text=f'{day} дня', callback_data=f'start_days-y-{day}'),
                         InlineKeyboardButton(text='>', callback_data=f'start_days-n-{day+1}'))
        elif day == 21:
            keyboard.add(InlineKeyboardButton(text='<', callback_data=f'start_days-n-{day-1}'),
                         InlineKeyboardButton(text=f'{day} день', callback_data=f'start_days-y-{day}'),
                         InlineKeyboardButton(text='>', callback_data=f'start_days-n-{day+1}'))
        elif 21 < day < 25:
            keyboard.add(InlineKeyboardButton(text='<', callback_data=f'start_days-n-{day-1}'),
                         InlineKeyboardButton(text=f'{day} дня', callback_data=f'start_days-y-{day}'),
                         InlineKeyboardButton(text='>', callback_data=f'start_days-n-{day+1}'))
        elif 4 < day < 31:
            keyboard.add(InlineKeyboardButton(text='<', callback_data=f'start_days-n-{day-1}'),
                         InlineKeyboardButton(text=f'{day} дней', callback_data=f'start_days-y-{day}'),
                         InlineKeyboardButton(text='>', callback_data=f'start_days-n-{day+1}'))
        elif day == 31:
            keyboard.add(InlineKeyboardButton(text='<', callback_data=f'start_days-n-{day-1}'),
                         InlineKeyboardButton(text=f'{day} день', callback_data=f'start_days-y-{day}'))
        return keyboard

    async def process_selection(self, query: CallbackQuery, data) -> tuple:
        return_data = (False, None)
        select = data.split(sep='-')[1]
        day = int(data.split(sep='-')[2])
        if select == 'y':
            return_data = True, day
        else:
            await query.message.edit_reply_markup(await self.start_days(day))
        return return_data


class SelectTime:
    async def start_time(self,
                         hour: int = 12,
                         minute: int = 0):
        keyboard = InlineKeyboardMarkup()
        if hour == 0:
            keyboard.add(InlineKeyboardButton(text=' ', callback_data=f'select_time-i-{hour}-{minute}'),
                         InlineKeyboardButton(text=f'{hour} ч', callback_data=f'select_time-i-{hour}-{minute}'),
                         InlineKeyboardButton(text='>', callback_data=f'select_time-n-{hour + 1}-{minute}'))
        elif hour == 23:
            keyboard.add(InlineKeyboardButton(text='<', callback_data=f'select_time-n-{hour - 1}-{minute}'),
                         InlineKeyboardButton(text=f'{hour} ч',  callback_data=f'select_time-i-{hour}-{minute}'),
                         InlineKeyboardButton(text=' ',  callback_data=f'select_time-i-{hour}-{minute}'))
        else:
            keyboard.add(InlineKeyboardButton(text='<', callback_data=f'select_time-n-{hour - 1}-{minute}'),
                         InlineKeyboardButton(text=f'{hour} ч',  callback_data=f'select_time-i-{hour}-{minute}'),
                         InlineKeyboardButton(text='>', callback_data=f'select_time-n-{hour + 1}-{minute}'))
        if minute == 0:
            keyboard.add(InlineKeyboardButton(text=' ',  callback_data=f'select_time-i-{hour}-{minute}'),
                         InlineKeyboardButton(text=f'{minute} м',  callback_data=f'select_time-i-{hour}-{minute}'),
                         InlineKeyboardButton(text='>', callback_data=f'select_time-n-{hour}-{minute + 5}'))
        elif minute == 55:
            keyboard.add(InlineKeyboardButton(text='<', callback_data=f'select_time-n-{hour}-{minute - 5}'),
                         InlineKeyboardButton(text=f'{minute} м',  callback_data=f'select_time-i-{hour}-{minute}'),
                         InlineKeyboardButton(text=' ',  callback_data=f'select_time-i-{hour}-{minute}'))
        else:
            keyboard.add(InlineKeyboardButton(text='<', callback_data=f'select_time-n-{hour}-{minute - 5}'),
                         InlineKeyboardButton(text=f'{minute} м', callback_data=f'select_time-i-{hour}-{minute}'),
                         InlineKeyboardButton(text='>', callback_data=f'select_time-n-{hour}-{minute + 5}'))
        keyboard.add(InlineKeyboardButton(text='Ок', callback_data=f'select_time-y-{hour}-{minute}'))
        return keyboard

    async def process_selection(self, query: CallbackQuery, data) -> tuple:
        return_data = (False, None)
        select = data.split(sep='-')[1]
        hour = int(data.split(sep='-')[2])
        minute = int(data.split(sep='-')[3])
        if select == 'y':
            return_data = True, {'hour': hour, 'minute': minute}
        elif select == 'i':
            await query.answer(cache_time=60)
        else:
            await query.message.edit_reply_markup(await self.start_time(hour, minute))
        return return_data