"""
ماژول بهینه‌سازی PDF
کاهش حجم فایل و بهبود کارایی
"""
import hashlib
import logging
import re
import zlib
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import cast

from PIL import Image


logger = logging.getLogger(__name__)


class OptimizationLevel(Enum):
    """سطوح بهینه‌سازی"""
    NONE = "none"           # بدون بهینه‌سازی
    FAST = "fast"           # بهینه‌سازی سریع
    BALANCED = "balanced"   # متعادل
    MAXIMUM = "maximum"     # حداکثر بهینه‌سازی


@dataclass
class OptimizationOptions:
    """گزینه‌های بهینه‌سازی"""
    level: OptimizationLevel = OptimizationLevel.BALANCED
    compress_images: bool = True          # فشرده‌سازی تصاویر
    compress_streams: bool = True         # فشرده‌سازی استریم‌ها
    remove_unused: bool = True            # حذف آبجکت‌های استفاده نشده
    merge_fonts: bool = False             # ادغام فونت‌ها
    linearize: bool = False               # خطی‌سازی برای وب
    remove_metadata: bool = False         # حذف متادیتا
    downscale_images: bool = False        # کاهش اندازه تصاویر
    image_quality: int = 85               # کیفیت تصاویر (0-100)
    remove_duplicates: bool = True        # حذف داده‌های تکراری


