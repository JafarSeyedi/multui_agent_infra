"""
مدیریت فونت‌ها در PDF - پیاده‌سازی حرفه‌ای با پشتیبانی کامل از فونت‌های فارسی و انگلیسی
"""

# mypy: ignore-errors

import os
import tempfile
import hashlib
import base64
import zlib
from typing import Dict, List, Optional, Tuple, Union, BinaryIO
from dataclasses import dataclass, field
from enum import Enum
import struct
from pathlib import Path
import warnings

# برای فونت‌های استاندارد PDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.pdfgen.canvas import Canvas

# برای پردازش فونت‌های TrueType/OpenType
try:
    from fontTools.ttLib import TTFont as FontToolsTTF
    from fontTools.subset import Subsetter
    FONTTOOLS_AVAILABLE = True
except ImportError:
    FONTTOOLS_AVAILABLE = False
    warnings.warn("fontTools not installed. Advanced font features will be limited.")


class FontStyle(Enum):
    """استایل‌های فونت"""
    NORMAL = "normal"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"
    LIGHT = "light"
    MEDIUM = "medium"
    SEMI_BOLD = "semi_bold"
    EXTRA_BOLD = "extra_bold"
    BLACK = "black"


class FontEncoding(Enum):
    """انکودینگ‌های فونت PDF"""
    WIN_ANSI = "WinAnsiEncoding"
    MAC_ROMAN = "MacRomanEncoding"
    PDF_DOC = "PDFDocEncoding"
    IDENTITY_H = "Identity-H"  # برای Unicode افقی
    IDENTITY_V = "Identity-V"  # برای Unicode عمودی
    CUSTOM = "Custom"


class FontSubsetStrategy(Enum):
    """استراتژی‌های زیرمجموعه‌سازی فونت"""
    NONE = "none"           # بدون زیرمجموعه‌سازی
    FULL = "full"           # تعبیه کامل فونت
    SUBSET = "subset"       # زیرمجموعه بر اساس کاراکترهای استفاده شده
    COMPRESSED = "compressed"  # زیرمجموعه فشرده شده


@dataclass
class FontMetrics:
    """متریک‌های فونت"""
    ascent: int = 0          # ارتفاع بالایی
    descent: int = 0         # ارتفاع پایینی
    cap_height: int = 0      # ارتفاع حروف بزرگ
    x_height: int = 0       # ارتفاع حروف کوچک
    italic_angle: int = 0   # زاویه ایتالیک
    stem_v: int = 0         # ضخامت عمودی
    stem_h: int = 0         # ضخامت افقی
    avg_width: int = 0      # میانگین عرض
    max_width: int = 0      # حداکثر عرض
    missing_width: int = 0  # عرض پیش‌فرض برای کاراکترهای ناموجود
    font_bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)  # [llx, lly, urx, ury]
    flags: int = 0          # پرچم‌های فونت


