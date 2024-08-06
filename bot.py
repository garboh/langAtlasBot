# -*- coding: utf-8 -*-
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputTextMessageContent, InlineQueryResultArticle
from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler, InlineQueryHandler, MessageHandler, filters, CallbackContext
from telegram.constants import ParseMode
from uuid import uuid4

from .database import openDb, closeDb, getBotLang, setBotLang, init_user
from .handlers import inline_query_handler, start_handler, cancel_handler, getid_handler, testo_handler, photo_handler, error_handler, callback_query_handler, inline_mode_handler
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    application = ApplicationBuilder().token("TOKEN").build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("cancel", cancel_handler))
    application.add_handler(CommandHandler("info", getid_handler))

    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(InlineQueryHandler(inline_mode_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, testo_handler))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    application.add_error_handler(error_handler)

    logger.info("running langAtlasBot!")
    application.run_polling()

if __name__ == '__main__':
    main()