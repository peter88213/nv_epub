"""Provide an Epub mixin class for the container.xml representation.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""


class ContainerXml:

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

    def write_container_xml(self):
        self.write_file('META-INF/container.xml', self._CONTAINER_XML)
