import pytest

from engines.document.models.media_types import DocumentFormat
from engines.document.models.document_registry import DocumentRegistry
from engines.document.parsers.usdm_parsers.html.html_parser import HtmlParser
from engines.document.parsers.usdm_parsers.latex.latex_parser import LatexParser
from engines.document.parsers.usdm_parsers.markdown.markdown_parser import MarkdownParser
from engines.document.parsers.usdm_parsers.rtf.rtf_parser import RTFParser
from engines.document.parsers.usdm_parsers.txt.txt_parser import TXTParser
from engines.document.writers.usdm_writers.html.html_writer import HTMLWriter
from engines.document.writers.usdm_writers.markdown.markdown_writer import MarkdownWriter

pytestmark = pytest.mark.asyncio


@pytest.fixture
def registry():
    reg = DocumentRegistry()
    reg.register_parser_plugin(DocumentFormat.HTML, HtmlParser)
    reg.register_parser_plugin(DocumentFormat.MARKDOWN, MarkdownParser)
    reg.register_parser_plugin(DocumentFormat.LATEX, LatexParser)
    reg.register_parser_plugin(DocumentFormat.RTF, RTFParser)
    reg.register_parser_plugin(DocumentFormat.TXT, TXTParser)
    reg.register_writer_plugin(DocumentFormat.HTML, HTMLWriter)
    reg.register_writer_plugin(DocumentFormat.MARKDOWN, MarkdownWriter)
    return reg


async def test_registry_parses_html(registry, sample_html):
    parser = registry.get_parser(sample_html)
    assert parser is not None
    assert isinstance(parser, HtmlParser)
    doc = await parser.parse_bytes(sample_html, document_id="test", source_name="test")
    assert doc is not None


async def test_registry_parses_markdown(registry, sample_markdown):
    parser = registry.get_parser(sample_markdown)
    assert parser is not None
    assert isinstance(parser, MarkdownParser)
    doc = await parser.parse_bytes(sample_markdown, document_id="test", source_name="test")
    assert doc is not None


async def test_registry_parses_latex(registry, sample_latex):
    parser = registry.get_parser(sample_latex)
    assert parser is not None
    assert isinstance(parser, LatexParser)
    doc = await parser.parse_bytes(sample_latex, document_id="test", source_name="test")
    assert doc is not None


async def test_registry_parses_rtf(registry, sample_rtf):
    parser = registry.get_parser(sample_rtf)
    assert parser is not None
    assert isinstance(parser, RTFParser)
    doc = await parser.parse_bytes(sample_rtf, document_id="test", source_name="test")
    assert doc is not None


async def test_registry_parses_txt(registry, sample_txt):
    parser = registry.get_parser(sample_txt)
    assert parser is not None
    assert isinstance(parser, TXTParser)
    doc = await parser.parse_bytes(sample_txt, document_id="test", source_name="test")
    assert doc is not None


async def test_registry_gets_writer(registry):
    writer = registry.get_writer(DocumentFormat.HTML)
    assert writer is not None
    assert isinstance(writer, HTMLWriter)


async def test_registry_ingestion_prepares_html(registry, sample_html):
    result = registry.prepare_ingestion(sample_html)
    assert result is not None
    assert "media_type" in result
    assert "parser" in result
    assert result["parser"] is not None
    assert isinstance(result["parser"], HtmlParser)
    assert result["format"] == DocumentFormat.HTML


async def test_registry_ingestion_prepares_markdown(registry, sample_markdown):
    result = registry.prepare_ingestion(sample_markdown)
    assert result is not None
    assert "media_type" in result
    assert "parser" in result
    assert result["parser"] is not None
    assert isinstance(result["parser"], MarkdownParser)
    assert result["format"] == DocumentFormat.MARKDOWN
