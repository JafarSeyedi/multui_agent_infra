#!/usr/bin/env python3
"""
Helper Tools module for PDF Parser
Includes utility functions for text, image processing, and helper operations
"""
import base64
import hashlib
import io
import json
import math
import os
import re
import tempfile
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import arabic_reshaper  # type: ignore[import-untyped]
from bidi.algorithm import get_display  # type: ignore[import-untyped]
from PIL import Image
from PIL.Image import Image as PILImage


class TextDirection(Enum):
    """Text direction"""
    LTR = "ltr"  # Left to right
    RTL = "rtl"  # Right to left
    TTB = "ttb"  # Top to bottom (vertical)


class Language(Enum):
    """Supported languages"""
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
    """Rectangular bounding box"""
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        """Bounding box width"""
        return abs(self.x1 - self.x0)

    @property
    def height(self) -> float:
        """Bounding box height"""
        return abs(self.y1 - self.y0)

    @property
    def area(self) -> float:
        """Bounding box area"""
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        """Bounding box center"""
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)

    def intersects(self, other: 'BoundingBox', threshold: float = 0.1) -> bool:
        """
        Check intersection of two bounding boxes
        
        Args:
            other: other bounding box
            threshold: intersection threshold (area ratio)
            
        Returns:
            True if they intersect
        """
        # Calculate intersection bounding box
        inter_x0 = max(self.x0, other.x0)
        inter_y0 = max(self.y0, other.y0)
        inter_x1 = min(self.x1, other.x1)
        inter_y1 = min(self.y1, other.y1)

        if inter_x0 < inter_x1 and inter_y0 < inter_y1:
            # Calculate intersection area
            inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
            # Calculate minimum area of two boxes
            min_area = min(self.area, other.area)
            # Check threshold
            return (inter_area / min_area) >= threshold
        return False

    def contains(self, point: tuple[float, float]) -> bool:
        """
        Check if point is inside bounding box
        
        Args:
            point: point (x, y)
            
        Returns:
            True if point is inside
        """
        x, y = point
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1

    def distance_to(self, other: 'BoundingBox') -> float:
        """
        Calculate distance between centers of two bounding boxes
        
        Args:
            other: other bounding box
            
        Returns:
            Euclidean distance
        """
        x1, y1 = self.center
        x2, y2 = other.center
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def to_tuple(self) -> tuple[float, float, float, float]:
        """Convert to tuple"""
        return (self.x0, self.y0, self.x1, self.y1)

    @classmethod
    def from_tuple(cls, bbox_tuple: tuple[float, float, float, float]) -> 'BoundingBox':
        """Create from tuple"""
        return cls(*bbox_tuple)

    def __str__(self) -> str:
        return f"BBox({self.x0:.2f}, {self.y0:.2f}, {self.x1:.2f}, {self.y1:.2f})"


