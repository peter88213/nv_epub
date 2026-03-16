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
import zipfile

from nvepub.nvepub_globals import EPUB_SUFFIX
from nvepub.nvepub_locale import _
from nvepub.stylesheet import STYLESHEET
from nvlib.model.file.file import File
from nvlib.novx_globals import CH_ROOT
from nvlib.novx_globals import norm_path


class Epub(File):

    DESCRIPTION = 'EPUB Ebook'
    EXTENSION = '.epub'
    SUFFIX = EPUB_SUFFIX

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

    _fileHeader = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"\n'
        '    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
        '<html xmlns="http://www.w3.org/1999/xhtml">\n'
        '<head>\n'
        '<link rel="stylesheet" '
        'href="../styles/style001.css" type="text/css" />\n'
        '<title></title>\n'
        '</head>\n'
        '<body>\n'
    )
    _fileFooter = (
        '</body>\n'
        '</html>\n'
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
        self._originalPath = self._filePath
        self._epubComponents = []
        self._ChIdsByContentFileNames = []

    def write(self):
        self._set_up()
        self.uuid = str(uuid.uuid4())
        ChIdsByContentFileNames = self._write_chapters()
        self._write_file(f'OEBPS/styles/style001.css', STYLESHEET)
        self._write_toc_ncx(ChIdsByContentFileNames)
        self._write_content_opf(ChIdsByContentFileNames)
        self._write_file('META-INF/container.xml', self._CONTAINER_XML)
        self._write_file('mimetype', self._MIMETYPE)

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

    def _convert_from_novx(self, text, **kwargs):
        if text is None:
            text = ''
        return(text)

    def _get_sectionMapping(
            self,
            scId,
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
        sectionNumber = 0
        wordsTotal = 0
        contentIndex = 0
        ChIdsByContentFileNames = {}

        for chId in self.novel.tree.get_children(CH_ROOT):
            lines = []
            template = None
            if self.novel.chapters[chId].chType != 0:
                continue

            if self.novel.chapters[chId].chLevel == 1 and self._partTemplate:
                template = Template(self._partTemplate)
            else:
                template = Template(self._chapterTemplate)
            lines.append(
                template.safe_substitute(
                    {
                        'ID': chId,
                        'Title': self.novel.chapters[chId].title,
                    }
                )
            )

            # Process sections.
            sectionLines = self._get_sections(
                chId,
                self.novel.chapters[chId].hasEpigraph,
            )
            lines.extend(sectionLines)

            if not lines:
                continue

            text = f'{self._fileHeader}{"".join(lines)}{self._fileFooter}'

            contentIndex += 1
            contentFileName = f'content{contentIndex:04}.xhtml'
            ChIdsByContentFileNames[contentFileName] = chId
            self._write_file(f'OEBPS/text/{contentFileName}', text)

        return ChIdsByContentFileNames

    def _write_content_opf(self, ChIdsByContentFileNames):
        opfMapping = {
            'Uuid': self.uuid,
            'Version': self.version,
            'Date': datetime.date.today().isoformat(),
            'Author': self.novel.authorName,
            'Language': self.novel.languageCode,
            'Title': self.novel.title,
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
            '        <item id="style001.css" '
            'href="styles/style001.css" media-type="text/css"/>'
        )
        for fileName in ChIdsByContentFileNames:
            contentOpfLines.append(
                f'        <item id="{fileName}" href="text/{fileName}" '
                'media-type="application/xhtml+xml"/>'

            )
        contentOpfLines.append('    <manifest>')
        contentOpfLines.append('    <spine toc="ncx">')
        for fileName in ChIdsByContentFileNames:
            contentOpfLines.append(
                f'       <itemref idref="{fileName}"/>'
            )
        contentOpfLines.append('    </spine>')
        contentOpfLines.append(
            Template(self._CONTENT_OPF_FOOTER).safe_substitute(opfMapping),
        )
        self._write_file(f'OEBPS/content.opf', '\n'.join(contentOpfLines))

    def _write_file(self, localPath, content):
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

    def _write_toc_ncx(self, ChIdsByContentFileNames):
        ncxMapping = {
            'Uuid': self.uuid,
            'Title': self.novel.title,
        }
        tocNcxLines = [
            Template(self._TOC_NCX_HEADER).safe_substitute(ncxMapping),
        ]
        for i, ContentFileName in enumerate(ChIdsByContentFileNames):
            chId = ChIdsByContentFileNames[ContentFileName]
            order = str(i + 1)
            navPointMapping = {
                'NavpointID': f'navPoint-{order}',
                'Playorder': order,
                'Title': self.novel.chapters[chId].title,
                'Filename': ContentFileName,
                'HeadingID': chId,
            }
            tocNcxLines.append(
                Template(self._TOC_NAV_POINT).safe_substitute(navPointMapping),
            )
        tocNcxLines.append(
            Template(self._TOC_NCX_FOOTER).safe_substitute(ncxMapping),
        )
        self._write_file(f'OEBPS/toc.ncx', '\n'.join(tocNcxLines))
