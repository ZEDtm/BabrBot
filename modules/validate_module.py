import re


def format_phone(phone_numbers):
    phone = re.sub(r'\D', '', phone_numbers)
    if phone[0] == '8':
        phone = '7' + phone[1:]
    return phone

