"""Provide an EPUP exporter service class for novelibre.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
import re

from nvepub.epub import Epub
from nvepub.nvepub_locale import _
from nvlib.controller.services.service_base import ServiceBase
from nvlib.novx_globals import norm_path


class EpubExporter(ServiceBase):

    def run(self, windowTitle, appVersion):

        def sanitize_path(pathStr):
            return re.sub(r'[\/\\\?\*:\|"><]', '_', pathStr)

        if self._mdl.prjFile is None:
            return False

        if self._mdl.prjFile.filePath is None:
            return False

        self._ui.restore_status()
        self._ui.propertiesView.apply_changes()
        if self._mdl.isModified:
            if not self._ui.ask_yes_no(
                message=_('Save changes?'),
                detail=f"{_('There are unsaved changes')}.",
                title=windowTitle,
            ):
                self._ui.set_status(f'#{_("Action canceled by user")}.')
                return False

            self._ctrl.save_project()

        authorName = self._mdl.novel.authorName
        if not authorName:
            authorName = _('Unknown')
        fileNameHead = sanitize_path(
            f'{self._mdl.novel.title} - {authorName}'
        )
        fileName = f'{fileNameHead}{Epub.EXTENSION}'
        prjDir = os.path.dirname(self._mdl.prjFile.filePath)
        epubPath = os.path.join(prjDir, fileName)
        if os.path.isfile(epubPath):
            if not self._ui.ask_yes_no(
                message=_('Overwrite existing e-book?'),
                detail=norm_path(epubPath),
                title=windowTitle,
            ):
                self._ui.set_status(f'#{_("Action canceled by user")}.')
                return False

        epubFile = Epub(
            epubPath,
            version=appVersion,
            prjDir=os.path.dirname(self._mdl.prjFile.filePath),
        )
        epubFile.novel = self._mdl.novel
        try:
            epubFile.write()
        except Exception as ex:
            self._ui.set_status(f'!{str(ex)}')
            return False

        self._ui.set_status(f'{_("File exported")}: {epubPath}')
        return True

