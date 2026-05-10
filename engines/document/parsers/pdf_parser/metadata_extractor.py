#!/usr/bin/env python3
"""
metadata_extractor.py - استخراج متادیتا از فایل‌های PDF
ماژول استخراج اطلاعات متادیتا، XMP، و اطلاعات فنی PDF
"""
import hashlib
import json
import mimetypes
import os
import re
import warnings
import xml.etree.ElementTree as ET
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Any

# برای پردازش XMP
try:
    import defusedxml.ElementTree as safe_ET  # type: ignore[import-untyped]
    ET = safe_ET
except ImportError:
    pass

# برای پردازش PDF
try:
    import PyPDF2  # type: ignore[import-not-found]
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber  # type: ignore[import-not-found]
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import pikepdf  # type: ignore[import-not-found]
    HAS_PIKEPDF = True
except ImportError:
    HAS_PIKEPDF = False


class MetadataType(Enum):
    """انواع متادیتا"""
    BASIC = "basic"
    XMP = "xmp"
    TECHNICAL = "technical"
    SECURITY = "security"
    CUSTOM = "custom"
    EMBEDDED = "embedded"


class PDFVersion(Enum):
    """نسخه‌های PDF"""
    PDF_1_0 = "1.0"
    PDF_1_1 = "1.1"
    PDF_1_2 = "1.2"
    PDF_1_3 = "1.3"
    PDF_1_4 = "1.4"
    PDF_1_5 = "1.5"
    PDF_1_6 = "1.6"
    PDF_1_7 = "1.7"
    PDF_2_0 = "2.0"


class PDFConformance(Enum):
    """سطوح انطباق PDF"""
    PDF_A_1A = "PDF/A-1a"
    PDF_A_1B = "PDF/A-1b"
    PDF_A_2A = "PDF/A-2a"
    PDF_A_2B = "PDF/A-2b"
    PDF_A_3A = "PDF/A-3a"
    PDF_A_3B = "PDF/A-3b"
    PDF_UA_1 = "PDF/UA-1"
    PDF_X_1A = "PDF/X-1a"
    PDF_X_3 = "PDF/X-3"
    PDF_X_4 = "PDF/X-4"
    PDF_E_1 = "PDF/E-1"


