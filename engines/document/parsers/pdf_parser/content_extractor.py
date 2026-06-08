#!/usr/bin/env python3
"""
PDF content Extraction module
PDF text, tables, images, links and other content extraction
"""
import base64
import io
import json
import re
import warnings
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from pathlib import Path
from typing import Any

import cv2  # type: ignore[import-not-found]
import numpy as np
import pdfplumber  # type: ignore[import-not-found]
import pytesseract  # type: ignore[import-not-found]
from camelot import py as camelot_py  # type: ignore[import-not-found]
from pdf2image import convert_from_path  # type: ignore[import-not-found]
from PIL import Image

try:
    import fitz  # type: ignore[import-untyped]  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    warnings.warn("PyMuPDF (fitz) not installed. Some features may be limited.")

try:
    import pandas as pd  # type: ignore[import-untyped]
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    warnings.warn("Pandas not installed. Table export to DataFrame disabled.")

# Import from other modules
from .layout_analyzer import PageLayout
from .structure_parser import StructuralElement


class ContentType(Enum):
    """Types of extractable content"""
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    LINK = "link"
    ANNOTATION = "annotation"
    EQUATION = "equation"
    CODE_BLOCK = "code_block"
    HEADER = "header"
    FOOTER = "footer"
    PAGE_NUMBER = "page_number"
    FORM_FIELD = "form_field"


@dataclass
class ExtractedText:
    """Class for holding extracted text"""
    text: str
    page_num: int
    bbox: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font_name: str | None = None
    font_size: float | None = None
    language: str = "fa"  # fa, en, ar, etc.
    confidence: float = 1.0
    structural_type: str | None = None  # paragraph, heading, caption, etc.
    parent_element_id: str | None = None


@dataclass
class ExtractedTable:
    """Class for holding extracted table"""
    page_num: int
    bbox: tuple[float, float, float, float]
    data: list[list[str]]
    headers: list[str] | None = None
    table_type: str = "grid"  # grid, stream, lattice
    accuracy: float = 1.0
    pandas_df: Any | None = None

    def to_dataframe(self):
        """Convert table data to DataFrame"""
        if HAS_PANDAS and self.data:
            return pd.DataFrame(self.data[1:], columns=self.data[0] if self.headers else None)
        return None

    def to_csv(self, filepath: str):
        """Save table as CSV"""
        if HAS_PANDAS:
            df = self.to_dataframe()
            if df is not None:
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                return True
        return False


@dataclass
class ExtractedImage:
    """Class for holding extracted image"""
    page_num: int
    bbox: tuple[float, float, float, float]
    image_data: bytes
    image_format: str  # JPEG, PNG, etc.
    width: int
    height: int
    dpi: tuple[int, int] = (72, 72)
    base64_data: str | None = None
    caption: str | None = None

    def __post_init__(self):
        """Calculate base64_data after initialization"""
        if self.image_data and not self.base64_data:
            self.base64_data = base64.b64encode(self.image_data).decode('utf-8')

    def save(self, filepath: str):
        """Save image to file"""
        with open(filepath, 'wb') as f:
            f.write(self.image_data)

    def to_pil_image(self):
        """Convert to PIL Image"""
        return Image.open(io.BytesIO(self.image_data))


@dataclass
class ExtractedLink:
    """Class for holding extracted link"""
    page_num: int
    bbox: tuple[float, float, float, float]
    uri: str
    text: str | None = None
    link_type: str = "uri"  # uri, internal, external


@dataclass
class ExtractedAnnotation:
    """Class for holding extracted annotation"""
    page_num: int
    bbox: tuple[float, float, float, float]
    annotation_type: str  # highlight, underline, strikeout, note, etc.
    content: str | None = None
    color: tuple[int, int, int] | None = None
    author: str | None = None
    date: str | None = None


