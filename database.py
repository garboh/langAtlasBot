# -*- coding: utf-8 -*-
import MySQLdb
import logging
from contextlib import contextmanager
from .config import DB_HOST, DB_USER, DB_PASS, DB_NAME

logger = logging.getLogger(__name__)

# Whitelisted column name maps — never interpolate user input
_CONTINENT_COL: dict[str, str] = {
    "it":  "continetName",
    "fur": "continetName_fur",
    "vec": "continetName_vec",
    "es":  "continetName_es",
    "cat": "continetName_cat",
    "en":  "continetName_en",
}
_COUNTRY_COL: dict[str, str] = {
    "it":  "countryName",
    "fur": "countryName_fur",
    "vec": "countryName_vec",
    "es":  "countryName_es",
    "cat": "countryName_cat",
    "en":  "countryName_en",
}
_LANG_COL: dict[str, str] = {
    "it":  "name",
    "fur": "name_fur",
    "vec": "name_vec",
    "es":  "name_es",
    "cat": "name_cat",
    "en":  "name_en",
}


@contextmanager
def get_db():
    conn = MySQLdb.connect(
        host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME,
        charset="utf8mb4", use_unicode=True,
    )
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def get_bot_lang(cur, chat_id: int) -> str:
    cur.execute("SELECT `lang` FROM `user` WHERE `id`=%s", (chat_id,))
    row = cur.fetchone()
    return row[0] if row else "en"


def set_bot_lang(cur, lang: str, chat_id: int) -> None:
    cur.execute("UPDATE `user` SET `lang`=%s WHERE `id`=%s", (lang, chat_id))


def init_user(cur, chat_id: int, language_code: str | None) -> bool:
    cur.execute("SELECT `id` FROM `user` WHERE `id`=%s", (chat_id,))
    if cur.fetchone():
        return False
    lang = language_code if language_code in _LANG_COL else "en"
    cur.execute(
        "INSERT INTO `user` (`id`, `status`, `lang`) VALUES (%s, 'new_user', %s)",
        (chat_id, lang),
    )
    return True


def get_user_status(cur, chat_id: int) -> str:
    cur.execute("SELECT `status` FROM `user` WHERE `id`=%s", (chat_id,))
    row = cur.fetchone()
    return row[0] if row else ""


def update_user_status(cur, status: str, user_id: int) -> None:
    cur.execute("UPDATE `user` SET `status`=%s WHERE `id`=%s", (status, user_id))


def get_feedback_status(cur, feedback_id: int):
    cur.execute("SELECT `status` FROM `feedback` WHERE `idFeed`=%s", (feedback_id,))
    return cur.fetchone()


def get_feedback(cur, feedback_id: int):
    cur.execute(
        "SELECT `user_id`, `text`, `admin_msg_id`, `user_full_name`, `user_username`"
        " FROM `feedback` WHERE `idFeed`=%s",
        (feedback_id,),
    )
    return cur.fetchone()


def update_feedback_status(cur, status: str, feedback_id: int) -> None:
    cur.execute("UPDATE `feedback` SET `status`=%s WHERE `idFeed`=%s", (status, feedback_id))


def update_feedback_admin_msg(cur, feedback_id: int, admin_msg_id: int) -> None:
    cur.execute("UPDATE `feedback` SET `admin_msg_id`=%s WHERE `idFeed`=%s", (admin_msg_id, feedback_id))


def update_richieste_status(cur, status: int, richiesta_id: int) -> None:
    cur.execute("UPDATE `richieste` SET `stato`=%s WHERE `idRichiesta`=%s", (status, richiesta_id))


def insert_richiesta(cur, chat_id: int, name_lang: str, link_lang: str) -> int:
    cur.execute(
        "INSERT INTO `richieste` (`user_id`, `nameLang`, `linkLang`, `stato`) VALUES (%s, %s, %s, 1)",
        (chat_id, name_lang, link_lang),
    )
    return cur.lastrowid


