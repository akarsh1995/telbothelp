#!/usr/bin/env python
# pylint: disable=C0116
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from collections import defaultdict
import logging

import uuid
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


class Reply:
    def __init__(self, prev_dict, next_reply_val):
        if prev_dict:
            self.reply_dict = {**prev_dict}
        self.next_reply_val = next_reply_val

    def attach_reply(self, reply, keyboard_vals=None, catch_previous_answer_regex=None):
        def reply_func(update, context):
            if keyboard_vals:
                update.message.reply_text(
                    reply,
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard_vals, one_time_keyboard=True
                    ),
                )
            else:
                update.message.reply_text(reply)
            return self.next_reply_val

        if not self.reply_dict.get("states"):
            self.reply_dict["states"] = defaultdict(list)
        self.reply_dict["states"][self.next_reply_val] += [
            MessageHandler(Filters.regex(catch_previous_answer_regex), reply_func)
        ]
        return Reply(self.reply_dict, self.next_reply_val)

    def stop_with(self, reply, catch_previous_answer_regex=None):
        def reply_func(update, context):
            update.message.reply_text(reply, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        if not self.reply_dict.get("states"):
            self.reply_dict["states"] = defaultdict(list)
        self.reply_dict["states"][self.next_reply_val] += [
            MessageHandler(Filters.regex(catch_previous_answer_regex), reply_func)
        ]
        return Reply(self.reply_dict, self.next_reply_val)

    def chain_conversation(self, reply):
        def cancel(update, context):
            user = update.message.from_user
            logger.info("User %s canceled the conversation.", user.first_name)
            update.message.reply_text(reply, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        if not self.reply_dict.get("fallbacks"):
            self.reply_dict["fallbacks"] = []
        self.reply_dict["fallbacks"] += [CommandHandler("cancel", cancel)]
        return ConversationHandler(**self.reply_dict)


class CreateConversation:
    def __init__(self):
        self.dict_of_list = defaultdict(list)

    def start(self, reply, keyboard_vals):
        next_val = str(uuid.uuid4())

        def reply_func(update, context):
            update.message.reply_text(
                reply,
                reply_markup=ReplyKeyboardMarkup(keyboard_vals, one_time_keyboard=True),
            )
            return next_val

        self.dict_of_list["entry_points"] += [CommandHandler("start", reply_func)]
        return Reply(self.dict_of_list, next_val)


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater("973653339:AAHOmx9R9PB_MoaAp8GCXHJVaGmMIe1sozs")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO

    c = CreateConversation()
    d = (
        c.start(
            "This is starting. Select your gender?",
            keyboard_vals=[["Boy", "Girl", "Other"]],
        )
        .attach_reply(
            "Tell me your Age.",
            keyboard_vals=None,
            catch_previous_answer_regex=r"^(Boy|Girl|Other)$",
        )
        .attach_reply(
            "Your meal pref",
            keyboard_vals=[["NonVeg", "Veg"]],
            catch_previous_answer_regex=r"^\d+[a-z]$",
        )
        .attach_reply(
            "Debit/credit",
            keyboard_vals=[["Debit", "Credit"]],
            catch_previous_answer_regex=r"^(NonVeg|Veg)$",
        )
        .stop_with(
            "Thanks for the replies.", catch_previous_answer_regex=r"^(Debit|Credit)$"
        )
        .chain_conversation("Sorry something wrong.")
    )
    dispatcher.add_handler(d)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