class TextUtils:
    """Text processing tools"""

    @staticmethod
    def detect_language(text: str) -> Language:
        """
        Detect text language
        
        Args:
            text: input text
            
        Returns:
            Detected language
        """
        if not text or not text.strip():
            return Language.UNKNOWN

        text = text.strip()

        # Various language patterns
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

        # Count characters per language
        counts = {}
        for lang, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                counts[lang] = len(matches)

        if not counts:
            return Language.UNKNOWN

        # Language with most characters
        detected_lang = max(counts.items(), key=lambda x: x[1])[0]

        # Detect Persian vs Arabic difference (simple)
        if detected_lang in [Language.PERSIAN, Language.ARABIC]:
            # Persian-specific words
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
        Detect text direction
        
        Args:
            text: input text
            
        Returns:
            Text direction
        """
        lang = TextUtils.detect_language(text)

        # RTL languages
        rtl_languages = [Language.PERSIAN, Language.ARABIC, Language.HEBREW]

        if lang in rtl_languages:
            return TextDirection.RTL
        elif lang == Language.CHINESE or lang == Language.JAPANESE:
            return TextDirection.TTB  # Vertical (in some cases)
        else:
            return TextDirection.LTR

    @staticmethod
    def normalize_persian_text(text: str) -> str:
        """
        Normalize Persian text
        
        Args:
            text: Persian text
            
        Returns:
            Normalized text
        """
        if not text:
            return text

        # Replace Arabic characters with Persian
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

        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @staticmethod
    def reshape_arabic_text(text: str) -> str:
        """
        Reshape Arabic/Persian text for correct display
        
        Args:
            text: input text
            
        Returns:
            Reshaped text
        """
        try:
            # Reshape Arabic text
            reshaped_text = arabic_reshaper.reshape(text)
            # Apply bidirectional algorithm
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except Exception:
            return text

    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts
        
        Args:
            text1: first text
            text2: second text
            
        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0

        # Normalize texts
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()

        if text1 == text2:
            return 1.0

        # Use Levenshtein distance
        len1, len2 = len(text1), len(text2)
        max_len = max(len1, len2)

        if max_len == 0:
            return 1.0

        # Distance matrix
        d = [[0] * (len2 + 1) for _ in range(len1 + 1)]

        for i in range(len1 + 1):
            d[i][0] = i
        for j in range(len2 + 1):
            d[0][j] = j

        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if text1[i-1] == text2[j-1] else 1
                d[i][j] = min(
                    d[i-1][j] + 1,      # Delete
                    d[i][j-1] + 1,      # Insert
                    d[i-1][j-1] + cost  # Replace
                )

        distance = d[len1][len2]
        similarity = 1.0 - (distance / max_len)

        return max(0.0, similarity)

    @staticmethod
    def extract_words(text: str, language: Language | None = None) -> list[str]:
        """
        Extract words from text
        
        Args:
            text: input text
            language: text language (optional)
            
        Returns:
            List of words
        """
        if not text:
            return []

        if language is None:
            language = TextUtils.detect_language(text)

        # Separator patterns by language
        if language in [Language.PERSIAN, Language.ARABIC]:
            # Persian/Arabic separators
            separators = r'[\s\u200c\u200f،؛:\.\!\?\(\)\[\]\{\}«»""'']+'
        elif language in [Language.CHINESE, Language.JAPANESE]:
            # Chinese/Japanese separators
            separators = r'[\s，。！？：；「」『』【】（）《》]+'
        else:
            # Standard separators
            separators = r'[\s\.,!?;:\(\)\[\]\{\}"'']+'

        words = re.split(separators, text)
        words = [w for w in words if w.strip()]

        return words

    @staticmethod
    def calculate_readability_score(text: str, language: Language = Language.ENGLISH) -> float:
        """
        Calculate text readability score
        
        Args:
            text: input text
            language: text language
            
        Returns:
            Readability score (0 to 100)
        """
        words = TextUtils.extract_words(text, language)
        sentences = re.split(r'[.!?۔؟۔]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not words or not sentences:
            return 0.0

        # Word and sentence counts
        word_count = len(words)
        sentence_count = len(sentences)

        if sentence_count == 0:
            return 0.0

        # Average word length (by characters)
        avg_word_length = sum(len(word) for word in words) / word_count

        # Average sentence length (by words)
        avg_sentence_length = word_count / sentence_count

        # Simple readability formula (Flesch Reading Ease)
        if language == Language.ENGLISH:
            # Formula for English
            score = 206.835 - 1.015 * avg_sentence_length - 84.6 * (avg_word_length / word_count)
        elif language in [Language.PERSIAN, Language.ARABIC]:
            # Adapted formula for Persian/Arabic
            score = 200 - 1.2 * avg_sentence_length - 80 * (avg_word_length / word_count)
        else:
            # General formula
            score = 180 - 1.1 * avg_sentence_length - 70 * (avg_word_length / word_count)

        # Clamp score between 0 and 100
        return max(0.0, min(100.0, score))


class ImageUtils:
    """Image processing tools"""

    @staticmethod
    def calculate_image_hash(image_data: bytes, hash_size: int = 8) -> str:
        """
        Calculate image hash for duplicate detection
        
        Args:
            image_data: image data
            hash_size: hash size
            
        Returns:
            Image hash
        """
        try:
            # Load image
            image: PILImage = Image.open(io.BytesIO(image_data))
            # Convert to grayscale and resize
            image = image.convert('L').resize((hash_size, hash_size), Image.Resampling.LANCZOS)

            # Calculate average
            pixels = list(image.getdata())
            avg = sum(pixels) / len(pixels)

            # Create hash
            hash_value = 0
            for pixel in pixels:
                hash_value = (hash_value << 1) | (1 if pixel > avg else 0)

            return hex(hash_value)[2:].zfill(hash_size * hash_size // 4)

        except Exception:
            # On error, hash from raw data
            return hashlib.md5(image_data).hexdigest()[:16]

    @staticmethod
    def image_to_base64(image_data: bytes, format: str = "PNG") -> str:
        """
        Convert image to base64
        
        Args:
            image_data: image data
            format: output format
            
        Returns:
            base64 string
        """
        try:
            # If data is already base64
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                return image_data

            # Base64 encode
            encoded = base64.b64encode(image_data).decode('utf-8')
            mime_type = f"image/{format.lower()}"
            return f"data:{mime_type};base64,{encoded}"

        except Exception:
            return ""

    @staticmethod
    def base64_to_image(base64_string: str) -> bytes | None:
        """
        Convert base64 to image data
        
        Args:
            base64_string: base64 string
            
        Returns:
            Image data or None
        """
        try:
            # Remove data URL prefix if present
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',', 1)[1]

            # Decode base64
            return base64.b64decode(base64_string)
        except Exception:
            return None

    @staticmethod
    def resize_image(image_data: bytes, max_width: int, max_height: int,
                    quality: int = 85) -> bytes:
        """
        Resize image
        
        Args:
            image_data: image data
            max_width: maximum width
            max_height: maximum height
            quality: output quality (for JPEG)
            
        Returns:
            Resized image data
        """
        try:
            image: PILImage = Image.open(io.BytesIO(image_data))
            original_width, original_height = image.size

            # Calculate new size maintaining aspect ratio
            ratio = min(max_width / original_width, max_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)

            # Resize
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Save to bytes
            output = io.BytesIO()
            if image.format == 'JPEG':
                resized_image.save(output, format='JPEG', quality=quality, optimize=True)
            else:
                resized_image.save(output, format=image.format or 'PNG', optimize=True)

            return output.getvalue()

        except Exception as e:
            warnings.warn(f"Error resizing image: {e}")
            return image_data  # Return original image on error

    @staticmethod
    def convert_image_format(image_data: bytes, target_format: str,
                           quality: int = 85) -> bytes:
        """
        Convert image format
        
        Args:
            image_data: image data
            target_format: target format (JPEG, PNG, WEBP)
            quality: quality (for compressed formats)
            
        Returns:
            Converted image data
        """
        try:
            image: PILImage = Image.open(io.BytesIO(image_data))

            # Convert to RGB if target format is JPEG
            if target_format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[3])
                else:
                    background.paste(image)
                image = background

            # Save with new format
            output = io.BytesIO()
            save_kwargs = {'format': target_format.upper()}

            if target_format.upper() in ('JPEG', 'WEBP'):
                save_kwargs['quality'] = str(quality)
                save_kwargs['optimize'] = str(True)

            image.save(output, **save_kwargs)
            return output.getvalue()

        except Exception as e:
            warnings.warn(f"Error converting image format: {e}")
            return image_data

    @staticmethod
    def extract_image_metadata(image_data: bytes) -> dict[str, Any]:
        """
        Extract image metadata
        
        Args:
            image_data: image data
            
        Returns:
            Metadata dictionary
        """
        metadata: dict[str, Any] = {
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

            # Count unique colors
            if image.mode in ('P', 'L', '1'):
                colors = image.getcolors()
                if colors:
                    metadata['color_count'] = len(colors)

            # Extract EXIF if present
            if hasattr(image, '_getexif') and image._getexif():
                exif = image._getexif()
                if exif:
                    metadata['exif'] = {}
                    # Important EXIF tags
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
            warnings.warn(f"Error extracting image metadata: {e}")

        return metadata


class FileUtils:
    """File utility tools"""

    @staticmethod
    def safe_filename(filename: str, max_length: int = 255) -> str:
        """
        Create safe filename
        
        Args:
            filename: original filename
            max_length: maximum filename length
            
        Returns:
            Safe filename
        """
        # Remove invalid characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)

        # Remove extra spaces
        safe_name = re.sub(r'\s+', '_', safe_name)

        # Limit length
        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            name = name[:max_length - len(ext)]
            safe_name = name + ext

        return safe_name

    @staticmethod
    def get_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
        """
        Calculate file hash
        
        Args:
            filepath: file path
            algorithm: hash algorithm (md5, sha1, sha256)
            
        Returns:
            File hash
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
        Create temporary file
        
        Args:
            data: file data
            suffix: file extension
            
        Returns:
            Temporary file path
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(data)
            return tmp.name

    @staticmethod
    def read_file_chunks(filepath: str, chunk_size: int = 8192):
        """
        Read file in chunks
        
        Args:
            filepath: file path
            chunk_size: chunk size
            
        Yields:
            Data chunks
        """
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    @staticmethod
    def get_file_info(filepath: str) -> dict[str, Any]:
        """
        Get file information
        
        Args:
            filepath: file path
            
        Returns:
            File information
        """
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

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
        Format file size
        
        Args:
            size_bytes: file size in bytes
            
        Returns:
            Formatted string
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
        Ensure directory exists
        
        Args:
            directory: directory path
            
        Returns:
            True if successful
        """
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            warnings.warn(f"Error creating directory: {e}")
            return False


class ValidationUtils:
    """Validation tools"""

    @staticmethod
    def is_valid_pdf(filepath: str) -> tuple[bool, str]:
        """
        Validate PDF file
        
        Args:
            filepath: PDF file path
            
        Returns:
            (is_valid, message)
        """
        try:
            path = Path(filepath)

            # Check file exists
            if not path.exists():
                return False, "File not found"

            # Check extension
            if path.suffix.lower() != '.pdf':
                return False, "File extension must be .pdf"

            # Check file size
            file_size = path.stat().st_size
            if file_size == 0:
                return False, "File is empty"

            if file_size > 500 * 1024 * 1024:  # 500 MB
                return False, "File size exceeds maximum allowed (500 MB)"

            # Check PDF header
            with open(filepath, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    return False, "File is not a valid PDF (invalid header)"

                # Check trailer
                f.seek(-128, 2)  # go to end of file
                trailer = f.read()
                if b'%%EOF' not in trailer:
                    return False, "File is not a valid PDF (invalid trailer)"

            return True, "PDF file is valid"

        except Exception as e:
            return False, f"Error checking file: {str(e)}"

    @staticmethod
    def is_valid_image(image_data: bytes) -> tuple[bool, str]:
        """
        Validate image data
        
        Args:
            image_data: image data
            
        Returns:
            (is_valid, message)
        """
        try:
            image: PILImage = Image.open(io.BytesIO(image_data))
            image.verify()  # Verify image validity
            return True, f"تصویر معتبر ({image.format or 'unknown'})"
        except Exception as e:
            return False, f"Image data is not valid: {str(e)}"

    @staticmethod
    def validate_bbox(bbox: tuple[float, float, float, float],
                     page_size: tuple[float, float]) -> bool:
        """
        Validate bounding box
        
        Args:
            bbox: bounding box (x0, y0, x1, y1)
            page_size: page size (width, height)
            
        Returns:
            True if bounding box is valid
        """
        if len(bbox) != 4:
            return False

        x0, y0, x1, y1 = bbox
        page_width, page_height = page_size

        # Check numeric values
        if not all(isinstance(v, (int, float)) for v in bbox):
            return False

        # Check range
        if x0 < 0 or y0 < 0 or x1 > page_width or y1 > page_height:
            return False

        # Check coordinate logic
        if x0 >= x1 or y0 >= y1:
            return False

        # Check size
        width = x1 - x0
        height = y1 - y0

        if width <= 0 or height <= 0:
            return False

        if width > page_width or height > page_height:
            return False

        return True


class PerformanceUtils:
    """Performance measurement tools"""

    @staticmethod
    def timeit(func: Callable) -> Callable:
        """
        Decorator for measuring function execution time
        
        Args:
            func: target function
            
        Returns:
            Wrapped function
        """
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed = end_time - start_time

            print(f"⏱️  زمان اجرای {func.__name__}: {elapsed:.4f} seconds")
            return result

        return wrapper

    @staticmethod
    def memory_usage() -> float:
        """
        Get memory usage
        
        Returns:
            Memory usage in megabytes
        """
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return memory_info.rss / 1024 / 1024  # In megabytes

    @staticmethod
    def profile_function(func: Callable, *args, **kwargs) -> dict[str, Any]:
        """
        Profile function
        
        Args:
            func: target function
            *args: function arguments
            **kwargs: keyword arguments
            
        Returns:
            Profiling information
        """
        import time
        import tracemalloc

        # Start memory tracking
        tracemalloc.start()

        # Start time
        start_time = time.time()

        # Execute function
        result = func(*args, **kwargs)

        # End time
        end_time = time.time()

        # Get memory statistics
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            'result': result,
            'execution_time': end_time - start_time,
            'memory_current_mb': current / 1024 / 1024,
            'memory_peak_mb': peak / 1024 / 1024,
            'success': True
        }


# General helper functions
def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """Merge two dictionaries"""
    result = dict1.copy()
    result.update(dict2)
    return result


def flatten_list(nested_list: list) -> list:
    """Flatten nested list"""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def chunk_list(lst: list, chunk_size: int) -> list[list]:
    """Split list into smaller chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division preventing division by zero"""
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between minimum and maximum"""
    return max(min_val, min(value, max_val))


