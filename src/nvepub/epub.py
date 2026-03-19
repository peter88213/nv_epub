"""Provide a class for EPUB representation.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_epub
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import datetime
import os
from shutil import rmtree
from string import Template
import tempfile
import uuid
from xml import sax
import zipfile

from nvepub.novx_to_xhtml import NovxToXhtml
from nvepub.nvepub_globals import EPUB_SUFFIX
from nvepub.nvepub_locale import _
from nvepub.stylesheet import Stylesheet
from nvlib.model.file.file import File
from nvlib.novx_globals import CH_ROOT
from nvlib.novx_globals import norm_path


class Epub(File, Stylesheet):

    DESCRIPTION = 'EPUB e-book'
    EXTENSION = '.epub'
    SUFFIX = EPUB_SUFFIX
    CSS_NAME = 'nv_epub.css'

    _MIMETYPE = 'application/epub+zip'
    _CONTAINER_XML = (
        '<?xml version="1.0"?>\n'
        '<container version="1.0" '
        'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '    <rootfiles>\n'
        '        <rootfile full-path='
        '"OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
        '   </rootfiles>\n'
        '</container>\n'
    )
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
        '       <reference type="cover" '
        'title="Cover Page" href="$Coverpage"/>\n'
        '    </guide>\n'
        '</package>\n'
    )
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
    _fileHeader = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"\n'
        '    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
        '<html xmlns="http://www.w3.org/1999/xhtml">\n'
        '<head>\n'
        '<link rel="stylesheet" '
        'href="../styles/$Stylesheet" type="text/css" />\n'
        '<title>$Title</title>\n'
        '</head>\n'
        '<body>\n'
    )
    _fileFooter = (
        '</body>\n'
        '</html>\n'
    )
    _frontmatter = (
        '<p class="title">$Title</p>\n'
        '<p class="author">$Author</p>\n'
    )
    _partTemplate = (
        '<h1 id="$ID">$Title</h1>\n'
    )
    _chapterTemplate = (
        '<h2 id="$ID">$Title</h2>\n'
    )
    _epigraphTemplate = '$SectionContent$Desc\n'
    _sectionTemplate = '$SectionContent\n'
    _sectionDivider = '<h4>* * *</h4>\n'

    def __init__(self, filePath, **kwargs):
        super().__init__(filePath, **kwargs)
        self.version = kwargs['version']
        self.uuid = None
        self._tempDir = tempfile.mkdtemp(suffix='.tmp', prefix='nv_epub_')
        self.prjDir = kwargs['prjDir']
        self._epubComponents = []
        self._ChIdsByContentFileNames = []
        self._contentParser = NovxToXhtml()

    def write(self):
        self._set_up()
        self.write_file('mimetype', self._MIMETYPE)
        self.uuid = str(uuid.uuid4())
        ChIdsByContentFileNames = self._write_chapters()
        self.write_css()
        self._write_toc_ncx(ChIdsByContentFileNames)
        self._write_content_opf(ChIdsByContentFileNames)
        self.write_file('META-INF/container.xml', self._CONTAINER_XML)

        #--- Pack the contents of the temporary directory into the EPUB file.
        workdir = os.getcwd()
        backedUp = False
        if os.path.isfile(self.filePath):
            try:
                os.replace(self.filePath, f'{self.filePath}.bak')
            except:
                raise RuntimeError(
                    f'{_("Cannot overwrite file")}: '
                    f'"{norm_path(self.filePath)}".'
                )
            else:
                backedUp = True
        try:
            with zipfile.ZipFile(self.filePath, 'w') as epubTarget:
                os.chdir(self._tempDir)
                for file in self._epubComponents:
                    epubTarget.write(file, compress_type=zipfile.ZIP_DEFLATED)
        except:
            os.chdir(workdir)
            if backedUp:
                os.replace(f'{self.filePath}.bak', self.filePath)
            raise RuntimeError(
                f'{_("Cannot create file")}: '
                f'"{norm_path(self.filePath)}".'
            )

        #--- Remove temporary data.
        os.chdir(workdir)
        self._tear_down()
        return f'{_("File written")}: "{norm_path(self.filePath)}".'

    def write_file(self, localPath, content):
        self._epubComponents.append(localPath)
        try:
            with open(
                f'{self._tempDir}/{localPath}',
                'w',
                encoding='utf-8'
            ) as f:
                f.write(content)
        except:
            raise RuntimeError(f'{_("Cannot write file")}: "{self._tempDir}/{localPath}"')

    def _convert_from_novx(self, text, **kwargs):
        append = kwargs.get('append', False)
        firstInChapter = kwargs.get('firstInChapter', False)
        isEpigraph = kwargs.get('isEpigraph', False)
        xml = kwargs.get('xml', False)

        if not text and not isEpigraph:
            return ''

        if xml:
            self._contentParser.feed(
                text,
                append,
                firstInChapter,
                isEpigraph,
                kwargs['pageIndex'],
            )
            return ''.join(self._contentParser.xhtmlLines)

        # Convert plain text into XML.
        lines = text.split('\n')
        if isEpigraph:
            # isEpigraph means that the text is an epigraph's source
            text = '<br />'.join(lines)
        else:
            text = ('</p><p>').join(lines)

        if isEpigraph:
            attr = ' class="epigraph_source"'
        else:
            attr = ''
        return (
            f'<p{attr}>{text}</p>'
        )
        return(text)

    def _escape_string(self, text):
        if text is None:
            return ''

        return sax.saxutils.escape(text)

    def _get_chapterMapping(self, chId):
        return {
            'ID': chId,
            'Title': self._escape_string(self.novel.chapters[chId].title),
            'Stylesheet': self.CSS_NAME,
        }

    def _get_footnoteMapping(self, noteIndex, ContentFileName, text):
        return {
            'Page': ContentFileName,
            'NoteIndex': noteIndex,
            'Text': text,
        }

    def _get_frontmatterMapping(self):
        return {
            'Title': self._escape_string(self.novel.title),
            'Author': self._escape_string(self.novel.authorName),
            'Stylesheet': self.CSS_NAME,
        }

    def _get_sectionMapping(
            self,
            scId,
            pageIndex,
            firstInChapter=False,
            isEpigraph=False,
        ):
        return {
            'SectionContent':self._convert_from_novx(
                self.novel.sections[scId].sectionContent,
                append=self.novel.sections[scId].appendToPrev,
                firstInChapter=firstInChapter,
                isEpigraph=isEpigraph,
                xml=True,
                pageIndex=pageIndex,
            ),
            'Desc':self._convert_from_novx(
                self.novel.sections[scId].desc,
                isEpigraph=isEpigraph,
                append=self.novel.sections[scId].appendToPrev,
            ),
        }

    def _get_sections(
            self,
            chId,
            pageIndex,
            isEpigraph,
    ):
        lines = []
        firstSectionInChapter = True
        for scId in self.novel.tree.get_children(chId):
            template = None
            sectionContent = self.novel.sections[scId].sectionContent
            if sectionContent is None:
                sectionContent = ''

            if self.novel.sections[scId].scType > 1:
                continue

            elif (
                self.novel.sections[scId].scType == 1
                or self.novel.chapters[chId].chType == 1
            ):
                # Unused section.
                isEpigraph = False
                continue

            else:
                # Normal section.
                if isEpigraph:
                    template = Template(self._epigraphTemplate)
                else:
                    template = Template(self._sectionTemplate)

            # Append section divider, if necessary.
            if not (
                isEpigraph
                or firstSectionInChapter
                or self.novel.sections[scId].appendToPrev
            ):
                lines.append(self._sectionDivider)

            # Apply template to any section.
            tempEpigraph = False
            tempFirstSection = firstSectionInChapter
            if isEpigraph:
                tempEpigraph = True
                tempFirstSection = False
            lines.append(
                template.safe_substitute(
                    self._get_sectionMapping(
                        scId,
                        pageIndex,
                        firstInChapter=tempFirstSection,
                        isEpigraph=tempEpigraph,
                    )
                )
            )
            isEpigraph = False
            if tempFirstSection:
                firstSectionInChapter = False

        return lines

    def _set_up(self):
        # Create and open a temporary directory for the files to zip.
        try:
            self._tear_down()
            os.makedirs(f'{self._tempDir}/META-INF')
            os.makedirs(f'{self._tempDir}/OEBPS/styles')
            os.makedirs(f'{self._tempDir}/OEBPS/text')
        except:
            raise RuntimeError(
                f'{_("Cannot create directory")}: '
                f'"{norm_path(self._tempDir)}".'
            )

    def _tear_down(self):
        # Delete the temporary directory containing the
        # unpacked ODF directory structure.
        try:
            rmtree(self._tempDir)
        except:
            pass

    def _write_chapters(self):
        """Process the chapters and nested sections.
        
        Write an xhtml file for each chapter.
        Return a list of file names.
        """

        def write_file(pageIndex, text, chId):
            contentFileName = f'content{pageIndex:04}.xhtml'
            ChIdsByContentFileNames[contentFileName] = chId
            self.write_file(f'OEBPS/text/{contentFileName}', text)

        pageIndex = 0
        ChIdsByContentFileNames = {}
        contentIds = ['frontmatter']
        contentIds.extend(self.novel.tree.get_children(CH_ROOT))

        for chId in contentIds:
            lines = []
            if not chId in self.novel.chapters:
                mapping = self._get_frontmatterMapping()
                lines.append(
                    Template(self._frontmatter).safe_substitute(
                        mapping
                    )
                )

            elif self.novel.chapters[chId].chType != 0:
                continue

            else:
                if self.novel.chapters[chId].chLevel == 1:
                    template = Template(self._partTemplate)
                else:
                    template = Template(self._chapterTemplate)
                mapping = self._get_chapterMapping(chId)
                lines.append(
                    template.safe_substitute(mapping)
                )

                #--- Process sections.
                lines.extend(
                    self._get_sections(
                        chId,
                        pageIndex + 1,
                        self.novel.chapters[chId].hasEpigraph,
                    )
                )
            if not lines:
                continue

            fileHeader = Template(self._fileHeader).safe_substitute(
                mapping
            )
            text = f'{fileHeader}{"".join(lines)}{self._fileFooter}'
            pageIndex += 1
            write_file(pageIndex, text, chId)

        #--- Write footnotes, if any.
        if self._contentParser.footnotes:
            lines = []
            for i, footnote in enumerate(self._contentParser.footnotes):
                pageIndex, text = footnote
                noteIndex = i + 1
                mapping = self._get_footnoteMapping(
                    f'{noteIndex:04}',
                    f'content{pageIndex:04}.xhtml',
                    text,
                )
                lines.append(
                    Template(self._FOOTNOTE).safe_substitute(mapping)
                )
            fileHeader = Template(self._fileHeader).safe_substitute(
                {'Title': 'Footnotes', 'Stylesheet': self.CSS_NAME, }
            )
            text = f'{fileHeader}{"".join(lines)}{self._fileFooter}'
            self.write_file(f'OEBPS/text/footnotes.xhtml', text)

        return ChIdsByContentFileNames

    def _write_content_opf(self, ChIdsByContentFileNames):
        opfMapping = {
            'Uuid': self.uuid,
            'Version': self.version,
            'Date': datetime.date.today().isoformat(),
            'Author': self._escape_string(self.novel.authorName),
            'Language': self.novel.languageCode,
            'Title': self._escape_string(self.novel.title),
            'Coverpage': 'text/content0001.xhtml'
        }
        contentOpfLines = [
            Template(self._CONTENT_OPF_HEADER).safe_substitute(opfMapping),
        ]
        contentOpfLines.append('    <manifest>')
        contentOpfLines.append(
            '        <item id="ncx" href="toc.ncx" '
            'media-type="application/x-dtbncx+xml"/>'
        )
        contentOpfLines.append(
            f'        <item id="{self.CSS_NAME}" '
            f'href="styles/{self.CSS_NAME}" media-type="text/css"/>'
        )
        for fileName in ChIdsByContentFileNames:
            contentOpfLines.append(
                f'        <item id="{fileName}" href="text/{fileName}" '
                'media-type="application/xhtml+xml"/>'

            )
        if self._contentParser.footnotes:
            contentOpfLines.append(
                '        <item id="footnotes.xhtml" '
                'href="text/footnotes.xhtml" '
                'media-type="application/xhtml+xml"/>'
            )
        contentOpfLines.append('    </manifest>')
        contentOpfLines.append('    <spine toc="ncx">')
        for fileName in ChIdsByContentFileNames:
            contentOpfLines.append(
                f'       <itemref idref="{fileName}"/>'
            )
        if self._contentParser.footnotes:
            contentOpfLines.append(
                '       <itemref idref="footnotes.xhtml" linear="no"/>'
            )
        contentOpfLines.append('    </spine>')
        contentOpfLines.append(
            Template(self._CONTENT_OPF_FOOTER).safe_substitute(opfMapping),
        )
        self.write_file(f'OEBPS/content.opf', '\n'.join(contentOpfLines))

    def _write_toc_ncx(self, ChIdsByContentFileNames):
        ncxMapping = {
            'Uuid': self.uuid,
            'Title': self._escape_string(self.novel.title),
        }
        tocNcxLines = [
            Template(self._TOC_NCX_HEADER).safe_substitute(ncxMapping),
        ]
        i = 0
        for ContentFileName in ChIdsByContentFileNames:
            chId = ChIdsByContentFileNames[ContentFileName]
            if not chId in self.novel.chapters:
                continue

            i += 1
            order = str(i)
            navPointMapping = {
                'NavpointID': f'navPoint-{order}',
                'Playorder': order,
                'Title': self._escape_string(self.novel.chapters[chId].title),
                'Filename': ContentFileName,
                'HeadingID': chId,
            }
            tocNcxLines.append(
                Template(self._TOC_NAV_POINT).safe_substitute(navPointMapping),
            )
        tocNcxLines.append(
            Template(self._TOC_NCX_FOOTER).safe_substitute(ncxMapping),
        )
        self.write_file(f'OEBPS/toc.ncx', '\n'.join(tocNcxLines))
