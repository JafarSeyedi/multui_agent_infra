import pytest

from engines.document.models.base import ElementType
from engines.document.models.usdm_models import (
    CodeContent,
    HeadingContent,
    ImageContent,
    ListContent,
    ParagraphContent,
    TableContent,
)
from engines.document.parsers.usdm_parsers.html.html_parser import HtmlParser

pytestmark = pytest.mark.asyncio


@pytest.fixture
def html_parser():
    return HtmlParser()


async def test_html_parser_name_and_extensions(html_parser):
    exts = html_parser.get_supported_extensions()
    assert ".html" in exts
    assert ".htm" in exts
    assert ".xhtml" in exts
    mimes = html_parser.get_supported_media_types()
    assert "text/html" in mimes
    assert "application/xhtml+xml" in mimes


async def test_html_parse_basic_structure(html_parser, sample_html):
    doc = await html_parser.parse_bytes(sample_html, document_id="test", source_name="test")
    assert doc.title == "Test HTML Document"
    assert len(doc.elements) > 0
    assert len(doc.logical_elements) > 0


async def test_html_parse_headings(html_parser, sample_html):
    doc = await html_parser.parse_bytes(sample_html, document_id="test", source_name="test")
    headings = [le for le in doc.logical_elements if le.element_type == ElementType.HEADING]
    assert len(headings) >= 2
    h1_headings = [h for h in headings if isinstance(h.content, HeadingContent) and h.content.level == 1]
    assert len(h1_headings) >= 1


async def test_html_parse_paragraphs_with_inline_formatting(html_parser, sample_html):
    doc = await html_parser.parse_bytes(sample_html, document_id="test", source_name="test")
    paras = [le for le in doc.logical_elements if le.element_type == ElementType.PARAGRAPH]
    assert len(paras) >= 1
    first_para = paras[0]
    assert isinstance(first_para.content, ParagraphContent)
    assert len(first_para.content.text.spans) > 0


async def test_html_parse_links(html_parser, sample_html):
    doc = await html_parser.parse_bytes(sample_html, document_id="test", source_name="test")
    found_link = False
    for le in doc.logical_elements:
        if le.element_type == ElementType.PARAGRAPH and isinstance(le.content, ParagraphContent):
            for span in le.content.text.spans:
                if span.href == "https://example.com":
                    found_link = True
    assert found_link


async def test_html_parse_images(html_parser, sample_html):
    doc = await html_parser.parse_bytes(sample_html, document_id="test", source_name="test")
    images = [le for le in doc.logical_elements if le.element_type == ElementType.IMAGE]
    assert len(images) >= 1
    img = images[0]
    assert isinstance(img.content, ImageContent)
    assert img.content.src == "image.png"
    assert img.content.alt == "An image"


async def test_html_parse_lists_ordered_unordered(html_parser, sample_html):
    doc = await html_parser.parse_bytes(sample_html, document_id="test", source_name="test")
    lists = [le for le in doc.logical_elements if le.element_type == ElementType.LIST]
    assert len(lists) >= 2
    ordered = [le for le in lists if isinstance(le.content, ListContent) and le.content.ordered]
    unordered = [le for le in lists if isinstance(le.content, ListContent) and not le.content.ordered]
    assert len(ordered) >= 1
    assert len(unordered) >= 1


async def test_html_parse_tables(html_parser, sample_html):
    doc = await html_parser.parse_bytes(sample_html, document_id="test", source_name="test")
    tables = [le for le in doc.logical_elements if le.element_type == ElementType.TABLE]
    assert len(tables) >= 1
    table = tables[0]
    assert isinstance(table.content, TableContent)
    assert len(table.content.rows) >= 2


async def test_html_parse_code_blocks(html_parser, sample_html):
    doc = await html_parser.parse_bytes(sample_html, document_id="test", source_name="test")
    codes = [le for le in doc.logical_elements if le.element_type == ElementType.CODE]
    assert len(codes) >= 1
    code = codes[0]
    assert isinstance(code.content, CodeContent)
    assert 'print("world")' in code.content.code


async def test_html_parse_blockquotes(html_parser, sample_html):
    doc = await html_parser.parse_bytes(sample_html, document_id="test", source_name="test")
    quotes = [le for le in doc.logical_elements if le.element_type == ElementType.QUOTE]
    assert len(quotes) >= 1


async def test_html_parse_semantic_elements(html_parser, sample_html):
    doc = await html_parser.parse_bytes(sample_html, document_id="test", source_name="test")
    headings = [le for le in doc.logical_elements if le.element_type == ElementType.HEADING]
    h3_headings = [h for h in headings if isinstance(h.content, HeadingContent) and h.content.level == 3]
    assert len(h3_headings) >= 2


async def test_html_parse_empty_document(html_parser):
    doc = await html_parser.parse_bytes(b"", document_id="test", source_name="test")
    assert doc is not None
    assert doc.title == "test"


async def test_html_parse_document_with_styles(html_parser):
    html = b"""<html><head><title>Styled</title></head>
<body><h1 style="color:red">Red Heading</h1><p>Text</p></body></html>"""
    doc = await html_parser.parse_bytes(html, document_id="test", source_name="test")
    assert doc.title == "Styled"
    headings = [le for le in doc.logical_elements if le.element_type == ElementType.HEADING]
    assert len(headings) >= 1


async def test_html_round_trip_elements(html_parser, sample_html):
    doc = await html_parser.parse_bytes(sample_html, document_id="test", source_name="test")
    element_types = {}
    for le in doc.logical_elements:
        et = le.element_type.value
        element_types[et] = element_types.get(et, 0) + 1
    assert "heading" in element_types
    assert "paragraph" in element_types
    assert "list" in element_types
    assert "table" in element_types
    assert "code" in element_types
    assert "image" in element_types
