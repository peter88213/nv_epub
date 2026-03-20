"""Provide a class for EPUB representation.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_epub
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from shutil import copy2
from shutil import rmtree
from string import Template
import tempfile
import uuid
from xml import sax
import zipfile

from nvepub.content_opf import ContentOpf
from nvepub.mimetype import Mimetype
from nvepub.novx_to_xhtml import NovxToXhtml
from nvepub.nvepub_locale import _
from nvepub.stylesheet import Stylesheet
from nvepub.toc import Toc
from nvlib.novx_globals import CH_ROOT
from nvlib.novx_globals import norm_path
from nvepub.container_xml import ContainerXml


class Epub(Stylesheet, Toc, ContentOpf, Mimetype, ContainerXml):

    DESCRIPTION = 'EPUB e-book'
    EXTENSION = '.epub'

    CSS_NAME = 'nv_epub.css'
    _COVER_FILE = 'cover.jpg'
    _COVER_PAGE_NAME = 'coverpage.xhtml'
    _FOOTNOTES_PAGE_NAME = 'footnotes.xhtml'

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
        '    <div>    <img id="cover" height="100%" alt="Cover" '
        'src="../$Cover" />\n'
        '    </div>\n'
        '  </body>\n'
        '</html>\n'

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
        self.novel = None
        self.filePath = filePath

        self.version = kwargs['version']
        self.uuid = None
        self._tempDir = tempfile.mkdtemp(suffix='.tmp', prefix='nv_epub_')
        self.prjDir = kwargs['prjDir']
        self._epubComponents = []
        self._ChIdsByContentFileNames = []
        self._contentParser = NovxToXhtml()
        self._hasCover = False
        self._coverPath = self._coverPagePath = 'text/content0001.xhtml'

    def write(self):
        self._set_up()
        self.write_mimetype()
        self._include_cover()
        self.uuid = str(uuid.uuid4())
        ChIdsByContentFileNames = self._write_chapters()
        self.write_css()
        # method of the Stylesheet mixin
        self.write_toc_ncx(ChIdsByContentFileNames)
        self.write_content_opf(ChIdsByContentFileNames)
        self.write_container_xml()

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

    def _include_cover(self):
        prjCoverPath = os.path.join(self.prjDir, self._COVER_FILE)
        if not os.path.isfile(prjCoverPath):
            return

        coverDir = f'{self._tempDir}/OEBPS/images'
        os.makedirs(coverDir)
        copy2(prjCoverPath, coverDir)
        self._epubComponents.append(f'OEBPS/images/{self._COVER_FILE}')
        self._coverPath = f'images/{self._COVER_FILE}'
        self._coverPagePath = f'text/{self._COVER_PAGE_NAME}'
        self._hasCover = True
        text = Template(self._COVER_PAGE).safe_substitute(
            {'Cover': self._coverPath, }
        )
        self.write_file(f'OEBPS/{self._coverPagePath}', text)

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

        def write_chapter_file(pageIndex, text, chId):
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
            write_chapter_file(pageIndex, text, chId)

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
            self.write_file(f'OEBPS/text/{self._FOOTNOTES_PAGE_NAME}', text)

        return ChIdsByContentFileNames

