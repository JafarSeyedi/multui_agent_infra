#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ماژول ابزارهای کمکی برای PDF Parser
شامل توابع کاربردی برای پردازش متن، تصویر، و عملیات کمکی
"""

import base64
import hashlib
import json
import math
import os
import re
import io
import tempfile
import warnings
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper  # type: ignore[import-untyped]
from bidi.algorithm import get_display  # type: ignore[import-not-found]
from PIL.Image import Image as PILImage


class TextDirection(Enum):
    """جهت متن"""
    LTR = "ltr"  # چپ به راست
    RTL = "rtl"  # راست به چپ
    TTB = "ttb"  # بالا به پایین (عمودی)


class Language(Enum):
    """زبان‌های پشتیبانی شده"""
    PERSIAN = "fa"
    ENGLISH = "en"
    ARABIC = "ar"
    FRENCH = "fr"
    GERMAN = "de"
    SPANISH = "es"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    HEBREW = "he"    
    UNKNOWN = "unknown"


@dataclass
class BoundingBox:
    """محدوده مستطیلی (Bounding Box)"""
    x0: float
    y0: float
    x1: float
    y1: float
    
    @property
    def width(self) -> float:
        """عرض محدوده"""
        return abs(self.x1 - self.x0)
    
    @property
    def height(self) -> float:
        """ارتفاع محدوده"""
        return abs(self.y1 - self.y0)
    
    @property
    def area(self) -> float:
        """مساحت محدوده"""
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[float, float]:
        """مرکز محدوده"""
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)
    
    def intersects(self, other: 'BoundingBox', threshold: float = 0.1) -> bool:
        """
        بررسی تقاطع دو محدوده
        
        Args:
            other: محدوده دیگر
            threshold: آستانه تقاطع (نسبت مساحت)
            
        Returns:
            True اگر تقاطع داشته باشند
        """
        # محاسبه محدوده تقاطع
        inter_x0 = max(self.x0, other.x0)
        inter_y0 = max(self.y0, other.y0)
        inter_x1 = min(self.x1, other.x1)
        inter_y1 = min(self.y1, other.y1)
        
        if inter_x0 < inter_x1 and inter_y0 < inter_y1:
            # محاسبه مساحت تقاطع
            inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
            # محاسبه حداقل مساحت دو محدوده
            min_area = min(self.area, other.area)
            # بررسی آستانه
            return (inter_area / min_area) >= threshold
        return False
    
    def contains(self, point: Tuple[float, float]) -> bool:
        """
        بررسی آیا نقطه در محدوده قرار دارد
        
        Args:
            point: نقطه (x, y)
            
        Returns:
            True اگر نقطه در محدوده باشد
        """
        x, y = point
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1
    
    def distance_to(self, other: 'BoundingBox') -> float:
        """
        محاسبه فاصله بین مرکز دو محدوده
        
        Args:
            other: محدوده دیگر
            
        Returns:
            فاصله اقلیدسی
        """
        x1, y1 = self.center
        x2, y2 = other.center
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    def to_tuple(self) -> Tuple[float, float, float, float]:
        """تبدیل به تاپل"""
        return (self.x0, self.y0, self.x1, self.y1)
    
    @classmethod
    def from_tuple(cls, bbox_tuple: Tuple[float, float, float, float]) -> 'BoundingBox':
        """ایجاد از تاپل"""
        return cls(*bbox_tuple)
    
    def __str__(self) -> str:
        return f"BBox({self.x0:.2f}, {self.y0:.2f}, {self.x1:.2f}, {self.y1:.2f})"


class TextUtils:
    """ابزارهای پردازش متن"""
    
    @staticmethod
    def detect_language(text: str) -> Language:
        """
        تشخیص زبان متن
        
        Args:
            text: متن ورودی
            
        Returns:
            زبان تشخیص داده شده
        """
        if not text or not text.strip():
            return Language.UNKNOWN
        
        text = text.strip()
        
        # الگوهای زبان‌های مختلف
        patterns = {
            Language.PERSIAN: r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]',
            Language.ARABIC: r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]',
            Language.ENGLISH: r'[a-zA-Z]',
            Language.FRENCH: r'[a-zA-ZÀ-ÿ]',
            Language.GERMAN: r'[a-zA-ZÄÖÜäöüß]',
            Language.SPANISH: r'[a-zA-ZÁÉÍÓÚáéíóúÑñ]',
            Language.RUSSIAN: r'[\u0400-\u04FF]',
            Language.CHINESE: r'[\u4e00-\u9fff]',
            Language.JAPANESE: r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]',
            Language.KOREAN: r'[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]',
        }
        
        # شمارش کاراکترهای هر زبان
        counts = {}
        for lang, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                counts[lang] = len(matches)
        
        if not counts:
            return Language.UNKNOWN
        
        # زبان با بیشترین تعداد کاراکتر
        detected_lang = max(counts.items(), key=lambda x: x[1])[0]
        
        # تشخیص تفاوت فارسی و عربی (ساده)
        if detected_lang in [Language.PERSIAN, Language.ARABIC]:
            # کلمات خاص فارسی
            persian_words = ['است', 'های', 'را', 'که', 'این', 'با', 'برای']
            arabic_words = ['ال', 'وال', 'ب', 'ف', 'و']
            
            persian_count = sum(1 for word in persian_words if word in text)
            arabic_count = sum(1 for word in arabic_words if word in text)
            
            if persian_count > arabic_count:
                return Language.PERSIAN
            else:
                return Language.ARABIC
        
        return detected_lang
    
    @staticmethod
    def detect_text_direction(text: str) -> TextDirection:
        """
        تشخیص جهت متن
        
        Args:
            text: متن ورودی
            
        Returns:
            جهت متن
        """
        lang = TextUtils.detect_language(text)
        
        # زبان‌های RTL
        rtl_languages = [Language.PERSIAN, Language.ARABIC, Language.HEBREW]
        
        if lang in rtl_languages:
            return TextDirection.RTL
        elif lang == Language.CHINESE or lang == Language.JAPANESE:
            return TextDirection.TTB  # عمودی (در برخی موارد)
        else:
            return TextDirection.LTR
    
    @staticmethod
    def normalize_persian_text(text: str) -> str:
        """
        نرمال‌سازی متن فارسی
        
        Args:
            text: متن فارسی
            
        Returns:
            متن نرمال‌سازی شده
        """
        if not text:
            return text
        
        # جایگزینی کاراکترهای عربی با فارسی
        replacements = {
            'ك': 'ک',
            'ي': 'ی',
            'ة': 'ه',
            'ۀ': 'ه',
            'ؤ': 'و',
            'إ': 'ا',
            'أ': 'ا',
            'آ': 'آ',
            'ٱ': 'ا',
            'ٲ': 'ا',
            'ٳ': 'ا',
            'ٵ': 'ا',
        }
        
        for arabic_char, persian_char in replacements.items():
            text = text.replace(arabic_char, persian_char)
        
        # حذف فاصله‌های اضافی
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def reshape_arabic_text(text: str) -> str:
        """
        شکل‌دهی متن عربی/فارسی برای نمایش صحیح
        
        Args:
            text: متن ورودی
            
        Returns:
            متن شکل‌دهی شده
        """
        try:
            # شکل‌دهی متن عربی
            reshaped_text = arabic_reshaper.reshape(text)
            # اعمال الگوریتم دوطرفه
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except Exception:
            return text
    
    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        """
        محاسبه شباهت بین دو متن
        
        Args:
            text1: متن اول
            text2: متن دوم
            
        Returns:
            میزان شباهت بین ۰ تا ۱
        """
        if not text1 or not text2:
            return 0.0
        
        # نرمال‌سازی متن‌ها
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text1 == text2:
            return 1.0
        
        # استفاده از فاصله لونشتاین
        len1, len2 = len(text1), len(text2)
        max_len = max(len1, len2)
        
        if max_len == 0:
            return 1.0
        
        # ماتریس فاصله
        d = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            d[i][0] = i
        for j in range(len2 + 1):
            d[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if text1[i-1] == text2[j-1] else 1
                d[i][j] = min(
                    d[i-1][j] + 1,      # حذف
                    d[i][j-1] + 1,      # درج
                    d[i-1][j-1] + cost  # جایگزینی
                )
        
        distance = d[len1][len2]
        similarity = 1.0 - (distance / max_len)
        
        return max(0.0, similarity)
    
    @staticmethod
    def extract_words(text: str, language: Optional[Language] = None) -> List[str]:
        """
        استخراج کلمات از متن
        
        Args:
            text: متن ورودی
            language: زبان متن (اختیاری)
            
        Returns:
            لیست کلمات
        """
        if not text:
            return []
        
        if language is None:
            language = TextUtils.detect_language(text)
        
        # الگوهای جداکننده بر اساس زبان
        if language in [Language.PERSIAN, Language.ARABIC]:
            # جداکننده‌های فارسی/عربی
            separators = r'[\s\u200c\u200f،؛:\.\!\?\(\)\[\]\{\}«»""'']+'
        elif language in [Language.CHINESE, Language.JAPANESE]:
            # جداکننده‌های چینی/ژاپنی
            separators = r'[\s，。！？：；「」『』【】（）《》]+'
        else:
            # جداکننده‌های استاندارد
            separators = r'[\s\.,!?;:\(\)\[\]\{\}"'']+'
        
        words = re.split(separators, text)
        words = [w for w in words if w.strip()]
        
        return words
    
    @staticmethod
    def calculate_readability_score(text: str, language: Language = Language.ENGLISH) -> float:
        """
        محاسبه نمره خوانایی متن
        
        Args:
            text: متن ورودی
            language: زبان متن
            
        Returns:
            نمره خوانایی (۰ تا ۱۰۰)
        """
        words = TextUtils.extract_words(text, language)
        sentences = re.split(r'[.!?۔؟۔]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not words or not sentences:
            return 0.0
        
        # تعداد کلمات و جملات
        word_count = len(words)
        sentence_count = len(sentences)
        
        if sentence_count == 0:
            return 0.0
        
        # میانگین طول کلمات (بر اساس حروف)
        avg_word_length = sum(len(word) for word in words) / word_count
        
        # میانگین طول جملات (بر اساس کلمات)
        avg_sentence_length = word_count / sentence_count
        
        # فرمول ساده خوانایی (Flesch Reading Ease)
        if language == Language.ENGLISH:
            # فرمول برای انگلیسی
            score = 206.835 - 1.015 * avg_sentence_length - 84.6 * (avg_word_length / word_count)
        elif language in [Language.PERSIAN, Language.ARABIC]:
            # فرمول تطبیقی برای فارسی/عربی
            score = 200 - 1.2 * avg_sentence_length - 80 * (avg_word_length / word_count)
        else:
            # فرمول عمومی
            score = 180 - 1.1 * avg_sentence_length - 70 * (avg_word_length / word_count)
        
        # محدود کردن نمره بین ۰ تا ۱۰۰
        return max(0.0, min(100.0, score))


class ImageUtils:
    """ابزارهای پردازش تصویر"""
    
    @staticmethod
    def calculate_image_hash(image_data: bytes, hash_size: int = 8) -> str:
        """
        محاسبه هش تصویر برای تشخیص تکراری بودن
        
        Args:
            image_data: داده‌های تصویر
            hash_size: اندازه هش
            
        Returns:
            هش تصویر
        """
        try:
            # بارگذاری تصویر
            image: PILImage = Image.open(io.BytesIO(image_data))
            # تبدیل به خاکستری و تغییر اندازه
            image = image.convert('L').resize((hash_size, hash_size), Image.Resampling.LANCZOS)
            
            # محاسبه میانگین
            pixels = list(image.getdata())
            avg = sum(pixels) / len(pixels)
            
            # ایجاد هش
            hash_value = 0
            for pixel in pixels:
                hash_value = (hash_value << 1) | (1 if pixel > avg else 0)
            
            return hex(hash_value)[2:].zfill(hash_size * hash_size // 4)
            
        except Exception as e:
            # در صورت خطا، هش از داده‌های خام
            return hashlib.md5(image_data).hexdigest()[:16]
    
    @staticmethod
    def image_to_base64(image_data: bytes, format: str = "PNG") -> str:
        """
        تبدیل تصویر به base64
        
        Args:
            image_data: داده‌های تصویر
            format: فرمت خروجی
            
        Returns:
            رشته base64
        """
        try:
            # اگر داده‌ها قبلاً base64 هستند
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                return image_data
            
            # کدگذاری base64
            encoded = base64.b64encode(image_data).decode('utf-8')
            mime_type = f"image/{format.lower()}"
            return f"data:{mime_type};base64,{encoded}"
            
        except Exception:
            return ""
    
    @staticmethod
    def base64_to_image(base64_string: str) -> Optional[bytes]:
        """
        تبدیل base64 به داده‌های تصویر
        
        Args:
            base64_string: رشته base64
            
        Returns:
            داده‌های تصویر یا None
        """
        try:
            # حذف پیشوند data URL اگر وجود دارد
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',', 1)[1]
            
            # دیکد base64
            return base64.b64decode(base64_string)
        except Exception:
            return None
    
    @staticmethod
    def resize_image(image_data: bytes, max_width: int, max_height: int, 
                    quality: int = 85) -> bytes:
        """
        تغییر اندازه تصویر
        
        Args:
            image_data: داده‌های تصویر
            max_width: حداکثر عرض
            max_height: حداکثر ارتفاع
            quality: کیفیت خروجی (برای JPEG)
            
        Returns:
            داده‌های تصویر تغییر اندازه داده شده
        """
        try:
            image: PILImage = Image.open(io.BytesIO(image_data))
            original_width, original_height = image.size
            
            # محاسبه اندازه جدید با حفظ نسبت ابعاد
            ratio = min(max_width / original_width, max_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            
            # تغییر اندازه
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # ذخیره به بایت
            output = io.BytesIO()
            if image.format == 'JPEG':
                resized_image.save(output, format='JPEG', quality=quality, optimize=True)
            else:
                resized_image.save(output, format=image.format or 'PNG', optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            warnings.warn(f"خطا در تغییر اندازه تصویر: {e}")
            return image_data  # بازگشت تصویر اصلی در صورت خطا
    
    @staticmethod
    def convert_image_format(image_data: bytes, target_format: str, 
                           quality: int = 85) -> bytes:
        """
        تبدیل فرمت تصویر
        
        Args:
            image_data: داده‌های تصویر
            target_format: فرمت هدف (JPEG, PNG, WEBP)
            quality: کیفیت (برای فرمت‌های فشرده)
            
        Returns:
            داده‌های تصویر تبدیل شده
        """
        try:
            image: PILImage = Image.open(io.BytesIO(image_data))
            
            # تبدیل به RGB اگر فرمت هدف JPEG است
            if target_format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[3])
                else:
                    background.paste(image)
                image = background
            
            # ذخیره با فرمت جدید
            output = io.BytesIO()
            save_kwargs = {'format': target_format.upper()}
            
            if target_format.upper() in ('JPEG', 'WEBP'):
                save_kwargs['quality'] = str(quality)
                save_kwargs['optimize'] = str(True)
            
            image.save(output, **save_kwargs)
            return output.getvalue()
            
        except Exception as e:
            warnings.warn(f"خطا در تبدیل فرمت تصویر: {e}")
            return image_data
    
    @staticmethod
    def extract_image_metadata(image_data: bytes) -> Dict[str, Any]:
        """
        استخراج متادیتای تصویر
        
        Args:
            image_data: داده‌های تصویر
            
        Returns:
            دیکشنری متادیتا
        """
        metadata: Dict[str, Any] = {
            'format': None,
            'size': (0, 0),
            'mode': None,
            'dpi': (72, 72),
            'has_alpha': False,
            'is_animated': False,
            'color_count': 0
        }
        
        try:
            image: PILImage = Image.open(io.BytesIO(image_data))
            
            metadata['format'] = image.format
            metadata['size'] = image.size
            metadata['mode'] = image.mode
            metadata['dpi'] = image.info.get('dpi', (72, 72))
            metadata['has_alpha'] = image.mode in ('RGBA', 'LA', 'P')
            metadata['is_animated'] = getattr(image, 'is_animated', False)
            
            # شمارش رنگ‌های منحصر به فرد
            if image.mode in ('P', 'L', '1'):
                colors = image.getcolors()
                if colors:
                    metadata['color_count'] = len(colors)
            
            # استخراج EXIF اگر وجود دارد
            if hasattr(image, '_getexif') and image._getexif():
                exif = image._getexif()
                if exif:
                    metadata['exif'] = {}
                    # تگ‌های EXIF مهم
                    exif_tags = {
                        271: 'make',
                        272: 'model',
                        274: 'orientation',
                        306: 'datetime',
                        36867: 'datetime_original',
                        36868: 'datetime_digitized',
                        37378: 'exposure_time',
                        37379: 'f_number',
                        37380: 'exposure_program',
                        37381: 'spectral_sensitivity',
                        37383: 'metering_mode',
                        37384: 'light_source',
                        37385: 'flash',
                        37386: 'focal_length',
                        41987: 'white_balance'
                    }
                    
                    for tag_id, tag_name in exif_tags.items():
                        if tag_id in exif:
                            metadata['exif'][tag_name] = exif[tag_id]
            
        except Exception as e:
            warnings.warn(f"خطا در استخراج متادیتای تصویر: {e}")
        
        return metadata


class FileUtils:
    """ابزارهای کار با فایل"""
    
    @staticmethod
    def safe_filename(filename: str, max_length: int = 255) -> str:
        """
        ایجاد نام فایل امن
        
        Args:
            filename: نام فایل اصلی
            max_length: حداکثر طول نام فایل
            
        Returns:
            نام فایل امن
        """
        # حذف کاراکترهای غیرمجاز
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # حذف فاصله‌های اضافی
        safe_name = re.sub(r'\s+', '_', safe_name)
        
        # محدود کردن طول
        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            name = name[:max_length - len(ext)]
            safe_name = name + ext
        
        return safe_name
    
    @staticmethod
    def get_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
        """
        محاسبه هش فایل
        
        Args:
            filepath: مسیر فایل
            algorithm: الگوریتم هش (md5, sha1, sha256)
            
        Returns:
            هش فایل
        """
        hash_func = getattr(hashlib, algorithm, hashlib.sha256)
        
        with open(filepath, 'rb') as f:
            file_hash = hash_func()
            chunk = f.read(8192)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(8192)
        
        return file_hash.hexdigest()
    
    @staticmethod
    def create_temp_file(data: bytes, suffix: str = '.tmp') -> str:
        """
        ایجاد فایل موقت
        
        Args:
            data: داده‌های فایل
            suffix: پسوند فایل
            
        Returns:
            مسیر فایل موقت
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(data)
            return tmp.name
    
    @staticmethod
    def read_file_chunks(filepath: str, chunk_size: int = 8192):
        """
        خواندن فایل به صورت تکه‌ای
        
        Args:
            filepath: مسیر فایل
            chunk_size: اندازه هر تکه
            
        Yields:
            تکه‌های داده
        """
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    @staticmethod
    def get_file_info(filepath: str) -> Dict[str, Any]:
        """
        دریافت اطلاعات فایل
        
        Args:
            filepath: مسیر فایل
            
        Returns:
            اطلاعات فایل
        """
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"فایل یافت نشد: {filepath}")
        
        stats = path.stat()
        
        return {
            'filename': path.name,
            'extension': path.suffix.lower(),
            'size_bytes': stats.st_size,
            'size_human': FileUtils.format_file_size(stats.st_size),
            'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'accessed': datetime.fromtimestamp(stats.st_atime).isoformat(),
            'is_file': path.is_file(),
            'is_dir': path.is_dir(),
            'absolute_path': str(path.absolute()),
            'parent_dir': str(path.parent),
            'hash_sha256': FileUtils.get_file_hash(filepath, 'sha256'),
            'hash_md5': FileUtils.get_file_hash(filepath, 'md5')
        }
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        فرمت‌بندی اندازه فایل
        
        Args:
            size_bytes: اندازه به بایت
            
        Returns:
            رشته فرمت شده
        """
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        unit_index = 0
        
        size = float(size_bytes)
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.2f} {units[unit_index]}"
    
    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """
        اطمینان از وجود دایرکتوری
        
        Args:
            directory: مسیر دایرکتوری
            
        Returns:
            True اگر موفقیت‌آمیز باشد
        """
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            warnings.warn(f"خطا در ایجاد دایرکتوری: {e}")
            return False


class ValidationUtils:
    """ابزارهای اعتبارسنجی"""
    
    @staticmethod
    def is_valid_pdf(filepath: str) -> Tuple[bool, str]:
        """
        بررسی اعتبار فایل PDF
        
        Args:
            filepath: مسیر فایل PDF
            
        Returns:
            (is_valid, message)
        """
        try:
            path = Path(filepath)
            
            # بررسی وجود فایل
            if not path.exists():
                return False, "فایل یافت نشد"
            
            # بررسی پسوند
            if path.suffix.lower() != '.pdf':
                return False, "پسوند فایل باید .pdf باشد"
            
            # بررسی اندازه فایل
            file_size = path.stat().st_size
            if file_size == 0:
                return False, "فایل خالی است"
            
            if file_size > 500 * 1024 * 1024:  # 500 MB
                return False, "حجم فایل بیش از حد مجاز است (حداکثر 500 مگابایت)"
            
            # بررسی هدر PDF
            with open(filepath, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    return False, "فایل PDF معتبر نیست (هدر نادرست)"
                
                # بررسی تریلر
                f.seek(-128, 2)  # به انتهای فایل برو
                trailer = f.read()
                if b'%%EOF' not in trailer:
                    return False, "فایل PDF معتبر نیست (تریلر نادرست)"
            
            return True, "فایل PDF معتبر است"
            
        except Exception as e:
            return False, f"خطا در بررسی فایل: {str(e)}"
    
    @staticmethod
    def is_valid_image(image_data: bytes) -> Tuple[bool, str]:
        """
        بررسی اعتبار داده‌های تصویر
        
        Args:
            image_data: داده‌های تصویر
            
        Returns:
            (is_valid, message)
        """
        try:
            image: PILImage = Image.open(io.BytesIO(image_data))
            image.verify()  # بررسی اعتبار تصویر
            return True, f"تصویر معتبر ({image.format or 'unknown'})"
        except Exception as e:
            return False, f"داده‌های تصویر معتبر نیستند: {str(e)}"
    
    @staticmethod
    def validate_bbox(bbox: Tuple[float, float, float, float], 
                     page_size: Tuple[float, float]) -> bool:
        """
        اعتبارسنجی محدوده (Bounding Box)
        
        Args:
            bbox: محدوده (x0, y0, x1, y1)
            page_size: اندازه صفحه (width, height)
            
        Returns:
            True اگر محدوده معتبر باشد
        """
        if len(bbox) != 4:
            return False
        
        x0, y0, x1, y1 = bbox
        page_width, page_height = page_size
        
        # بررسی مقادیر عددی
        if not all(isinstance(v, (int, float)) for v in bbox):
            return False
        
        # بررسی محدوده
        if x0 < 0 or y0 < 0 or x1 > page_width or y1 > page_height:
            return False
        
        # بررسی منطقی بودن مختصات
        if x0 >= x1 or y0 >= y1:
            return False
        
        # بررسی اندازه
        width = x1 - x0
        height = y1 - y0
        
        if width <= 0 or height <= 0:
            return False
        
        if width > page_width or height > page_height:
            return False
        
        return True


class PerformanceUtils:
    """ابزارهای اندازه‌گیری عملکرد"""
    
    @staticmethod
    def timeit(func: Callable) -> Callable:
        """
        دکوراتور برای اندازه‌گیری زمان اجرای تابع
        
        Args:
            func: تابع هدف
            
        Returns:
            تابع پوشش داده شده
        """
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed = end_time - start_time
            
            print(f"⏱️  زمان اجرای {func.__name__}: {elapsed:.4f} ثانیه")
            return result
        
        return wrapper
    
    @staticmethod
    def memory_usage() -> float:
        """
        دریافت میزان مصرف حافظه
        
        Returns:
            مصرف حافظه به مگابایت
        """
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return memory_info.rss / 1024 / 1024  # به مگابایت
    
    @staticmethod
    def profile_function(func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        پروفایلینگ تابع
        
        Args:
            func: تابع هدف
            *args: آرگومان‌های تابع
            **kwargs: آرگومان‌های کلیدواژه
            
        Returns:
            اطلاعات پروفایلینگ
        """
        import time
        import tracemalloc
        
        # شروع ردیابی حافظه
        tracemalloc.start()
        
        # زمان شروع
        start_time = time.time()
        
        # اجرای تابع
        result = func(*args, **kwargs)
        
        # زمان پایان
        end_time = time.time()
        
        # دریافت آمار حافظه
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return {
            'result': result,
            'execution_time': end_time - start_time,
            'memory_current_mb': current / 1024 / 1024,
            'memory_peak_mb': peak / 1024 / 1024,
            'success': True
        }


