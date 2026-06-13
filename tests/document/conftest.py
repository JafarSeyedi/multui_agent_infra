import sys

sys.path.insert(0, "/home/sjfs/autogen_project/multi_agent_infra")

import pytest

from engines.document.models.base import ElementType
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.usdm_models import (
    CharacterStyle, DocumentElement, HeadingContent, LogicalElement, ParagraphContent, ParagraphStyle, RichTextContent, RichTextSpan,
    Section, StyleSheet, TableStyle, USDMDocument,
)
from engines.document.parsers.base import ParseOptions
from engines.document.writers.base import WriteOptions


pytestmark = pytest.mark.asyncio
@pytest.fixture
def parse_options():
    return ParseOptions()


@pytest.fixture
def write_options():
    return WriteOptions()


@pytest.fixture
def sample_usdm_minimal():
    doc = USDMDocument(
        title="Minimal Test",
        document_id="test-min-001",
        media_type=MEDIA_TYPES["txt"],
    )
    para = LogicalElement(
        element_id="p1",
        element_type=ElementType.PARAGRAPH,
        content=ParagraphContent(text=RichTextContent(spans=[RichTextSpan(text="Hello world")])),
    )
    doc.logical_elements.append(para)
    sec = Section(
        section_id="s1",
        elements=[DocumentElement(element_id="p1", element_type=ElementType.PARAGRAPH)],
    )
    doc.sections.append(sec)
    return doc


@pytest.fixture
def sample_usdm_document():
    doc = USDMDocument(
        title="Test Document",
        document_id="test-001",
        media_type=MEDIA_TYPES["html"],
    )
    doc.stylesheet = StyleSheet(
        character_styles={
            "bold": CharacterStyle(name="bold", bold=True),
            "italic": CharacterStyle(name="italic", italic=True),
        },
        paragraph_styles={"centered": ParagraphStyle(name="centered", alignment="center")},
        table_styles={"default": TableStyle(name="default")},
    )
    h1 = LogicalElement(
        element_id="h1", element_type=ElementType.HEADING,
        content=HeadingContent(level=1, text=RichTextContent(spans=[RichTextSpan(text="Main Title")])),
    )
    h2 = LogicalElement(
        element_id="h2", element_type=ElementType.HEADING,
        content=HeadingContent(level=2, text=RichTextContent(spans=[RichTextSpan(text="Subtitle")])),
    )
    doc.logical_elements.extend([h1, h2])
    sec = Section(
        section_id="s1", title=h1.content,
        elements=[
            DocumentElement(element_id="h1", element_type=ElementType.HEADING),
            DocumentElement(element_id="h2", element_type=ElementType.HEADING),
        ],
    )
    doc.sections.append(sec)
    return doc


@pytest.fixture
def sample_html():
    return b"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Test</title></head>
<body>
<h1>Main Heading</h1>
<h2>Subheading</h2>
<p>A paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
<p>Another paragraph with <a href="https://example.com">a link</a>.</p>
<ul><li>Item 1</li><li>Item 2</li></ul>
<ol><li>First</li><li>Second</li></ol>
<pre><code>print('hello')</code></pre>
<blockquote><p>A quote</p></blockquote>
<figure><img src="test.png" alt="test"><figcaption>Caption</figcaption></figure>
<table><thead><tr><th>H1</th><th>H2</th></tr></thead><tbody><tr><td>A</td><td>B</td></tr></tbody></table>
</body>
</html>"""


@pytest.fixture
def sample_markdown():
    return b"""# Main Heading

## Subheading

A paragraph with **bold** and *italic* text.

Another paragraph with [a link](https://example.com).

- Item 1
- Item 2

1. First
2. Second

```python
print('hello')
```

> A quote

| H1 | H2 |
|----|----|
| A  | B  |

~~strikethrough~~

- [x] Done
- [ ] Not done
"""


@pytest.fixture
def sample_latex():
    return b"""\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\usepackage{amsmath}
\\usepackage{graphicx}
\\usepackage{hyperref}

\\title{Test Document}
\\author{Author Name}
\\date{\\today}

\\begin{document}
\\maketitle

\\section{Introduction}
This is a paragraph with \\textbf{bold} and \\textit{italic} text.
This has a footnote\\footnote{A footnote.}.

\\subsection{Math}
Inline math: $E = mc^2$
\\begin{equation}
  \\int_0^1 f(x) dx
\\end{equation}

\\begin{itemize}
  \\item Item 1
  \\item Item 2
\\end{itemize}

\\begin{table}[ht]
\\centering
\\begin{tabular}{ll}
H1 & H2 \\\\
A & B \\\\
\\end{tabular}
\\caption{A table}\\label{tab:1}
\\end{table}

See Table~\\ref{tab:1}.

\\begin{figure}[ht]
\\centering
\\includegraphics[width=0.5\\textwidth]{test.png}
\\caption{A figure}
\\end{figure}

\\end{document}
"""


@pytest.fixture
def sample_rtf():
    return b"""{\\rtf1\\ansi\\ansicpg1252\\deff0
{\\fonttbl{\\f0\\fnil\\fcharset0 Calibri;}}
{\\colortbl ;\\red0\\green0\\blue255;}
\\viewkind4\\uc1
\\pard\\sa200\\sl276\\slmult1\\lang9\\f0\\fs22\\b Main Heading\\b0\\par
\\par
A paragraph with \\b bold\\b0  and \\i italic\\i0  text.\\par
\\par
\\cf1 Blue text\\cf0\\par
\\page\\par
}
"""


@pytest.fixture
def sample_txt():
    return b"""MAIN TITLE
==========

A paragraph of text.

Another paragraph.

- Item 1
- Item 2
- Item 3

Final paragraph.
"""
