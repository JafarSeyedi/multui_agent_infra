# engines/document/writers/pptx_writer/writer.py
"""
PPTX writer – converts a PSDMDocument into a valid .pptx ZIP archive.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, AsyncIterator

from ..base import BaseDocumentWriter, WriteOptions
from ...models.psdm_models import (
    PSDMDocument, Slide, SlideMaster, SlideLayout, Theme,
    NotesSlide, SlideComment, MediaReference,
)
from ...models.usdm_models import (
    ImageContent, ChartContent, DrawingContent, OLEObjectContent,
    LogicalElement, ElementType,
)
from .constants import NAMESPACES
from .slide_writer import write_slide
from .master_writer import write_master, write_layout
from .theme_writer import write_theme
from .notes_writer import write_notes_slide
from .comments_writer import write_comments
from .diagram_writer import write_diagram
from .media_writer import build_slide_media_rels, collect_media_files
from .ole_writer import collect_ole_binaries
from .relationship_utils import build_rels_element, rels_to_xml
from . import drawingml_helpers  # noqa (used by sub‑writers)


class PPTXWriter(BaseDocumentWriter):
    """Writes a PSDMDocument to a PowerPoint .pptx file."""

    def __init__(self, options: Optional[WriteOptions] = None):
        super().__init__(options or WriteOptions())
        self._next_rid = 1          # global relationship id counter
        self._media_counter = 0     # for unique media file names
        self._chart_counter = 0
        self._diagram_counter = 0
        self._ole_counter = 0

    # ── public API ──────────────────────────────────────────────
    async def write_stream(self, document: PSDMDocument) -> AsyncIterator[bytes]:
        data = await self.write(document)
        yield data

    async def write(self, document: PSDMDocument) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            self._build_package(zf, document)
        return buf.getvalue()

    async def write_to_file(
        self, document: PSDMDocument, target: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        data = await self.write(document)
        target.write_bytes(data)

    def get_supported_media_types(self) -> list[str]:
        return [
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.openxmlformats-officedocument.presentationml.template",
            "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
        ]

    def get_supported_extensions(self) -> list[str]:
        return [".pptx", ".pptm", ".potx", ".potm"]

    # ── internal builder ────────────────────────────────────────
    def _next_id(self) -> int:
        rid = self._next_rid
        self._next_rid += 1
        return rid

    def _build_package(self, zf: zipfile.ZipFile, doc: PSDMDocument) -> None:
        # 1. [Content_Types].xml
        content_types = self._build_content_types(doc)
        zf.writestr("[Content_Types].xml", self._to_xml(content_types))

        # 2. _rels/.rels (package rels)
        package_rels = build_rels_element([
            ("rId1",
             "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
             "ppt/presentation.xml"),
        ])
        zf.writestr("_rels/.rels", rels_to_xml(package_rels))

        # 3. ppt/presentation.xml
        pres_xml, pres_rels_list = self._build_presentation(doc)
        zf.writestr("ppt/presentation.xml", self._to_xml(pres_xml))

        # ppt/_rels/presentation.xml.rels
        pres_rels = build_rels_element(pres_rels_list)
        zf.writestr("ppt/_rels/presentation.xml.rels", rels_to_xml(pres_rels))

        # 4. Theme
        if doc.theme:
            theme_xml = write_theme(doc.theme)
            zf.writestr("ppt/theme/theme1.xml", self._to_xml(theme_xml))

        # 5. Masters & layouts
        for master_name, master in doc.slide_masters.items():
            master_xml = write_master(master)
            master_path = f"ppt/slideMasters/{master_name}.xml"
            zf.writestr(master_path, self._to_xml(master_xml))

            # Layouts
            layout_rels: List[Tuple[str, str, str]] = []
            for layout_name, layout in master.layouts.items():
                layout_xml = write_layout(layout, master_name)
                layout_path = f"ppt/slideLayouts/{layout_name}.xml"
                zf.writestr(layout_path, self._to_xml(layout_xml))
                # relationship for this layout inside master rels
                rid = f"rId{self._next_id()}"
                layout_rels.append((
                    rid,
                    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout",
                    f"../slideLayouts/{layout_name}.xml"
                ))

            # master rels
            master_rel_path = f"ppt/slideMasters/_rels/{master_name}.xml.rels"
            master_rels_elem = build_rels_element(layout_rels)
            zf.writestr(master_rel_path, rels_to_xml(master_rels_elem))

        # 6. Slides & their dependencies
        slide_rids: List[Tuple[str, str, str]] = []
        for idx, slide in enumerate(doc.slides):
            slide_file = f"slide{idx+1}.xml"
            slide_path = f"ppt/slides/{slide_file}"
            slide_xml = write_slide(slide)
            zf.writestr(slide_path, self._to_xml(slide_xml))

            # Build relationships for this slide
            slide_rel_items = self._build_slide_relationships(slide, idx)
            slide_rel_elem = build_rels_element(slide_rel_items)
            rel_dir = f"ppt/slides/_rels/{slide_file}.rels"
            zf.writestr(rel_dir, rels_to_xml(slide_rel_elem))

            # Link from presentation
            rid = f"rId{self._next_id()}"
            slide_rids.append((
                rid,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide",
                f"slides/{slide_file}"
            ))

            # Write notes if present
            if slide.notes:
                notes_rid = f"rId{self._next_id()}"
                notes_file = f"notesSlide{idx+1}.xml"
                notes_xml = write_notes_slide(slide.notes, slide_rid=notes_rid)
                zf.writestr(f"ppt/notesSlides/{notes_file}", self._to_xml(notes_xml))
                # add notes relationship to slide rels later (we already wrote slide rels, need to append)
                # For simplicity, we'll include it when building the slide rels above, so we adjust later.
                # We'll handle that inside _build_slide_relationships.

            # Write comments if present
            if slide.comments:
                comments_file = f"comment{idx+1}.xml"
                comments_xml = write_comments(slide.comments)
                zf.writestr(f"ppt/comments/{comments_file}", self._to_xml(comments_xml))
                # relationship added in slide rels

        # 7. Write images, media, charts, diagrams, OLE objects
        self._write_binary_parts(zf, doc)

        # 8. Section info (store in presentation.xml via <p:sectionLst>)
        # We'll include it when building presentation.

        # Update presentation.xml with slide references and sections
        self._finalize_presentation(pres_xml, slide_rids, doc.sections)

    def _build_presentation(self, doc: PSDMDocument) -> Tuple[Element, List[Tuple[str, str, str]]]:
        """Create <p:presentation> and collect its relationships."""
        from xml.etree.ElementTree import Element, SubElement
        P = f"{{{NAMESPACES['p']}}}"
        A = f"{{{NAMESPACES['a']}}}"
        R = f"{{{NAMESPACES['r']}}}"

        pres = Element(f"{P}presentation")
        # Presentation attributes from parsed meta
        for attr, val in doc._meta.get("presentation_attrs", {}).items():
            pres.set(attr, str(val))

        # Slide size
        sldSz = SubElement(pres, f"{P}sldSz", {
            "cx": str(doc.presentation_properties.slide_width or 9144000),
            "cy": str(doc.presentation_properties.slide_height or 6858000),
        })
        # Notes size (default)
        SubElement(pres, f"{P}notesSz", {"cx": "6858000", "cy": "9144000"})

        # Show properties
        showPr = SubElement(pres, f"{P}showPr")
        showPr.set("show", doc.presentation_properties.show_type.value)
        if doc.presentation_properties.loop:
            showPr.set("loop", "1")

        # Default text style (if theme provides none)
        # We don't write inline defaultTextStyle; it's in the theme.

        # Relationships collected: theme, masters, slides (to be filled later)
        rels: List[Tuple[str, str, str]] = []
        # Theme
        if doc.theme:
            rid = f"rId{self._next_id()}"
            rels.append((
                rid,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme",
                "theme/theme1.xml"
            ))
        # Slide masters
        for master_name in doc.slide_masters:
            rid = f"rId{self._next_id()}"
            rels.append((
                rid,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster",
                f"slideMasters/{master_name}.xml"
            ))

        return pres, rels

    def _finalize_presentation(self, pres_xml, slide_rids, sections):
        """Add <p:sldIdLst> and <p:sectionLst> to the presentation element."""
        from xml.etree.ElementTree import SubElement
        P = f"{{{NAMESPACES['p']}}}"
        R = f"{{{NAMESPACES['r']}}}"

        # Slide ID list
        sldIdLst = SubElement(pres_xml, f"{P}sldIdLst")
        for rid, _, _ in slide_rids:
            sid = self._next_id()  # unique slide id
            SubElement(sldIdLst, f"{P}sldId", {f"{R}id": rid, "id": str(sid)})

        # Sections
        if sections:
            secLst = SubElement(pres_xml, f"{P}sectionLst")
            for sec in sections:
                # Find the rId of the first slide in that section
                # We assume sec.first_slide_id is the rId (as stored by parser)
                first_rid = sec.first_slide_id
                if first_rid:
                    SubElement(secLst, f"{P}section", {
                        "name": sec.name,
                        f"{R}id": first_rid
                    })

    def _build_slide_relationships(self, slide: Slide, slide_index: int) -> List[Tuple[str, str, str]]:
        """Return (rId, type, target) for all parts referenced by this slide."""
        rels: List[Tuple[str, str, str]] = []

        # Layout (from slide.layout)
        if slide.layout:
            rid = f"rId{self._next_id()}"
            layout_name = slide.layout.name
            rels.append((
                rid,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout",
                f"../slideLayouts/{layout_name}.xml"
            ))
            # Store the rId on the layout so slide_writer can use it? Not needed.

        # Notes
        if slide.notes:
            rid = f"rId{self._next_id()}"
            rels.append((
                rid,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide",
                f"../notesSlides/notesSlide{slide_index+1}.xml"
            ))

        # Comments
        if slide.comments:
            rid = f"rId{self._next_id()}"
            rels.append((
                rid,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
                f"../comments/comment{slide_index+1}.xml"
            ))

        # Images – iterate over elements and collect unique rIds
        img_rids: Dict[str, str] = {}  # rId -> target path in package
        self._collect_image_rels(slide.elements, img_rids)
        for rid, target in img_rids.items():
            rels.append((
                rid,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                target
            ))

        # Charts
        chart_rels = self._collect_chart_rels(slide.elements)
        rels.extend(chart_rels)

        # Diagrams
        diag_rels = self._collect_diagram_rels(slide.elements)
        rels.extend(diag_rels)

        # Media
        media_rels_map = build_slide_media_rels(slide)
        for rid, target in media_rels_map.items():
            rels.append((
                rid,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/media",
                target
            ))

        # OLE objects
        ole_rels = self._collect_ole_rels(slide.elements)
        rels.extend(ole_rels)

        return rels

    def _collect_image_rels(self, elements: List[LogicalElement], out: Dict[str, str]) -> None:
        for elem in elements:
            if elem.element_type == ElementType.IMAGE and isinstance(elem.content, ImageContent):
                img = elem.content
                if img.src and not img.src.startswith("ppt/"):
                    rid = f"rId{self._next_id()}"
                    out[rid] = img.src  # img.src currently holds the relative path, we need to store target
                    img.src = rid       # replace with rId for slide XML
                # if already a rId, keep it
            elif elem.element_type == ElementType.SHAPE:
                shape = elem.content
                # shape may have fill image? not handled yet

    def _collect_chart_rels(self, elements: List[LogicalElement]) -> List[Tuple[str, str, str]]:
        rels = []
        for elem in elements:
            if elem.element_type == ElementType.CHART and isinstance(elem.content, ChartContent):
                chart = elem.content
                rid = f"rId{self._next_id()}"
                chart._meta["rId"] = rid
                # target will be written in _write_binary_parts
                chart_file = f"../charts/chart{self._chart_counter+1}.xml"
                rels.append((
                    rid,
                    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart",
                    chart_file
                ))
                self._chart_counter += 1
        return rels

    def _collect_diagram_rels(self, elements: List[LogicalElement]) -> List[Tuple[str, str, str]]:
        rels = []
        for elem in elements:
            if elem.element_type == ElementType.DRAWING and isinstance(elem.content, DrawingContent):
                drawing = elem.content
                rid = f"rId{self._next_id()}"
                drawing._meta["rId"] = rid
                diag_file = f"../diagrams/diagram{self._diagram_counter+1}.xml"
                rels.append((
                    rid,
                    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagram",
                    diag_file
                ))
                self._diagram_counter += 1
        return rels

    def _collect_ole_rels(self, elements: List[LogicalElement]) -> List[Tuple[str, str, str]]:
        rels = []
        for elem in elements:
            if elem.element_type == ElementType.OLE_OBJECT and isinstance(elem.content, OLEObjectContent):
                ole = elem.content
                rid = f"rId{self._next_id()}"
                ole.relationship_id = rid
                target = f"../embeddings/oleObject{self._ole_counter+1}.bin"
                rels.append((
                    rid,
                    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject",
                    target
                ))
                self._ole_counter += 1
        return rels

    def _write_binary_parts(self, zf: zipfile.ZipFile, doc: PSDMDocument) -> None:
        # Media files
        media_files = collect_media_files(doc.slides)
        for path, data in media_files.items():
            zf.writestr(f"ppt/{path}", data)

        # OLE objects
        ole_files = collect_ole_binaries(doc.slides)
        for path, data in ole_files.items():
            zf.writestr(path, data)

        # Charts – regenerate chart XML from ChartContent
        for slide in doc.slides:
            for elem in slide.elements:
                if elem.element_type == ElementType.CHART and isinstance(elem.content, ChartContent):
                    chart = elem.content
                    rid = chart._meta.get("rId")
                    if rid:
                        # Serialise chart to XML (reuse spreadsheet chart writer or similar)
                        chart_xml = self._write_chart_xml(chart)
                        filename = f"charts/chart{self._chart_counter}.xml"
                        zf.writestr(f"ppt/{filename}", chart_xml)
                        self._chart_counter += 1

        # Diagrams
        for slide in doc.slides:
            for elem in slide.elements:
                if elem.element_type == ElementType.DRAWING and isinstance(elem.content, DrawingContent):
                    drawing = elem.content
                    rid = drawing._meta.get("rId")
                    if rid:
                        diag_xml = write_diagram(drawing)
                        filename = f"diagrams/diagram{self._diagram_counter}.xml"
                        zf.writestr(f"ppt/{filename}", diag_xml)
                        self._diagram_counter += 1

    def _write_chart_xml(self, chart: ChartContent) -> bytes:
        """Produce the chart XML part. Reuses the spreadsheet chart writer logic."""
        # Import the chart builder (from spreadsheet writer) to generate XML.
        # For brevity, we assume a function write_chart exists.
        from ..spreadsheet_writer.xlsx.charts_writer import write_chart_xml
        return write_chart_xml(chart)

    def _build_content_types(self, doc: PSDMDocument) -> Element:
        """Create [Content_Types].xml."""
        from xml.etree.ElementTree import Element, SubElement
        ns = "http://schemas.openxmlformats.org/package/2006/content-types"
        ct = Element("Types", {"xmlns": ns})
        # Default extensions
        defaults = {
            "xml": "application/xml",
            "rels": "application/vnd.openxmlformats-package.relationships+xml",
            "png": "image/png",
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "bin": "application/vnd.openxmlformats-officedocument.oleObject",
        }
        for ext, mime in defaults.items():
            SubElement(ct, "Default", {"Extension": ext, "ContentType": mime})

        # Override for specific parts
        overrides = [
            ("/ppt/presentation.xml",
             "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"),
            ("/ppt/slideMasters/",       "application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"),
            ("/ppt/slideLayouts/",       "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"),
            ("/ppt/slides/",             "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"),
            ("/ppt/notesSlides/",        "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"),
            ("/ppt/theme/theme1.xml",    "application/vnd.openxmlformats-officedocument.theme+xml"),
            ("/ppt/comments/",           "application/vnd.openxmlformats-officedocument.presentationml.comments+xml"),
            ("/ppt/charts/",             "application/vnd.openxmlformats-officedocument.drawingml.chart+xml"),
            ("/ppt/diagrams/",           "application/vnd.openxmlformats-officedocument.drawingml.diagramData+xml"),
        ]
        for path, mime in overrides:
            SubElement(ct, "Override", {"PartName": path, "ContentType": mime})

        return ct

    @staticmethod
    def _to_xml(elem: Element) -> bytes:
        from xml.etree.ElementTree import tostring
        return tostring(elem, xml_declaration=True, encoding="UTF-8", method="xml")