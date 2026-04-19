# -*- coding: utf-8 -*-
import asyncio
import logging
from uuid import uuid4

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from .broadcast import broadcast_new_language
from .config import ADMIN_GROUP_ID
from .database import (
    get_bot_lang,
    get_countries_by_continent,
    get_continent_name_and_img,
    get_country_name_and_img,
    get_custom_lang_name_and_flag,
    get_db,
    get_feedback,
    get_feedback_status,
    get_lang_name_and_flag,
    get_langs_by_country,
    get_languages_by_initial,
    get_user_status,
    init_user,
    insert_feedback,
    insert_richiesta,
    search_languages,
    set_bot_lang,
    update_feedback_admin_msg,
    update_feedback_status,
    update_richieste_status,
    update_user_status,
)
from .utils import get_translator

logger = logging.getLogger(__name__)

# ConversationHandler states
LANG_NAME, LANG_LINK, FEEDBACK_TEXT = range(3)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _main_menu(_, chat_type: str = "private") -> InlineKeyboardMarkup:
    ask_cb = "askLang" if chat_type == "private" else "askLangGroup"
    feed_cb = "feedback" if chat_type == "private" else "feedbackGroup"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(_("1️⃣ Catalogazione alfabetica"), callback_data="orderAlpha")],
        [InlineKeyboardButton(_("2️⃣ Catalogazione politica"), callback_data="orderPolitica")],
        [InlineKeyboardButton(_("➕ Richiedi lingua"), callback_data=ask_cb),
         InlineKeyboardButton(_("💬 Feedback"), callback_data=feed_cb)],
        [InlineKeyboardButton(_("🗣 Lingua Bot"), callback_data="linguaALT"),
         InlineKeyboardButton(_("ℹ️ Info"), callback_data="credits")],
    ])


def _welcome_text(_) -> str:
    return _(
        "<b>Benvenuto nell'Atlante linguistico di Telegram.</b>\n\n"
        "Tramite questo bot potrai:\n"
        "👉🏻 navigare tra lingue presenti, organizzate alfabeticamente e politicamente\n"
        "👉🏻 accedere alle schede delle lingue desiderate ed installarle su Telegram\n"
        "👉🏻 richiedere l'aggiunta di una lingua all'Atlante o fornirci un feedback\n"
        "👉🏻 cambiare lingua al bot"
    )


def _get_lang(chat_id: int) -> str:
    with get_db() as cur:
        return get_bot_lang(cur, chat_id)


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_lang = update.effective_user.language_code or "en"
    try:
        with get_db() as cur:
            init_user(cur, chat_id, user_lang)
            lang = get_bot_lang(cur, chat_id)
    except Exception as e:
        logger.error("DB error in start_handler: %s", e)
        await update.message.reply_text("⚠️ Database error. Please try again later.")
        return

    _ = get_translator(lang)[0]
    await update.message.reply_html(
        _welcome_text(_),
        reply_markup=_main_menu(_, update.effective_chat.type),
    )


# ---------------------------------------------------------------------------
# /cancel command
# ---------------------------------------------------------------------------

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: ARG001
    _ = get_translator(_get_lang(update.effective_chat.id))[0]
    await update.message.reply_text(_("👋 A presto!"))


# ---------------------------------------------------------------------------
# /info command
# ---------------------------------------------------------------------------

async def getid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"🪪 Il tuo ID Telegram è: <code>{update.effective_user.id}</code>", parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------------------
# Main callback dispatcher
# ---------------------------------------------------------------------------

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # acknowledge immediately to avoid Telegram timeout
    chat_id = query.message.chat_id
    chat_type = query.message.chat.type

    try:
        with get_db() as cur:
            lang = get_bot_lang(cur, chat_id)
    except Exception as e:
        logger.error("DB error fetching lang: %s", e)
        await query.answer(show_alert=True, text="⚠️ Errore database.")
        return

    _, __ = get_translator(lang)
    data = query.data or ""
    args = data.split("_")

    try:
        await _dispatch(query, context, args, lang, _, __, chat_type)
    except Exception as e:
        logger.error("Error in callback dispatch [%s]: %s", data, e)
        await query.answer(show_alert=True, text=_("❌ Si è verificato un errore. Riprova più tardi."))


