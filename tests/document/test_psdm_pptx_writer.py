import sys
sys.path.insert(0, "/home/sjfs/autogen_project/multi_agent_infra")

import pytest
import zipfile
from io import BytesIO

from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.psdm_models import (
    PSDMDocument, PresentationProperties, Slide, SlideMaster, SlideLayout, Theme,
    PresentationSection,
)
from engines.document.models.usdm_models import (
    RichTextContent, ShapeContent, LogicalElement
)
from engines.document.models.base import ElementType
from engines.document.writers.psdm_writers.pptx.writer import PPTXWriter

pytestmark = pytest.mark.asyncio


@pytest.fixture
def sample_psdm_document():
    doc = PSDMDocument(
        title="Test Presentation",
        document_id="test-pptx-001",
        media_type=MEDIA_TYPES["pptx"],
    )
    doc.presentation_properties = PresentationProperties(
        slide_width=9144000,
        slide_height=6858000,
        paper_size="letter",
        orientation="landscape",
    )
    master = SlideMaster(name="Office Theme")
    layout = SlideLayout(name="Title Slide")
    master.layouts["Title Slide"] = layout
    doc.slide_masters["Office Theme"] = master

    theme = Theme(
        name="Office",
        color_scheme={"dk1": "#000000", "lt1": "#FFFFFF"},
        major_font="Calibri",
        minor_font="Calibri",
    )
    doc.theme = theme

    slide1 = Slide(
        slide_id="slide1",
        name="Title Slide",
        background_color="#FFFFFF",
    )
    shape = ShapeContent(
        shape_type="rectangle",
        x=1000000, y=1000000, width=5000000, height=3000000,
        name="Title",
        text=RichTextContent(spans=[]),
    )
    slide1.elements.append(LogicalElement(
        element_id="shape1",
        element_type=ElementType.SHAPE,
        content=shape,
    ))
    doc.slides.append(slide1)

    section = PresentationSection(name="Section 1", first_slide_id="slide1")
    doc.sections.append(section)

    return doc


@pytest.fixture
def pptx_writer():
    return PPTXWriter()


class TestPPTXWriterOutput:
    @pytest.mark.asyncio
    async def test_write_returns_bytes(self, pptx_writer, sample_psdm_document):
        result = await pptx_writer.write(sample_psdm_document)
        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_write_creates_valid_zip(self, pptx_writer, sample_psdm_document):
        result = await pptx_writer.write(sample_psdm_document)
        buf = BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "[Content_Types].xml" in names
            assert "_rels/.rels" in names
            assert "ppt/presentation.xml" in names
            assert "ppt/theme/theme1.xml" in names
            assert "ppt/slides/slide1.xml" in names

    @pytest.mark.asyncio
    async def test_write_includes_slide_master(self, pptx_writer, sample_psdm_document):
        result = await pptx_writer.write(sample_psdm_document)
        buf = BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert any("slideMasters/" in n for n in names)

    @pytest.mark.asyncio
    async def test_write_includes_layout(self, pptx_writer, sample_psdm_document):
        result = await pptx_writer.write(sample_psdm_document)
        buf = BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert any("slideLayouts/" in n for n in names)

    @pytest.mark.asyncio
    async def test_write_to_file(self, pptx_writer, sample_psdm_document, tmp_path):
        target = tmp_path / "test.pptx"
        await pptx_writer.write_to_file(sample_psdm_document, target)
        assert target.exists()
        assert target.stat().st_size > 0

    def test_get_supported_extensions(self, pptx_writer):
        exts = pptx_writer.get_supported_extensions()
        assert ".pptx" in exts
        assert ".potx" in exts

    def test_get_supported_media_types(self, pptx_writer):
        types = pptx_writer.get_supported_media_types()
        assert any("presentationml" in t for t in types)
