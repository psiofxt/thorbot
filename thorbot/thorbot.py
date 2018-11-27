# stdlib
import logging
import random
import re
from datetime import datetime as dt
from datetime import timedelta

# third-party
import pymongo
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from emoji import emojize
from pymongo import MongoClient

# local
from config import Config
from messages import (
    LINK_WARN, PERMITTED, WARN, FINAL_WARNING, WELCOME_MESSAGE, CLEAR_WARN,
    AIRDROP, TOKENS
)
from utils import admin_only, exempt_admins, config_chat_only

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)


class ThorBot():
    def __init__(self):
        self.config = Config()

    def error(self, bot, update, error):
        logger.warning('Update "%s" caused error "%s"', update, error)

    @config_chat_only
    @admin_only()
    def clear_db(self, bot, update):
        self.config.db.users.remove({})

    @config_chat_only
    @exempt_admins()
    def add_user(self, bot, update):
        update = update.to_dict()
        user_id = update['message']['from']['id']
        try:
            username = '@' + update['message']['from']['username']
        except KeyError:
            logger.info("No username for user")
            return
        except TypeError:
            logger.info("No username for user")
            return
        chat_id = update['message']['chat']['id']
        try:
            self.config.db.users.insert_one({'username': username,
                                             'user_id': user_id,
                                             'chat_id': chat_id,
                                             'warnings': 0,
                                             'link_permits': 0})
        except pymongo.errors.DuplicateKeyError as dup:
            pass

    @config_chat_only
    @admin_only()
    def warn(self, bot, update, args):
        update = update.to_dict()
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
                '$inc': {
                    'warnings': 1
                }
            }, upsert=False)
        updated_warning = user_record['warnings'] + 1
        bot.delete_message(chat_id=chat_id,
                           message_id=update['message']['message_id'])

        if updated_warning == self.config.warn_limit - 1:
            message = emojize(FINAL_WARNING.format(
                num=updated_warning, username=username), use_aliases=True)
        elif updated_warning == self.config.warn_limit:
            bot.kick_chat_member(chat_id, user_record['user_id'])
            bot.send_message(chat_id=chat_id,
                             text="Kicked user {}".format(username))
            self.config.db.users.remove(user_record['_id'])
            return
        else:
            message = emojize(WARN.format(
               num=updated_warning, username=username), use_aliases=True)
        bot.send_message(chat_id=chat_id,
                         text=emojize(message))

    @config_chat_only
    @admin_only()
    def clear_warnings(self, bot, update, args):
        update = update.to_dict()
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
                    'warnings': 0
                }
            }, upsert=False)
        bot.delete_message(chat_id=chat_id,
                           message_id=update['message']['message_id'])
        message = CLEAR_WARN.format(username=username)
        bot.send_message(chat_id=chat_id,
                         text=message)

    @config_chat_only
    @admin_only()
    def permit_link(self, bot, update, args):
        update = update.to_dict()
        if not args:
            return

        username = args[0]
        try:
            num = int(args[1])
        except IndexError:
            num = 1
        except ValueError:
            return
        chat_id = update['message']['chat']['id']
        user_record = self.config.db.users.find_one(
            {
                'username': username,
                'chat_id': chat_id
            }
        )

        if not user_record:
            logger.error("No record found for user")
            bot.delete_message(chat_id=chat_id,
                               message_id=update['message']['message_id'])
            return

        self.config.db.users.update_one(
            {'_id': user_record['_id']},
            {
                '$set': {
                    'link_permits': num
                }
            }, upsert=False)
        bot.delete_message(chat_id=chat_id,
                           message_id=update['message']['message_id'])
        bot.send_message(chat_id=chat_id,
                         text=emojize(PERMITTED.format(
                            num=num, username=username), use_aliases=True))

    @config_chat_only
    def handle_new_chat_members(self, bot, update):
        msg = update.effective_message
        first_name = msg['new_chat_members'][0]['first_name']

        # Delete the join message
        try:
            bot.delete_message(
                chat_id=msg.chat.id,
                message_id=msg.message_id,
            )
        except Exception as ex:
            if 'Message to delete not found' in str(ex):
                logging.error('Failed to delete msg: %s', ex)
                return
            elif "Message can't be deleted" in str(ex):
                logging.error('Failed to delete msg: %s', ex)
                return
            else:
                raise

        # Delete the previous welcome message
        try:
            bot.delete_message(
                chat_id=msg.chat.id,
                message_id=self.config.last_welcome_id,
            )
        except KeyError:
            self.config.set_last_welcome_id = msg.message_id
        except Exception as ex:
            if 'Message to delete not found' in str(ex):
                logging.error('Failed to delete msg: %s', ex)
            elif "Message can't be deleted" in str(ex):
                logging.error('Failed to delete msg: %s', ex)
            else:
                pass

        welcome = bot.send_message(
            chat_id=msg.chat.id,
            text=emojize(WELCOME_MESSAGE.format(first_name=first_name),
                         use_aliases=True),
            parse_mode='Markdown')
        self.config.last_welcome_id = welcome['message_id']

        # Finally, inster the user
        user_id = msg['new_chat_members'][0]['id']
        try:
            username = '@' + msg['new_chat_members'][0]['username']
        except KeyError:
            logger.info("No username for user")
            return
        except TypeError:
            logger.info("No username for user")
            return
        chat_id = msg.chat.id
        try:
            self.config.db.users.insert_one({'username': username,
                                             'user_id': user_id,
                                             'chat_id': chat_id,
                                             'warnings': 0,
                                             'link_permits': 0})
        except pymongo.errors.DuplicateKeyError as dup:
            pass

    @config_chat_only
    def handle_left_chat_member(self, bot, update):
        msg = update.effective_message
        try:
            bot.delete_message(
                chat_id=msg.chat.id,
                message_id=msg.message_id,
            )
        except Exception as ex:
            if 'Message to delete not found' in str(ex):
                logging.error('Failed to delete join message: %s' % ex)
                return
            elif "Message can't be deleted" in str(ex):
                logging.error('Failed to delete msg: %s', ex)
                return
            else:
                raise

    @config_chat_only
    @exempt_admins()
    def handle_forwarded(self, bot, update):
        update = update.to_dict()
        chat_id = update['message']['chat']['id']
        try:
            username = '@' + update['message']['from']['username']
        except TypeError:
            logger.info("No username for user")
            bot.delete_message(chat_id=chat_id,
                               message_id=update['message']['message_id'])
            return
        user_id = update['message']['from']['id']

        user_record = self.config.db.users.find_one(
            {
                'username': username,
                'chat_id': chat_id
            }
        )
        if user_record and user_record['link_permits'] > 0:
            self.config.db.users.update_one(
                {'user_id': user_id},
                {
                    '$inc': {
                        'link_permits': -1
                    }
                }, upsert=False)
            return
        bot.delete_message(chat_id=chat_id,
                           message_id=update['message']['message_id'])

    @config_chat_only
    @exempt_admins()
    def handle_links(self, bot, update):
        update = update.to_dict()
        chat_id = update['message']['chat']['id']
        try:
            username = '@' + update['message']['from']['username']
        except TypeError:
            logger.info("No username for user")
            bot.delete_message(chat_id=chat_id,
                               message_id=update['message']['message_id'])
            return
        user_id = update['message']['from']['id']

        user_record = self.config.db.users.find_one(
            {
                'username': username,
                'chat_id': chat_id
            }
        )
        if user_record and user_record['link_permits'] > 0:
            self.config.db.users.update_one(
                {'user_id': user_id},
                {
                    '$inc': {
                        'link_permits': -1
                    }
                }, upsert=False)
            return
        bot.delete_message(chat_id=chat_id,
                           message_id=update['message']['message_id'])
        bot.send_message(chat_id=chat_id,
                         text=emojize(LINK_WARN.format(username=username)))

    @config_chat_only
    @exempt_admins()
    def handle_files(self, bot, update):
        update = update.to_dict()
        bot.delete_message(chat_id=update['message']['chat']['id'],
                           message_id=update['message']['message_id'])

    @config_chat_only
    def airdrop(self, bot, update):
        update = update.to_dict()
        bot.send_message(chat_id=update['message']['chat']['id'],
                         text=AIRDROP)

    @config_chat_only
    def tokens(self, bot, update):
        update = update.to_dict()
        bot.send_message(chat_id=update['message']['chat']['id'],
                         text=TOKENS)

    def run(self):
        updater = Updater(self.config.telegram_api_key)
        bot = updater.bot
        dp = updater.dispatcher

        administrators = [
            admin.to_dict() for admin in
            bot.getChatAdministrators(chat_id=self.config.group_id)]
        admin_ids = [admin['user']['id'] for admin in administrators]
        self.config.admin_ids = admin_ids

        # Add the error handler
        dp.add_error_handler(self.error)

        # Message handlers
        dp.add_handler(MessageHandler(Filters.document & (~ Filters.animation),
                                      self.handle_files))
        dp.add_handler(MessageHandler(Filters.entity("url"),
            self.handle_links))
        dp.add_handler(MessageHandler(Filters.forwarded,
            self.handle_forwarded))
        dp.add_handler(MessageHandler(Filters.text, self.add_user))
        dp.add_handler(MessageHandler(
            Filters.status_update.new_chat_members,
            self.handle_new_chat_members))
        dp.add_handler(MessageHandler(
            Filters.status_update.left_chat_member,
            self.handle_left_chat_member))

        # Command handlers
        dp.add_handler(CommandHandler("airdrop", self.airdrop))
        dp.add_handler(CommandHandler("tokens", self.tokens))
        dp.add_handler(CommandHandler("clear_db", self.clear_db))
        dp.add_handler(CommandHandler("warn", self.warn, pass_args=True))
        dp.add_handler(CommandHandler("clear_warnings",
                                      self.clear_warnings, pass_args=True))
        dp.add_handler(CommandHandler("permit", self.permit_link,
                                      pass_args=True))

        # Start the Bot
        logger.info("Thorbot initialized, mjolnir charged...")
        updater.start_polling()
        updater.idle()


thorbot = ThorBot()
thorbot.run()
