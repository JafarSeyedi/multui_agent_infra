"""
PDF Structure Analysis module
"""
import logging
import re
from collections import Counter
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any

import fitz  # type: ignore[import-untyped]  # PyMuPDF

logger = logging.getLogger(__name__)


class StructuralElementType(Enum):
    """Types of structural elements"""
    TITLE = "title"
    HEADING = "heading"
    SUBHEADING = "subheading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    FIGURE = "figure"
    CAPTION = "caption"
    FOOTNOTE = "footnote"
    HEADER = "header"
    FOOTER = "footer"
    PAGE_NUMBER = "page_number"
    SECTION = "section"
    CHAPTER = "chapter"


@dataclass
class StructuralElement:
    """Structural element"""
    id: str
    element_type: StructuralElementType
    text: str
    page_number: int
    bbox: tuple[float, float, float, float]
    level: int = 1
    parent_id: str | None = None
    children_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class DocumentStructure:
    """Document structure"""
    elements: list[StructuralElement] = field(default_factory=list)
    hierarchy: dict[str, list[str]] = field(default_factory=dict)  # parent -> children
    element_map: dict[str, StructuralElement] = field(default_factory=dict)
    toc: list[dict[str, Any]] = field(default_factory=list)  # Table of contents
    sections: list[dict[str, Any]] = field(default_factory=list)


