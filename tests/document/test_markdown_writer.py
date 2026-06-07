import pytest

from engines.document.writers.usdm_writers.markdown.markdown_writer import MarkdownWriter

pytestmark = pytest.mark.asyncio


@pytest.fixture
def markdown_writer(write_options):
    return MarkdownWriter(options=write_options)


async def test_markdown_writer_name(markdown_writer):
    exts = markdown_writer.get_supported_extensions()
    assert ".md" in exts
    assert ".markdown" in exts
    mimes = markdown_writer.get_supported_media_types()
    assert "text/markdown" in mimes


async def test_markdown_write_basic(markdown_writer, sample_usdm_minimal):
    result = await markdown_writer.write(sample_usdm_minimal)
    assert isinstance(result, bytes)
    assert len(result) > 0


async def test_markdown_write_headings(markdown_writer, sample_usdm_document):
    result = await markdown_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "# " in text
    assert "## " in text


async def test_markdown_write_bold_italic(markdown_writer, sample_usdm_document):
    result = await markdown_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "**" in text or "*" in text


async def test_markdown_write_links(markdown_writer, sample_usdm_document):
    result = await markdown_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "https://example.com" in text


async def test_markdown_write_lists(markdown_writer, sample_usdm_document):
    result = await markdown_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "- " in text or "* " in text


async def test_markdown_write_tables(markdown_writer, sample_usdm_document):
    result = await markdown_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "|" in text
    assert "---" in text


async def test_markdown_write_code_blocks(markdown_writer, sample_usdm_document):
    result = await markdown_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "```" in text
    assert "print" in text


async def test_markdown_write_blockquotes(markdown_writer):
    from engines.document.models.base import ElementType
    from engines.document.models.media_types import MEDIA_TYPES
    from engines.document.models.usdm_models import (
        LogicalElement,
        ParagraphContent,
        QuoteContent,
        RichTextContent,
        RichTextSpan,
        USDMDocument,
    )

    quote_content = QuoteContent(
        elements=[
            LogicalElement(
                element_id="q1",
                element_type=ElementType.PARAGRAPH,
                content=ParagraphContent(
                    text=RichTextContent(spans=[RichTextSpan(text="Quoted text.")])
                ),
            )
        ]
    )
    doc = USDMDocument(
        document_id="bq-test",
        title="Blockquote Test",
        media_type=MEDIA_TYPES["markdown"],
        logical_elements=[
            LogicalElement(
                element_id="quote_1",
                element_type=ElementType.QUOTE,
                content=quote_content,
            )
        ],
    )
    result = await markdown_writer.write(doc)
    text = result.decode("utf-8")
    assert ">" in text


async def test_markdown_output_encoding(markdown_writer, sample_usdm_document):
    result = await markdown_writer.write(sample_usdm_document)
    assert isinstance(result, bytes)
    decoded = result.decode("utf-8")
    assert len(decoded) > 0
