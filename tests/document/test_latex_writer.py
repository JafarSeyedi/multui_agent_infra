import pytest

from engines.document.writers.usdm_writers.latex.latex_writer import LatexWriter

pytestmark = pytest.mark.asyncio


@pytest.fixture
def latex_writer(write_options):
    return LatexWriter(options=write_options)


async def test_latex_writer_name(latex_writer):
    exts = latex_writer.get_supported_extensions()
    assert ".tex" in exts
    assert ".latex" in exts
    mimes = latex_writer.get_supported_media_types()
    assert "application/x-latex" in mimes


async def test_latex_write_basic_document(latex_writer, sample_usdm_minimal):
    result = await latex_writer.write(sample_usdm_minimal)
    assert isinstance(result, bytes)
    assert len(result) > 0


async def test_latex_write_sections(latex_writer, sample_usdm_document):
    result = await latex_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "\\section" in text or "\\chapter" in text


async def test_latex_write_environments(latex_writer, sample_usdm_document):
    result = await latex_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "\\begin" in text
    assert "\\end" in text


async def test_latex_write_inline_math(latex_writer):
    from engines.document.models.base import ElementType
    from engines.document.models.media_types import MEDIA_TYPES
    from engines.document.models.usdm_models import (
        LogicalElement,
        MathContent,
        USDMDocument,
    )

    math_content = MathContent(latex="E = mc^2", display=False)
    doc = USDMDocument(
        document_id="math-test",
        title="Math Test",
        media_type=MEDIA_TYPES["latex"],
        logical_elements=[
            LogicalElement(
                element_id="math_1",
                element_type=ElementType.MATH,
                content=math_content,
            )
        ],
    )
    result = await latex_writer.write(doc)
    text = result.decode("utf-8")
    assert "$" in text


async def test_latex_write_display_math(latex_writer):
    from engines.document.models.base import ElementType
    from engines.document.models.media_types import MEDIA_TYPES
    from engines.document.models.usdm_models import (
        LogicalElement,
        MathContent,
        USDMDocument,
    )

    math_content = MathContent(latex="\\int_0^\\infty e^{-x} dx = 1", display=True)
    doc = USDMDocument(
        document_id="math-test",
        title="Math Test",
        media_type=MEDIA_TYPES["latex"],
        logical_elements=[
            LogicalElement(
                element_id="math_1",
                element_type=ElementType.MATH,
                content=math_content,
            )
        ],
    )
    result = await latex_writer.write(doc)
    text = result.decode("utf-8")
    assert "\\[" in text


async def test_latex_write_lists(latex_writer, sample_usdm_document):
    result = await latex_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "itemize" in text or "enumerate" in text


async def test_latex_write_tables(latex_writer, sample_usdm_document):
    result = await latex_writer.write(sample_usdm_document)
    text = result.decode("utf-8")
    assert "table" in text
    assert "tabular" in text


async def test_latex_output_has_document_class(latex_writer, sample_usdm_minimal):
    result = await latex_writer.write(sample_usdm_minimal)
    text = result.decode("utf-8")
    assert "\\documentclass" in text


async def test_latex_output_has_begin_end_document(latex_writer, sample_usdm_minimal):
    result = await latex_writer.write(sample_usdm_minimal)
    text = result.decode("utf-8")
    assert "\\begin{document}" in text
    assert "\\end{document}" in text
