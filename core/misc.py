# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

'''Miscellaneous functions.'''

def stripunicode(string):
    '''Strip unicode from a string.'''
    if isinstance(string, str):
        # If the string is just a string without any unicode, just return it.
        return string

    if isinstance(string, unicode):
        # The string *is* unicode, let's strip stuff from it.
        # fancy quotes
        string = string.replace(u'\u201c', u'"')
        string = string.replace(u'\u201d', u'"')
        string = string.replace(u'\u2018', u"'")
        string = string.replace(u'\u2019', u"'")
        # ellipsis
        string = string.replace(u'\u2026', u'...')
        # return the string encoded into ascii
        return string.encode()
