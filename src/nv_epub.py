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
from nvlib.controller.plugin.plugin_base import PluginBase
from nvlib.novx_globals import norm_path
from nvepub.epub import Epub


class Plugin(PluginBase):
    """Template plugin class."""
    VERSION = '@release'
    API_VERSION = '5.0'
    DESCRIPTION = 'EPUB exporter'
    URL = 'https://github.com/peter88213/nv_epub'

    HELP_URL = 'https://github.com/peter88213/nv_epub/tree/main/docs/nv_epub'

    def install(self, model, view, controller):
        """Install the plugin.
        
        Positional arguments:
            model -- reference to the novelibre main model instance.
            view -- reference to the novelibre main view instance.
            controller -- reference to the novelibre main controller instance.

        Extends the superclass method.
        """
        super().install(model, view, controller)

        #--- Configure the main menu.

        # Add an entry to the "Export" menu.
        pos = self._ui.exportMenu.index(_('Options'))
        self._ui.exportMenu.insert_separator(pos)
        label = f"EPUB {_('Ebook')}"
        self._ui.exportMenu.insert_command(
            pos,
            label=label,
            command=self._export_epub,
        )
        self._ui.exportMenu.disableOnLock.insert(label)

        # Add an entry to the Help menu.
        label = _('nv_epub Online help')
        self._ui.helpMenu.add_command(
            label=label,
            command=self.open_help,
        )

    def _export_epub(self):
        if self._mdl.prjFile.filePath is None:
            return False

        path, __ = os.path.splitext(self._mdl.prjFile.filePath)
        EpubPath = f'{path}{Epub.EXTENSION}'
        if os.path.isfile(EpubPath):
            if not self._ui.ask_yes_no(
                message=_('Overwrite existing Ebook?'),
                detail=norm_path(EpubPath)
            ):
                self._ui.set_status(f'#{_("Action canceled by user")}.')
                return False

        self._ui.restore_status()
        self._ui.propertiesView.apply_changes()
        EpubFile = Epub(EpubPath)
        EpubFile.novel = self._mdl.novel
        try:
            EpubFile.write()
        except TypeError as ex:
            self._ui.set_status(f'!{str(ex)}')
            return False

        self._ui.set_status(f'{_("File exported")}: {EpubPath}')
        return True

    def open_help(self):
        webbrowser.open(self.HELP_URL)