async def _dispatch(query, context, args: list[str], lang: str, _, __, chat_type: str) -> None:
    action = args[0]
    chat_id = query.message.chat_id

    # ---- 404 / placeholder ----
    if action in ("404", ""):
        await query.answer(show_alert=True, text=_("⚠️ Ancora non disponibile"))

    # ---- Main menu ----
    elif action == "backMenu":
        await query.edit_message_text(
            _welcome_text(_),
            parse_mode=ParseMode.HTML,
            reply_markup=_main_menu(_, chat_type),
            disable_web_page_preview=True,
        )

    # ---- Alphabetic catalogue ----
    elif action == "orderAlpha":
        rows = [
            [InlineKeyboardButton(c, callback_data=f"orderChar_{c}") for c in "ABCDEFG"],
            [InlineKeyboardButton(c, callback_data=f"orderChar_{c}") for c in "HIJKLMN"],
            [InlineKeyboardButton(c, callback_data=f"orderChar_{c}") for c in "OPQRSTU"],
            [InlineKeyboardButton(c, callback_data=f"orderChar_{c}") for c in "VWXYZ"],
            [InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")],
        ]
        await query.edit_message_text(
            _("Hai scelto di proseguire tramite l'<b>organizzazione alfabetica</b>! 🔠\n\n"
              "Seleziona la prima lettera del nome della lingua che stai cercando."),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(rows),
            disable_web_page_preview=True,
        )

    elif action == "orderChar":
        if len(args) < 2:
            return
        char = args[1].upper()
        if len(char) != 1 or not char.isalpha():
            return
        with get_db() as cur:
            rows = get_languages_by_initial(cur, lang, char)
        buttons: list[list] = []
        row: list = []
        for name, _flag, code in rows:
            row.append(InlineKeyboardButton(name, callback_data=f"lang_{code}_oc_{char}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([
            InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"),
            InlineKeyboardButton(_("◀️ Indietro"), callback_data="orderAlpha"),
        ])
        count = len(rows)
        s = __(
            "È presente <b>{count}</b> lingua che inizia per <b>{char}</b>!\n\n"
            "Nel caso non sia presente in questo elenco, prima di richiedere la lingua che cerchi, "
            "assicurati che la lettera scelta sia corretta o prova ad utilizzare la catalogazione politica.",
            "Sono presenti <b>{count}</b> lingue che iniziano per <b>{char}</b>!\n\n"
            "Nel caso non sia presente in questo elenco, prima di richiedere la lingua che cerchi, "
            "assicurati che la lettera scelta sia corretta o prova ad utilizzare la catalogazione politica.",
            count,
        ).format(count=count, char=char)
        await query.edit_message_text(s, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    # ---- Political / geographic catalogue ----
    elif action == "orderPolitica":
        continents = [
            (_("America settentrionale"), "orderCont_1"),
            (_("America meridionale"),   "orderCont_2"),
            (_("Europa"),                "orderCont_3"),
            (_("Africa"),                "orderCont_4"),
            (_("Asia"),                  "orderCont_5"),
            (_("Oceania"),               "orderCont_6"),
        ]
        rows = [[InlineKeyboardButton(name, callback_data=cb)] for name, cb in continents]
        rows.append([InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")])
        await query.edit_message_text(
            _("Hai scelto di proseguire tramite la <b>organizzazione politica</b>! <a href='https://atlasbot.garbo.tech/img/imgbot/planisfero_colorato.jpg'>🌍</a>\n\n"
              "Seleziona il continente che vuoi esplorare."),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(rows),
        )

    elif action == "orderCont":
        if len(args) < 2:
            return
        continent_id = int(args[1])
        offset = int(args[2]) if len(args) >= 3 else 0
        with get_db() as cur:
            continent = get_continent_name_and_img(cur, lang, continent_id)
            countries = get_countries_by_continent(cur, lang, continent_id, offset)
        if not continent:
            return
        continent_name, img_url = continent
        rows = [[InlineKeyboardButton(name, callback_data=f"orderState_{cid}")]
                for cid, name in countries]
        nav: list = []
        if offset > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"orderCont_{continent_id}_{max(0, offset - 20)}"))
        if len(countries) == 20:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"orderCont_{continent_id}_{offset + 20}"))
        if nav:
            rows.append(nav)
        rows.append([InlineKeyboardButton(_("⏪ Torna indietro"), callback_data="orderPolitica")])
        await query.edit_message_text(
            _("Ottimo, hai selezionato l'<b>{continent}</b>! <a href='{img}'>🌍</a>\n\n"
              "Ora seleziona lo Stato che vuoi visitare.").format(continent=continent_name, img=img_url),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(rows),
        )

    elif action == "orderState":
        if len(args) < 2:
            return
        country_id = int(args[1])
        offset = int(args[2]) if len(args) >= 3 else 0
        with get_db() as cur:
            country = get_country_name_and_img(cur, lang, country_id)
            langs = get_langs_by_country(cur, lang, country_id, offset)
        if not country:
            return
        country_name, img_url = country
        rows = [[InlineKeyboardButton(name, callback_data=f"lang_{code}_os_{country_id}")]
                for code, name in langs]
        nav: list = []
        if offset > 0:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"orderState_{country_id}_{max(0, offset - 20)}"))
        if len(langs) == 20:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"orderState_{country_id}_{offset + 20}"))
        if nav:
            rows.append(nav)
        rows.append([InlineKeyboardButton(_("⏪ Torna indietro"), callback_data="orderPolitica")])
        await query.edit_message_text(
            _("Ecco le lingue attualmente presenti nello Stato: <b>{state}</b>! <a href='{img}'>🌍</a>\n\n"
              "Seleziona la lingua che preferisci per accedere alla sua scheda e vedere le opzioni disponibili.\n\n"
              "Nel caso non sia presente in questo elenco, prima di richiedere la lingua che cerchi, "
              "prova a visitare altri Stati o ad utilizzare la catalogazione alfabetica.").format(
                state=country_name, img=img_url),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(rows),
        )

    # ---- Language detail ----
    elif action == "lang":
        # lang_{code}_{oc|os}_{char_or_country_id}
        if len(args) < 4:
            return
        code = args[1]
        origin = args[2]   # "oc" = from orderChar, "os" = from orderState
        back_id = args[3]
        with get_db() as cur:
            row = get_lang_name_and_flag(cur, lang, code) or get_custom_lang_name_and_flag(cur, lang, code)
        if not row:
            await query.answer(show_alert=True, text=_("⚠️ Lingua non trovata."))
            return
        name, flag = row
        back_cb = f"orderChar_{back_id}" if origin == "oc" else f"orderState_{back_id}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"),
            InlineKeyboardButton(_("◀️ Indietro"), callback_data=back_cb),
        ]])
        await query.edit_message_text(
            _("Per installare la lingua {langName} su Telegram clicca sul seguente link.\n\n"
              "<a href='{flag}'>👉🏻</a> https://t.me/setlanguage/{code}\n\n"
              "Ricorda: potrai sempre tornare alla lingua iniziale tramite le impostazioni native dell'app.").format(
                langName=name, flag=flag, code=code),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    # ---- Bot language selection ----
    elif action == "linguaALT":
        sel = {k: "" for k in ("it", "en", "fur", "vec", "es", "cat")}
        sel[lang] = "☑️"
        rows = [
            [InlineKeyboardButton(f"Català {sel['cat']}",    callback_data="setBotLang_cat"),
             InlineKeyboardButton(f"English {sel['en']}",   callback_data="setBotLang_en")],
            [InlineKeyboardButton(f"Español {sel['es']}",   callback_data="setBotLang_es"),
             InlineKeyboardButton(f"Furlan {sel['fur']}",   callback_data="setBotLang_fur")],
            [InlineKeyboardButton(f"Italiano {sel['it']}",  callback_data="setBotLang_it"),
             InlineKeyboardButton(f"Veneto {sel['vec']}",   callback_data="setBotLang_vec")],
            [InlineKeyboardButton(_("🌐 Contribute a translation"), url="https://github.com/garboh/langAtlasBot"),
             InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")],
        ]
        await query.edit_message_text(
            _("Seleziona la lingua del bot.\n\n"
              "Se la lingua che desideri non fosse presente nell'elenco seguente, puoi contribuire aprendo una "
              "<a href='https://github.com/garboh/langAtlasBot'>Pull Request su GitHub</a> con il file di traduzione. 👍🏻\n\n"
              "Nel caso dovessi riscontrare qualche difficoltà non esitare ad utilizzare il modulo di feedback."),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(rows),
            disable_web_page_preview=True,
        )

    elif action == "setBotLang":
        new_lang = args[1] if len(args) >= 2 else "en"
        with get_db() as cur:
            set_bot_lang(cur, new_lang, chat_id)
        _ = get_translator(new_lang)[0]
        await query.edit_message_text(
            _("✅ Lingua del Bot cambiata. Premi su /start per applicare le modifiche."),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    # ---- Credits / Info ----
    elif action == "credits":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(_("📝 Disclaimer"), callback_data="funzCat")],
            [InlineKeyboardButton(_("👥 Riconoscimenti"), callback_data="talksUs")],
            [InlineKeyboardButton(_("⚒ Codice sorgente"), url="https://github.com/garboh/langAtlasBot")],
            [InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")],
        ])
        await query.edit_message_text(
            _("L'<b>Atlante Linguistico</b> ospita e punta a diffondere tutte le possibili localizzazioni "
              "linguistiche di Telegram, offrendo funzioni avanzate di ricerca e applicazione.\n\n"
              "L'Atlante nasce dall'idea e dalla progettazione di <a href='https://t.me/cmpfrc'>Federico</a>, "
              "e dal supporto degli altri collaboratori di <a href='https://t.me/LenguaVeneta'>Còdaze Veneto</a>, "
              "ente che si occupa della localizzazione e diffusione di prodotti in lingua veneta.\n"
              "@langAtlasBot è stato sviluppato in <a href='https://it.wikipedia.org/wiki/Python'>Python</a> "
              "e viene mantenuto da <a href='https://t.me/garboh'>Francesco</a>.\n\n"
              "Utilizza il modulo di feedback per eventuali apprezzamenti, suggerimenti o proposte. "
              "Grazie di aver mostrato interesse per l'Atlante! 😉"),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    elif action == "funzCat":
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"),
            InlineKeyboardButton(_("◀️ Indietro"), callback_data="credits"),
        ]])
        await query.edit_message_text(
            _("📝 <b>Disclaimer</b>\n\n"
              "I dati inseriti nell'Atlante riguardanti l'organizzazione politica delle lingue sono stati "
              "raccolti dalle pagine di Wikipedia italiana ed inglese. In caso di errori o dati mancanti "
              "si prega di comunicarlo tramite il modulo di feedback.\n\n"
              "Le lingue inserite nell'Atlante richiedono uno standard minimo di completezza e qualità. "
              "Si richiede che siano completi almeno 2 client e che ci sia volontà di completamento e "
              "aggiornamento dell'intero progetto di traduzione. "
              "Come una lingua può facilmente essere aggiunta potrà altrettanto facilmente essere rimossa."),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    elif action == "talksUs":
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"),
            InlineKeyboardButton(_("◀️ Indietro"), callback_data="credits"),
        ]])
        await query.edit_message_text(
            _("In questa sezione sono elencati i riferimenti a siti, giornali, agenzie di stampa e a "
              "qualsiasi altro media che si è occupato o ha diffuso il nostro progetto:\n\n"
              "➖ l'<a href='https://arlef.it/en/'>ARLeF</a> ha presentato l'Atlante durante la "
              "<b>conferenza stampa regionale</b> sulla localizzazione di Telegram in Friulano."),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    # ---- Lang request intro (private only) ----
    elif action == "askLang":
        if chat_type != "private":
            await _redirect_to_private(query, context, _, _("➕ Richiedi lingua"))
            return
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"),
            InlineKeyboardButton(_("Procedi ▶️"), callback_data="okAskLang"),
        ]])
        await query.edit_message_text(
            _("Con questa procedura potrai richiedere l'inserimento di una lingua all'Atlante.\n\n"
              "La richiesta verrà visionata dai nostri moderatori; in seguito ti sarà fornito un "
              "riscontro sull'avanzamento della proposta. Ti chiediamo di pazientare."),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    elif action == "askLangGroup":
        await _redirect_to_private(query, context, _, _("➕ Richiedi lingua"))

    elif action == "feedbackGroup":
        await _redirect_to_private(query, context, _, _("💬 Feedback"))

    # ---- Cancel (outside conversation) ----
    elif action == "cancel":
        with get_db() as cur:
            update_user_status(cur, "action_cancel", chat_id)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
        await query.edit_message_text(
            _("✅ Operazione annullata."),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    # ---- Admin: approve language request ----
    elif action == "langAdded":
        # langAdded_{user_id}_{lang_name}_{request_id}_{user_lang}
        if len(args) < 5:
            return
        user_id, lang_name, req_id, user_lang_code = args[1], args[2], args[3], args[4]
        await query.edit_message_text(
            f"{query.message.text}\n\n#inserito by @{query.from_user.username}",
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML,
        )
        _u = get_translator(user_lang_code)[0]
        await context.bot.send_message(
            chat_id=int(user_id),
            text=_u("Ottime notizie! La tua richiesta di inserimento della lingua {langName} nell'Atlante "
                    "Linguistico è stata accettata! 👌🏻\n\nOra, con la modalità INLINE del bot @langAtlasBot, "
                    "potrai condividere nelle chat la lingua che hai richiesto.").format(langName=lang_name),
            parse_mode=ParseMode.HTML,
        )
        with get_db() as cur:
            update_richieste_status(cur, 2, int(req_id))
        await context.bot.unpin_chat_message(chat_id=ADMIN_GROUP_ID, message_id=query.message.message_id)
        asyncio.create_task(broadcast_new_language(context.bot, int(req_id)))

    # ---- Admin: reject language request ----
    elif action in ("langRifiutato", "langRifiutatoISO", "langRifiutatoNotExist",
                    "langRifiutatoExist", "langRifiutatoLink"):
        if len(args) < 5:
            return
        user_id, lang_name, req_id, user_lang_code = args[1], args[2], args[3], args[4]
        tag = {
            "langRifiutato":         "#rifiutato",
            "langRifiutatoISO":      "#rifiutato ISO_ERROR",
            "langRifiutatoNotExist": "#rifiutato NOT_EXIST",
            "langRifiutatoExist":    "#rifiutato ALREADY_EXIST",
            "langRifiutatoLink":     "#rifiutato LINK_ERROR",
        }[action]
        await query.edit_message_text(
            f"{query.message.text}\n\n{tag} by @{query.from_user.username}",
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML,
        )
        _u = get_translator(user_lang_code)[0]
        reasons = {
            "langRifiutato":         _u("Siamo spiacenti, la tua richiesta di inserimento della lingua {n} "
                                        "nell'Atlante Linguistico è stata rifiutata. <b>Per ora</b> non possiede "
                                        "i requisiti di qualità e completezza necessari. 🖐🏻").format(n=lang_name),
            "langRifiutatoISO":      _u("Siamo spiacenti, il codice ISO fornito non è corretto. "
                                        "Invia una nuova richiesta con le informazioni corrette."),
            "langRifiutatoNotExist": _u("Spiacenti, la lingua che hai inviato non esiste."),
            "langRifiutatoExist":    _u("Siamo spiacenti, la lingua {n} è già presente nell'Atlante "
                                        "e non può essere reinserita.").format(n=lang_name),
            "langRifiutatoLink":     _u("Siamo spiacenti, hai fornito un link errato. Ricorda: il link deve "
                                        "puntare a un progetto su https://translations.telegram.org\n"
                                        "Invia una nuova richiesta con le informazioni corrette."),
        }
        await context.bot.send_message(int(user_id), text=reasons[action], parse_mode=ParseMode.HTML)
        with get_db() as cur:
            update_richieste_status(cur, 3, int(req_id))
        await context.bot.unpin_chat_message(chat_id=ADMIN_GROUP_ID, message_id=query.message.message_id)

    # ---- Admin: answer feedback ----
    elif action == "feedbackAnsw":
        if len(args) < 2:
            return
        feedback_id = int(args[1])
        with get_db() as cur:
            status = get_feedback_status(cur, feedback_id)
            if not status:
                await query.answer(show_alert=True, text="❌ Feedback non trovato.")
                return
            if status[0] == "toBeAnswered":
                update_user_status(cur, f"answeringFeedback_{feedback_id}", query.from_user.id)
                update_feedback_status(cur, "answering", feedback_id)
        if status[0] == "toBeAnswered":
            await context.bot.send_message(query.from_user.id,
                                           "✏️ Inviami la risposta al feedback (solo testo).")
        elif status[0] == "answering":
            await query.answer(show_alert=True, text="⚠️ Qualcuno sta già rispondendo a questo feedback.")
        else:
            await query.answer(show_alert=True, text="❌ Stato del feedback non valido.")


async def _redirect_to_private(query, context, _, button_text: str) -> None:
    await query.answer(
        show_alert=True,
        text=_("🚫 Questa funzione è disponibile solo nella chat privata con il bot."),
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(button_text, url="https://t.me/langAtlasBot?start=open"),
    ]])
    await context.bot.send_message(
        query.from_user.id,
        text=_("Salve! Utilizza questo spazio per la funzione richiesta."),
        reply_markup=keyboard,
    )


