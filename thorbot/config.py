import pymongo
from os import environ as env
from pymongo import MongoClient


class Config():
    data = {
        'last_welcome_id': None,
        'admin_ids': None
    }

    def __init__(self):
        try:
            self.settings = {
                'telegram_api_key': env.get('BOT_API_KEY'),
                'group_id': env.get('GROUP_ID'),
                'permitted_ids': [env.get('MASTER_ID')],
                'warn_limit': 3,
                'blacklist': []
            }

            # Setup DB
            client = MongoClient('mongodb://mongo:27017')
            self.db = client.test
            if self.db.users.index_information().get('username_1_chat_id_1') is None:
                self.db.users.create_index([('username', pymongo.ASCENDING),
                                            ('chat_id', pymongo.ASCENDING)],
                                           unique=True)

        except KeyError as e:
            raise Exception(e)

    @property
    def telegram_api_key(self):
        return self.settings['telegram_api_key']

    @property
    def group_id(self):
        return self.settings['group_id']

    @property
    def permitted_ids(self):
        return self.settings['permitted_ids']

    @property
    def admin_ids(self):
        return self.data['admin_ids']

    @admin_ids.setter
    def admin_ids(self, admin_ids):
        self.data['admin_ids'] = admin_ids

    @property
    def blacklist(self):
        return self.data['blacklist']

    @property
    def warn_limit(self):
        return self.settings['warn_limit']

    @property
    def last_welcome_id(self):
        return self.data['last_welcome_id']

    @last_welcome_id.setter
    def last_welcome_id(self, msg_id):
        self.data['last_welcome_id'] = msg_id
