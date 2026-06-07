import pytest

from engines.document.models.base import ElementType
from engines.document.parsers.usdm_parsers.txt.txt_parser import TXTParser

pytestmark = pytest.mark.asyncio


@pytest.fixture
def txt_parser():
    return TXTParser()


async def test_txt_parser_name_and_extensions(txt_parser):
    assert txt_parser.name == "txt"
    exts = txt_parser.supported_extensions
    assert ".txt" in exts
    assert ".text" in exts
    assert ".log" in exts


async def test_txt_parse_paragraphs(txt_parser, sample_txt):
    doc = await txt_parser.parse_bytes(sample_txt, document_id="test", source_name="test")
    paras = [le for le in doc.logical_elements if le.element_type == ElementType.PARAGRAPH]
    assert len(paras) >= 1


async def test_txt_parse_encoding_utf8(txt_parser):
    text = "Hello UTF-8: \xc3\xa9\xc3\xa8\xc3\xa0".encode("utf-8")
    doc = await txt_parser.parse_bytes(text, document_id="test", source_name="test")
    assert doc is not None


async def test_txt_parse_encoding_detection(txt_parser):
    text = b"Simple ASCII text for encoding detection."
    doc = await txt_parser.parse_bytes(text, document_id="test", source_name="test")
    assert doc is not None
    assert doc.metadata.get("encoding") is not None


async def test_txt_parse_heading_detection(txt_parser):
    text = b"Title\n=====\n\nSome content here."
    doc = await txt_parser.parse_bytes(text, document_id="test", source_name="test")
    headings = [le for le in doc.logical_elements if le.element_type == ElementType.HEADING]
    assert len(headings) >= 1


async def test_txt_parse_list_detection(txt_parser):
    text = b"- Item 1\n- Item 2\n- Item 3\n"
    doc = await txt_parser.parse_bytes(text, document_id="test", source_name="test")
    lists = [le for le in doc.logical_elements if le.element_type == ElementType.LIST]
    assert len(lists) >= 1


async def test_txt_parse_empty(txt_parser):
    doc = await txt_parser.parse_bytes(b"", document_id="test", source_name="test")
    assert doc is not None
    assert len(doc.logical_elements) == 0


async def test_txt_parse_single_paragraph(txt_parser):
    text = b"This is a single paragraph with no breaks."
    doc = await txt_parser.parse_bytes(text, document_id="test", source_name="test")
    paras = [le for le in doc.logical_elements if le.element_type == ElementType.PARAGRAPH]
    assert len(paras) >= 1
