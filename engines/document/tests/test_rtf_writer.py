import pytest

from engines.document.writers.usdm_writers.rtf.rtf_writer import RTFWriter

pytestmark = pytest.mark.asyncio


@pytest.fixture
def rtf_writer(write_options):
    return RTFWriter(options=write_options)


async def test_rtf_writer_name(rtf_writer):
    exts = rtf_writer.get_supported_extensions()
    assert ".rtf" in exts
    mimes = rtf_writer.get_supported_media_types()
    assert "application/rtf" in mimes


async def test_rtf_write_basic(rtf_writer, sample_usdm_minimal):
    result = await rtf_writer.write(sample_usdm_minimal)
    assert isinstance(result, bytes)
    assert len(result) > 0


async def test_rtf_write_character_formatting(rtf_writer, sample_usdm_document):
    result = await rtf_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "\\b" in text


async def test_rtf_write_paragraphs(rtf_writer, sample_usdm_document):
    result = await rtf_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "\\par" in text


async def test_rtf_write_tables(rtf_writer, sample_usdm_document):
    result = await rtf_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "\\trowd" in text or "\\cell" in text


async def test_rtf_output_starts_with_rtf1(rtf_writer, sample_usdm_minimal):
    result = await rtf_writer.write(sample_usdm_minimal)
    text = result.decode("utf-8")
    assert text.strip().startswith("{\\rtf1")


async def test_rtf_output_ends_with_brace(rtf_writer, sample_usdm_minimal):
    result = await rtf_writer.write(sample_usdm_minimal)
    text = result.decode("utf-8")
    assert text.strip().endswith("}")
