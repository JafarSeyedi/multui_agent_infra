import pytest

from engines.document.models.base import ElementType
from engines.document.models.usdm_models import (
    HeadingContent,
    MathContent,
)
from engines.document.parsers.usdm_parsers.latex.latex_parser import LatexParser

pytestmark = pytest.mark.asyncio


@pytest.fixture
def latex_parser():
    return LatexParser()


async def test_latex_parser_name(latex_parser):
    assert latex_parser.name == "latex"
    exts = latex_parser.supported_extensions
    assert ".tex" in exts
    assert ".latex" in exts


async def test_latex_parse_document_structure(latex_parser, sample_latex):
    doc = await latex_parser.parse_bytes(sample_latex, document_id="test", source_name="test")
    assert doc is not None
    assert doc.title == "Test LaTeX Document"
    assert len(doc.logical_elements) > 0


async def test_latex_parse_sections(latex_parser, sample_latex):
    doc = await latex_parser.parse_bytes(sample_latex, document_id="test", source_name="test")
    headings = [le for le in doc.logical_elements if le.element_type == ElementType.HEADING]
    assert len(headings) >= 2
    heading_texts = []
    for h in headings:
        if isinstance(h.content, HeadingContent):
            for span in h.content.text.spans:
                heading_texts.append(span.text)
    assert any("Introduction" in t for t in heading_texts)
    assert any("Background" in t for t in heading_texts)


async def test_latex_parse_environments(latex_parser, sample_latex):
    doc = await latex_parser.parse_bytes(sample_latex, document_id="test", source_name="test")
    lists = [le for le in doc.logical_elements if le.element_type == ElementType.LIST]
    quotes = [le for le in doc.logical_elements if le.element_type == ElementType.QUOTE]
    tables = [le for le in doc.logical_elements if le.element_type == ElementType.TABLE]
    assert len(lists) >= 1
    assert len(quotes) >= 1
    assert len(tables) >= 1


async def test_latex_parse_inline_math(latex_parser, sample_latex):
    doc = await latex_parser.parse_bytes(sample_latex, document_id="test", source_name="test")
    maths = [le for le in doc.logical_elements if le.element_type == ElementType.MATH]
    assert len(maths) >= 1
    inline_maths = [m for m in maths if isinstance(m.content, MathContent) and not m.content.display]
    assert len(inline_maths) >= 1


async def test_latex_parse_display_math(latex_parser, sample_latex):
    doc = await latex_parser.parse_bytes(sample_latex, document_id="test", source_name="test")
    maths = [le for le in doc.logical_elements if le.element_type == ElementType.MATH]
    display_maths = [m for m in maths if isinstance(m.content, MathContent) and m.content.display]
    assert len(display_maths) >= 1


async def test_latex_parse_commands(latex_parser, sample_latex):
    doc = await latex_parser.parse_bytes(sample_latex, document_id="test", source_name="test")
    assert doc.stylesheet is not None
    assert len(doc.stylesheet.character_styles) > 0
    assert len(doc.stylesheet.paragraph_styles) > 0


async def test_latex_parse_special_characters(latex_parser):
    tex = b"""\\documentclass{article}
\\title{Test & Special % Characters}
\\begin{document}
\\maketitle
\\section{Intro}
Text with \\& and \\% chars.
\\end{document}
"""
    doc = await latex_parser.parse_bytes(tex, document_id="test", source_name="test")
    assert doc is not None
    assert "Test" in doc.title
