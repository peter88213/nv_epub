"""Provide global constants and functions.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_epub
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from xml import sax

CSS_NAME = 'nv_epub.css'
COVER_FILE = 'cover.jpg'
COVER_PAGE_NAME = 'coverpage.xhtml'
FOOTNOTES_PAGE_NAME = 'footnotes.xhtml'
DEFAULT_COVER_PATH = 'text/content0001.xhtml'


def escape_string(text):
    if text is None:
        return ''

    return sax.saxutils.escape(text)

