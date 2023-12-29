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
    full_name: str
    phone_number: str
    company_name: str
    company_site: str

    def __call__(self):
        return asdict(self)


def find_user(user_id: str):
    return users.find_one({'user_id': int(user_id)})