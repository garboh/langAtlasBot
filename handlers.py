# -*- coding: utf-8 -*-
import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InputTextMessageContent, InlineQueryResultArticle, Update
from telegram.ext import CallbackContext
from telegram.constants import ParseMode
from .utils import set_msg_lang, _, __
from .database import openDb, closeDb, getBotLang, setBotLang, init_user, get_feedback_status, update_user_status, update_feedback_status, update_richieste_status, get_continent_name_and_img, get_country_name_and_img, get_lang_name_and_flag, get_custom_lang_name_and_flag, get_languages_by_initial, getState, getLang, search_languages
from uuid import uuid4

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user_lang = update.message.from_user.language_code
    try:
        openDb()
        if init_user(chat_id, user_lang):
            lang = getBotLang(chat_id)
            setBotLang(lang, chat_id)
            set_msg_lang(lang)
        closeDb()
        welcome_message = _(
            "<b>Benvenuto nell'Atlante linguistico di Telegram.</b>\n\n"
            "Tramite questo bot potrai:\n"
            "👉🏻 navigare tra lingue presenti, organizzate alfabeticamente e politicamente\n"
            "👉🏻 accedere alle schede delle lingue desiderate ed installarle su Telegram\n"
            "👉🏻 richiedere l'aggiunta di una lingua all'Atlante o fornirci un feedback\n"
            "👉🏻 cambiare lingua al bot"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(_("1️⃣ Catalogazione alfabetica"), callback_data="orderAlpha")],
            [InlineKeyboardButton(_("2️⃣ Catalogazione politica"), callback_data="orderPolitica")],
            [InlineKeyboardButton(_("➕ Richiedi lingua"), callback_data="404"), InlineKeyboardButton(_("💬 Feedback"), callback_data="404")],
            [InlineKeyboardButton(_("🗣 Lingua Bot"), callback_data="linguaALT"), InlineKeyboardButton(_("ℹ️ Info"), callback_data="credits")]
        ])
        await context.bot.send_message(chat_id, text=welcome_message, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        await context.bot.send_message(chat_id, "Database connection failed. Please try again later.")

async def callback_query_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await handle_callback(query, context)

async def handle_callback(query, context):
    openDb()
    langBot = getBotLang(query.message.chat_id)
    setBotLang(langBot, query.message.chat_id)
    args = query.data.split('_')
    
    try:
        if args[0] == "404" or args[0] == "":
            await query.answer(show_alert=True, text=_("⚠️ Ancora non disponibile"))
        elif args[0] == "orderAlpha":
            keyboard_alfabetica = InlineKeyboardMarkup([
                [InlineKeyboardButton("A", callback_data="orderChar_A"), InlineKeyboardButton("B", callback_data="orderChar_B"),InlineKeyboardButton("C", callback_data="orderChar_C"),InlineKeyboardButton("D", callback_data="orderChar_D"),InlineKeyboardButton("E", callback_data="orderChar_E"),InlineKeyboardButton("F", callback_data="orderChar_F"),InlineKeyboardButton("G", callback_data="orderChar_G")],
                [InlineKeyboardButton("H", callback_data="orderChar_H"),InlineKeyboardButton("I", callback_data="orderChar_I"),InlineKeyboardButton("J", callback_data="orderChar_J"),InlineKeyboardButton("K", callback_data="orderChar_K"),InlineKeyboardButton("L", callback_data="orderChar_L"),InlineKeyboardButton("M", callback_data="orderChar_M"),InlineKeyboardButton("N", callback_data="orderChar_N")],
                [InlineKeyboardButton("O", callback_data="orderChar_O"),InlineKeyboardButton("P", callback_data="orderChar_P"),InlineKeyboardButton("Q", callback_data="orderChar_Q"),InlineKeyboardButton("R", callback_data="orderChar_R"),InlineKeyboardButton("S", callback_data="orderChar_S"),InlineKeyboardButton("T", callback_data="orderChar_T"),InlineKeyboardButton("U", callback_data="orderChar_U")],
                [InlineKeyboardButton("V", callback_data="orderChar_V"),InlineKeyboardButton("W", callback_data="orderChar_W"),InlineKeyboardButton("X", callback_data="orderChar_X"),InlineKeyboardButton("Y", callback_data="orderChar_Y"),InlineKeyboardButton("Z", callback_data="orderChar_Z")],
                [InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]
            ])
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("Hai scelto di proseguire tramite l'<b>organizzazione alfabetica</b>!🔠\n\nSeleziona la prima lettera del nome della lingua che stai cercando."),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard_alfabetica
            )
            await query.answer(show_alert=False, text="✅")
        elif args[0] == "backMenu":
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("<b>Benvenuto nell'Atlante linguistico di Telegram.</b>\n\nTramite questo bot potrai:\n👉🏻 navigare tra lingue presenti, organizzate alfabeticamente e politicamente\n👉🏻 accedere alle schede delle lingue desiderate ed installarle su Telegram\n👉🏻 richiedere l'aggiunta di una lingua all'Atlante o fornirci un feedback\n👉🏻 cambiare lingua al bot"),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(_("1️⃣ Catalogazione alfabetica"), callback_data="orderAlpha")],
                    [InlineKeyboardButton(_("2️⃣ Catalogazione politica"), callback_data="orderPolitica")],
                    [InlineKeyboardButton(_("➕ Richiedi lingua"), callback_data="404"), InlineKeyboardButton(_("💬 Feedback"), callback_data="404")],
                    [InlineKeyboardButton(_("🗣 Lingua Bot"), callback_data="linguaALT"), InlineKeyboardButton(_("ℹ️ Info"), callback_data="credits")]
                ])
            )
            await query.answer(show_alert=False, text="✅")
        elif args[0] == "feedbackAnsw":
            status = get_feedback_status(args[1])
            if status and status[0] == "toBeAnswered":
                await query.answer(show_alert=True, text="Ok, controlla in privata")
                update_user_status(f'answeringFeedback_{args[1]}', query.from_user.id)
                await context.bot.send_message(chat_id=query.from_user.id, text="Ehy.. inviami la risposta al feedback", parse_mode=ParseMode.HTML)
                update_feedback_status('answering', args[1])
            elif status and status[0] == "answering":
                await query.answer(show_alert=True, text="⚠️ Qualcuno sta già rispondendo")
            else:
                await query.answer(show_alert=True, text="❌ Qualcosa è andato storto...")
        elif args[0] == "langAdded":
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="{} \n\n#inserito by @{}".format(str(query.message.text), str(query.from_user.username)),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
            )
            set_msg_lang(args[4])
            await context.bot.send_message(
                chat_id=args[1],
                text=_("Ottime notizie! La tua richiesta di inserimento della lingua {langName} nell'Atlante Linguistico è stata accettata! 👌🏻\n\nOra, con la modalità INLINE del bot @langAtlastBot, potrai condividere nelle chat la lingua che hai richiesto. 👌🏻").format(langName=args[2]),
                parse_mode=ParseMode.HTML
            )
            await query.answer(show_alert=False, text="✅")
            update_richieste_status(2, args[3])
            await context.bot.unpin_chat_message(chat_id=-1001198344093, message_id=query.message.message_id)
            subprocess.check_call([sys.executable, "sendms.py", "{}".format(args[3])])
        elif args[0] == "langRifiutato":
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="{} \n\n#rifiutato by @{}".format(str(query.message.text), str(query.from_user.username)),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
            )
            set_msg_lang(args[4])
            await context.bot.send_message(
                chat_id=args[1],
                text=_("Siamo spiacenti, la tua richiesta di inserimento della lingua {langName} nell'Atlante Linguistico è stata rifiutata. <b>Per ora</b> non possiede i requisiti di qualità e completezza necessari al suo inserimento. 🖐🏻").format(langName=args[2]),
                parse_mode=ParseMode.HTML
            )
            await query.answer(show_alert=False, text="✅")
            update_richieste_status(3, args[3])
            await context.bot.unpin_chat_message(chat_id=-1001198344093, message_id=query.message.message_id)
        elif args[0] == "langRifiutatoISO":
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="{} \n\n#rifiutato ISO_ERROR by @{}".format(str(query.message.text), str(query.from_user.username)),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
            )
            set_msg_lang(args[4])
            await context.bot.send_message(
                chat_id=args[1],
                text=_("Siamo spiacenti, il codice ISO fornito non è corretto. Invia una nuova richiesta con le informazioni corrette."),
                parse_mode=ParseMode.HTML
            )
            await query.answer(show_alert=False, text="✅")
            update_richieste_status(3, args[3])
            await context.bot.unpin_chat_message(chat_id=-1001198344093, message_id=query.message.message_id)
        elif args[0] == "langRifiutatoNotExist":
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="{} \n\n#rifiutato NOT_EXIST by @{}".format(str(query.message.text), str(query.from_user.username)),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
            )
            set_msg_lang(args[4])
            await context.bot.send_message(
                chat_id=args[1],
                text=_("Spiacenti, la lingua che hai inviato non esiste."),
                parse_mode=ParseMode.HTML
            )
            await query.answer(show_alert=False, text="✅")
            update_richieste_status(3, args[3])
            await context.bot.unpin_chat_message(chat_id=-1001198344093, message_id=query.message.message_id)
        elif args[0] == "langRifiutatoExist":
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="{} \n\n#rifiutato ALREADY_EXIST by @{}".format(str(query.message.text), str(query.from_user.username)),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
            )
            set_msg_lang(args[4])
            await context.bot.send_message(
                chat_id=args[1],
                text=_("Siamo spiacenti, risultando già presente nell'Atlante Linguistico, la tua richiesta di inserimento della lingua {langName} non può essere soddisfatta.").format(langName=args[2]),
                parse_mode=ParseMode.HTML
            )
            await query.answer(show_alert=False, text="✅")
            update_richieste_status(3, args[3])
            await context.bot.unpin_chat_message(chat_id=-1001198344093, message_id=query.message.message_id)
        elif args[0] == "langRifiutatoLink":
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="{} \n\n#rifiutato LINK_ERROR by @{}".format(str(query.message.text), str(query.from_user.username)),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
            )
            set_msg_lang(args[4])
            await context.bot.send_message(
                chat_id=args[1],
                text=_("Siamo spiacenti, hai fornito un link errato. Ricorda: l'inserimento di una lingua nell'Atlante prevede un link ad progetto presente nella piattaforma https://translations.telegram.org\nInvia una nuova richiesta con le informazioni corrette."),
                parse_mode=ParseMode.HTML
            )
            await query.answer(show_alert=False, text="✅")
            update_richieste_status(3, args[3])
            await context.bot.unpin_chat_message(chat_id=-1001198344093, message_id=query.message.message_id)
        elif args[0] == "askLang":
            if query.message.chat.type == "private":
                keyboard_confirm = InlineKeyboardMarkup([
                    [InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"), InlineKeyboardButton(_("Procedi ▶️"), callback_data="okAskLang")]
                ])
                await context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id,
                    text=_("Con questa procedura potrai richiedere l'inserimento di una lingua all'Atlante.\n\nLa richiesta verrà visionata dai nostri moderatori, in seguito ti sarà fornito un riscontro sull'avanzamento della proposta, ti chiediamo di pazientare."),
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard_confirm
                )
                await query.answer(show_alert=False, text="✅")
            else:
                await query.answer(show_alert=True, text=_("🚫 Siamo spiacenti, è possibile richiedere l'aggiunta di nuove lingue soltanto tramite la chat privata con il bot."))
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(_("➕ Richiedi lingua"), callback_data="404"), InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]
                ])
                await context.bot.send_message(
                    query.from_user.id,
                    text=_("Salve! Se desideri richiedere l'inserimento di una nuova lingua utilizza questo spazio e la seguente procedura, grazie."),
                    reply_markup=reply_markup
                )
        elif args[0] == "feedback":
            if query.message.chat.type == "private":
                keyboard_confirm = InlineKeyboardMarkup([
                    [InlineKeyboardButton(_("❌ Anulla"), callback_data="cancel")]
                ])
                await context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id,
                    text=_("Inviaci un commento. Il tuo messaggio verrà visionato dagli amministratori dell'Atlante."),
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard_confirm
                )
                await query.answer(show_alert=False, text="✅")
                update_user_status('awaitingFeedback', query.message.chat_id)
            else:
                await query.answer(show_alert=True, text=_("🚫 Siamo spiacenti, è possibile inviare un feedback soltanto tramite la chat privata con il bot."))
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(_("💬 Scrivi un commento"), callback_data="feedback"), InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]
                ])
                await context.bot.send_message(
                    query.from_user.id,
                    text=_("Salve! Se desideri inviare un feedback riguardo l'Atlante premi il tasto sottostante."),
                    reply_markup=reply_markup
                )
        elif args[0] == "cancel":
            update_user_status('action_cancel', query.message.chat_id)
            await query.answer(show_alert=True, text=_("✅ Operazione annullata."))
            keyboard_back= InlineKeyboardMarkup([[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("✅ Operazione annullata."),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard_back
            )
        elif args[0] == "okAskLang":
            update_user_status('askLang', query.message.chat_id)
            keyboard_confirm = InlineKeyboardMarkup([[InlineKeyboardButton(_("❌ Anulla"), callback_data="cancel")]])
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("Ottimo!\nScrivi il nome della <b>lingua</b> che vorresti fosse aggiunta."),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard_confirm
            )
            await query.answer(show_alert=False, text="✅")
        elif args[0] == "setBotLang":
            setBotLang(args[1], query.message.chat_id)
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("Lingua del Bot cambiata. Premi su /start per applicare le modifiche."),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
            )
            await query.answer(show_alert=False, text="✅")
        elif args[0] == "linguaALT":
            itSelected = ""
            enSelected = ""
            furSelected = ""
            vecSelected = ""
            catSelected = ""
            esSelected = ""
            
            if getBotLang(query.message.chat_id) == "it":
                itSelected = "☑️"
            elif getBotLang(query.message.chat_id) == "fur":
                furSelected = "☑️"
            elif getBotLang(query.message.chat_id) == "vec":
                vecSelected = "☑️"
            elif getBotLang(query.message.chat_id) == "es":
                esSelected = "☑️"
            elif getBotLang(query.message.chat_id) == "cat":
                catSelected = "☑️"
            else:
                enSelected = "☑️"

            keyboard_lingualt= InlineKeyboardMarkup([
                [InlineKeyboardButton("Català {}".format(catSelected), callback_data="setBotLang_cat"), InlineKeyboardButton("English {}".format(enSelected), callback_data="setBotLang_en")],
                [InlineKeyboardButton("Español {}".format(esSelected), callback_data="setBotLang_es"), InlineKeyboardButton("Furlan {}".format(furSelected), callback_data="setBotLang_fur")],
                [InlineKeyboardButton("Italiano {}".format(itSelected), callback_data="setBotLang_it"), InlineKeyboardButton("Veneto {}".format(vecSelected), callback_data="setBotLang_vec")],
                [InlineKeyboardButton(_("🌐 Traduci bot"), url="https://www.transifex.com/codaze-veneto/telegram-linguistic-atlas/"), InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]
            ])
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("Seleziona la lingua del bot. \n\nSe la lingua che desideri non fosse presente nell'elenco seguente, richiedila iscrivendoti su <a href='https://www.transifex.com/codaze-veneto/telegram-linguistic-atlas/'>Transifex</a> e aiutaci a svilupparla. 👍🏻\n\nNel caso dovessi riscontrare qualche difficoltà non esitare ad utilizzare il modulo di feedback."),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard_lingualt
            )
            await query.answer(show_alert=False, text="✅")
        elif args[0] == "credits":
            keyboard_lingualt= InlineKeyboardMarkup([
                [InlineKeyboardButton(_("📝 Disclaimer"), callback_data="funzCat")],
                [InlineKeyboardButton(_("👥 Riconoscimenti"), callback_data="talksUs")],
                [InlineKeyboardButton(_("⚒ Codice sorgente"), url="https://github.com/garboh/langAtlasBot")],
                [InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]
            ])
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("L'<b>Atlante Linguistico</b> ospita e punta a diffondere tutte le possibili localizzazioni linguistiche di Telegram, offrendo funzioni avanzate di ricerca e applicazione.\n\nL'Atlante nasce dall'idea e dalla progettazione di <a href='https://t.me/cmpfrc'>Federico</a>, e dal supporto degli altri collaboratori di <a href='https://t.me/LenguaVeneta'>Còdaze Veneto</a>, ente che si occupa della localizzazione e diffusione di prodotti in lingua veneta.\n@langAtlasBot, il bot che ospita l'Atlante, è stato sviluppato in <a href='https://it.wikipedia.org/wiki/Python'>python</a> e viene mantenuto da <a href='https://t.me/garboh'>Francesco</a>, tecnico informatico, junior developer e studente dell'UniPD in Ing. Informatica.\n\nUtilizza il modulo di feedback per eventuali apprezzamenti, suggerimenti, proposte, o se vuoi supportare in qualche modo il progetto. Grazie di aver mostrato interesse per l'Atlante! 😉"),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard_lingualt
            )
            await query.answer(show_alert=False, text="✅")
        elif args[0] == "funzCat":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"), InlineKeyboardButton(_("️️◀️ Indietro"), callback_data="credits")]
            ])
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("📝 <b>Disclaimer</b>\n\nI dati inseriti nell'Atlante e riguardanti l'organizzazione politica delle lingue, sono stati raccolti dalle pagine delle WIkipedia italiana ed inglese. In caso errori o dati mancanti si prega di comunicarlo tramite il modulo di feedback.\n\nLe lingue inserite nell'Atlante richiedono uno standard minimo di completezza e qualità. Si richiede che siano completi almeno 2 client e che possibilmente ci sia volontà di completamento e aggiornamento dell'intero progetto di traduzione. Come una lingua può facilmente essere aggiunta potrà altrettanto facilmente essere rimossa. Grazie della comprensione."),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            await query.answer(show_alert=False, text="✅")
        elif args[0] == "talksUs":
            keyboard_lingualt= InlineKeyboardMarkup([
                [InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"), InlineKeyboardButton(_("️️◀️ Indietro"), callback_data="credits")]
            ])
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("In questa sezione sono elencati i riferimenti a siti, giornali, agenzie di stampa e a qualsiasi altro media che si è occupato o ha diffuso il nostro progetto:\n\n➖ l'<a href='https://arlef.it/en/'>ARLeF</a> ha presentato l'Atlante durante la <b>conferenza stampa regionale</b> sulla localizzazione di Telegram in Friulano."),
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard_lingualt
            )
            await query.answer(show_alert=False, text="✅")
        elif args[0] == "orderPolitica":
            keyboard_continenti= InlineKeyboardMarkup([
                [InlineKeyboardButton(_("America settentrionale"), callback_data="orderCont_1")],
                [InlineKeyboardButton(_("America meridionale"), callback_data="orderCont_2")],
                [InlineKeyboardButton(_("Europa"), callback_data="orderCont_3")],
                [InlineKeyboardButton(_("Africa"), callback_data="orderCont_4")],
                [InlineKeyboardButton(_("Asia"), callback_data="orderCont_5")],
                [InlineKeyboardButton(_("Oceania"), callback_data="orderCont_6")],
                [InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]
            ])
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("Hai scelto di proseguire tramite la <b>organizzazione politica</b>! <a href='https://atlasbot.garbo.tech/img/imgbot/planisfero_colorato.jpg'>🌍</a>\n\nSeleziona il continente che vuoi esplorare."),
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard_continenti
            )
            await query.answer(show_alert=False, text="✅")
        elif args[0] == "orderCont":
            offset = 0
            if len(args) == 3:
                offset = args[2]
            
            varContinentName = "continetName"
            if getBotLang(query.message.chat_id) == "it":
                varContinentName = "continetName"
            elif getBotLang(query.message.chat_id) == "fur":
                varContinentName = "continetName_fur"
            elif getBotLang(query.message.chat_id) == "vec":
                varContinentName = "continetName_vec"
            elif getBotLang(query.message.chat_id) == "es":
                varContinentName = "continetName_es"
            elif getBotLang(query.message.chat_id) == "cat":
                varContinentName = "continetName_cat"
            else:
                varContinentName = "continetName_en"
                
            row = get_continent_name_and_img(varContinentName, args[1])
            continentName = row[0]
            imgContinent = row[1]
            keyboard_stati = getState(query, args[1], offset)
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("Ottimo, hai selezionato l'<b>{continent}</b>! <a href='{linkToContinentIMG}'>🌍</a> \n\nOra seleziona lo Stato che vuoi visitare.").format(continent=continentName, linkToContinentIMG=imgContinent),
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard_stati
            )
            await query.answer(show_alert=False, text="✅")
        elif args[0] == "orderState":
            varCountryName = "countryName_en"
            if getBotLang(query.message.chat_id) == "it":
                varCountryName = "countryName"
            elif getBotLang(query.message.chat_id) == "fur":
                varCountryName = "countryName_fur"
            elif getBotLang(query.message.chat_id) == "vec":
                varCountryName = "countryName_vec"
            elif getBotLang(query.message.chat_id) == "es":
                varCountryName = "countryName_es"
            elif getBotLang(query.message.chat_id) == "cat":
                varCountryName = "countryName_cat"

            row = get_country_name_and_img(varCountryName, args[1])
            countryName = row[0]
            imgCountry = row[1]
            keyboard_lang = getLang(query, args[1], 0)
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("Ecco le lingue attualmente presenti nello Stato: <b>{state}</b>! <a href='{linkToStateIMG}'>🌍</a>\n\nSeleziona la lingua che preferisci per accedere alla sua scheda e vedere le opzioni disponibili.\n\nNel caso non sia presente in questo elenco, prima di richiedere la lingua che cerchi, prova a visitare altri Stati o ad utilizzare la catalogazione alfabetica.").format(state=countryName, linkToStateIMG=imgCountry),
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard_lang
            )
            await query.answer(show_alert=False, text="✅")
        elif args[0] == "lang":
            
            varDialectName = "name"
            if getBotLang(query.message.chat_id) == "it":
                varDialectName = "name"
            elif getBotLang(query.message.chat_id) == "fur":
                varDialectName = "name_fur"
            elif getBotLang(query.message.chat_id) == "vec":
                varDialectName = "name_vec"
            elif getBotLang(query.message.chat_id) == "es":
                varDialectName = "name_es"
            elif getBotLang(query.message.chat_id) == "cat":
                varDialectName = "name_cat"
            else:
                varDialectName = "name_en"
            
            row = get_lang_name_and_flag(varDialectName, args[1])
            if not row:
                row = get_custom_lang_name_and_flag(varDialectName, args[1])
            nome = row[0]
            flag = row[1]
            
            test = "404"
            if args[2] == "oc":
                test = "orderChar"
            if args[2] == "os":
                test = "orderState"

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"), InlineKeyboardButton(_("◀️ Indietro"), callback_data="{}_{}_1".format(test, args[3]))]
            ])
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=_("Per installare la lingua {langName} su Telegram clicca sul seguente link.\n\n<a href='{linkToLangIMG}'>👉🏻</a> https://t.me/setlanguage/{langCode}\n\nRicorda: potrai sempre tornare alla lingua iniziale tramite le impostazioni native dell'app.").format(langName=nome, linkToLangIMG=flag, langCode=args[1]),
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            await query.answer(show_alert=False, text="✅")
        elif args[0] == "orderChar":
            
            varDialectName = "name"
            if getBotLang(query.message.chat_id) == "it":
                varDialectName = "name"
            elif getBotLang(query.message.chat_id) == "fur":
                varDialectName = "name_fur"
            elif getBotLang(query.message.chat_id) == "vec":
                varDialectName = "name_vec"
            elif getBotLang(query.message.chat_id) == "es":
                varDialectName = "name_es"
            elif getBotLang(query.message.chat_id) == "cat":
                varDialectName = "name_cat"
            else:
                varDialectName = "name_en"
            
            rows = get_languages_by_initial(varDialectName, args[1])
            arrays_Lang=[]
            arrays_Lang.append([])
            lenLan = len(arrays_Lang)
            count = 0
            for lang in rows:
                count+= 1
                if count % 2 == 0:
                    arrays_Lang[-1].append(InlineKeyboardButton("{}".format(lang[0]), callback_data="lang_{}_oc_{}".format(lang[2], args[1])))
                else:
                    arrays_Lang.append([])
                    arrays_Lang[-1].append(InlineKeyboardButton("{}".format(lang[0]), callback_data="lang_{}_oc_{}".format(lang[2], args[1])))
            
            arrays_Lang.append([])
            arrays_Lang[-1].append(InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"))
            arrays_Lang[-1].append(InlineKeyboardButton(_("◀️ Indietro"), callback_data="orderAlpha"))
            keyBoard = InlineKeyboardMarkup(arrays_Lang)
            
            s = __("È presente <b>{count}</b> lingua che inizia per <b>{char}</b>!\n\nNel caso non sia presente in questo elenco, prima di richiedere la lingua che cerchi, assicurati che la lettera scelta sia corretta o prova ad utilizzare la catalogazione politica.", "Sono presenti <b>{count}</b> lingue che iniziano per <b>{char}</b>!\n\nNel caso non sia presente in questo elenco, prima di richiedere la lingua che cerchi, assicurati che la lettera scelta sia corretta o prova ad utilizzare la catalogazione politica.", count)
            testo = s.format(count=count, char=args[1])
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=testo,
                parse_mode=ParseMode.HTML,
                reply_markup=keyBoard
            )
            await query.answer(show_alert=False, text="✅")
    except IndexError as e:
        logger.error("IndexError: %s", e)
        await query.answer(show_alert=True, text=_("Errore nei parametri del callback. Si prega di riprovare."))
    except Exception as e:
        logger.error("Errore generico: %s", e)
        await query.answer(show_alert=True, text=_("Si è verificato un errore. Si prega di riprovare più tardi."))
    finally:
        closeDb()

