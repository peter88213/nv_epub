[Project homepage](https|//github.com/peter88213/nv_epub) > [Index](../) > User guide

------------------------------------------------------------------------

#  User guide

This page refers to the latest
[nv_epub](https|//github.com/peter88213/nv_epub/) release. You can
open it with **Help \> nv_epub Online help**.


## Export an EPUB e-book from the current *novelibre* project

*novelibre* main menu| **Export \> EPUB e-book** creates an *.epub* file
with the *novelibre* project\'s name in the project directory.
File name suffix is `_ebook`.

---

## Use a custom css stylesheet

Just place your stylesheet named `nv_epub.css` in the project directory.


### XHTML elements used with the EPUB created by *nv_epub*

| XHTML                   | *Writer* style name                             | Description                                            |
|-------------------------|-------------------------------------------------|--------------------------------------------------------|
| **h1**                  | **Heading 1**                                   | Part heading.                                          |
| **h2**                  | **Heading 2**                                   | Chapter heading.                                       |
| **h4**                  | **Heading 4**                                   | Section divider.                                       |
| **p**                   | **Default paragraph style**                     |(Not explicitly applied)                                |
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
