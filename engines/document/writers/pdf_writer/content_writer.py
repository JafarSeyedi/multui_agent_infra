"""
نویسنده محتوای PDF - تبدیل عناصر USDM به دستورات PDF
"""
import base64
import io
from dataclasses import dataclass

from ...models.usdm_models import ImageObject
from ...models.usdm_models import StyleSheet
from ...models.usdm_models import TableContent
from ...models.usdm_models import TextRun
from ...models.usdm_models import VectorPath
from .pdf_objects import PDFDictionary
from .pdf_objects import PDFStream
from .utils import ColorConverter
from .utils import UnitConverter


@dataclass
class TextState:
    """وضعیت متن For PDF"""
    font_name: str = "/F1"
    font_size: float = 12.0
    color: tuple[float, float, float] = (0.0, 0.0, 0.0)  # RGB
    leading: float = 14.0  # فاصله خطوط


class ContentWriter:
    """کلاس اصلی برای نوشتن محتوای PDF"""

    def __init__(self, font_manager, unit_converter: UnitConverter):
        self.font_manager = font_manager
        self.unit_converter = unit_converter
        self.color_converter = ColorConverter()
        self.current_state = TextState()
        self._next_obj_id = 1

    def create_text_stream(self, text_runs: list[TextRun],
                          stylesheet: StyleSheet,
                          page_width: float,
                          page_height: float) -> PDFStream:
        """ایجاد استریم متن برای صفحه"""
        stream_data = io.BytesIO()

        # ذخیره وضعیت گرافیکی
        stream_data.write(b"q\n")

        # تنظیم فضای رنگ
        stream_data.write(b"0 0 0 rg\n")  # رنگ پیش‌فرض مشکی

        # نوشتن هر TextRun
        for text_run in text_runs:
            self._write_text_run(stream_data, text_run, stylesheet, page_height)

        # بازیابی وضعیت
        stream_data.write(b"Q\n")

        obj_id = self._next_obj_id
        self._next_obj_id += 1
        return PDFStream(obj_id=obj_id, data=stream_data.getvalue())

    def _write_text_run(self, stream: io.BytesIO, text_run: TextRun,
                       stylesheet: StyleSheet, page_height: float):
        """نوشتن یک TextRun"""
        if not text_run.text:
            return

        # دریافت استایل
        style = None
        if text_run.style_id and text_run.style_id in stylesheet.character_styles:
            style = stylesheet.character_styles[text_run.style_id]

        # تنظیم فونت
        font_name = "/F1"  # فونت پیش‌فرض
        font_size = 12.0

        if style:
            font_name = self.font_manager.get_pdf_font_name(style.font_family)
            font_size = style.size or 12.0

            # تنظیم حالت bold/italic
            if style.bold and style.italic:
                font_name += ",BoldItalic"
            elif style.bold:
                font_name += ",Bold"
            elif style.italic:
                font_name += ",Italic"

        # تنظیم فونت و سایز
        stream.write(f"BT\n/{font_name[1:]} {font_size} Tf\n".encode())

        # تنظیم موقعیت (تبدیل Y از بالا به پایین)
        bbox = text_run.bbox or {"x": 0, "y": 0, "width": 0, "height": 0}
        x = bbox.get("x", 0)
        y = page_height - bbox.get("y", 0) - bbox.get("height", 0)

        stream.write(f"1 0 0 1 {x:.2f} {y:.2f} Tm\n".encode())

        # تنظیم رنگ
        if style and style.color:
            rgb = self.color_converter.hex_to_rgb(style.color)
            stream.write(f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} rg\n".encode())

        # نوشتن متن با پشتیبانی از فارسی
        text = self._encode_pdf_text(text_run.text, text_run.language)
        stream.write(f"({text}) Tj\n".encode())

        stream.write(b"ET\n")

    def _encode_pdf_text(self, text: str, language: str | None = "en") -> str:
        """کدگذاری متن For PDF با پشتیبانی از فارسی"""
        if not text:
            return ""

        # جایگزینی کاراکترهای خاص
        replacements = {
            '(': r'\(',
            ')': r'\)',
            '\\': r'\\',
            '\n': r'\n',
            '\r': r'\r',
            '\t': r'\t',
            '\b': r'\b',
            '\f': r'\f'
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # اگر متن فارسی است، نیاز به پردازش بیشتر دارد
        if language == "fa":
            # معکوس کردن متن برای نمایش صحیح راست به چپ
            # در واقعیت نیاز به استفاده از فونت‌های UTF-16 داریم
            pass

        return text

    def create_image_stream(self, image_object: ImageObject) -> PDFStream | None:
        """ایجاد استریم تصویر"""
        # if not image_object.src:
        #     return None

        try:
            # استخراج داده تصویر
            image_bytes = None

            if image_object.src.startswith('data:'):
                # استخراج از data URL
                import re
                match = re.match(r'data:image/(\w+);base64,(.+)', image_object.src)
                if match:
                    _, base64_data = match.groups()
                    image_bytes = base64.b64decode(base64_data)
            else:
                # فرض می‌کنیم base64 خالص است
                image_bytes = base64.b64decode(image_object.src)

            if not image_bytes:
                return None

            # ایجاد استریم تصویر
            stream_data = io.BytesIO()

            # دستورات PDF برای نمایش تصویر
            width = image_object.width or 100
            height = image_object.height or 100
            x = image_object.bbox.get("x", 0) if image_object.bbox else 0
            y = image_object.bbox.get("y", 0) if image_object.bbox else 0

            stream_data.write(b"q\n")
            stream_data.write(f"{width} 0 0 {height} {x} {y} cm\n".encode())
            stream_data.write(b"/Im1 Do\n")
            stream_data.write(b"Q\n")

            obj_id = self._next_obj_id
            self._next_obj_id += 1
            image_stream = PDFStream(
                obj_id=obj_id,
                data=image_bytes,
                filters=["DCTDecode"] if image_object.format.lower() in ['jpg', 'jpeg'] else ["FlateDecode"]
            )
            obj_id = self._next_obj_id
            self._next_obj_id += 1
            # ایجاد دیکشنری تصویر
            _image_dict = PDFDictionary(obj_id=obj_id, entries={
                'Type': '/XObject',
                'Subtype': '/Image',
                'Width': width,
                'Height': height,
                'ColorSpace': '/DeviceRGB',
                'BitsPerComponent': 8,
                'Filter': '/DCTDecode' if image_object.format.lower() in ['jpg', 'jpeg'] else '/FlateDecode',
                'Length': len(image_bytes)
            })

            return image_stream

        except Exception as e:
            print(f"خطا در ایجاد تصویر PDF: {e}")
            return None

    def create_vector_stream(self, vector_path: VectorPath, page_height: float) -> PDFStream | None:
        """ایجاد استریم مسیر برداری"""
        if not vector_path.points:
            return None

        stream_data = io.BytesIO()

        # شروع مسیر
        stream_data.write(b"q\n")

        # تنظیم رنگ و ضخامت خط
        if vector_path.stroke_color:
            rgb = self.color_converter.hex_to_rgb(vector_path.stroke_color)
            stream_data.write(f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} RG\n".encode())

        if vector_path.stroke_width:
            stream_data.write(f"{vector_path.stroke_width} w\n".encode())

        # تنظیم رنگ پر کردن
        if vector_path.fill_color:
            rgb = self.color_converter.hex_to_rgb(vector_path.fill_color)
            stream_data.write(f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} rg\n".encode())

        # رسم مسیر
        points = vector_path.points
        if points:
            # حرکت به نقطه اول
            x, y = points[0]["x"], page_height - points[0]["y"]
            stream_data.write(f"{x} {y} m\n".encode())

            # رسم خطوط به نقاط بعدی
            for point in points[1:]:
                x, y = point["x"], page_height - point["y"]
                stream_data.write(f"{x} {y} l\n".encode())

            # بستن مسیر
            if vector_path.fill_color:
                stream_data.write(b"b\n")  # بستن و پر کردن
            else:
                stream_data.write(b"S\n")  # فقط stroke

        stream_data.write(b"Q\n")

        obj_id = self._next_obj_id
        self._next_obj_id += 1
        return PDFStream(obj_id=obj_id, data=stream_data.getvalue())

    def create_table_stream(self, table_content: TableContent,
                           stylesheet: StyleSheet,
                           page_width: float,
                           page_height: float) -> PDFStream:
        """ایجاد استریم جدول"""
        stream_data = io.BytesIO()

        if not table_content.rows:
            obj_id = self._next_obj_id
            self._next_obj_id += 1
            return PDFStream(obj_id=obj_id,data=stream_data.getvalue())

        # محاسبات اولیه جدول
        rows = table_content.rows
        col_count = max(len(row.cells) for row in rows) if rows else 0

        # ابعاد سلول‌ها
        cell_width = (page_width - 100) / col_count if col_count > 0 else 100
        cell_height = 20

        # شروع موقعیت
        start_x = 50
        start_y = page_height - 100

        stream_data.write(b"q\n")

        # رسم جدول
        for row_idx, row in enumerate(rows):
            y = start_y - (row_idx * cell_height)

            for col_idx, cell in enumerate(row.cells):
                x = start_x + (col_idx * cell_width)

                # رسم border سلول
                stream_data.write(b"0 0 0 RG\n")  # رنگ border مشکی
                stream_data.write(b"1 w\n")  # ضخامت border

                # مستطیل سلول
                stream_data.write(f"{x} {y - cell_height} {cell_width} {cell_height} re\n".encode())
                stream_data.write(b"S\n")  # stroke

                # نوشتن متن سلول
                if cell:
                    # تنظیم فونت
                    stream_data.write(b"BT\n")
                    stream_data.write(b"/F1 10 Tf\n")  # فونت پیش‌فرض

                    # موقعیت متن (وسط سلول)
                    text_x = x + 5
                    text_y = y - cell_height + 5

                    stream_data.write(f"1 0 0 1 {text_x} {text_y} Tm\n".encode())
                    stream_data.write(b"0 0 0 rg\n")  # رنگ متن مشکی

                # نوشتن متن
                    text = self._encode_pdf_text(str(cell))
                    stream_data.write(f"({text}) Tj\n".encode())

                    stream_data.write(b"ET\n")

        stream_data.write(b"Q\n")

        obj_id = self._next_obj_id
        self._next_obj_id += 1
        return PDFStream(obj_id=obj_id,data=stream_data.getvalue())