async def cancel_handler(update: Update, context: CallbackContext) -> None:
    await context.bot.send_message(update.message.chat_id, 'Bye! I hope we can talk again some day.')

async def getid_handler(update: Update, context: CallbackContext) -> None:
    await context.bot.send_message(update.message.chat_id, f'Your ID is {update.message.from_user.id}')

async def testo_handler(update: Update, context: CallbackContext) -> None:
    await context.bot.send_message(update.message.chat_id, 'Received your text message!')

async def photo_handler(update: Update, context: CallbackContext) -> None:
    await context.bot.send_message(update.message.chat_id, 'Nice photo!')

async def error_handler(update: Update, context: CallbackContext, error: Exception) -> None:
    logger.warning('Update "%s" caused error "%s"', update, error)
    try:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
        await context.bot.send_message(chat_id=update.message.chat_id, reply_markup=keyboard, text=_("❌ Si è verificato un errore. Riprova più tardi. \n\nGli amministratori del bot sono già stati avvisati dell'intoppo. Se il problema persiste non esitare ad utilizzare il modulo di feedback, grazie. 📬"))
        await context.bot.send_message(chat_id=-1001198344093, text=f'Update "{update}" caused error "{error}"')
        openDb()
        update_user_status('action_cancel', update.message.from_user.id)
        closeDb()
    except Exception as e:
        logger.error("Error handling another error: %s", e)