# ---------------------------------------------------------------------------
# ConversationHandler — language request
# ---------------------------------------------------------------------------

async def ask_lang_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    lang = _get_lang(chat_id)
    _ = get_translator(lang)[0]
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(_("❌ Annulla"), callback_data="conv_cancel")]])
    await query.edit_message_text(
        _("Ottimo!\nScrivi il <b>nome della lingua</b> che vorresti fosse aggiunta all'Atlante."),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
    return LANG_NAME


async def receive_lang_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(update.effective_chat.id)
    _ = get_translator(lang)[0]
    name = update.message.text.strip()
    if len(name) > 100:
        await update.message.reply_text(_("⚠️ Il nome della lingua è troppo lungo. Riprova."))
        return LANG_NAME
    context.user_data["lang_request_name"] = name
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(_("❌ Annulla"), callback_data="conv_cancel")]])
    await update.message.reply_text(
        _("Ottimo! Ora inviami il link al progetto di traduzione su <a href='https://translations.telegram.org'>translations.telegram.org</a>.").format(),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
    return LANG_LINK


async def receive_lang_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    lang = _get_lang(chat_id)
    _ = get_translator(lang)[0]
    link = update.message.text.strip()

    if "translations.telegram.org" not in link:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(_("❌ Annulla"), callback_data="conv_cancel")]])
        await update.message.reply_text(
            _("⚠️ Il link non sembra valido. Deve contenere translations.telegram.org. Riprova."),
            reply_markup=keyboard,
        )
        return LANG_LINK

    name = context.user_data.pop("lang_request_name", "")
    try:
        with get_db() as cur:
            req_id = insert_richiesta(cur, chat_id, name, link)
        await context.bot.send_message(
            ADMIN_GROUP_ID,
            f"🆕 <b>Nuova richiesta lingua</b>\n\n"
            f"👤 User ID: <code>{chat_id}</code>\n"
            f"🌐 Lingua: <b>{name}</b>\n"
            f"🔗 Link: {link}\n"
            f"🆔 Request ID: <code>{req_id}</code>\n\n"
            f"Azioni:\n"
            f"/langAdded_{chat_id}_{name}_{req_id}_{lang}\n"
            f"/langRifiutato_{chat_id}_{name}_{req_id}_{lang}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approva", callback_data=f"langAdded_{chat_id}_{name}_{req_id}_{lang}"),
                 InlineKeyboardButton("❌ Rifiuta", callback_data=f"langRifiutato_{chat_id}_{name}_{req_id}_{lang}")],
                [InlineKeyboardButton("🚫 ISO error", callback_data=f"langRifiutatoISO_{chat_id}_{name}_{req_id}_{lang}"),
                 InlineKeyboardButton("🚫 Non esiste", callback_data=f"langRifiutatoNotExist_{chat_id}_{name}_{req_id}_{lang}")],
                [InlineKeyboardButton("🚫 Già presente", callback_data=f"langRifiutatoExist_{chat_id}_{name}_{req_id}_{lang}"),
                 InlineKeyboardButton("🚫 Link errato", callback_data=f"langRifiutatoLink_{chat_id}_{name}_{req_id}_{lang}")],
            ]),
        )
        await update.message.reply_text(
            _("✅ Richiesta inviata con successo! I nostri moderatori la valuteranno al più presto. Grazie! 🙏"),
            parse_mode=ParseMode.HTML,
            reply_markup=_main_menu(_),
        )
    except Exception as e:
        logger.error("Error inserting richiesta: %s", e)
        await update.message.reply_text(_("❌ Si è verificato un errore. Riprova più tardi."))

    return ConversationHandler.END


