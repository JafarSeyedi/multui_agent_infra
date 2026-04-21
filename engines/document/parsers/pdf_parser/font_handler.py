# -*- coding: utf-8 -*-
"""
font_handler.py - مدیریت فونت‌های فارسی در PDF

این ماژول مسئولیت استخراج، تحلیل و مدیریت فونت‌های فارسی در فایل‌های PDF را بر عهده دارد.
"""

import os
import re
import json
import base64
import hashlib
import logging
from typing import Dict, List, Tuple, Optional, Any, Union, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import struct
import zlib
import io

# تنظیمات لاگ‌گیری
logger = logging.getLogger(__name__)


class FontType(Enum):
    """انواع فونت‌های PDF"""
    TYPE0 = "Type0"  # فونت مرکب
    TYPE1 = "Type1"  # Type1
    TYPE3 = "Type3"  # Type3
    TRUETYPE = "TrueType"
    CIDFONT_TYPE0 = "CIDFontType0"
    CIDFONT_TYPE2 = "CIDFontType2"
    OPENTYPE = "OpenType"
    UNKNOWN = "Unknown"


class FontEncoding(Enum):
    """انواع encoding فونت‌ها"""
    STANDARD = "StandardEncoding"
    WIN_ANSI = "WinAnsiEncoding"
    MAC_ROMAN = "MacRomanEncoding"
    PDF_DOC = "PDFDocEncoding"
    IDENTITY_H = "Identity-H"
    IDENTITY_V = "Identity-V"
    CUSTOM = "Custom"
    UNKNOWN = "Unknown"


class FontLanguage(Enum):
    """زبان‌های فونت"""
    FARSI = "Farsi"
    ARABIC = "Arabic"
    ENGLISH = "English"
    MULTILINGUAL = "Multilingual"
    UNKNOWN = "Unknown"


@dataclass
class FontDescriptor:
    """داده‌های توصیف‌کننده فونت"""
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
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    char_set: str = ""
    font_file: Optional[bytes] = None
    font_file_length: int = 0
    font_file_type: str = ""
    font_file_subtype: str = ""


@dataclass
class FontInfo:
    """اطلاعات کامل یک فونت"""
    # شناسه فونت
    font_id: str = ""
    font_name: str = ""
    base_font: str = ""
    
    # نوع فونت
    font_type: FontType = FontType.UNKNOWN
    subtype: str = ""
    
    # encoding
    encoding: FontEncoding = FontEncoding.UNKNOWN
    to_unicode_cmap: Optional[bytes] = None
    cid_system_info: Optional[Dict[str, str]] = None
    
    # اطلاعات فنی
    descriptor: Optional[FontDescriptor] = None
    first_char: int = 0
    last_char: int = 255
    widths: List[float] = field(default_factory=list)
    
    # اطلاعات زبانی
    language: FontLanguage = FontLanguage.UNKNOWN
    supports_farsi: bool = False
    supports_arabic: bool = False
    supports_english: bool = False
    
    # اطلاعات embedded
    is_embedded: bool = False
    embedded_data: Optional[bytes] = None
    embedded_data_type: str = ""
    
    # اطلاعات استفاده
    used_in_pages: List[int] = field(default_factory=list)
    char_count: int = 0
    is_subset: bool = False
    
    # متادیتا
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FontAnalysisResult:
    """نتایج تحلیل فونت‌ها"""
    # لیست فونت‌ها
    fonts: List[FontInfo] = field(default_factory=list)
    
    # آمار کلی
    total_fonts: int = 0
    embedded_fonts: int = 0
    subset_fonts: int = 0
    farsi_fonts: int = 0
    arabic_fonts: int = 0
    
    # فونت‌های فارسی
    farsi_font_list: List[FontInfo] = field(default_factory=list)
    
    # مشکلات فونت
    font_problems: List[Dict[str, Any]] = field(default_factory=list)
    
    # پیشنهادات
    suggestions: List[str] = field(default_factory=list)
    
    # اطلاعات فنی
    has_to_unicode: bool = False
    has_cid_system_info: bool = False
    encoding_issues: List[str] = field(default_factory=list)


