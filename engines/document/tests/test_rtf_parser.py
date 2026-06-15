import pytest

from engines.document.models.base import ElementType
from engines.document.models.usdm_models import (
    ParagraphContent,
    TableContent,
)
from engines.document.parsers.usdm_parsers.rtf.rtf_parser import RTFParser

pytestmark = pytest.mark.asyncio


@pytest.fixture
def rtf_parser():
    return RTFParser()


async def test_rtf_parser_name_and_extensions(rtf_parser):
    assert rtf_parser.name == "rtf"
    exts = rtf_parser.supported_extensions
    assert ".rtf" in exts


async def test_rtf_parse_basic_text(rtf_parser, sample_rtf):
    doc = await rtf_parser.parse_bytes(sample_rtf, document_id="test", source_name="test")
    assert doc is not None
    paras = [le for le in doc.logical_elements if le.element_type == ElementType.PARAGRAPH]
    assert len(paras) >= 1


async def test_rtf_parse_character_formatting(rtf_parser, sample_rtf):
    doc = await rtf_parser.parse_bytes(sample_rtf, document_id="test", source_name="test")
    paras = [le for le in doc.logical_elements if le.element_type == ElementType.PARAGRAPH]
    found_bold = False
    for p in paras:
        if isinstance(p.content, ParagraphContent):
            for span in p.content.text.spans:
                if span.bold:
                    found_bold = True
    assert found_bold


async def test_rtf_parse_fonts_and_colors(rtf_parser, sample_rtf):
    doc = await rtf_parser.parse_bytes(sample_rtf, document_id="test", source_name="test")
    assert doc.stylesheet is not None
    assert len(doc.stylesheet.character_styles) > 0


async def test_rtf_parse_paragraphs(rtf_parser, sample_rtf):
    doc = await rtf_parser.parse_bytes(sample_rtf, document_id="test", source_name="test")
    paras = [le for le in doc.logical_elements if le.element_type == ElementType.PARAGRAPH]
    assert len(paras) >= 1


async def test_rtf_parse_tables(rtf_parser):
    rtf = b"""{\\rtf1\\ansi\\ansicpg1252\\deff0
{\\fonttbl{\\f0\\fswiss\\fcharset0 Arial;}}
\\trowd \\cellx1000 \\cellx2000
\\intbl Header1\\cell Header2\\cell
\\row
\\trowd \\cellx1000 \\cellx2000
\\intbl Data1\\cell Data2\\cell
\\row
}
"""
    doc = await rtf_parser.parse_bytes(rtf, document_id="test", source_name="test")
    tables = [le for le in doc.logical_elements if le.element_type == ElementType.TABLE]
    assert len(tables) >= 1
    table = tables[0]
    assert isinstance(table.content, TableContent)
    assert len(table.content.rows) >= 1


async def test_rtf_parse_lists(rtf_parser):
    rtf = b"""{\\rtf1\\ansi\\ansicpg1252\\deff0
{\\fonttbl{\\f0\\fswiss\\fcharset0 Arial;}}
\\pnbody\\pnlvlblt\\pnf1\\pnfs20{\\'b7}\\tab Item 1\\par
\\pnbody\\pnlvlblt\\pnf1\\pnfs20{\\'b7}\\tab Item 2\\par
}
"""
    doc = await rtf_parser.parse_bytes(rtf, document_id="test", source_name="test")
    assert doc is not None
    paras = [le for le in doc.logical_elements if le.element_type == ElementType.PARAGRAPH]
    assert len(paras) >= 1


async def test_rtf_parse_headings(rtf_parser, sample_rtf):
    doc = await rtf_parser.parse_bytes(sample_rtf, document_id="test", source_name="test")
    headings = [le for le in doc.logical_elements if le.element_type == ElementType.HEADING]
    assert len(headings) >= 1


async def test_rtf_parse_unicode(rtf_parser):
    rtf = b"""{\\rtf1\\ansi\\ansicpg1252\\deff0
{\\fonttbl{\\f0\\fswiss\\fcharset0 Arial;}}
\\u1044? test\\par
}
"""
    doc = await rtf_parser.parse_bytes(rtf, document_id="test", source_name="test")
    assert doc is not None


async def test_rtf_parse_empty(rtf_parser):
    doc = await rtf_parser.parse_bytes(b"", document_id="test", source_name="test")
    assert doc is not None
