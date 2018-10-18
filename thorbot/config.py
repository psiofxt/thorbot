from os import environ as env
from pymongo import MongoClient


class Config():
    data = {}

    def __init__(self):
        try:
            self.settings = {
                'telegram_api_key': env.get('BOT_API_KEY'),
                'group_id': env.get('GROUP_ID'),
                'permitted_ids': [env.get('MASTER_ID')],
                'blacklist': []
            }
            client = MongoClient('mongodb://mongo:27017')
            db = client.m_db

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

    def set_admin_ids(self, admin_ids):
        self.data['admin_ids'] = admin_ids

    @property
    def blacklist(self):
        return self.data['blacklist']
