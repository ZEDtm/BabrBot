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
    admin: bool

    def __call__(self):
        return asdict(self)


@dataclass
class Event:
    id: int
    name: str
    description: str
    price: int
    service_description: list
    service_price: list
    duration: int
    year: int
    month: int
    day: int
    hour: int
    minute: int
    users: list

    def __call__(self):
        return asdict(self)
