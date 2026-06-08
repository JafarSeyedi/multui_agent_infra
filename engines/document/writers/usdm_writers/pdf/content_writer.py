"""
PDF content writer - converts USDM elements to PDF commands
"""
import base64
import io
from dataclasses import dataclass

from ....models.usdm_models import ImageObject
from ....models.usdm_models import StyleSheet
from ....models.usdm_models import TableContent
from ....models.usdm_models import TextRun
from ....models.usdm_models import VectorPath
from .pdf_objects import PDFDictionary
from .pdf_objects import PDFStream
from .utils import ColorConverter
from .utils import UnitConverter


@dataclass
class TextState:
    """Text state for PDF"""
    font_name: str = "/F1"
    font_size: float = 12.0
    color: tuple[float, float, float] = (0.0, 0.0, 0.0)  # RGB
    leading: float = 14.0  # Line spacing


class ContentWriter:
    """Main class for writing PDF content"""

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
        """Create text stream for page"""
        stream_data = io.BytesIO()

        # Save graphics state
        stream_data.write(b"q\n")

        # Set color space
        stream_data.write(b"0 0 0 rg\n")  # Default black color

        # Write each TextRun
        for text_run in text_runs:
            self._write_text_run(stream_data, text_run, stylesheet, page_height)

        # Restore state
        stream_data.write(b"Q\n")

        obj_id = self._next_obj_id
        self._next_obj_id += 1
        return PDFStream(obj_id=obj_id, data=stream_data.getvalue())

    def _write_text_run(self, stream: io.BytesIO, text_run: TextRun,
                       stylesheet: StyleSheet, page_height: float):
        """Write a TextRun"""
        if not text_run.text:
            return

        # Get style
        style = None
        if text_run.style_id and text_run.style_id in stylesheet.character_styles:
            style = stylesheet.character_styles[text_run.style_id]

        # Set font
        font_name = "/F1"  # Default font
        font_size = 12.0

        if style:
            font_name = self.font_manager.get_pdf_font_name(style.font_family)
            font_size = style.size or 12.0

            # Set bold/italic state
            if style.bold and style.italic:
                font_name += ",BoldItalic"
            elif style.bold:
                font_name += ",Bold"
            elif style.italic:
                font_name += ",Italic"

        # Set font and size
        stream.write(f"BT\n/{font_name[1:]} {font_size} Tf\n".encode())

        # Set position (convert Y from top to bottom)
        bbox = text_run.bbox or {"x": 0, "y": 0, "width": 0, "height": 0}
        x = bbox.get("x", 0)
        y = page_height - bbox.get("y", 0) - bbox.get("height", 0)

        stream.write(f"1 0 0 1 {x:.2f} {y:.2f} Tm\n".encode())

        # Set color
        if style and style.color:
            rgb = self.color_converter.hex_to_rgb(style.color)
            stream.write(f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} rg\n".encode())

        # Write text with Persian support
        text = self._encode_pdf_text(text_run.text, text_run.language)
        stream.write(f"({text}) Tj\n".encode())

        stream.write(b"ET\n")

    def _encode_pdf_text(self, text: str, language: str | None = "en") -> str:
        """Encode text for PDF with Persian support"""
        if not text:
            return ""

        # Replace special characters
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

        # If text is Persian, further processing is needed
        if language == "fa":
            # Reverse text for correct right-to-left display
            # In reality, UTF-16 fonts are needed
            pass

        return text

    def create_image_stream(self, image_object: ImageObject) -> PDFStream | None:
        """Create image stream"""
        # if not image_object.src:
        #     return None

        try:
            # Extract image data
            image_bytes = None

            if image_object.src.startswith('data:'):
                # Extract from data URL
                import re
                match = re.match(r'data:image/(\w+);base64,(.+)', image_object.src)
                if match:
                    _, base64_data = match.groups()
                    image_bytes = base64.b64decode(base64_data)
            else:
                # Assume it's raw base64
                image_bytes = base64.b64decode(image_object.src)

            if not image_bytes:
                return None

            # Create image stream
            stream_data = io.BytesIO()

            # PDF commands for image display
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
            # Create image dictionary
            PDFDictionary(obj_id=obj_id, entries={
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
            print(f"Error creating PDF image: {e}")
            return None

    def create_vector_stream(self, vector_path: VectorPath, page_height: float) -> PDFStream | None:
        """Create vector path stream"""
        if not vector_path.points:
            return None

        stream_data = io.BytesIO()

        # Start path
        stream_data.write(b"q\n")

        # Set line color and width
        if vector_path.stroke_color:
            rgb = self.color_converter.hex_to_rgb(vector_path.stroke_color)
            stream_data.write(f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} RG\n".encode())

        if vector_path.stroke_width:
            stream_data.write(f"{vector_path.stroke_width} w\n".encode())

        # Set fill color
        if vector_path.fill_color:
            rgb = self.color_converter.hex_to_rgb(vector_path.fill_color)
            stream_data.write(f"{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} rg\n".encode())

        # Draw path
        points = vector_path.points
        if points:
            # Move to first point
            x, y = points[0]["x"], page_height - points[0]["y"]
            stream_data.write(f"{x} {y} m\n".encode())

            # Draw lines to next points
            for point in points[1:]:
                x, y = point["x"], page_height - point["y"]
                stream_data.write(f"{x} {y} l\n".encode())

            # Close path
            if vector_path.fill_color:
                stream_data.write(b"b\n")  # Close and fill
            else:
                stream_data.write(b"S\n")  # Stroke only

        stream_data.write(b"Q\n")

        obj_id = self._next_obj_id
        self._next_obj_id += 1
        return PDFStream(obj_id=obj_id, data=stream_data.getvalue())

    def create_table_stream(self, table_content: TableContent,
                           stylesheet: StyleSheet,
                           page_width: float,
                           page_height: float) -> PDFStream:
        """Create table stream"""
        stream_data = io.BytesIO()

        if not table_content.rows:
            obj_id = self._next_obj_id
            self._next_obj_id += 1
            return PDFStream(obj_id=obj_id,data=stream_data.getvalue())

        # Initial table calculations
        rows = table_content.rows
        col_count = max(len(row.cells) for row in rows) if rows else 0

        # Cell dimensions
        cell_width = (page_width - 100) / col_count if col_count > 0 else 100
        cell_height = 20

        # Starting position
        start_x = 50
        start_y = page_height - 100

        stream_data.write(b"q\n")

        # Draw table
        for row_idx, row in enumerate(rows):
            y = start_y - (row_idx * cell_height)

            for col_idx, cell in enumerate(row.cells):
                x = start_x + (col_idx * cell_width)

                # Draw cell border
                stream_data.write(b"0 0 0 RG\n")  # Black border color
                stream_data.write(b"1 w\n")  # Border thickness

                # Cell rectangle
                stream_data.write(f"{x} {y - cell_height} {cell_width} {cell_height} re\n".encode())
                stream_data.write(b"S\n")  # Stroke

                # Write cell text
                if cell:
                    # Set font
                    stream_data.write(b"BT\n")
                    stream_data.write(b"/F1 10 Tf\n")  # Default font

                    # Text position (center of cell)
                    text_x = x + 5
                    text_y = y - cell_height + 5

                    stream_data.write(f"1 0 0 1 {text_x} {text_y} Tm\n".encode())
                    stream_data.write(b"0 0 0 rg\n")  # Black text color

                # Write text
                    text = self._encode_pdf_text(str(cell))
                    stream_data.write(f"({text}) Tj\n".encode())

                    stream_data.write(b"ET\n")

        stream_data.write(b"Q\n")

        obj_id = self._next_obj_id
        self._next_obj_id += 1
        return PDFStream(obj_id=obj_id,data=stream_data.getvalue())
