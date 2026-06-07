import pytest

from engines.document.writers.usdm_writers.html.html_writer import HTMLWriter

pytestmark = pytest.mark.asyncio


@pytest.fixture
def html_writer(write_options):
    return HTMLWriter(options=write_options)


async def test_html_writer_name_and_extensions(html_writer):
    exts = html_writer.get_supported_extensions()
    assert ".html" in exts
    assert ".htm" in exts
    mimes = html_writer.get_supported_media_types()
    assert "text/html" in mimes


async def test_html_write_basic_document(html_writer, sample_usdm_minimal):
    result = await html_writer.write(sample_usdm_minimal)
    assert isinstance(result, bytes)
    assert len(result) > 0
    text = result.decode("utf-8")
    assert "<!DOCTYPE html>" in text


async def test_html_write_headings(html_writer, sample_usdm_document):
    result = await html_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "<h1>" in text
    assert "<h2>" in text


async def test_html_write_paragraphs_with_formatting(html_writer, sample_usdm_document):
    result = await html_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "<p>" in text
    assert "<strong>" in text or "<b>" in text


async def test_html_write_links(html_writer, sample_usdm_document):
    result = await html_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert 'href="https://example.com"' in text


async def test_html_write_images(html_writer, sample_usdm_document):
    result = await html_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "<img" in text
    assert 'src="test.png"' in text


async def test_html_write_lists(html_writer, sample_usdm_document):
    result = await html_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "<ul>" in text
    assert "<ol>" in text


async def test_html_write_tables(html_writer, sample_usdm_document):
    result = await html_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "<table>" in text
    assert "<th>" in text or "<td>" in text


async def test_html_write_code_blocks(html_writer, sample_usdm_document):
    result = await html_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "<pre><code" in text
    assert "print" in text


async def test_html_write_stylesheet(html_writer, sample_usdm_document):
    result = await html_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "<style>" in text


async def test_html_write_document_title(html_writer, sample_usdm_document):
    result = await html_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "<title>Test Document</title>" in text


async def test_html_output_is_valid_html5(html_writer, sample_usdm_document):
    result = await html_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert text.strip().startswith("<!DOCTYPE html>")
    assert "<html" in text
    assert "<head>" in text
    assert "<body>" in text
    assert "</body>" in text
    assert "</html>" in text


async def test_html_write_empty_document(html_writer):
    from engines.document.models.media_types import MEDIA_TYPES
    from engines.document.models.usdm_models import USDMDocument

    doc = USDMDocument(
        document_id="empty-test",
        title="Empty",
        media_type=MEDIA_TYPES["html"],
    )
    result = await html_writer.write(doc)
    assert isinstance(result, bytes)
    assert len(result) > 0
    text = result.decode("utf-8")
    assert "<!DOCTYPE html>" in text
