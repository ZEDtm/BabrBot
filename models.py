from pymongo.mongo_client import MongoClient
from config import MONGO_LOGIN, MONGO_PASS
from dataclasses import dataclass, asdict

uri = f"mongodb+srv://{MONGO_LOGIN}:{MONGO_PASS}@atlascluster.u3h56sm.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)

db = client.BabrBot
users = db.users


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

    def __call__(self):
        return asdict(self)


def find_user(user_id: str):
    return users.find_one({'user_id': int(user_id)})


def update_full_name(user_id: str, name: str):
    user = {'user_id': int(user_id)}
    new_full_name = {"$set": {'full_name': name}}
    users.update_one(user, new_full_name)


def update_company_name(user_id: str, name: str):
    user = {'user_id': int(user_id)}
    new_company_name = {"$set": {'company_name': name}}
    users.update_one(user, new_company_name)


def update_company_site(user_id: str, site: str):
    user = {'user_id': int(user_id)}
    new_company_site = {"$set": {'company_site': site}}
    users.update_one(user, new_company_site)