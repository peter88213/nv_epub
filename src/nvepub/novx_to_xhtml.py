"""Provide a class for parsing novx section content, converting it to XHTML.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_epub
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from xml import sax


class NovxToXhtml(sax.ContentHandler):
    """A parser to convert novx markup to odt markup."""

    def __init__(self):
        super().__init__()
        self.xhtmlLines = None
        self._languages = None
        self._indentParagraph = None
        self._note = None
        self._comment = None
        self._firstParagraphInChapter = None
        self._spanLevel = None

    def feed(
        self,
        xmlString,
        languages,
        append,
        firstInChapter,
        isEpigraph,
    ):
        """Feed a string file to the parser.
        
        Positional arguments:
            xmlString: str -- content as XML string.
            languages: list[str] -- Ordered list of the document's languages.
            append: boolean -- indent the first paragraph, if True.
            firstInChapter: boolean -- apply the "Chapter beginning" 
                                       paragraph style, if True.
            isEpigraph: bool -- if True, use "Epigraph" paragraph styles.            
        """
        self._languages = languages
        self._firstParagraphInChapter = firstInChapter
        self._indentParagraph = append and not isEpigraph
        self._isEpigraph = isEpigraph
        self._note = False
        self._spanLevel = 0
        self._comment = False
        self.xhtmlLines = []
        if xmlString:
            sax.parseString(f'<content>{xmlString}</content>', self)

    def characters(self, content):
        """Receive notification of character data.
        
        Overrides the xml.sax.ContentHandler method             
        """
        if self._comment:
            return

        if self._note:
            return

        content = sax.saxutils.escape(content)
        self.xhtmlLines.append(content)
        self._indentParagraph = True

    def endElement(self, name):
        """Signals the end of an element in non-namespace mode.
        
        Overrides the xml.sax.ContentHandler method     
        """
        if name == 'p':
            while self._spanLevel > 0:
                self._spanLevel -= 1
                self.xhtmlLines.append('</span>')
            self.xhtmlLines.append('</p>\n')
            return

        if name in ('em', 'strong', 'span'):
            self.xhtmlLines.append(f'</{name}>')
            return

        if name == 'comment':
            self._comment = False
            return

        if name == 'note':
            self._note = False

        if name in (
            'h5',
            'h6',
            'h7',
            'h8',
            'h9',
        ):
            while self._spanLevel > 0:
                self._spanLevel -= 1
                self.xhtmlLines.append('</span>')
            self.xhtmlLines.append('</p>\n')
            self._indentParagraph = False
            return

        if name == 'li':
            self.xhtmlLines.append('</li>\n')
            return

        if name == 'ul':
            self._list = False
            self._indentParagraph = False
            self.xhtmlLines.append('</ul>\n')
            return

    def startElement(self, name, attrs):
        """Signals the start of an element in non-namespace mode.
        
        Overrides the xml.sax.ContentHandler method             
        """
        xmlAttributes = {}
        for attribute in attrs.items():
            attrKey, attrValue = attribute
            xmlAttributes[attrKey] = attrValue

        if name == 'p':
            if xmlAttributes.get('style', None) == 'quotations':
                self.xhtmlLines.append(
                    '<p class="Quotations">'
                )
            elif self._note:
                return

            elif self._comment:
                self.xhtmlLines.append('<p>')

            elif self._firstParagraphInChapter:
                self.xhtmlLines.append(
                    f'<p class="Chapter_beginning">'
                )
            elif self._isEpigraph:
                self.xhtmlLines.append(
                    f'<p class="Epigraph">'
                )
            elif self._indentParagraph:
                self.xhtmlLines.append(
                    '<p class="First_line_indent">'
                )
            else:
                self.xhtmlLines.append(
                    '<p class="Text_body">'
                )
            if not self._isEpigraph:
                self._firstParagraphInChapter = False
                self._indentParagraph = False

            language = xmlAttributes.get('xml:lang', None)
            if language:
                self.xhtmlLines.append(f'<span xml:lang="{language}">')
                self._spanLevel += 1
            return

        if name == 'em':
            self.xhtmlLines.append(
                '<em>'
            )
            return

        if name == 'strong':
            self.xhtmlLines.append(
                '<strong>'
            )
            return

        if name == 'span':
            language = xmlAttributes.get('xml:lang', None)
            if language:
                self.xhtmlLines.append(f'<span xml:lang="{language}">')
            return

        if name == 'comment':
            self._comment = True
            return

        if name == 'note':
            self._note = True
            return

        if name in (
            'h5',
            'h6',
            'h7',
            'h8',
            'h9',
        ):
            level = name[-1]
            self.xhtmlLines.append(
                f'<p class="Heading_{level}">'
            )
            language = xmlAttributes.get('xml:lang', None)
            if language:
                self.xhtmlLines.append(f'<span xml:lang="{language}">')
                self._spanLevel += 1
            return

        if name == 'ul':
            self._list = True
            self.xhtmlLines.append('<ul>')
            return

        if name == 'li':
            self.xhtmlLines.append('<li>')
