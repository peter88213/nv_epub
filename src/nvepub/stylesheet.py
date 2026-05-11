"""Provide an Epub mixin class for css stylesheet representation.

Copyright (c) Peter Triesberger
For further information see https://github.com/peter88213/nv_epub
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os

from nvepub.nvepub_globals import CSS_NAME


class Stylesheet:

    DEFAULT_CSS = '''@namespace h "http://www.w3.org/1999/xhtml";
@page
    {
    margin: 5pt;
    }
strong
    {
    font-weight: normal;
    text-transform: uppercase;
    }
em 
    {
    font-style: italic;
    }
body
    {
    font-family: "100 %", serif, sansserif;
    }
h1
    {
    margin-top:4em;
    margin-bottom:2em;
    page-break-after:avoid;
    font-size: 1.20em;
    text-align: center;
    text-indent:0em;
    }
h2
    {
    margin-top:3em;
    margin-right:0em;
    margin-bottom:2em;
    margin-left:0em;
    page-break-after:avoid;
    font-size: 1.10em;
    text-align: center;
    text-indent:0em;
    }
h4
    {
    margin-top:1em;
    margin-bottom:1em;
    line-height:normal;
    text-align: center;
    text-indent:0em;
    }
p
    {
    margin:0pt;
    text-indent:0em;
    line-height: 1.2em;
    text-align: left;
    font-size: 1.0em;
    widows: 2;
    orphans: 2;
    }
p.title
    {
    margin-top:2em;
    margin-bottom:1.5em;
    page-break-after:avoid;
    font-size: 1.50em;
    text-align: center;
    text-indent:0em;
    }
p.author
    {
    margin-top:2em;
    margin-bottom:1.5em;
    page-break-after:avoid;
    font-size: 1.00em;
    text-align: center;
    text-indent:0em;
    }
p.epigraph
    {
    font-size: 0.8em;
    margin-left:3em;
    margin-right:3em;
    margin-top:2em;
    margin-bottom:1.5em;
    line-height: 1em;
    }
p.epigraph_source
    {
    font-size: 0.8em;
    margin-left:3em;
    margin-right:3em;
    text-align: center;
    margin-bottom:3em;
    font-variant: small-caps;
    line-height: 1em;
    }
p.chapter_beginning, p.text_body
    {
    text-indent:0em;
    }
p.first_line_indent
    {
    text-indent:1.5em;
    }
p.quotations
    {
    text-indent:0em;
    margin-left:2.5em;
    margin-right: 1em;
    }
p.custom_5
    {
    margin-top:2em;
    margin-bottom:2em;
    line-height:normal;
    page-break-after:avoid;
    font-size: .90em;
    text-align: center;
    text-indent:0em;
    }
p.custom_6, .custom_7, .custom_8, .custom_9
    {
    margin-top:2em;
    margin-bottom:2em;
    line-height:normal;
    page-break-after:avoid;
    font-size: .90em;
    text-align: center;
    text-indent:0em;
    }
'''

    def write_css(self, prjDir):
        prjCssPath = os.path.join(prjDir, CSS_NAME)
        try:
            with open(prjCssPath, 'r', encoding='utf-8') as f:
                css = f.read()
        except:
            css = self.DEFAULT_CSS
        self.write_file(f'OEBPS/styles/{CSS_NAME}', css)

        # Find out whether strongly emphasized text
        # must be transformed to all-caps.
        lines = css.split('\n')
        strong = False
        upcaseStrong = False
        for line in lines:
            if strong:
                if not line.startswith(' '):
                    break

                elif 'uppercase' in line:
                    upcaseStrong = True
                    break

            elif line.startswith('strong'):
                strong = True
        return upcaseStrong

