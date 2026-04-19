# -*- coding: utf-8 -*-
import logging
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

from .config import BOT_TOKEN
from .handlers import (
    FEEDBACK_TEXT,
    LANG_LINK,
    LANG_NAME,
    ask_lang_start,
    callback_query_handler,
    cancel_command_in_conv,
    cancel_conversation,
    cancel_handler,
    error_handler,
    feedback_start,
    getid_handler,
    inline_mode_handler,
    receive_feedback,
    receive_lang_link,
    receive_lang_name,
    start_handler,
    testo_handler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def build_application() -> Application:
    ask_lang_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_lang_start, pattern="^okAskLang$")],
        states={
            LANG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_lang_name)],
            LANG_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_lang_link)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_conversation, pattern="^conv_cancel$"),
            CommandHandler("cancel", cancel_command_in_conv),
        ],
        per_message=False,
    )

    feedback_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(feedback_start, pattern="^feedback$")],
        states={
            FEEDBACK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_feedback)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_conversation, pattern="^conv_cancel$"),
            CommandHandler("cancel", cancel_command_in_conv),
        ],
        per_message=False,
    )

    app = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandlers must come before the generic CallbackQueryHandler
    app.add_handler(ask_lang_conv)
    app.add_handler(feedback_conv)

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("cancel", cancel_handler))
    app.add_handler(CommandHandler("info", getid_handler))

    app.add_handler(CallbackQueryHandler(callback_query_handler))
    app.add_handler(InlineQueryHandler(inline_mode_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, testo_handler))

    app.add_error_handler(error_handler)

    return app


def main() -> None:
    app = build_application()
    logger.info("langAtlasBot avviato.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