class FontHandler:
    """کلاس اصلی مدیریت فونت‌های فارسی"""
    
    def __init__(self, pdf_parser=None):
        """
        مقداردهی اولیه
        
        Args:
            pdf_parser: نمونه PDFParser (اختیاری)
        """
        self.pdf_parser = pdf_parser
        self.font_cache: Dict[str, FontInfo] = {}
        self.character_maps: Dict[str, Dict[int, str]] = {}
        
        # جداول mapping برای فونت‌های فارسی
        self._init_farsi_mappings()
        
    def _init_farsi_mappings(self):
        """مقداردهی جداول mapping فارسی"""
        # جدول تبدیل کدهای فارسی رایج
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
        
        # لیست کاراکترهای فارسی
        self.farsi_chars = set([
            'آ', 'أ', 'ؤ', 'إ', 'ئ', 'ا', 'ب', 'ة', 'ت', 'ث',
            'ج', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص',
            'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ک', 'ل', 'م',
            'ن', 'ه', 'و', 'ی', 'ي', 'ً', 'ٌ', 'ٍ', 'َ', 'ُ',
            'ِ', 'ّ', 'ْ', 'پ', 'چ', 'ژ', 'گ', '۰', '۱', '۲',
            '۳', '۴', '۵', '۶', '۷', '۸', '۹'
        ])
        
        # لیست کاراکترهای عربی
        self.arabic_chars = set([
            'آ', 'أ', 'ؤ', 'إ', 'ئ', 'ا', 'ب', 'ة', 'ت', 'ث',
            'ج', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص',
            'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م',
            'ن', 'ه', 'و', 'ي', 'ى', 'ً', 'ٌ', 'ٍ', 'َ', 'ُ',
            'ِ', 'ّ', 'ْ'
        ])
        
        # نام فونت‌های فارسی رایج
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
        استخراج و تحلیل فونت‌های PDF
        
        Args:
            pdf_path: مسیر فایل PDF
            
        Returns:
            FontAnalysisResult: نتایج تحلیل فونت‌ها
        """
        logger.info(f"استخراج فونت‌ها از فایل: {pdf_path}")
        
        result = FontAnalysisResult()
        
        try:
            # استفاده از PyPDF2 برای استخراج فونت‌ها
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # استخراج فونت‌ها از هر صفحه
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        self._extract_fonts_from_page(page, page_num, result)
                    except Exception as e:
                        logger.warning(f"خطا در استخراج فونت‌های صفحه {page_num}: {str(e)}")
                
                # تحلیل فونت‌های استخراج شده
                self._analyze_extracted_fonts(result)
                
        except ImportError:
            logger.error("PyPDF2 نصب نیست. استفاده از روش fallback")
            self._extract_fonts_fallback(pdf_path, result)
        except Exception as e:
            logger.error(f"خطا در استخراج فونت‌ها: {str(e)}")
            result.font_problems.append({
                "type": "extraction_error",
                "message": f"خطا در استخراج فونت‌ها: {str(e)}"
            })
        
        return result
    
    def _extract_fonts_from_page(self, page, page_num: int, result: FontAnalysisResult):
        """
        استخراج فونت‌ها از یک صفحه
        
        Args:
            page: صفحه PDF
            page_num: شماره صفحه
            result: شیء نتایج
        """
        try:
            # استخراج منابع صفحه
            if hasattr(page, 'resources') and page.resources:
                resources = page.resources
                
                # استخراج فونت‌ها از منابع
                if hasattr(resources, 'get') and '/Font' in resources:
                    fonts = resources['/Font']
                    
                    if fonts:
                        for font_name, font_obj in fonts.items():
                            try:
                                font_info = self._parse_font_object(font_obj, font_name)
                                if font_info:
                                    # اضافه کردن شماره صفحه به لیست صفحات استفاده
                                    if page_num not in font_info.used_in_pages:
                                        font_info.used_in_pages.append(page_num)
                                    
                                    # بررسی تکراری نبودن فونت
                                    font_key = f"{font_info.font_name}_{font_info.base_font}"
                                    if font_key not in self.font_cache:
                                        self.font_cache[font_key] = font_info
                                        result.fonts.append(font_info)
                                    else:
                                        # به‌روزرسانی صفحات استفاده
                                        cached_font = self.font_cache[font_key]
                                        if page_num not in cached_font.used_in_pages:
                                            cached_font.used_in_pages.append(page_num)
                                    
                            except Exception as e:
                                logger.warning(f"خطا در پردازش فونت {font_name}: {str(e)}")
                                result.font_problems.append({
                                    "font_name": font_name,
                                    "page": page_num,
                                    "error": str(e)
                                })
                
        except Exception as e:
            logger.warning(f"خطا در استخراج فونت‌های صفحه {page_num}: {str(e)}")
    
    def _parse_font_object(self, font_obj, font_name: str) -> Optional[FontInfo]:
        """
        پارس شیء فونت PDF
        
        Args:
            font_obj: شیء فونت PDF
            font_name: نام فونت
            
        Returns:
            FontInfo: اطلاعات فونت
        """
        font_info = FontInfo()
        font_info.font_id = hashlib.md5(f"{font_name}_{id(font_obj)}".encode()).hexdigest()[:8]
        font_info.font_name = font_name
        
        try:
            # استخراج base font
            if hasattr(font_obj, 'get') and '/BaseFont' in font_obj:
                font_info.base_font = font_obj['/BaseFont']
            elif hasattr(font_obj, 'base_font'):
                font_info.base_font = font_obj.base_font
            
            # استخراج subtype
            if hasattr(font_obj, 'get') and '/Subtype' in font_obj:
                font_info.subtype = font_obj['/Subtype']
                # تعیین نوع فونت بر اساس subtype
                font_info.font_type = self._determine_font_type(font_info.subtype)
            
            # استخراج encoding
            if hasattr(font_obj, 'get'):
                if '/Encoding' in font_obj:
                    encoding_obj = font_obj['/Encoding']
                    if hasattr(encoding_obj, 'get') and '/BaseEncoding' in encoding_obj:
                        font_info.encoding = self._determine_encoding(encoding_obj['/BaseEncoding'])
                    elif isinstance(encoding_obj, str):
                        font_info.encoding = self._determine_encoding(encoding_obj)
                
                # بررسی ToUnicode
                if '/ToUnicode' in font_obj:
                    font_info.to_unicode_cmap = self._extract_to_unicode(font_obj['/ToUnicode'])
                    font_info.has_to_unicode = True
                
                # بررسی CIDSystemInfo
                if '/CIDSystemInfo' in font_obj:
                    cid_info = font_obj['/CIDSystemInfo']
                    if hasattr(cid_info, 'get'):
                        font_info.cid_system_info = {
                            'Registry': cid_info.get('/Registry', ''),
                            'Ordering': cid_info.get('/Ordering', ''),
                            'Supplement': cid_info.get('/Supplement', 0)
                        }
                        font_info.has_cid_system_info = True
                
                # استخراج descriptor
                if '/FontDescriptor' in font_obj:
                    descriptor_obj = font_obj['/FontDescriptor']
                    font_info.descriptor = self._parse_font_descriptor(descriptor_obj)
                    font_info.is_embedded = font_info.descriptor.font_file is not None
                
                # استخراج widths
                if '/Widths' in font_obj:
                    widths_obj = font_obj['/Widths']
                    if isinstance(widths_obj, list):
                        font_info.widths = [float(w) for w in widths_obj]
                
                # استخراج first_char و last_char
                if '/FirstChar' in font_obj:
                    font_info.first_char = int(font_obj['/FirstChar'])
                if '/LastChar' in font_obj:
                    font_info.last_char = int(font_obj['/LastChar'])
            
            # تشخیص زبان فونت
            font_info.language = self._detect_font_language(font_info)
            font_info.supports_farsi = self._check_farsi_support(font_info)
            font_info.supports_arabic = self._check_arabic_support(font_info)
            font_info.supports_english = self._check_english_support(font_info)
            
            # بررسی subset بودن
            font_info.is_subset = self._is_subset_font(font_info.base_font)
            
            return font_info
            
        except Exception as e:
            logger.error(f"خطا در پارس فونت {font_name}: {str(e)}")
            return None
    
    def _parse_font_descriptor(self, descriptor_obj) -> FontDescriptor:
        """
        پارس descriptor فونت
        
        Args:
            descriptor_obj: شیء descriptor
            
        Returns:
            FontDescriptor: اطلاعات descriptor
        """
        descriptor = FontDescriptor()
        
        try:
            if hasattr(descriptor_obj, 'get'):
                # استخراج نام فونت
                if '/FontName' in descriptor_obj:
                    descriptor.font_name = descriptor_obj['/FontName']
                
                # استخراج base font
                if '/BaseFont' in descriptor_obj:
                    descriptor.base_font = descriptor_obj['/BaseFont']
                
                # استخراج خانواده فونت
                if '/FontFamily' in descriptor_obj:
                    descriptor.font_family = descriptor_obj['/FontFamily']
                
                # استخراج stretch
                if '/FontStretch' in descriptor_obj:
                    descriptor.font_stretch = descriptor_obj['/FontStretch']
                
                # استخراج وزن
                if '/FontWeight' in descriptor_obj:
                    descriptor.font_weight = int(descriptor_obj['/FontWeight'])
                
                # استخراج زاویه ایتالیک
                if '/ItalicAngle' in descriptor_obj:
                    descriptor.italic_angle = float(descriptor_obj['/ItalicAngle'])
                
                # استخراج مقادیر typographic
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
                
                # استخراج flags
                if '/Flags' in descriptor_obj:
                    descriptor.flags = int(descriptor_obj['/Flags'])
                
                # استخراج bbox
                if '/FontBBox' in descriptor_obj:
                    bbox_obj = descriptor_obj['/FontBBox']
                    if isinstance(bbox_obj, list) and len(bbox_obj) == 4:
                        descriptor.bbox = tuple(float(x) for x in bbox_obj)
                
                # استخراج char set
                if '/CharSet' in descriptor_obj:
                    descriptor.char_set = descriptor_obj['/CharSet']
                
                # استخراج فایل فونت embedded
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
            logger.warning(f"خطا در پارس descriptor فونت: {str(e)}")
        
        return descriptor
    
    def _extract_font_file(self, font_file_obj) -> Optional[bytes]:
        """
        استخراج داده‌های فایل فونت
        
        Args:
            font_file_obj: شیء فایل فونت
            
        Returns:
            bytes: داده‌های فونت
        """
        try:
            if hasattr(font_file_obj, 'get_data'):
                return font_file_obj.get_data()
            elif hasattr(font_file_obj, '_data'):
                return font_file_obj._data
            elif isinstance(font_file_obj, bytes):
                return font_file_obj
        except Exception as e:
            logger.warning(f"خطا در استخراج فایل فونت: {str(e)}")
        
        return None
    
    def _extract_to_unicode(self, to_unicode_obj) -> Optional[bytes]:
        """
        استخراج ToUnicode CMap
        
        Args:
            to_unicode_obj: شیء ToUnicode
            
        Returns:
            bytes: داده‌های CMap
        """
        try:
            if hasattr(to_unicode_obj, 'get_data'):
                return to_unicode_obj.get_data()
            elif hasattr(to_unicode_obj, '_data'):
                return to_unicode_obj._data
        except Exception as e:
            logger.warning(f"خطا در استخراج ToUnicode: {str(e)}")
        
        return None
    
    def _determine_font_type(self, subtype: str) -> FontType:
        """
        تعیین نوع فونت بر اساس subtype
        
        Args:
            subtype: subtype فونت
            
        Returns:
            FontType: نوع فونت
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
        """
        تعیین encoding فونت
        
        Args:
            encoding: encoding فونت
            
        Returns:
            FontEncoding: نوع encoding
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
        تشخیص زبان فونت
        
        Args:
            font_info: اطلاعات فونت
            
        Returns:
            FontLanguage: زبان فونت
        """
        # بررسی بر اساس نام فونت
        font_name_lower = font_info.base_font.lower()
        
        # بررسی فونت‌های فارسی
        farsi_keywords = ['farsi', 'persian', 'iran', 'nazanin', 'titr', 'yekan', 
                         'zar', 'badr', 'lotus', 'mitra', 'roya', 'shabnam']
        
        for keyword in farsi_keywords:
            if keyword in font_name_lower:
                return FontLanguage.FARSI
        
        # بررسی فونت‌های عربی
        arabic_keywords = ['arabic', 'arab', 'kfgq', 'scheherazade', 'lateef', 'amiri']
        
        for keyword in arabic_keywords:
            if keyword in font_name_lower:
                return FontLanguage.ARABIC
        
        # بررسی بر اساس charset
        if font_info.descriptor and font_info.descriptor.char_set:
            char_set = font_info.descriptor.char_set.lower()
            if 'arabic' in char_set or 'farsi' in char_set or 'persian' in char_set:
                return FontLanguage.FARSI
        
        # بررسی بر اساس CIDSystemInfo
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
        بررسی پشتیبانی از فارسی
        
        Args:
            font_info: اطلاعات فونت
            
        Returns:
            bool: True اگر فونت از فارسی پشتیبانی کند
        """
        # بررسی بر اساس نام فونت
        if font_info.base_font:
            for farsi_font in self.farsi_font_names:
                if farsi_font.lower() in font_info.base_font.lower():
                    return True
        
        # بررسی بر اساس زبان تشخیص داده شده
        if font_info.language == FontLanguage.FARSI:
            return True
        
        # بررسی بر اساس charset
        if font_info.descriptor and font_info.descriptor.char_set:
            char_set = font_info.descriptor.char_set.lower()
            if 'arabic' in char_set or 'farsi' in char_set or 'persian' in char_set:
                return True
        
        return False
    
    def _check_arabic_support(self, font_info: FontInfo) -> bool:
        """
        بررسی پشتیبانی از عربی
        
        Args:
            font_info: اطلاعات فونت
            
        Returns:
            bool: True اگر فونت از عربی پشتیبانی کند
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
        بررسی پشتیبانی از انگلیسی
        
        Args:
            font_info: اطلاعات فونت
            
        Returns:
            bool: True اگر فونت از انگلیسی پشتیبانی کند
        """
        # بیشتر فونت‌ها از انگلیسی پشتیبانی می‌کنند
        # مگر اینکه مشخصاً فقط برای زبان خاصی باشند
        if font_info.language == FontLanguage.FARSI or font_info.language == FontLanguage.ARABIC:
            # فونت‌های فارسی/عربی معمولاً از انگلیسی هم پشتیبانی می‌کنند
            return True
        
        return True
    
    def _is_subset_font(self, base_font: str) -> bool:
        """
        بررسی subset بودن فونت
        
        Args:
            base_font: نام base font
            
        Returns:
            bool: True اگر فونت subset باشد
        """
        if not base_font:
            return False
        
        # فونت‌های subset معمولاً با حروف بزرگ و علامت + شروع می‌شوند
        # یا شامل کلمات خاصی هستند
        subset_indicators = ['+', 'SUBSET', 'SUBSETTED', 'SUBSET-']
        
        for indicator in subset_indicators:
            if indicator in base_font.upper():
                return True
        
        return False
    
    def _analyze_extracted_fonts(self, result: FontAnalysisResult):
        """
        تحلیل فونت‌های استخراج شده
        
        Args:
            result: شیء نتایج
        """
        result.total_fonts = len(result.fonts)
        
        for font in result.fonts:
            # شمارش فونت‌های embedded
            if font.is_embedded:
                result.embedded_fonts += 1
            
            # شمارش فونت‌های subset
            if font.is_subset:
                result.subset_fonts += 1
            
            # شمارش فونت‌های فارسی
            if font.supports_farsi:
                result.farsi_fonts += 1
                result.farsi_font_list.append(font)
            
            # شمارش فونت‌های عربی
            if font.supports_arabic:
                result.arabic_fonts += 1
            
            # بررسی مشکلات encoding
            if font.encoding == FontEncoding.UNKNOWN:
                result.encoding_issues.append(f"فونت {font.font_name}: encoding نامشخص")
            
            # بررسی ToUnicode
            if not font.to_unicode_cmap and font.supports_farsi:
                result.font_problems.append({
                    "font": font.font_name,
                    "type": "missing_tounicode",
                    "message": "فونت فارسی بدون ToUnicode CMap"
                })
        
        # تولید پیشنهادات
        self._generate_suggestions(result)
    
    def _generate_suggestions(self, result: FontAnalysisResult):
        """تولید پیشنهادات بر اساس تحلیل فونت‌ها"""
        
        if result.farsi_fonts == 0:
            result.suggestions.append("هیچ فونت فارسی در سند یافت نشد. ممکن است متن فارسی به درستی نمایش داده نشود.")
        
        if result.embedded_fonts == 0:
            result.suggestions.append("هیچ فونت embedded در سند وجود ندارد. ممکن است نمایش سند در سیستم‌های دیگر با مشکل مواجه شود.")
        
        if result.subset_fonts > 0:
            result.suggestions.append(f"{result.subset_fonts} فونت subset شده وجود دارد. ممکن است برخی کاراکترها موجود نباشند.")
        
        for font in result.fonts:
            if font.supports_farsi and not font.is_embedded:
                result.suggestions.append(f"فونت فارسی '{font.base_font}' embedded نیست. برای نمایش صحیح در همه سیستم‌ها آن را embed کنید.")
            
            if font.supports_farsi and not font.to_unicode_cmap:
                result.suggestions.append(f"فونت فارسی '{font.base_font}' فاقد ToUnicode CMap است. ممکن است متن فارسی قابل جستجو نباشد.")
    
    def _extract_fonts_fallback(self, pdf_path: str, result: FontAnalysisResult):
        """
        روش fallback برای استخراج فونت‌ها (بدون PyPDF2)
        
        Args:
            pdf_path: مسیر فایل PDF
            result: شیء نتایج
        """
        logger.info("استفاده از روش fallback برای استخراج فونت‌ها")
        
        try:
            with open(pdf_path, 'rb') as file:
                content = file.read()
                
                # جستجوی فونت‌ها در محتوای باینری
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
                            # استخراج اطلاعات فونت از اطراف موقعیت
                            font_info = self._extract_font_from_binary(content, pos)
                            if font_info:
                                result.fonts.append(font_info)
                        except Exception as e:
                            logger.warning(f"خطا در استخراج فونت از موقعیت {pos}: {str(e)}")
                
                # تحلیل فونت‌های استخراج شده
                self._analyze_extracted_fonts(result)
                
        except Exception as e:
            logger.error(f"خطا در روش fallback: {str(e)}")
            result.font_problems.append({
                "type": "fallback_error",
                "message": f"خطا در استخراج فونت‌ها: {str(e)}"
            })
    
    def _find_all_occurrences(self, content: bytes, pattern: bytes) -> List[int]:
        """
        یافتن تمام occurrences یک الگو در محتوا
        
        Args:
            content: محتوای باینری
            pattern: الگوی جستجو
            
        Returns:
            List[int]: لیست موقعیت‌ها
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
    
    def _extract_font_from_binary(self, content: bytes, position: int) -> Optional[FontInfo]:
        """
        استخراج اطلاعات فونت از محتوای باینری
        
        Args:
            content: محتوای باینری
            position: موقعیت شروع
            
        Returns:
            FontInfo: اطلاعات فونت
        """
        # این یک پیاده‌سازی ساده است
        # در واقعیت نیاز به پارس دقیق‌تر ساختار PDF دارد
        
        font_info = FontInfo()
        font_info.font_id = f"bin_{position:08x}"
        
        # استخراج base font از اطراف موقعیت
        start = max(0, position - 200)
        end = min(len(content), position + 200)
        chunk = content[start:end]
        
        # جستجوی BaseFont
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
        
        # جستجوی Subtype
        subtype_match = re.search(b'/Subtype\\s*/([^\\s\\[\\]<]+)', chunk)
        if subtype_match and subtype_match.group(1):
            try:
                subtype_bytes = subtype_match.group(1)
                if subtype_bytes:
                    font_info.subtype = subtype_bytes.decode('latin-1', errors='ignore')
            except (UnicodeDecodeError, AttributeError):
                pass
