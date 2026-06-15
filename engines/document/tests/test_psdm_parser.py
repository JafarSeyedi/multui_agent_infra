import sys
sys.path.insert(0, "/home/sjfs/autogen_project/multi_agent_infra")

import pytest
import zipfile
from io import BytesIO

from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.psdm_models import PSDMDocument
from engines.document.parsers.psdm_parsers.pptx.parser import PPTXParser

pytestmark = pytest.mark.asyncio


def make_minimal_pptx() -> bytes:
    """Create a minimal valid PPTX ZIP in memory."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/ppt/presentation.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            '<Override PartName="/ppt/slideMasters/slideMaster1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
            '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
            '<Override PartName="/ppt/slides/slide1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
            '</Types>'
        ))
        zf.writestr("_rels/.rels", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
            '</Relationships>'
        ))
        zf.writestr("ppt/_rels/presentation.xml.rels", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>'
            '</Relationships>'
        ))
        zf.writestr("ppt/presentation.xml", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<p:sldSz cx="9144000" cy="6858000"/>'
            '<p:notesSz cx="6858000" cy="9144000"/>'
            '<p:showPr show="default"/>'
            '<p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst>'
            '</p:presentation>'
        ))
        zf.writestr("ppt/slideMasters/slideMaster1.xml", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">'
            '<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></p:bgPr></p:bg></p:cSld>'
            '</p:sldMaster>'
        ))
        zf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
            '</Relationships>'
        ))
        zf.writestr("ppt/slideLayouts/slideLayout1.xml", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Title Slide">'
            '<p:cSld><p:spTree></p:spTree></p:cSld>'
            '</p:sldLayout>'
        ))
        zf.writestr("ppt/slides/slide1.xml", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Title Slide">'
            '<p:cSld>'
            '<p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></p:bgPr></p:bg>'
            '</p:cSld>'
            '</p:sld>'
        ))
        zf.writestr("ppt/slides/_rels/slide1.xml.rels", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
            '</Relationships>'
        ))
    buf.seek(0)
    return buf.read()


class TestPPTXParser:
    @pytest.mark.asyncio
    async def test_parse_bytes_returns_document(self):
        parser = PPTXParser()
        data = make_minimal_pptx()
        doc = await parser.parse_bytes(data, "test-001", "test.pptx")
        assert isinstance(doc, PSDMDocument)
        assert doc.title == "test.pptx"
        assert doc.document_id == "test-001"
        assert doc.media_type == MEDIA_TYPES["pptx"]

    @pytest.mark.asyncio
    async def test_parse_slide_count(self):
        parser = PPTXParser()
        data = make_minimal_pptx()
        doc = await parser.parse_bytes(data, "test-001", "test.pptx")
        assert len(doc.slides) == 1

    @pytest.mark.asyncio
    async def test_parse_slide_master(self):
        parser = PPTXParser()
        data = make_minimal_pptx()
        doc = await parser.parse_bytes(data, "test-001", "test.pptx")
        assert len(doc.slide_masters) >= 1
        assert "Office Theme" in doc.slide_masters

    @pytest.mark.asyncio
    async def test_parse_presentation_properties(self):
        parser = PPTXParser()
        data = make_minimal_pptx()
        doc = await parser.parse_bytes(data, "test-001", "test.pptx")
        assert doc.presentation_properties.slide_width == 9144000
        assert doc.presentation_properties.slide_height == 6858000

    @pytest.mark.asyncio
    async def test_parse_sections(self):
        parser = PPTXParser()
        data = make_minimal_pptx()
        doc = await parser.parse_bytes(data, "test-001", "test.pptx")
        assert hasattr(doc, 'sections')
        assert isinstance(doc.sections, list)

    @pytest.mark.asyncio
    async def test_supported_extensions(self):
        parser = PPTXParser()
        exts = parser.supported_extensions
        assert ".pptx" in exts
        assert ".pptm" in exts
