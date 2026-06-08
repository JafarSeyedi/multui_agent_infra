#!/usr/bin/env python3
"""
metadata_extractor.py - Extract metadata from PDF files
Module for extracting metadata, XMP, and technical PDF information
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

# For XMP processing
try:
    import defusedxml.ElementTree as safe_ET  # type: ignore[import-untyped]
    ET = safe_ET
except ImportError:
    pass

# For PDF processing
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
    """Metadata types"""
    BASIC = "basic"
    XMP = "xmp"
    TECHNICAL = "technical"
    SECURITY = "security"
    CUSTOM = "custom"
    EMBEDDED = "embedded"


class PDFVersion(Enum):
    """PDF versions"""
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
    """PDF conformance levels"""
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
    """Main PDF metadata class"""

    # Basic information
    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: str | None = None
    creator: str | None = None
    producer: str | None = None
    creation_date: datetime | None = None
    modification_date: datetime | None = None

    # Technical information
    pdf_version: str | None = None
    page_count: int | None = None
    file_size: int | None = None
    file_hash_md5: str | None = None
    file_hash_sha256: str | None = None
    mime_type: str | None = None

    # Security information
    encrypted: bool = False
    encryption_type: str | None = None
    permissions: list[str] = field(default_factory=list)
    can_print: bool = True
    can_modify: bool = True
    can_copy: bool = True
    can_annotate: bool = True

    # Structural information
    tagged: bool = False
    linearized: bool = False
    has_attachments: bool = False
    has_forms: bool = False
    has_javascript: bool = False
    has_embedded_files: bool = False

    # XMP information
    xmp_metadata: dict[str, Any] = field(default_factory=dict)

    # Font information
    fonts: list[dict[str, Any]] = field(default_factory=list)

    # Color information
    color_spaces: list[str] = field(default_factory=list)

    # Image information
    image_count: int = 0
    image_formats: dict[str, int] = field(default_factory=dict)

    # Layout information
    layers: list[str] = field(default_factory=list)

    # Custom information
    custom_metadata: dict[str, Any] = field(default_factory=dict)

    # Conformance information
    conformance: str | None = None
    validation_errors: list[str] = field(default_factory=list)

    # Geolocation information
    geolocation: dict[str, float] | None = None

    # Legal information
    copyright: str | None = None
    license: str | None = None
    rights: str | None = None

    # Language information
    language: str | None = None
    languages: list[str] = field(default_factory=list)

    # Accessibility information
    accessibility: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)

        # Convert datetime to string
        if result.get('creation_date'):
            result['creation_date'] = result['creation_date'].isoformat()
        if result.get('modification_date'):
            result['modification_date'] = result['modification_date'].isoformat()

        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def get_summary(self) -> dict[str, Any]:
        """Get metadata summary"""
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
    """Main class for extracting metadata from PDF"""

    def __init__(self, pdf_path: str | None = None, pdf_bytes: bytes | None = None):
        """
        Initialize metadata extractor
        
        Args:
            pdf_path: PDF file path
            pdf_bytes: PDF data as bytes
        """
        self.pdf_path = pdf_path
        self.pdf_bytes = pdf_bytes
        self.metadata = PDFMetadata()

        if pdf_path and pdf_bytes:
            raise ValueError("Only one of pdf_path or pdf_bytes should be specified")

        if not pdf_path and not pdf_bytes:
            raise ValueError("One of pdf_path or pdf_bytes must be specified")

    def extract_all(self) -> PDFMetadata:
        """Extract all metadata"""
        try:
            # Extract basic information
            self._extract_basic_metadata()

            # Extract technical information
            self._extract_technical_metadata()

            # Extract security information
            self._extract_security_metadata()

            # Extract XMP information
            self._extract_xmp_metadata()

            # Extract structural information
            self._extract_structural_metadata()

            # Extract font information
            self._extract_font_metadata()

            # Extract image information
            self._extract_image_metadata()

            # Extract conformance information
            self._extract_conformance_metadata()

            # Extract custom information
            self._extract_custom_metadata()

            # Extract accessibility information
            self._extract_accessibility_metadata()

            return self.metadata

        except Exception as e:
            raise PDFMetadataError(f"Error extracting metadata: {str(e)}")

    def _extract_basic_metadata(self):
        """Extract basic metadata"""
        if HAS_PYPDF2:
            self._extract_with_pypdf2()
        elif HAS_PIKEPDF:
            self._extract_with_pikepdf()
        elif HAS_PDFPLUMBER:
            self._extract_with_pdfplumber()
        else:
            self._extract_with_binary_scan()

    def _extract_with_pypdf2(self):
        """with PyPDF2"""
        try:
            if self.pdf_path:
                with open(self.pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
            else:
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(self.pdf_bytes))

            # Basic information
            info = pdf_reader.metadata
            if info:
                self.metadata.title = info.get('/Title')
                self.metadata.author = info.get('/Author')
                self.metadata.subject = info.get('/Subject')
                self.metadata.keywords = info.get('/Keywords')
                self.metadata.creator = info.get('/Creator')
                self.metadata.producer = info.get('/Producer')

                # Dates
                creation_date = info.get('/CreationDate')
                if creation_date:
                    self.metadata.creation_date = self._parse_pdf_date(creation_date)

                mod_date = info.get('/ModDate')
                if mod_date:
                    self.metadata.modification_date = self._parse_pdf_date(mod_date)

            # Technical information
            self.metadata.pdf_version = pdf_reader.pdf_header
            self.metadata.page_count = len(pdf_reader.pages)
            self.metadata.encrypted = pdf_reader.is_encrypted

            if pdf_reader.is_encrypted:
                self.metadata.encryption_type = "Standard" if hasattr(pdf_reader, '_encryption') else "Unknown"

                # Check permissions
                if hasattr(pdf_reader, '_encryption'):
                    encrypt = pdf_reader._encryption
                    if hasattr(encrypt, 'P'):
                        permissions = int(encrypt.P)
                        self._parse_permissions(permissions)

        except Exception as e:
            warnings.warn(f"خطا در with PyPDF2: {str(e)}")

    def _extract_with_pikepdf(self):
        """with pikepdf"""
        try:
            if self.pdf_path:
                pdf = pikepdf.Pdf.open(self.pdf_path)
            else:
                import io
                pdf = pikepdf.Pdf.open(io.BytesIO(self.pdf_bytes))

            # Basic information
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

                # Dates
                if '/CreationDate' in info:
                    creation_date = str(info['/CreationDate'])
                    self.metadata.creation_date = self._parse_pdf_date(creation_date)

                if '/ModDate' in info:
                    mod_date = str(info['/ModDate'])
                    self.metadata.modification_date = self._parse_pdf_date(mod_date)

            # Technical information
            self.metadata.pdf_version = str(pdf.pdf_version)
            self.metadata.page_count = len(pdf.pages)
            self.metadata.encrypted = pdf.is_encrypted

            if pdf.is_encrypted:
                self.metadata.encryption_type = "Standard"

                # Check permissions
                if hasattr(pdf, 'permissions'):
                    perms = pdf.permissions
                    self._parse_pikepdf_permissions(perms)

            # Check XMP
            self._extract_xmp_from_pikepdf(pdf)

            pdf.close()

        except Exception as e:
            warnings.warn(f"خطا در with pikepdf: {str(e)}")

    def _extract_with_pdfplumber(self):
        """with pdfplumber"""
        try:
            if self.pdf_path:
                pdf = pdfplumber.open(self.pdf_path)
            else:
                import io
                pdf = pdfplumber.open(io.BytesIO(self.pdf_bytes))

            # Basic metadata information
            metadata = pdf.metadata
            if metadata:
                self.metadata.title = metadata.get('Title')
                self.metadata.author = metadata.get('Author')
                self.metadata.subject = metadata.get('Subject')
                self.metadata.keywords = metadata.get('Keywords')
                self.metadata.creator = metadata.get('Creator')
                self.metadata.producer = metadata.get('Producer')

                # Dates
                creation_date = metadata.get('CreationDate')
                if creation_date:
                    self.metadata.creation_date = self._parse_pdf_date(creation_date)

                mod_date = metadata.get('ModDate')
                if mod_date:
                    self.metadata.modification_date = self._parse_pdf_date(mod_date)

            # Technical information
            self.metadata.page_count = len(pdf.pages)

            pdf.close()

        except Exception as e:
            warnings.warn(f"خطا در with pdfplumber: {str(e)}")

    def _extract_with_binary_scan(self):
        """Extract with binary scan (no dependencies)"""
        try:
            if self.pdf_path:
                with open(self.pdf_path, 'rb') as file:
                    data = file.read()
            else:
                data = self.pdf_bytes

            # Search for metadata in binary data
            self._scan_binary_for_metadata(data)

        except Exception as e:
            warnings.warn(f"خطا در Extract with binary scan: {str(e)}")

    def _extract_technical_metadata(self):
        """Extract technical information"""
        try:
            if self.pdf_path:
                # File information
                file_stat = os.stat(self.pdf_path)
                self.metadata.file_size = file_stat.st_size

                # Calculate hash
                with open(self.pdf_path, 'rb') as file:
                    file_data = file.read()
                    self.metadata.file_hash_md5 = hashlib.md5(file_data).hexdigest()
                    self.metadata.file_hash_sha256 = hashlib.sha256(file_data).hexdigest()

                # MIME type
                mime_type, _ = mimetypes.guess_type(self.pdf_path)
                self.metadata.mime_type = mime_type or 'application/pdf'

            elif self.pdf_bytes:
                self.metadata.file_size = len(self.pdf_bytes)
                self.metadata.file_hash_md5 = hashlib.md5(self.pdf_bytes).hexdigest()
                self.metadata.file_hash_sha256 = hashlib.sha256(self.pdf_bytes).hexdigest()
                self.metadata.mime_type = 'application/pdf'

            # Detect PDF version from header
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
            warnings.warn(f"خطا در Extract technical information: {str(e)}")

    def _extract_security_metadata(self):
        """Extract security information"""
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
                    # Detect encryption type
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

                        # Check permissions
                        if hasattr(encrypt, 'P'):
                            permissions = int(encrypt.P)
                            self._parse_permissions(permissions)

        except Exception as e:
            warnings.warn(f"خطا در Extract security information: {str(e)}")

    def _extract_xmp_metadata(self):
        """Extract XMP metadata"""
        try:
            if self.pdf_path:
                with open(self.pdf_path, 'rb') as file:
                    data = file.read()
            else:
                data = self.pdf_bytes

            # Search for XMP packet
            xmp_start = data.find(b'<?xpacket begin')
            xmp_end = data.find(b'<?xpacket end', xmp_start)

            if xmp_start != -1 and xmp_end != -1:
                xmp_data = data[xmp_start:xmp_end + 14]  # +14 برای شامل کردن '<?xpacket end'
                xmp_text = xmp_data.decode('utf-8', errors='ignore')

                # Parse XMP data
                self._parse_xmp_data(xmp_text)

        except Exception as e:
            warnings.warn(f"خطا در استخراج XMP: {str(e)}")

    def _extract_xmp_from_pikepdf(self, pdf):
        """Extract XMP from pikepdf"""
        try:
            if hasattr(pdf, 'open_metadata') and '/Metadata' in pdf.Root:
                metadata_stream = pdf.Root['/Metadata']
                xmp_data = metadata_stream.read_bytes()

                # Parse XMP data
                xmp_text = xmp_data.decode('utf-8', errors='ignore')
                self._parse_xmp_data(xmp_text)

        except Exception as e:
            warnings.warn(f"خطا در Extract XMP from pikepdf: {str(e)}")

    def _extract_structural_metadata(self):
        """Extract structural information"""
        try:
            if HAS_PYPDF2:
                if self.pdf_path:
                    with open(self.pdf_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                else:
                    import io
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(self.pdf_bytes))

                # Check various structures
                root = pdf_reader.trailer.get('/Root', {})

                # Check tagged PDF
                if '/MarkInfo' in root:
                    mark_info = root['/MarkInfo']
                    if '/Marked' in mark_info:
                        self.metadata.tagged = bool(mark_info['/Marked'])

                # Check linearized
                self.metadata.linearized = pdf_reader.is_linearized if hasattr(pdf_reader, 'is_linearized') else False

                # Check attachments
                if '/Names' in root and '/EmbeddedFiles' in root['/Names']:
                    self.metadata.has_attachments = True

                # Check forms
                if '/AcroForm' in root:
                    self.metadata.has_forms = True

                # Check javascript
                if '/Names' in root and '/JavaScript' in root['/Names']:
                    self.metadata.has_javascript = True

                # Check embedded files
                self._check_for_embedded_files(pdf_reader)

        except Exception as e:
            warnings.warn(f"خطا در Extract structural information: {str(e)}")

    def _extract_font_metadata(self):
        """Extract font information"""
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

                    # Convert to list of dicts
                    self.metadata.fonts = [json.loads(f) for f in fonts]

        except Exception as e:
            warnings.warn(f"خطا در Extract font information: {str(e)}")

    def _extract_image_metadata(self):
        """Extract image information"""
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
            warnings.warn(f"خطا در Extract image information: {str(e)}")

    def _extract_conformance_metadata(self):
        """Extract conformance information"""
        try:
            if self.pdf_path:
                with open(self.pdf_path, 'rb') as file:
                    data = file.read(5000)  # Read first 5KB for search
            else:
                data = self.pdf_bytes[:5000]

            data_str = data.decode('ascii', errors='ignore')

            # Search for PDF standards
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

            # Search in XMP
            if self.metadata.xmp_metadata:
                xmp_str = json.dumps(self.metadata.xmp_metadata)
                for std_type, std_list in standards.items():
                    for std in std_list:
                        if std in xmp_str:
                            self.metadata.conformance = std
                            return

        except Exception as e:
            warnings.warn(f"خطا در Extract conformance information: {str(e)}")

    def _extract_custom_metadata(self):
        """Extract custom metadata"""
        try:
            # Search for custom metadata in entire file
            if self.pdf_path:
                with open(self.pdf_path, 'rb') as file:
                    data = file.read()
            else:
                data = self.pdf_bytes

            # Custom metadata patterns
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
            warnings.warn(f"خطا در Extract custom metadata: {str(e)}")

    def _extract_accessibility_metadata(self):
        """Extract accessibility information"""
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

                # Check logical structure
                if '/StructTreeRoot' in root:
                    accessibility_info['has_structure_tree'] = True

                # Check language
                if '/Lang' in root:
                    accessibility_info['language_specified'] = True
                    self.metadata.language = str(root['/Lang'])

                # Check alt text for images
                if '/MarkInfo' in root:
                    mark_info = root['/MarkInfo']
                    if '/Marked' in mark_info:
                        accessibility_info['tagged'] = bool(mark_info['/Marked'])

                # Check navigation
                if '/Outlines' in root:
                    accessibility_info['has_outlines'] = True

                self.metadata.accessibility = accessibility_info

        except Exception as e:
            warnings.warn(f"خطا در Extract accessibility information: {str(e)}")

    def _parse_pdf_date(self, pdf_date_str: str) -> datetime | None:
        """Parse PDF date"""
        try:
            # Format: D:YYYYMMDDHHmmSSOHH'mm'
            # Example: D:20250101120000+03'30'

            if not pdf_date_str.startswith('D:'):
                return None

            date_str = pdf_date_str[2:]  # Remove 'D:'

            # Extract date parts
            year = int(date_str[0:4]) if len(date_str) >= 4 else 1970
            month = int(date_str[4:6]) if len(date_str) >= 6 else 1
            day = int(date_str[6:8]) if len(date_str) >= 8 else 1
            hour = int(date_str[8:10]) if len(date_str) >= 10 else 0
            minute = int(date_str[10:12]) if len(date_str) >= 12 else 0
            second = int(date_str[12:14]) if len(date_str) >= 14 else 0

            # Create datetime
            dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)

            # Set offset if present
            if len(date_str) > 14:
                offset_str = date_str[14:]
                if offset_str[0] in ['+', '-']:
                    offset_sign = 1 if offset_str[0] == '+' else -1
                    offset_hour = int(offset_str[1:3]) if len(offset_str) >= 3 else 0
                    offset_minute = int(offset_str[4:6]) if len(offset_str) >= 6 else 0

                    # Apply offset
                    from datetime import timedelta
                    offset = timedelta(hours=offset_hour, minutes=offset_minute)
                    if offset_sign == -1:
                        offset = -offset

                    dt = dt.replace(tzinfo=timezone(offset))

            return dt

        except Exception:
            return None

    def _parse_permissions(self, permissions: int):
        """Parse PDF permissions"""
        # Standard PDF permission masks
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

        # Set simple flags
        self.metadata.can_print = 'print' in self.metadata.permissions
        self.metadata.can_modify = 'modify' in self.metadata.permissions
        self.metadata.can_copy = 'copy' in self.metadata.permissions
        self.metadata.can_annotate = 'annotate' in self.metadata.permissions

    def _parse_pikepdf_permissions(self, permissions):
        """Parse pikepdf permissions"""
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
        """Parse XMP data"""
        try:
            # Remove namespaces for simplicity
            xmp_text = xmp_text.replace('rdf:', '').replace('dc:', '').replace('xmp:', '')

            # Parse XML
            root = ET.fromstring(xmp_text)

            # Extract common metadata
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

            # Update main metadata with XMP
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
        """Binary scan to find metadata"""
        try:
            # Convert to text for searching
            text = data.decode('latin-1', errors='ignore')

            # Search for standard PDF metadata
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
                    # Remove escaping
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

            # Search PDF version
            version_match = re.search(r'%PDF-(\d\.\d)', text[:1000])
            if version_match and not self.metadata.pdf_version:
                self.metadata.pdf_version = version_match.group(1)

        except Exception as e:
            warnings.warn(f"Error in binary scan: {str(e)}")

    def _check_for_embedded_files(self, pdf_reader):
        """Check embedded files"""
        try:
            # Check embedded files in PDF
            if hasattr(pdf_reader, 'attachments'):
                attachments = pdf_reader.attachments
                if attachments and len(attachments) > 0:
                    self.metadata.has_embedded_files = True
                    self.metadata.has_attachments = True

            # Check in trailer
            if '/Names' in pdf_reader.trailer:
                names = pdf_reader.trailer['/Names']
                if isinstance(names, dict) and '/EmbeddedFiles' in names:
                    self.metadata.has_embedded_files = True
                    self.metadata.has_attachments = True

        except Exception as e:
            warnings.warn(f"Error checking embedded files: {str(e)}")


class PDFMetadataError(Exception):
    """PDF metadata extraction error"""


class MetadataExtractor:
    """Main class for metadata extraction"""

    @staticmethod
    def extract_from_file(
        pdf_path: str,
        extract_types: list[MetadataType] | None = None
    ) -> dict[str, Any]:
        """
        Extract metadata from file
        
        Args:
            pdf_path: PDF file path
            extract_types: list of metadata types to extract
            
        Returns:
            Dictionary containing extracted metadata
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

        # Add metadata based on requested types
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
        Extract metadata from byte data
        
        Args:
            pdf_bytes: PDF data as bytes
            extract_types: list of metadata types to extract
            
        Returns:
            Dictionary containing extracted metadata
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

        # Add metadata based on requested types
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
        Extract metadata summary
        
        Args:
            pdf_path: PDF file path
            
        Returns:
            Dictionary containing metadata summary
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
        Validation PDF file
        
        Args:
            pdf_path: PDF file path
            
        Returns:
            Dictionary containing validation results
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
            # Check file exists
            if not os.path.exists(pdf_path):
                validation_result["errors"].append("File does not exist")
                return validation_result

            # Check file size
            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                validation_result["errors"].append("File is empty")
                return validation_result

            if file_size > 500 * 1024 * 1024:  # 500MB
                validation_result["warnings"].append("File is very large")

            # Check PDF header
            with open(pdf_path, 'rb') as file:
                header = file.read(5)
                if not header.startswith(b'%PDF-'):
                    validation_result["errors"].append("File is not a valid PDF (invalid header)")
                    return validation_result

            # Extract metadata for further validation
            extractor = PDFMetadataExtractor(pdf_path=pdf_path)
            metadata = extractor.extract_all()

            validation_result["is_valid"] = True
            validation_result["page_count"] = metadata.page_count
            validation_result["pdf_version"] = metadata.pdf_version
            validation_result["file_size"] = metadata.file_size

            # Check conformance
            if metadata.conformance:
                validation_result["compliance"] = metadata.conformance

            # Check validation errors
            if metadata.validation_errors:
                validation_result["errors"].extend(metadata.validation_errors)

            # Check accessibility
            if metadata.accessibility:
                accessibility_issues: list[str] = []
                if not metadata.accessibility.get('tagged', False):
                    accessibility_issues.append("PDF is not tagged")
                if not metadata.accessibility.get('language_specified', False):
                    accessibility_issues.append("Document language not specified")

                if accessibility_issues:
                    validation_result["warnings"].extend(accessibility_issues)

            # Check security
            if metadata.encrypted:
                validation_result["warnings"].append("File is encrypted")

            # Check structure
            if not metadata.tagged:
                validation_result["warnings"].append("PDF without logical structure")

        except Exception as e:
            validation_result["errors"].append(f"Error in validation: {str(e)}")

        return validation_result

    @staticmethod
    def compare_metadata(pdf_path1: str, pdf_path2: str) -> dict[str, Any]:
        """
        Compare metadata of two PDF files
        
        Args:
            pdf_path1: path to first PDF file
            pdf_path2: path to second PDF file
            
        Returns:
            Dictionary containing comparison results
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

        # Compare main fields
        fields_to_compare = [
            'title', 'author', 'subject', 'keywords', 'creator', 'producer',
            'pdf_version', 'page_count', 'file_size', 'encrypted'
        ]

        for field_name in fields_to_compare:
            value1 = getattr(metadata1, field_name)
            value2 = getattr(metadata2, field_name)

            if value1 != value2:
                comparison["differences"][field] = {
                    "file1": value1,
                    "file2": value2
                }
            else:
                comparison["similarities"][field] = value1

        # Compare dates
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

        # Compare file hash
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

        # Calculate similarity percentage
        total_fields = len(fields_to_compare) + 4  # Main fields + dates + hashes
        similar_fields = len(comparison["similarities"])
        similarity_percentage = (similar_fields / total_fields) * 100

        comparison["similarity_percentage"] = round(similarity_percentage, 2)
        comparison["is_identical"] = len(comparison["differences"]) == 0

        return comparison


# Helper functions
def extract_metadata(pdf_path: str, detailed: bool = False) -> dict[str, Any]:
    """
    Simple function to extract metadata
    
    Args:
        pdf_path: PDF file path
        detailed: If True, extract all metadata
        
    Returns:
        Dictionary containing metadata
    """
    if detailed:
        extractor = PDFMetadataExtractor(pdf_path=pdf_path)
        metadata = extractor.extract_all()
        return metadata.to_dict()
    else:
        return MetadataExtractor.extract_summary(pdf_path)


def batch_extract_metadata(pdf_files: list[str], output_format: str = 'json') -> list[dict[str, Any]]:
    """
    Extract metadata from multiple PDF files
    
    Args:
        pdf_files: List of PDF file paths
        output_format: Output format ('json' or 'dict')
        
    Returns:
        List of metadata dictionaries
    """
    results: list[dict[str, Any]] = []

    for pdf_file in pdf_files:
        try:
            if not os.path.exists(pdf_file):
                results.append({
                    "file": pdf_file,
                    "error": "File does not exist",
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
    Export metadata to JSON file
    
    Args:
        pdf_path: PDF file path
        output_path: JSON output path (if None, saves next to the PDF file)
        
    Returns:
        Created JSON file path
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
    Export metadata of multiple files to CSV
    
    Args:
        pdf_files: List of PDF file paths
        output_path: CSV output file path
        
    Returns:
        Created CSV file path
    """
    import csv

    # CSV fields
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