@dataclass
class ContentExtractionStats:
    """Content extraction statistics"""
    total_pages: int = 0
    text_blocks: int = 0
    tables: int = 0
    images: int = 0
    links: int = 0
    annotations: int = 0
    equations: int = 0
    code_blocks: int = 0
    total_text_chars: int = 0
    total_text_words: int = 0
    extraction_time: float = 0.0
    languages_detected: list[str] = field(default_factory=list)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'total_pages': self.total_pages,
            'text_blocks': self.text_blocks,
            'tables': self.tables,
            'images': self.images,
            'links': self.links,
            'annotations': self.annotations,
            'equations': self.equations,
            'code_blocks': self.code_blocks,
            'total_text_chars': self.total_text_chars,
            'total_text_words': self.total_text_words,
            'extraction_time': self.extraction_time,
            'languages_detected': self.languages_detected
        }


class ContentExtractor:
    """
    Main class for PDF content extraction
    """

    def __init__(self,
                 pdf_path: str,
                 use_ocr: bool = False,
                 ocr_languages: list[str] | None = None,
                 table_method: str = "lattice",
                 image_dpi: int = 150):
        """
        Initialize content extractor
        
        Args:
            pdf_path: Path to the PDF file
            use_ocr: Use OCR for scanned PDFs
            ocr_languages: OCR languages (default: ['fas', 'eng'])
            table_method: Table extraction method ('lattice', 'stream')
            image_dpi: Quality of extracted images
        """
        self.pdf_path = pdf_path
        self.use_ocr = use_ocr
        self.ocr_languages = ocr_languages or ['fas', 'eng']
        self.table_method = table_method
        self.image_dpi = image_dpi

        # Store results
        self.extracted_texts: list[ExtractedText] = []
        self.extracted_tables: list[ExtractedTable] = []
        self.extracted_images: list[ExtractedImage] = []
        self.extracted_links: list[ExtractedLink] = []
        self.extracted_annotations: list[ExtractedAnnotation] = []

        # Statistics
        self.stats = ContentExtractionStats()

        # OCR setup
        if use_ocr:
            self._setup_ocr()

    def _setup_ocr(self):
        """Initialize OCR setup"""
        try:
            # Check Tesseract availability
            pytesseract.get_tesseract_version()
        except Exception as e:
            warnings.warn(f"Tesseract OCR not available: {e}")
            self.use_ocr = False

    def extract_all(self,
                   layout: list[PageLayout] | None = None,
                   structure: list[StructuralElement] | None = None) -> dict[str, Any]:
        """
        Extract all PDF content
        
        Args:
            layout: Output from LayoutAnalyzer (optional)
            structure: Output from StructureParser (optional)
            
        Returns:
            Dictionary containing all extracted content
        """
        import time
        start_time = time.time()


        results: dict[str, Any] = {
            'texts': [],
            'tables': [],
            'images': [],
            'links': [],
            'annotations': [],
            'metadata': {},
            'stats': {}
        }

        try:
            # Extract metadata
            results['metadata'] = self.extract_metadata()

            # Extract text
            print("📝 Extracting text...")
            self.extract_text(layout, structure)
            results['texts'] = [t.__dict__ for t in self.extracted_texts]

            # Extract tables
            print("📊 Extracting tables...")
            self.extract_tables()
            results['tables'] = [t.__dict__ for t in self.extracted_tables]

            # Extract images
            print("🖼️ Extracting images...")
            self.extract_images()
            results['images'] = [img.__dict__ for img in self.extracted_images]

            # Extract links
            print("🔗 Extracting links...")
            self.extract_links()
            results['links'] = [link.__dict__ for link in self.extracted_links]

            # Extract annotations
            print("📋 Extracting annotations...")
            self.extract_annotations()
            results['annotations'] = [ann.__dict__ for ann in self.extracted_annotations]

            # Detect equations and code blocks
            print("🧮 Detecting equations and code...")
            self.detect_equations_and_code()

            # Calculate statistics
            self.stats.total_pages = results['metadata'].get('num_pages', 0)
            self.stats.text_blocks = len(self.extracted_texts)
            self.stats.tables = len(self.extracted_tables)
            self.stats.images = len(self.extracted_images)
            self.stats.links = len(self.extracted_links)
            self.stats.annotations = len(self.extracted_annotations)

            # Calculate character and word counts
            total_chars = sum(len(t.text) for t in self.extracted_texts)
            total_words = sum(len(t.text.split()) for t in self.extracted_texts)
            self.stats.total_text_chars = total_chars
            self.stats.total_text_words = total_words

            # Extraction time
            self.stats.extraction_time = time.time() - start_time

            results['stats'] = self.stats.to_dict()

            print(f"✅ Extraction complete! Time: {self.stats.extraction_time:.2f}s")
            print(f"📊 Stats: {self.stats.text_blocks} text blocks, {self.stats.tables} tables, {self.stats.images} images")

        except Exception as e:
            print(f"❌ Extraction error: {e}")
            import traceback
            traceback.print_exc()

        return results

    def extract_text(self,
                    layout: list[PageLayout] | None = None,
                    structure: list[StructuralElement] | None = None) -> list[ExtractedText]:
        """
        Extract text from PDF
        
        Args:
            layout: Page layout information
            structure: Document structure information
            
        Returns:
            List of extracted texts
        """
        self.extracted_texts = []

        try:
            if self.use_ocr:
                # Use OCR for scanned PDFs
                self._extract_text_with_ocr()
            else:
                # Direct text extraction
                self._extract_text_direct(layout, structure)

        except Exception as e:
            print(f"Text extraction error: {e}")
            # Try fallback method
            self._extract_text_fallback()

        return self.extracted_texts

    def _extract_text_direct(self,
                            layout: list[PageLayout] | None = None,
                            structure: list[StructuralElement] | None = None):
        """Direct text extraction from PDF"""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    # Extract text with pdfplumber
                    text = page.extract_text()

                    if text and text.strip():
                        # Extract text with position preservation
                        chars = page.chars

                        if chars:
                            # Group characters by lines
                            lines: dict[int, list[dict[str, Any]]] = {}
                            for char in chars:
                                line_key = round(char['top'])
                                if line_key not in lines:
                                    lines[line_key] = []
                                lines[line_key].append(char)

                            # Sort lines
                            sorted_lines = sorted(lines.items(), key=lambda x: x[0])

                            for line_top, line_chars in sorted_lines:
                                # Sort characters within each line
                                line_chars.sort(key=lambda x: x['x0'])

                                # Build line text
                                line_text = ''.join([c['text'] for c in line_chars])

                                # Calculate line bounding box
                                x0 = min(c['x0'] for c in line_chars)
                                y0 = min(c['top'] for c in line_chars)
                                x1 = max(c['x1'] for c in line_chars)
                                y1 = max(c['bottom'] for c in line_chars)

                                # Detect language
                                language = self._detect_language(line_text)

                                # Create extracted text object
                                extracted_text = ExtractedText(
                                    text=line_text,
                                    page_num=page_num,
                                    bbox=(x0, y0, x1, y1),
                                    language=language,
                                    confidence=0.95
                                )

                                self.extracted_texts.append(extracted_text)
                        else:
                            # If no characters available, store the full page text
                            extracted_text = ExtractedText(
                                text=text,
                                page_num=page_num,
                                bbox=page.bbox,
                                language=self._detect_language(text),
                                confidence=0.9
                            )
                            self.extracted_texts.append(extracted_text)

                    # Update statistics
                    self.stats.languages_detected.extend(self._detect_languages_in_text(text))

                except Exception as e:
                    print(f"Error extracting text from page {page_num}: {e}")

    def _extract_text_with_ocr(self):
        """Extract text using OCR"""
        try:
            # Convert PDF to images
            images = convert_from_path(self.pdf_path, dpi=self.image_dpi)

            for page_num, image in enumerate(images, 1):
                # Convert to OpenCV format
                open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

                # Preprocess image for better OCR
                gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                # Apply OCR
                config = f'--oem 3 --psm 6 -l {"+".join(self.ocr_languages)}'
                ocr_result = pytesseract.image_to_data(
                    thresh,
                    output_type=pytesseract.Output.DICT,
                    config=config
                )

                # Process OCR results
                n_boxes = len(ocr_result['text'])
                for i in range(n_boxes):
                    if int(ocr_result['conf'][i]) > 60:  # Confidence above 60%
                        text = ocr_result['text'][i].strip()
                        if text:
                            x = ocr_result['left'][i]
                            y = ocr_result['top'][i]
                            w = ocr_result['width'][i]
                            h = ocr_result['height'][i]

                            extracted_text = ExtractedText(
                                text=text,
                                page_num=page_num,
                                bbox=(x, y, x + w, y + h),
                                language=self.ocr_languages[0].replace('fas', 'fa'),
                                confidence=float(ocr_result['conf'][i]) / 100.0
                            )
                            self.extracted_texts.append(extracted_text)

        except Exception as e:
            print(f"OCR error: {e}")

    def _extract_text_fallback(self):
        """Fallback method for text extraction"""
        try:
            if HAS_PYMUPDF:
                doc = fitz.open(self.pdf_path)
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()

                    if text:
                        extracted_text = ExtractedText(
                            text=text,
                            page_num=page_num + 1,
                            bbox=page.rect,
                            language=self._detect_language(text),
                            confidence=0.8
                        )
                        self.extracted_texts.append(extracted_text)
                doc.close()
        except Exception as e:
            print(f"Fallback text extraction error: {e}")

    def extract_tables(self) -> list[ExtractedTable]:
        """
        Extract tables from PDF
        
        Returns:
            List of extracted tables
        """
        self.extracted_tables = []

        try:
            # Method 1: Using Camelot
            self._extract_tables_camelot()

            # Method 2: Using pdfplumber (if Camelot fails)
            if not self.extracted_tables:
                self._extract_tables_pdfplumber()

        except Exception as e:
            print(f"Table extraction error: {e}")

        return self.extracted_tables

    def _extract_tables_camelot(self):
        """Extract tables with Camelot"""
        try:
            tables = camelot_py.read_pdf(
                self.pdf_path,
                pages='all',
                flavor=self.table_method,
                strip_text='\n',
                suppress_stdout=True
            )

            for table in tables:
                if table.parsing_report and table.parsing_report.get('accuracy', 0) > 50:
                    # Convert table data
                    table_data = []
                    for row in table.df.values.tolist():
                        table_data.append([str(cell) if cell is not None else "" for cell in row])

                    # Create extracted table object
                    extracted_table = ExtractedTable(
                        page_num=table.page,
                        bbox=table._bbox,
                        data=table_data,
                        headers=table.df.columns.tolist() if not table.df.empty else None,
                        table_type=self.table_method,
                        accuracy=table.parsing_report.get('accuracy', 0) / 100.0
                    )

                    self.extracted_tables.append(extracted_table)

        except Exception as e:
            print(f"Error extracting tables with Camelot: {e}")

    def _extract_tables_pdfplumber(self):
        """Extract tables with pdfplumber"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()

                    for table in tables:
                        if table:
                            # Approximate bounding box calculation
                            bbox = page.bbox

                            # Create extracted table object
                            extracted_table = ExtractedTable(
                                page_num=page_num,
                                bbox=bbox,
                                data=table,
                                table_type="stream",
                                accuracy=0.7
                            )

                            self.extracted_tables.append(extracted_table)

        except Exception as e:
            print(f"Error extracting tables with pdfplumber: {e}")

    def extract_images(self,
                      min_size: tuple[int, int] = (50, 50),
                      max_images_per_page: int = 20) -> list[ExtractedImage]:
        """
        Extract images from PDF
        
        Args:
            min_size: Minimum image dimensions (width, height)
            max_images_per_page: Maximum images per page
            
        Returns:
            List of extracted images
        """
        self.extracted_images = []

        try:
            if HAS_PYMUPDF:
                self._extract_images_pymupdf(min_size, max_images_per_page)
            else:
                self._extract_images_pdfplumber(min_size, max_images_per_page)

        except Exception as e:
            print(f"Image extraction error: {e}")

        return self.extracted_images

    def _extract_images_pymupdf(self, min_size: tuple[int, int], max_images_per_page: int):
        """Extract images with PyMuPDF"""
        doc = fitz.open(self.pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)

            for img_index, img in enumerate(image_list[:max_images_per_page]):
                xref = img[0]
                base_image = doc.extract_image(xref)

                if base_image:
                    image_data = base_image["image"]
                    width = base_image["width"]
                    height = base_image["height"]

                    # Check minimum size
                    if width >= min_size[0] and height >= min_size[1]:
                        image_format = base_image["ext"]

                        # Create extracted image object
                        extracted_image = ExtractedImage(
                            page_num=page_num + 1,
                            bbox=(0, 0, width, height),  # Exact position needs more processing
                            image_data=image_data,
                            image_format=image_format.upper(),
                            width=width,
                            height=height,
                            dpi=(72, 72)
                        )

                        self.extracted_images.append(extracted_image)

        doc.close()

    def _extract_images_pdfplumber(self, min_size: tuple[int, int], max_images_per_page: int):
        """Extract images with pdfplumber"""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                images = page.images

                for img_index, img in enumerate(images[:max_images_per_page]):
                    if 'stream' in img:
                        image_data = img['stream'].get_data()

                        if image_data:
                            width = img.get('width', 0)
                            height = img.get('height', 0)

                            # Check minimum size
                            if width >= min_size[0] and height >= min_size[1]:
                                image_format = self._detect_image_format(image_data)

                                # Create extracted image object
                                extracted_image = ExtractedImage(
                                    page_num=page_num,
                                    bbox=(img['x0'], img['top'], img['x1'], img['bottom']),
                                    image_data=image_data,
                                    image_format=image_format,
                                    width=int(width),
                                    height=int(height),
                                    dpi=(72, 72)
                                )

                                self.extracted_images.append(extracted_image)

    def extract_links(self) -> list[ExtractedLink]:
        """
        Extract links from PDF
        
        Returns:
            List of extracted links
        """
        self.extracted_links = []

        try:
            if HAS_PYMUPDF:
                self._extract_links_pymupdf()
            else:
                self._extract_links_pdfplumber()

        except Exception as e:
            print(f"Link extraction error: {e}")

        return self.extracted_links

    def _extract_links_pymupdf(self):
        """Extract links with PyMuPDF"""
        doc = fitz.open(self.pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            links = page.get_links()

            for link in links:
                if 'uri' in link:
                    extracted_link = ExtractedLink(
                        page_num=page_num + 1,
                        bbox=link.get('from', (0, 0, 0, 0)),
                        uri=link['uri'],
                        link_type="external" if link['uri'].startswith('http') else "internal"
                    )
                    self.extracted_links.append(extracted_link)

        doc.close()

    def _extract_links_pdfplumber(self):
        """Extract links with pdfplumber"""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # pdfplumber does not directly support links
                # Can find links from extracted text
                text = page.extract_text()
                if text:
                    urls = self._extract_urls_from_text(text)
                    for url in urls:
                        extracted_link = ExtractedLink(
                            page_num=page_num,
                            bbox=page.bbox,
                            uri=url,
                            link_type="external" if url.startswith('http') else "internal"
                        )
                        self.extracted_links.append(extracted_link)

    def extract_annotations(self) -> list[ExtractedAnnotation]:
        """
        Extract annotations from PDF
        
        Returns:
            List of extracted annotations
        """
        self.extracted_annotations = []

        try:
            if HAS_PYMUPDF:
                self._extract_annotations_pymupdf()

        except Exception as e:
            print(f"Annotation extraction error: {e}")

        return self.extracted_annotations

    def _extract_annotations_pymupdf(self):
        """Extract annotations with PyMuPDF"""
        doc = fitz.open(self.pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            annots = page.annots()

            if annots:
                for annot in annots:
                    annot_type = annot.type[1]  # highlight, underline, etc.
                    rect = annot.rect
                    content = annot.info.get('content', '')

                    extracted_annotation = ExtractedAnnotation(
                        page_num=page_num + 1,
                        bbox=(rect.x0, rect.y0, rect.x1, rect.y1),
                        annotation_type=annot_type,
                        content=content,
                        author=annot.info.get('title', ''),
                        date=annot.info.get('modDate', '')
                    )

                    self.extracted_annotations.append(extracted_annotation)

        doc.close()

    def detect_equations_and_code(self):
        """Detect mathematical equations and code blocks"""
        # Mathematical equation patterns
        equation_patterns = [
            r'\$[^$]+\$',  # Inline equations
            r'\\\[.*?\\\]',  # Display equations
            r'\\\(.*?\\\)',  # Inline equations with LaTeX
            r'\\begin\{equation\}.*?\\end\{equation\}',
            r'\\begin\{align\}.*?\\end\{align\}',
            r'\\frac\{.*?\}\{.*?\}',  # Fractions
            r'\\sum_\{.*?\}\^\{.*?\}',  # Sigma
            r'\\int_\{.*?\}\^\{.*?\}',  # Integral
        ]

        # Code block patterns
        code_patterns = [
            r'```.*?```',  # Code block with backticks
            r'def\s+\w+\(.*?\):',  # Python function definition
            r'function\s+\w+\(.*?\)\s*\{',  # JavaScript function definition
            r'class\s+\w+',  # Class definition
            r'import\s+\w+',  # Import statement
            r'#include\s+<.*?>',  # C++ include
            r'public\s+class',  # Java class
        ]

        for text_obj in self.extracted_texts:
            text = text_obj.text

            # Check for mathematical equations
            for pattern in equation_patterns:
                if re.search(pattern, text, re.DOTALL):
                    text_obj.structural_type = "equation"
                    self.stats.equations += 1
                    break

            # Check for code blocks
            for pattern in code_patterns:
                if re.search(pattern, text):
                    text_obj.structural_type = "code_block"
                    self.stats.code_blocks += 1
                    break

    def extract_metadata(self) -> dict[str, Any]:
        """
        Extract PDF metadata
        
        Returns:
            Metadata dictionary
        """
        metadata = {}

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # Main metadata
                metadata.update({
                    'num_pages': len(pdf.pages),
                    'author': pdf.metadata.get('Author', ''),
                    'title': pdf.metadata.get('Title', ''),
                    'subject': pdf.metadata.get('Subject', ''),
                    'keywords': pdf.metadata.get('Keywords', ''),
                    'creator': pdf.metadata.get('Creator', ''),
                    'producer': pdf.metadata.get('Producer', ''),
                    'creation_date': pdf.metadata.get('CreationDate', ''),
                    'modification_date': pdf.metadata.get('ModDate', ''),
                })

                # Additional info
                # Access attributes from the PDF stream object (pdfplumber's internal PDF object)
                metadata['pdf_version'] = getattr(pdf.stream, 'pdf_version', None)
                metadata['is_encrypted'] = getattr(pdf.stream, 'is_encrypted', False)

                # Collect font information
                fonts: set[str] = set()
                for page in pdf.pages:
                    # pdfplumber provides page.fonts (but mypy may not know it)
                    page_fonts = getattr(page, 'fonts', [])
                    for font in page_fonts:
                        basefont = font.get('basefont', '')
                        if basefont:
                            fonts.add(basefont)
                metadata['fonts'] = list(fonts)

        except Exception as e:
            print(f"Metadata extraction error: {e}")
            metadata['error'] = str(e)

        return metadata

    def export_to_json(self, output_path: str):
        """
        Export results to JSON format
        
        Args:
            output_path: Output file path
        """
        results = {
            'metadata': self.extract_metadata(),
            'texts': [t.__dict__ for t in self.extracted_texts],
            'tables': [t.__dict__ for t in self.extracted_tables],
            'images': [img.__dict__ for img in self.extracted_images],
            'links': [link.__dict__ for link in self.extracted_links],
            'annotations': [ann.__dict__ for ann in self.extracted_annotations],
            'stats': self.stats.to_dict()
        }

        # Remove image_data from JSON (large size)
        for img in results['images']:
            if 'image_data' in img:
                del img['image_data']

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    def export_to_csv(self, output_dir: str | Path):
        """
        Export results to CSV format
        
        Args:
            output_dir: Output directory
        """
        import csv

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save texts
        if self.extracted_texts:
            text_path = output_dir / "texts.csv"
            with open(text_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['page', 'text', 'language', 'confidence', 'bbox'])
                for text in self.extracted_texts:
                    writer.writerow([
                        text.page_num,
                        text.text,
                        text.language,
                        text.confidence,
                        str(text.bbox)
                    ])

        # Save tables
        if self.extracted_tables and HAS_PANDAS:
            for i, table in enumerate(self.extracted_tables):
                table_path = output_dir / f"table_{i+1}.csv"
                table.to_csv(str(table_path))

    def _detect_language(self, text: str) -> str:
        """
        Detect text language
        
        Args:
            text: Input text
            
        Returns:
            Language code ('fa', 'en', 'ar', 'mixed')
        """
        if not text.strip():
            return 'unknown'

        # Persian/Arabic characters
        persian_arabic_chars = re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text)

        # English characters
        english_chars = re.findall(r'[a-zA-Z]', text)

        if persian_arabic_chars and not english_chars:
            return 'fa'
        elif english_chars and not persian_arabic_chars:
            return 'en'
        elif persian_arabic_chars and english_chars:
            return 'mixed'
        else:
            return 'unknown'

    def _detect_languages_in_text(self, text: str) -> list[str]:
        """Detect languages present in text"""
        languages = set()

        # Split text into sentences
        sentences = re.split(r'[.!?]', text)

        for sentence in sentences:
            lang = self._detect_language(sentence)
            if lang != 'unknown':
                languages.add(lang)

        return list(languages)

    def _extract_urls_from_text(self, text: str) -> list[str]:
        """Extract URLs from text"""
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.\-?=&%#+]*'
        return re.findall(url_pattern, text)

    def _detect_image_format(self, image_data: bytes) -> str:
        """Detect image format"""
        try:
            image = Image.open(io.BytesIO(image_data))
            return image.format or 'UNKNOWN'
        except Exception:
            return 'UNKNOWN'

    def get_summary(self) -> dict[str, Any]:
        """
        Get summary of extraction results
        
        Returns:
            Dictionary of results summary
        """
        return {
            'total_pages': self.stats.total_pages,
            'text_blocks': len(self.extracted_texts),
            'tables': len(self.extracted_tables),
            'images': len(self.extracted_images),
            'links': len(self.extracted_links),
            'annotations': len(self.extracted_annotations),
            'equations': self.stats.equations,
            'code_blocks': self.stats.code_blocks,
            'total_characters': self.stats.total_text_chars,
            'total_words': self.stats.total_text_words,
            'extraction_time': self.stats.extraction_time,
            'languages': list(set(self.stats.languages_detected))
        }


# Helper function for quick use
def extract_content_from_pdf(pdf_path: str,
                           use_ocr: bool = False,
                           output_json: str | None = None,
                           output_dir: str | None = None) -> dict[str, Any]:
    """
    Helper function for PDF content extraction
    
    Args:
        pdf_path: Path to the PDF file
        use_ocr: Use OCR
        output_json: Path to save JSON (optional)
        output_dir: Directory to save CSV and images (optional)
        
    Returns:
        Extraction results
    """
    extractor = ContentExtractor(pdf_path, use_ocr=use_ocr)
    results = extractor.extract_all()

    # Save JSON output
    if output_json:
        extractor.export_to_json(output_json)

    # Save CSV output
    if output_dir:
        extractor.export_to_csv(output_dir)

        # Save images
        images_dir = Path(output_dir) / "images"
        images_dir.mkdir(exist_ok=True)

        for i, image in enumerate(extractor.extracted_images):
            image_path = images_dir / f"image_{i+1}_{image.page_num}.{image.image_format.lower()}"
            image.save(str(image_path))

    return results


# if __name__ == "__main__":
#     # Example usage
#     pdf_path = "sample.pdf"

#     # Create extractor instance
#     extractor = ContentExtractor(pdf_path, use_ocr=True)

#     # Extract all content
#     results = extractor.extract_all()

#     # Show summary
#     summary = extractor.get_summary()
#     print("📊 Extraction Summary:")
#     for key, value in summary.items():
#         print(f"  {key}: {value}")

#     # Save results
#     extractor.export_to_json("extraction_results.json")
#     extractor.export_to_csv("extraction_output")

#     print(f"✅ Extraction complete! Results saved to extraction_results.json.")
