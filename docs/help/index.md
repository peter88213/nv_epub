[Project homepage](https|//github.com/peter88213/nv_epub) > [Index](../) > User guide

------------------------------------------------------------------------

#  User guide

This page refers to the latest
[nv_epub](https|//github.com/peter88213/nv_epub/) release. You can
open it with **Help \> nv_epub Online help**.


---

## Export an e-book

**Export > EPUB e-book** creates an *.epub* file in the project directory.
The filenames of the generated e-book follows this pattern: 
`<Title> - <Author>.epub` 


---

## How to provide a cover image (optional)

By default, the first page, which includes the title and author, is used as the cover image. 
However, if you have a suitable cover image in JPEG format, you can save it in the project 
directory with the filename `cover.jpg`. *nv_epub* will then incorporate it. 

---

## How to provide a custom css stylesheet (optional)

*nv_epub* generates a stylesheet containing all the necessary style classes. 
If you don't like the default stylesheet, you can provide your own. 
Save it in the project directory with the filename `nv_epub.css`. 


### XHTML elements used with the EPUB created by *nv_epub*

| XHTML                   | *Writer* style name                             | Description                                            |
|-------------------------|-------------------------------------------------|--------------------------------------------------------|
| **h1**                  | **Heading 1**                                   | Part heading.                                          |
| **h2**                  | **Heading 2**                                   | Chapter heading.                                       |
| **h4**                  | **Heading 4**                                   | Section divider.                                       |
| **p**                   | **Default paragraph style**                     | (Not explicitly applied)                               |
| **p.title**             | **Title**                                       | Novel title.                                           |
| **p.author**            | **Subtitle**                                    | Author.                                                |
| **p.epigraph**          | **Epigraph**                                    | Epigraph body.                                         |
| **p.epigraph_source**   | **Epigraph source**                             | The epigraph's source, if any.                         |
| **p.chapter_beginning** | **Chapter beginning**                           | Chapter's first paragraph.                             |
| **p.text_body**         | **Text body**                                   | Section's first paragraph, if not beginning a chapter. |
| **p.first_line_indent** | **First line indent**                           | Regular paragraph.                                     |
| **p.quotations**        | **Quotations** (OO) / **Block Quotations** (LO) | Paragraph visually distinguished from the body text.   |
| **p.custom_5**          | **Heading 5**                                   | Paragraph visually distinguished from the body text.   |
| **p.custom_6**          | **Heading 6**                                   | Paragraph visually distinguished from the body text.   |
| **p.custom_7**          | **Heading 7**                                   | Paragraph visually distinguished from the body text.   |
| **p.custom_8**          | **Heading 8**                                   | Paragraph visually distinguished from the body text.   |
| **p.custom_9**          | **Heading 9**                                   | Paragraph visually distinguished from the body text.   |
| **ul**                  | (N/A)                                           | Unordered list (enclosing list elements).              |
| **li**                  | (**First line indent** is applied)              | List element paragraph.                                |
| **em**                  | **Emphasis**                                    | Emphasized text.                                       | 
| **strong**              | **Strong emphasis**                             | Strongly emphasized text.                              | 


---

Copyright (c) by Peter Triesberger. All rights reserved.
