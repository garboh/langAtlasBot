#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telegram import *
from telegram.ext import *
from telegram.ext.dispatcher import run_async
import logging
import platform
if not platform.python_version().startswith('3'):
    print("Python Version: "+platform.python_version())
    print("Incompatible version of python! Python 3 is required")
    exit()
print("Vython Version: "+platform.python_version())
print("Starting langAtlasBot...")

import MySQLdb
import datetime
from datetime import timedelta
import random
import time
import gettext
from gettext import ngettext

import subprocess
import sys

from time import sleep
from uuid import uuid4
from telegram.utils.helpers import escape_markdown

msg_id = None

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


en = gettext.translation('langAtlasBot', localedir='locale', languages=['en'])
it = gettext.translation('langAtlasBot', localedir='locale', languages=['it'])
es = gettext.translation('langAtlasBot', localedir='locale', languages=['es'])
cat = gettext.translation('langAtlasBot', localedir='locale', languages=['cat'])
fur = gettext.translation('langAtlasBot', localedir='locale', languages=['fur'])
vec = gettext.translation('langAtlasBot', localedir='locale', languages=['vec'])


# xgettext -d langAtlasBot -o langAtlasBot.pot main.py



def openDb():
    global db
    global cur

    db = MySQLdb.connect(host="",      # your host, usually localhost
                         user="",           # your username
                         passwd="#",  # your password
                         db="",         # name of the data base
                         charset='utf8mb4',
                         use_unicode=True)
    cur = db.cursor()
    
def getBotLang(chat=0):
    cur.execute("SELECT `lang` FROM `user` WHERE `id`={}".format(chat))
    row = cur.fetchone()
    if row:
        return row[0]
    else:
        return None

def setBotLang(lang, chat):
    global _
    global __
    if lang == 'it':
        _ = it.gettext
        __ = it.ngettext
    elif lang == 'es':
        _ = es.gettext
        __ = es.ngettext
    elif lang == 'cat':
        _ = cat.gettext
        __ = cat.ngettext
    elif lang == 'fur':
        _ = fur.gettext
        __ = fur.ngettext
    elif lang == 'vec':
        _ = vec.gettext
        __ = vec.ngettext
    else:
        _ = en.gettext
        __ = en.ngettext
       
    cur.execute("UPDATE `user` SET `lang`='{}' WHERE `id`={}".format(lang, chat))

def setMsgLang(lang):
    global _
    global __
    if lang == 'it':
        _ = it.gettext
        __ = it.ngettext
    elif lang == 'es':
        __ = es.ngettext
        _ = es.gettext
    elif lang == 'cat':
        __ = cat.ngettext
        _ = cat.gettext
    elif lang == 'fur':
        __ = fur.ngettext
        _ = fur.gettext
    elif lang == 'vec':
        __ = vec.ngettext
        _ = vec.gettext

    else:
        __ = en.ngettext
        _ = en.gettext

