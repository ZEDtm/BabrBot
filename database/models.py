import datetime
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
    subscribe_year: int
    subscribe_month: int
    subscribe_day: int

    def __call__(self):
        return asdict(self)


@dataclass
class Event:
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
    public: bool
    users: list

    def __call__(self):
        return asdict(self)


@dataclass
class Archive:
    name: str
    description: str
    year: int
    month: int
    day: int
    users: list
    link: str

    def __call__(self):
        return asdict(self)


@dataclass
class Payment:
    user_id: int
    binding: str
    info: list
    total_amount: int
    invoice_payload: str
    telegram_payment_charge_id: str
    provider_payment_charge_id: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int

    def __call__(self):
        return asdict(self)