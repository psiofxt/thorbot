# stdlib
import logging
import random
from datetime import datetime as dt
from datetime import timedelta

# third-party
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

        # Start the Bot
        logger.info("Thorbot initialized, mjolnir charged...")
        updater.start_polling()
        updater.idle()


thorbot = ThorBot()
thorbot.run()