@dataclass
class PDFMetadata:
    """کلاس اصلی متادیتای PDF"""

    # اطلاعات پایه
    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: str | None = None
    creator: str | None = None
    producer: str | None = None
    creation_date: datetime | None = None
    modification_date: datetime | None = None

    # اطلاعات فنی
    pdf_version: str | None = None
    page_count: int | None = None
    file_size: int | None = None
    file_hash_md5: str | None = None
    file_hash_sha256: str | None = None
    mime_type: str | None = None

    # اطلاعات امنیتی
    encrypted: bool = False
    encryption_type: str | None = None
    permissions: list[str] = field(default_factory=list)
    can_print: bool = True
    can_modify: bool = True
    can_copy: bool = True
    can_annotate: bool = True

    # اطلاعات ساختاری
    tagged: bool = False
    linearized: bool = False
    has_attachments: bool = False
    has_forms: bool = False
    has_javascript: bool = False
    has_embedded_files: bool = False

    # اطلاعات XMP
    xmp_metadata: dict[str, Any] = field(default_factory=dict)

    # اطلاعات فونت‌ها
    fonts: list[dict[str, Any]] = field(default_factory=list)

    # اطلاعات رنگ
    color_spaces: list[str] = field(default_factory=list)

    # اطلاعات تصاویر
    image_count: int = 0
    image_formats: dict[str, int] = field(default_factory=dict)

    # اطلاعات لایه‌بندی
    layers: list[str] = field(default_factory=list)

    # اطلاعات سفارشی
    custom_metadata: dict[str, Any] = field(default_factory=dict)

    # اطلاعات انطباق
    conformance: str | None = None
    validation_errors: list[str] = field(default_factory=list)

    # اطلاعات جغرافیایی
    geolocation: dict[str, float] | None = None

    # اطلاعات حقوقی
    copyright: str | None = None
    license: str | None = None
    rights: str | None = None

    # اطلاعات زبان
    language: str | None = None
    languages: list[str] = field(default_factory=list)

    # اطلاعات دسترسی
    accessibility: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """تبدیل به دیکشنری"""
        result = asdict(self)

        # تبدیل datetime به string
        if result.get('creation_date'):
            result['creation_date'] = result['creation_date'].isoformat()
        if result.get('modification_date'):
            result['modification_date'] = result['modification_date'].isoformat()

        return result

    def to_json(self, indent: int = 2) -> str:
        """تبدیل به JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def get_summary(self) -> dict[str, Any]:
        """دریافت خلاصه متادیتا"""
        return {
            "title": self.title,
            "author": self.author,
            "page_count": self.page_count,
            "file_size": self.file_size,
            "pdf_version": self.pdf_version,
            "encrypted": self.encrypted,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None,
            "modification_date": self.modification_date.isoformat() if self.modification_date else None,
        }


class PDFMetadataExtractor:
    """کلاس اصلی استخراج متادیتا از PDF"""

    def __init__(self, pdf_path: str | None = None, pdf_bytes: bytes | None = None):
        """
        مقداردهی اولیه استخراج‌کننده متادیتا
        
        Args:
            pdf_path: مسیر فایل PDF
            pdf_bytes: داده‌های PDF به صورت بایت
        """
        self.pdf_path = pdf_path
        self.pdf_bytes = pdf_bytes
        self.metadata = PDFMetadata()

        if pdf_path and pdf_bytes:
            raise ValueError("فقط یکی از pdf_path یا pdf_bytes باید مشخص شود")

        if not pdf_path and not pdf_bytes:
            raise ValueError("یکی از pdf_path یا pdf_bytes باید مشخص شود")

    def extract_all(self) -> PDFMetadata:
        """استخراج تمام متادیتاها"""
        try:
            # استخراج اطلاعات پایه
            self._extract_basic_metadata()

            # استخراج اطلاعات فنی
            self._extract_technical_metadata()

            # استخراج اطلاعات امنیتی
            self._extract_security_metadata()

            # استخراج اطلاعات XMP
            self._extract_xmp_metadata()

            # استخراج اطلاعات ساختاری
            self._extract_structural_metadata()

            # استخراج اطلاعات فونت‌ها
            self._extract_font_metadata()

            # استخراج اطلاعات تصاویر
            self._extract_image_metadata()

            # استخراج اطلاعات انطباق
            self._extract_conformance_metadata()

            # استخراج اطلاعات سفارشی
            self._extract_custom_metadata()

            # استخراج اطلاعات دسترسی
            self._extract_accessibility_metadata()

            return self.metadata

        except Exception as e:
            raise PDFMetadataError(f"خطا در استخراج متادیتا: {str(e)}")

    def _extract_basic_metadata(self):
        """استخراج متادیتای پایه"""
        if HAS_PYPDF2:
            self._extract_with_pypdf2()
        elif HAS_PIKEPDF:
            self._extract_with_pikepdf()
        elif HAS_PDFPLUMBER:
            self._extract_with_pdfplumber()
        else:
            self._extract_with_binary_scan()

    def _extract_with_pypdf2(self):
        """استخراج با PyPDF2"""
        try:
            if self.pdf_path:
                with open(self.pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
            else:
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(self.pdf_bytes))

            # اطلاعات پایه
            info = pdf_reader.metadata
            if info:
                self.metadata.title = info.get('/Title')
                self.metadata.author = info.get('/Author')
                self.metadata.subject = info.get('/Subject')
                self.metadata.keywords = info.get('/Keywords')
                self.metadata.creator = info.get('/Creator')
                self.metadata.producer = info.get('/Producer')

                # تاریخ‌ها
                creation_date = info.get('/CreationDate')
                if creation_date:
                    self.metadata.creation_date = self._parse_pdf_date(creation_date)

                mod_date = info.get('/ModDate')
                if mod_date:
                    self.metadata.modification_date = self._parse_pdf_date(mod_date)

            # اطلاعات فنی
            self.metadata.pdf_version = pdf_reader.pdf_header
            self.metadata.page_count = len(pdf_reader.pages)
            self.metadata.encrypted = pdf_reader.is_encrypted

            if pdf_reader.is_encrypted:
                self.metadata.encryption_type = "Standard" if hasattr(pdf_reader, '_encryption') else "Unknown"

                # بررسی مجوزها
                if hasattr(pdf_reader, '_encryption'):
                    encrypt = pdf_reader._encryption
                    if hasattr(encrypt, 'P'):
                        permissions = int(encrypt.P)
                        self._parse_permissions(permissions)

        except Exception as e:
            warnings.warn(f"خطا در استخراج با PyPDF2: {str(e)}")

    def _extract_with_pikepdf(self):
        """استخراج با pikepdf"""
        try:
            if self.pdf_path:
                pdf = pikepdf.Pdf.open(self.pdf_path)
            else:
                import io
                pdf = pikepdf.Pdf.open(io.BytesIO(self.pdf_bytes))

            # اطلاعات پایه
            if '/Info' in pdf.trailer:
                info = pdf.trailer['/Info']

                if '/Title' in info:
                    self.metadata.title = str(info['/Title'])
                if '/Author' in info:
                    self.metadata.author = str(info['/Author'])
                if '/Subject' in info:
                    self.metadata.subject = str(info['/Subject'])
                if '/Keywords' in info:
                    self.metadata.keywords = str(info['/Keywords'])
                if '/Creator' in info:
                    self.metadata.creator = str(info['/Creator'])
                if '/Producer' in info:
                    self.metadata.producer = str(info['/Producer'])

                # تاریخ‌ها
                if '/CreationDate' in info:
                    creation_date = str(info['/CreationDate'])
                    self.metadata.creation_date = self._parse_pdf_date(creation_date)

                if '/ModDate' in info:
                    mod_date = str(info['/ModDate'])
                    self.metadata.modification_date = self._parse_pdf_date(mod_date)

            # اطلاعات فنی
            self.metadata.pdf_version = str(pdf.pdf_version)
            self.metadata.page_count = len(pdf.pages)
            self.metadata.encrypted = pdf.is_encrypted

            if pdf.is_encrypted:
                self.metadata.encryption_type = "Standard"

                # بررسی مجوزها
                if hasattr(pdf, 'permissions'):
                    perms = pdf.permissions
                    self._parse_pikepdf_permissions(perms)

            # بررسی XMP
            self._extract_xmp_from_pikepdf(pdf)

            pdf.close()

        except Exception as e:
            warnings.warn(f"خطا در استخراج با pikepdf: {str(e)}")

    def _extract_with_pdfplumber(self):
        """استخراج با pdfplumber"""
        try:
            if self.pdf_path:
                pdf = pdfplumber.open(self.pdf_path)
            else:
                import io
                pdf = pdfplumber.open(io.BytesIO(self.pdf_bytes))

            # اطلاعات پایه از metadata
            metadata = pdf.metadata
            if metadata:
                self.metadata.title = metadata.get('Title')
                self.metadata.author = metadata.get('Author')
                self.metadata.subject = metadata.get('Subject')
                self.metadata.keywords = metadata.get('Keywords')
                self.metadata.creator = metadata.get('Creator')
                self.metadata.producer = metadata.get('Producer')

                # تاریخ‌ها
                creation_date = metadata.get('CreationDate')
                if creation_date:
                    self.metadata.creation_date = self._parse_pdf_date(creation_date)

                mod_date = metadata.get('ModDate')
                if mod_date:
                    self.metadata.modification_date = self._parse_pdf_date(mod_date)

            # اطلاعات فنی
            self.metadata.page_count = len(pdf.pages)

            pdf.close()

        except Exception as e:
            warnings.warn(f"خطا در استخراج با pdfplumber: {str(e)}")

    def _extract_with_binary_scan(self):
        """استخراج با اسکن باینری (بدون وابستگی)"""
        try:
            if self.pdf_path:
                with open(self.pdf_path, 'rb') as file:
                    data = file.read()
            else:
                data = self.pdf_bytes

            # جستجوی متادیتا در داده‌های باینری
            self._scan_binary_for_metadata(data)

        except Exception as e:
            warnings.warn(f"خطا در استخراج با اسکن باینری: {str(e)}")

    def _extract_technical_metadata(self):
        """استخراج اطلاعات فنی"""
        try:
            if self.pdf_path:
                # اطلاعات فایل
                file_stat = os.stat(self.pdf_path)
                self.metadata.file_size = file_stat.st_size

                # محاسبه هش
                with open(self.pdf_path, 'rb') as file:
                    file_data = file.read()
                    self.metadata.file_hash_md5 = hashlib.md5(file_data).hexdigest()
                    self.metadata.file_hash_sha256 = hashlib.sha256(file_data).hexdigest()

                # نوع MIME
                mime_type, _ = mimetypes.guess_type(self.pdf_path)
                self.metadata.mime_type = mime_type or 'application/pdf'

            elif self.pdf_bytes:
                self.metadata.file_size = len(self.pdf_bytes)
                self.metadata.file_hash_md5 = hashlib.md5(self.pdf_bytes).hexdigest()
                self.metadata.file_hash_sha256 = hashlib.sha256(self.pdf_bytes).hexdigest()
                self.metadata.mime_type = 'application/pdf'

            # تشخیص نسخه PDF از هدر
            if not self.metadata.pdf_version:
                if self.pdf_path:
                    with open(self.pdf_path, 'rb') as file:
                        header = file.read(20).decode('ascii', errors='ignore')
                else:
                    header = self.pdf_bytes[:20].decode('ascii', errors='ignore')

                version_match = re.search(r'%PDF-(\d\.\d)', header)
                if version_match:
                    self.metadata.pdf_version = version_match.group(1)

        except Exception as e:
            warnings.warn(f"خطا در استخراج اطلاعات فنی: {str(e)}")

    def _extract_security_metadata(self):
        """استخراج اطلاعات امنیتی"""
        try:
            if HAS_PYPDF2:
                if self.pdf_path:
                    with open(self.pdf_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                else:
                    import io
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(self.pdf_bytes))

                self.metadata.encrypted = pdf_reader.is_encrypted

                if pdf_reader.is_encrypted:
                    # تشخیص نوع رمزگذاری
                    if hasattr(pdf_reader, '_encryption'):
                        encrypt = pdf_reader._encryption

                        if hasattr(encrypt, 'V'):
                            v = encrypt.V
                            if v == 1:
                                self.metadata.encryption_type = "RC4 (40-bit)"
                            elif v == 2:
                                self.metadata.encryption_type = "RC4 (128-bit)"
                            elif v == 3:
                                self.metadata.encryption_type = "AES (128-bit)"
                            elif v == 4:
                                self.metadata.encryption_type = "AES (256-bit)"
                            else:
                                self.metadata.encryption_type = f"Unknown (V={v})"

                        # بررسی مجوزها
                        if hasattr(encrypt, 'P'):
                            permissions = int(encrypt.P)
                            self._parse_permissions(permissions)

        except Exception as e:
            warnings.warn(f"خطا در استخراج اطلاعات امنیتی: {str(e)}")

    def _extract_xmp_metadata(self):
        """استخراج متادیتای XMP"""
        try:
            if self.pdf_path:
                with open(self.pdf_path, 'rb') as file:
                    data = file.read()
            else:
                data = self.pdf_bytes

            # جستجوی XMP packet
            xmp_start = data.find(b'<?xpacket begin')
            xmp_end = data.find(b'<?xpacket end', xmp_start)

            if xmp_start != -1 and xmp_end != -1:
                xmp_data = data[xmp_start:xmp_end + 14]  # +14 برای شامل کردن '<?xpacket end'
                xmp_text = xmp_data.decode('utf-8', errors='ignore')

                # تجزیه XMP
                self._parse_xmp_data(xmp_text)

        except Exception as e:
            warnings.warn(f"خطا در استخراج XMP: {str(e)}")

    def _extract_xmp_from_pikepdf(self, pdf):
        """استخراج XMP از pikepdf"""
        try:
            if hasattr(pdf, 'open_metadata') and '/Metadata' in pdf.Root:
                metadata_stream = pdf.Root['/Metadata']
                xmp_data = metadata_stream.read_bytes()

                # تجزیه XMP
                xmp_text = xmp_data.decode('utf-8', errors='ignore')
                self._parse_xmp_data(xmp_text)

        except Exception as e:
            warnings.warn(f"خطا در استخراج XMP از pikepdf: {str(e)}")

    def _extract_structural_metadata(self):
        """استخراج اطلاعات ساختاری"""
        try:
            if HAS_PYPDF2:
                if self.pdf_path:
                    with open(self.pdf_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                else:
                    import io
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(self.pdf_bytes))

                # بررسی ساختارهای مختلف
                root = pdf_reader.trailer.get('/Root', {})

                # بررسی tagged PDF
                if '/MarkInfo' in root:
                    mark_info = root['/MarkInfo']
                    if '/Marked' in mark_info:
                        self.metadata.tagged = bool(mark_info['/Marked'])

                # بررسی linearized
                self.metadata.linearized = pdf_reader.is_linearized if hasattr(pdf_reader, 'is_linearized') else False

                # بررسی attachments
                if '/Names' in root and '/EmbeddedFiles' in root['/Names']:
                    self.metadata.has_attachments = True

                # بررسی forms
                if '/AcroForm' in root:
                    self.metadata.has_forms = True

                # بررسی javascript
                if '/Names' in root and '/JavaScript' in root['/Names']:
                    self.metadata.has_javascript = True

                # بررسی embedded files
                self._check_for_embedded_files(pdf_reader)

        except Exception as e:
            warnings.warn(f"خطا در استخراج اطلاعات ساختاری: {str(e)}")

    def _extract_font_metadata(self):
        """استخراج اطلاعات فونت‌ها"""
        try:
            if HAS_PDFPLUMBER and self.pdf_path:
                with pdfplumber.open(self.pdf_path) as pdf:
                    fonts = set()

                    for page in pdf.pages:
                        if hasattr(page, 'fonts'):
                            for font_name, font_info in page.fonts.items():
                                font_data = {
                                    'name': font_name,
                                    'type': font_info.get('type', 'Unknown'),
                                    'encoding': font_info.get('encoding', 'Unknown'),
                                    'embedded': font_info.get('embedded', False)
                                }
                                fonts.add(json.dumps(font_data, sort_keys=True))

                    # تبدیل به لیست دیکشنری
                    self.metadata.fonts = [json.loads(f) for f in fonts]

        except Exception as e:
            warnings.warn(f"خطا در استخراج اطلاعات فونت‌ها: {str(e)}")

    def _extract_image_metadata(self):
        """استخراج اطلاعات تصاویر"""
        try:
            if HAS_PDFPLUMBER and self.pdf_path:
                with pdfplumber.open(self.pdf_path) as pdf:
                    image_count = 0
                    image_formats = {}

                    for page_num, page in enumerate(pdf.pages):
                        images = page.images
                        image_count += len(images)

                        for img in images:
                            img_format = img.get('filter', 'Unknown')
                            if img_format in image_formats:
                                image_formats[img_format] += 1
                            else:
                                image_formats[img_format] = 1

                    self.metadata.image_count = image_count
                    self.metadata.image_formats = image_formats

        except Exception as e:
            warnings.warn(f"خطا در استخراج اطلاعات تصاویر: {str(e)}")

    def _extract_conformance_metadata(self):
        """استخراج اطلاعات انطباق"""
        try:
            if self.pdf_path:
                with open(self.pdf_path, 'rb') as file:
                    data = file.read(5000)  # خواندن 5KB اول برای جستجو
            else:
                data = self.pdf_bytes[:5000]

            data_str = data.decode('ascii', errors='ignore')

            # جستجوی استانداردهای PDF
            standards = {
                'PDF/A': ['PDF/A-1a', 'PDF/A-1b', 'PDF/A-2a', 'PDF/A-2b', 'PDF/A-3a', 'PDF/A-3b'],
                'PDF/UA': ['PDF/UA-1'],
                'PDF/X': ['PDF/X-1a', 'PDF/X-3', 'PDF/X-4'],
                'PDF/E': ['PDF/E-1']
            }

            for std_type, std_list in standards.items():
                for std in std_list:
                    if std in data_str:
                        self.metadata.conformance = std
                        return

            # جستجوی در XMP
            if self.metadata.xmp_metadata:
                xmp_str = json.dumps(self.metadata.xmp_metadata)
                for std_type, std_list in standards.items():
                    for std in std_list:
                        if std in xmp_str:
                            self.metadata.conformance = std
                            return

        except Exception as e:
            warnings.warn(f"خطا در استخراج اطلاعات انطباق: {str(e)}")

    def _extract_custom_metadata(self):
        """استخراج متادیتای سفارشی"""
        try:
            # جستجوی متادیتای سفارشی در کل فایل
            if self.pdf_path:
                with open(self.pdf_path, 'rb') as file:
                    data = file.read()
            else:
                data = self.pdf_bytes

            # الگوهای متادیتای سفارشی
            patterns = {
                'custom_metadata': rb'/(\w+)\s*\(([^)]+)\)',
                'properties': rb'/<(\w+)>\s*\(([^)]+)\)',
            }

            for pattern_name, pattern in patterns.items():
                matches = re.findall(pattern, data)
                for match in matches:
                    key = match[0].decode('ascii', errors='ignore')
                    value = match[1].decode('utf-8', errors='ignore')
                    self.metadata.custom_metadata[key] = value

        except Exception as e:
            warnings.warn(f"خطا در استخراج متادیتای سفارشی: {str(e)}")

    def _extract_accessibility_metadata(self):
        """استخراج اطلاعات دسترسی"""
        try:
            if HAS_PYPDF2:
                if self.pdf_path:
                    with open(self.pdf_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                else:
                    import io
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(self.pdf_bytes))

                root = pdf_reader.trailer.get('/Root', {})

                accessibility_info = {}

                # بررسی ساختار منطقی
                if '/StructTreeRoot' in root:
                    accessibility_info['has_structure_tree'] = True

                # بررسی زبان
                if '/Lang' in root:
                    accessibility_info['language_specified'] = True
                    self.metadata.language = str(root['/Lang'])

                # بررسی alt text برای تصاویر
                if '/MarkInfo' in root:
                    mark_info = root['/MarkInfo']
                    if '/Marked' in mark_info:
                        accessibility_info['tagged'] = bool(mark_info['/Marked'])

                # بررسی navigation
                if '/Outlines' in root:
                    accessibility_info['has_outlines'] = True

                self.metadata.accessibility = accessibility_info

        except Exception as e:
            warnings.warn(f"خطا در استخراج اطلاعات دسترسی: {str(e)}")

    def _parse_pdf_date(self, pdf_date_str: str) -> datetime | None:
        """پارس تاریخ PDF"""
        try:
            # فرمت: D:YYYYMMDDHHmmSSOHH'mm'
            # مثال: D:20250101120000+03'30'

            if not pdf_date_str.startswith('D:'):
                return None

            date_str = pdf_date_str[2:]  # حذف 'D:'

            # استخراج بخش‌های تاریخ
            year = int(date_str[0:4]) if len(date_str) >= 4 else 1970
            month = int(date_str[4:6]) if len(date_str) >= 6 else 1
            day = int(date_str[6:8]) if len(date_str) >= 8 else 1
            hour = int(date_str[8:10]) if len(date_str) >= 10 else 0
            minute = int(date_str[10:12]) if len(date_str) >= 12 else 0
            second = int(date_str[12:14]) if len(date_str) >= 14 else 0

            # ایجاد datetime
            dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)

            # تنظیم offset اگر وجود دارد
            if len(date_str) > 14:
                offset_str = date_str[14:]
                if offset_str[0] in ['+', '-']:
                    offset_sign = 1 if offset_str[0] == '+' else -1
                    offset_hour = int(offset_str[1:3]) if len(offset_str) >= 3 else 0
                    offset_minute = int(offset_str[4:6]) if len(offset_str) >= 6 else 0

                    # اعمال offset
                    from datetime import timedelta
                    offset = timedelta(hours=offset_hour, minutes=offset_minute)
                    if offset_sign == -1:
                        offset = -offset

                    dt = dt.replace(tzinfo=timezone(offset))

            return dt

        except Exception:
            return None

    def _parse_permissions(self, permissions: int):
        """پارس مجوزهای PDF"""
        # ماسک‌های مجوز استاندارد PDF
        PERMISSION_MASKS = {
            'print': 0b000000000100,  # 4
            'modify': 0b000000001000,  # 8
            'copy': 0b000000010000,  # 16
            'annotate': 0b000000100000,  # 32
            'fill_forms': 0b000100000000,  # 256
            'extract': 0b000010000000,  # 512
            'assemble': 0b001000000000,  # 1024
            'print_high_quality': 0b010000000000,  # 2048
        }

        self.metadata.permissions = []

        for perm_name, mask in PERMISSION_MASKS.items():
            if permissions & mask:
                self.metadata.permissions.append(perm_name)

        # تنظیم پرچم‌های ساده
        self.metadata.can_print = 'print' in self.metadata.permissions
        self.metadata.can_modify = 'modify' in self.metadata.permissions
        self.metadata.can_copy = 'copy' in self.metadata.permissions
        self.metadata.can_annotate = 'annotate' in self.metadata.permissions

    def _parse_pikepdf_permissions(self, permissions):
        """پارس مجوزهای pikepdf"""
        if hasattr(permissions, 'print'):
            self.metadata.can_print = permissions.print
            if permissions.print:
                self.metadata.permissions.append('print')

        if hasattr(permissions, 'modify'):
            self.metadata.can_modify = permissions.modify
            if permissions.modify:
                self.metadata.permissions.append('modify')

        if hasattr(permissions, 'copy'):
            self.metadata.can_copy = permissions.copy
            if permissions.copy:
                self.metadata.permissions.append('copy')

        if hasattr(permissions, 'annotate'):
            self.metadata.can_annotate = permissions.annotate
            if permissions.annotate:
                self.metadata.permissions.append('annotate')

    def _parse_xmp_data(self, xmp_text: str):
        """پارس داده‌های XMP"""
        try:
            # حذف namespace برای سادگی
            xmp_text = xmp_text.replace('rdf:', '').replace('dc:', '').replace('xmp:', '')

            # تجزیه XML
            root = ET.fromstring(xmp_text)

            # استخراج metadata های رایج
            xmp_data = {}

            # Dublin Core
            dc_elements = ['title', 'creator', 'subject', 'description',
                          'publisher', 'contributor', 'date', 'type',
                          'format', 'identifier', 'source', 'language',
                          'relation', 'coverage', 'rights']

            for elem in dc_elements:
                nodes = root.findall(f'.//{elem}')
                if nodes:
                    values = [n.text for n in nodes if n.text]
                    if values:
                        xmp_data[elem] = values[0] if len(values) == 1 else values

            # XMP Basic
            xmp_basic = ['CreateDate', 'ModifyDate', 'MetadataDate',
                        'CreatorTool', 'Label', 'Rating']

            for elem in xmp_basic:
                nodes = root.findall(f'.//{elem}')
                if nodes:
                    values = [n.text for n in nodes if n.text]
                    if values:
                        xmp_data[elem.lower()] = values[0] if len(values) == 1 else values

            # PDF Specific
            pdf_elements = ['Keywords', 'PDFVersion', 'Producer']

            for elem in pdf_elements:
                nodes = root.findall(f'.//{elem}')
                if nodes:
                    values = [n.text for n in nodes if n.text]
                    if values:
                        xmp_data[elem.lower()] = values[0] if len(values) == 1 else values

            self.metadata.xmp_metadata = xmp_data

            def _stringify_xmp_value(value: Any) -> str:
                if isinstance(value, list):
                    return ", ".join(str(item) for item in value)
                return str(value)

            # به‌روزرسانی metadata اصلی با XMP
            if 'title' in xmp_data and not self.metadata.title:
                self.metadata.title = _stringify_xmp_value(xmp_data['title'])
            if 'creator' in xmp_data and not self.metadata.author:
                self.metadata.author = _stringify_xmp_value(xmp_data['creator'])
            if 'subject' in xmp_data and not self.metadata.subject:
                self.metadata.subject = _stringify_xmp_value(xmp_data['subject'])
            if 'keywords' in xmp_data and not self.metadata.keywords:
                self.metadata.keywords = _stringify_xmp_value(xmp_data['keywords'])
            if 'creatortool' in xmp_data and not self.metadata.creator:
                self.metadata.creator = _stringify_xmp_value(xmp_data['creatortool'])
            if 'producer' in xmp_data and not self.metadata.producer:
                self.metadata.producer = _stringify_xmp_value(xmp_data['producer'])

        except Exception as e:
            warnings.warn(f"خطا در پارس XMP: {str(e)}")

    def _scan_binary_for_metadata(self, data: bytes):
        """اسکن باینری برای یافتن متادیتا"""
        try:
            # تبدیل به متن برای جستجو
            text = data.decode('latin-1', errors='ignore')

            # جستجوی متادیتای استاندارد PDF
            patterns = {
                'title': r'/Title\s*\(([^)]+)\)',
                'author': r'/Author\s*\(([^)]+)\)',
                'subject': r'/Subject\s*\(([^)]+)\)',
                'keywords': r'/Keywords\s*\(([^)]+)\)',
                'creator': r'/Creator\s*\(([^)]+)\)',
                'producer': r'/Producer\s*\(([^)]+)\)',
                'creation_date': r'/CreationDate\s*\(([^)]+)\)',
                'mod_date': r'/ModDate\s*\(([^)]+)\)',
            }

            for field, pattern in patterns.items():
                match = re.search(pattern, text)
                if match:
                    value = match.group(1)
                    # حذف escaping
                    value = value.replace('\\(', '(').replace('\\)', ')')
                    value = value.replace('\\n', '\n').replace('\\r', '\r')
                    value = value.replace('\\t', '\t').replace('\\b', '\b')
                    value = value.replace('\\f', '\f').replace('\\\\', '\\')

                    if field == 'title' and not self.metadata.title:
                        self.metadata.title = value
                    elif field == 'author' and not self.metadata.author:
                        self.metadata.author = value
                    elif field == 'subject' and not self.metadata.subject:
                        self.metadata.subject = value
                    elif field == 'keywords' and not self.metadata.keywords:
                        self.metadata.keywords = value
                    elif field == 'creator' and not self.metadata.creator:
                        self.metadata.creator = value
                    elif field == 'producer' and not self.metadata.producer:
                        self.metadata.producer = value
                    elif field == 'creation_date':
                        dt = self._parse_pdf_date(value)
                        if dt and not self.metadata.creation_date:
                            self.metadata.creation_date = dt
                    elif field == 'mod_date':
                        dt = self._parse_pdf_date(value)
                        if dt and not self.metadata.modification_date:
                            self.metadata.modification_date = dt

            # جستجوی نسخه PDF
            version_match = re.search(r'%PDF-(\d\.\d)', text[:1000])
            if version_match and not self.metadata.pdf_version:
                self.metadata.pdf_version = version_match.group(1)

        except Exception as e:
            warnings.warn(f"خطا در اسکن باینری: {str(e)}")

    def _check_for_embedded_files(self, pdf_reader):
        """بررسی فایل‌های embedded"""
        try:
            # بررسی embedded files در PDF
            if hasattr(pdf_reader, 'attachments'):
                attachments = pdf_reader.attachments
                if attachments and len(attachments) > 0:
                    self.metadata.has_embedded_files = True
                    self.metadata.has_attachments = True

            # بررسی در trailer
            if '/Names' in pdf_reader.trailer:
                names = pdf_reader.trailer['/Names']
                if isinstance(names, dict) and '/EmbeddedFiles' in names:
                    self.metadata.has_embedded_files = True
                    self.metadata.has_attachments = True

        except Exception as e:
            warnings.warn(f"خطا در بررسی embedded files: {str(e)}")


class PDFMetadataError(Exception):
    """خطای استخراج متادیتای PDF"""


class MetadataExtractor:
    """کلاس اصلی برای استخراج متادیتا"""

    @staticmethod
    def extract_from_file(
        pdf_path: str,
        extract_types: list[MetadataType] | None = None
    ) -> dict[str, Any]:
        """
        استخراج متادیتا از فایل
        
        Args:
            pdf_path: مسیر فایل PDF
            extract_types: لیست انواع متادیتا برای استخراج
            
        Returns:
            دیکشنری حاوی متادیتاهای استخراج شده
        """
        if extract_types is None:
            extract_types = [MetadataType.BASIC, MetadataType.TECHNICAL, MetadataType.XMP]

        extractor = PDFMetadataExtractor(pdf_path=pdf_path)
        metadata = extractor.extract_all()

        result: dict[str, Any] = {
            "file_path": pdf_path,
            "file_name": os.path.basename(pdf_path),
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_types": [t.value for t in extract_types]
        }

        # اضافه کردن metadata بر اساس انواع درخواستی
        metadata_dict = metadata.to_dict()

        for meta_type in extract_types:
            if meta_type == MetadataType.BASIC:
                result["basic_metadata"] = {
                    "title": metadata_dict.get("title"),
                    "author": metadata_dict.get("author"),
                    "subject": metadata_dict.get("subject"),
                    "keywords": metadata_dict.get("keywords"),
                    "creator": metadata_dict.get("creator"),
                    "producer": metadata_dict.get("producer"),
                    "creation_date": metadata_dict.get("creation_date"),
                    "modification_date": metadata_dict.get("modification_date")
                }

            elif meta_type == MetadataType.TECHNICAL:
                result["technical_metadata"] = {
                    "pdf_version": metadata_dict.get("pdf_version"),
                    "page_count": metadata_dict.get("page_count"),
                    "file_size": metadata_dict.get("file_size"),
                    "file_hash_md5": metadata_dict.get("file_hash_md5"),
                    "file_hash_sha256": metadata_dict.get("file_hash_sha256"),
                    "mime_type": metadata_dict.get("mime_type"),
                    "tagged": metadata_dict.get("tagged"),
                    "linearized": metadata_dict.get("linearized"),
                    "has_attachments": metadata_dict.get("has_attachments"),
                    "has_forms": metadata_dict.get("has_forms"),
                    "has_javascript": metadata_dict.get("has_javascript"),
                    "has_embedded_files": metadata_dict.get("has_embedded_files")
                }

            elif meta_type == MetadataType.SECURITY:
                result["security_metadata"] = {
                    "encrypted": metadata_dict.get("encrypted"),
                    "encryption_type": metadata_dict.get("encryption_type"),
                    "permissions": metadata_dict.get("permissions"),
                    "can_print": metadata_dict.get("can_print"),
                    "can_modify": metadata_dict.get("can_modify"),
                    "can_copy": metadata_dict.get("can_copy"),
                    "can_annotate": metadata_dict.get("can_annotate")
                }

            elif meta_type == MetadataType.XMP:
                result["xmp_metadata"] = metadata_dict.get("xmp_metadata", {})

            elif meta_type == MetadataType.CUSTOM:
                result["custom_metadata"] = metadata_dict.get("custom_metadata", {})

            elif meta_type == MetadataType.EMBEDDED:
                result["embedded_metadata"] = {
                    "fonts": metadata_dict.get("fonts", []),
                    "color_spaces": metadata_dict.get("color_spaces", []),
                    "image_count": metadata_dict.get("image_count"),
                    "image_formats": metadata_dict.get("image_formats", {}),
                    "layers": metadata_dict.get("layers", [])
                }

        return result

    @staticmethod
    def extract_from_bytes(
        pdf_bytes: bytes,
        extract_types: list[MetadataType] | None = None
    ) -> dict[str, Any]:
        """
        استخراج متادیتا از داده‌های بایت
        
        Args:
            pdf_bytes: داده‌های PDF به صورت بایت
            extract_types: لیست انواع متادیتا برای استخراج
            
        Returns:
            دیکشنری حاوی متادیتاهای استخراج شده
        """
        if extract_types is None:
            extract_types = [MetadataType.BASIC, MetadataType.TECHNICAL, MetadataType.XMP]

        extractor = PDFMetadataExtractor(pdf_bytes=pdf_bytes)
        metadata = extractor.extract_all()

        result: dict[str, Any] = {
            "file_name": "in_memory.pdf",
            "file_size": len(pdf_bytes),
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_types": [t.value for t in extract_types]
        }

        # اضافه کردن metadata بر اساس انواع درخواستی
        metadata_dict = metadata.to_dict()

        for meta_type in extract_types:
            if meta_type == MetadataType.BASIC:
                result["basic_metadata"] = {
                    "title": metadata_dict.get("title"),
                    "author": metadata_dict.get("author"),
                    "subject": metadata_dict.get("subject"),
                    "keywords": metadata_dict.get("keywords"),
                    "creator": metadata_dict.get("creator"),
                    "producer": metadata_dict.get("producer"),
                    "creation_date": metadata_dict.get("creation_date"),
                    "modification_date": metadata_dict.get("modification_date")
                }

            elif meta_type == MetadataType.TECHNICAL:
                result["technical_metadata"] = {
                    "pdf_version": metadata_dict.get("pdf_version"),
                    "page_count": metadata_dict.get("page_count"),
                    "file_size": metadata_dict.get("file_size"),
                    "file_hash_md5": metadata_dict.get("file_hash_md5"),
                    "file_hash_sha256": metadata_dict.get("file_hash_sha256"),
                    "mime_type": metadata_dict.get("mime_type"),
                    "tagged": metadata_dict.get("tagged"),
                    "linearized": metadata_dict.get("linearized"),
                    "has_attachments": metadata_dict.get("has_attachments"),
                    "has_forms": metadata_dict.get("has_forms"),
                    "has_javascript": metadata_dict.get("has_javascript"),
                    "has_embedded_files": metadata_dict.get("has_embedded_files")
                }

            elif meta_type == MetadataType.SECURITY:
                result["security_metadata"] = {
                    "encrypted": metadata_dict.get("encrypted"),
                    "encryption_type": metadata_dict.get("encryption_type"),
                    "permissions": metadata_dict.get("permissions"),
                    "can_print": metadata_dict.get("can_print"),
                    "can_modify": metadata_dict.get("can_modify"),
                    "can_copy": metadata_dict.get("can_copy"),
                    "can_annotate": metadata_dict.get("can_annotate")
                }

            elif meta_type == MetadataType.XMP:
                result["xmp_metadata"] = metadata_dict.get("xmp_metadata", {})

            elif meta_type == MetadataType.CUSTOM:
                result["custom_metadata"] = metadata_dict.get("custom_metadata", {})

            elif meta_type == MetadataType.EMBEDDED:
                result["embedded_metadata"] = {
                    "fonts": metadata_dict.get("fonts", []),
                    "color_spaces": metadata_dict.get("color_spaces", []),
                    "image_count": metadata_dict.get("image_count"),
                    "image_formats": metadata_dict.get("image_formats", {}),
                    "layers": metadata_dict.get("layers", [])
                }

        return result

    @staticmethod
    def extract_summary(pdf_path: str) -> dict[str, Any]:
        """
        استخراج خلاصه متادیتا
        
        Args:
            pdf_path: مسیر فایل PDF
            
        Returns:
            دیکشنری حاوی خلاصه متادیتا
        """
        extractor = PDFMetadataExtractor(pdf_path=pdf_path)
        metadata = extractor.extract_all()

        return {
            "file_name": os.path.basename(pdf_path),
            "file_path": pdf_path,
            "summary": metadata.get_summary(),
            "extraction_time": datetime.now().isoformat()
        }

    @staticmethod
    def validate_pdf(pdf_path: str) -> dict[str, Any]:
        """
        اعتبارسنجی فایل PDF
        
        Args:
            pdf_path: مسیر فایل PDF
            
        Returns:
            دیکشنری حاوی نتایج اعتبارسنجی
        """
        validation_result: dict[str, Any] = {
            "file_path": pdf_path,
            "file_name": os.path.basename(pdf_path),
            "is_valid": False,
            "validation_time": datetime.now().isoformat(),
            "errors": [],
            "warnings": [],
            "compliance": None
        }

        try:
            # بررسی وجود فایل
            if not os.path.exists(pdf_path):
                validation_result["errors"].append("فایل وجود ندارد")
                return validation_result

            # بررسی سایز فایل
            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                validation_result["errors"].append("فایل خالی است")
                return validation_result

            if file_size > 500 * 1024 * 1024:  # 500MB
                validation_result["warnings"].append("فایل بسیار بزرگ است")

            # بررسی هدر PDF
            with open(pdf_path, 'rb') as file:
                header = file.read(5)
                if not header.startswith(b'%PDF-'):
                    validation_result["errors"].append("فایل PDF معتبر نیست (هدر نادرست)")
                    return validation_result

            # استخراج متادیتا برای اعتبارسنجی بیشتر
            extractor = PDFMetadataExtractor(pdf_path=pdf_path)
            metadata = extractor.extract_all()

            validation_result["is_valid"] = True
            validation_result["page_count"] = metadata.page_count
            validation_result["pdf_version"] = metadata.pdf_version
            validation_result["file_size"] = metadata.file_size

            # بررسی انطباق
            if metadata.conformance:
                validation_result["compliance"] = metadata.conformance

            # بررسی خطاهای اعتبارسنجی
            if metadata.validation_errors:
                validation_result["errors"].extend(metadata.validation_errors)

            # بررسی دسترسی‌پذیری
            if metadata.accessibility:
                accessibility_issues: list[str] = []
                if not metadata.accessibility.get('tagged', False):
                    accessibility_issues.append("PDF برچسب‌گذاری نشده است")
                if not metadata.accessibility.get('language_specified', False):
                    accessibility_issues.append("زبان سند مشخص نشده است")

                if accessibility_issues:
                    validation_result["warnings"].extend(accessibility_issues)

            # بررسی امنیت
            if metadata.encrypted:
                validation_result["warnings"].append("فایل رمزگذاری شده است")

            # بررسی ساختار
            if not metadata.tagged:
                validation_result["warnings"].append("PDF بدون ساختار منطقی")

        except Exception as e:
            validation_result["errors"].append(f"خطا در اعتبارسنجی: {str(e)}")

        return validation_result

    @staticmethod
    def compare_metadata(pdf_path1: str, pdf_path2: str) -> dict[str, Any]:
        """
        مقایسه متادیتای دو فایل PDF
        
        Args:
            pdf_path1: مسیر فایل PDF اول
            pdf_path2: مسیر فایل PDF دوم
            
        Returns:
            دیکشنری حاوی نتایج مقایسه
        """
        extractor1 = PDFMetadataExtractor(pdf_path=pdf_path1)
        extractor2 = PDFMetadataExtractor(pdf_path=pdf_path2)

        metadata1 = extractor1.extract_all()
        metadata2 = extractor2.extract_all()

        comparison: dict[str, Any] = {
            "files": {
                "file1": pdf_path1,
                "file2": pdf_path2
            },
            "comparison_time": datetime.now().isoformat(),
            "differences": {},
            "similarities": {}
        }

        # مقایسه فیلدهای اصلی
        fields_to_compare = [
            'title', 'author', 'subject', 'keywords', 'creator', 'producer',
            'pdf_version', 'page_count', 'file_size', 'encrypted'
        ]

        for field in fields_to_compare:
            value1 = getattr(metadata1, field)
            value2 = getattr(metadata2, field)

            if value1 != value2:
                comparison["differences"][field] = {
                    "file1": value1,
                    "file2": value2
                }
            else:
                comparison["similarities"][field] = value1

        # مقایسه تاریخ‌ها
        if metadata1.creation_date != metadata2.creation_date:
            comparison["differences"]["creation_date"] = {
                "file1": metadata1.creation_date.isoformat() if metadata1.creation_date else None,
                "file2": metadata2.creation_date.isoformat() if metadata2.creation_date else None
            }

        if metadata1.modification_date != metadata2.modification_date:
            comparison["differences"]["modification_date"] = {
                "file1": metadata1.modification_date.isoformat() if metadata1.modification_date else None,
                "file2": metadata2.modification_date.isoformat() if metadata2.modification_date else None
            }

        # مقایسه هش فایل
        if metadata1.file_hash_md5 != metadata2.file_hash_md5:
            comparison["differences"]["file_hash_md5"] = {
                "file1": metadata1.file_hash_md5,
                "file2": metadata2.file_hash_md5
            }

        if metadata1.file_hash_sha256 != metadata2.file_hash_sha256:
            comparison["differences"]["file_hash_sha256"] = {
                "file1": metadata1.file_hash_sha256,
                "file2": metadata2.file_hash_sha256
            }

        # محاسبه درصد تشابه
        total_fields = len(fields_to_compare) + 4  # فیلدهای اصلی + تاریخ‌ها + هش‌ها
        similar_fields = len(comparison["similarities"])
        similarity_percentage = (similar_fields / total_fields) * 100

        comparison["similarity_percentage"] = round(similarity_percentage, 2)
        comparison["is_identical"] = len(comparison["differences"]) == 0

        return comparison


# توابع کمکی
def extract_metadata(pdf_path: str, detailed: bool = False) -> dict[str, Any]:
    """
    تابع ساده برای استخراج متادیتا
    
    Args:
        pdf_path: مسیر فایل PDF
        detailed: اگر True باشد، تمام متادیتا استخراج می‌شود
        
    Returns:
        دیکشنری حاوی متادیتا
    """
    if detailed:
        extractor = PDFMetadataExtractor(pdf_path=pdf_path)
        metadata = extractor.extract_all()
        return metadata.to_dict()
    else:
        return MetadataExtractor.extract_summary(pdf_path)


def batch_extract_metadata(pdf_files: list[str], output_format: str = 'json') -> list[dict[str, Any]]:
    """
    استخراج متادیتا از چندین فایل PDF
    
    Args:
        pdf_files: لیست مسیر فایل‌های PDF
        output_format: فرمت خروجی ('json' یا 'dict')
        
    Returns:
        لیست دیکشنری‌های متادیتا
    """
    results: list[dict[str, Any]] = []

    for pdf_file in pdf_files:
        try:
            if not os.path.exists(pdf_file):
                results.append({
                    "file": pdf_file,
                    "error": "فایل وجود ندارد",
                    "success": False
                })
                continue

            extractor = PDFMetadataExtractor(pdf_path=pdf_file)
            metadata = extractor.extract_all()

            result = {
                "file": pdf_file,
                "file_name": os.path.basename(pdf_file),
                "success": True,
                "metadata": metadata.to_dict() if output_format == 'dict' else metadata.to_json()
            }

            results.append(result)

        except Exception as e:
            results.append({
                "file": pdf_file,
                "error": str(e),
                "success": False
            })

    return results


def export_metadata_to_json(pdf_path: str, output_path: str | None = None) -> str:
    """
    صادر کردن متادیتا به فایل JSON
    
    Args:
        pdf_path: مسیر فایل PDF
        output_path: مسیر خروجی JSON (اگر None باشد، در کنار فایل PDF ذخیره می‌شود)
        
    Returns:
        مسیر فایل JSON ایجاد شده
    """
    extractor = PDFMetadataExtractor(pdf_path=pdf_path)
    metadata = extractor.extract_all()

    if output_path is None:
        base_name = os.path.splitext(pdf_path)[0]
        output_path = f"{base_name}_metadata.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json_data = metadata.to_json(indent=2)
        f.write(json_data)

    return output_path


def export_metadata_to_csv(pdf_files: list[str], output_path: str) -> str:
    """
    صادر کردن متادیتای چندین فایل به CSV
    
    Args:
        pdf_files: لیست مسیر فایل‌های PDF
        output_path: مسیر فایل CSV خروجی
        
    Returns:
        مسیر فایل CSV ایجاد شده
    """
    import csv

    # فیلدهای CSV
    fields = [
        'file_name', 'title', 'author', 'subject', 'keywords',
        'creator', 'producer', 'creation_date', 'modification_date',
        'pdf_version', 'page_count', 'file_size', 'encrypted',
        'encryption_type', 'tagged', 'has_attachments', 'has_forms',
        'has_javascript', 'conformance'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()

        for pdf_file in pdf_files:
            try:
                extractor = PDFMetadataExtractor(pdf_path=pdf_file)
                metadata = extractor.extract_all()
                metadata_dict = metadata.to_dict()

                row = {
                    'file_name': os.path.basename(pdf_file),
                    'title': metadata_dict.get('title', ''),
                    'author': metadata_dict.get('author', ''),
                    'subject': metadata_dict.get('subject', ''),
                    'keywords': metadata_dict.get('keywords', ''),
                    'creator': metadata_dict.get('creator', ''),
                    'producer': metadata_dict.get('producer', ''),
                    'creation_date': metadata_dict.get('creation_date', ''),
                    'modification_date': metadata_dict.get('modification_date', ''),
                    'pdf_version': metadata_dict.get('pdf_version', ''),
                    'page_count': metadata_dict.get('page_count', ''),
                    'file_size': metadata_dict.get('file_size', ''),
                    'encrypted': metadata_dict.get('encrypted', False),
                    'encryption_type': metadata_dict.get('encryption_type', ''),
                    'tagged': metadata_dict.get('tagged', False),
                    'has_attachments': metadata_dict.get('has_attachments', False),
                    'has_forms': metadata_dict.get('has_forms', False),
                    'has_javascript': metadata_dict.get('has_javascript', False),
                    'conformance': metadata_dict.get('conformance', '')
                }

                writer.writerow(row)

            except Exception as e:
                print(f"خطا در پردازش فایل {pdf_file}: {str(e)}")

    return output_path


# # تابع اصلی برای تست
# def main():
#     """تابع اصلی برای تست ماژول"""
#     import sys

#     if len(sys.argv) < 2:
#         print("استفاده: python metadata_extractor.py <مسیر فایل PDF>")
#         print("مثال: python metadata_extractor.py document.pdf")
#         sys.exit(1)

#     pdf_path = sys.argv[1]

#     if not os.path.exists(pdf_path):
#         print(f"فایل {pdf_path} یافت نشد.")
#         sys.exit(1)

#     try:
#         # استخراج متادیتا
#         extractor = PDFMetadataExtractor(pdf_path=pdf_path)
#         metadata = extractor.extract_all()

#         # نمایش خلاصه
#         print("=" * 80)
#         print("خلاصه متادیتای PDF")
#         print("=" * 80)
#         print(f"فایل: {os.path.basename(pdf_path)}")
#         print(f"اندازه: {metadata.file_size:,} بایت")
#         print(f"تعداد صفحات: {metadata.page_count}")
#         print(f"نسخه PDF: {metadata.pdf_version}")
#         print(f"عنوان: {metadata.title or 'ندارد'}")
#         print(f"نویسنده: {metadata.author or 'ندارد'}")
#         print(f"موضوع: {metadata.subject or 'ندارد'}")
#         print(f"تاریخ ایجاد: {metadata.creation_date or 'ندارد'}")
#         print(f"تاریخ ویرایش: {metadata.modification_date or 'ندارد'}")
#         print(f"رمزگذاری شده: {'بله' if metadata.encrypted else 'خیر'}")
#         print(f"انطباق: {metadata.conformance or 'ندارد'}")

#         # ذخیره به JSON
#         json_path = export_metadata_to_json(pdf_path)
#         print(f"\nمتادیتا در فایل {json_path} ذخیره شد.")

#     except Exception as e:
#         print(f"خطا در استخراج متادیتا: {str(e)}")
#         sys.exit(1)


# if __name__ == "__main__":
#     main()
