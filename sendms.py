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


    db = MySQLdb.connect(host="localhost",
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
    
    sql = "SELECT * FROM `user"
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
        elif row[2] == "es":
            messaggio = "➕ ¡Nuevo idioma añadido!\n\n¡El idioma {nameLang} ha sido añadido al Atlas! Utiliza el siguiente enlace para probarlo: {linkLang}".format(nameLang=nameLang, linkLang=linkLang)
        elif row[2] == "fur":
            messaggio = "➕ Zontade une gnove lenghe!\n\nLa lenghe {nameLang} e je stade zontade al Atlant. Dopre il link {linkLang} par provâle!".format(nameLang=nameLang, linkLang=linkLang)
        
        # elif row[2] == "cat":
            # messaggio = "".format(nameLang=nameLang, linkLang=linkLang)
            # String NULL -> https://www.transifex.com/codaze-veneto/telegram-linguistic-atlas/translate/#ca/langtla_botpot/308075038
            
        else:
            messaggio = "➕New language added!\n\nThe language {nameLang} has been inserted in the Atlas. Use the link {linkLang} to try it!".format(nameLang=nameLang, linkLang=linkLang)
        try:
             reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Share", switch_inline_query="{}".format(nameLang))]])
             
             bot.sendMessage(chat_id, text=messaggio, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
             print("Inviato {} - Inviati {}".format(conta, inviati))
             inviati += 1
        except:
            print("Errore {} - Errori {}".format(conta, errori))
            errori += 1

        conta = conta + 1
        contados = contados + 1
        rimanenti = totali - conta
        if contados == 5:
            try:
                bot.editMessageText(chat_id=-1001198344093, message_id=prova.message_id, text="Spam avviato... \n{} messagi inviati\n{} errori\n\n{} rimanenti / {} totali".format(inviati, errori, rimanenti, totali), )
            except:
                pass
            contados=0
            time.sleep(0.3)
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
