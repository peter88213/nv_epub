"""Provide a class for EPUB representation.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_epub
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from shutil import rmtree
import tempfile
import zipfile

from nvepub.nvepub_locale import _
from nvepub.stylesheet import STYLESHEET
from nvlib.model.file.file_export import FileExport
from nvlib.novx_globals import norm_path


class Epub(FileExport):

    DESCRIPTION = 'EPUB Ebook'
    EXTENSION = '.epub'

    _EPUB_COMPONENTS = [
        'mimetype',
        'META-INF/container.xml',
        'OEBPS/styles/style001.css',
    ]
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
        self._tempDir = tempfile.mkdtemp(suffix='.tmp', prefix='e_')
        self._originalPath = self._filePath

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
                for file in self._EPUB_COMPONENTS:
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

    def _tear_down(self):
        # Delete the temporary directory containing the
        # unpacked ODF directory structure.
        try:
            rmtree(self._tempDir)
        except:
            pass

