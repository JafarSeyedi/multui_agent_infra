"""
Utility tools for PDF Writer
"""
import base64
import io
import re
from dataclasses import dataclass
from typing import Any

from PIL import Image


class ColorConverter:
    """Color converter"""

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
        """Convert hex to RGB (values 0-1)"""
        hex_color = hex_color.lstrip('#')

        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])

        if len(hex_color) != 6:
            return (0.0, 0.0, 0.0)

        try:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return (r, g, b)
        except ValueError:
            return (0.0, 0.0, 0.0)

    @staticmethod
    def rgb_to_hex(r: float, g: float, b: float) -> str:
        """Convert RGB to hex"""
        r_int = max(0, min(255, int(r * 255)))
        g_int = max(0, min(255, int(g * 255)))
        b_int = max(0, min(255, int(b * 255)))
        return f"#{r_int:02x}{g_int:02x}{b_int:02x}"

    @staticmethod
    def cmyk_to_rgb(c: float, m: float, y: float, k: float) -> tuple[float, float, float]:
        """Convert CMYK to RGB"""
        r = (1 - c) * (1 - k)
        g = (1 - m) * (1 - k)
        b = (1 - y) * (1 - k)
        return (r, g, b)

    @staticmethod
    def rgb_to_cmyk(r: float, g: float, b: float) -> tuple[float, float, float, float]:
        """Convert RGB to CMYK"""
        if (r, g, b) == (0, 0, 0):
            return (0, 0, 0, 1)

        c = 1 - r
        m = 1 - g
        y = 1 - b

        k = min(c, m, y)
        c = (c - k) / (1 - k) if (1 - k) != 0 else 0
        m = (m - k) / (1 - k) if (1 - k) != 0 else 0
        y = (y - k) / (1 - k) if (1 - k) != 0 else 0

        return (c, m, y, k)

    @staticmethod
    def parse_color(color_str: str) -> tuple[float, float, float] | None:
        """Parse color string to RGB"""
        if not color_str:
            return None

        color_str = color_str.strip().lower()

        # Hex
        if color_str.startswith('#'):
            return ColorConverter.hex_to_rgb(color_str)

        # rgb()
        rgb_match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_str)
        if rgb_match:
            r, g, b = map(int, rgb_match.groups())
            return (r/255.0, g/255.0, b/255.0)

        # rgba()
        rgba_match = re.match(r'rgba\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)', color_str)
        if rgba_match:
            r_str, g_str, b_str, _alpha_str = rgba_match.groups()
            return (int(r_str)/255.0, int(g_str)/255.0, int(b_str)/255.0)

        # Color name
        named_colors = {
            'black': (0.0, 0.0, 0.0),
            'white': (1.0, 1.0, 1.0),
            'red': (1.0, 0.0, 0.0),
            'green': (0.0, 1.0, 0.0),
            'blue': (0.0, 0.0, 1.0),
            'yellow': (1.0, 1.0, 0.0),
            'cyan': (0.0, 1.0, 1.0),
            'magenta': (1.0, 0.0, 1.0),
            'gray': (0.5, 0.5, 0.5),
            'grey': (0.5, 0.5, 0.5),
            'orange': (1.0, 0.65, 0.0),
            'purple': (0.5, 0.0, 0.5),
            'brown': (0.65, 0.16, 0.16),
            'pink': (1.0, 0.75, 0.8),
            'gold': (1.0, 0.84, 0.0),
            'silver': (0.75, 0.75, 0.75)
        }

        if color_str in named_colors:
            return named_colors[color_str]

        return None


