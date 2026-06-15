import pytest

from engines.document.models.base import ElementType
from engines.document.parsers.usdm_parsers.html.html_parser import HtmlParser
from engines.document.parsers.usdm_parsers.latex.latex_parser import LatexParser
from engines.document.parsers.usdm_parsers.markdown.markdown_parser import MarkdownParser
from engines.document.parsers.usdm_parsers.rtf.rtf_parser import RTFParser
from engines.document.parsers.usdm_parsers.txt.txt_parser import TXTParser
from engines.document.writers.usdm_writers.base import WriteOptions
from engines.document.writers.usdm_writers.html.html_writer import HTMLWriter
from engines.document.writers.usdm_writers.latex.latex_writer import LatexWriter
from engines.document.writers.usdm_writers.markdown.markdown_writer import MarkdownWriter
from engines.document.writers.usdm_writers.rtf.rtf_writer import RTFWriter
from engines.document.writers.usdm_writers.txt.txt_writer import TXTWriter

pytestmark = pytest.mark.asyncio


async def test_markdown_roundtrip(sample_markdown, parse_options):
    parser = MarkdownParser()
    doc = await parser.parse_bytes(sample_markdown, document_id="test", source_name="test")
    original_count = len(doc.logical_elements)

    writer = MarkdownWriter(options=WriteOptions())
    result = await writer.write(doc)
    assert isinstance(result, bytes)
    assert len(result) > 0

    parser2 = MarkdownParser()
    doc2 = await parser2.parse_bytes(result, document_id="test2", source_name="test2")
    assert len(doc2.logical_elements) >= original_count // 2


async def test_latex_roundtrip(sample_latex, parse_options):
    parser = LatexParser()
    doc = await parser.parse_bytes(sample_latex, document_id="test", source_name="test")
    original_headings = len([le for le in doc.logical_elements if le.element_type == ElementType.HEADING])

    writer = LatexWriter(options=WriteOptions())
    result = await writer.write(doc)
    assert isinstance(result, bytes)
    assert len(result) > 0

    parser2 = LatexParser()
    doc2 = await parser2.parse_bytes(result, document_id="test2", source_name="test2")
    rt_headings = len([le for le in doc2.logical_elements if le.element_type == ElementType.HEADING])
    assert rt_headings >= original_headings // 2


async def test_txt_roundtrip(sample_txt, parse_options):
    parser = TXTParser()
    doc = await parser.parse_bytes(sample_txt, document_id="test", source_name="test.txt")
    len(doc.logical_elements)

    writer = TXTWriter(options=WriteOptions())
    result = await writer.write(doc)
    assert isinstance(result, bytes)
    assert len(result) > 0

    parser2 = TXTParser()
    doc2 = await parser2.parse_bytes(result, document_id="test2", source_name="test2.txt")
    assert len(doc2.logical_elements) >= 1


async def test_html_roundtrip(sample_html, parse_options):
    parser = HtmlParser()
    doc = await parser.parse_bytes(sample_html, document_id="test", source_name="test")
    original_count = len(doc.logical_elements)

    writer = HTMLWriter(options=WriteOptions())
    result = await writer.write(doc)
    assert isinstance(result, bytes)
    assert len(result) > 0

    parser2 = HtmlParser()
    doc2 = await parser2.parse_bytes(result, document_id="test2", source_name="test2")
    assert len(doc2.logical_elements) >= original_count // 2


async def test_rtf_roundtrip(sample_rtf, parse_options):
    parser = RTFParser()
    doc = await parser.parse_bytes(sample_rtf, document_id="test", source_name="test")
    len(doc.logical_elements)

    writer = RTFWriter(options=WriteOptions())
    result = await writer.write(doc)
    assert isinstance(result, bytes)
    assert len(result) > 0

    parser2 = RTFParser()
    doc2 = await parser2.parse_bytes(result, document_id="test2", source_name="test2")
    assert len(doc2.logical_elements) >= 1


async def test_cross_format_pipeline(sample_html, parse_options):
    html_parser = HtmlParser()
    doc = await html_parser.parse_bytes(sample_html, document_id="test", source_name="test")

    md_writer = MarkdownWriter(options=WriteOptions())
    md_result = await md_writer.write(doc)
    assert isinstance(md_result, bytes)
    assert len(md_result) > 0

    md_parser = MarkdownParser()
    doc2 = await md_parser.parse_bytes(md_result, document_id="test2", source_name="test2")
    assert len(doc2.logical_elements) >= 1
