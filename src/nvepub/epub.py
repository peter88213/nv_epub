"""Provide a class for EPUB representation.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_epub
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from shutil import rmtree
import tempfile
import zipfile

from nvepub.nvepub_globals import EPUB_SUFFIX
from nvepub.nvepub_locale import _
from nvepub.stylesheet import STYLESHEET
from nvlib.model.file.file_export import FileExport
from nvlib.novx_globals import norm_path
from nvlib.novx_globals import CH_ROOT
from string import Template


class Epub(FileExport):

    DESCRIPTION = 'EPUB Ebook'
    EXTENSION = '.epub'
    SUFFIX = EPUB_SUFFIX

    _MIMETYPE = 'application/epub+zip'
    _CONTAINER_XML = (
        '<?xml version="1.0"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '    <rootfiles>\n'
        '        <rootfile full-path='
        '"OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
        '   </rootfiles>\n'
        '</container>\n'
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
    _sectionTemplate = '$SectionContent\n'
    _sectionDivider = '<h4">* * *</h4>\n'

    def __init__(self, filePath, **kwargs):
        """Create a temporary directory for zipfile generation.
        
        Positional arguments:
            filePath: str -- path to the file 
                             represented by the Novel instance.
            
        Optional arguments:
            kwargs -- keyword arguments to be used by subclasses.            

        Extends the superclass constructor,        
        """
        super().__init__(filePath, **kwargs)
        self._tempDir = tempfile.mkdtemp(suffix='.tmp', prefix='nv_epub_')
        self._originalPath = self._filePath
        self._epubComponents = [
            'mimetype',
            'META-INF/container.xml',
            'OEBPS/styles/style001.css',
        ]

    def write(self):
        self._set_up()
        #--- Pack the contents of the temporary directory into the ODF file.
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
        except NotImplementedError:
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

    def _get_chapters(self):
        """Process the chapters and nested sections.
        
        Return a list of strings, or a message, depending 
        on the _perChapter variable.
        Extends the superclass method for the 'document per chapter' option.
        """
        textDir = f'{self._tempDir}/OEBPS/text'
        chapterNumber = 0
        sectionNumber = 0
        wordsTotal = 0
        contentIndex = 0
        for chId in self.novel.tree.get_children(CH_ROOT):
            lines = []
            dispNumber = 0
            if not self.chapterFilter.accept(self, chId):
                continue
            # The order counts; be aware that "Todo" and "Notes" chapters are
            # always unused.

            # Has the chapter only sections not to be exported?
            template = None
            if self.novel.chapters[chId].chType != 0:
                # Chapter is unused.
                if self._unusedChapterTemplate:
                    template = Template(self._unusedChapterTemplate)
            elif self.novel.chapters[chId].chLevel == 1 and self._partTemplate:
                template = Template(self._partTemplate)
            else:
                template = Template(self._chapterTemplate)
                chapterNumber += 1
                dispNumber = chapterNumber
            if template is not None:
                lines.append(
                    template.safe_substitute(
                        self._get_chapterMapping(chId, dispNumber)
                    )
                )

            # Process sections.
            sectionLines, sectionNumber, wordsTotal = self._get_sections(
                chId,
                sectionNumber,
                wordsTotal,
                self.novel.chapters[chId].hasEpigraph,
                )
            lines.extend(sectionLines)

            # Process chapter ending.
            template = None
            if self.novel.chapters[chId].chType != 0:
                if self._unusedChapterEndTemplate:
                    template = Template(self._unusedChapterEndTemplate)
            elif self._chapterEndTemplate:
                template = Template(self._chapterEndTemplate)
            if template is not None:
                lines.append(
                    template.safe_substitute(
                        self._get_chapterMapping(chId, dispNumber)
                    )
                )
            if not lines:
                continue

            text = f'{self._fileHeader}{"".join(lines)}{self._fileFooter}'

            contentIndex += 1
            textPath = (f'{textDir}/content{contentIndex:04}.xhtml')
            self._epubComponents.append(f'OEBPS/text/content{contentIndex:04}.xhtml')
            try:
                with open(textPath, 'w', encoding='utf-8') as f:
                    f.write(text)
            except:
                raise RuntimeError(f'Cannot write "{norm_path(textPath)}".')

    def _set_up(self):
        # Helper method for ZIP file generation.
        # Prepare the temporary directory containing the internal structure
        # of an EPUB file.
        # Raise the "RuntimeError" exception in case of error.

        #--- Create and open a temporary directory for the files to zip.
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
        #--- Generate mimetype.
        try:
            with open(
                f'{self._tempDir}/mimetype',
                'w',
                encoding='utf-8'
            ) as f:
                f.write(self._MIMETYPE)
        except:
            raise RuntimeError(f'{_("Cannot write file")}: "mimetype"')

        #--- Generate META-INF\container.xml.
        try:
            with open(
                f'{self._tempDir}/META-INF/container.xml',
                'w',
                encoding='utf-8'
            ) as f:
                f.write(self._CONTAINER_XML)
        except:
            raise RuntimeError(f'{_("Cannot write file")}: "container.xml"')

        #--- Generate OEBPS/styles/style001.css.
        try:
            with open(
                f'{self._tempDir}/OEBPS/styles/style001.css',
                'w',
                encoding='utf-8'
            ) as f:
                f.write(STYLESHEET)
        except:
            raise RuntimeError(f'{_("Cannot write file")}: "style001.css"')

        #--- Generate OEBPS/text/contentxxxx.xhtml.
        self._get_chapters()

    def _tear_down(self):
        # Delete the temporary directory containing the
        # unpacked ODF directory structure.
        try:
            rmtree(self._tempDir)
        except:
            pass

