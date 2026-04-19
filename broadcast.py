# -*- coding: utf-8 -*-
import asyncio
import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from .config import ADMIN_GROUP_ID
from .database import get_db, get_richiesta, get_all_users

logger = logging.getLogger(__name__)

_MESSAGES: dict[str, str] = {
    "it":  "➕ Nuova lingua aggiunta!\n\nNell'Atlante è stata inserita la lingua <b>{name}</b>.\nPer provarla utilizza il link {link}!",
    "vec": "➕ Łengua nova zontada!\n\nInte l'Atlante a ze stà zontada na łengua nova <b>{name}</b>.\nPar proarla dòpara el link {link}!",
    "es":  "➕ ¡Nuevo idioma añadido!\n\n¡El idioma <b>{name}</b> ha sido añadido al Atlas!\nUtiliza el siguiente enlace para probarlo: {link}",
    "fur": "➕ Zontade une gnove lenghe!\n\nLa lenghe <b>{name}</b> e je stade zontade al Atlant.\nDopre il link {link} par provâle!",
    "cat": "➕ S'ha afegit un idioma nou!\n\nL'idioma <b>{name}</b> ha estat afegit a l'Atles.\nFes servir l'enllaç {link} per provar-lo!",
    "en":  "➕ New language added!\n\nThe language <b>{name}</b> has been inserted in the Atlas.\nUse the link {link} to try it!",
}


async def broadcast_new_language(bot: Bot, richiesta_id: int) -> None:
    with get_db() as cur:
        row = get_richiesta(cur, richiesta_id)
        if not row:
            logger.error("Richiesta %s not found for broadcast", richiesta_id)
            return
        name_lang, link_lang = row[0], row[1]
        users = get_all_users(cur)

    sent = errors = 0
    total = len(users)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Share 🌐", switch_inline_query=name_lang)]])

    try:
        status_msg = await bot.send_message(ADMIN_GROUP_ID, f"📢 Avvio notifica per <b>{name_lang}</b> ({total} utenti)...", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error("Could not send start notification: %s", e)
        return

    for i, (chat_id, lang) in enumerate(users, 1):
        template = _MESSAGES.get(lang, _MESSAGES["en"])
        text = template.format(name=name_lang, link=link_lang)
        try:
            await bot.send_message(chat_id, text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            sent += 1
        except Exception as e:
            logger.debug("Could not deliver to %s: %s", chat_id, e)
            errors += 1

        if i % 10 == 0:
            try:
                await bot.edit_message_text(
                    chat_id=ADMIN_GROUP_ID,
                    message_id=status_msg.message_id,
                    text=f"📢 Notifica in corso...\n✅ {sent} inviati | ❌ {errors} errori | {i}/{total}",
                )
            except Exception:
                pass
            await asyncio.sleep(0.5)
        else:
            await asyncio.sleep(0.05)

    await bot.send_message(
        ADMIN_GROUP_ID,
        f"✅ Notifica completata per <b>{name_lang}</b>!\n✅ {sent} inviati | ❌ {errors} errori",
        parse_mode=ParseMode.HTML,
    )
