"""Plugin template for novelibre.

Requires Python 3.7+
Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_plugin
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
import webbrowser

from nvplugin.nvplugin_locale import _
# this should be the first import
from nvlib.controller.plugin.plugin_base import PluginBase


class Plugin(PluginBase):
    """Template plugin class."""
    VERSION = '@release'
    API_VERSION = '5.0'
    DESCRIPTION = 'Plugin template'
    URL = 'https://github.com/peter88213/nv_plugin'

    HELP_URL = 'https://github.com/peter88213/nv_plugin/tree/main/docs/nv_plugin'

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

        # Add an entry to the Help menu.
        label = _('nv_plugin Online help')
        self._ui.helpMenu.add_command(
            label=label,
            command=self.open_help,
        )

    def open_help(self):
        webbrowser.open(self.HELP_URL)

