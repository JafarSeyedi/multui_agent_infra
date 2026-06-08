"""
font_handler.py - Managing Persian fonts in PDF

This module is responsible for extracting, analyzing, and managing Persian fonts in PDF files.
"""
import hashlib
import logging
import re
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any

# Logging settings
logger = logging.getLogger(__name__)


class FontType(Enum):
    """PDF font types"""
    TYPE0 = "Type0"  # Composite font
    TYPE1 = "Type1"  # Type1
    TYPE3 = "Type3"  # Type3
    TRUETYPE = "TrueType"
    CIDFONT_TYPE0 = "CIDFontType0"
    CIDFONT_TYPE2 = "CIDFontType2"
    OPENTYPE = "OpenType"
    UNKNOWN = "Unknown"


class FontEncoding(Enum):
    """Font encoding types"""
    STANDARD = "StandardEncoding"
    WIN_ANSI = "WinAnsiEncoding"
    MAC_ROMAN = "MacRomanEncoding"
    PDF_DOC = "PDFDocEncoding"
    IDENTITY_H = "Identity-H"
    IDENTITY_V = "Identity-V"
    CUSTOM = "Custom"
    UNKNOWN = "Unknown"


class FontLanguage(Enum):
    """Font languages"""
    FARSI = "Farsi"
    ARABIC = "Arabic"
    ENGLISH = "English"
    MULTILINGUAL = "Multilingual"
    UNKNOWN = "Unknown"


@dataclass
class FontDescriptor:
    """Font descriptor data"""
    font_name: str = ""
    base_font: str = ""
    font_family: str = ""
    font_stretch: str = ""
    font_weight: int = 400
    italic_angle: float = 0.0
    ascent: float = 0.0
    descent: float = 0.0
    cap_height: float = 0.0
    x_height: float = 0.0
    stem_v: float = 0.0
    stem_h: float = 0.0
    avg_width: float = 0.0
    max_width: float = 0.0
    missing_width: float = 0.0
    flags: int = 0
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    char_set: str = ""
    font_file: bytes | None = None
    font_file_length: int = 0
    font_file_type: str = ""
    font_file_subtype: str = ""


@dataclass
class FontInfo:
    """Complete font information"""
    # Font ID
    font_id: str = ""
    font_name: str = ""
    base_font: str = ""

    # Font type
    font_type: FontType = FontType.UNKNOWN
    subtype: str = ""

    # encoding
    encoding: FontEncoding = FontEncoding.UNKNOWN
    to_unicode_cmap: bytes | None = None
    cid_system_info: dict[str, str] | None = None
    has_to_unicode: bool = False
    has_cid_system_info: bool = False

    # Technical information
    descriptor: FontDescriptor | None = None
    first_char: int = 0
    last_char: int = 255
    widths: list[float] = field(default_factory=list)

    # Language information
    language: FontLanguage = FontLanguage.UNKNOWN
    supports_farsi: bool = False
    supports_arabic: bool = False
    supports_english: bool = False

    # Embedded information
    is_embedded: bool = False
    embedded_data: bytes | None = None
    embedded_data_type: str = ""

    # Usage information
    used_in_pages: list[int] = field(default_factory=list)
    char_count: int = 0
    is_subset: bool = False

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FontAnalysisResult:
    """Font analysis results"""
    # Font list
    fonts: list[FontInfo] = field(default_factory=list)

    # Overall Statistics
    total_fonts: int = 0
    embedded_fonts: int = 0
    subset_fonts: int = 0
    farsi_fonts: int = 0
    arabic_fonts: int = 0

    # Persian fonts
    farsi_font_list: list[FontInfo] = field(default_factory=list)

    # Font problems
    font_problems: list[dict[str, Any]] = field(default_factory=list)

    # Suggestions
    suggestions: list[str] = field(default_factory=list)

    # Technical information
    has_to_unicode: bool = False
    has_cid_system_info: bool = False
    encoding_issues: list[str] = field(default_factory=list)


