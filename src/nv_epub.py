"""An EPUB exporter plugin for novelibre.

Requires Python 3.7+
Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_epub
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""
import os
import webbrowser

from nvepub.nvepub_locale import _
# this should be the first import
from nvepub.epub import Epub
from nvlib.controller.plugin.plugin_base import PluginBase
from nvlib.novx_globals import norm_path


class Plugin(PluginBase):
    """Template plugin class."""
    VERSION = '@release'
    API_VERSION = '5.53'
    DESCRIPTION = 'EPUB e-book exporter'
    URL = 'https://github.com/peter88213/nv_epub'
    HELP_URL = 'https://peter88213.github.io/nv_epub/help/'

    FEATURE = f"EPUB {_('e-book')}"

    def install(self, model, view, controller):
        """Install the plugin.
        
        Positional arguments:
            model -- reference to the novelibre main model instance.
            view -- reference to the novelibre main view instance.
            controller -- reference to the novelibre main controller instance.

        Extends the superclass method.
        """
        super().install(model, view, controller)
        self._icon = self._get_icon('nv_epub.png')

        #--- Configure the main menu.

        # Add an entry to the "Export" menu.
        pos = self._ui.exportMenu.index(_('Options'))
        self._ui.exportMenu.insert_separator(pos)
        label = self.FEATURE
        self._ui.exportMenu.insert_command(
            pos,
            label=label,
            image=self._icon,
            compound='left',
            command=self._export_epub,
        )
        self._ui.exportMenu.disableOnClose.append(label)

        # Add an entry to the Help menu.
        label = _('EPUB export plugin Online help')
        self._ui.helpMenu.add_command(
            label=label,
            image=self._icon,
            compound='left',
            command=self.open_help,
        )

    def _export_epub(self):

        def sanitize_path(pathStr):
            for c in  ('\\', '/', ':', '*', '?', '"', '<', '>', '|'):
                pathStr = pathStr.replace(c, '_')
            return pathStr

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
                title=self.FEATURE,
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
                title=self.FEATURE,
            ):
                self._ui.set_status(f'#{_("Action canceled by user")}.')
                return False

        epubFile = Epub(
            epubPath,
            version=self.VERSION,
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

    def open_help(self):
        webbrowser.open(self.HELP_URL)