# ---------------------------------------------------------------------------
# ConversationHandler — feedback
# ---------------------------------------------------------------------------

async def feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.message.chat.type != "private":
        await query.answer(
            show_alert=True,
            text="🚫 Il feedback può essere inviato solo nella chat privata con il bot.",
        )
        return ConversationHandler.END

    lang = _get_lang(query.message.chat_id)
    _ = get_translator(lang)[0]
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(_("❌ Annulla"), callback_data="conv_cancel")]])
    await query.edit_message_text(
        _("Inviaci un commento o suggerimento. Il tuo messaggio verrà visionato dagli amministratori dell'Atlante."),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
    return FEEDBACK_TEXT


async def receive_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    lang = _get_lang(chat_id)
    _ = get_translator(lang)[0]
    text = update.message.text.strip()
    if len(text) > 2000:
        await update.message.reply_text(_("⚠️ Il messaggio è troppo lungo (max 2000 caratteri). Riprova."))
        return FEEDBACK_TEXT
    user = update.effective_user
    full_name = user.full_name
    username = user.username

    try:
        with get_db() as cur:
            feed_id = insert_feedback(cur, chat_id, text, full_name, username)

        user_line = f"👤 <b>{full_name}</b>"
        if username:
            user_line += f" (@{username})"
        admin_text = (
            f"💬 <b>Nuovo feedback</b>\n\n"
            f"{user_line}\n"
            f"🆔 ID: <code>{chat_id}</code>\n"
            f"🌐 Lingua bot: {lang}\n"
            f"🔢 Feedback ID: <code>{feed_id}</code>\n\n"
            f"{text}"
        )
        msg = await context.bot.send_message(
            ADMIN_GROUP_ID,
            admin_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✏️ Rispondi", callback_data=f"feedbackAnsw_{feed_id}"),
            ]]),
        )
        with get_db() as cur:
            update_feedback_admin_msg(cur, feed_id, msg.message_id)

        await update.message.reply_text(
            _("✅ Feedback inviato! Grazie per il tuo contributo. 📬"),
            reply_markup=_main_menu(_),
        )
    except Exception as e:
        logger.error("Error inserting feedback: %s", e)
        await update.message.reply_text(_("❌ Si è verificato un errore. Riprova più tardi."))

    return ConversationHandler.END


