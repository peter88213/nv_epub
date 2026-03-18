"""Provide a class for parsing novx section content, converting it to XHTML.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_epub
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from xml import sax


class NovxToXhtml(sax.ContentHandler):
    """A parser to convert novx XML markup to XHTML."""

    def __init__(self):
        super().__init__()
        self._noteLines = []
        self.xhtmlLines = []
        self.footnotes = []
        self._indentParagraph = None
        self._list = None
        self._note = None
        self._skipElement = None
        self._quotations = None
        self._firstParagraphInChapter = None

    def feed(
        self,
        xmlString,
        append,
        firstInChapter,
        isEpigraph,
    ):
        """Feed a string file to the parser.
        
        Positional arguments:
            xmlString: str -- content as XML string.
            append: boolean -- indent the first paragraph, if True.
            firstInChapter: boolean -- apply the "Chapter beginning" 
                                       paragraph style, if True.
            isEpigraph: bool -- if True, use "Epigraph" paragraph styles.            
        """
        self._firstParagraphInChapter = firstInChapter
        self._indentParagraph = append and not isEpigraph
        self._isEpigraph = isEpigraph
        self._quotations = False
        self._list = False
        self._note = False
        self._skipElement = False
        self._noteLines.clear()
        self.xhtmlLines.clear()
        self.footnotes.clear()
        if xmlString:
            sax.parseString(f'<content>{xmlString}</content>', self)

    def characters(self, content):
        """Receive notification of character data.
        
        Overrides the xml.sax.ContentHandler method             
        """
        if self._skipElement:
            return

        content = sax.saxutils.escape(content)
        if self._note:
            self._noteLines.append(content)
        else:
            self.xhtmlLines.append(content)
            self._indentParagraph = not self._quotations

    def endElement(self, name):
        """Signals the end of an element in non-namespace mode.
        
        Overrides the xml.sax.ContentHandler method     
        """
        if name in ('comment', 'note-citation'):
            self._skipElement = False
            return

        if self._skipElement:
            return

        if self._note:
            lines = self._noteLines
        else:
            lines = self.xhtmlLines

        if name == 'p':
            if self._list:
                return

            lines.append('&nbsp;</p>\n')
            self._quotations = False
            return

        if name in ('em', 'strong', 'span'):
            lines.append(f'</{name}>')
            return

        if name == 'note':
            self.footnotes.append(''.join(self._noteLines))
            self._noteLines.clear()
            self._note = False
            return

        if name in ('h5', 'h6', 'h7', 'h8', 'h9',):
            self.xhtmlLines.append('</p>\n')
            self._indentParagraph = False
            return

        if name == 'li':
            self.xhtmlLines.append(f'</{name}>\n')
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
        if self._skipElement:
            return

        xmlAttributes = {}
        for attribute in attrs.items():
            attrKey, attrValue = attribute
            xmlAttributes[attrKey] = attrValue
        language = xmlAttributes.get('xml:lang', None)
        if language:
            lang = f' xml:lang="{language}"'
        else:
            lang = ''

        if self._note:
            lines = self._noteLines
        else:
            lines = self.xhtmlLines

        if name == 'p':
            if self._list:
                return

            if self._note:
                lines.append(f'<p{lang}>')
            elif self._isEpigraph:
                lines.append(f'<p class="epigraph"{lang}>')
            elif xmlAttributes.get('style', None) == 'quotations':
                lines.append(f'<p class="quotations"{lang}>')
                self._quotations = True
                self._indentParagraph = False
            elif self._firstParagraphInChapter:
                lines.append(f'<p class="chapter_beginning"{lang}>')
            elif self._indentParagraph:
                lines.append(f'<p class="first_line_indent"{lang}>')
            else:
                lines.append(f'<p class="text_body"{lang}>')
            if not self._isEpigraph:
                self._firstParagraphInChapter = False
                self._indentParagraph = False
            return

        if name in ('em', 'strong', 'li'):
            lines.append(f'<{name}>')
            return

        if name == 'span':
            lines.append(f'<span{lang}>')
            return

        if name in ('comment', 'note-citation'):
            self._skipElement = True
            return

        if name == 'note':
            self._note = True
            return

        if name in ('h5', 'h6', 'h7', 'h8', 'h9',):
            level = name[-1]
            lines.append(
                f'<p class="custom_{level}{lang}">'
            )
            return

        if name == 'ul':
            self._list = True
            lines.append('<ul>\n')
            return