class UnitConverter:
    """Unit converter"""

    # Unit to point conversion
    CONVERSION_FACTORS = {
        'pt': 1.0,          # Point
        'px': 0.75,         # Pixel (approximate)
        'in': 72.0,         # Inch
        'cm': 28.3465,      # Centimeter
        'mm': 2.83465,      # Millimeter
        'pc': 12.0,         # Pica
        'em': 12.0,         # Em (approximate)
        'rem': 12.0,        # Rem (approximate)
        'percent': 0.01     # Percent
    }

    @staticmethod
    def to_points(value: float, unit: str = 'pt') -> float:
        """Convert value to points"""
        factor = UnitConverter.CONVERSION_FACTORS.get(unit.lower(), 1.0)
        return value * factor

    @staticmethod
    def from_points(value: float, unit: str = 'pt') -> float:
        """Convert from points to another unit"""
        factor = UnitConverter.CONVERSION_FACTORS.get(unit.lower(), 1.0)
        if factor == 0:
            return 0.0
        return value / factor

    @staticmethod
    def convert(value: float, from_unit: str, to_unit: str) -> float:
        """Convert between different units"""
        points = UnitConverter.to_points(value, from_unit)
        return UnitConverter.from_points(points, to_unit)

    @staticmethod
    def parse_measurement(measurement: str) -> tuple[float, str]:
        """Parse measurement string"""
        if not measurement:
            return (0.0, 'pt')

        measurement = measurement.strip().lower()

        # Different patterns
        patterns = [
            r'^([\d.]+)\s*(pt|px|in|cm|mm|pc|em|rem|%)$',
            r'^([\d.]+)(pt|px|in|cm|mm|pc|em|rem|%)$'
        ]

        for pattern in patterns:
            match = re.match(pattern, measurement)
            if match:
                value = float(match.group(1))
                unit = match.group(2)
                if unit == '%':
                    unit = 'percent'
                return (value, unit)

        # If no unit specified, assume points
        try:
            value = float(measurement)
            return (value, 'pt')
        except ValueError:
            return (0.0, 'pt')

    @staticmethod
    def normalize_measurement(measurement: str, target_unit: str = 'pt') -> float:
        """Normalize measurement to target unit"""
        value, unit = UnitConverter.parse_measurement(measurement)
        return UnitConverter.convert(value, unit, target_unit)


class ImageProcessor:
    """Image processor"""

    def __init__(self):
        self.supported_formats = ['jpeg', 'jpg', 'png', 'gif', 'bmp', 'tiff', 'webp']

    def process_image(self, image_data: bytes,
                     max_width: int | None = None,
                     max_height: int | None = None,
                     quality: int = 85,
                     format: str = 'jpeg') -> dict[str, Any]:
        """
        Process image

        Args:
            image_data: Image data
            max_width: Maximum width (pixels)
            max_height: Maximum height (pixels)
            quality: Quality (0-100)
            format: Output format

        Returns:
            Dictionary containing processed image information
        """
        try:
            # Open image
            image: Image.Image = Image.open(io.BytesIO(image_data))

            # Save original info
            original_width, original_height = image.size
            original_format = image.format.lower() if image.format else 'unknown'
            image.mode

            # Resize if needed
            if max_width or max_height:
                image = self._resize_image(image, max_width, max_height)

            # Convert to RGB if needed
            if image.mode not in ['RGB', 'RGBA', 'L']:
                if image.mode == 'P' and 'transparency' in image.info:
                    image = image.convert('RGBA')
                else:
                    image = image.convert('RGB')

            # Compression
            output_buffer = io.BytesIO()

            if format.lower() in ['jpeg', 'jpg']:
                if image.mode == 'RGBA':
                    # Create white background for JPEG
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3] if image.mode == 'RGBA' else None)
                    image = background

                image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
                mime_type = 'image/jpeg'

            elif format.lower() == 'png':
                image.save(output_buffer, format='PNG', optimize=True)
                mime_type = 'image/png'

            elif format.lower() == 'webp':
                image.save(output_buffer, format='WEBP', quality=quality)
                mime_type = 'image/webp'

            else:
                # Save with original format
                image.save(output_buffer, format=image.format or 'PNG')
                mime_type = f'image/{original_format}'

            processed_data = output_buffer.getvalue()
            new_width, new_height = image.size

            return {
                'data': processed_data,
                'width': new_width,
                'height': new_height,
                'format': format.lower(),
                'mime_type': mime_type,
                'size_bytes': len(processed_data),
                'original_width': original_width,
                'original_height': original_height,
                'original_format': original_format,
                'compression_ratio': len(processed_data) / len(image_data) if image_data else 1.0
            }

        except Exception as e:
            raise Exception(f"Error in image processing: {e}")

    def _resize_image(self, image: Image.Image,
                     max_width: int | None,
                     max_height: int | None) -> Image.Image:
        """Resize image"""
        original_width, original_height = image.size

        # If no limits
        if not max_width and not max_height:
            return image

        # Calculate new dimensions
        if max_width and max_height:
            # Maintain aspect ratio
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            ratio = min(width_ratio, height_ratio)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)

        elif max_width:
            # Width constraint
            ratio = max_width / original_width
            new_width = max_width
            new_height = int(original_height * ratio)

        else:  # max_height
            # Height constraint
            assert max_height is not None
            ratio = max_height / original_height
            new_width = int(original_width * ratio)
            new_height = max_height

        # Resize
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def extract_image_info(self, image_data: bytes) -> dict[str, Any]:
        """Extract image information"""
        try:
            image: Image.Image = Image.open(io.BytesIO(image_data))

            info = {
                'width': image.width,
                'height': image.height,
                'format': image.format,
                'mode': image.mode,
                'size_bytes': len(image_data),
                'dpi': image.info.get('dpi', (72, 72)),
                'has_alpha': image.mode in ['RGBA', 'LA', 'PA'],
                'is_animated': getattr(image, 'is_animated', False),
                'n_frames': getattr(image, 'n_frames', 1)
            }

            # Additional info for specific formats
            if image.format == 'JPEG':
                info['exif'] = image._getexif() if hasattr(image, '_getexif') else None

            elif image.format == 'PNG':
                info['transparency'] = image.info.get('transparency')
                info['gamma'] = image.info.get('gamma')

            elif image.format == 'TIFF':
                info['tiff_tags'] = image.tag_v2 if hasattr(image, 'tag_v2') else {}

            return info

        except Exception as e:
            raise Exception(f"Error in image info extraction: {e}")

    def convert_to_base64(self, image_data: bytes, mime_type: str | None = None) -> str:
        """Convert image to base64"""
        if not mime_type:
            # Auto-detect MIME type
            try:
                image: Image.Image = Image.open(io.BytesIO(image_data))
                mime_type = f'image/{image.format.lower()}' if image.format else 'image/jpeg'
            except Exception:
                mime_type = 'image/jpeg'

        base64_data = base64.b64encode(image_data).decode('utf-8')
        return f"data:{mime_type};base64,{base64_data}"

    def create_thumbnail(self, image_data: bytes,
                        thumbnail_size: tuple[int, int] = (100, 100),
                        quality: int = 75) -> bytes:
        """Create thumbnail"""
        try:
            image: Image.Image = Image.open(io.BytesIO(image_data))

            # Maintain aspect ratio
            original_width, original_height = image.size
            thumb_width, thumb_height = thumbnail_size

            # Calculate thumbnail dimensions with aspect ratio
            width_ratio = thumb_width / original_width
            height_ratio = thumb_height / original_height
            ratio = min(width_ratio, height_ratio)

            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)

            # Resize
            thumbnail = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Save
            output_buffer = io.BytesIO()
            thumbnail.save(output_buffer, format='JPEG', quality=quality)

            return output_buffer.getvalue()

        except Exception as e:
            raise Exception(f"Error creating thumbnail: {e}")