# # Main function for testing
# def main():
#     """Main function for testing the module"""
#     import sys

#     if len(sys.argv) < 2:
#         print("استفاده: python metadata_extractor.py <PDF file path>")
#         print("مثال: python metadata_extractor.py document.pdf")
#         sys.exit(1)

#     pdf_path = sys.argv[1]

#     if not os.path.exists(pdf_path):
#         print(f"فایل {pdf_path} یافت نشد.")
#         sys.exit(1)

#     try:
#         # Extract metadata
#         extractor = PDFMetadataExtractor(pdf_path=pdf_path)
#         metadata = extractor.extract_all()

#         # Show summary
#         print("=" * 80)
#         print("خلاصه Metadataی PDF")
#         print("=" * 80)
#         print(f"فایل: {os.path.basename(pdf_path)}")
#         print(f"اندازه: {metadata.file_size:,} بایت")
#         print(f"تعداد صفحات: {metadata.page_count}")
#         print(f"نسخه PDF: {metadata.pdf_version}")
#         print(f"عنوان: {metadata.title or 'ندارد'}")
#         print(f"نویسنده: {metadata.author or 'ندارد'}")
#         print(f"موضوع: {metadata.subject or 'ندارد'}")
#         print(f"Creation date: {metadata.creation_date or 'ندارد'}")
#         print(f"تاریخ ویرایش: {metadata.modification_date or 'ندارد'}")
#         print(f"رمزگذاری شده: {'بله' if metadata.encrypted else 'خیر'}")
#         print(f"انطباق: {metadata.conformance or 'ندارد'}")

#         # Store به JSON
#         json_path = export_metadata_to_json(pdf_path)
#         print(f"\nMetadata در فایل {json_path} ذخیره شد.")

#     except Exception as e:
#         print(f"Error extracting metadata: {str(e)}")
#         sys.exit(1)


# if __name__ == "__main__":
#     main()
