"""Provide an Epub mixin class for the mimetype representation.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import datetime
from string import Template


class Mimetype:

    _MIMETYPE = 'application/epub+zip'

    def write_mimetype(self):
        self.write_file('mimetype', self._MIMETYPE)