def insert_feedback(cur, chat_id: int, text: str, full_name: str, username: str | None) -> int:
    cur.execute(
        "INSERT INTO `feedback` (`user_id`, `text`, `status`, `user_full_name`, `user_username`)"
        " VALUES (%s, %s, 'toBeAnswered', %s, %s)",
        (chat_id, text, full_name, username),
    )
    return cur.lastrowid


def get_richiesta(cur, richiesta_id: int):
    cur.execute(
        "SELECT `nameLang`, `linkLang` FROM `richieste` WHERE `idRichiesta`=%s",
        (richiesta_id,),
    )
    return cur.fetchone()


def get_continent_name_and_img(cur, lang: str, continent_id: int):
    col = _CONTINENT_COL.get(lang, "continetName_en")
    cur.execute(f"SELECT `{col}`, `img` FROM `continent` WHERE `id`=%s", (continent_id,))
    return cur.fetchone()


def get_country_name_and_img(cur, lang: str, country_id: int):
    col = _COUNTRY_COL.get(lang, "countryName_en")
    cur.execute(f"SELECT `{col}`, `img` FROM `country` WHERE `id`=%s", (country_id,))
    return cur.fetchone()


def get_lang_name_and_flag(cur, lang: str, lang_code: str):
    col = _LANG_COL.get(lang, "name_en")
    cur.execute(f"SELECT `{col}`, `flag` FROM `lang` WHERE `code`=%s", (lang_code,))
    return cur.fetchone()


def get_custom_lang_name_and_flag(cur, lang: str, lang_code: str):
    col = _LANG_COL.get(lang, "name_en")
    cur.execute(f"SELECT `{col}`, `flag` FROM `customLang` WHERE `codeCLang`=%s", (lang_code,))
    return cur.fetchone()


def get_languages_by_initial(cur, lang: str, initial: str):
    col = _LANG_COL.get(lang, "name_en")
    cur.execute(
        f"(SELECT `{col}`, `flag`, `code` FROM `lang`"
        f"  WHERE `visible`=1 AND `{col}` LIKE %s)"
        f" UNION"
        f" (SELECT `{col}`, `flag`, `codeCLang` AS `code` FROM `customLang`"
        f"  WHERE `visible`=1 AND `{col}` LIKE %s)"
        f" ORDER BY 1",
        (initial + "%", initial + "%"),
    )
    return cur.fetchall()


def get_countries_by_continent(cur, lang: str, continent_id: int, offset: int = 0):
    col = _COUNTRY_COL.get(lang, "countryName_en")
    cur.execute(
        f"SELECT `id`, `{col}` FROM `country`"
        f" WHERE `continent`=%s ORDER BY `{col}` LIMIT %s, 20",
        (continent_id, offset),
    )
    return cur.fetchall()


def get_langs_by_country(cur, lang: str, country_id: int, offset: int = 0):
    col = _LANG_COL.get(lang, "name_en")
    cur.execute(
        f"SELECT l.`code`, l.`{col}` FROM `lang` l"
        f" JOIN `country_lang` cl ON l.`code` = cl.`lang`"
        f" WHERE cl.`country`=%s AND l.`visible`=1"
        f" ORDER BY l.`{col}` LIMIT %s, 20",
        (country_id, offset),
    )
    return cur.fetchall()


def search_languages(cur, query: str, lang: str):
    col = _LANG_COL.get(lang, "name_en")
    q = query + "%"
    cur.execute(
        f"(SELECT `code`, `{col}` AS `name`, `flag` FROM `lang`"
        f"  WHERE `visible`=1 AND (`code` LIKE %s OR `{col}` LIKE %s) LIMIT 20)"
        f" UNION ALL"
        f" (SELECT `codeCLang` AS `code`, `{col}` AS `name`, `flag` FROM `customLang`"
        f"  WHERE `visible`=1 AND (`codeCLang` LIKE %s OR `{col}` LIKE %s))"
        f" ORDER BY `name` LIMIT 40",
        (q, q, q, q),
    )
    return cur.fetchall()


def get_all_users(cur):
    cur.execute("SELECT `id`, `lang` FROM `user`")
    return cur.fetchall()