async def inline_query_handler(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    results = []
    # Handle the inline query
    await update.inline_query.answer(results)

async def inline_mode_handler(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query.strip()
    user_id = update.inline_query.from_user.id

    try:
        openDb()
        langBot = getBotLang(user_id)
        setBotLang(langBot, user_id)

        results = []
        rowAll = search_languages(query, langBot)

        if rowAll:
            for lang in rowAll:
                results.append(InlineQueryResultArticle(
                    id=str(uuid4()),  # Genera un ID unico per ogni risultato
                    title=_("Applica la lingua {langName} su Telegram!").format(langName=lang[1]),
                    input_message_content=InputTextMessageContent(
                        _("Hai selezionato la lingua {langName}.").format(langName=lang[1])
                    ),
                    thumbnail_url=lang[2],  # URL della miniatura dell'immagine
                    description=_("Seleziona questa lingua per cambiare la lingua dell'interfaccia.")
                ))
        else:
            results.append(InlineQueryResultArticle(
                id=str(uuid4()),
                title=_("Non è stata trovata alcuna lingua."),
                input_message_content=InputTextMessageContent(
                    _("❌ Non è stata trovata alcuna lingua.")
                ),
                description=_("Nessun risultato trovato.")
            ))

        await update.inline_query.answer(results)
    except Exception as e:
        logger.error("Errore durante la gestione della query inline: %s", e)
    finally:
        closeDb()
