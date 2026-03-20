"""Provide an Epub mixin class for the content.opf representation.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import datetime
from string import Template


class ContentOpf:

    _CONTENT_OPF_HEADER = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" '
        'unique-identifier="BookID" version="2.0">\n'
        '    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:opf="http://www.idpf.org/2007/opf">\n'
        '        <dc:identifier id="BookID" '
        'opf:scheme="UUID">$Uuid</dc:identifier>\n'
        '        <dc:contributor opf:role="bkp">Created with nv_epub '
        '$Version by Peter Triesberger '
        'https://github.com/peter88213/nv_epub</dc:contributor>\n'
        '        <dc:date opf:event="creation">$Date</dc:date>\n'
        '        <dc:creator opf:role="aut">$Author</dc:creator>\n'
        '        <dc:language>$Language</dc:language>\n'
        '        <dc:title>$Title</dc:title>\n'
        '        <meta name="nv_epub" content="$Version"/>\n'
        '        <meta name="cover" content="cover.jpg"/>\n'
        '    </metadata>'
    )
    _CONTENT_OPF_FOOTER = (
        '    <guide>\n'
        '        <reference type="cover" '
        'title="Cover" href="$Coverpage"/>\n'
        '    </guide>\n'
        '</package>\n'
    )

    def write_content_opf(self, ChIdsByContentFileNames):
        opfMapping = {
            'Uuid': self.uuid,
            'Version': self.version,
            'Date': datetime.date.today().isoformat(),
            'Author': self._escape_string(self.novel.authorName),
            'Language': self.novel.languageCode,
            'Title': self._escape_string(self.novel.title),
            'Coverpage': self._coverPagePath,
        }
        contentOpfLines = [
            Template(self._CONTENT_OPF_HEADER).safe_substitute(opfMapping),
        ]

        #--- manifest
        contentOpfLines.append('    <manifest>')
        contentOpfLines.append(
            '        <item id="ncx" href="toc.ncx" '
            'media-type="application/x-dtbncx+xml"/>'
        )
        contentOpfLines.append(
            f'        <item id="{self.CSS_NAME}" '
            f'href="styles/{self.CSS_NAME}" media-type="text/css"/>'
        )
        if self._hasCover:
            contentOpfLines.append(
                f'        <item id="{self._COVER_FILE}" '
                f'href="images/{self._COVER_FILE}" '
                'media-type="image/jpeg"/>'
            )
            contentOpfLines.append(
                f'        <item id="{self._COVER_PAGE_NAME}" '
                f'href="text/{self._COVER_PAGE_NAME}" '
                'media-type="application/xhtml+xml"/>'
            )
        for fileName in ChIdsByContentFileNames:
            contentOpfLines.append(
                f'        <item id="{fileName}" href="text/{fileName}" '
                'media-type="application/xhtml+xml"/>'

            )
        if self._contentParser.footnotes:
            contentOpfLines.append(
                f'        <item id="{self._FOOTNOTES_PAGE_NAME}" '
                f'href="text/{self._FOOTNOTES_PAGE_NAME}" '
                'media-type="application/xhtml+xml"/>'
            )
        contentOpfLines.append('    </manifest>')

        #--- spine
        contentOpfLines.append('    <spine toc="ncx">')
        if self._hasCover:
            contentOpfLines.append(
                '        <itemref idref="coverpage.xhtml"/>'
            )
        for fileName in ChIdsByContentFileNames:
            contentOpfLines.append(
                f'        <itemref idref="{fileName}"/>'
            )
        if self._contentParser.footnotes:
            contentOpfLines.append(
                f'        <itemref idref="{self._FOOTNOTES_PAGE_NAME}" '
                'linear="no"/>'
            )
        contentOpfLines.append('    </spine>')
        contentOpfLines.append(
            Template(self._CONTENT_OPF_FOOTER).safe_substitute(opfMapping),
        )
        self.write_file(f'OEBPS/content.opf', '\n'.join(contentOpfLines))

