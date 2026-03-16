"""Export EPUB file

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_epub
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import sys

from nvepub.epub import Epub
from nvepub.nvepub_globals import EPUB_SUFFIX
from nvlib.alternative_ui.ui_tk import UiTk
from testlib.novx_converter import NovxConverter

SUFFIX = EPUB_SUFFIX


def run(sourcePath, suffix=''):
    ui = UiTk('novelibre export')
    converter = NovxConverter()
    converter.EXPORT_TARGET_CLASSES.append(Epub)
    converter.ui = ui
    kwargs = {
        'suffix': suffix,
        'version':'0.0',
    }
    converter.run(sourcePath, **kwargs)
    ui.start()


if __name__ == '__main__':
    run(sys.argv[1], SUFFIX)
