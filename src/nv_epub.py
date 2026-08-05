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
from nvepub.nvepub_locale import _
# this should be the first import

from nvepub.epub_exporter import EpubExporter
from nvlib.controller.plugin.plugin_base import PluginBase


class Plugin(PluginBase):
    """EPUB exporter plugin class."""
    VERSION = '@release'
    API_VERSION = '5.63'
    DESCRIPTION = 'EPUB e-book exporter'
    URL = 'https://github.com/peter88213/nv_epub'
    HELP_PAGE = 'nv_epub'

    FEATURE = f"EPUB {_('e-book')}"

    DTD_MAJOR_VERSION = 1
    DTD_MINOR_VERSION = 10
    # DTD version supported by the plugin.

    def install(self, model, view, controller):
        """Install the plugin at runtime.
        
        Positional arguments:
            model -- reference to the novelibre main model instance.
            view -- reference to the novelibre main view instance.
            controller -- reference to the novelibre main controller instance.

        Extends the superclass method.
        """
        # Raise an exception if the plugin is not compatible
        # with the DTD supported by novelibre.
        (
            novelibreDtdMajorVersion,
            novelibreDtdMinorVersion
        ) = model.nvService.get_novx_dtd_version()
        if (
            novelibreDtdMajorVersion != self.DTD_MAJOR_VERSION or
            novelibreDtdMinorVersion > self.DTD_MINOR_VERSION
        ):
            raise RuntimeError(
                'Outdated: Current novx file version not supported.'
            )

        super().install(model, view, controller)
        self._icon = self._get_icon('nv_epub.png')

        self.exporter = EpubExporter(model, view, controller)

        #--- Configure the user interface.

        def run():
            self.exporter.run(self.FEATURE, self.VERSION)

        # Add an entry to the Export menu.
        pos = self._ui.exportMenu.index(_('Options'))
        self._ui.exportMenu.insert_separator(pos)
        label = self.FEATURE
        self._ui.exportMenu.insert_command(
            pos,
            label=label,
            image=self._icon,
            compound='left',
            command=run,
        )
        self._ui.exportMenu.disableOnClose.append(label)

        self._add_help_menu_entry(_('EPUB export plugin help'))