# Shared cancel for both conversations
async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    lang = _get_lang(query.message.chat_id)
    _ = get_translator(lang)[0]
    await query.edit_message_text(
        _("✅ Operazione annullata."),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"),
        ]]),
    )
    return ConversationHandler.END


async def cancel_command_in_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    lang = _get_lang(update.effective_chat.id)
    _ = get_translator(lang)[0]
    await update.message.reply_text(_("✅ Operazione annullata."))
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Text handler (admin feedback replies, outside conversations)
# ---------------------------------------------------------------------------

async def testo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    try:
        with get_db() as cur:
            status = get_user_status(cur, chat_id)
    except Exception as e:
        logger.error("DB error in testo_handler: %s", e)
        return

    if not status or not status.startswith("answeringFeedback_"):
        return

    feedback_id = int(status.split("_", 1)[1])
    reply_text = update.message.text.strip()

    try:
        with get_db() as cur:
            fb = get_feedback(cur, feedback_id)
            if not fb:
                await update.message.reply_text("❌ Feedback non trovato.")
                return
            user_id, fb_text, admin_msg_id, fb_full_name, fb_username = fb
            update_feedback_status(cur, "answered", feedback_id)
            update_user_status(cur, "new_user", chat_id)

        lang = _get_lang(user_id)
        _ = get_translator(lang)[0]
        await context.bot.send_message(
            user_id,
            _("📬 <b>Risposta al tuo feedback</b>\n\n{reply}").format(reply=reply_text),
            parse_mode=ParseMode.HTML,
        )
        await update.message.reply_text("✅ Risposta inviata con successo!")

        if admin_msg_id:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
            admin_username = update.effective_user.username
            respondent = f"@{admin_username}" if admin_username else update.effective_user.full_name

            user_line = f"👤 <b>{fb_full_name}</b>"
            if fb_username:
                user_line += f" (@{fb_username})"
            edited_text = (
                f"💬 <b>Nuovo feedback</b>\n\n"
                f"{user_line}\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"🔢 Feedback ID: <code>{feedback_id}</code>\n\n"
                f"{fb_text}\n\n"
                f"✅ Risposto da {respondent} il {now}"
            )
            try:
                await context.bot.edit_message_text(
                    chat_id=ADMIN_GROUP_ID,
                    message_id=admin_msg_id,
                    text=edited_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=None,
                )
            except Exception as e:
                logger.warning("Could not edit admin feedback message: %s", e)
    except Exception as e:
        logger.error("Error sending feedback reply: %s", e)
        await update.message.reply_text("❌ Errore nell'invio della risposta.")


