# -*- coding: utf-8 -*-
import gettext
import logging
import os
from typing import Callable

locale_path = os.path.join(os.path.dirname(__file__), "locale")
logger = logging.getLogger(__name__)

SUPPORTED_LANGS = frozenset(["en", "it", "fur", "vec", "es", "cat"])
_cache: dict[str, gettext.GNUTranslations] = {}


def _load(lang: str) -> gettext.GNUTranslations:
    if lang not in _cache:
        try:
            t = gettext.translation("langAtlasBot", localedir=locale_path, languages=[lang])
        except FileNotFoundError:
            logger.warning("No translation file for '%s', falling back to 'en'", lang)
            t = gettext.translation("langAtlasBot", localedir=locale_path, languages=["en"])
        _cache[lang] = t
    return _cache[lang]


def get_translator(lang: str) -> tuple[Callable, Callable]:
    """Return (gettext, ngettext) callables for the given language code."""
    t = _load(lang if lang in SUPPORTED_LANGS else "en")
    return t.gettext, t.ngettext
