# stdlib
import logging
import random
from datetime import datetime as dt
from datetime import timedelta

# third-party
import pymongo
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from emoji import emojize
from pymongo import MongoClient

# local
from config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)


class ThorBot():
    def __init__(self):
        self.config = Config()

    def error(self, bot, update, error):
        logger.warning('Update "%s" caused error "%s"', update, error)

    def clear_db(self, bot, update):
        self.config.db.users.remove({})

    def add_user(self, bot, update):
        update = update.to_dict()
        user_id = update['message']['from']['id']
        username = '@' + update['message']['from']['username']
        chat_id = update['message']['chat']['id']
        try:
            self.config.db.users.insert_one({'username': username,
                                             'user_id': user_id,
                                             'chat_id': chat_id,
                                             'warnings': 0,
                                             'link_permits': 0})
        except pymongo.errors.DuplicateKeyError as dup:
            pass

        # Testing prints
        users = self.config.db.users.find()
        for user in users:
            logger.info(user)

    def warn(self, bot, update, args):
        update = update.to_dict()
        """if user_id in self.config.admin_ids:
            return"""
        if not args:
            return

        username = args[0]
        chat_id = update['message']['chat']['id']
        user_record = self.config.db.users.find_one(
            {
                'username': username,
                'chat_id': chat_id
            }
        )

        if not user_record:
            logger.error("No record found for user")
            return

        self.config.db.users.update_one(
            {'_id': user_record['_id']},
            {
                '$set': {
                    'warnings': user_record['warnings'] + 1
                }
            }, upsert=False)


    def run(self):
        updater = Updater(self.config.telegram_api_key)
        bot = updater.bot
        dp = updater.dispatcher

        administrators = [
            admin.to_dict() for admin in
            bot.getChatAdministrators(chat_id=self.config.group_id)]
        admin_ids = [admin['user']['id'] for admin in administrators]
        self.config.set_admin_ids(admin_ids)

        # Add the error handler
        dp.add_error_handler(self.error)

        # Message handlers
        dp.add_handler(MessageHandler(Filters.text, self.add_user))

        # Command handlers
        dp.add_handler(CommandHandler("clear_db", self.clear_db))
        dp.add_handler(CommandHandler("warn", self.warn, pass_args=True))

        # Start the Bot
        logger.info("Thorbot initialized, mjolnir charged...")
        updater.start_polling()
        updater.idle()


thorbot = ThorBot()
thorbot.run()
