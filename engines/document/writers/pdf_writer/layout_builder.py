"""
PDF page layout builder
"""
import math
from dataclasses import dataclass
from typing import Any

from ...models.usdm_models import USDMDocument
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
        """عرض منطقه محتوا"""
        return self.width - self.margin_left - self.margin_right

    @property
    def content_height(self) -> float:
        """ارتفاع منطقه محتوا"""
        return self.height - self.margin_top - self.margin_bottom - self.header_height - self.footer_height

    @property
    def column_width(self) -> float:
        """عرض هر ستون"""
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
        """ایجاد طرح‌بندی صفحات بر اساس سند USDM"""
        layouts: list[PageLayout] = []

        # اگر صفحات از قبل وجود دارند، از آنها استفاده کن
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
            # ایجاد صفحات جدید بر اساس محتوا
            page_size = options.get('page_size', 'A4')
            orientation = options.get('page_orientation', 'portrait')

            width, height = self._get_page_size(page_size, orientation)

            # تخمین تعداد صفحات مورد نیاز
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
        """دریافت اندازه صفحه بر اساس نام"""
        # نقاط در اینچ (72 points = 1 inch)
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
        """تخمین حجم محتوای سند"""
        volume = 0

        # تخمین از عناصر منطقی
        for element in document.logical_elements:
            if hasattr(element, 'text'):
                volume += len(element.text or '') * 10  # تقریباً 10 نقطه برای هر کاراکتر
            elif hasattr(element, 'rows'):
                # برای جداول
                rows = getattr(element, 'rows', [])
                for row in rows:
                    for cell in row:
                        volume += len(str(cell)) * 8

        # تخمین از صفحات
        for page in document.pages:
            for elmnt in page.elements:
                if hasattr(elmnt, 'text'):
                    volume += len(getattr(elmnt, 'text', '')) * 10
                elif hasattr(elmnt, 'image_data'):
                    volume += 1000  # تقریب برای تصاویر

        return volume

    def create_pdf_pages(self, pdf_factory, layouts: list[PageLayout]) -> list[PDFPage]:
        """ایجاد اشیاء PDF Page"""
        pdf_pages = []

        for layout in layouts:
            pdf_page = pdf_factory.create_page(
                media_box=[0, 0, layout.width, layout.height]
            )

            # تنظیم منابع صفحه
            pdf_page.resources = {
                'ProcSet': ['/PDF', '/Text', '/ImageB', '/ImageC', '/ImageI'],
                'Font': pdf_factory.create_dictionary({}),  # بعداً پر می‌شود
                'XObject': pdf_factory.create_dictionary({})  # برای تصاویر
            }

            pdf_pages.append(pdf_page)

        return pdf_pages

    def calculate_text_position(self, text_run, page_layout: PageLayout,
                               current_y: float) -> tuple[float, float, float]:
        """محاسبه موقعیت متن در صفحه"""
        bbox = getattr(text_run, 'bbox', {})

        # اگر موقعیت از قبل وجود دارد
        if bbox and 'x' in bbox and 'y' in bbox:
            x = bbox['x']
            y = page_layout.height - bbox['y']  # تبدیل به سیستم مختصات PDF
            width = bbox.get('width', 0)
            return x, y, width

        # محاسبه موقعیت خودکار
        x = page_layout.margin_left
        y = current_y

        # محاسبه عرض متن
        font_size = 12
        if hasattr(text_run, 'style_id'):
            # در واقعیت باید از FontManager استفاده شود
            pass

        avg_char_width = font_size * 0.6
        width = len(text_run.text) * avg_char_width

        # اگر متن از عرض صفحه بیشتر شود، به خط بعد برو
        if x + width > page_layout.width - page_layout.margin_right:
            x = page_layout.margin_left
            y -= font_size * 1.5  # رفتن به خط بعد

        return x, y, width

    def calculate_image_position(self, image_object, page_layout: PageLayout,
                                current_y: float) -> tuple[float, float, float, float]:
        """محاسبه موقعیت تصویر در صفحه"""
        bbox = getattr(image_object, 'bbox', {})

        if bbox and all(k in bbox for k in ['x', 'y', 'width', 'height']):
            x = bbox['x']
            y = page_layout.height - bbox['y'] - bbox['height']
            width = bbox['width']
            height = bbox['height']
            return x, y, width, height

        # موقعیت پیش‌فرض
        x = page_layout.margin_left
        width = image_object.width or 100
        height = image_object.height or 100

        # اگر تصویر از عرض صفحه بیشتر شود، وسط‌چین کن
        if width > page_layout.content_width:
            width = page_layout.content_width
            height = (image_object.height or 100) * (width / (image_object.width or 100))
            x = page_layout.margin_left

        y = current_y - height

        return x, y, width, height

    def get_page_layout(self, page_number: int) -> PageLayout | None:
        """دریافت طرح‌بندی صفحه"""
        return self.page_layouts.get(page_number)