@dataclass
class PDFColor:
    """PDF color class"""
    r: float  # 0-1
    g: float  # 0-1
    b: float  # 0-1
    c: float = 0.0  # CMYK
    m: float = 0.0
    y: float = 0.0
    k: float = 0.0
    a: float = 1.0  # Alpha

    @classmethod
    def from_hex(cls, hex_color: str, alpha: float = 1.0) -> 'PDFColor':
        """Create from hex"""
        r, g, b = ColorConverter.hex_to_rgb(hex_color)
        return cls(r=r, g=g, b=b, a=alpha)

    @classmethod
    def from_rgb(cls, r: float, g: float, b: float, alpha: float = 1.0) -> 'PDFColor':
        """Create from RGB"""
        return cls(r=r, g=g, b=b, a=alpha)

    @classmethod
    def from_cmyk(cls, c: float, m: float, y: float, k: float, alpha: float = 1.0) -> 'PDFColor':
        """Create from CMYK"""
        r, g, b = ColorConverter.cmyk_to_rgb(c, m, y, k)
        return cls(r=r, g=g, b=b, c=c, m=m, y=y, k=k, a=alpha)

    def to_pdf_rgb(self) -> str:
        """Convert to PDF RGB string"""
        return f"{self.r:.3f} {self.g:.3f} {self.b:.3f} rg"

    def to_pdf_cmyk(self) -> str:
        """Convert to PDF CMYK string"""
        return f"{self.c:.3f} {self.m:.3f} {self.y:.3f} {self.k:.3f} k"

    def to_pdf_gray(self) -> str:
        """Convert to PDF gray string"""
        gray = 0.299 * self.r + 0.587 * self.g + 0.114 * self.b
        return f"{gray:.3f} g"

    def to_hex(self) -> str:
        """Convert to hex"""
        return ColorConverter.rgb_to_hex(self.r, self.g, self.b)
