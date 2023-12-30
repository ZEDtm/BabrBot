from dataclasses import dataclass, asdict


@dataclass
class User:
    user_id: int
    telegram_first_name: str
    telegram_last_name: str
    telegram_user_name: str
    full_name: str
    phone_number: str
    company_name: str
    company_site: str
    events: list

    def __call__(self):
        return asdict(self)


@dataclass
class Event:
    year: str
    month: str
    day: str
    name: str
    users: list

    def __call__(self):
        return asdict(self)
