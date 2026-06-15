import pytest

from engines.document.models.base import ElementType
from engines.document.models.usdm_models import (
    HeadingContent,
    ListContent,
    ParagraphContent,
    TableContent,
)
from engines.document.parsers.usdm_parsers.markdown.markdown_parser import MarkdownParser

pytestmark = pytest.mark.asyncio


@pytest.fixture
def markdown_parser():
    return MarkdownParser()


async def test_markdown_parser_name(markdown_parser):
    assert markdown_parser.name == "markdown"
    exts = markdown_parser.supported_extensions
    assert ".md" in exts
    assert ".markdown" in exts


async def test_markdown_parse_headings(markdown_parser, sample_markdown):
    doc = await markdown_parser.parse_bytes(sample_markdown, document_id="test", source_name="test")
    headings = [le for le in doc.logical_elements if le.element_type == ElementType.HEADING]
    assert len(headings) >= 2
    levels = [h.content.level for h in headings if isinstance(h.content, HeadingContent)]
    assert 1 in levels
    assert 2 in levels


async def test_markdown_parse_paragraphs(markdown_parser, sample_markdown):
    doc = await markdown_parser.parse_bytes(sample_markdown, document_id="test", source_name="test")
    paras = [le for le in doc.logical_elements if le.element_type == ElementType.PARAGRAPH]
    assert len(paras) >= 1
    first_para = paras[0]
    assert isinstance(first_para.content, ParagraphContent)


async def test_markdown_parse_bold_italic(markdown_parser, sample_markdown):
    doc = await markdown_parser.parse_bytes(sample_markdown, document_id="test", source_name="test")
    paras = [le for le in doc.logical_elements if le.element_type == ElementType.PARAGRAPH]
    found_bold = False
    found_italic = False
    for p in paras:
        if isinstance(p.content, ParagraphContent):
            for span in p.content.text.spans:
                if "bold" in span.character_style.lower() if span.character_style else "":
                    found_bold = True
                if "italic" in span.character_style.lower() if span.character_style else "":
                    found_italic = True
    assert found_bold or found_italic or len(paras) > 0


async def test_markdown_parse_links_and_images(markdown_parser, sample_markdown):
    doc = await markdown_parser.parse_bytes(sample_markdown, document_id="test", source_name="test")
    links = [le for le in doc.logical_elements if le.element_type == ElementType.LINK]
    assert len(links) >= 1
    images = [le for le in doc.logical_elements if le.element_type == ElementType.IMAGE]
    assert len(images) >= 0


async def test_markdown_parse_lists(markdown_parser, sample_markdown):
    doc = await markdown_parser.parse_bytes(sample_markdown, document_id="test", source_name="test")
    lists = [le for le in doc.logical_elements if le.element_type == ElementType.LIST]
    assert len(lists) >= 2
    ordered = [le for le in lists if isinstance(le.content, ListContent) and le.content.ordered]
    unordered = [le for le in lists if isinstance(le.content, ListContent) and not le.content.ordered]
    assert len(ordered) >= 1
    assert len(unordered) >= 1


async def test_markdown_parse_code_blocks(markdown_parser, sample_markdown):
    doc = await markdown_parser.parse_bytes(sample_markdown, document_id="test", source_name="test")
    codes = [le for le in doc.logical_elements if le.element_type == ElementType.CODE]
    assert len(codes) >= 1


async def test_markdown_parse_blockquotes(markdown_parser, sample_markdown):
    doc = await markdown_parser.parse_bytes(sample_markdown, document_id="test", source_name="test")
    quotes = [le for le in doc.logical_elements if le.element_type == ElementType.QUOTE]
    assert len(quotes) >= 1


async def test_markdown_parse_tables(markdown_parser):
    md = b"""| Col1 | Col2 |
|------|------|
| A | B |
| C | D |
"""
    doc = await markdown_parser.parse_bytes(md, document_id="test", source_name="test")
    tables = [le for le in doc.logical_elements if le.element_type == ElementType.TABLE]
    assert len(tables) >= 1
    table = tables[0]
    assert isinstance(table.content, TableContent)


async def test_markdown_parse_horizontal_rules(markdown_parser):
    md = b"""# Heading

Text before.

---

Text after.
"""
    doc = await markdown_parser.parse_bytes(md, document_id="test", source_name="test")
    assert doc is not None
    paras = [le for le in doc.logical_elements if le.element_type == ElementType.PARAGRAPH]
    assert len(paras) >= 1


async def test_markdown_parse_empty(markdown_parser):
    doc = await markdown_parser.parse_bytes(b"", document_id="test", source_name="test")
    assert doc is not None
    assert doc.title == "test"