class StructureParser:
    """PDF structure analyzer"""

    def __init__(self, options: dict[str, Any] | None = None):
        self.options = options or {}
        self.heading_patterns = self.options.get('heading_patterns', [
            r'^(?:chapter|فصل)\s+[IVXLCDM0-9]+',  # Chapter X
            r'^[0-9]+\.\s+[A-Z]',  # 1. Title
            r'^[0-9]+\.[0-9]+\s+',  # 1.1 Title
            r'^[A-Z][A-Za-z\s]+$',  # ALL CAPS TITLE
            r'^[\u0600-\u06FF\s]+\:$',  # Persian text ending with colon
        ])
        self.title_threshold = self.options.get('title_threshold', 0.8)
        self.min_heading_font_size = self.options.get('min_heading_font_size', 14)

    def parse_structure(self, pdf_doc: fitz.Document,
                       layout_analysis: dict[int, Any]) -> DocumentStructure:
        """
        Analyze PDF structure
        
        Args:
            pdf_doc: PDF document
            layout_analysis: page layout analysis
            
        Returns:
            DocumentStructure: document structure
        """
        structure = DocumentStructure()

        # Extract TOC from PDF
        structure.toc = self._extract_toc(pdf_doc)

        # Analyze structure of each page
        for page_num in range(pdf_doc.page_count):
            page = pdf_doc[page_num]
            page_layout = layout_analysis.get(page_num)

            if page_layout:
                page_elements = self._analyze_page_structure(page, page_num, page_layout)
                structure.elements.extend(page_elements)

        # Build hierarchy
        structure = self._build_hierarchy(structure)

        # Identify sections
        structure.sections = self._identify_sections(structure)

        # Create element map
        for element in structure.elements:
            structure.element_map[element.id] = element

        return structure

    def _extract_toc(self, pdf_doc: fitz.Document) -> list[dict[str, Any]]:
        """Extract table of contents"""
        toc = []

        try:
            pdf_toc = pdf_doc.get_toc()
            for item in pdf_toc:
                level, title, page = item
                toc.append({
                    "level": level,
                    "title": title,
                    "page": page,
                    "type": "toc_entry"
                })
        except Exception:
            logger.warning("Could not extract TOC from PDF")

        return toc

    def _analyze_page_structure(self, page: fitz.Page, page_num: int,
                               page_layout: Any) -> list[StructuralElement]:
        """Analyze structure of a page"""
        elements = []

        # Extract text blocks
        text_blocks = page.get_text("dict")["blocks"]

        for block_idx, block in enumerate(text_blocks):
            if block["type"] == 0:  # Text
                block_text = self._extract_block_text(block)
                if not block_text.strip():
                    continue

                # Analyze block features
                font_sizes = self._extract_font_sizes(block)
                avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12

                # Classify element type
                element_type, confidence = self._classify_element(
                    block_text, avg_font_size, block, page_num
                )

                # Create structural element
                element = StructuralElement(
                    id=f"elem_{page_num}_{block_idx}",
                    element_type=element_type,
                    text=block_text,
                    page_number=page_num + 1,
                    bbox=tuple(block["bbox"]),
                    level=self._determine_level(element_type, avg_font_size),
                    metadata={
                        "font_sizes": font_sizes,
                        "line_count": len(block.get("lines", [])),
                        "word_count": len(block_text.split()),
                        "confidence": confidence
                    },
                    confidence=confidence
                )

                elements.append(element)

        # Detect page number
        page_number_element = self._detect_page_number(page, page_num, page_layout)
        if page_number_element:
            elements.append(page_number_element)

        # Detect header and footer
        header_footer_elements = self._detect_header_footer(page, page_num, page_layout)
        elements.extend(header_footer_elements)

        return elements

    def _extract_block_text(self, block: dict) -> str:
        """Extract text from block"""
        text_parts = []

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if text:
                    text_parts.append(text)

        return " ".join(text_parts)

    def _extract_font_sizes(self, block: dict) -> list[float]:
        """Extract block font sizes"""
        font_sizes = []

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                font_size = span.get("size", 0)
                if font_size > 0:
                    font_sizes.append(font_size)

        return font_sizes

    def _classify_element(self, text: str, font_size: float,
                         block: dict, page_num: int) -> tuple[StructuralElementType, float]:
        """Classify element"""
        text_lower = text.lower()
        words = text.split()
        word_count = len(words)

        # Detect main title
        if page_num == 0 and font_size >= 20 and word_count <= 10:
            return StructuralElementType.TITLE, 0.9

        # Detect heading
        if font_size >= self.min_heading_font_size:
            # Check heading patterns
            for pattern in self.heading_patterns:
                if re.match(pattern, text, re.IGNORECASE):
                    return StructuralElementType.HEADING, 0.85

            # Detect based on text length and font
            if word_count <= 15 and font_size >= 16:
                return StructuralElementType.HEADING, 0.7

        # Detect subheading
        if font_size >= 14 and font_size < 16 and word_count <= 20:
            return StructuralElementType.SUBHEADING, 0.6

        # Detect list
        if text.strip().startswith(('•', '-', '*', '◦', '‣', '▪')) or \
           re.match(r'^[0-9]+[\.\)]', text.strip()):
            return StructuralElementType.LIST_ITEM, 0.8

        # Detect caption
        if text_lower.startswith(('figure', 'fig', 'table', 'شکل', 'جدول')):
            return StructuralElementType.CAPTION, 0.75

        # Detect footnote
        if re.match(r'^\[[0-9]+\]', text.strip()) or \
           re.match(r'^\([0-9]+\)', text.strip()):
            return StructuralElementType.FOOTNOTE, 0.8

        # Default: paragraph
        return StructuralElementType.PARAGRAPH, 0.5

    def _determine_level(self, element_type: StructuralElementType, font_size: float) -> int:
        """Determine element level"""
        if element_type == StructuralElementType.TITLE:
            return 1
        elif element_type == StructuralElementType.HEADING:
            if font_size >= 20:
                return 2
            elif font_size >= 16:
                return 3
            else:
                return 4
        elif element_type == StructuralElementType.SUBHEADING:
            return 5
        elif element_type == StructuralElementType.PARAGRAPH:
            return 6
        else:
            return 7

    def _detect_page_number(self, page: fitz.Page, page_num: int,
                           page_layout: Any) -> StructuralElement | None:
        """Detect page number"""
        page_height = page.rect.height

        # Search in bottom of page
        footer_region = (0, page_height * 0.9, page.rect.width, page_height)

        text_blocks = page.get_text("dict")["blocks"]
        for block in text_blocks:
            if block["type"] == 0:
                bbox = block["bbox"]
                # Check if block is in footer region
                if (bbox[1] >= footer_region[1] and bbox[3] <= footer_region[3] and
                    bbox[0] >= footer_region[0] and bbox[2] <= footer_region[2]):

                    block_text = self._extract_block_text(block)
                    # Check if text is only numbers
                    if re.match(r'^[0-9]+$', block_text.strip()):
                        return StructuralElement(
                            id=f"page_num_{page_num}",
                            element_type=StructuralElementType.PAGE_NUMBER,
                            text=block_text,
                            page_number=page_num + 1,
                            bbox=tuple(bbox),
                            level=99,
                            metadata={"detection_method": "footer_region"}
                        )

        return None

    def _detect_header_footer(self, page: fitz.Page, page_num: int,
                            page_layout: Any) -> list[StructuralElement]:
        """Detect header and footer"""
        elements = []
        page_height = page.rect.height

        # Header and footer regions
        header_region = (0, 0, page.rect.width, page_height * 0.1)
        footer_region = (0, page_height * 0.9, page.rect.width, page_height)

        text_blocks = page.get_text("dict")["blocks"]

        for block_idx, block in enumerate(text_blocks):
            if block["type"] == 0:
                bbox = block["bbox"]
                block_text = self._extract_block_text(block)

                if not block_text.strip():
                    continue

                # Check header
                if (bbox[1] >= header_region[1] and bbox[3] <= header_region[3]):
                    element = StructuralElement(
                        id=f"header_{page_num}_{block_idx}",
                        element_type=StructuralElementType.HEADER,
                        text=block_text,
                        page_number=page_num + 1,
                        bbox=tuple(bbox),
                        level=98,
                        metadata={"region": "header"}
                    )
                    elements.append(element)

                # Check footer
                elif (bbox[1] >= footer_region[1] and bbox[3] <= footer_region[3]):
                    element = StructuralElement(
                        id=f"footer_{page_num}_{block_idx}",
                        element_type=StructuralElementType.FOOTER,
                        text=block_text,
                        page_number=page_num + 1,
                        bbox=tuple(bbox),
                        level=98,
                        metadata={"region": "footer"}
                    )
                    elements.append(element)

        return elements

    def _build_hierarchy(self, structure: DocumentStructure) -> DocumentStructure:
        """Build element hierarchy"""
        # Sort elements by position
        sorted_elements = sorted(structure.elements,
                               key=lambda x: (x.page_number, x.bbox[1], x.bbox[0]))

        # Build hierarchy
        hierarchy = defaultdict(list)
        parent_stack: list[StructuralElement] = []

        for element in sorted_elements:
            # Remove parents with higher or equal level
            while parent_stack and parent_stack[-1].level >= element.level:
                parent_stack.pop()

            # Set parent
            if parent_stack:
                element.parent_id = parent_stack[-1].id
                hierarchy[parent_stack[-1].id].append(element.id)

            # Add to stack if element is structural
            if element.element_type in [
                StructuralElementType.TITLE,
                StructuralElementType.HEADING,
                StructuralElementType.SUBHEADING,
                StructuralElementType.SECTION,
                StructuralElementType.CHAPTER
            ]:
                parent_stack.append(element)

        structure.hierarchy = dict(hierarchy)
        return structure

    def _identify_sections(self, structure: DocumentStructure) -> list[dict[str, Any]]:
        """Identify document sections"""
        sections: list[dict[str, Any]] = []
        current_section: dict[str, Any] | None = None

        for element in sorted(structure.elements,
                            key=lambda x: (x.page_number, x.bbox[1])):

            if element.element_type in [
                StructuralElementType.TITLE,
                StructuralElementType.HEADING,
                StructuralElementType.CHAPTER
            ]:
                # Close previous section
                if current_section:
                    sections.append(current_section)

                # Start new section
                current_section = {
                    "id": element.id,
                    "title": element.text,
                    "type": element.element_type.value,
                    "level": element.level,
                    "page_start": element.page_number,
                    "page_end": element.page_number,
                    "elements": [element.id],
                    "children": []
                }
            elif current_section:
                # Add element to current section
                current_section["elements"].append(element.id)
                current_section["page_end"] = max(current_section["page_end"], element.page_number)

        # Add last section
        if current_section:
            sections.append(current_section)

        return sections

    def export_to_json(self, structure: DocumentStructure) -> dict[str, Any]:
        """Export structure to JSON"""
        return {
            "toc": structure.toc,
            "sections": structure.sections,
            "elements": [
                {
                    "id": elem.id,
                    "type": elem.element_type.value,
                    "text": elem.text[:200] + "..." if len(elem.text) > 200 else elem.text,
                    "page": elem.page_number,
                    "level": elem.level,
                    "parent_id": elem.parent_id,
                    "children_ids": elem.children_ids,
                    "bbox": {
                        "x0": elem.bbox[0],
                        "y0": elem.bbox[1],
                        "x1": elem.bbox[2],
                        "y1": elem.bbox[3]
                    },
                    "confidence": elem.confidence,
                    "metadata": elem.metadata
                }
                for elem in structure.elements
            ],
            "hierarchy": structure.hierarchy,
            "statistics": {
                "total_elements": len(structure.elements),
                "by_type": Counter([e.element_type.value for e in structure.elements]),
                "by_page": Counter([e.page_number for e in structure.elements])
            }
        }

    def visualize_hierarchy(self, structure: DocumentStructure, output_path: str | None = None):
        """Visualize hierarchy"""
        try:
            import matplotlib.pyplot as plt  # type: ignore[import-not-found]
            import networkx as nx  # type: ignore[import-untyped]

            G = nx.DiGraph() # type: ignore[var-annotated]

            # Add nodes
            for element in structure.elements:
                G.add_node(
                    element.id,
                    label=f"{element.element_type.value[:3]}: {element.text[:30]}...",
                    type=element.element_type.value,
                    level=element.level
                )

            # Add edges
            for parent_id, children_ids in structure.hierarchy.items():
                for child_id in children_ids:
                    G.add_edge(parent_id, child_id)

            # Draw graph
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(G, seed=42)

            # Color by type
            node_colors = []
            for node in G.nodes():
                node_type = G.nodes[node]['type']
                if node_type == "title":
                    node_colors.append('red')
                elif node_type == "heading":
                    node_colors.append('orange')
                elif node_type == "subheading":
                    node_colors.append('yellow')
                elif node_type == "paragraph":
                    node_colors.append('green')
                else:
                    node_colors.append('blue')

            nx.draw(
                G, pos,
                with_labels=True,
                labels=nx.get_node_attributes(G, 'label'),
                node_color=node_colors,
                node_size=500,
                font_size=8,
                font_weight='bold',
                edge_color='gray',
                width=1,
                alpha=0.8
            )

            plt.title("Document Structure Hierarchy")

            if output_path:
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close()
            else:
                plt.show()

        except ImportError:
            logger.warning("NetworkX or Matplotlib not installed. Visualization skipped.")
