"""
PDF page layout builder
"""
import math
from dataclasses import dataclass
from typing import Any

from ....models.usdm_models import USDMDocument
from .pdf_objects import PDFPage
from .utils import UnitConverter


@dataclass
class PageLayout:
    """Page layout"""
    page_number: int
    width: float
    height: float
    margin_top: float = 72  # 1 inch
    margin_bottom: float = 72
    margin_left: float = 72
    margin_right: float = 72
    header_height: float = 36
    footer_height: float = 36
    columns: int = 1
    column_gap: float = 12

    @property
    def content_width(self) -> float:
        """Content area width"""
        return self.width - self.margin_left - self.margin_right

    @property
    def content_height(self) -> float:
        """Content area height"""
        return self.height - self.margin_top - self.margin_bottom - self.header_height - self.footer_height

    @property
    def column_width(self) -> float:
        """Column width"""
        if self.columns <= 1:
            return self.content_width
        return (self.content_width - (self.columns - 1) * self.column_gap) / self.columns


class LayoutBuilder:
    """PDF page layout builder"""

    def __init__(self, unit_converter: UnitConverter):
        self.unit_converter = unit_converter
        self.page_layouts: dict[int, PageLayout] = {}

    def create_page_layouts(self, document: USDMDocument,
                           options: dict[str, Any]) -> list[PageLayout]:
        """Create page layouts from USDM document"""
        layouts: list[PageLayout] = []

        # Use existing pages if present
        if document.pages:
            for usdm_page in document.pages:
                layout = PageLayout(
                    page_number=usdm_page.page_number or len(layouts) + 1,
                    width=self.unit_converter.to_points(usdm_page.width or 210),  # mm to points
                    height=self.unit_converter.to_points(usdm_page.height or 297),
                    margin_top=options.get('margin_top', 72),
                    margin_bottom=options.get('margin_bottom', 72),
                    margin_left=options.get('margin_left', 72),
                    margin_right=options.get('margin_right', 72)
                )
                layouts.append(layout)
                self.page_layouts[layout.page_number] = layout
        else:
            # Create new pages based on content
            page_size = options.get('page_size', 'A4')
            orientation = options.get('page_orientation', 'portrait')

            width, height = self._get_page_size(page_size, orientation)

            # Estimate required page count
            content_volume = self._estimate_content_volume(document)
            page_count = max(1, math.ceil(content_volume / (width * height * 0.7)))

            for i in range(page_count):
                layout = PageLayout(
                    page_number=i + 1,
                    width=width,
                    height=height,
                    margin_top=options.get('margin_top', 72),
                    margin_bottom=options.get('margin_bottom', 72),
                    margin_left=options.get('margin_left', 72),
                    margin_right=options.get('margin_right', 72)
                )
                layouts.append(layout)
                self.page_layouts[layout.page_number] = layout

        return layouts

    def _get_page_size(self, page_size: str, orientation: str) -> tuple[float, float]:
        """Get page size by name"""
        # Points per inch (72 points = 1 inch)
        sizes = {
            'A4': (595, 842),      # 210mm x 297mm
            'letter': (612, 792),   # 8.5in x 11in
            'legal': (612, 1008),   # 8.5in x 14in
            'A3': (842, 1190),      # 297mm x 420mm
            'A5': (420, 595),       # 148mm x 210mm
            'B4': (729, 1032),      # 250mm x 353mm
            'B5': (516, 729)        # 176mm x 250mm
        }

        width, height = sizes.get(page_size, sizes['A4'])

        if orientation == 'landscape':
            return (height, width)
        return (width, height)

    def _estimate_content_volume(self, document: USDMDocument) -> float:
        """Estimate document content volume"""
        volume = 0

        # Estimate from logical elements
        for element in document.logical_elements:
            if hasattr(element, 'text'):
                volume += len(element.text or '') * 10  # Approximately 10 points per character
            elif hasattr(element, 'rows'):
                # For tables
                rows = getattr(element, 'rows', [])
                for row in rows:
                    for cell in row:
                        volume += len(str(cell)) * 8

        # Estimate from pages
        for page in document.pages:
            for elmnt in page.elements:
                if hasattr(elmnt, 'text'):
                    volume += len(getattr(elmnt, 'text', '')) * 10
                elif hasattr(elmnt, 'image_data'):
                    volume += 1000  # Approximation for images

        return volume

    def create_pdf_pages(self, pdf_factory, layouts: list[PageLayout]) -> list[PDFPage]:
        """Create PDF Page objects"""
        pdf_pages = []

        for layout in layouts:
            pdf_page = pdf_factory.create_page(
                media_box=[0, 0, layout.width, layout.height]
            )

            # Configure page resources
            pdf_page.resources = {
                'ProcSet': ['/PDF', '/Text', '/ImageB', '/ImageC', '/ImageI'],
                'Font': pdf_factory.create_dictionary({}),  # Will be filled later
                'XObject': pdf_factory.create_dictionary({})  # For images
            }

            pdf_pages.append(pdf_page)

        return pdf_pages

    def calculate_text_position(self, text_run, page_layout: PageLayout,
                               current_y: float) -> tuple[float, float, float]:
        """Calculate text position on page"""
        bbox = getattr(text_run, 'bbox', {})

        # If position already exists
        if bbox and 'x' in bbox and 'y' in bbox:
            x = bbox['x']
            y = page_layout.height - bbox['y']  # Convert to PDF coordinate system
            width = bbox.get('width', 0)
            return x, y, width

        # Calculate automatic position
        x = page_layout.margin_left
        y = current_y

        # Calculate text width
        font_size = 12
        if hasattr(text_run, 'style_id'):
            # In practice, FontManager should be used
            pass

        avg_char_width = font_size * 0.6
        width = len(text_run.text) * avg_char_width

        # If text exceeds page width, wrap to next line
        if x + width > page_layout.width - page_layout.margin_right:
            x = page_layout.margin_left
            y -= font_size * 1.5  # Move to next line

        return x, y, width

    def calculate_image_position(self, image_object, page_layout: PageLayout,
                                current_y: float) -> tuple[float, float, float, float]:
        """Calculate image position on page"""
        bbox = getattr(image_object, 'bbox', {})

        if bbox and all(k in bbox for k in ['x', 'y', 'width', 'height']):
            x = bbox['x']
            y = page_layout.height - bbox['y'] - bbox['height']
            width = bbox['width']
            height = bbox['height']
            return x, y, width, height

        # Default position
        x = page_layout.margin_left
        width = image_object.width or 100
        height = image_object.height or 100

        # If image exceeds page width, center it
        if width > page_layout.content_width:
            width = page_layout.content_width
            height = (image_object.height or 100) * (width / (image_object.width or 100))
            x = page_layout.margin_left

        y = current_y - height

        return x, y, width, height

    def get_page_layout(self, page_number: int) -> PageLayout | None:
        """Get page layout"""
        return self.page_layouts.get(page_number)