# توابع کمکی عمومی
def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """ادغام دو دیکشنری"""
    result = dict1.copy()
    result.update(dict2)
    return result


def flatten_list(nested_list: List) -> List:
    """تخت کردن لیست تو در تو"""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """تقسیم لیست به تکه‌های کوچک"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """تقسیم امن با جلوگیری از تقسیم بر صفر"""
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float, max_val: float) -> float:
    """محدود کردن مقدار بین حداقل و حداکثر"""
    return max(min_val, min(value, max_val))


def format_bytes(size: float) -> str:
    """فرمت‌بندی بایت به واحدهای خوانا"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


# کلاس برای لاگ‌گیری
class Logger:
    """لاگر ساده"""
    
    def __init__(self, log_file: Optional[str] = None, level: str = 'INFO'):
        """
        مقداردهی اولیه لاگر
        
        Args:
            log_file: مسیر فایل لاگ (اختیاری)
            level: سطح لاگ (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_file = log_file
        self.level = level.upper()
        self.levels = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3}
        
        if log_file:
            FileUtils.ensure_directory(os.path.dirname(log_file))
    
    def log(self, level: str, message: str, **kwargs):
        """
        ثبت لاگ
        
        Args:
            level: سطح لاگ
            message: پیام
            **kwargs: اطلاعات اضافی
        """
        if self.levels.get(level.upper(), 99) < self.levels.get(self.level, 0):
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level.upper()}] {message}"
        
        if kwargs:
            log_message += f" | {json.dumps(kwargs, ensure_ascii=False)}"
        
        # چاپ در کنسول
        print(log_message)
        
        # ذخیره در فایل
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
    
    def debug(self, message: str, **kwargs):
        """ثبت لاگ سطح DEBUG"""
        self.log('DEBUG', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """ثبت لاگ سطح INFO"""
        self.log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """ثبت لاگ سطح WARNING"""
        self.log('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """ثبت لاگ سطح ERROR"""
        self.log('ERROR', message, **kwargs)


# # نمونه لاگر پیش‌فرض
# logger = Logger()


# if __name__ == "__main__":
#     # تست توابع
#     text = "این یک متن فارسی است. This is English text."
    
#     print("🔍 تست تشخیص زبان:")
#     lang = TextUtils.detect_language(text)
#     print(f"   زبان تشخیص داده شده: {lang}")
    
#     print("\n🧭 تست تشخیص جهت متن:")
#     direction = TextUtils.detect_text_direction(text)
#     print(f"   جهت متن: {direction}")
    
#     print("\n📏 تست BoundingBox:")
#     bbox = BoundingBox(10, 20, 100, 200)
#     print(f"   BBox: {bbox}")
#     print(f"   عرض: {bbox.width}")
#     print(f"   ارتفاع: {bbox.height}")
#     print(f"   مساحت: {bbox.area}")
#     print(f"   مرکز: {bbox.center}")
    
#     print("\n📊 تست اعتبارسنجی:")
#     is_valid, msg = ValidationUtils.is_valid_pdf("test.pdf")
#     print(f"   اعتبار PDF: {is_valid} - {msg}")