class PDFOptimizer:
    """بهینه‌ساز PDF"""

    def __init__(self, options: OptimizationOptions | None = None):
        self.options = options or OptimizationOptions()
        self.stats = {
            'original_size': 0,
            'optimized_size': 0,
            'compression_ratio': 1.0,
            'objects_removed': 0,
            'images_optimized': 0,
            'streams_compressed': 0
        }

    def optimize(self, pdf_data: bytes) -> bytes:
        """بهینه‌سازی PDF"""
        self.stats['original_size'] = len(pdf_data)

        if self.options.level == OptimizationLevel.NONE:
            return pdf_data

        # تجزیه PDF به بخش‌های مختلف
        pdf_parts = self._parse_pdf_structure(pdf_data)

        # اعمال بهینه‌سازی‌ها
        optimized_parts = self._apply_optimizations(pdf_parts)

        # مونتاژ مجدد PDF
        optimized_data = self._assemble_pdf(optimized_parts)

        self.stats['optimized_size'] = len(optimized_data)
        if self.stats['original_size'] > 0:
            self.stats['compression_ratio'] = self.stats['optimized_size'] / self.stats['original_size']

        return optimized_data

    def _parse_pdf_structure(self, pdf_data: bytes) -> dict[str, Any]:
        """تجزیه ساختار PDF"""
        # این یک پیاده‌سازی ساده است
        # در عمل نیاز به پارسر کامل PDF دارد

        parts = {
            'header': b'',
            'objects': [],
            'xref': b'',
            'trailer': b'',
            'startxref': b''
        }

        # پیدا کردن header
        header_match = re.search(rb'%PDF-\d\.\d', pdf_data)
        if header_match:
            parts['header'] = pdf_data[:header_match.end()]
            remaining = pdf_data[header_match.end():]
        else:
            parts['header'] = b'%PDF-1.7\n'
            remaining = pdf_data

        # پیدا کردن startxref
        startxref_match = re.search(rb'startxref\s+(\d+)', remaining)
        if startxref_match:
            parts['startxref'] = remaining[startxref_match.start():]
            remaining = remaining[:startxref_match.start()]

        # پیدا کردن trailer
        trailer_match = re.search(rb'trailer\s*<<.*?>>', remaining, re.DOTALL)
        if trailer_match:
            parts['trailer'] = remaining[trailer_match.start():]
            remaining = remaining[:trailer_match.start()]

        # پیدا کردن xref
        xref_match = re.search(rb'xref\s+\d+\s+\d+.*?\n', remaining, re.DOTALL)
        if xref_match:
            parts['xref'] = remaining[xref_match.start():]
            remaining = remaining[:xref_match.start()]

        # استخراج آبجکت‌ها (ساده)
        # در پیاده‌سازی واقعی نیاز به پارسر کامل داریم
        parts['objects_data'] = remaining

        return parts

    def _apply_optimizations(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """اعمال بهینه‌سازی‌ها"""
        optimized_parts = pdf_parts.copy()

        # فشرده‌سازی استریم‌ها
        if self.options.compress_streams:
            optimized_parts = self._compress_streams(optimized_parts)

        # بهینه‌سازی تصاویر
        if self.options.compress_images:
            optimized_parts = self._optimize_images(optimized_parts)

        # حذف آبجکت‌های استفاده نشده
        if self.options.remove_unused:
            optimized_parts = self._remove_unused_objects(optimized_parts)

        # حذف داده‌های تکراری
        if self.options.remove_duplicates:
            optimized_parts = self._remove_duplicates(optimized_parts)

        # حذف متادیتا
        if self.options.remove_metadata:
            optimized_parts = self._remove_metadata(optimized_parts)

        # خطی‌سازی برای وب
        if self.options.linearize:
            optimized_parts = self._linearize_pdf(optimized_parts)

        return optimized_parts

    def _compress_streams(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """فشرده‌سازی استریم‌ها"""
        # پیدا کردن و فشرده‌سازی استریم‌ها
        pattern = rb'stream\s*\n(.*?)\n\s*endstream'
        objects_data = pdf_parts.get('objects_data', b'')

        def compress_stream(match):
            stream_data = match.group(1)
            try:
                # فشرده‌سازی با zlib
                compressed = zlib.compress(stream_data, level=zlib.Z_BEST_COMPRESSION)
                return b'stream\n' + compressed + b'\nendstream'
            except:
                return match.group(0)

        compressed_data = re.sub(pattern, compress_stream, objects_data, flags=re.DOTALL)

        pdf_parts['objects_data'] = compressed_data
        self.stats['streams_compressed'] += 1

        return pdf_parts

    def _optimize_images(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """
        بهینه‌سازی تصاویر در PDF با قابلیت‌های:
        1. کاهش اندازه تصاویر (downscaling)
        2. فشرده‌سازی با الگوریتم‌های بهینه
        3. حذف متادیتای غیرضروری
        4. تبدیل فرمت‌های غیربهینه
        
        Args:
            pdf_parts: دیکشنری حاوی بخش‌های PDF
            
        Returns:
            pdf_parts بهینه‌سازی شده
        """
        try:
            if 'objects' not in pdf_parts:
                logger.warning("PDF بدون آبجکت برای بهینه‌سازی تصاویر")
                return pdf_parts

            objects = pdf_parts['objects']
            optimized_count = 0
            total_size_before = 0
            total_size_after = 0

            # آمار بهینه‌سازی
            self.stats['images_optimized'] = 0
            self.stats['images_downscaled'] = 0
            self.stats['images_converted'] = 0
            self.stats['size_reduction_bytes'] = 0
            self.stats['size_reduction_percent'] = 0.0

            # گزینه‌های بهینه‌سازی
            options = getattr(self, 'optimization_options', {
                'downscale_images': True,
                'max_image_width': 1920,
                'max_image_height': 1080,
                'jpeg_quality': 85,
                'compress_png': True,
                'remove_metadata': True,
                'convert_rgb_to_cmyk': False,
                'dpi_threshold': 300
            })

            # پردازش هر آبجکت
            for i, obj in enumerate(objects):
                if self._is_image_object(obj):
                    original_size = self._get_object_size(obj)
                    total_size_before += original_size

                    # بهینه‌سازی تصویر
                    optimized_obj = self._optimize_single_image(obj, options)

                    if optimized_obj:
                        new_size = self._get_object_size(optimized_obj)
                        size_reduction = original_size - new_size

                        if size_reduction > 0:
                            objects[i] = optimized_obj
                            optimized_count += 1
                            total_size_after += new_size

                            # به‌روزرسانی آمار
                            self.stats['images_optimized'] += 1
                            self.stats['size_reduction_bytes'] += size_reduction

                            logger.debug(f"تصویر بهینه‌سازی شد: {size_reduction} بایت کاهش")

            # محاسبه درصد کاهش
            if total_size_before > 0:
                reduction_percent = ((total_size_before - total_size_after) / total_size_before) * 100
                self.stats['size_reduction_percent'] = round(reduction_percent, 2)

                logger.info(
                    f"بهینه‌سازی تصاویر کامل شد: {optimized_count} تصویر، "
                    f"{self.stats['size_reduction_bytes']:,} بایت کاهش "
                    f"({self.stats['size_reduction_percent']}%)"
                )

            pdf_parts['objects'] = objects
            return pdf_parts

        except Exception as e:
            logger.error(f"خطا در بهینه‌سازی تصاویر: {e}", exc_info=True)
            return pdf_parts


    def _is_image_object(self, obj: dict) -> bool:
        """
        تشخیص آبجکت تصویر در PDF
        
        Args:
            obj: آبجکت PDF
            
        Returns:
            True اگر آبجکت تصویر باشد
        """
        try:
            # بررسی بر اساس subtype
            if obj.get('type') == 'xobject':
                subtype = obj.get('subtype', '')
                return subtype.lower() == '/image'

            # بررسی در metadata
            metadata = obj.get('metadata', {})
            if '/Subtype' in metadata:
                return metadata['/Subtype'] == '/Image'

            # بررسی در value
            value = obj.get('value', '')
            if isinstance(value, str):
                return '/Subtype /Image' in value or '/Filter /DCTDecode' in value

            return False
        except:
            return False


    def _get_object_size(self, obj: dict) -> int:
        """
        محاسبه اندازه آبجکت
        
        Args:
            obj: آبجکت PDF
            
        Returns:
            اندازه بر حسب بایت
        """
        try:
            # اندازه stream
            if 'stream' in obj:
                stream_data = obj['stream']
                if isinstance(stream_data, bytes):
                    return len(stream_data)
                elif isinstance(stream_data, str):
                    return len(stream_data.encode('utf-8'))

            # اندازه value
            if 'value' in obj:
                value = obj['value']
                if isinstance(value, bytes):
                    return len(value)
                elif isinstance(value, str):
                    return len(value.encode('utf-8'))

            # اندازه تقریبی
            return len(str(obj).encode('utf-8'))
        except:
            return 0


    def _optimize_single_image(self, image_obj: dict, options: dict) -> dict | None:
        """
        بهینه‌سازی یک تصویر
        
        Args:
            image_obj: آبجکت تصویر
            options: گزینه‌های بهینه‌سازی
            
        Returns:
            آبجکت بهینه‌سازی شده یا None
        """
        try:
            # استخراج داده‌های تصویر
            image_data, image_info = self._extract_image_data(image_obj)
            if not image_data:
                return None

            # تشخیص فرمت تصویر
            image_format = self._detect_image_format(image_info)

            # پردازش بر اساس فرمت
            processed_data = None

            if image_format == 'JPEG':
                processed_data = self._optimize_jpeg_image(
                    image_data, image_info, options
                )
            elif image_format == 'PNG':
                processed_data = self._optimize_png_image(
                    image_data, image_info, options
                )
            elif image_format == 'TIFF':
                processed_data = self._optimize_tiff_image(
                    image_data, image_info, options
                )
            elif image_format == 'JBIG2':
                processed_data = self._optimize_jbig2_image(
                    image_data, image_info, options
                )
            elif image_format == 'CCITT':
                processed_data = self._optimize_ccitt_image(
                    image_data, image_info, options
                )
            else:
                # فرمت‌های دیگر - فشرده‌سازی عمومی
                processed_data = self._compress_generic_image(
                    image_data, image_info, options
                )

            if processed_data:
                # ایجاد آبجکت بهینه‌سازی شده
                optimized_obj = self._create_optimized_image_object(
                    image_obj, processed_data, image_info, image_format
                )
                return optimized_obj

            return None

        except Exception as e:
            logger.warning(f"خطا در بهینه‌سازی تصویر: {e}")
            return None


    def _extract_image_data(self, image_obj: dict) -> tuple[bytes | None, dict]:
        """
        استخراج داده‌های تصویر از آبجکت PDF
        
        Args:
            image_obj: آبجکت تصویر PDF
            
        Returns:
            (داده‌های تصویر, اطلاعات تصویر)
        """
        try:
            image_info: dict[str, Any] = {}

            # استخراج از stream
            if 'stream' in image_obj:
                stream_data = image_obj['stream']
                if isinstance(stream_data, bytes):
                    image_data = stream_data
                else:
                    image_data = str(stream_data).encode('utf-8')
            # استخراج از value
            elif 'value' in image_obj:
                value = image_obj['value']
                if isinstance(value, bytes):
                    image_data = value
                else:
                    image_data = str(value).encode('utf-8')
            else:
                return None, {}

            # استخراج اطلاعات از metadata
            metadata = image_obj.get('metadata', {})

            # ابعاد
            if '/Width' in metadata and '/Height' in metadata:
                image_info['width'] = int(metadata['/Width'])
                image_info['height'] = int(metadata['/Height'])

            # فضای رنگ
            if '/ColorSpace' in metadata:
                image_info['colorspace'] = metadata['/ColorSpace']

            # عمق بیت
            if '/BitsPerComponent' in metadata:
                image_info['bits_per_component'] = int(metadata['/BitsPerComponent'])

            # فیلتر
            if '/Filter' in metadata:
                image_info['filter'] = metadata['/Filter']

            # DPI
            if '/Width' in metadata and '/Height' in metadata:
                # محاسبه DPI تقریبی
                if '/UserUnit' in metadata:
                    user_unit = float(metadata['/UserUnit'])
                    image_info['dpi'] = int(72 * user_unit)
                else:
                    image_info['dpi'] = 72  # پیش‌فرض

            return image_data, image_info

        except Exception as e:
            logger.warning(f"خطا در استخراج داده‌های تصویر: {e}")
            return None, {}


    def _detect_image_format(self, image_info: dict) -> str:
        """
        تشخیص فرمت تصویر
        
        Args:
            image_info: اطلاعات تصویر
            
        Returns:
            فرمت تصویر
        """
        filter_type = image_info.get('filter', '')

        if '/DCTDecode' in str(filter_type):
            return 'JPEG'
        elif '/FlateDecode' in str(filter_type):
            return 'PNG'
        elif '/CCITTFaxDecode' in str(filter_type):
            return 'CCITT'
        elif '/JBIG2Decode' in str(filter_type):
            return 'JBIG2'
        elif '/JPXDecode' in str(filter_type):
            return 'JPEG2000'
        else:
            # سعی در تشخیص از روی داده‌ها
            return 'UNKNOWN'


    def _optimize_jpeg_image(self, image_data: bytes, image_info: dict, options: dict) -> bytes | None:
        """
        بهینه‌سازی تصویر JPEG
        
        Args:
            image_data: داده‌های تصویر
            image_info: اطلاعات تصویر
            options: گزینه‌های بهینه‌سازی
            
        Returns:
            داده‌های بهینه‌سازی شده
        """
        try:
            from PIL import Image
            import io

            # باز کردن تصویر
            img = cast(Image.Image, Image.open(io.BytesIO(image_data)))

            # کاهش اندازه اگر لازم باشد
            if options.get('downscale_images', True):
                img = self._downscale_image(img, image_info, options)
                self.stats['images_downscaled'] += 1

            # حذف متادیتا
            if options.get('remove_metadata', True):
                # حذف EXIF و سایر متادیتا
                img_data = list(img.getdata())
                img = cast(Image.Image, Image.new(img.mode, img.size))
                img.putdata(img_data)

            # ذخیره با کیفیت بهینه
            output = io.BytesIO()
            quality = options.get('jpeg_quality', 85)

            # تبدیل به RGB اگر لازم باشد
            if img.mode not in ['RGB', 'L']:
                if img.mode == 'RGBA':
                    # ایجاد پس‌زمینه سفید برای تصاویر RGBA
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    img = cast(Image.Image, background)
                else:
                    img = cast(Image.Image, img.convert('RGB'))

            img.save(output, format='JPEG', quality=quality, optimize=True)

            return output.getvalue()

        except Exception as e:
            logger.warning(f"خطا در بهینه‌سازی JPEG: {e}")
            return image_data  # بازگشت داده اصلی در صورت خطا


    def _optimize_png_image(self, image_data: bytes, image_info: dict, options: dict) -> bytes | None:
        """
        بهینه‌سازی تصویر PNG
        
        Args:
            image_data: داده‌های تصویر
            image_info: اطلاعات تصویر
            options: گزینه‌های بهینه‌سازی
            
        Returns:
            داده‌های بهینه‌سازی شده
        """
        try:
            from PIL import Image
            import io

            # باز کردن تصویر
            img = cast(Image.Image, Image.open(io.BytesIO(image_data)))

            # کاهش اندازه اگر لازم باشد
            if options.get('downscale_images', True):
                img = self._downscale_image(img, image_info, options)
                self.stats['images_downscaled'] += 1

            # کاهش عمق رنگ اگر ممکن باشد
            if img.mode in ['RGBA', 'RGB']:
                # بررسی اگر تصویر فقط از 256 رنگ استفاده می‌کند
                colors = img.getcolors(maxcolors=256)
                if colors and len(colors) <= 256:
                    img = cast(Image.Image, img.convert('P', palette=Image.Palette.ADAPTIVE, colors=256))
                    self.stats['images_converted'] += 1

            # ذخیره با فشرده‌سازی بهینه
            output = io.BytesIO()

            # تنظیمات فشرده‌سازی PNG
            png_info: dict[str, Any] = {
                'optimize': True,
            }

            if options.get('compress_png', True):
                # سطح فشرده‌سازی zlib
                png_info['compress_level'] = 9  # حداکثر فشرده‌سازی

            img.save(output, format='PNG', **png_info)

            return output.getvalue()

        except Exception as e:
            logger.warning(f"خطا در بهینه‌سازی PNG: {e}")
            return image_data


    def _optimize_tiff_image(self, image_data: bytes, image_info: dict, options: dict) -> bytes | None:
        """
        بهینه‌سازی تصویر TIFF
        
        Args:
            image_data: داده‌های تصویر
            image_info: اطلاعات تصویر
            options: گزینه‌های بهینه‌سازی
            
        Returns:
            داده‌های بهینه‌سازی شده
        """
        try:
            from PIL import Image
            import io

            # باز کردن تصویر
            img = cast(Image.Image, Image.open(io.BytesIO(image_data)))

            # کاهش اندازه اگر لازم باشد
            if options.get('downscale_images', True):
                img = self._downscale_image(img, image_info, options)
                self.stats['images_downscaled'] += 1

            # تبدیل به JPEG اگر کیفیت قابل قبول باشد
            if options.get('convert_tiff_to_jpeg', True):
                output = io.BytesIO()
                quality = options.get('jpeg_quality', 85)

                # تبدیل به RGB
                if img.mode not in ['RGB', 'L']:
                    img = cast(Image.Image, img.convert('RGB'))

                img.save(output, format='JPEG', quality=quality, optimize=True)
                self.stats['images_converted'] += 1

                return output.getvalue()

            # یا فشرده‌سازی TIFF
            output = io.BytesIO()
            img.save(output, format='TIFF', compression='tiff_lzw')

            return output.getvalue()

        except Exception as e:
            logger.warning(f"خطا در بهینه‌سازی TIFF: {e}")
            return image_data


    def _optimize_jbig2_image(self, image_data: bytes, image_info: dict, options: dict) -> bytes:
        """
        بهینه‌سازی تصویر JBIG2
        (JBIG2 از قبل فشرده است، فقط بررسی اندازه)
        
        Args:
            image_data: داده‌های تصویر
            image_info: اطلاعات تصویر
            options: گزینه‌های بهینه‌سازی
            
        Returns:
            داده‌های بهینه‌سازی شده
        """
        # JBIG2 از قبل بسیار فشرده است
        # فقط می‌توانیم بررسی کنیم که آیا نیاز به downscale دارد
        return image_data


    def _optimize_ccitt_image(self, image_data: bytes, image_info: dict, options: dict) -> bytes:
        """
        بهینه‌سازی تصویر CCITT (فکس)
        
        Args:
            image_data: داده‌های تصویر
            image_info: اطلاعات تصویر
            options: گزینه‌های بهینه‌سازی
            
        Returns:
            داده‌های بهینه‌سازی شده
        """
        # CCITT برای اسناد سیاه و سفید بهینه است
        # معمولاً نیازی به بهینه‌سازی بیشتر ندارد
        return image_data


    def _compress_generic_image(self, image_data: bytes, image_info: dict, options: dict) -> bytes:
        """
        فشرده‌سازی عمومی برای فرمت‌های ناشناخته
        
        Args:
            image_data: داده‌های تصویر
            image_info: اطلاعات تصویر
            options: گزینه‌های بهینه‌سازی
            
        Returns:
            داده‌های فشرده‌شده
        """
        try:
            # استفاده از zlib برای فشرده‌سازی عمومی
            compressed = zlib.compress(image_data, level=9)

            # فقط اگر فشرده‌سازی مؤثر بود
            if len(compressed) < len(image_data):
                return compressed

            return image_data
        except:
            return image_data


    def _downscale_image(self, img: Image.Image, image_info: dict, options: dict) -> Image.Image:
        """
        کاهش اندازه تصویر
        
        Args:
            img: شیء تصویر PIL
            image_info: اطلاعات تصویر
            options: گزینه‌های بهینه‌سازی
            
        Returns:
            تصویر با اندازه کاهش یافته
        """
        try:
            width, height = img.size
            max_width = options.get('max_image_width', 1920)
            max_height = options.get('max_image_height', 1080)
            dpi_threshold = options.get('dpi_threshold', 300)

            # بررسی DPI
            current_dpi = image_info.get('dpi', 72)
            if current_dpi > dpi_threshold:
                # محاسبه ضریب کاهش
                scale_factor = dpi_threshold / current_dpi
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
            else:
                # بررسی ابعاد
                if width > max_width or height > max_height:
                    # محاسبه نسبت
                    width_ratio = max_width / width
                    height_ratio = max_height / height
                    scale_factor = min(width_ratio, height_ratio)

                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)
                else:
                    return img

            # اطمینان از حداقل اندازه
            new_width = max(new_width, 100)
            new_height = max(new_height, 100)

            # تغییر اندازه با فیلتر با کیفیت
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        except Exception as e:
            logger.warning(f"خطا در کاهش اندازه تصویر: {e}")
            return img


    def _create_optimized_image_object(self, original_obj: dict,
                                    optimized_data: bytes,
                                    image_info: dict,
                                    image_format: str) -> dict:
        """
        ایجاد آبجکت تصویر بهینه‌سازی شده
        
        Args:
            original_obj: آبجکت اصلی
            optimized_data: داده‌های بهینه‌سازی شده
            image_info: اطلاعات تصویر
            image_format: فرمت تصویر
            
        Returns:
            آبجکت بهینه‌سازی شده
        """
        # ایجاد کپی از آبجکت اصلی
        optimized_obj = original_obj.copy()

        # به‌روزرسانی stream
        if 'stream' in optimized_obj:
            optimized_obj['stream'] = optimized_data
        elif 'value' in optimized_obj:
            optimized_obj['value'] = optimized_data

        # به‌روزرسانی metadata
        metadata = optimized_obj.get('metadata', {}).copy()

        # به‌روزرسانی اندازه
        metadata['/Length'] = len(optimized_data)

        # به‌روزرسانی فیلتر بر اساس فرمت
        if image_format == 'JPEG':
            metadata['/Filter'] = '/DCTDecode'
        elif image_format == 'PNG':
            metadata['/Filter'] = '/FlateDecode'

        # به‌روزرسانی ابعاد اگر تغییر کرده باشد
        if 'width' in image_info and 'height' in image_info:
            metadata['/Width'] = image_info['width']
            metadata['/Height'] = image_info['height']

        # حذف متادیتای غیرضروری
        if 'remove_metadata' in getattr(self, 'optimization_options', {}):
            keys_to_remove = ['/Metadata', '/PieceInfo', '/StructParent', '/ID']
            for key in keys_to_remove:
                metadata.pop(key, None)

        optimized_obj['metadata'] = metadata

        # افزودن پرچم بهینه‌سازی
        optimized_obj['optimized'] = True
        optimized_obj['original_size'] = self._get_object_size(original_obj)
        optimized_obj['optimized_size'] = len(optimized_data)

        return optimized_obj

    def _remove_unused_objects(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """حذف آبجکت‌های استفاده نشده"""
        # تحلیل ارجاعات و پیدا کردن آبجکت‌های استفاده نشده
        # این پیاده‌سازی ساده فقط آبجکت‌های مشخص را حذف می‌کند

        objects_data = pdf_parts.get('objects_data', b'')

        # پیدا کردن آبجکت‌ها
        object_pattern = rb'(\d+\s+\d+\s+obj.*?endobj)'
        objects = re.findall(object_pattern, objects_data, re.DOTALL)

        # تحلیل ساده (در عمل پیچیده‌تر است)
        used_objects = set()

        # پیدا کردن ارجاعات
        ref_pattern = rb'(\d+\s+\d+\s+R)'
        for obj in objects:
            refs = re.findall(ref_pattern, obj)
            for ref in refs:
                used_objects.add(ref.decode('utf-8').split()[0])

        # حذف آبجکت‌های استفاده نشده
        kept_objects = []
        for obj in objects:
            obj_match = re.match(rb'(\d+)\s+\d+\s+obj', obj)
            if obj_match:
                obj_num = obj_match.group(1).decode('utf-8')
                if obj_num in used_objects or self._is_root_object(obj):
                    kept_objects.append(obj)
                else:
                    self.stats['objects_removed'] += 1

        pdf_parts['objects_data'] = b'\n'.join(kept_objects)
        return pdf_parts

    def _is_root_object(self, obj_data: bytes) -> bool:
        """بررسی اینکه آیا آبجکت ریشه است"""
        root_patterns = [
            rb'/Type\s*/Catalog',
            rb'/Pages\s+\d+\s+\d+\s+R',
            rb'/Outlines',
            rb'/AcroForm'
        ]

        for pattern in root_patterns:
            if re.search(pattern, obj_data):
                return True

        return False

    def _remove_duplicates(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """حذف داده‌های تکراری"""
        # شناسایی و حذف آبجکت‌های تکراری
        # این پیاده‌سازی ساده فقط آبجکت‌های یکسان را حذف می‌کند

        objects_data = pdf_parts.get('objects_data', b'')

        object_pattern = rb'(\d+\s+\d+\s+obj.*?endobj)'
        objects = re.findall(object_pattern, objects_data, re.DOTALL)

        # حذف تکراری‌ها
        unique_objects = []
        seen_hashes = set()

        for obj in objects:
            obj_hash = hashlib.md5(obj).hexdigest()
            if obj_hash not in seen_hashes:
                seen_hashes.add(obj_hash)
                unique_objects.append(obj)
            else:
                self.stats['objects_removed'] += 1

        pdf_parts['objects_data'] = b'\n'.join(unique_objects)
        return pdf_parts

    def _remove_metadata(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """حذف متادیتا"""
        # حذف دیکشنری Info و XMP metadata
        objects_data = pdf_parts.get('objects_data', b'')

        # حذف آبجکت‌های Info
        info_pattern = rb'\d+\s+\d+\s+obj\s*<<\s*/Type\s*/Metadata.*?endobj'
        objects_data = re.sub(info_pattern, b'', objects_data, flags=re.DOTALL)

        # حذف XMP
        xmp_pattern = rb'<x:xmpmeta.*?</x:xmpmeta>'
        objects_data = re.sub(xmp_pattern, b'', objects_data, flags=re.DOTALL | re.IGNORECASE)

        pdf_parts['objects_data'] = objects_data
        return pdf_parts

    def _linearize_pdf(self, pdf_parts: dict[str, Any]) -> dict[str, Any]:
        """
        خطی‌سازی PDF برای بارگذاری سریع‌تر در وب
        
        پیاده‌سازی بر اساس استاندارد PDF 1.4+ Linearization
        RFC: https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/PDF32000_2008.pdf
        بخش: Annex F (Linearized PDF)
        
        Args:
            pdf_parts: دیکشنری حاوی بخش‌های PDF
            
        Returns:
            pdf_parts خطی‌سازی شده
        """
        try:
            # 1. بررسی ساختار PDF
            if 'objects' not in pdf_parts or not pdf_parts['objects']:
                logger.warning("PDF بدون آبجکت برای خطی‌سازی")
                return pdf_parts

            objects = pdf_parts['objects']
            total_objects = len(objects)

            # 2. ایجاد Linearization Dictionary (آبجکت اول)
            linearization_value: dict[str, Any] = {
                'Type': '/Linearization',
                'L': pdf_parts.get('file_size', 0),
                'H': [0, 0],
                'O': 1,
                'E': 0,
                'N': total_objects,
                'T': 0,
                'P': 0
            }
            linearization_dict: dict[str, Any] = {
                'obj_num': 1,
                'generation': 0,
                'type': 'dict',
                'value': linearization_value
            }

            # 3. شناسایی صفحات و مرتب‌سازی
            pages = []
            page_objects = []
            other_objects = []

            for obj in objects:
                if obj.get('type') == 'page':
                    pages.append(obj)
                    page_objects.append(obj)
                else:
                    other_objects.append(obj)

            # 4. مرتب‌سازی آبجکت‌ها برای خطی‌سازی
            # ترتیب: Linearization Dict → Root → Pages → Resources → Content → سایر
            sorted_objects = []

            # 4.1. Linearization Dictionary (همیشه آبجکت 1)
            sorted_objects.append(linearization_dict)

            # 4.2. Root object
            root_obj = next((obj for obj in objects if obj.get('type') == 'catalog'), None)
            if root_obj:
                sorted_objects.append(root_obj)
                other_objects.remove(root_obj)

            # 4.3. Pages objects
            sorted_objects.extend(page_objects)

            # 4.4. Page resources
            resource_objects = [obj for obj in other_objects if obj.get('type') in ['font', 'xobject', 'colorspace']]
            sorted_objects.extend(resource_objects)
            for obj in resource_objects:
                other_objects.remove(obj)

            # 4.5. Page contents
            content_objects = [obj for obj in other_objects if obj.get('type') == 'content']
            sorted_objects.extend(content_objects)
            for obj in content_objects:
                other_objects.remove(obj)

            # 4.6. سایر آبجکت‌ها
            sorted_objects.extend(other_objects)

            # 5. به‌روزرسانی شماره‌های آبجکت
            for i, obj in enumerate(sorted_objects, 1):
                obj['obj_num'] = i

            # 6. ایجاد Hint Tables
            hint_tables = self._create_hint_tables(sorted_objects, pages)

            # 7. ایجاد Hint Stream
            hint_stream = self._create_hint_stream(hint_tables)
            hint_stream_obj = {
                'obj_num': len(sorted_objects) + 1,
                'generation': 0,
                'type': 'stream',
                'value': hint_stream,
                'metadata': {
                    'Length': len(hint_stream),
                    'Filter': '/FlateDecode'
                }
            }

            sorted_objects.append(hint_stream_obj)

            # 8. به‌روزرسانی Linearization Dictionary با اطلاعات Hint Stream
            linearization_value['H'] = [
                self._calculate_object_offset(hint_stream_obj, sorted_objects),
                len(hint_stream)
            ]

            # 9. به‌روزرسانی اطلاعات صفحات
            if pages:
                first_page = pages[0]
                linearization_value['P'] = first_page['obj_num']
                linearization_value['T'] = self._calculate_object_offset(first_page, sorted_objects)

            # 10. ایجاد هدر خطی‌سازی شده
            # استفاده از کامنت استاندارد به جای کاراکترهای چینی
            linearized_header = b'%PDF-1.7\n%EOF\n%Linearized-1.0\n'

            # 11. به‌روزرسانی pdf_parts
            pdf_parts['header'] = linearized_header
            pdf_parts['objects'] = sorted_objects
            pdf_parts['linearized'] = True

            # 12. محاسبه مجدد offsets برای xref table
            pdf_parts['xref_offsets'] = self._calculate_xref_offsets(sorted_objects, len(linearized_header))

            logger.info(f"PDF خطی‌سازی شده با {len(sorted_objects)} آبجکت")
            return pdf_parts

        except Exception as e:
            logger.error(f"خطا در خطی‌سازی PDF: {e}", exc_info=True)
            # در صورت خطا، PDF اصلی را بازمی‌گردانیم
            return pdf_parts


    def _create_hint_tables(self, objects: list[dict], pages: list[dict]) -> dict[str, list]:
        """
        ایجاد Hint Tables برای خطی‌سازی
        
        Hint Tables شامل اطلاعاتی برای بارگذاری بهینه صفحات هستند.
        
        Args:
            objects: لیست آبجکت‌های مرتب‌شده
            pages: لیست آبجکت‌های صفحه
            
        Returns:
            دیکشنری حاوی hint tables
        """
        hint_tables: dict[str, list[list[int]]] = {
            'primary': [],  # Primary Hint Table
            'overflow': []  # Overflow Hint Table
        }

        # محاسبه offsets برای هر صفحه
        page_offsets = []
        for page in pages:
            offset = self._calculate_object_offset(page, objects)
            length = self._calculate_object_length(page)
            page_offsets.append({
                'offset': offset,
                'length': length,
                'obj_num': page['obj_num']
            })

        # ایجاد Primary Hint Table
        # فرمت: [object_number, offset, length] برای هر صفحه
        for page_info in page_offsets:
            hint_tables['primary'].append([
                page_info['obj_num'],
                page_info['offset'],
                page_info['length']
            ])

        # ایجاد Overflow Hint Table (برای اطلاعات اضافی)
        # شامل اطلاعات shared objects بین صفحات
        shared_objects = self._identify_shared_objects(objects, pages)
        for shared_obj in shared_objects:
            offset = self._calculate_object_offset(shared_obj, objects)
            length = self._calculate_object_length(shared_obj)
            hint_tables['overflow'].append([
                shared_obj['obj_num'],
                offset,
                length,
                len(shared_obj.get('shared_pages', []))
            ])

        return hint_tables


    def _create_hint_stream(self, hint_tables: dict[str, list]) -> bytes:
        """
        ایجاد Hint Stream به صورت بایت
        
        Args:
            hint_tables: tables hint
            
        Returns:
            بایت‌های hint stream
        """
        import struct
        import zlib

        # ساختار داده‌های hint
        hint_data = bytearray()

        # Primary Hint Table
        primary_table = hint_tables['primary']
        hint_data.extend(struct.pack('>I', len(primary_table)))  # تعداد صفحات

        for entry in primary_table:
            # object number, offset, length
            hint_data.extend(struct.pack('>III', entry[0], entry[1], entry[2]))

        # Overflow Hint Table
        overflow_table = hint_tables['overflow']
        hint_data.extend(struct.pack('>I', len(overflow_table)))  # تعداد shared objects

        for entry in overflow_table:
            # object number, offset, length, page_count
            hint_data.extend(struct.pack('>IIIH', entry[0], entry[1], entry[2], entry[3]))

        # فشرده‌سازی با zlib
        compressed_data = zlib.compress(hint_data)

        return compressed_data


    def _calculate_object_offset(self, obj: dict, all_objects: list[dict]) -> int:
        """
        محاسبه offset آبجکت در فایل
        
        Args:
            obj: آبجکت مورد نظر
            all_objects: لیست تمام آبجکت‌ها
            
        Returns:
            offset در بایت
        """
        # این یک پیاده‌سازی ساده است
        # در پیاده‌سازی واقعی باید offset دقیق محاسبه شود
        base_offset = 100  # offset هدر و سایر اطلاعات

        # پیدا کردن index آبجکت
        try:
            obj_index = all_objects.index(obj)
            # فرض: هر آبجکت حدود 500 بایت فضا می‌گیرد
            return base_offset + (obj_index * 500)
        except ValueError:
            return base_offset


    def _calculate_object_length(self, obj: dict) -> int:
        """
        محاسبه طول آبجکت
        
        Args:
            obj: آبجکت مورد نظر
            
        Returns:
            طول بر حسب بایت
        """
        # محاسبه تقریبی طول بر اساس نوع آبجکت
        obj_type = obj.get('type', 'unknown')

        if obj_type == 'page':
            return 200  # طول تقریبی page object
        elif obj_type == 'content':
            content = obj.get('value', '')
            return len(str(content).encode('utf-8')) + 100
        elif obj_type == 'font':
            return 300
        elif obj_type == 'stream':
            stream_data = obj.get('value', b'')
            return len(stream_data) + 50
        else:
            return 100


    def _identify_shared_objects(self, objects: list[dict], pages: list[dict]) -> list[dict]:
        """
        شناسایی آبجکت‌های مشترک بین صفحات
        
        Args:
            objects: تمام آبجکت‌ها
            pages: آبجکت‌های صفحه
            
        Returns:
            لیست آبجکت‌های مشترک
        """
        shared_objects = []

        # منابعی که بین صفحات مشترک هستند (فونت‌ها، تصاویر، ...)
        resource_types = ['font', 'xobject', 'colorspace', 'pattern']

        for obj in objects:
            if obj.get('type') in resource_types:
                # بررسی استفاده در بیش از یک صفحه
                used_in_pages = []

                for page in pages:
                    page_resources = page.get('resources', {})
                    resource_refs = []

                    if 'Font' in page_resources:
                        resource_refs.extend(page_resources['Font'].values())
                    if 'XObject' in page_resources:
                        resource_refs.extend(page_resources['XObject'].values())
                    if 'ColorSpace' in page_resources:
                        resource_refs.extend(page_resources['ColorSpace'].values())

                    if obj['obj_num'] in resource_refs:
                        used_in_pages.append(page['obj_num'])

                if len(used_in_pages) > 1:
                    obj['shared_pages'] = used_in_pages
                    shared_objects.append(obj)

        return shared_objects


    def _calculate_xref_offsets(self, objects: list[dict], header_length: int) -> list[int]:
        """
        محاسبه offsets برای xref table
        
        Args:
            objects: آبجکت‌های مرتب‌شده
            header_length: طول هدر
            
        Returns:
            لیست offsets
        """
        offsets = []
        current_offset = header_length

        for obj in objects:
            offsets.append(current_offset)
            # محاسبه طول آبجکت فعلی
            obj_length = self._calculate_object_length(obj)
            current_offset += obj_length

        return offsets

    def _assemble_pdf(self, pdf_parts: dict[str, Any]) -> bytes:
        """مونتاژ مجدد PDF"""
        parts = [
            pdf_parts.get('header', b'%PDF-1.7\n'),
            pdf_parts.get('objects_data', b''),
            pdf_parts.get('xref', b''),
            pdf_parts.get('trailer', b''),
            pdf_parts.get('startxref', b'')
        ]

        return b''.join(parts)

    def get_optimization_stats(self) -> dict[str, Any]:
        """دریافت آمار بهینه‌سازی"""
        return self.stats.copy()
