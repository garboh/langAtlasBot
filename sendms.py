import telegram
from telegram import *
import time
import MySQLdb
    
def main(args):
    bot = telegram.Bot(token='') 
    inviati = 0
    errori = 0
    totali = 0
    conta = 0
    contados = 0
    prova = bot.sendMessage(-1001198344093, text="Avvio notifica ...")

    idRichiesta = args[1]


    db = MySQLdb.connect(host="",
                         user="",
                         passwd="",
                         db="",
                         charset='utf8mb4',
                         use_unicode=True)
    cur = db.cursor()

    query = "SELECT * FROM `richieste` WHERE `idRichiesta` = {}".format(idRichiesta)
    cur.execute(query)
    row = cur.fetchone()
    nameLang = row[2]
    linkLang = row[3]
    
    sql = "SELECT * FROM `user`"
    cur.execute(sql)
    
    rows = cur.fetchall()
    for row in rows:
        totali += 1
    
    row = 0
    cur.execute(sql)
    rows = cur.fetchall()
    for row in rows:
        chat_id = row[0]
        messaggio = ""
        if row[2] == "it":
			messaggio = "➕Nuova lingua aggiunta!\n\nNell'Atlante è stata inserita la lingua {nameLang}. Per provarla utilizza il link {linkLang}!".format(nameLang=nameLang, linkLang=linkLang)
		elif row[2] == "vec":
			messaggio = "➕Łengua nova zontada!\n\nInte l'Atlante A ze stà zontada na łengua nova {nameLang}. Par proarla dòpara el link {linkLang}!".format(nameLang=nameLang, linkLang=linkLang)
		else:
			messaggio = "➕New language added!\n\nThe language {nameLang} has been inserted in the Atlas. Use the link {linkLang} to try it!".format(nameLang=nameLang, linkLang=linkLang)
        try:
             #reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start"), InlineKeyboardButton("Support the project 💪", url="https://paypal.me/garboh")]])
             #bot.sendMessage(chat_id, text=messaggio, reply_markup=reply_markup)
             
             bot.sendMessage(chat_id, text=messaggio, parse_mode=ParseMode.HTML)
             print("Inviato {} - Inviati {}".format(conta, inviati))
             inviati += 1
        except:
            print("Errore {} - Errori {}".format(conta, errori))
            errori += 1

        conta = conta + 1
        contados = contados + 1
        rimanenti = totali - conta
        if contados == 20:
            try:
                bot.editMessageText(chat_id=-1001198344093, message_id=prova.message_id, text="Spam avviato... \n{} messagi inviati\n{} errori\n\n{} rimanenti / {} totali".format(inviati, errori, rimanenti, totali), )
            except:
                pass
            contados=0
            time.sleep(1)
        else:
            time.sleep(0.5)
    
    
    
    bot.sendMessage(-1001198344093, text="Finito!!! \n{} messaggi inviati \n{} errori".format(inviati, errori))
    db.commit()
    db.close()
    print("\n{} messaggi inviati \n{} errori".format(inviati, errori))
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
