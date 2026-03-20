"""Provide an Epub mixin class for the EPUB table of contents representation.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from string import Template

from nvepub.nvepub_globals import escape_string


class Toc:

    _TOC_NCX_HEADER = (
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"\n'
        '    "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">\n'
        '\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
        '    <head>\n'
        '        <meta name="dtb:uid" content="$Uuid"/>\n'
        '        <meta name="dtb:depth" content="2"/>\n'
        '        <meta name="dtb:totalPageCount" content="0"/>\n'
        '        <meta name="dtb:maxPageNumber" content="0"/>\n'
        '    </head>\n'
        '    <docTitle>\n'
        '        <text>$Title</text>\n'
        '    </docTitle>\n'
        '    <navMap>'
    )
    _TOC_NAV_POINT = (
'      <navPoint id="$NavpointID" playOrder="$Playorder">\n'
'        <navLabel>\n'
'          <text>$Title</text>\n'
'        </navLabel>\n'
'        <content src="text/$Filename#$HeadingID"/>\n'
'      </navPoint>'
    )
    _TOC_NCX_FOOTER = (
        '    </navMap>\n'
        '</ncx>\n'
    )
    _FOOTNOTE = (
        '<div class="footnote" id="footnote-$NoteIndex">\n'
        '<p class="fnparagraph">'
        '$Text&nbsp; '
        '<a href="$Page#fnreturn-$NoteIndex"><strong>&#x21B5;</strong></a>'
        '</p>\n'
        '</div>\n'
    )

    def write_toc_ncx(
        self,
        chIdsByContentFileNames,
        eBookUuid,
    ):
        ncxMapping = {
            'Uuid': eBookUuid,
            'Title': escape_string(self.novel.title),
        }
        tocNcxLines = [
            Template(self._TOC_NCX_HEADER).substitute(ncxMapping),
        ]
        i = 0
        for ContentFileName in chIdsByContentFileNames:
            chId = chIdsByContentFileNames[ContentFileName]
            if not chId in self.novel.chapters:
                continue

            i += 1
            order = str(i)
            navPointMapping = {
                'NavpointID': f'navPoint-{order}',
                'Playorder': order,
                'Title': escape_string(self.novel.chapters[chId].title),
                'Filename': ContentFileName,
                'HeadingID': chId,
            }
            tocNcxLines.append(
                Template(self._TOC_NAV_POINT).substitute(navPointMapping),
            )
        tocNcxLines.append(
            Template(self._TOC_NCX_FOOTER).substitute(ncxMapping),
        )
        self.write_file(f'OEBPS/toc.ncx', '\n'.join(tocNcxLines))