def format_bytes(size: float) -> str:
    """Format bytes to human-readable units"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


# Logger class
class Logger:
    """Simple logger"""

    def __init__(self, log_file: str | None = None, level: str = 'INFO'):
        """
        Initialize logger
        
        Args:
            log_file: log file path (optional)
            level: log level (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_file = log_file
        self.level = level.upper()
        self.levels = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3}

        if log_file:
            FileUtils.ensure_directory(os.path.dirname(log_file))

    def log(self, level: str, message: str, **kwargs):
        """
        Log message
        
        Args:
            level: log level
            message: log message
            **kwargs: additional information
        """
        if self.levels.get(level.upper(), 99) < self.levels.get(self.level, 0):
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level.upper()}] {message}"

        if kwargs:
            log_message += f" | {json.dumps(kwargs, ensure_ascii=False)}"

        # Print to console
        print(log_message)

        # Save to file
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')

    def debug(self, message: str, **kwargs):
        """Log DEBUG level message"""
        self.log('DEBUG', message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log INFO level message"""
        self.log('INFO', message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log WARNING level message"""
        self.log('WARNING', message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log ERROR level message"""
        self.log('ERROR', message, **kwargs)


# # Default logger instance
# logger = Logger()


# if __name__ == "__main__":
#     # Test functions
#     text = "This is a Persian text. This is English text."

#     print("🔍 Test language detection:")
#     lang = TextUtils.detect_language(text)
#     print(f"   Detected language: {lang}")

#     print("\n🧭 Test text direction:")
#     direction = TextUtils.detect_text_direction(text)
#     print(f"   Text direction: {direction}")

#     print("\n📏 Test BoundingBox:")
#     bbox = BoundingBox(10, 20, 100, 200)
#     print(f"   BBox: {bbox}")
#     print(f"   Width: {bbox.width}")
#     print(f"   Height: {bbox.height}")
#     print(f"   Area: {bbox.area}")
#     print(f"   Center: {bbox.center}")

#     print("\n📊 Test Validation:")
#     is_valid, msg = ValidationUtils.is_valid_pdf("test.pdf")
#     print(f"   PDF validity: {is_valid} - {msg}")
