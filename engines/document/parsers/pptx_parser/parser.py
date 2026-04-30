# engines/document/parsers/pptx_parser/parser.py
"""
Main PPTX parser: opens the ZIP, coordinates all sub-parsers, and assembles
a complete PSDMDocument ready for round‑trip.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from xml.etree import ElementTree as ET

from ..base import BaseDocumentParser, ParseOptions
from ...models.base import BaseDocument
from ...models.psdm_models import (
    PSDMDocument,
    Slide,
    SlideLayout,
    SlideMaster,
    Theme,
    PresentationProperties,
    NotesSlide,
    Section,
)
from ...models.media_types import DocumentStandard  # assuming PSDM added
from ...models.usdm_models import (
    LogicalElement, ElementType, ImageContent, ChartContent,
)

from .constants import NAMESPACES, REL_TYPE
from .relationship_utils import (
    load_rels,
    get_target_for_id,
    get_targets_by_type,
    resolve_slide_rels,
    resolve_path,
    resolve_image_path,
)
from .slide_builder import build_slide
from .master_parser import parse_master, parse_layout
from .theme_parser import parse_theme
from .notes_parser import parse_notes_slide
from .comments_parser import parse_comments
from .animation_parser import parse_slide_transition, parse_slide_animations  # not needed here, slide builder does it
from ..drawingml.chart_ref_parser import resolve_chart
from ..drawingml.diagram_parser import resolve_diagram
# Inside the slide processing loop, right before appending slide to the list:
from .media_parser import load_media_binaries

NS = NAMESPACES


class PPTXParser(BaseDocumentParser):
    """Complete PPTX parser – produces PSDMDocument."""

    name = "pptx"
    supported_extensions = (".pptx", ".pptm", ".potx", ".potm")

    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None,
    ) -> BaseDocument:
        options = options or ParseOptions()
        doc = await self._parse_to_psdm(data, source_name, options)
        doc.document_id = document_id
        doc.metadata = metadata or {}
        doc.title = source_name or document_id
        # media_type detection
        from ...models.media_detection import detect_media_type
        doc.media_type = detect_media_type(path=source_name, data=data)
        doc.file_extension = Path(source_name).suffix if source_name else ".pptx"
        return doc

    async def parse_path(
        self,
        path: Union[str, Path],
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None,
    ) -> BaseDocument:
        file_path = Path(path)
        data = file_path.read_bytes()
        return await self.parse_bytes(data, document_id, file_path.name, metadata, options)

    async def parse_stream(
        self,
        stream: AsyncIterator[bytes],
        document_id: str,
        source_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None,
    ) -> BaseDocument:
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    async def _parse_to_psdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> PSDMDocument:
        zip_data = io.BytesIO(data)
        with zipfile.ZipFile(zip_data, "r") as zf:
            # 1. Load package-level relationships
            package_rels = load_rels(zf, "_rels/.rels")
            # 2. Presentation part is usually "ppt/presentation.xml"
            pres_path = "ppt/presentation.xml"
            pres_xml = self._load_xml(zf, pres_path)
            # 3. Presentation relationships (ppt/_rels/presentation.xml.rels)
            pres_rels = load_rels(zf, "ppt/_rels/presentation.xml.rels")

            # 4. Parse presentation attributes
            pres_attrs = dict(pres_xml.attrib)
            properties = PresentationProperties()
            sld_sz = pres_xml.find("p:sldSz", NS)
            if sld_sz is not None:
                properties.slide_width = int(sld_sz.get("cx", "0"))
                properties.slide_height = int(sld_sz.get("cy", "0"))
            notes_sz = pres_xml.find("p:notesSz", NS)
            if notes_sz is not None:
                # store in properties? we can extend, but for now keep in meta
                pass
            # Show properties
            show_pr = pres_xml.find("p:showPr", NS)
            if show_pr is not None:
                properties.loop = show_pr.get("loop") == "1"
                properties.show_type = show_pr.get("show") or "default"
            # Default text style
            def_text_style = None
            # (could be extracted from <p:defaultTextStyle>)

            # 5. Parse theme (theme1.xml)
            theme_xml = None
            theme_rel_target = get_target_for_id(pres_rels, list(pres_rels.keys())[0])  # find theme relationship
            # Usually the first relationship of type "theme" in pres_rels.
            theme_rels = get_targets_by_type(pres_rels, REL_TYPE["theme"])
            if theme_rels:
                theme_path = resolve_path("ppt", theme_rels[0])
                theme_xml = self._load_xml(zf, theme_path, optional=True)

            theme = parse_theme(theme_xml) if theme_xml is not None else Theme()

            # 6. Parse slide masters and layouts
            # Master relationships: type slideMaster
            master_rels_targets = get_targets_by_type(pres_rels, REL_TYPE["slideMaster"])
            masters: Dict[str, SlideMaster] = {}
            for target in master_rels_targets:
                master_path = resolve_path("ppt", target)
                master_xml = self._load_xml(zf, master_path)
                if master_xml is None:
                    continue
                # Get the master's own relationships for layouts
                master_rels = load_rels(zf, _rels_path_for(master_path))
                # Parse layouts first (they are separate parts linked from master relationships)
                layouts: Dict[str, SlideLayout] = {}
                layout_targets = get_targets_by_type(master_rels, REL_TYPE["slideLayout"])
                for lt in layout_targets:
                    layout_path = resolve_path(_dir_of(master_path), lt)
                    layout_xml = self._load_xml(zf, layout_path)
                    if layout_xml is not None:
                        layout = parse_layout(layout_xml)
                        # The layout's master_name is the master name; set it
                        layout.master_name = path_to_name(master_path)
                        layouts[layout.name] = layout
                master = parse_master(master_xml, layouts, path_to_name(master_path))
                masters[master.name] = master

            # 7. Parse slides
            slides: List[Slide] = []
            slide_rels_targets = get_targets_by_type(pres_rels, REL_TYPE["slide"])
            # Sort by order? Typically they appear in order in relationships.
            # We'll keep insertion order from get_targets_by_type (which may be arbitrary).
            # Better to order by <p:sldIdLst> in presentation.xml.
            sld_id_lst = pres_xml.find("p:sldIdLst", NS)
            ordered_ids = []
            if sld_id_lst is not None:
                for sld_id_elem in sld_id_lst.findall("p:sldId", NS):
                    r_id = sld_id_elem.get(f"{{{NS['r']}}}id")
                    if r_id:
                        ordered_ids.append(r_id)
            # Build slide list respecting order
            for r_id in ordered_ids:
                target = get_target_for_id(pres_rels, r_id)
                if not target:
                    continue
                slide_path = resolve_path("ppt", target)
                slide_xml = self._load_xml(zf, slide_path)
                if slide_xml is None:
                    continue
                # Slide relationships
                slide_rels = resolve_slide_rels(zf, slide_path)

                # Build slide (without resolving layout yet)
                slide = build_slide(
                    slide_xml,
                    slide_path,
                    zf,
                    slide_rels,
                    {},  # layouts will be resolved later
                    masters,
                    pres_rels,
                )

                # Resolve layout for this slide
                layout_target = get_target_for_id(slide_rels, "layout")  # standard relationship
                # Actually the layout relation is stored in the slide's own rels with type "layout"
                layout_r_id = None
                for rid, (rtype, _) in slide_rels.items():
                    if rtype.endswith("/slideLayout"):
                        layout_r_id = rid
                        break
                if layout_r_id:
                    layout_target = get_target_for_id(slide_rels, layout_r_id)
                    # Find layout object by name (the target is something like "../slideLayouts/slideLayout1.xml")
                    layout_name = path_to_name(layout_target) if layout_target else None
                    if layout_name and layout_name in layouts:
                        slide.layout = layouts[layout_name]

                # Resolve images
                for elem in slide.elements:
                    if elem.element_type == ElementType.IMAGE and isinstance(elem.content, ImageContent):
                        resolve_image(
                            elem.content,
                            slide_rels,
                            zf,
                            base_path=_dir_of(slide_path),
                        )
                    elif elem.element_type == ElementType.CHART and isinstance(elem.content, ChartContent):
                        r_id = getattr(elem.content, '_chart_rId', None)
                        if r_id:
                            chart = resolve_chart(
                                r_id,
                                slide_rels,
                                zf,
                                relationship_target_resolver=lambda base, tgt: resolve_path(_dir_of(slide_path), tgt)
                            )
                            if chart:
                                # Replace placeholder with fully resolved chart
                                elem.content.chart_type = chart.chart_type
                                elem.content.grouping = chart.grouping
                                elem.content.direction = chart.direction
                                elem.content.title = chart.title
                                elem.content.series = chart.series
                                elem.content.category_axis = chart.category_axis
                                elem.content.value_axis = chart.value_axis
                                if hasattr(chart, '_chart_rId'):
                                    delattr(elem.content, '_chart_rId')
                            else:
                                # Remove the element if chart not resolved? better keep placeholder
                                pass
                    elif elem.element_type == ElementType.DRAWING and isinstance(elem.content, DrawingContent):
                        diag_rId = getattr(elem.content, '_diagram_rId', None)
                        if diag_rId:
                            resolved = resolve_diagram(
                                diag_rId,
                                {rid: tgt for rid, (_, tgt) in slide_rels.items()},
                                zf,
                                _dir_of(slide_path),
                                rel_resolver=lambda base, t: resolve_path(base, t)
                            )
                            if resolved:
                                elem.content.vector_data = resolved.vector_data
                                # optionally copy width/height
                                delattr(elem.content, '_diagram_rId')
                    # if elem.element_type == ElementType.SHAPE and hasattr(elem.content, '_meta') and isinstance(elem.content, ShapeContent):
                    #     r_id = elem.content._meta.get("media_link_rId")
                    #     if r_id:
                    #         # Create a MediaReference for it
                    #         media_ref = MediaReference(
                    #             relationship_id=r_id,
                    #             media_type=_guess_media_type_from_rel(r_id, slide_rels),  # helper needed
                    #         )
                    #         slide.media_references.append(media_ref)
                    #         elem._meta["media_reference"] = media_ref
            
                load_media_binaries(slide.media_references, slide.elements, zf)
                load_ole_binaries(slide.elements, slide_rels, zf, _dir_of(slide_path))

                # Resolve notes
                notes_target = get_target_for_id(slide_rels, "notesSlide")  # relationship type?
                notes_r_id = None
                for rid, (rtype, _) in slide_rels.items():
                    if rtype.endswith("/notesSlide"):
                        notes_r_id = rid
                        break
                if notes_r_id:
                    notes_target = get_target_for_id(slide_rels, notes_r_id)
                    notes_path = resolve_path(_dir_of(slide_path), notes_target)
                    notes_xml = self._load_xml(zf, notes_path, optional=True)
                    if notes_xml is not None:
                        slide.notes = parse_notes_slide(notes_xml)

                # Resolve comments
                comments_r_id = None
                for rid, (rtype, _) in slide_rels.items():
                    if rtype.endswith("/comments"):
                        comments_r_id = rid
                        break
                if comments_r_id:
                    comments_target = get_target_for_id(slide_rels, comments_r_id)
                    comments_path = resolve_path(_dir_of(slide_path), comments_target)
                    comments_xml = self._load_xml(zf, comments_path, optional=True)
                    if comments_xml is not None:
                        slide.comments = parse_comments(comments_xml)

                slides.append(slide)

            # 8. Sections (if any)
            sections = self._parse_sections(pres_xml)
            if sections:
                self._map_sections_to_slides(sections, ordered_ids, slides)            

            # 9. Assemble PSDMDocument
            psdm = PSDMDocument(
                slides=slides,
                slide_masters=masters,
                presentation_properties=properties,
                theme=theme,
            )
            # Add any extra parsed data
            if pres_attrs:
                psdm._meta["presentation_attrs"] = pres_attrs
            return psdm

    def _parse_sections(self, pres_xml: ET.Element) -> List[Section]:
        sections = []
        sec_lst = pres_xml.find("p:sectionLst", NS)
        if sec_lst is not None:
            for sec_elem in sec_lst.findall("p:section", NS):
                name = sec_elem.get("name", "")
                first_slide_rId = sec_elem.get(f"{{{NS['r']}}}id")  # actually the attribute is "firstSlide" which is a relationship ID
                # The attribute is named "firstSlide" without namespace – we'll use that.
                # Let's just use sec_elem.get("firstSlide")
                first = sec_elem.get("firstSlide") or sec_elem.get(f"{{{NS['r']}}}id")
                sections.append(Section(name=name, first_slide_id=first or ""))
        return sections

    @staticmethod
    def _map_sections_to_slides(
        sections: List[Section],
        ordered_rids: List[str],
        slides: List[Slide],
    ) -> None:
        if not sections or not ordered_rids or not slides:
            return
        # Map each relationship ID to its index in the slide order
        rid_to_idx = {rid: idx for idx, rid in enumerate(ordered_rids)}
        starts = []
        for sec in sections:
            idx = rid_to_idx.get(sec.first_slide_id)
            if idx is not None:
                starts.append((idx, sec.name))
        if not starts:
            return
        starts.sort(key=lambda x: x[0])
        # Assign section to each slide range
        for i, (start_idx, name) in enumerate(starts):
            end_idx = starts[i + 1][0] if i + 1 < len(starts) else len(slides)
            for j in range(start_idx, end_idx):
                if j < len(slides):
                    slides[j]._meta["section"] = name
                
    @staticmethod
    def _load_xml(zf: zipfile.ZipFile, path: str, optional: bool = False) -> Optional[ET.Element]:
        try:
            with zf.open(path) as f:
                return ET.parse(f).getroot()
        except KeyError:
            if optional:
                return None
            raise

    def _parse_document_metadata(self, zf: ZipFile):
        # Try core.xml
        core_xml = self._load_xml(zf, "docProps/core.xml", optional=True)
        app_xml = self._load_xml(zf, "docProps/app.xml", optional=True)
        meta = {}
        if core_xml is not None:
            # ... extract title, creator, etc. using Dublin Core elements
            pass  # detailed implementation omitted for brevity; store in PSDMDocument.metadata
        if app_xml is not None:
            pass
        return meta

# ── Helper functions ─────────────────────────────────────────────
def _rels_path_for(part_path: str) -> str:
    dir_name, file_name = part_path.rsplit("/", 1)
    return f"{dir_name}/_rels/{file_name}.rels"

def _dir_of(path: str) -> str:
    return path.rsplit("/", 1)[0] if "/" in path else ""

def path_to_name(path: str) -> str:
    """Extract a readable name from a ZIP path like 'slideLayouts/slideLayout1.xml'."""
    base = path.rsplit("/", 1)[-1]
    name = base.rsplit(".", 1)[0]
    return name.replace("slideLayout", "Layout").replace("slideMaster", "Master")