def init(bot, update, message):
    openDb()
    cur.execute("SELECT * FROM `user` WHERE `id`={}".format(int(message.chat_id)))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO `user` (`id`, `status`, `lang`) VALUES ({}, 'new_user', '{}')".format(int(message.chat_id), message.from_user.language_code))
        langBot = getBotLang(update.message.chat_id)
        setBotLang(langBot, update.message.chat_id)
        end()
        return True
    else:
        langBot = getBotLang(update.message.chat_id)
        setBotLang(langBot, update.message.chat_id)
        stato = row[1]
        args = stato.split('_')
        if args[0] == "askLang":
            try:
                bot.editMessageText(chat_id=update.message.chat_id, message_id=(update.message.message_id - 1), text=_("Nome lingua: <b>{langName}</b>").format(langName=update.message.text), parse_mode=ParseMode.HTML)
            except:
                pass
            cur.execute("INSERT INTO `richieste`(`idChat`, `name`) VALUES ({},\"{}\")".format(update.message.from_user.id, MySQLdb.escape_string(update.message.text).decode('UTF-8')))
            idRichiesta = db.insert_id()
            keyboard_confirm = InlineKeyboardMarkup([[InlineKeyboardButton(_("❌ Anulla"), callback_data="cancel")]])
            bot.sendMessage(update.message.chat_id, text = _("Ottimo!\nOra invia il link associato alla lingua che vorresti fosse aggiunta. Ricorda che il link deve corrispondere ad un progetto presente nella piattaforma https://translations.telegram.org e deve avere un formato simile al seguente: https://t.me/setlanguage/<i>language_user_name</i>"), parse_mode=ParseMode.HTML, reply_markup=keyboard_confirm)
            cur.execute("UPDATE `user` SET `status`='awaitingLink_{}' WHERE `id`='{}'".format(idRichiesta, update.message.from_user.id))
            end()
            return False
        elif args[0] == "awaitingLink":
            if (update.message.text).startswith("https://t.me/setlanguage/"):
                try:
                    bot.editMessageText(chat_id=update.message.chat_id, message_id=(update.message.message_id - 1), text=_("Link: <b>{link}</b>").format(link=update.message.text), parse_mode=ParseMode.HTML)
                except:
                    pass
                keyboard_confirm = InlineKeyboardMarkup([[InlineKeyboardButton(_("❌ Anulla"), callback_data="cancel")]])
                bot.sendMessage(update.message.chat_id, text = _("Grazie!\n\nAllega ora il nome degli Stati, separati da virgola, nei quali questa la lingua possiede uno status di ufficialità o di riconoscimento.\n\nEsempio: Italia, Brasile, Spagna, ..."), parse_mode=ParseMode.HTML, reply_markup=keyboard_confirm)
                cur.execute("UPDATE `user` SET `status`='awaitingStati_{}' WHERE `id`='{}'".format(args[1], update.message.from_user.id))
                cur.execute("UPDATE `richieste` SET `link`=\"{}\" WHERE `idRichiesta`={}".format(MySQLdb.escape_string(update.message.text).decode('UTF-8'), args[1]))
                end()
            else:
                bot.sendMessage(update.message.chat_id, text = _("Link non valido. Il formato del link dev'essere così composto: https://t.me/setlanguage/language_user_name\n\nPuoi copiare il link corretto nella pagina della lingua che stai chiedendo sulla piattaforma https://translations.telegram.org sotto la voce \"Sharing Link\"."),parse_mode=ParseMode.HTML )
            return False
        elif args[0] == "awaitingStati":
            try:
                bot.editMessageText(chat_id=update.message.chat_id, message_id=(update.message.message_id - 1), text=_("Stati: <b>{states}</b>").format(states=update.message.text), parse_mode=ParseMode.HTML)
            except:
                pass
            keyboard_confirm = InlineKeyboardMarkup([[InlineKeyboardButton(_("❌ Anulla"), callback_data="cancel")]])
            bot.sendMessage(update.message.chat_id, text = _("Grazie. Abbiamo quasi finito!\n\nRiporta il codice linguistico <a href='https://en.m.wikipedia.org/wiki/List_of_ISO_639-3_codes'>ISO_639-3</a> collegato alla tua lingua. Se non possiedi questa informazione premi sul link appena fornito per recuperarla."), parse_mode=ParseMode.HTML, reply_markup=keyboard_confirm)
            cur.execute("UPDATE `user` SET `status`='awaitingISO_{}' WHERE `id`='{}'".format(args[1], update.message.from_user.id))
            cur.execute("UPDATE `richieste` SET `stati`=\"{}\" WHERE `idRichiesta`={}".format(MySQLdb.escape_string(update.message.text).decode('UTF-8'), args[1]))
            end()
            return False
        elif args[0] == "awaitingISO":
            isoCode = MySQLdb.escape_string(update.message.text).decode('UTF-8')
            cur.execute("UPDATE richieste SET isoCode=\"{}\", stato=1 WHERE idRichiesta={}".format(isoCode, int(args[1])))
            try:
                bot.editMessageText(chat_id=update.message.chat_id, message_id=(update.message.message_id - 1), text="ISO: {}".format(str(update.message.text)), parse_mode=ParseMode.HTML)
            except:
                pass
            keyboard_confirm = InlineKeyboardMarkup([[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
            cur.execute("UPDATE `user` SET `status`='langRecived' WHERE `id`='{}'".format(update.message.from_user.id))
            bot.sendMessage(update.message.chat_id, text = _("✅ Proposta inoltrata con successo!\n\nVisto il gran numero di richieste che riceviamo ti chiediamo di pazientare qualche giorno. Presto riceverai un riscontro sull'andamento della tua richiesta.\n\nSe la lingua proposta non avesse ancora i requisiti minimi, approfittane per cercare di completarla."), parse_mode=ParseMode.HTML, reply_markup=keyboard_confirm)
            cur.execute("SELECT * FROM richieste WHERE idRichiesta={}".format(args[1]))
            row = cur.fetchone()
            nomeLingua = row[2]
            link = row[3]
            stati = row[4]
            lastName = "NULL"
            username = "NULL"
            if update.message.from_user.last_name:
                lastName = update.message.from_user.last_name
            if update.message.from_user.username:
                username = "@{}".format(update.message.from_user.username)
            
            cur.execute("SELECT lang FROM user WHERE id={}".format(update.message.from_user.id))
            rowUser = cur.fetchone()
            langUser = rowUser[0]
            
            keyboard_confirm = InlineKeyboardMarkup([[InlineKeyboardButton("Inserito ✅", callback_data="langAdded_{}_{}_{}_{}".format(update.message.from_user.id, nomeLingua, args[1], langUser)), InlineKeyboardButton("Rifiutato ❌", callback_data="langRifiutato_{}_{}_{}_{}".format(update.message.from_user.id, nomeLingua, args[1], langUser))], [InlineKeyboardButton("ISO Err ❌", callback_data="langRifiutatoISO_{}_{}_{}_{}".format(update.message.from_user.id, nomeLingua, args[1], langUser)), InlineKeyboardButton("Link Err ❌", callback_data="langRifiutatoLink_{}_{}_{}_{}".format(update.message.from_user.id, nomeLingua, args[1], langUser)), InlineKeyboardButton("Esiste già ❌", callback_data="langRifiutatoExist_{}_{}_{}_{}".format(update.message.from_user.id, nomeLingua, args[1], langUser))]])
            idMsg = bot.sendMessage(chat_id=-1001198344093, text = "🌐 Nuova lingua: \n\nNome: {}\nCognome: {}\nUsername: {}\n<code>{}</code> #id{}\n\nNome Lingua: {}\nLink: {}\nStati: {}\nID: <code>{}</code> \nCodice ISO: {}".format(update.message.from_user.first_name, lastName, username, update.message.from_user.id, update.message.from_user.id, nomeLingua, link, stati, args[1], update.message.text), parse_mode=ParseMode.HTML, reply_markup=keyboard_confirm)
            bot.pin_chat_message(chat_id=-1001198344093, message_id=idMsg.message_id, disable_notification=True)
            end()
            return False
        elif args[0] == "awaitingFeedback":
            try:
                bot.editMessageText(chat_id=update.message.chat_id, message_id=(update.message.message_id - 1), text=_("Inviaci un commento. Il tuo messaggio verrà visionato dagli amministratori dell'Atlante.").format(update.message.text), parse_mode=ParseMode.HTML)
            except:
                pass
            keyboard_confirm = InlineKeyboardMarkup([[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
            bot.sendMessage(update.message.chat_id, text = _("✅ Commento inoltrato!"), parse_mode=ParseMode.HTML, reply_markup=keyboard_confirm)
            cur.execute("UPDATE `user` SET `status`='feedbak_sent' WHERE `id`='{}'".format(update.message.from_user.id))
            lastName = "NULL"
            username = "NULL"
            if update.message.from_user.last_name:
                lastName = update.message.from_user.last_name
            if update.message.from_user.username:
                username = "@{}".format(update.message.from_user.username)
            
            cur.execute("INSERT INTO `feedback`(`chat_id`, `msg_id`, `status`) VALUES ({},{},'toBeAnswered')".format(update.message.chat_id, update.message.message_id))
            feedbackID = cur.lastrowid
            bot.forwardMessage(chat_id=-1001198344093, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
            
            keyboard_confirm = InlineKeyboardMarkup([[InlineKeyboardButton("Rispondi 📝", callback_data="feedbackAnsw_{}".format(feedbackID))]])
            idMsg = bot.sendMessage(chat_id=-1001198344093, text = "💬 Hai ricevuto un feedback: \n\nNome: {}\nCognome: {}\nUsername: {}\n<code>{}</code> #id{}\n\n#FeedBack{} ".format(update.message.from_user.first_name, lastName, username, update.message.from_user.id, update.message.from_user.id, feedbackID), parse_mode=ParseMode.HTML, reply_markup=keyboard_confirm)
            
            
            cur.execute("UPDATE `feedback` SET `adminMsgID`='{}' WHERE `idFeed`='{}'".format(idMsg.message_id, feedbackID))
            
            bot.pin_chat_message(chat_id=-1001198344093, message_id=idMsg.message_id, disable_notification=True)
            end()

            return False
        
        elif args[0] == "answeringFeedback":
            if update.message.chat.type == "private":
                if update.message.text == "Anulla":
                    cur.execute("UPDATE `user` SET `status`='cancel' WHERE `id`='{}'".format(update.message.chat_id))
                    bot.sendMessage(chat_id=update.from_user.id, text="Ok, annullato", parse_mode=ParseMode.HTML)
                    cur.execute("UPDATE `feedback` SET `status`='toBeAnswered' WHERE `idFeed`='{}'".format(args[1]))
                else:
                    cur.execute("UPDATE `user` SET `status`='confirmAnswer_{}' WHERE `id`='{}'".format(args[1], update.message.chat_id))
                    bot.sendMessage(chat_id=update.message.chat_id, text="Perefetto, scrivi \"Conferma\" per inviare la risposta o invia di nuovo il messaggio se vuoi modificarlo.", parse_mode=ParseMode.HTML)
                    cur.execute("UPDATE `feedback` SET `risposta`='{}' WHERE `idFeed`='{}'".format(update.message.text, args[1]))
        elif args[0] == "confirmAnswer":
            if update.message.chat.type == "private":
                if update.message.text == "Anulla":
                    cur.execute("UPDATE `user` SET `status`='cancel' WHERE `id`='{}'".format(update.message.chat_id))
                    bot.sendMessage(chat_id=update.from_user.id, text="Ok, annullato", parse_mode=ParseMode.HTML)
                    cur.execute("UPDATE `feedback` SET `status`='toBeAnswered' WHERE `idFeed`='{}'".format(args[1]))
                elif update.message.text == "Conferma" or update.message.text == "conferma":
                    cur.execute("UPDATE `user` SET `status`='feedAnswered' WHERE `id`='{}'".format(update.message.chat_id))
                    cur.execute("UPDATE `feedback` SET `status`='answered' WHERE `idFeed`='{}'".format(args[1]))
                    bot.sendMessage(chat_id=update.message.chat_id, text="Risposta inviata", parse_mode=ParseMode.HTML)
                    cur.execute("SELECT * FROM `feedback` WHERE `idFeed`='{}'".format(args[1]))
                    rigaFeed = cur.fetchone()
                    feedChatID = rigaFeed[1]
                    feedmsgID = rigaFeed[2]
                    feedText = rigaFeed[4]
                    feedAdminMsgID = rigaFeed[5]
                    bot.sendMessage(chat_id=feedChatID, text=feedText, parse_mode=ParseMode.HTML, reply_to_message_id=feedmsgID)
                    bot.unpin_chat_message(chat_id=-1001198344093, message_id=feedAdminMsgID)
                    bot.editMessageText(chat_id=-1001198344093,  message_id=feedAdminMsgID, text="<i>{}</i> \n\n#risposta by @{}".format(str(feedText), str(update.message.from_user.username)), disable_web_page_preview=True, parse_mode=ParseMode.HTML)
                else:
                    bot.sendMessage(chat_id=update.message.chat_id, text="Perefetto, scrivi \"Conferma\" per inviare la risposta o invia di nuovo il messaggio se vuoi modificarlo.", parse_mode=ParseMode.HTML)
                    cur.execute("UPDATE `feedback` SET `risposta`=\"{}\" WHERE `idFeed`='{}'".format(MySQLdb.escape_string(update.message.text).decode('UTF-8'), args[1]))
    return True

def end():
    db.commit()
    db.close()


def start(bot, update):
    if init(bot, update, update.message):
        bot.sendMessage(update.message.chat_id, text = _("<b>Benvenuto nell'Atlante linguistico di Telegram.</b>\n\nTramite questo bot potrai:\n👉🏻 navigare tra lingue presenti, organizzate alfabeticamente e politicamente\n👉🏻 accedere alle schede delle lingue desiderate ed installarle su Telegram\n👉🏻 richiedere l'aggiunta di una lingua all'Atlante o fornirci un feedback\n👉🏻 cambiare lingua al bot"), parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("1️⃣ Catalogazione alfabetica"), callback_data="orderAlpha")],[InlineKeyboardButton(_("2️⃣ Catalogazione politica"), callback_data="orderPolitica")],[InlineKeyboardButton(_("➕ Richiedi lingua"), callback_data="askLang"),InlineKeyboardButton(_("💬 Feedback"), callback_data="feedback")],[InlineKeyboardButton(_("🗣 Lingua Bot"), callback_data="linguaALT"), InlineKeyboardButton(_("ℹ️ Info"), callback_data="credits")]]))



def getKeyBoard(bot, update):
    cur.execute("SELECT * FROM `lang`")
    rowL = cur.fetchall()
    if rowL:
        array_Lang=[]
        array_Lang.append([])
        lenLan = len(array_Lang)
        count = 0
        for lang in rowL:
            count+= 1
            if count % 2 == 0:
                array_Lang[-1].append(InlineKeyboardButton("{}".format(lang[1]), callback_data="lang_{}".format(lang[0])))
            else:
                array_Lang.append([])
                array_Lang[-1].append(InlineKeyboardButton("{}".format(lang[1]), callback_data="lang_{}".format(lang[0])))
            
    keyBoard = InlineKeyboardMarkup(array_Lang)
    return keyBoard
    
  
def getid(bot, update):
    bot.sendMessage(update.message.chat_id, text = update.message.chat_id)

def testo(bot, update):
    if init(bot, update, update.message):
        end()
        
def photo(bot, update):
    if init(bot, update, update.message):
        end()

def cancel(bot, update):
    if init(bot, update, update.message):
        cur.execute("UPDATE `user` SET `status`='action_cancel' WHERE `id`='{}'".format(update.message.from_user.id))
        bot.sendMessage(update.message.chat_id, text = _("Operazione annullata."), reply_markup=ReplyKeyboardRemove())
        end()
        
def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))
    try:
        keyboard= InlineKeyboardMarkup([[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
        bot.sendMessage(update.message.chat_id, reply_markup = keyboard, text=_("❌ Si è verificato un errore. Riprova più tardi. \n\nGli amministratori del bot sono già stati avvisati dell'intoppo. Se il problema persiste non esitare ad utilizzare il modulo di feedback, grazie. 📬"))
        bot.sendMessage(chat_id=-1001198344093, text='Update "%s" caused error "%s"' % (update, error))
        openDb()
        cur.execute("UPDATE `user` SET `status`='action_cancel' WHERE `id`='{}'".format(update.message.from_user.id))
        end()
    except:
        pass
        
@run_async
def inline_query(bot, update):
    openDb()
    langBot = getBotLang(update.callback_query.message.chat_id)
    setBotLang(langBot, update.callback_query.message.chat_id)
    args = update.callback_query.data.split('_')
    
    if args[0] == "404" or args[0] == "":
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True, text=_("⚠️ Ancora non disponibile"))
    elif args[0] == "orderAlpha":
        keyboard_alfabetica = InlineKeyboardMarkup([[InlineKeyboardButton("A", callback_data="orderChar_A"), InlineKeyboardButton("B", callback_data="orderChar_B"),InlineKeyboardButton("C", callback_data="orderChar_C"),InlineKeyboardButton("D", callback_data="orderChar_D"),InlineKeyboardButton("E", callback_data="orderChar_E"),InlineKeyboardButton("F", callback_data="orderChar_F"),InlineKeyboardButton("G", callback_data="orderChar_G")],[InlineKeyboardButton("H", callback_data="orderChar_H"),InlineKeyboardButton("I", callback_data="orderChar_I"),InlineKeyboardButton("J", callback_data="orderChar_J"),InlineKeyboardButton("K", callback_data="orderChar_K"),InlineKeyboardButton("L", callback_data="orderChar_L"),InlineKeyboardButton("M", callback_data="orderChar_M"),InlineKeyboardButton("N", callback_data="orderChar_N")],[InlineKeyboardButton("O", callback_data="orderChar_O"),InlineKeyboardButton("P", callback_data="orderChar_P"),InlineKeyboardButton("Q", callback_data="orderChar_Q"),InlineKeyboardButton("R", callback_data="orderChar_R"),InlineKeyboardButton("S", callback_data="orderChar_S"),InlineKeyboardButton("T", callback_data="orderChar_T"),InlineKeyboardButton("U", callback_data="orderChar_U")],[InlineKeyboardButton("V", callback_data="orderChar_V"),InlineKeyboardButton("W", callback_data="orderChar_W"),InlineKeyboardButton("X", callback_data="orderChar_X"),InlineKeyboardButton("Y", callback_data="orderChar_Y"),InlineKeyboardButton("Z", callback_data="orderChar_Z")],[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("Hai scelto di proseguire tramite l'<b>organizzazione alfabetica</b>!🔠\n\nSeleziona la prima lettera del nome della lingua che stai cercando."), disable_web_page_preview=True, parse_mode=ParseMode.HTML, reply_markup=keyboard_alfabetica)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
    elif args[0] == "backMenu":
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("<b>Benvenuto nell'Atlante linguistico di Telegram.</b>\n\nTramite questo bot potrai:\n👉🏻 navigare tra lingue presenti, organizzate alfabeticamente e politicamente\n👉🏻 accedere alle schede delle lingue desiderate ed installarle su Telegram\n👉🏻 richiedere l'aggiunta di una lingua all'Atlante o fornirci un feedback\n👉🏻 cambiare lingua al bot"), disable_web_page_preview=True, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_("1️⃣ Catalogazione alfabetica"), callback_data="orderAlpha")],[InlineKeyboardButton(_("2️⃣ Catalogazione politica"), callback_data="orderPolitica")],[InlineKeyboardButton(_("➕ Richiedi lingua"), callback_data="askLang"),InlineKeyboardButton(_("💬 Feedback"), callback_data="feedback")],[InlineKeyboardButton(_("🗣 Lingua Bot"), callback_data="linguaALT"), InlineKeyboardButton(_("ℹ️ Info"), callback_data="credits")]]))
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
    elif args[0] == "feedbackAnsw":
        cur.execute("SELECT status FROM feedback WHERE idFeed='{}'".format(args[1]))
        row = cur.fetchone()
        if row[0] == "toBeAnswered":
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True, text="Ok, controlla in privata")
            cur.execute("UPDATE `user` SET `status`='answeringFeedback_{}' WHERE `id`='{}'".format(args[1], update.callback_query.from_user.id))
            bot.sendMessage(chat_id=update.callback_query.from_user.id, text="Ehy.. inviami la risposta al feedback", parse_mode=ParseMode.HTML)
            cur.execute("UPDATE `feedback` SET `status`='answering' WHERE `idFeed`='{}'".format(args[1]))
        elif row[0] == "answering":
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True, text="⚠️ Qualcuno sta già rispondendo")
        else:
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True, text="❌ Qualcosa è andato storto...")
    elif args[0] == "langAdded":
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text="{} \n\n#inserito by @{}".format(str(update.callback_query.message.text), str(update.callback_query.from_user.username)), disable_web_page_preview=True, parse_mode=ParseMode.HTML)
        setMsgLang(args[4])
        bot.sendMessage(chat_id=args[1], text=_("Ottime notizie! La tua richiesta di inserimento della lingua {langName} nell'Atlante Linguistico è stata accettata! 👌🏻\n\nOra, con la modalità INLINE del bot @langAtlastBot, potrai condividere nelle chat la lingua che hai richiesto. 👌🏻").format(langName=args[2]), parse_mode=ParseMode.HTML)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
        cur.execute("UPDATE `richieste` SET `stato`='2' WHERE `idRichiesta`='{}'".format(args[3]))
        bot.unpin_chat_message(chat_id=-1001198344093, message_id=update.callback_query.message.message_id)
        subprocess.check_call([sys.executable, "sendms.py", "{}".format(args[3])])
    elif args[0] == "langRifiutato":
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text="{} \n\n#rifiutato by @{}".format(str(update.callback_query.message.text), str(update.callback_query.from_user.username)), disable_web_page_preview=True, parse_mode=ParseMode.HTML)
        setMsgLang(args[4])
        bot.sendMessage(chat_id=args[1], text=_("Siamo spiacenti, la tua richiesta di inserimento della lingua {langName} nell'Atlante Linguistico è stata rifiutata. <b>Per ora</b> non possiede i requisiti di qualità e completezza necessari al suo inserimento. 🖐🏻").format(langName=args[2]), parse_mode=ParseMode.HTML)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
        cur.execute("UPDATE `richieste` SET `stato`='3' WHERE `idRichiesta`='{}'".format(args[3]))
        bot.unpin_chat_message(chat_id=-1001198344093, message_id=update.callback_query.message.message_id)
    elif args[0] == "langRifiutatoISO":
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text="{} \n\n#rifiutato ISO_ERROR by @{}".format(str(update.callback_query.message.text), str(update.callback_query.from_user.username)), disable_web_page_preview=True, parse_mode=ParseMode.HTML)
        setMsgLang(args[4])
        bot.sendMessage(chat_id=args[1], text=_("Siamo spiacenti, il codice ISO fornito non è corretto. Invia una nuova richiesta con le informazioni corrette."), parse_mode=ParseMode.HTML)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
        cur.execute("UPDATE `richieste` SET `stato`='3' WHERE `idRichiesta`='{}'".format(args[3]))
        bot.unpin_chat_message(chat_id=-1001198344093, message_id=update.callback_query.message.message_id)
    elif args[0] == "langRifiutatoExist":
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text="{} \n\n#rifiutato ALREADY_EXIST by @{}".format(str(update.callback_query.message.text), str(update.callback_query.from_user.username)), disable_web_page_preview=True, parse_mode=ParseMode.HTML)
        setMsgLang(args[4])
        bot.sendMessage(chat_id=args[1], text=_("Siamo spiacenti, risultando già presente nell'Atlante Linguistico, la tua richiesta di inserimento della lingua {langName} non può essere soddisfatta.").format(langName=args[2]), parse_mode=ParseMode.HTML)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
        cur.execute("UPDATE `richieste` SET `stato`='3' WHERE `idRichiesta`='{}'".format(args[3]))
        bot.unpin_chat_message(chat_id=-1001198344093, message_id=update.callback_query.message.message_id)
    elif args[0] == "langRifiutatoLink":
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text="{} \n\n#rifiutato LINK_ERROR by @{}".format(str(update.callback_query.message.text), str(update.callback_query.from_user.username)), disable_web_page_preview=True, parse_mode=ParseMode.HTML)
        setMsgLang(args[4])
        bot.sendMessage(chat_id=args[1], text=_("Siamo spiacenti, hai fornito un link errato. Ricorda: l'inserimento di una lingua nell'Atlante prevede un link ad progetto presente nella piattaforma https://translations.telegram.org\nInvia una nuova richiesta con le informazioni corrette.").format(langName=args[2]), parse_mode=ParseMode.HTML)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
        cur.execute("UPDATE `richieste` SET `stato`='3' WHERE `idRichiesta`='{}'".format(args[3]))
        bot.unpin_chat_message(chat_id=-1001198344093, message_id=update.callback_query.message.message_id)
    elif args[0] == "askLang":
        if update.callback_query.message.chat.type == "private":
            keyboard_confirm = keyboard_lingualt= InlineKeyboardMarkup([[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"), InlineKeyboardButton(_("Procedi ▶️"), callback_data="okAskLang")]])
            bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("Con questa procedura potrai richiedere l'inserimento di una lingua all'Atlante.\n\nLa richiesta verrà visionata dai nostri moderatori, in seguito ti sarà fornito un riscontro sull'avanzamento della proposta, ti chiediamo di pazientare."), disable_web_page_preview=True, parse_mode=ParseMode.HTML, reply_markup=keyboard_confirm)
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
        else:
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True, text=_("🚫 Siamo spiacenti, è possibile richiedere l'aggiunta di nuove lingue soltanto tramite la chat privata con il bot."))
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(_("➕ Richiedi lingua"), callback_data="askLang"),InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
            bot.sendMessage(update.effective_user.id, text = _("Salve! Se desideri richiedere l'inserimento di una nuova lingua utilizza questo spazio e la seguente procedura, grazie."), reply_markup=reply_markup)
    elif args[0] == "feedback":
        if update.callback_query.message.chat.type == "private":
            keyboard_confirm = keyboard_lingualt= InlineKeyboardMarkup([[InlineKeyboardButton(_("❌ Anulla"), callback_data="cancel")]])
            bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("Inviaci un commento. Il tuo messaggio verrà visionato dagli amministratori dell'Atlante."), disable_web_page_preview=True, parse_mode=ParseMode.HTML, reply_markup=keyboard_confirm)
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
            cur.execute("UPDATE `user` SET `status`='awaitingFeedback' WHERE `id`='{}'".format(update.callback_query.message.chat_id))
        else:
            bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True, text=_("🚫 Siamo spiacenti, è possibile inviare un feedback soltanto tramite la chat privata con il bot."))
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(_("💬 Scrivi un commento"), callback_data="feedback"),InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
            bot.sendMessage(update.effective_user.id, text = _("Salve! Se desideri inviare un feedback riguardo l'Atlante premi il tasto sottostante."), reply_markup=reply_markup)
    elif args[0] == "cancel":
        cur.execute("UPDATE `user` SET `status`='action_cancel' WHERE `id`='{}'".format(update.callback_query.message.chat_id))
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=True, text=_("✅ Operazione annullata."))
        keyboard_back= InlineKeyboardMarkup([[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("✅ Operazione annullata."), disable_web_page_preview=True, parse_mode=ParseMode.HTML, reply_markup=keyboard_back)
    elif args[0] == "okAskLang":
        cur.execute("UPDATE `user` SET `status`='askLang' WHERE `id`='{}'".format(update.callback_query.message.chat_id))
        keyboard_confirm = keyboard_lingualt= InlineKeyboardMarkup([[InlineKeyboardButton(_("❌ Anulla"), callback_data="cancel")]])
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("Ottimo!\nScrivi il nome della <b>lingua</b> che vorresti fosse aggiunta."), disable_web_page_preview=True, parse_mode=ParseMode.HTML, reply_markup=keyboard_confirm)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")       
    elif args[0] == "setBotLang":
        setBotLang(args[1], update.callback_query.message.chat_id)
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("Lingua del Bot cambiata. Premi su /start per applicare le modifiche."), disable_web_page_preview=True, parse_mode=ParseMode.HTML)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")        
    elif args[0] == "linguaALT":
        itSelected = ""
        enSelected = ""
        furSelected = ""
        vecSelected = ""
        catSelected = ""
        esSelected = ""
        
        if getBotLang(update.callback_query.message.chat_id) == "it":
            itSelected = "☑️"
        elif getBotLang(update.callback_query.message.chat_id) == "fur":
            furSelected = "☑️"
        elif getBotLang(update.callback_query.message.chat_id) == "vec":
            vecSelected = "☑️"
        elif getBotLang(update.callback_query.message.chat_id) == "es":
            esSelected = "☑️"
        elif getBotLang(update.callback_query.message.chat_id) == "cat":
            catSelected = "☑️"
        else:
            enSelected = "☑️"

        keyboard_lingualt= InlineKeyboardMarkup([[InlineKeyboardButton("Català {}".format(catSelected), callback_data="setBotLang_cat"),InlineKeyboardButton("English {}".format(enSelected), callback_data="setBotLang_en")],[InlineKeyboardButton("Español {}".format(esSelected), callback_data="setBotLang_es"), InlineKeyboardButton("Furlan {}".format(furSelected), callback_data="setBotLang_fur")], [InlineKeyboardButton("Italiano {}".format(itSelected), callback_data="setBotLang_it"), InlineKeyboardButton("Veneto {}".format(vecSelected), callback_data="setBotLang_vec")],[InlineKeyboardButton(_("🌐 Traduci bot"), url="https://www.transifex.com/codaze-veneto/telegram-linguistic-atlas/"), InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("Seleziona la lingua del bot. \n\nSe la lingua che desideri non fosse presente nell'elenco seguente, richiedila iscrivendoti su <a href='https://www.transifex.com/codaze-veneto/telegram-linguistic-atlas/'>Transifex</a> e aiutaci a svilupparla. 👍🏻\n\nNel caso dovessi riscontrare qualche difficoltà non esitare ad utilizzare il modulo di feedback."), disable_web_page_preview=True, parse_mode=ParseMode.HTML, reply_markup=keyboard_lingualt)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")        
    elif args[0] == "credits":
        keyboard_lingualt= InlineKeyboardMarkup([[InlineKeyboardButton(_("📝 Disclaimer"), callback_data="funzCat")], [InlineKeyboardButton(_("👥 Riconoscimenti"), callback_data="talksUs")],[InlineKeyboardButton(_("⚒ Codice sorgente"), url="https://github.com/garboh/langAtlasBot")],[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("L'<b>Atlante Linguistico</b> ospita e punta a diffondere tutte le possibili localizzazioni linguistiche di Telegram, offrendo funzioni avanzate di ricerca e applicazione.\n\nL'Atlante nasce dall'idea e dalla progettazione di <a href='https://t.me/cmpfrc'>Federico</a>, e dal supporto degli altri collaboratori di <a href='https://t.me/LenguaVeneta'>Còdaze Veneto</a>, ente che si occupa della localizzazione e diffusione di prodotti in lingua veneta.\n@langAtlasBot, il bot che ospita l'Atlante, è stato sviluppato in <a href='https://it.wikipedia.org/wiki/Python'>python</a> e viene mantenuto da <a href='https://t.me/garboh'>Francesco</a>, tecnico informatico, junior developer e studente dell'UniPD in Ing. Informatica.\n\nUtilizza il modulo di feedback per eventuali apprezzamenti, suggerimenti, proposte, o se vuoi supportare in qualche modo il progetto. Grazie di aver mostrato interesse per l'Atlante! 😉"), disable_web_page_preview=True, parse_mode=ParseMode.HTML, reply_markup=keyboard_lingualt)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")        
    elif args[0] == "funzCat":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"), InlineKeyboardButton(_("️️◀️ Indietro"), callback_data="credits")]])
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("📝 <b>Disclaimer</b>\n\nI dati inseriti nell'Atlante e riguardanti l'organizzazione politica delle lingue, sono stati raccolti dalle pagine delle WIkipedia italiana ed inglese. In caso errori o dati mancanti si prega di comunicarlo tramite il modulo di feedback.\n\nLe lingue inserite nell'Atlante richiedono uno standard minimo di completezza e qualità. Si richiede che siano completi almeno 2 client e che possibilmente ci sia volontà di completamento e aggiornamento dell'intero progetto di traduzione. Come una lingua può facilmente essere aggiunta potrà altrettanto facilmente essere rimossa. Grazie della comprensione."), disable_web_page_preview=True, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")        
    elif args[0] == "talksUs":
        keyboard_lingualt= InlineKeyboardMarkup([[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"), InlineKeyboardButton(_("️️◀️ Indietro"), callback_data="credits")]])
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("In questa sezione sono elencati i riferimenti a siti, giornali, agenzie di stampa e a qualsiasi altro media che si è occupato o ha diffuso il nostro progetto:\n\n➖ l'<a href='https://arlef.it/en/'>ARLeF</a> ha presentato l'Atlante durante la <b>conferenza stampa regionale</b> sulla localizzazione di Telegram in Friulano."), disable_web_page_preview=True, parse_mode=ParseMode.HTML, reply_markup=keyboard_lingualt)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")        
    elif args[0] == "orderPolitica":
        keyboard_continenti= InlineKeyboardMarkup([[InlineKeyboardButton(_("America settentrionale"), callback_data="orderCont_1")],[InlineKeyboardButton(_("America meridionale"), callback_data="orderCont_2")],[InlineKeyboardButton(_("Europa"), callback_data="orderCont_3")],[InlineKeyboardButton(_("Africa"), callback_data="orderCont_4")],[InlineKeyboardButton(_("Asia"), callback_data="orderCont_5")],[InlineKeyboardButton(_("Oceania"), callback_data="orderCont_6")],[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu")]])
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("Hai scelto di proseguire tramite la <b>organizzazione politica</b>! <a href='https://atlasbot.garbo.tech/img/imgbot/planisfero_colorato.jpg'>🌍</a>\n\nSeleziona il continente che vuoi esplorare."), parse_mode=ParseMode.HTML, reply_markup=keyboard_continenti)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
    elif args[0] == "orderCont":
        offset = 0
        if len(args) == 3:
            offset = args[2]
        
        varContinentName = "continetName"
        if getBotLang(update.callback_query.message.chat_id) == "it":
            varContinentName = "continetName"
        elif getBotLang(update.callback_query.message.chat_id) == "fur":
            varContinentName = "continetName_fur"
        elif getBotLang(update.callback_query.message.chat_id) == "vec":
            varContinentName = "continetName_vec"
        elif getBotLang(update.callback_query.message.chat_id) == "es":
            varContinentName = "continetName_es"
        elif getBotLang(update.callback_query.message.chat_id) == "cat":
            varContinentName = "continetName_cat"
        else:
            varContinentName = "continetName_en"
            
        cur.execute("SELECT {}, img FROM continent WHERE id={}".format(varContinentName, str(args[1])))
        row = cur.fetchone()
        continentName = row[0]
        imgContinent = row[1]
        keyboard_stati = getState(bot, update, args[1], offset)
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("Ottimo, hai selezionato l'<b>{continent}</b>! <a href='{linkToContinentIMG}'>🌍</a> \n\nOra seleziona lo Stato che vuoi visitare.").format(continent=continentName, linkToContinentIMG=imgContinent), parse_mode=ParseMode.HTML, reply_markup=keyboard_stati)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
    elif args[0] == "orderState":
        
        varCountryName = "countryName_en"
        if getBotLang(update.callback_query.message.chat_id) == "it":
            varCountryName = "countryName"
        # elif getBotLang(update.callback_query.message.chat_id) == "fur":
            # varCountryName = "countryName_fur"
        elif getBotLang(update.callback_query.message.chat_id) == "vec":
            varCountryName = "countryName_vec"
        elif getBotLang(update.callback_query.message.chat_id) == "es":
            varCountryName = "countryName_es"
        elif getBotLang(update.callback_query.message.chat_id) == "cat":
            varCountryName = "countryName_cat"
        else:
            varCountryName = "countryName_en"
        
        cur.execute("SELECT {}, img FROM country WHERE id={}".format(varCountryName, str(args[1])))
        row = cur.fetchone()
        countryName = row[0]
        imgCountry = row[1]
        keyboard_lang = getLang(bot, update, args[1], args[2])
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("Ecco le lingue attualmente presenti nello Stato: <b>{state}</b>! <a href='{linkToStateIMG}'>🌍</a>\n\nSeleziona la lingua che preferisci per accedere alla sua scheda e vedere le opzioni disponibili.\n\nNel caso non sia presente in questo elenco, prima di richiedere la lingua che cerchi, prova a visitare altri Stati o ad utilizzare la catalogazione alfabetica.").format(state=countryName, linkToStateIMG=imgCountry), parse_mode=ParseMode.HTML, reply_markup=keyboard_lang)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
    elif args[0] == "lang":
        
        varDialectName = "name"
        if getBotLang(update.callback_query.message.chat_id) == "it":
            varDialectName = "name"
        # elif getBotLang(update.callback_query.message.chat_id) == "fur":
            # varDialectName = "name_fur"
        elif getBotLang(update.callback_query.message.chat_id) == "vec":
            varDialectName = "name_vec"
        elif getBotLang(update.callback_query.message.chat_id) == "es":
            varDialectName = "name_es"
        elif getBotLang(update.callback_query.message.chat_id) == "cat":
            varDialectName = "name_cat"
        else:
            varDialectName = "name_en"
        
        cur.execute("SELECT {}, flag FROM lang WHERE code='{}'".format(varDialectName, str(args[1])))
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT {}, flag FROM customLang WHERE codeCLang='{}'".format(varDialectName, str(args[1])))
            row = cur.fetchone()
        nome = row[0]
        flag = row[1]
        
        test = "404"
        if args[2] == "oc":
            test = "orderChar"
        if args[2] == "os":
            test = "orderState"

        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"), InlineKeyboardButton(_("◀️ Indietro"), callback_data="{}_{}_1".format(test, args[3]))]])
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=_("Per installare la lingua {langName} su Telegram clicca sul seguente link.\n\n<a href='{linkToLangIMG}'>👉🏻</a> https://t.me/setlanguage/{langCode}\n\nRicorda: potrai sempre tornare alla lingua iniziale tramite le impostazioni native dell'app.").format(langName=nome, linkToLangIMG=flag, langCode=args[1]), parse_mode=ParseMode.HTML, reply_markup=keyboard)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")
    elif args[0] == "orderChar":
        
        varDialectName = "name"
        if getBotLang(update.callback_query.message.chat_id) == "it":
            varDialectName = "name"
        # elif getBotLang(update.callback_query.message.chat_id) == "fur":
            # varDialectName = "name_fur"
        elif getBotLang(update.callback_query.message.chat_id) == "vec":
            varDialectName = "name_vec"
        elif getBotLang(update.callback_query.message.chat_id) == "es":
            varDialectName = "name_es"
        elif getBotLang(update.callback_query.message.chat_id) == "cat":
            varDialectName = "name_cat"
        else:
            varDialectName = "name_en"
        
        cur.execute("(SELECT {}, flag, code FROM lang WHERE `visible`=1 AND {} LIKE '{}%') UNION (SELECT {}, flag, codeCLang as code FROM customLang WHERE `visible`=1 AND {} LIKE '{}%') ORDER BY {}".format(varDialectName, varDialectName, str(args[1]),varDialectName,varDialectName,str(args[1]),varDialectName))
        rowL = cur.fetchall()
        arrays_Lang=[]
        arrays_Lang.append([])
        lenLan = len(arrays_Lang)
        count = 0
        for lang in rowL:
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
        bot.editMessageText(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, text=testo.format(count, args[1]), parse_mode=ParseMode.HTML, reply_markup=keyBoard)
        bot.answerCallbackQuery(callback_query_id=update.callback_query.id, show_alert=False, text="✅")

    end()
    
def getState(bot, update, continent, offset):
    cur.execute("SELECT count(*) AS conta FROM `country` WHERE `continent`={}".format(continent))
    row = cur.fetchone()
    tot = row[0]
    
    varCountryName = "countryName"
    if getBotLang(update.callback_query.message.chat_id) == "it":
        varCountryName = "countryName"
    # elif getBotLang(update.callback_query.message.chat_id) == "fur":
        # varCountryName = "countryName_fur"
    elif getBotLang(update.callback_query.message.chat_id) == "vec":
        varCountryName = "countryName_vec"
    elif getBotLang(update.callback_query.message.chat_id) == "es":
        varCountryName = "countryName_es"
    elif getBotLang(update.callback_query.message.chat_id) == "cat":
        varCountryName = "countryName_cat"
    else:
        varCountryName = "countryName_en"
    
    cur.execute("SELECT `id`, `{}` AS countryName FROM `country` WHERE `continent`={} ORDER BY `countryName` LIMIT 10 OFFSET {}".format(varCountryName, continent, offset))
    array_Lang=[]
    
    rowL = cur.fetchall()
    if rowL:
        array_Lang.append([])
        lenLan = len(array_Lang)
        count = 0
        for lang in rowL:
            count+= 1
            if count % 2 == 0:
                array_Lang[-1].append(InlineKeyboardButton("{}".format(lang[1]), callback_data="orderState_{}_{}".format(lang[0], continent)))
            else:
                array_Lang.append([])
                array_Lang[-1].append(InlineKeyboardButton("{}".format(lang[1]), callback_data="orderState_{}_{}".format(lang[0], continent)))
    
    array_Lang.append([])
    
    if int(offset) > 0:
        array_Lang[-1].append(InlineKeyboardButton(_("⬅️ Pag. prec."), callback_data="orderCont_{}_{}".format(continent, str(int(offset)-10))))
    if (int(offset) + 10) < int(tot):
        array_Lang[-1].append(InlineKeyboardButton(_("Pag. suc. ➡️"), callback_data="orderCont_{}_{}".format(continent, str(int(offset)+10))))
        
    array_Lang.append([])
    array_Lang[-1].append(InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"))
    array_Lang[-1].append(InlineKeyboardButton(_("◀️ Indietro"), callback_data="orderPolitica"))
            
    keyBoard = InlineKeyboardMarkup(array_Lang)
    return keyBoard

def getLang(bot, update, country, continet):
    
    varDialectName = "name"
    if getBotLang(update.callback_query.message.chat_id) == "it":
        varDialectName = "name"
    elif getBotLang(update.callback_query.message.chat_id) == "fur":
        varDialectName = "name_fur"
    elif getBotLang(update.callback_query.message.chat_id) == "vec":
        varDialectName = "name_vec"
    elif getBotLang(update.callback_query.message.chat_id) == "es":
        varDialectName = "name_es"
    elif getBotLang(update.callback_query.message.chat_id) == "cat":
        varDialectName = "name_cat"
    else:
        varDialectName = "name_en"
    
    cur.execute("(SELECT lang.code, lang.{}, country.continent FROM `country_lang` JOIN lang ON country_lang.lang=lang.code JOIN country ON country_lang.country=country.id WHERE country_lang.country={} AND lang.visible=1) UNION (SELECT customLang.codeCLang as code, customLang.{}, country.continent FROM `country_customLang` JOIN customLang ON country_customLang.customLang=customLang.codeCLang JOIN country ON country_customLang.country=country.id WHERE country_customLang.country={} AND customLang.visible=1)".format(varDialectName, country, varDialectName, country))
    arrays_Lang=[]
    orderCountLang = -1
    rowL = cur.fetchall()
    if rowL:
        arrays_Lang.append([])
        lenLan = len(arrays_Lang)
        count = 0
        for lang in rowL:
            count+= 1
            if count % 2 == 0:
                arrays_Lang[-1].append(InlineKeyboardButton("{}".format(lang[1]), callback_data="lang_{}_os_{}".format(lang[0], country)))
            else:
                arrays_Lang.append([])
                arrays_Lang[-1].append(InlineKeyboardButton("{}".format(lang[1]), callback_data="lang_{}_os_{}".format(lang[0], country)))
        orderCountLang = lang[2]
    else:
        orderCountLang = continet
    arrays_Lang.append([])
    arrays_Lang[-1].append(InlineKeyboardButton(_("⏪ Torna al menù"), callback_data="backMenu"))
    
    arrays_Lang[-1].append(InlineKeyboardButton(_("◀️ Indietro"), callback_data="orderCont_{}".format(orderCountLang)))
            
    keyBoards = InlineKeyboardMarkup(arrays_Lang)
    return keyBoards

@run_async
def inlinemode(bot, update):
    """Handle the inline query."""
    openDb()
    
    query = MySQLdb.escape_string(update.inline_query.query).decode('UTF-8')
    
    langBot = getBotLang(update.inline_query.from_user.id)
    setBotLang(langBot, update.inline_query.from_user.id)
    
    varDialectName = "name"
    if langBot == "it":
        varDialectName = "name"
    elif langBot == "fur":
        varDialectName = "name_fur"
    elif langBot == "vec":
        varDialectName = "name_vec"
    elif langBot == "es":
        varDialectName = "name_es"
    elif langBot == "cat":
        varDialectName = "name_cat"
    else:
        varDialectName = "name_en"
    
    cur.execute("(SELECT code,{varDialectName} AS name,flag FROM `lang` WHERE `visible`=1 AND (`code` LIKE \"{query}%\" OR `name` LIKE \"{query}%\") LIMIT 20) UNION ALL (SELECT codeCLang AS code,{varDialectName} AS name,flag FROM `customLang` WHERE `visible`=1 AND (`codeCLang` LIKE \"{query}%\" OR `name` LIKE \"{query}%\"))  ORDER BY `name`".format(varDialectName=varDialectName, query=query))
    rowAll = cur.fetchall()
    if rowAll:
        results = []
        for lang in rowAll:
            results.append(InlineQueryResultArticle(id="{}".format(lang[0]),title="🌐 {}".format(lang[1]), thumb_url="{}".format(lang[2]), description=_("Applica la lingua {langName} su Telegram!").format(langName=lang[1]), input_message_content=InputTextMessageContent(_("Per installare la lingua {langName} su Telegram clicca sul seguente link.\n\n<a href='{linkToLangIMG}'>👉🏻</a> https://t.me/setlanguage/{langCode}\n\nRicorda: potrai sempre tornare alla lingua iniziale tramite le impostazioni native dell'app.").format(langName=lang[1], linkToLangIMG=lang[2], langCode=lang[0]), parse_mode=ParseMode.HTML)))
    else:
        results = [
            InlineQueryResultArticle(
                id=uuid4(),
                title=_("Non è stata trovata alcuna lingua."),
                input_message_content=InputTextMessageContent(
                    _("❌ Non è stata trovata alcuna lingua.")))]

    update.inline_query.answer(results)
    end()
    
def main():
   
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("") #your API TOKEN here


    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    #j = updater.job_queue

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("cancel", cancel))
    dp.add_handler(CommandHandler("info", getid))
   
    
    # on noncommand i.e message - echo the message on Telegram


    dp.add_handler(CallbackQueryHandler(inline_query))
    dp.add_handler(InlineQueryHandler(inlinemode))
    dp.add_handler(MessageHandler(Filters.text, testo))
    dp.add_handler(MessageHandler(Filters.photo, photo))




    # log all errors
    dp.add_error_handler(error)

    print("running langAtlasBot!")
    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
if __name__ == '__main__':
    main()
