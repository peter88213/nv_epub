"""Provide an Epub mixin class for the cover representation.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from shutil import copy2
from string import Template

from nvepub.nvepub_globals import COVER_FILE
from nvepub.nvepub_globals import COVER_PAGE_NAME
from nvepub.nvepub_globals import DEFAULT_COVER_PATH


class Cover:

    _COVER_PAGE = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n'
        '  <head>\n'
        '    <meta http-equiv="Content-Type" content="text/html; '
        'charset=UTF-8"/>\n'
        '    <title>Cover</title>\n'
        '    <style type="text/css" title="override_css">\n'
        '      @page {padding: 0pt; margin:0pt}\n'
        '      body { text-align: center; padding:0pt; margin: 0pt; '
        'background-color : #000000;}\n'
        '    </style>\n'
        '  </head>\n'
        '  <body>\n'
        '    <div>\n'
        '        <img id="cover" height="100%" alt="Cover" '
        'src="../$Cover" />\n'
        '    </div>\n'
        '  </body>\n'
        '</html>\n'

    )

    def include_cover(self, rootDir, prjDir):
        prjCoverPath = os.path.join(prjDir, COVER_FILE)
        if not os.path.isfile(prjCoverPath):
            return DEFAULT_COVER_PATH, False

        coverDir = f'{rootDir}/OEBPS/images'
        os.makedirs(coverDir)
        copy2(prjCoverPath, coverDir)
        self.epubComponents.append(f'OEBPS/images/{COVER_FILE}')
        coverPagePath = f'text/{COVER_PAGE_NAME}'
        text = Template(self._COVER_PAGE).substitute(
            {'Cover': f'images/{COVER_FILE}', }
        )
        self.write_file(f'OEBPS/{coverPagePath}', text)
        return coverPagePath, True

