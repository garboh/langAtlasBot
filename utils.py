# -*- coding: utf-8 -*-
import gettext
import os

# Path to the locale directory
locale_path = os.path.join(os.path.dirname(__file__), 'locale')

# Localization
en = gettext.translation('langAtlasBot', localedir=locale_path, languages=['en'])
#it = gettext.translation('langAtlasBot', localedir='locale', languages=['it'])
#es = gettext.translation('langAtlasBot', localedir='locale', languages=['es'])
#cat = gettext.translation('langAtlasBot', localedir='locale', languages=['cat'])
#fur = gettext.translation('langAtlasBot', localedir='locale', languages=['fur'])
#vec = gettext.translation('langAtlasBot', localedir='locale', languages=['vec'])

_ = en.gettext
__ = en.ngettext

def set_msg_lang(lang):
    global _
    global __
    _ = en.gettext
    __ = en.ngettext
    #if lang == 'it':
    #    _ = it.gettext
    #    __ = it.ngettext
    #elif lang == 'es':
    #    _ = es.gettext
    #    __ = es.ngettext
    #elif lang == 'cat':
    #    _ = cat.gettext
    #    __ = cat.ngettext
    #elif lang == 'fur':
    #    _ = fur.gettext
    #    __ = fur.ngettext
    #elif lang == 'vec':
    #    _ = vec.gettext
    #    __ = vec.ngettext
    #else:
    #    _ = en.gettext
    #    __ = en.ngettext
