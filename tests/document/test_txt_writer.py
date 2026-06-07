import pytest

from engines.document.writers.usdm_writers.txt.txt_writer import TXTWriter

pytestmark = pytest.mark.asyncio


@pytest.fixture
def txt_writer(write_options):
    return TXTWriter(options=write_options)


async def test_txt_writer_name(txt_writer):
    exts = txt_writer.get_supported_extensions()
    assert ".txt" in exts
    assert ".text" in exts
    mimes = txt_writer.get_supported_media_types()
    assert "text/plain" in mimes


async def test_txt_write_basic(txt_writer, sample_usdm_minimal):
    result = await txt_writer.write(sample_usdm_minimal)
    assert isinstance(result, bytes)
    assert len(result) > 0


async def test_txt_write_headings(txt_writer, sample_usdm_document):
    result = await txt_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "# " in text


async def test_txt_write_paragraphs(txt_writer, sample_usdm_document):
    result = await txt_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "Normal text" in text


async def test_txt_write_lists(txt_writer, sample_usdm_document):
    result = await txt_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "- " in text or "1. " in text


async def test_txt_write_encoding(txt_writer, sample_usdm_document):
    result = await txt_writer.write(sample_usdm_document)
    assert isinstance(result, bytes)
    decoded = result.decode("utf-8")
    assert len(decoded) > 0


async def test_txt_output_is_plain_text(txt_writer, sample_usdm_document):
    result = await txt_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "<" not in text or text.count("<") == 0