@dataclass
class FontInfo:
    """اطلاعات کامل فونت"""
    # اطلاعات پایه
    name: str                      # نام فونت (PostScript)
    family: str                    # خانواده فونت
    style: FontStyle               # استایل فونت
    language: str = "fa"          # زبان فونت (پیش‌فرض فارسی)
    
    # اطلاعات فنی
    embedded: bool = False         # آیا فونت تعبیه شده است؟
    subset: bool = False           # آیا زیرمجموعه شده است؟
    encoding: FontEncoding = FontEncoding.IDENTITY_H
    subset_strategy: FontSubsetStrategy = FontSubsetStrategy.FULL
    
    # داده‌های فونت
    ttf_data: Optional[bytes] = None          # داده‌های خام TTF/OTF
    subset_data: Optional[bytes] = None        # داده‌های زیرمجموعه
    used_glyphs: List[int] = field(default_factory=list)  # گلیف‌های استفاده شده
    
    # اطلاعات PDF
    pdf_name: Optional[str] = None            # نام فونت در PDF (مثل /F1)
    object_number: Optional[int] = None       # شماره آبجکت در PDF
    generation_number: int = 0                # شماره نسل
    
    # متریک‌ها
    metrics: FontMetrics = field(default_factory=FontMetrics)
    
    # اطلاعات فایل
    file_path: Optional[str] = None           # مسیر فایل فونت
    file_size: int = 0                        # حجم فایل
    checksum: Optional[str] = None            # چکسام فونت
    
    # اطلاعات فنی پیشرفته
    is_cid: bool = False                      # آیا فونت CID است؟
    cid_system_info: Optional[Dict] = None    # اطلاعات سیستم CID
    cmap: Optional[Dict] = None               # نقشه کاراکتر به گلیف
    glyph_widths: Optional[Dict[int, int]] = None  # عرض گلیف‌ها
    
    def __post_init__(self):
        """اعتبارسنجی و تنظیم مقادیر پیش‌فرض"""
        if not self.pdf_name:
            self.pdf_name = f"/F{hash(self.name) % 10000:04d}"
        
        if self.ttf_data:
            self.file_size = len(self.ttf_data)
            self.checksum = hashlib.md5(self.ttf_data).hexdigest()
            
            # استخراج متریک‌ها از داده‌های فونت
            if FONTTOOLS_AVAILABLE:
                self._extract_metrics_from_ttf()
    
    def _extract_metrics_from_ttf(self):
        """استخراج متریک‌ها از فایل TTF"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.ttf', delete=False) as tmp:
                tmp.write(self.ttf_data)
                tmp_path = tmp.name
            
            font = FontToolsTTF(tmp_path)
            
            # استخراج اطلاعات از جداول مختلف
            os2_table = font['OS/2']
            head_table = font['head']
            hhea_table = font['hhea'] if 'hhea' in font else None
            post_table = font['post'] if 'post' in font else None
            
            # تنظیم متریک‌ها
            self.metrics.ascent = getattr(hhea_table, 'ascent', 0) if hhea_table else 0
            self.metrics.descent = getattr(hhea_table, 'descent', 0) if hhea_table else 0
            self.metrics.cap_height = getattr(os2_table, 'sCapHeight', 0)
            self.metrics.x_height = getattr(os2_table, 'sxHeight', 0)
            self.metrics.italic_angle = getattr(post_table, 'italicAngle', 0) if post_table else 0
            self.metrics.stem_v = 80  # مقدار پیش‌فرض برای فونت‌های لاتین
            
            # Font BBox
            self.metrics.font_bbox = (
                head_table.xMin,
                head_table.yMin,
                head_table.xMax,
                head_table.yMax
            )
            
            # پرچم‌های فونت
            flags = 0
            if os2_table.fsSelection & 0x001:  # Italic
                flags |= 1 << 6
            if os2_table.fsSelection & 0x020:  # Bold
                flags |= 1 << 18
            if os2_table.panose.bFamilyType == 2:  # Latin
                flags |= 1 << 1
            elif os2_table.panose.bFamilyType == 5:  # Symbol
                flags |= 1 << 2
            else:  # Nonsymbolic
                flags |= 1 << 5
            
            self.metrics.flags = flags
            
            # استخراج عرض گلیف‌ها
            if 'hmtx' in font:
                hmtx_table = font['hmtx']
                self.metrics.glyph_widths = {}
                for glyph_name in font.getGlyphOrder():
                    if glyph_name in hmtx_table.metrics:
                        self.metrics.glyph_widths[glyph_name] = hmtx_table.metrics[glyph_name][0]
            
            # استخراج cmap
            if 'cmap' in font:
                cmap_table = font['cmap']
                self.cmap = {}
                for table in cmap_table.tables:
                    if table.isUnicode():
                        for code, glyph_name in table.cmap.items():
                            self.cmap[code] = glyph_name
            
            font.close()
            os.unlink(tmp_path)
            
        except Exception as e:
            warnings.warn(f"خطا در استخراج متریک‌های فونت {self.name}: {e}")
    
    def create_subset(self, characters: str) -> bytes:
        """ایجاد زیرمجموعه فونت بر اساس کاراکترهای استفاده شده"""
        if not self.ttf_data or not FONTTOOLS_AVAILABLE:
            return self.ttf_data or b""
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.ttf', delete=False) as tmp:
                tmp.write(self.ttf_data)
                tmp_path = tmp.name
            
            # بارگذاری فونت
            font = FontToolsTTF(tmp_path)
            
            # تنظیم زیرمجموعه
            subsetter = Subsetter()
            
            # تبدیل کاراکترها به کدهای Unicode
            unicodes = {ord(c) for c in characters if ord(c) < 0xFFFF}
            
            # افزودن کاراکترهای ضروری
            unicodes.update({0x0020})  # Space
            unicodes.update({0x000D, 0x000A})  # CR, LF
            
            # برای فونت‌های فارسی، کاراکترهای ضروری فارسی را اضافه کن
            if self.language == "fa":
                # کاراکترهای ضروری فارسی
                persian_essential = {
                    0x0621, 0x0622, 0x0623, 0x0624, 0x0625, 0x0626, 0x0627,  # همزه تا الف
                    0x0628, 0x0629, 0x062A, 0x062B, 0x062C, 0x062D, 0x062E,  # ب تا خ
                    0x062F, 0x0630, 0x0631, 0x0632, 0x0633, 0x0634, 0x0635,  # د تا ص
                    0x0636, 0x0637, 0x0638, 0x0639, 0x063A, 0x0640, 0x0641,  # ض تا ف
                    0x0642, 0x0643, 0x0644, 0x0645, 0x0646, 0x0647, 0x0648,  # ق تا و
                    0x0649, 0x064A, 0x064B, 0x064C, 0x064D, 0x064E, 0x064F,  # ی تا حرکات
                    0x0650, 0x0651, 0x0652, 0x0653, 0x0654, 0x0655, 0x0656,  # حرکات ادامه
                    0x0660, 0x0661, 0x0662, 0x0663, 0x0664, 0x0665, 0x0666,  # اعداد فارسی
                    0x0667, 0x0668, 0x0669, 0x06F0, 0x06F1, 0x06F2, 0x06F3,  # اعداد ادامه
                    0x06F4, 0x06F5, 0x06F6, 0x06F7, 0x06F8, 0x06F9, 0x067E,  # پ
                    0x0686, 0x0698, 0x06AF, 0x06A9, 0x06CC, 0x06C0, 0x0629    # چ ژ گ ک ی ه
                }
                unicodes.update(persian_essential)
            
            subsetter.populate(unicodes=unicodes)
            subsetter.subset(font)
            
            # ذخیره زیرمجموعه
            with tempfile.NamedTemporaryFile(suffix='.subset.ttf', delete=False) as tmp_subset:
                subset_path = tmp_subset.name
            
            font.save(subset_path)
            
            # خواندن داده‌های زیرمجموعه
            with open(subset_path, 'rb') as f:
                subset_data = f.read()
            
            # ذخیره گلیف‌های استفاده شده
            self.used_glyphs = list(unicodes)
            self.subset = True
            self.subset_data = subset_data
            
            # پاکسازی فایل‌های موقت
            font.close()
            os.unlink(tmp_path)
            os.unlink(subset_path)
            
            return subset_data
            
        except Exception as e:
            warnings.warn(f"خطا در ایجاد زیرمجموعه فونت {self.name}: {e}")
            return self.ttf_data or b""
    
    def get_font_data(self) -> bytes:
        """دریافت داده‌های فونت (اصلی یا زیرمجموعه)"""
        if self.subset and self.subset_data:
            return self.subset_data
        return self.ttf_data or b""
    
    def get_encoding_name(self) -> str:
        """دریافت نام انکودینگ برای PDF"""
        if self.encoding == FontEncoding.IDENTITY_H:
            return "/Identity-H"
        elif self.encoding == FontEncoding.IDENTITY_V:
            return "/Identity-V"
        elif self.encoding == FontEncoding.WIN_ANSI:
            return "/WinAnsiEncoding"
        elif self.encoding == FontEncoding.MAC_ROMAN:
            return "/MacRomanEncoding"
        elif self.encoding == FontEncoding.PDF_DOC:
            return "/PDFDocEncoding"
        else:
            return "/Identity-H"  # پیش‌فرض


class FontManager:
    """مدیر فونت‌های PDF با پشتیبانی کامل از فارسی و انگلیسی"""
    
    # فونت‌های استاندارد فارسی (مجاز)
    PERSIAN_STANDARD_FONTS = {
        "B Nazanin": {
            "normal": "B Nazanin",
            "bold": "B Nazanin Bold",
            "italic": "B Nazanin Italic"
        },
        "B Lotus": {
            "normal": "B Lotus",
            "bold": "B Lotus Bold",
            "italic": "B Lotus Italic"
        },
        "B Mitra": {
            "normal": "B Mitra",
            "bold": "B Mitra Bold"
        },
        "B Traffic": {
            "normal": "B Traffic",
            "bold": "B Traffic Bold"
        },
        "B Yekan": {
            "normal": "B Yekan",
            "bold": "B Yekan Bold"
        },
        "B Zar": {
            "normal": "B Zar",
            "bold": "B Zar Bold"
        },
        "IranNastaliq": {
            "normal": "IranNastaliq"
        },
        "Iranian Sans": {
            "normal": "Iranian Sans",
            "bold": "Iranian Sans Bold"
        },
        "Iranian Serif": {
            "normal": "Iranian Serif",
            "bold": "Iranian Serif Bold"
        }
    }
    
    # فونت‌های استاندارد لاتین
    LATIN_STANDARD_FONTS = {
        "Helvetica": {
            "normal": "Helvetica",
            "bold": "Helvetica-Bold",
            "italic": "Helvetica-Oblique",
            "bold_italic": "Helvetica-BoldOblique"
        },
        "Times": {
            "normal": "Times-Roman",
            "bold": "Times-Bold",
            "italic": "Times-Italic",
            "bold_italic": "Times-BoldItalic"
        },
        "Courier": {
            "normal": "Courier",
            "bold": "Courier-Bold",
            "italic": "Courier-Oblique",
            "bold_italic": "Courier-BoldOblique"
        },
        "Symbol": {
            "normal": "Symbol"
        },
        "ZapfDingbats": {
            "normal": "ZapfDingbats"
        }
    }
    
    def __init__(self, embed_fonts: bool = True, subset_fonts: bool = True):
        """
        مقداردهی اولیه مدیر فونت
        
        Args:
            embed_fonts: آیا فونت‌ها تعبیه شوند؟
            subset_fonts: آیا از زیرمجموعه‌سازی استفاده شود؟
        """
        self.fonts: Dict[str, FontInfo] = {}
        self.font_mapping: Dict[Tuple[str, str, str], str] = {}  # (family, style, language) -> font_key
        self.embed_fonts = embed_fonts
        self.subset_fonts = subset_fonts
        self.next_font_id = 1
        
        # ثبت فونت‌های استاندارد
        self._register_standard_fonts()
        
        # کش برای فونت‌های بارگذاری شده
        self._font_cache: Dict[str, bytes] = {}
        
        # دایرکتوری‌های جستجوی فونت
        self.font_directories = self._get_default_font_directories()
    
    def _get_default_font_directories(self) -> List[str]:
        """دریافت دایرکتوری‌های پیش‌فرض فونت"""
        directories = []
        
        # سیستم‌عامل‌های مختلف
        if os.name == 'nt':  # Windows
            directories.extend([
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts'),
            ])
        elif os.name == 'posix':  # Linux/Mac
            directories.extend([
                '/usr/share/fonts',
                '/usr/local/share/fonts',
                '/Library/Fonts',  # Mac
                os.path.expanduser('~/.fonts'),
                os.path.expanduser('~/Library/Fonts'),  # Mac user
            ])
        
        # دایرکتوری‌های فارسی
        persian_dirs = [
            '/usr/share/fonts/truetype/persian',
            '/usr/share/fonts/truetype/farsi',
            '/usr/share/fonts/iranian',
        ]
        
        for dir_path in persian_dirs:
            if os.path.exists(dir_path):
                directories.append(dir_path)
        
        return directories
    
    def _register_standard_fonts(self):
        """ثبت فونت‌های استاندارد PDF"""
        # فونت‌های لاتین
        for family, styles in self.LATIN_STANDARD_FONTS.items():
            for style_name, font_name in styles.items():
                style = FontStyle(style_name)
                font_info = FontInfo(
                    name=font_name,
                    family=family,
                    style=style,
                    language="en",
                    embedded=False,  # فونت‌های استاندارد تعبیه نمی‌شوند
                    encoding=FontEncoding.WIN_ANSI
                )
                
                font_key = f"STD-{family}-{style.value}"
                self.fonts[font_key] = font_info
                self.font_mapping[(family, style.value, "en")] = font_key
        
        # فونت‌های فارسی (به عنوان فونت‌های تعبیه‌شده)
        for family, styles in self.PERSIAN_STANDARD_FONTS.items():
            for style_name, font_name in styles.items():
                style = FontStyle(style_name)
                font_info = FontInfo(
                    name=font_name,
                    family=family,
                    style=style,
                    language="fa",
                    embedded=True,  # فونت‌های فارسی باید تعبیه شوند
                    encoding=FontEncoding.IDENTITY_H,
                    subset_strategy=FontSubsetStrategy.SUBSET if self.subset_fonts else FontSubsetStrategy.FULL
                )
                
                font_key = f"FA-{family}-{style.value}"
                self.fonts[font_key] = font_info
                self.font_mapping[(family, style.value, "fa")] = font_key
    
    def register_font_file(self, font_path: str, family: Optional[str] = None,
                          style: FontStyle = FontStyle.NORMAL,
                          language: str = "fa") -> str:
        """ثبت فونت از فایل"""
        try:
            # بررسی وجود فایل
            if not os.path.exists(font_path):
                raise FileNotFoundError(f"فونت یافت نشد: {font_path}")
            
            # خواندن فایل فونت
            with open(font_path, 'rb') as f:
                font_data = f.read()
            
            # استخراج نام فونت از داده‌ها
            font_name = self._extract_font_name(font_data)
            if not font_name:
                font_name = Path(font_path).stem
            
            # استفاده از نام خانواده ارائه شده یا استخراج شده
            actual_family = family or self._extract_font_family(font_data) or font_name
            
            # ایجاد کلید یکتا
            font_key = f"CUSTOM-{actual_family}-{style.value}-{language}-{hash(font_data) % 10000:04d}"
            
            # ایجاد اطلاعات فونت
            font_info = FontInfo(
                name=font_name,
                family=actual_family,
                style=style,
                language=language,
                embedded=self.embed_fonts,
                ttf_data=font_data,
                file_path=font_path,
                encoding=FontEncoding.IDENTITY_H if language == "fa" else FontEncoding.WIN_ANSI,
                subset_strategy=FontSubsetStrategy.SUBSET if self.subset_fonts else FontSubsetStrategy.FULL
            )
            
            # ذخیره در کش
            self._font_cache[font_key] = font_data
            
            # ثبت فونت
            self.fonts[font_key] = font_info
            self.font_mapping[(actual_family, style.value, language)] = font_key
            
            # ثبت در ReportLab (اگر موجود باشد)
            self._register_with_reportlab(font_info)
            
            return font_key
            
        except Exception as e:
            warnings.warn(f"خطا در ثبت فونت از فایل {font_path}: {e}")
            # بازگشت به فونت پیش‌فرض
            return self.get_default_font(language, style)
    
    def register_font_data(self, font_data: bytes, font_name: str, family: str,
                          style: FontStyle = FontStyle.NORMAL,
                          language: str = "fa") -> str:
        """ثبت فونت از داده‌های باینری"""
        try:
            # ایجاد کلید یکتا
            font_key = f"CUSTOM-{family}-{style.value}-{language}-{hash(font_data) % 10000:04d}"
            
            # ایجاد اطلاعات فونت
            font_info = FontInfo(
                name=font_name,
                family=family,
                style=style,
                language=language,
                embedded=self.embed_fonts,
                ttf_data=font_data,
                encoding=FontEncoding.IDENTITY_H if language == "fa" else FontEncoding.WIN_ANSI,
                subset_strategy=FontSubsetStrategy.SUBSET if self.subset_fonts else FontSubsetStrategy.FULL
            )
            
            # ذخیره در کش
            self._font_cache[font_key] = font_data
            
            # ثبت فونت
            self.fonts[font_key] = font_info
            self.font_mapping[(family, style.value, language)] = font_key
            
            # ثبت در ReportLab
            self._register_with_reportlab(font_info)
            
            return font_key
            
        except Exception as e:
            warnings.warn(f"خطا در ثبت فونت از داده‌ها: {e}")
            return self.get_default_font(language, style)
    
    def _extract_font_name(self, font_data: bytes) -> Optional[str]:
        """استخراج نام فونت از داده‌های TTF/OTF"""
        if not FONTTOOLS_AVAILABLE or len(font_data) < 100:
            return None
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.ttf', delete=False) as tmp:
                tmp.write(font_data)
                tmp_path = tmp.name
            
            font = FontToolsTTF(tmp_path)
            
            # استخراج نام از جدول 'name'
            name_table = font['name']
            font_name = None
            
            # جستجوی نام به زبان انگلیسی
            for record in name_table.names:
                if record.nameID == 4 and record.platformID == 3 and record.platEncID == 1:
                    font_name = record.toUnicode()
                    break
            
            # اگر نام انگلیسی یافت نشد، اولین نام را بگیر
            if not font_name and name_table.names:
                font_name = name_table.names[0].toUnicode()
            
            font.close()
            os.unlink(tmp_path)
            
            return font_name
            
        except Exception:
            return None
    
    def _extract_font_family(self, font_data: bytes) -> Optional[str]:
        """استخراج خانواده فونت از داده‌های TTF/OTF"""
        if not FONTTOOLS_AVAILABLE:
            return None
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.ttf', delete=False) as tmp:
                tmp.write(font_data)
                tmp_path = tmp.name
            
            font = FontToolsTTF(tmp_path)
            
            # استخراج خانواده از جدول 'name'
            name_table = font['name']
            font_family = None
            
            for record in name_table.names:
                if record.nameID == 1 and record.platformID == 3 and record.platEncID == 1:
                    font_family = record.toUnicode()
                    break
            
            font.close()
            os.unlink(tmp_path)
            
            return font_family
            
        except Exception:
            return None
    
    def _register_with_reportlab(self, font_info: FontInfo):
        """ثبت فونت در ReportLab"""
        try:
            if not font_info.ttf_data:
                return
            
            # ایجاد نام ReportLab
            reportlab_name = f"{font_info.family}_{font_info.style.value}"
            
            # ذخیره موقت فایل فونت
            with tempfile.NamedTemporaryFile(suffix='.ttf', delete=False) as tmp:
                tmp.write(font_info.ttf_data)
                tmp_path = tmp.name
            
            # ثبت در ReportLab
            pdfmetrics.registerFont(TTFont(reportlab_name, tmp_path))
            
            # ثبت مپینگ
            addMapping(
                font_info.family,
                font_info.style == FontStyle.BOLD or font_info.style == FontStyle.BOLD_ITALIC,
                font_info.style == FontStyle.ITALIC or font_info.style == FontStyle.BOLD_ITALIC,
                reportlab_name
            )
            
            # حذف فایل موقت
            os.unlink(tmp_path)
            
        except Exception as e:
            warnings.warn(f"خطا در ثبت فونت {font_info.name} در ReportLab: {e}")
    
    def get_font(self, family: str, style: FontStyle = FontStyle.NORMAL,
                language: str = "fa") -> Optional[FontInfo]:
        """دریافت اطلاعات فونت"""
        # جستجوی مستقیم
        key = (family, style.value, language)
        if key in self.font_mapping:
            font_key = self.font_mapping[key]
            return self.fonts.get(font_key)
        
        # جستجو با زبان جایگزین
        alt_language = "en" if language == "fa" else "fa"
        key = (family, style.value, alt_language)
        if key in self.font_mapping:
            font_key = self.font_mapping[key]
            return self.fonts.get(font_key)
        
        # جستجوی بدون در نظر گرفتن زبان
        for lang in [language, alt_language, "*"]:
            for style_variant in [style.value, "normal"]:
                key = (family, style_variant, lang)
                if key in self.font_mapping:
                    font_key = self.font_mapping[key]
                    return self.fonts.get(font_key)
        
        return None
    
    def get_pdf_font_name(self, family: str, style: FontStyle = FontStyle.NORMAL,
                         language: str = "fa") -> str:
        """دریافت نام فونت برای استفاده در PDF"""
        font_info = self.get_font(family, style, language)
        if font_info and font_info.pdf_name:
            return font_info.pdf_name
        
        # اگر فونت یافت نشد، از فونت پیش‌فرض استفاده کن
        return self.get_default_font(language, style)
    
    def get_default_font(self, language: str = "fa", style: FontStyle = FontStyle.NORMAL) -> str:
        """دریافت فونت پیش‌فرض برای زبان"""
        if language == "fa":
            # فونت پیش‌فرض فارسی
            default_fa_fonts = ["B Nazanin", "B Lotus", "B Mitra"]
            for font_family in default_fa_fonts:
                font_info = self.get_font(font_family, style, "fa")
                if font_info:
                    return font_info.pdf_name or f"/FA{self.next_font_id}"
        else:
            # فونت پیش‌فرض انگلیسی
            default_en_fonts = ["Helvetica", "Times", "Courier"]
            for font_family in default_en_fonts:
                font_info = self.get_font(font_family, style, "en")
                if font_info:
                    return font_info.pdf_name or f"/F{self.next_font_id}"
        
        # اگر هیچ فونتی یافت نشد، یک فونت استاندارد برگردان
        return "/Helvetica" if style == FontStyle.NORMAL else f"/Helvetica-{style.value.upper()}"
    
    def create_subset_for_text(self, text: str, language: str = "fa") -> Dict[str, bytes]:
        """ایجاد زیرمجموعه فونت‌ها برای متن داده شده"""
        subsets = {}
        
        # استخراج کاراکترهای منحصر به فرد
        unique_chars = set(text)
        
        # گروه‌بندی فونت‌ها بر اساس زبان
        target_language = language
        
        for font_key, font_info in self.fonts.items():
            if font_info.language == target_language and font_info.embedded:
                # ایجاد زیرمجموعه
                subset_data = font_info.create_subset(text)
                if subset_data:
                    subsets[font_key] = subset_data
        
        return subsets
    
    def embed_fonts_in_pdf(self, pdf_writer, used_fonts: List[str] = None) -> Dict[str, int]:
        """تعبیه فونت‌ها در PDF و برگرداندن مپ نام فونت به شماره آبجکت"""
        font_objects = {}
        
        # اگر لیست فونت‌های استفاده شده مشخص نشده، همه فونت‌های تعبیه‌شده را در نظر بگیر
        if used_fonts is None:
            used_fonts = [k for k, v in self.fonts.items() if v.embedded]
        
        for font_key in used_fonts:
            font_info = self.fonts.get(font_key)
            if not font_info or not font_info.embedded:
                continue
            
            # ایجاد آبجکت فونت در PDF
            font_obj_num = self._create_font_object(pdf_writer, font_info)
            if font_obj_num:
                font_objects[font_info.pdf_name] = font_obj_num
        
        return font_objects
    
    def _create_font_object(self, pdf_writer, font_info: FontInfo) -> Optional[int]:
        """ایجاد آبجکت فونت در PDF"""
        try:
            # دریافت داده‌های فونت
            font_data = font_info.get_font_data()
            if not font_data:
                return None
            
            # فشرده‌سازی داده‌های فونت
            compressed_data = zlib.compress(font_data)
            
            # ایجاد دیکشنری فونت
            font_dict = {
                'Type': '/Font',
                'Subtype': '/TrueType' if font_info.language == "en" else '/CIDFontType2',
                'BaseFont': f'/{font_info.name}',
                'Encoding': font_info.get_encoding_name(),
            }
            
            # برای فونت‌های فارسی (CID)
            if font_info.language == "fa":
                font_dict.update({
                    'Subtype': '/CIDFontType2',
                    'CIDSystemInfo': {
                        'Registry': '(Adobe)',
                        'Ordering': '(Farsi)',
                        'Supplement': 0
                    },
                    'FontDescriptor': self._create_font_descriptor(pdf_writer, font_info),
                    'DW': 1000,  # عرض پیش‌فرض
                    'W': self._create_width_array(font_info),  # آرایه عرض‌ها
                })
            
            # برای فونت‌های لاتین (TrueType)
            else:
                font_dict.update({
                    'Subtype': '/TrueType',
                    'FirstChar': 32,
                    'LastChar': 255,
                    'Widths': self._create_latin_widths_array(font_info),
                    'FontDescriptor': self._create_font_descriptor(pdf_writer, font_info),
                })
            
            # ایجاد استریم فونت
            font_stream = {
                'Type': '/FontDescriptor',
                'FontName': f'/{font_info.name}',
                'FontFamily': f'({font_info.family})',
                'Flags': font_info.metrics.flags,
                'FontBBox': list(font_info.metrics.font_bbox),
                'ItalicAngle': font_info.metrics.italic_angle,
                'Ascent': font_info.metrics.ascent,
                'Descent': font_info.metrics.descent,
                'CapHeight': font_info.metrics.cap_height,
                'StemV': font_info.metrics.stem_v,
                'StemH': font_info.metrics.stem_h,
                'AvgWidth': font_info.metrics.avg_width,
                'MaxWidth': font_info.metrics.max_width,
                'MissingWidth': font_info.metrics.missing_width,
            }
            
            # اگر فونت تعبیه شده است، داده‌های فونت را اضافه کن
            if font_info.embedded:
                font_stream['FontFile2'] = pdf_writer.create_stream(
                    compressed_data,
                    compress=True,
                    additional_entries={
                        'Length1': len(font_data),
                        'Length': len(compressed_data)
                    }
                )
            
            # ایجاد آبجکت فونت
            font_obj_num = pdf_writer.create_object(font_dict)
            
            # ذخیره شماره آبجکت
            font_info.object_number = font_obj_num
            
            return font_obj_num
            
        except Exception as e:
            warnings.warn(f"خطا در ایجاد آبجکت فونت {font_info.name}: {e}")
            return None
    
    def _create_font_descriptor(self, pdf_writer, font_info: FontInfo) -> Dict:
        """ایجاد دیکشنری توصیف‌کننده فونت"""
        return {
            'Type': '/FontDescriptor',
            'FontName': f'/{font_info.name}',
            'FontFamily': f'({font_info.family})',
            'Flags': font_info.metrics.flags,
            'FontBBox': list(font_info.metrics.font_bbox),
            'ItalicAngle': font_info.metrics.italic_angle,
            'Ascent': font_info.metrics.ascent,
            'Descent': font_info.metrics.descent,
            'CapHeight': font_info.metrics.cap_height,
            'StemV': font_info.metrics.stem_v,
            'StemH': font_info.metrics.stem_h,
            'AvgWidth': font_info.metrics.avg_width,
            'MaxWidth': font_info.metrics.max_width,
            'MissingWidth': font_info.metrics.missing_width,
        }
    
    def _create_width_array(self, font_info: FontInfo) -> List:
        """ایجاد آرایه عرض برای فونت‌های فارسی (CID)"""
        # این یک پیاده‌سازی ساده است
        # در پیاده‌سازی واقعی باید عرض واقعی گلیف‌ها محاسبه شود
        widths = []
        
        # برای فونت‌های فارسی، عرض پیش‌فرض 1000 واحد است
        # این می‌تواند بر اساس متریک‌های واقعی فونت تنظیم شود
        if font_info.metrics.glyph_widths:
            # استفاده از عرض‌های واقعی اگر موجود باشد
            for glyph_id, width in font_info.metrics.glyph_widths.items():
                if isinstance(glyph_id, int) and 0 <= glyph_id < 65536:
                    widths.append([glyph_id, glyph_id, width])
        else:
            # استفاده از عرض پیش‌فرض
            widths.append([0, 65535, 1000])
        
        return widths
    
    def _create_latin_widths_array(self, font_info: FontInfo) -> List:
        """ایجاد آرایه عرض برای فونت‌های لاتین"""
        widths = []
        
        # عرض پیش‌فرض برای کاراکترهای ASCII
        for i in range(32, 256):
            if font_info.metrics.glyph_widths and i in font_info.metrics.glyph_widths:
                widths.append(font_info.metrics.glyph_widths[i])
            else:
                widths.append(600)  # عرض پیش‌فرض
        
        return widths
    
    def get_font_resources_dict(self) -> Dict:
        """دریافت دیکشنری منابع فونت برای PDF"""
        resources = {'Font': {}}
        
        for font_key, font_info in self.fonts.items():
            if font_info.pdf_name:
                # فقط فونت‌هایی که در PDF استفاده می‌شوند
                font_ref = f"{font_info.object_number} 0 R" if font_info.object_number else font_info.pdf_name
                resources['Font'][font_info.pdf_name[1:]] = font_ref
        
        return resources
    
    def analyze_text_font_requirements(self, text: str) -> Dict:
        """تحلیل نیازهای فونت برای متن داده شده"""
        result = {
            'languages': set(),
            'characters': set(),
            'unicode_ranges': set(),
            'font_families_needed': set(),
            'recommended_fonts': []
        }
        
        # تحلیل کاراکترها
        for char in text:
            code_point = ord(char)
            result['characters'].add(char)
            
            # تشخیص زبان
            if 0x0600 <= code_point <= 0x06FF:  # محدوده عربی/فارسی
                result['languages'].add('fa')
                result['unicode_ranges'].add('Arabic')
            elif 0x0750 <= code_point <= 0x077F:  # عربی افزوده
                result['languages'].add('fa')
                result['unicode_ranges'].add('Arabic Extended')
            elif 0x08A0 <= code_point <= 0x08FF:  # عربی افزوده-الف
                result['languages'].add('fa')
                result['unicode_ranges'].add('Arabic Extended-A')
            elif 0xFB50 <= code_point <= 0xFDFF:  # صورت‌های ارائه عربی-الف
                result['languages'].add('fa')
                result['unicode_ranges'].add('Arabic Presentation Forms-A')
            elif 0xFE70 <= code_point <= 0xFEFF:  # صورت‌های ارائه عربی-ب
                result['languages'].add('fa')
                result['unicode_ranges'].add('Arabic Presentation Forms-B')
            elif 0x0000 <= code_point <= 0x007F:  # ASCII پایه
                result['languages'].add('en')
                result['unicode_ranges'].add('Basic Latin')
            elif 0x0080 <= code_point <= 0x00FF:  # Latin-1 تکمیلی
                result['languages'].add('en')
                result['unicode_ranges'].add('Latin-1 Supplement')
            elif 0x0100 <= code_point <= 0x017F:  # Latin Extended-A
                result['languages'].add('en')
                result['unicode_ranges'].add('Latin Extended-A')
        
        # پیشنهاد فونت‌ها
        if 'fa' in result['languages']:
            result['font_families_needed'].add('persian')
            result['recommended_fonts'].extend([
                {'family': 'B Nazanin', 'style': 'normal', 'language': 'fa'},
                {'family': 'B Lotus', 'style': 'normal', 'language': 'fa'},
                {'family': 'B Mitra', 'style': 'normal', 'language': 'fa'},
            ])
        
        if 'en' in result['languages']:
            result['font_families_needed'].add('latin')
            result['recommended_fonts'].extend([
                {'family': 'Helvetica', 'style': 'normal', 'language': 'en'},
                {'family': 'Times', 'style': 'normal', 'language': 'en'},
                {'family': 'Courier', 'style': 'normal', 'language': 'en'},
            ])
        
        # تبدیل set به list برای JSON serialization
        result['languages'] = list(result['languages'])
        result['characters'] = list(result['characters'])
        result['unicode_ranges'] = list(result['unicode_ranges'])
        result['font_families_needed'] = list(result['font_families_needed'])
        
        return result
    
    def optimize_fonts(self, min_usage_percentage: float = 0.1) -> Dict[str, List[str]]:
        """بهینه‌سازی فونت‌ها با حذف فونت‌های کم استفاده"""
        optimization_result = {
            'removed': [],
            'kept': [],
            'merged': []
        }
        
        # اینجا می‌توان منطق پیچیده‌تری برای بهینه‌سازی اضافه کرد
        # مثلاً ادغام فونت‌های مشابه یا حذف فونت‌های تکراری
        
        return optimization_result
    
    def get_statistics(self) -> Dict:
        """دریافت آمار فونت‌ها"""
        stats = {
            'total_fonts': len(self.fonts),
            'embedded_fonts': sum(1 for f in self.fonts.values() if f.embedded),
            'subset_fonts': sum(1 for f in self.fonts.values() if f.subset),
            'persian_fonts': sum(1 for f in self.fonts.values() if f.language == 'fa'),
            'latin_fonts': sum(1 for f in self.fonts.values() if f.language == 'en'),
            'by_family': {},
            'by_style': {},
            'by_language': {},
            'total_size_bytes': 0,
            'embedded_size_bytes': 0,
            'subset_size_bytes': 0,
            'font_details': []
        }
        
        # محاسبه آمار بر اساس خانواده
        for font_info in self.fonts.values():
            # آمار خانواده
            family = font_info.family
            if family not in stats['by_family']:
                stats['by_family'][family] = 0
            stats['by_family'][family] += 1
            
            # آمار استایل
            style = font_info.style.value
            if style not in stats['by_style']:
                stats['by_style'][style] = 0
            stats['by_style'][style] += 1
            
            # آمار زبان
            lang = font_info.language
            if lang not in stats['by_language']:
                stats['by_language'][lang] = 0
            stats['by_language'][lang] += 1
            
            # محاسبه حجم
            font_data = font_info.get_font_data()
            if font_data:
                font_size = len(font_data)
                stats['total_size_bytes'] += font_size
                
                if font_info.embedded:
                    stats['embedded_size_bytes'] += font_size
                
                if font_info.subset:
                    stats['subset_size_bytes'] += font_size
            
            # جزئیات فونت
            font_detail = {
                'name': font_info.name,
                'family': font_info.family,
                'style': font_info.style.value,
                'language': font_info.language,
                'embedded': font_info.embedded,
                'subset': font_info.subset,
                'encoding': font_info.encoding.value,
                'pdf_name': font_info.pdf_name,
                'object_number': font_info.object_number,
                'file_size': font_info.file_size,
                'checksum': font_info.checksum[:8] if font_info.checksum else None,
                'metrics': {
                    'ascent': font_info.metrics.ascent,
                    'descent': font_info.metrics.descent,
                    'cap_height': font_info.metrics.cap_height,
                    'x_height': font_info.metrics.x_height,
                    'italic_angle': font_info.metrics.italic_angle,
                    'font_bbox': font_info.metrics.font_bbox
                }
            }
            stats['font_details'].append(font_detail)
        
        # تبدیل حجم به فرمت خوانا
        stats['total_size_mb'] = stats['total_size_bytes'] / (1024 * 1024)
        stats['embedded_size_mb'] = stats['embedded_size_bytes'] / (1024 * 1024)
        stats['subset_size_mb'] = stats['subset_size_bytes'] / (1024 * 1024)
        
        # محاسبه درصدها
        if stats['total_fonts'] > 0:
            stats['embedded_percentage'] = (stats['embedded_fonts'] / stats['total_fonts']) * 100
            stats['subset_percentage'] = (stats['subset_fonts'] / stats['total_fonts']) * 100
            stats['persian_percentage'] = (stats['persian_fonts'] / stats['total_fonts']) * 100
            stats['latin_percentage'] = (stats['latin_fonts'] / stats['total_fonts']) * 100
        else:
            stats['embedded_percentage'] = 0
            stats['subset_percentage'] = 0
            stats['persian_percentage'] = 0
            stats['latin_percentage'] = 0
        
        # مرتب‌سازی
        stats['by_family'] = dict(sorted(stats['by_family'].items(), key=lambda x: x[1], reverse=True))
        stats['by_style'] = dict(sorted(stats['by_style'].items(), key=lambda x: x[1], reverse=True))
        stats['by_language'] = dict(sorted(stats['by_language'].items(), key=lambda x: x[1], reverse=True))
        
        return stats
    
    def export_font_info(self, output_format: str = 'json') -> Union[Dict, str]:
        """صدور اطلاعات فونت‌ها در فرمت‌های مختلف"""
        stats = self.get_statistics()
        
        if output_format.lower() == 'json':
            import json
            return json.dumps(stats, indent=2, ensure_ascii=False)
        
        elif output_format.lower() == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # هدر
            writer.writerow([
                'Name', 'Family', 'Style', 'Language', 'Embedded', 'Subset',
                'Encoding', 'PDF Name', 'Object #', 'File Size (KB)', 'Checksum'
            ])
            
            # داده‌ها
            for font in stats['font_details']:
                writer.writerow([
                    font['name'],
                    font['family'],
                    font['style'],
                    font['language'],
                    'Yes' if font['embedded'] else 'No',
                    'Yes' if font['subset'] else 'No',
                    font['encoding'],
                    font['pdf_name'],
                    font['object_number'] or 'N/A',
                    f"{font['file_size'] / 1024:.2f}",
                    font['checksum'] or 'N/A'
                ])
            
            # خلاصه
            writer.writerow([])
            writer.writerow(['SUMMARY'])
            writer.writerow(['Total Fonts', stats['total_fonts']])
            writer.writerow(['Embedded Fonts', f"{stats['embedded_fonts']} ({stats['embedded_percentage']:.1f}%)"])
            writer.writerow(['Subset Fonts', f"{stats['subset_fonts']} ({stats['subset_percentage']:.1f}%)"])
            writer.writerow(['Persian Fonts', f"{stats['persian_fonts']} ({stats['persian_percentage']:.1f}%)"])
            writer.writerow(['Latin Fonts', f"{stats['latin_fonts']} ({stats['latin_percentage']:.1f}%)"])
            writer.writerow(['Total Size', f"{stats['total_size_mb']:.2f} MB"])
            writer.writerow(['Embedded Size', f"{stats['embedded_size_mb']:.2f} MB"])
            writer.writerow(['Subset Size', f"{stats['subset_size_mb']:.2f} MB"])
            
            return output.getvalue()
        
        elif output_format.lower() == 'html':
            html = """
            <!DOCTYPE html>
            <html lang="fa">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Font Manager Report</title>
                <style>
                    body { font-family: 'B Nazanin', Tahoma, sans-serif; direction: rtl; margin: 20px; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 30px; }
                    .stat-card { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; text-align: center; }
                    .stat-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
                    .stat-label { color: #6c757d; margin-top: 5px; }
                    .table-container { overflow-x: auto; margin-bottom: 30px; }
                    table { width: 100%; border-collapse: collapse; }
                    th { background: #2c3e50; color: white; padding: 12px; text-align: right; }
                    td { padding: 10px; border-bottom: 1px solid #dee2e6; text-align: right; }
                    tr:nth-child(even) { background: #f8f9fa; }
                    .badge { display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 12px; }
                    .badge-success { background: #28a745; color: white; }
                    .badge-warning { background: #ffc107; color: #212529; }
                    .badge-info { background: #17a2b8; color: white; }
                    .chart-container { margin: 30px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>گزارش مدیریت فونت‌های PDF</h1>
                        <p>تاریخ تولید: """ + self._get_current_date() + """</p>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">""" + str(stats['total_fonts']) + """</div>
                            <div class="stat-label">تعداد کل فونت‌ها</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">""" + f"{stats['embedded_fonts']} ({stats['embedded_percentage']:.1f}%)" + """</div>
                            <div class="stat-label">فونت‌های تعبیه شده</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">""" + f"{stats['subset_fonts']} ({stats['subset_percentage']:.1f}%)" + """</div>
                            <div class="stat-label">فونت‌های زیرمجموعه</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">""" + f"{stats['persian_fonts']} ({stats['persian_percentage']:.1f}%)" + """</div>
                            <div class="stat-label">فونت‌های فارسی</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">""" + f"{stats['total_size_mb']:.2f} MB" + """</div>
                            <div class="stat-label">حجم کل فونت‌ها</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">""" + f"{stats['embedded_size_mb']:.2f} MB" + """</div>
                            <div class="stat-label">حجم فونت‌های تعبیه شده</div>
                        </div>
                    </div>
                    
                    <h2>جزئیات فونت‌ها</h2>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>نام فونت</th>
                                    <th>خانواده</th>
                                    <th>استایل</th>
                                    <th>زبان</th>
                                    <th>تعبیه شده</th>
                                    <th>زیرمجموعه</th>
                                    <th>انکودینگ</th>
                                    <th>نام در PDF</th>
                                    <th>حجم (KB)</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for font in stats['font_details']:
                embedded_badge = '<span class="badge badge-success">بله</span>' if font['embedded'] else '<span class="badge badge-warning">خیر</span>'
                subset_badge = '<span class="badge badge-info">بله</span>' if font['subset'] else ''
                lang_badge = '<span class="badge badge-success">فارسی</span>' if font['language'] == 'fa' else '<span class="badge badge-info">انگلیسی</span>'
                
                html += f"""
                                <tr>
                                    <td>{font['name']}</td>
                                    <td>{font['family']}</td>
                                    <td>{font['style']}</td>
                                    <td>{lang_badge}</td>
                                    <td>{embedded_badge}</td>
                                    <td>{subset_badge}</td>
                                    <td>{font['encoding']}</td>
                                    <td>{font['pdf_name']}</td>
                                    <td>{font['file_size'] / 1024:.2f}</td>
                                </tr>
                """
            
            html += """
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="chart-container">
                        <h2>توزیع فونت‌ها بر اساس خانواده</h2>
                        <div style="height: 300px; background: #f8f9fa; padding: 20px; border-radius: 5px;">
                            <!-- در اینجا می‌توان نمودار اضافه کرد -->
                            <p style="text-align: center; color: #6c757d; margin-top: 100px;">
                                نمودار توزیع فونت‌ها (قابل پیاده‌سازی با کتابخانه‌های نمودار)
                            </p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html
        
        else:
            # خروجی متنی ساده
            output = []
            output.append("=" * 80)
            output.append("گزارش مدیریت فونت‌های PDF")
            output.append("=" * 80)
            output.append(f"تاریخ: {self._get_current_date()}")
            output.append(f"تعداد کل فونت‌ها: {stats['total_fonts']}")
            output.append(f"فونت‌های تعبیه شده: {stats['embedded_fonts']} ({stats['embedded_percentage']:.1f}%)")
            output.append(f"فونت‌های زیرمجموعه: {stats['subset_fonts']} ({stats['subset_percentage']:.1f}%)")
            output.append(f"فونت‌های فارسی: {stats['persian_fonts']} ({stats['persian_percentage']:.1f}%)")
            output.append(f"فونت‌های انگلیسی: {stats['latin_fonts']} ({stats['latin_percentage']:.1f}%)")
            output.append(f"حجم کل: {stats['total_size_mb']:.2f} MB")
            output.append(f"حجم تعبیه شده: {stats['embedded_size_mb']:.2f} MB")
            output.append(f"حجم زیرمجموعه: {stats['subset_size_mb']:.2f} MB")
            output.append("")
            output.append("توزیع بر اساس خانواده:")
            for family, count in stats['by_family'].items():
                output.append(f"  {family}: {count}")
            output.append("")
            output.append("توزیع بر اساس استایل:")
            for style, count in stats['by_style'].items():
                output.append(f"  {style}: {count}")
            output.append("")
            output.append("توزیع بر اساس زبان:")
            for lang, count in stats['by_language'].items():
                output.append(f"  {lang}: {count}")
            output.append("")
            output.append("=" * 80)
            output.append("جزئیات فونت‌ها:")
            output.append("=" * 80)
            
            for font in stats['font_details']:
                output.append(f"نام: {font['name']}")
                output.append(f"  خانواده: {font['family']}")
                output.append(f"  استایل: {font['style']}")
                output.append(f"  زبان: {font['language']}")
                output.append(f"  تعبیه شده: {'بله' if font['embedded'] else 'خیر'}")
                output.append(f"  زیرمجموعه: {'بله' if font['subset'] else 'خیر'}")
                output.append(f"  انکودینگ: {font['encoding']}")
                output.append(f"  نام PDF: {font['pdf_name']}")
                output.append(f"  شماره آبجکت: {font['object_number'] or 'N/A'}")
                output.append(f"  حجم: {font['file_size'] / 1024:.2f} KB")
                output.append(f"  چکسام: {font['checksum'] or 'N/A'}")
                output.append("-" * 40)
            
            return "\n".join(output)
    
    def _get_current_date(self) -> str:
        """دریافت تاریخ جاری به صورت رشته"""
        from datetime import datetime
        now = datetime.now()
        return now.strftime("%Y/%m/%d %H:%M:%S")
    
    def clear_cache(self):
        """پاک کردن کش فونت‌ها"""
        self._font_cache.clear()
    
    def reset(self):
        """بازنشانی مدیر فونت به حالت اولیه"""
        self.fonts.clear()
        self.font_mapping.clear()
        self._font_cache.clear()
        self.next_font_id = 1
        self._register_standard_fonts()
    
    def find_font_by_checksum(self, checksum: str) -> Optional[FontInfo]:
        """یافتن فونت بر اساس چکسام"""
        for font_info in self.fonts.values():
            if font_info.checksum == checksum:
                return font_info
        return None
    
    def find_font_by_name(self, name: str) -> List[FontInfo]:
        """یافتن فونت‌ها بر اساس نام"""
        results = []
        for font_info in self.fonts.values():
            if name.lower() in font_info.name.lower() or name.lower() in font_info.family.lower():
                results.append(font_info)
        return results
    
    def get_font_list(self, language: Optional[str] = None, 
                     embedded_only: bool = False,
                     subset_only: bool = False) -> List[Dict]:
        """دریافت لیست فونت‌ها با فیلترهای مختلف"""
        font_list = []
        
        for font_key, font_info in self.fonts.items():
            # اعمال فیلترها
            if language and font_info.language != language:
                continue
            if embedded_only and not font_info.embedded:
                continue
            if subset_only and not font_info.subset:
                continue
            
            font_list.append({
                'key': font_key,
                'name': font_info.name,
                'family': font_info.family,
                'style': font_info.style.value,
                'language': font_info.language,
                'embedded': font_info.embedded,
                'subset': font_info.subset,
                'encoding': font_info.encoding.value,
                'pdf_name': font_info.pdf_name,
                'object_number': font_info.object_number,
                'file_size': font_info.file_size,
                'checksum': font_info.checksum,
                'file_path': font_info.file_path
            })
        
        # مرتب‌سازی بر اساس نام خانواده
        font_list.sort(key=lambda x: (x['family'], x['name']))
        
        return font_list
    
    def validate_fonts(self) -> Dict[str, List[str]]:
        """اعتبارسنجی فونت‌های ثبت شده"""
        validation_results = {
            'valid': [],
            'invalid': [],
            'warnings': [],
            'errors': []
        }
        
        for font_key, font_info in self.fonts.items():
            try:
                # بررسی وجود داده‌های فونت
                if not font_info.ttf_data and font_info.embedded:
                    validation_results['errors'].append(f"فونت {font_info.name} تعبیه شده است اما داده‌ای ندارد")
                    validation_results['invalid'].append(font_key)
                    continue
                
                # بررسی اندازه فونت
                if font_info.ttf_data and len(font_info.ttf_data) < 1024:
                    validation_results['warnings'].append(f"فونت {font_info.name} اندازه غیرعادی کوچکی دارد")
                
                # بررسی نام فونت
                if not font_info.name or len(font_info.name.strip()) == 0:
                    validation_results['errors'].append(f"فونت {font_key} نام معتبری ندارد")
                    validation_results['invalid'].append(font_key)
                    continue
                
                # بررسی خانواده فونت
                if not font_info.family or len(font_info.family.strip()) == 0:
                    validation_results['warnings'].append(f"فونت {font_info.name} خانواده معتبری ندارد")
                
                # بررسی متریک‌ها
                if font_info.metrics.ascent == 0 and font_info.metrics.descent == 0:
                    validation_results['warnings'].append(f"فونت {font_info.name} متریک‌های معتبری ندارد")
                
                # بررسی انکودینگ برای فونت‌های فارسی
                if font_info.language == 'fa' and font_info.encoding != FontEncoding.IDENTITY_H:
                    validation_results['warnings'].append(f"فونت فارسی {font_info.name} از انکودینگ {font_info.encoding.value} استفاده می‌کند. پیشنهاد: Identity-H")
                
                validation_results['valid'].append(font_key)
                
            except Exception as e:
                validation_results['errors'].append(f"خطا در اعتبارسنجی فونت {font_key}: {str(e)}")
                validation_results['invalid'].append(font_key)
        
        return validation_results
    
    def optimize_font_usage(self, text_content: str, max_fonts: int = 5) -> List[str]:
        """بهینه‌سازی استفاده از فونت‌ها بر اساس محتوای متن"""
        # تحلیل نیازهای فونت
        requirements = self.analyze_text_font_requirements(text_content)
        
        # انتخاب فونت‌های بهینه
        optimal_fonts = []
        
        # اولویت‌بندی فونت‌های فارسی
        if 'fa' in requirements['languages']:
            persian_fonts = self.get_font_list(language='fa', embedded_only=True)
            if persian_fonts:
                # انتخاب فونت‌های فارسی بر اساس محبوبیت و سازگاری
                preferred_persian = ['B Nazanin', 'B Lotus', 'B Mitra', 'B Traffic', 'B Yekan']
                for font_family in preferred_persian:
                    for font in persian_fonts:
                        if font['family'] == font_family and font['style'] == 'normal':
                            optimal_fonts.append(font['key'])
                            break
                    if len(optimal_fonts) >= max_fonts // 2:
                        break
        
        # فونت‌های انگلیسی
        if 'en' in requirements['languages']:
            latin_fonts = self.get_font_list(language='en')
            if latin_fonts:
                # انتخاب فونت‌های استاندارد
                preferred_latin = ['Helvetica', 'Times', 'Courier']
                for font_family in preferred_latin:
                    for font in latin_fonts:
                        if font['family'] == font_family and font['style'] == 'normal':
                            optimal_fonts.append(font['key'])
                            break
                    if len(optimal_fonts) >= max_fonts:
                        break
        
        # اگر فونتی انتخاب نشد، از فونت پیش‌فرض استفاده کن
        if not optimal_fonts:
            optimal_fonts.append(self.get_default_font('fa' if 'fa' in requirements['languages'] else 'en'))
        
        return optimal_fonts
    
    def create_font_subset_report(self, text: str) -> Dict:
        """ایجاد گزارش زیرمجموعه فونت برای متن داده شده"""
        report = {
            'text_length': len(text),
            'unique_characters': len(set(text)),
            'languages_detected': [],
            'font_subsets': {},
            'size_reduction': {},
            'recommendations': []
        }
        
        # تشخیص زبان‌ها
        requirements = self.analyze_text_font_requirements(text)
        report['languages_detected'] = requirements['languages']
        
        # ایجاد زیرمجموعه برای هر فونت
        for font_key, font_info in self.fonts.items():
            if font_info.embedded and font_info.language in requirements['languages']:
                original_size = len(font_info.ttf_data) if font_info.ttf_data else 0
                
                # ایجاد زیرمجموعه
                subset_data = font_info.create_subset(text)
                subset_size = len(subset_data) if subset_data else 0
                
                if original_size > 0 and subset_size > 0:
                    reduction_percentage = ((original_size - subset_size) / original_size) * 100
                    
                    report['font_subsets'][font_key] = {
                        'font_name': font_info.name,
                        'original_size_kb': original_size / 1024,
                        'subset_size_kb': subset_size / 1024,
                        'reduction_kb': (original_size - subset_size) / 1024,
                        'reduction_percentage': reduction_percentage,
                        'used_glyphs_count': len(font_info.used_glyphs) if font_info.used_glyphs else 0
                    }
                    
                    # توصیه‌ها
                    if reduction_percentage > 70:
                        report['recommendations'].append(
                            f"فونت {font_info.name}: کاهش حجم {reduction_percentage:.1f}% - استفاده از زیرمجموعه بسیار موثر است"
                        )
                    elif reduction_percentage > 30:
                        report['recommendations'].append(
                            f"فونت {font_info.name}: کاهش حجم {reduction_percentage:.1f}% - استفاده از زیرمجموعه توصیه می‌شود"
                        )
                    else:
                        report['recommendations'].append(
                            f"فونت {font_info.name}: کاهش حجم {reduction_percentage:.1f}% - زیرمجموعه‌سازی تاثیر کمی دارد"
                        )
        
        # محاسبه کاهش حجم کلی
        total_original = sum(info['original_size_kb'] for info in report['font_subsets'].values())
        total_subset = sum(info['subset_size_kb'] for info in report['font_subsets'].values())
        
        if total_original > 0:
            total_reduction = ((total_original - total_subset) / total_original) * 100
            report['size_reduction'] = {
                'total_original_kb': total_original,
                'total_subset_kb': total_subset,
                'total_reduction_kb': total_original - total_subset,
                'total_reduction_percentage': total_reduction
            }
        
        return report

