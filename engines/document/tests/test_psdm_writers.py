import sys
sys.path.insert(0, "/home/sjfs/autogen_project/multi_agent_infra")

import pytest

from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.psdm_models import (
    PSDMDocument, PresentationProperties, Slide,
)
from engines.document.writers.psdm_writers.revealjs.writer import RevealJSWriter
from engines.document.writers.psdm_writers.stagecraft.writer import StagecraftWriter
from engines.document.writers.psdm_writers.impressjs.writer import ImpressJSWriter
from engines.document.writers.psdm_writers.shower.writer import ShowerWriter
from engines.document.writers.psdm_writers.heedjs.writer import HeedJSWriter
from engines.document.writers.psdm_writers.deckjs.writer import DeckJSWriter

pytestmark = pytest.mark.asyncio


@pytest.fixture
def sample_presentation():
    doc = PSDMDocument(
        title="Test Presentation",
        document_id="test-html-001",
        media_type=MEDIA_TYPES["html"],
    )
    doc.presentation_properties = PresentationProperties(
        slide_width=1920.0,
        slide_height=1080.0,
        auto_advance=True,
    )
    doc.theme = None

    slide1 = Slide(
        slide_id="slide1",
        name="Title",
        background_color="#FFFFFF",
    )
    slide2 = Slide(
        slide_id="slide2",
        name="Content",
        background_color="#F5F5F5",
    )
    doc.slides.extend([slide1, slide2])
    return doc


class TestRevealJSWriter:
    def test_instantiation(self):
        writer = RevealJSWriter()
        assert writer is not None

    def test_supported_extensions(self):
        writer = RevealJSWriter()
        exts = writer.get_supported_extensions()
        assert ".html" in exts

    def test_supported_media_types(self):
        writer = RevealJSWriter()
        types = writer.get_supported_media_types()
        assert "text/html" in types

    @pytest.mark.asyncio
    async def test_write_returns_html(self, sample_presentation):
        writer = RevealJSWriter()
        result = await writer.write(sample_presentation)
        assert isinstance(result, bytes)
        html = result.decode("utf-8")
        assert len(html) > 0
        assert "reveal" in html.lower() or "html" in html.lower()

    @pytest.mark.asyncio
    async def test_write_stream(self, sample_presentation):
        writer = RevealJSWriter()
        chunks = []
        async for chunk in writer.write_stream(sample_presentation):
            chunks.append(chunk)
        assert len(chunks) == 1
        assert isinstance(chunks[0], bytes)

    @pytest.mark.asyncio
    async def test_write_to_file(self, sample_presentation, tmp_path):
        writer = RevealJSWriter()
        target = tmp_path / "reveal.html"
        await writer.write_to_file(sample_presentation, target)
        assert target.exists()
        content = target.read_text()
        assert len(content) > 0


class TestStagecraftWriter:
    def test_instantiation(self):
        writer = StagecraftWriter()
        assert writer is not None

    def test_supported_extensions(self):
        writer = StagecraftWriter()
        exts = writer.get_supported_extensions()
        assert ".html" in exts

    @pytest.mark.asyncio
    async def test_write_returns_html(self, sample_presentation):
        writer = StagecraftWriter()
        result = await writer.write(sample_presentation)
        assert isinstance(result, bytes)
        html = result.decode("utf-8")
        assert len(html) > 0
        assert "stage-slide" in html

    @pytest.mark.asyncio
    async def test_contains_navigation(self, sample_presentation):
        writer = StagecraftWriter()
        result = await writer.write(sample_presentation)
        html = result.decode("utf-8")
        assert "prevSlide" in html or "nextSlide" in html


class TestImpressJSWriter:
    def test_instantiation(self):
        writer = ImpressJSWriter()
        assert writer is not None

    def test_supported_extensions(self):
        writer = ImpressJSWriter()
        exts = writer.get_supported_extensions()
        assert ".html" in exts

    @pytest.mark.asyncio
    async def test_write_returns_html(self, sample_presentation):
        writer = ImpressJSWriter()
        result = await writer.write(sample_presentation)
        assert isinstance(result, bytes)
        html = result.decode("utf-8")
        assert len(html) > 0
        assert 'class="step"' in html

    @pytest.mark.asyncio
    async def test_step_data_attributes(self, sample_presentation):
        writer = ImpressJSWriter()
        result = await writer.write(sample_presentation)
        html = result.decode("utf-8")
        assert 'data-x="' in html
        assert 'data-y="' in html


class TestShowerWriter:
    def test_instantiation(self):
        writer = ShowerWriter()
        assert writer is not None

    def test_supported_extensions(self):
        writer = ShowerWriter()
        exts = writer.get_supported_extensions()
        assert ".html" in exts

    @pytest.mark.asyncio
    async def test_write_returns_html(self, sample_presentation):
        writer = ShowerWriter()
        result = await writer.write(sample_presentation)
        assert isinstance(result, bytes)
        html = result.decode("utf-8")
        assert len(html) > 0


class TestHeedJSWriter:
    def test_instantiation(self):
        writer = HeedJSWriter()
        assert writer is not None

    def test_supported_extensions(self):
        writer = HeedJSWriter()
        exts = writer.get_supported_extensions()
        assert ".html" in exts

    @pytest.mark.asyncio
    async def test_write_returns_html(self, sample_presentation):
        writer = HeedJSWriter()
        result = await writer.write(sample_presentation)
        assert isinstance(result, bytes)
        html = result.decode("utf-8")
        assert len(html) > 0


class TestDeckJSWriter:
    def test_instantiation(self):
        writer = DeckJSWriter()
        assert writer is not None

    def test_supported_extensions(self):
        writer = DeckJSWriter()
        exts = writer.get_supported_extensions()
        assert ".html" in exts

    @pytest.mark.asyncio
    async def test_write_returns_html(self, sample_presentation):
        writer = DeckJSWriter()
        result = await writer.write(sample_presentation)
        assert isinstance(result, bytes)
        html = result.decode("utf-8")
        assert len(html) > 0