# ---------------------------------------------------------------------------
# Inline mode
# ---------------------------------------------------------------------------

async def inline_mode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query_text = update.inline_query.query.strip()
    user_id = update.inline_query.from_user.id

    try:
        with get_db() as cur:
            lang = get_bot_lang(cur, user_id)
            rows = search_languages(cur, query_text, lang)
    except Exception as e:
        logger.error("DB error in inline_mode_handler: %s", e)
        await update.inline_query.answer([])
        return

    _ = get_translator(lang)[0]
    results = []
    for code, name, flag in rows:
        results.append(InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"🌐 {name}",
            thumbnail_url=flag or None,
            description=_("Applica la lingua {langName} su Telegram!").format(langName=name),
            input_message_content=InputTextMessageContent(
                _("Per installare la lingua {langName} su Telegram clicca sul seguente link.\n\n"
                  "<a href='{flag}'>👉🏻</a> https://t.me/setlanguage/{code}\n\n"
                  "Ricorda: potrai sempre tornare alla lingua iniziale tramite le impostazioni native dell'app.").format(
                    langName=name, flag=flag or "", code=code),
                parse_mode=ParseMode.HTML,
            ),
        ))

    if not results:
        results.append(InlineQueryResultArticle(
            id=str(uuid4()),
            title=_("Non è stata trovata alcuna lingua."),
            description=_("Nessun risultato trovato."),
            input_message_content=InputTextMessageContent(_("❌ Non è stata trovata alcuna lingua.")),
        ))

    await update.inline_query.answer(results, cache_time=30)


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception:", exc_info=context.error)
    try:
        await context.bot.send_message(
            ADMIN_GROUP_ID,
            f"⚠️ Unhandled error:\n<code>{context.error}</code>\n\nUpdate:\n<code>{update}</code>",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    if not isinstance(update, Update):
        return
    if update.effective_message:
        lang = _get_lang(update.effective_chat.id)
        _ = get_translator(lang)[0]
        try:
            await update.effective_message.reply_text(
                _("❌ Si è verificato un errore. Riprova più tardi.\n\n"
                  "Gli amministratori del bot sono già stati avvisati. "
                  "Se il problema persiste utilizza il modulo di feedback. 📬"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"),
                ]]),
            )
        except Exception:
            pass