class FontHandler:
    """Main class for managing Persian fonts"""

    def __init__(self, pdf_parser=None) -> None:
        """
        Initialize
        
        Args:
            pdf_parser: PDFParser instance (optional)
        """
        self.pdf_parser = pdf_parser
        self.font_cache: dict[str, FontInfo] = {}
        self.character_maps: dict[str, dict[int, str]] = {}

        # Mapping tables for Persian fonts
        self._init_farsi_mappings()

    def _init_farsi_mappings(self):
        """Initialize Persian mapping tables"""
        # Common Persian code conversion table
        self.farsi_code_pages = {
            # Windows-1256 Arabic
            'windows-1256': {
                0xC1: 'آ', 0xC2: 'أ', 0xC3: 'ؤ', 0xC4: 'إ', 0xC5: 'ئ',
                0xC6: 'ا', 0xC7: 'ب', 0xC8: 'ة', 0xC9: 'ت', 0xCA: 'ث',
                0xCB: 'ج', 0xCC: 'ح', 0xCD: 'خ', 0xCE: 'د', 0xCF: 'ذ',
                0xD0: 'ر', 0xD1: 'ز', 0xD2: 'س', 0xD3: 'ش', 0xD4: 'ص',
                0xD5: 'ض', 0xD6: 'ط', 0xD7: 'ظ', 0xD8: 'ع', 0xD9: 'غ',
                0xDA: 'ف', 0xDB: 'ق', 0xDC: 'ک', 0xDD: 'ل', 0xDE: 'م',
                0xDF: 'ن', 0xE0: 'ه', 0xE1: 'و', 0xE2: 'ی', 0xE3: 'ي',
                0xE4: 'ً', 0xE5: 'ٌ', 0xE6: 'ٍ', 0xE7: 'َ', 0xE8: 'ُ',
                0xE9: 'ِ', 0xEA: 'ّ', 0xEB: 'ْ', 0xEC: 'پ', 0xED: 'چ',
                0xEE: 'ژ', 0xEF: 'گ'
            },

            # Mac Farsi
            'mac-farsi': {
                0x80: 'آ', 0x81: 'أ', 0x82: 'ؤ', 0x83: 'إ', 0x84: 'ئ',
                0x85: 'ا', 0x86: 'ب', 0x87: 'ة', 0x88: 'ت', 0x89: 'ث',
                0x8A: 'ج', 0x8B: 'ح', 0x8C: 'خ', 0x8D: 'د', 0x8E: 'ذ',
                0x8F: 'ر', 0x90: 'ز', 0x91: 'س', 0x92: 'ش', 0x93: 'ص',
                0x94: 'ض', 0x95: 'ط', 0x96: 'ظ', 0x97: 'ع', 0x98: 'غ',
                0x99: 'ف', 0x9A: 'ق', 0x9B: 'ک', 0x9C: 'ل', 0x9D: 'م',
                0x9E: 'ن', 0x9F: 'ه', 0xA0: 'و', 0xA1: 'ی', 0xA2: 'ي',
                0xA3: 'ً', 0xA4: 'ٌ', 0xA5: 'ٍ', 0xA6: 'َ', 0xA7: 'ُ',
                0xA8: 'ِ', 0xA9: 'ّ', 0xAA: 'ْ', 0xAB: 'پ', 0xAC: 'چ',
                0xAD: 'ژ', 0xAE: 'گ'
            },

            # ISO-8859-6 Arabic
            'iso-8859-6': {
                0xC1: 'آ', 0xC2: 'أ', 0xC3: 'ؤ', 0xC4: 'إ', 0xC5: 'ئ',
                0xC6: 'ا', 0xC7: 'ب', 0xC8: 'ة', 0xC9: 'ت', 0xCA: 'ث',
                0xCB: 'ج', 0xCC: 'ح', 0xCD: 'خ', 0xCE: 'د', 0xCF: 'ذ',
                0xD0: 'ر', 0xD1: 'ز', 0xD2: 'س', 0xD3: 'ش', 0xD4: 'ص',
                0xD5: 'ض', 0xD6: 'ط', 0xD7: 'ظ', 0xD8: 'ع', 0xD9: 'غ',
                0xDA: 'ف', 0xDB: 'ق', 0xDC: 'ک', 0xDD: 'ل', 0xDE: 'م',
                0xDF: 'ن', 0xE0: 'ه', 0xE1: 'و', 0xE2: 'ی', 0xE3: 'ي',
                0xE4: 'ً', 0xE5: 'ٌ', 0xE6: 'ٍ', 0xE7: 'َ', 0xE8: 'ُ',
                0xE9: 'ِ', 0xEA: 'ّ', 0xEB: 'ْ', 0xEC: 'پ', 0xED: 'چ',
                0xEE: 'ژ', 0xEF: 'گ'
            }
        }

        # Persian character list
        self.farsi_chars = {
            'آ', 'أ', 'ؤ', 'إ', 'ئ', 'ا', 'ب', 'ة', 'ت', 'ث',
            'ج', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص',
            'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ک', 'ل', 'م',
            'ن', 'ه', 'و', 'ی', 'ي', 'ً', 'ٌ', 'ٍ', 'َ', 'ُ',
            'ِ', 'ّ', 'ْ', 'پ', 'چ', 'ژ', 'گ', '۰', '۱', '۲',
            '۳', '۴', '۵', '۶', '۷', '۸', '۹'
        }

        # Arabic character list
        self.arabic_chars = {
            'آ', 'أ', 'ؤ', 'إ', 'ئ', 'ا', 'ب', 'ة', 'ت', 'ث',
            'ج', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص',
            'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م',
            'ن', 'ه', 'و', 'ي', 'ى', 'ً', 'ٌ', 'ٍ', 'َ', 'ُ',
            'ِ', 'ّ', 'ْ'
        }

        # Common Persian font names
        self.farsi_font_names = {
            'B Nazanin', 'B Titr', 'B Yekan', 'B Zar', 'B Badr',
            'B Compset', 'B Elham', 'B Farnaz', 'B Homa', 'B Koodak',
            'B Lotus', 'B Mitra', 'B Morvarid', 'B Roya', 'B Setareh',
            'B Shabnam', 'B Tabassom', 'B Traffic', 'B Yas', 'IranNastaliq',
            'Iranian Sans', 'Iranian Serif', 'Tahoma', 'Times New Roman',
            'Arial', 'DejaVu Sans', 'Scheherazade', 'Lateef', 'Amiri'
        }

    def extract_fonts_from_pdf(self, pdf_path: str) -> FontAnalysisResult:
        """
        Extract and analyze PDF fonts
        
        Args:
            pdf_path: PDF file path
            
        Returns:
            FontAnalysisResult: Font analysis results
        """
        logger.info(f"Extracting fonts from file: {pdf_path}")

        result = FontAnalysisResult()

        try:
            # Using PyPDF2 for font extraction
            import PyPDF2

            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract fonts from each page
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        self._extract_fonts_from_page(page, page_num, result)
                    except Exception as e:
                        logger.warning(f"خطا در استخراج فونت‌های صفحه {page_num}: {str(e)}")

                # Analyze extracted fonts
                self._analyze_extracted_fonts(result)

        except ImportError:
            logger.error("PyPDF2 not installed. Using fallback method")
            self._extract_fonts_fallback(pdf_path, result)
        except Exception as e:
            logger.error(f"Error extracting fonts: {str(e)}")
            result.font_problems.append({
                "type": "extraction_error",
                "message": f"Error extracting fonts: {str(e)}"
            })

        return result

    def _extract_fonts_from_page(self, page, page_num: int, result: FontAnalysisResult):
        """
        Extract fonts from a page
        
        Args:
            page: PDF page
            page_num: page number
            result: Results object
        """
        try:
            # Extract page resources
            if hasattr(page, 'resources') and page.resources:
                resources = page.resources

                # Extract fonts from resources
                if hasattr(resources, 'get') and '/Font' in resources:
                    fonts = resources['/Font']

                    if fonts:
                        for font_name, font_obj in fonts.items():
                            try:
                                font_info = self._parse_font_object(font_obj, font_name)
                                if font_info:
                                    # Add page number to used pages list
                                    if page_num not in font_info.used_in_pages:
                                        font_info.used_in_pages.append(page_num)

                                    # Check font is not duplicate
                                    font_key = f"{font_info.font_name}_{font_info.base_font}"
                                    if font_key not in self.font_cache:
                                        self.font_cache[font_key] = font_info
                                        result.fonts.append(font_info)
                                    else:
                                        # Update used pages
                                        cached_font = self.font_cache[font_key]
                                        if page_num not in cached_font.used_in_pages:
                                            cached_font.used_in_pages.append(page_num)

                            except Exception as e:
                                logger.warning(f"Error processing font {font_name}: {str(e)}")
                                result.font_problems.append({
                                    "font_name": font_name,
                                    "page": page_num,
                                    "error": str(e)
                                })

        except Exception as e:
            logger.warning(f"خطا در استخراج فونت‌های صفحه {page_num}: {str(e)}")

    def _parse_font_object(self, font_obj, font_name: str) -> FontInfo | None:
        """
        Parse PDF font object
        
        Args:
            font_obj: PDF font object
            font_name: font name
            
        Returns:
            FontInfo: font information
        """
        font_info = FontInfo()
        font_info.font_id = hashlib.md5(f"{font_name}_{id(font_obj)}".encode()).hexdigest()[:8]
        font_info.font_name = font_name

        try:
            # Extract base font
            if hasattr(font_obj, 'get') and '/BaseFont' in font_obj:
                font_info.base_font = font_obj['/BaseFont']
            elif hasattr(font_obj, 'base_font'):
                font_info.base_font = font_obj.base_font

            # Extract subtype
            if hasattr(font_obj, 'get') and '/Subtype' in font_obj:
                font_info.subtype = font_obj['/Subtype']
                # Determine font type by subtype
                font_info.font_type = self._determine_font_type(font_info.subtype)

            # Extract encoding
            if hasattr(font_obj, 'get'):
                if '/Encoding' in font_obj:
                    encoding_obj = font_obj['/Encoding']
                    if hasattr(encoding_obj, 'get') and '/BaseEncoding' in encoding_obj:
                        font_info.encoding = self._determine_encoding(encoding_obj['/BaseEncoding'])
                    elif isinstance(encoding_obj, str):
                        font_info.encoding = self._determine_encoding(encoding_obj)

                # Check ToUnicode
                if '/ToUnicode' in font_obj:
                    font_info.to_unicode_cmap = self._extract_to_unicode(font_obj['/ToUnicode'])
                    font_info.has_to_unicode = True

                # Check CIDSystemInfo
                if '/CIDSystemInfo' in font_obj:
                    cid_info = font_obj['/CIDSystemInfo']
                    if hasattr(cid_info, 'get'):
                        font_info.cid_system_info = {
                            'Registry': cid_info.get('/Registry', ''),
                            'Ordering': cid_info.get('/Ordering', ''),
                            'Supplement': cid_info.get('/Supplement', 0)
                        }
                        font_info.has_cid_system_info = True

                # Extract descriptor
                if '/FontDescriptor' in font_obj:
                    descriptor_obj = font_obj['/FontDescriptor']
                    font_info.descriptor = self._parse_font_descriptor(descriptor_obj)
                    font_info.is_embedded = font_info.descriptor.font_file is not None

                # Extract widths
                if '/Widths' in font_obj:
                    widths_obj = font_obj['/Widths']
                    if isinstance(widths_obj, list):
                        font_info.widths = [float(w) for w in widths_obj]

                # Extract first_char and last_char
                if '/FirstChar' in font_obj:
                    font_info.first_char = int(font_obj['/FirstChar'])
                if '/LastChar' in font_obj:
                    font_info.last_char = int(font_obj['/LastChar'])

            # Detect font language
            font_info.language = self._detect_font_language(font_info)
            font_info.supports_farsi = self._check_farsi_support(font_info)
            font_info.supports_arabic = self._check_arabic_support(font_info)
            font_info.supports_english = self._check_english_support(font_info)

            # Check if subset
            font_info.is_subset = self._is_subset_font(font_info.base_font)

            return font_info

        except Exception as e:
            logger.error(f"Error parsing font {font_name}: {str(e)}")
            return None

    def _parse_font_descriptor(self, descriptor_obj) -> FontDescriptor:
        """
        Parse font descriptor
        
        Args:
            descriptor_obj: descriptor object
            
        Returns:
            FontDescriptor: descriptor information
        """
        descriptor = FontDescriptor()

        try:
            if hasattr(descriptor_obj, 'get'):
                # Extract font name
                if '/FontName' in descriptor_obj:
                    descriptor.font_name = descriptor_obj['/FontName']

                # Extract base font
                if '/BaseFont' in descriptor_obj:
                    descriptor.base_font = descriptor_obj['/BaseFont']

                # Extract font family
                if '/FontFamily' in descriptor_obj:
                    descriptor.font_family = descriptor_obj['/FontFamily']

                # Extract stretch
                if '/FontStretch' in descriptor_obj:
                    descriptor.font_stretch = descriptor_obj['/FontStretch']

                # Extract weight
                if '/FontWeight' in descriptor_obj:
                    descriptor.font_weight = int(descriptor_obj['/FontWeight'])

                # Extract italic angle
                if '/ItalicAngle' in descriptor_obj:
                    descriptor.italic_angle = float(descriptor_obj['/ItalicAngle'])

                # Extract typographic values
                if '/Ascent' in descriptor_obj:
                    descriptor.ascent = float(descriptor_obj['/Ascent'])
                if '/Descent' in descriptor_obj:
                    descriptor.descent = float(descriptor_obj['/Descent'])
                if '/CapHeight' in descriptor_obj:
                    descriptor.cap_height = float(descriptor_obj['/CapHeight'])
                if '/XHeight' in descriptor_obj:
                    descriptor.x_height = float(descriptor_obj['/XHeight'])
                if '/StemV' in descriptor_obj:
                    descriptor.stem_v = float(descriptor_obj['/StemV'])
                if '/StemH' in descriptor_obj:
                    descriptor.stem_h = float(descriptor_obj['/StemH'])
                if '/AvgWidth' in descriptor_obj:
                    descriptor.avg_width = float(descriptor_obj['/AvgWidth'])
                if '/MaxWidth' in descriptor_obj:
                    descriptor.max_width = float(descriptor_obj['/MaxWidth'])
                if '/MissingWidth' in descriptor_obj:
                    descriptor.missing_width = float(descriptor_obj['/MissingWidth'])

                # Extract flags
                if '/Flags' in descriptor_obj:
                    descriptor.flags = int(descriptor_obj['/Flags'])

                # Extract bbox
                if '/FontBBox' in descriptor_obj:
                    bbox_obj = descriptor_obj['/FontBBox']
                    if isinstance(bbox_obj, list) and len(bbox_obj) == 4:
                        descriptor.bbox = (float(bbox_obj[0]), float(bbox_obj[1]), float(bbox_obj[2]), float(bbox_obj[3]))

                # Extract char set
                if '/CharSet' in descriptor_obj:
                    descriptor.char_set = descriptor_obj['/CharSet']

                # Extract embedded font file
                if '/FontFile' in descriptor_obj:
                    descriptor.font_file = self._extract_font_file(descriptor_obj['/FontFile'])
                    descriptor.font_file_type = 'Type1'
                elif '/FontFile2' in descriptor_obj:
                    descriptor.font_file = self._extract_font_file(descriptor_obj['/FontFile2'])
                    descriptor.font_file_type = 'TrueType'
                elif '/FontFile3' in descriptor_obj:
                    descriptor.font_file = self._extract_font_file(descriptor_obj['/FontFile3'])
                    descriptor.font_file_type = 'OpenType'

                if descriptor.font_file:
                    descriptor.font_file_length = len(descriptor.font_file)

        except Exception as e:
            logger.warning(f"Error parsing font descriptor: {str(e)}")

        return descriptor

    def _extract_font_file(self, font_file_obj) -> bytes | None:
        """
        Extract font file data
        
        Args:
            font_file_obj: font file object
            
        Returns:
            bytes: font data
        """
        try:
            if hasattr(font_file_obj, 'get_data'):
                return font_file_obj.get_data()
            elif hasattr(font_file_obj, '_data'):
                return font_file_obj._data
            elif isinstance(font_file_obj, bytes):
                return font_file_obj
        except Exception as e:
            logger.warning(f"Error extracting font file: {str(e)}")

        return None

    def _extract_to_unicode(self, to_unicode_obj) -> bytes | None:
        """
        Extract ToUnicode CMap
        
        Args:
            to_unicode_obj: ToUnicode object
            
        Returns:
            bytes: CMap data
        """
        try:
            if hasattr(to_unicode_obj, 'get_data'):
                return to_unicode_obj.get_data()
            elif hasattr(to_unicode_obj, '_data'):
                return to_unicode_obj._data
        except Exception as e:
            logger.warning(f"Error extracting ToUnicode: {str(e)}")

        return None

    def _determine_font_type(self, subtype: str) -> FontType:
        """
        Determine font type by subtype
        
        Args:
            subtype: font subtype
            
        Returns:
            FontType: font type
        """
        subtype = str(subtype).upper()

        if subtype == '/TYPE0':
            return FontType.TYPE0
        elif subtype == '/TYPE1':
            return FontType.TYPE1
        elif subtype == '/TYPE3':
            return FontType.TYPE3
        elif subtype == '/TRUETYPE':
            return FontType.TRUETYPE
        elif subtype == '/CIDFONTTYPE0':
            return FontType.CIDFONT_TYPE0
        elif subtype == '/CIDFONTTYPE2':
            return FontType.CIDFONT_TYPE2
        elif subtype == '/OPENTYPE':
            return FontType.OPENTYPE
        else:
            return FontType.UNKNOWN

    def _determine_encoding(self, encoding: str) -> FontEncoding:
        """\n        Determine font encoding
        
        Args:
            encoding: font encoding
            
        Returns:
            FontEncoding: encoding type
        """
        if not encoding:
            return FontEncoding.UNKNOWN

        encoding = str(encoding).upper()

        if encoding == '/STANDARDENCODING':
            return FontEncoding.STANDARD
        elif encoding == '/WINANSIENCODING':
            return FontEncoding.WIN_ANSI
        elif encoding == '/MACROMANENCODING':
            return FontEncoding.MAC_ROMAN
        elif encoding == '/PDFDOCENCODING':
            return FontEncoding.PDF_DOC
        elif encoding == '/IDENTITY-H':
            return FontEncoding.IDENTITY_H
        elif encoding == '/IDENTITY-V':
            return FontEncoding.IDENTITY_V
        else:
            return FontEncoding.CUSTOM

    def _detect_font_language(self, font_info: FontInfo) -> FontLanguage:
        """
        Detect font language
        
        Args:
            font_info: font information
            
        Returns:
            FontLanguage: font language
        """
        # Check by font name
        font_name_lower = font_info.base_font.lower()

        # Check Persian fonts
        farsi_keywords = ['farsi', 'persian', 'iran', 'nazanin', 'titr', 'yekan',
                         'zar', 'badr', 'lotus', 'mitra', 'roya', 'shabnam']

        for keyword in farsi_keywords:
            if keyword in font_name_lower:
                return FontLanguage.FARSI

        # Check Arabic fonts
        arabic_keywords = ['arabic', 'arab', 'kfgq', 'scheherazade', 'lateef', 'amiri']

        for keyword in arabic_keywords:
            if keyword in font_name_lower:
                return FontLanguage.ARABIC

        # Check by charset
        if font_info.descriptor and font_info.descriptor.char_set:
            char_set = font_info.descriptor.char_set.lower()
            if 'arabic' in char_set or 'farsi' in char_set or 'persian' in char_set:
                return FontLanguage.FARSI

        # Check by CIDSystemInfo
        if font_info.cid_system_info:
            registry = font_info.cid_system_info.get('Registry', '').lower()
            ordering = font_info.cid_system_info.get('Ordering', '').lower()

            if 'arabic' in registry or 'farsi' in registry or 'persian' in registry:
                return FontLanguage.FARSI
            if 'arabic' in ordering or 'farsi' in ordering or 'persian' in ordering:
                return FontLanguage.FARSI

        return FontLanguage.UNKNOWN

    def _check_farsi_support(self, font_info: FontInfo) -> bool:
        """
        Check Persian support
        
        Args:
            font_info: font information
            
        Returns:
            bool: True if font supports Persian
        """
        # Check by font name
        if font_info.base_font:
            for farsi_font in self.farsi_font_names:
                if farsi_font.lower() in font_info.base_font.lower():
                    return True

        # Check by detected language
        if font_info.language == FontLanguage.FARSI:
            return True

        # Check by charset
        if font_info.descriptor and font_info.descriptor.char_set:
            char_set = font_info.descriptor.char_set.lower()
            if 'arabic' in char_set or 'farsi' in char_set or 'persian' in char_set:
                return True

        return False

    def _check_arabic_support(self, font_info: FontInfo) -> bool:
        """
        Check Arabic support
        
        Args:
            font_info: font information
            
        Returns:
            bool: True if font supports Arabic
        """
        if font_info.language == FontLanguage.ARABIC:
            return True

        if font_info.base_font:
            arabic_keywords = ['arabic', 'arab', 'kfgq', 'scheherazade', 'lateef', 'amiri']
            for keyword in arabic_keywords:
                if keyword in font_info.base_font.lower():
                    return True

        return False

    def _check_english_support(self, font_info: FontInfo) -> bool:
        """
        Check English support
        
        Args:
            font_info: font information
            
        Returns:
            bool: True if font supports English
        """
        # Most fonts support English
        # Unless specifically for a particular language
        if font_info.language == FontLanguage.FARSI or font_info.language == FontLanguage.ARABIC:
            # Persian/Arabic fonts usually support English too
            return True

        return True

    def _is_subset_font(self, base_font: str) -> bool:
        """
        Check if font is subset
        
        Args:
            base_font: base font name
            
        Returns:
            bool: True if font is subset
        """
        if not base_font:
            return False

        # Subset fonts usually start with uppercase letters and + sign
        # Or contain specific words
        subset_indicators = ['+', 'SUBSET', 'SUBSETTED', 'SUBSET-']

        for indicator in subset_indicators:
            if indicator in base_font.upper():
                return True

        return False

    def _analyze_extracted_fonts(self, result: FontAnalysisResult):
        """
        Analyze extracted fonts
        
        Args:
            result: Results object
        """
        result.total_fonts = len(result.fonts)

        for font in result.fonts:
            # Count embedded fonts
            if font.is_embedded:
                result.embedded_fonts += 1

            # Count subset fonts
            if font.is_subset:
                result.subset_fonts += 1

            # Count Persian fonts
            if font.supports_farsi:
                result.farsi_fonts += 1
                result.farsi_font_list.append(font)

            # Count Arabic fonts
            if font.supports_arabic:
                result.arabic_fonts += 1

            # Check encoding issues
            if font.encoding == FontEncoding.UNKNOWN:
                result.encoding_issues.append(f"فونت {font.font_name}: unknown encoding")

            # Check ToUnicode
            if not font.to_unicode_cmap and font.supports_farsi:
                result.font_problems.append({
                    "font": font.font_name,
                    "type": "missing_tounicode",
                    "message": "Persian font without ToUnicode CMap"
                })

        # Generate suggestions
        self._generate_suggestions(result)

    def _generate_suggestions(self, result: FontAnalysisResult):
        """Generate suggestions based on font analysis"""

        if result.farsi_fonts == 0:
            result.suggestions.append("No Persian font found in the document. Persian text may not display correctly.")

        if result.embedded_fonts == 0:
            result.suggestions.append("No embedded fonts in the document. The document may not display correctly on other systems.")

        if result.subset_fonts > 0:
            result.suggestions.append(f"{result.subset_fonts} subset fonts exist. Some characters may not be available.")

        for font in result.fonts:
            if font.supports_farsi and not font.is_embedded:
                result.suggestions.append(f"Persian font '{font.base_font}' is not embedded. Embed it for correct display on all systems.")

            if font.supports_farsi and not font.to_unicode_cmap:
                result.suggestions.append(f"Persian font '{font.base_font}' lacks ToUnicode CMap. Persian text may not be searchable.")

    def _extract_fonts_fallback(self, pdf_path: str, result: FontAnalysisResult):
        """
        Fallback method for font extraction (without PyPDF2)
        
        Args:
            pdf_path: PDF file path
            result: Results object
        """
        logger.info("Using fallback method for font extraction")

        try:
            with open(pdf_path, 'rb') as file:
                content = file.read()

                # Search for fonts in binary content
                font_patterns = [
                    b'/Font',
                    b'/BaseFont',
                    b'/FontDescriptor',
                    b'/Type /Font',
                    b'/Subtype /Type1',
                    b'/Subtype /TrueType',
                    b'/Subtype /Type0'
                ]

                for pattern in font_patterns:
                    positions = self._find_all_occurrences(content, pattern)
                    for pos in positions:
                        try:
                            # Extract font information from around position
                            font_info = self._extract_font_from_binary(content, pos)
                            if font_info:
                                result.fonts.append(font_info)
                        except Exception as e:
                            logger.warning(f"Error extracting font at position {pos}: {str(e)}")

                # Analyze extracted fonts
                self._analyze_extracted_fonts(result)

        except Exception as e:
            logger.error(f"Error in fallback method: {str(e)}")
            result.font_problems.append({
                "type": "fallback_error",
                "message": f"Error extracting fonts: {str(e)}"
            })

    def _find_all_occurrences(self, content: bytes, pattern: bytes) -> list[int]:
        """
        Find all occurrences of a pattern in content
        
        Args:
            content: binary content
            pattern: search pattern
            
        Returns:
            List[int]: list of positions
        """
        positions = []
        start = 0

        while True:
            pos = content.find(pattern, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1

        return positions

    def _extract_font_from_binary(self, content: bytes, position: int) -> FontInfo | None:
        """
        Extract font information from binary content
        
        Args:
            content: binary content
            position: start position
            
        Returns:
            FontInfo: font information
        """
        # This is a simple implementation
        # In reality, it needs more precise PDF structure parsing

        font_info = FontInfo()
        font_info.font_id = f"bin_{position:08x}"

        # Extract base font from around position
        start = max(0, position - 200)
        end = min(len(content), position + 200)
        chunk = content[start:end]

        # Search for BaseFont
        basefont_match = re.search(b'/BaseFont\\s*/([^\\s\\[\\]<]+)', chunk)
        if basefont_match and basefont_match.group(1):
            try:
                font_bytes = basefont_match.group(1)
                if font_bytes:
                    font_info.base_font = font_bytes.decode('latin-1', errors='ignore')
                    if font_info.base_font:
                        font_info.font_name = font_info.base_font.split('+')[-1] if '+' in font_info.base_font else font_info.base_font
            except (UnicodeDecodeError, AttributeError):
                pass

        # Search for Subtype
        subtype_match = re.search(b'/Subtype\\s*/([^\\s\\[\\]<]+)', chunk)
        if subtype_match and subtype_match.group(1):
            try:
                subtype_bytes = subtype_match.group(1)
                if subtype_bytes:
                    font_info.subtype = subtype_bytes.decode('latin-1', errors='ignore')
            except (UnicodeDecodeError, AttributeError):
                pass
        return font_info
