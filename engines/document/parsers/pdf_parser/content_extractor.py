#!/usr/bin/env python3
"""
ماژول استخراج محتوای PDF
استخراج متن، جداول، تصاویر، لینک‌ها و سایر محتوا از فایل‌های PDF
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
    """انواع محتوای قابل استخراج"""
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
    """کلاس برای نگهداری متن استخراج شده"""
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
    """کلاس برای نگهداری جدول استخراج شده"""
    page_num: int
    bbox: tuple[float, float, float, float]
    data: list[list[str]]
    headers: list[str] | None = None
    table_type: str = "grid"  # grid, stream, lattice
    accuracy: float = 1.0
    pandas_df: Any | None = None

    def to_dataframe(self):
        """تبدیل داده‌های جدول به DataFrame"""
        if HAS_PANDAS and self.data:
            return pd.DataFrame(self.data[1:], columns=self.data[0] if self.headers else None)
        return None

    def to_csv(self, filepath: str):
        """ذخیره جدول به صورت CSV"""
        if HAS_PANDAS:
            df = self.to_dataframe()
            if df is not None:
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                return True
        return False


@dataclass
class ExtractedImage:
    """کلاس برای نگهداری تصویر استخراج شده"""
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
        """محاسبه base64_data پس از مقداردهی"""
        if self.image_data and not self.base64_data:
            self.base64_data = base64.b64encode(self.image_data).decode('utf-8')

    def save(self, filepath: str):
        """ذخیره تصویر در فایل"""
        with open(filepath, 'wb') as f:
            f.write(self.image_data)

    def to_pil_image(self):
        """تبدیل به تصویر PIL"""
        return Image.open(io.BytesIO(self.image_data))


@dataclass
class ExtractedLink:
    """کلاس برای نگهداری لینک استخراج شده"""
    page_num: int
    bbox: tuple[float, float, float, float]
    uri: str
    text: str | None = None
    link_type: str = "uri"  # uri, internal, external


@dataclass
class ExtractedAnnotation:
    """کلاس برای نگهداری حاشیه‌نویسی استخراج شده"""
    page_num: int
    bbox: tuple[float, float, float, float]
    annotation_type: str  # highlight, underline, strikeout, note, etc.
    content: str | None = None
    color: tuple[int, int, int] | None = None
    author: str | None = None
    date: str | None = None


@dataclass
class ContentExtractionStats:
    """آمار استخراج محتوا"""
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
        """تبدیل به دیکشنری"""
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
    کلاس اصلی برای استخراج محتوای PDF
    """

    def __init__(self,
                 pdf_path: str,
                 use_ocr: bool = False,
                 ocr_languages: list[str] | None = None,
                 table_method: str = "lattice",
                 image_dpi: int = 150):
        """
        مقداردهی اولیه استخراج کننده محتوا
        
        Args:
            pdf_path: مسیر فایل PDF
            use_ocr: استفاده از OCR برای PDFهای اسکن شده
            ocr_languages: زبان‌های OCR (پیش‌فرض: ['fas', 'eng'])
            table_method: روش استخراج جداول ('lattice', 'stream')
            image_dpi: کیفیت تصاویر استخراج شده
        """
        self.pdf_path = pdf_path
        self.use_ocr = use_ocr
        self.ocr_languages = ocr_languages or ['fas', 'eng']
        self.table_method = table_method
        self.image_dpi = image_dpi

        # ذخیره نتایج
        self.extracted_texts: list[ExtractedText] = []
        self.extracted_tables: list[ExtractedTable] = []
        self.extracted_images: list[ExtractedImage] = []
        self.extracted_links: list[ExtractedLink] = []
        self.extracted_annotations: list[ExtractedAnnotation] = []

        # آمار
        self.stats = ContentExtractionStats()

        # تنظیمات OCR
        if use_ocr:
            self._setup_ocr()

    def _setup_ocr(self):
        """تنظیمات اولیه OCR"""
        try:
            # بررسی وجود Tesseract
            pytesseract.get_tesseract_version()
        except Exception as e:
            warnings.warn(f"Tesseract OCR not available: {e}")
            self.use_ocr = False

    def extract_all(self,
                   layout: list[PageLayout] | None = None,
                   structure: list[StructuralElement] | None = None) -> dict[str, Any]:
        """
        استخراج تمام محتواهای PDF
        
        Args:
            layout: خروجی LayoutAnalyzer (اختیاری)
            structure: خروجی StructureParser (اختیاری)
            
        Returns:
            دیکشنری حاوی تمام محتواهای استخراج شده
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
            # استخراج متادیتا
            results['metadata'] = self.extract_metadata()

            # استخراج متن
            print("📝 استخراج متن...")
            self.extract_text(layout, structure)
            results['texts'] = [t.__dict__ for t in self.extracted_texts]

            # استخراج جداول
            print("📊 استخراج جداول...")
            self.extract_tables()
            results['tables'] = [t.__dict__ for t in self.extracted_tables]

            # استخراج تصاویر
            print("🖼️ استخراج تصاویر...")
            self.extract_images()
            results['images'] = [img.__dict__ for img in self.extracted_images]

            # استخراج لینک‌ها
            print("🔗 استخراج لینک‌ها...")
            self.extract_links()
            results['links'] = [link.__dict__ for link in self.extracted_links]

            # استخراج حاشیه‌نویسی‌ها
            print("📋 استخراج حاشیه‌نویسی‌ها...")
            self.extract_annotations()
            results['annotations'] = [ann.__dict__ for ann in self.extracted_annotations]

            # تشخیص معادلات و بلوک‌های کد
            print("🧮 تشخیص معادلات و کد...")
            self.detect_equations_and_code()

            # محاسبه آمار
            self.stats.total_pages = results['metadata'].get('num_pages', 0)
            self.stats.text_blocks = len(self.extracted_texts)
            self.stats.tables = len(self.extracted_tables)
            self.stats.images = len(self.extracted_images)
            self.stats.links = len(self.extracted_links)
            self.stats.annotations = len(self.extracted_annotations)

            # محاسبه تعداد کاراکترها و کلمات
            total_chars = sum(len(t.text) for t in self.extracted_texts)
            total_words = sum(len(t.text.split()) for t in self.extracted_texts)
            self.stats.total_text_chars = total_chars
            self.stats.total_text_words = total_words

            # زمان استخراج
            self.stats.extraction_time = time.time() - start_time

            results['stats'] = self.stats.to_dict()

            print(f"✅ استخراج کامل شد! زمان: {self.stats.extraction_time:.2f} ثانیه")
            print(f"📊 آمار: {self.stats.text_blocks} بلوک متن، {self.stats.tables} جدول، {self.stats.images} تصویر")

        except Exception as e:
            print(f"❌ خطا در استخراج: {e}")
            import traceback
            traceback.print_exc()

        return results

    def extract_text(self,
                    layout: list[PageLayout] | None = None,
                    structure: list[StructuralElement] | None = None) -> list[ExtractedText]:
        """
        استخراج متن از PDF
        
        Args:
            layout: اطلاعات لایه‌بندی صفحات
            structure: اطلاعات ساختاری سند
            
        Returns:
            لیست متن‌های استخراج شده
        """
        self.extracted_texts = []

        try:
            if self.use_ocr:
                # استفاده از OCR برای PDFهای اسکن شده
                self._extract_text_with_ocr()
            else:
                # استخراج متن مستقیم
                self._extract_text_direct(layout, structure)

        except Exception as e:
            print(f"خطا در استخراج متن: {e}")
            # تلاش با روش جایگزین
            self._extract_text_fallback()

        return self.extracted_texts

    def _extract_text_direct(self,
                            layout: list[PageLayout] | None = None,
                            structure: list[StructuralElement] | None = None):
        """استخراج متن مستقیم از PDF"""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    # استخراج متن با pdfplumber
                    text = page.extract_text()

                    if text and text.strip():
                        # استخراج متن با حفظ موقعیت
                        chars = page.chars

                        if chars:
                            # گروه‌بندی کاراکترها بر اساس خطوط
                            lines: dict[int, list[dict[str, Any]]] = {}
                            for char in chars:
                                line_key = round(char['top'])
                                if line_key not in lines:
                                    lines[line_key] = []
                                lines[line_key].append(char)

                            # مرتب‌سازی خطوط
                            sorted_lines = sorted(lines.items(), key=lambda x: x[0])

                            for line_top, line_chars in sorted_lines:
                                # مرتب‌سازی کاراکترها در هر خط
                                line_chars.sort(key=lambda x: x['x0'])

                                # ساخت متن خط
                                line_text = ''.join([c['text'] for c in line_chars])

                                # محاسبه bounding box خط
                                x0 = min(c['x0'] for c in line_chars)
                                y0 = min(c['top'] for c in line_chars)
                                x1 = max(c['x1'] for c in line_chars)
                                y1 = max(c['bottom'] for c in line_chars)

                                # تشخیص زبان
                                language = self._detect_language(line_text)

                                # ایجاد شیء متن استخراج شده
                                extracted_text = ExtractedText(
                                    text=line_text,
                                    page_num=page_num,
                                    bbox=(x0, y0, x1, y1),
                                    language=language,
                                    confidence=0.95
                                )

                                self.extracted_texts.append(extracted_text)
                        else:
                            # اگر کاراکترها موجود نباشند، کل متن صفحه را ذخیره می‌کنیم
                            extracted_text = ExtractedText(
                                text=text,
                                page_num=page_num,
                                bbox=page.bbox,
                                language=self._detect_language(text),
                                confidence=0.9
                            )
                            self.extracted_texts.append(extracted_text)

                    # به‌روزرسانی آمار
                    self.stats.languages_detected.extend(self._detect_languages_in_text(text))

                except Exception as e:
                    print(f"خطا در استخراج متن صفحه {page_num}: {e}")

    def _extract_text_with_ocr(self):
        """استخراج متن با استفاده از OCR"""
        try:
            # تبدیل PDF به تصاویر
            images = convert_from_path(self.pdf_path, dpi=self.image_dpi)

            for page_num, image in enumerate(images, 1):
                # تبدیل به OpenCV format
                open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

                # پیش‌پردازش تصویر برای بهبود OCR
                gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                # اعمال OCR
                config = f'--oem 3 --psm 6 -l {"+".join(self.ocr_languages)}'
                ocr_result = pytesseract.image_to_data(
                    thresh,
                    output_type=pytesseract.Output.DICT,
                    config=config
                )

                # پردازش نتایج OCR
                n_boxes = len(ocr_result['text'])
                for i in range(n_boxes):
                    if int(ocr_result['conf'][i]) > 60:  # اطمینان بالای 60%
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
            print(f"خطا در OCR: {e}")

    def _extract_text_fallback(self):
        """روش جایگزین برای استخراج متن"""
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
            print(f"خطا در روش جایگزین استخراج متن: {e}")

    def extract_tables(self) -> list[ExtractedTable]:
        """
        استخراج جداول از PDF
        
        Returns:
            لیست جداول استخراج شده
        """
        self.extracted_tables = []

        try:
            # روش ۱: استفاده از Camelot
            self._extract_tables_camelot()

            # روش ۲: استفاده از pdfplumber (اگر Camelot جواب نداد)
            if not self.extracted_tables:
                self._extract_tables_pdfplumber()

        except Exception as e:
            print(f"خطا در استخراج جداول: {e}")

        return self.extracted_tables

    def _extract_tables_camelot(self):
        """استخراج جداول با Camelot"""
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
                    # تبدیل داده‌های جدول
                    table_data = []
                    for row in table.df.values.tolist():
                        table_data.append([str(cell) if cell is not None else "" for cell in row])

                    # ایجاد شیء جدول استخراج شده
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
            print(f"خطا در استخراج جداول با Camelot: {e}")

    def _extract_tables_pdfplumber(self):
        """استخراج جداول با pdfplumber"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()

                    for table in tables:
                        if table:
                            # محاسبه تقریبی bounding box
                            bbox = page.bbox

                            # ایجاد شیء جدول استخراج شده
                            extracted_table = ExtractedTable(
                                page_num=page_num,
                                bbox=bbox,
                                data=table,
                                table_type="stream",
                                accuracy=0.7
                            )

                            self.extracted_tables.append(extracted_table)

        except Exception as e:
            print(f"خطا در استخراج جداول با pdfplumber: {e}")

    def extract_images(self,
                      min_size: tuple[int, int] = (50, 50),
                      max_images_per_page: int = 20) -> list[ExtractedImage]:
        """
        استخراج تصاویر از PDF
        
        Args:
            min_size: حداقل ابعاد تصویر (عرض، ارتفاع)
            max_images_per_page: حداکثر تعداد تصویر در هر صفحه
            
        Returns:
            لیست تصاویر استخراج شده
        """
        self.extracted_images = []

        try:
            if HAS_PYMUPDF:
                self._extract_images_pymupdf(min_size, max_images_per_page)
            else:
                self._extract_images_pdfplumber(min_size, max_images_per_page)

        except Exception as e:
            print(f"خطا در استخراج تصاویر: {e}")

        return self.extracted_images

    def _extract_images_pymupdf(self, min_size: tuple[int, int], max_images_per_page: int):
        """استخراج تصاویر با PyMuPDF"""
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

                    # بررسی حداقل اندازه
                    if width >= min_size[0] and height >= min_size[1]:
                        image_format = base_image["ext"]

                        # ایجاد شیء تصویر استخراج شده
                        extracted_image = ExtractedImage(
                            page_num=page_num + 1,
                            bbox=(0, 0, width, height),  # موقعیت دقیق نیاز به پردازش بیشتر دارد
                            image_data=image_data,
                            image_format=image_format.upper(),
                            width=width,
                            height=height,
                            dpi=(72, 72)
                        )

                        self.extracted_images.append(extracted_image)

        doc.close()

    def _extract_images_pdfplumber(self, min_size: tuple[int, int], max_images_per_page: int):
        """استخراج تصاویر با pdfplumber"""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                images = page.images

                for img_index, img in enumerate(images[:max_images_per_page]):
                    if 'stream' in img:
                        image_data = img['stream'].get_data()

                        if image_data:
                            width = img.get('width', 0)
                            height = img.get('height', 0)

                            # بررسی حداقل اندازه
                            if width >= min_size[0] and height >= min_size[1]:
                                image_format = self._detect_image_format(image_data)

                                # ایجاد شیء تصویر استخراج شده
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
        استخراج لینک‌ها از PDF
        
        Returns:
            لیست لینک‌های استخراج شده
        """
        self.extracted_links = []

        try:
            if HAS_PYMUPDF:
                self._extract_links_pymupdf()
            else:
                self._extract_links_pdfplumber()

        except Exception as e:
            print(f"خطا در استخراج لینک‌ها: {e}")

        return self.extracted_links

    def _extract_links_pymupdf(self):
        """استخراج لینک‌ها با PyMuPDF"""
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
        """استخراج لینک‌ها با pdfplumber"""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # pdfplumber لینک‌ها را مستقیماً پشتیبانی نمی‌کند
                # می‌توان از متن استخراج شده لینک‌ها را پیدا کرد
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
        استخراج حاشیه‌نویسی‌ها از PDF
        
        Returns:
            لیست حاشیه‌نویسی‌های استخراج شده
        """
        self.extracted_annotations = []

        try:
            if HAS_PYMUPDF:
                self._extract_annotations_pymupdf()

        except Exception as e:
            print(f"خطا در استخراج حاشیه‌نویسی‌ها: {e}")

        return self.extracted_annotations

    def _extract_annotations_pymupdf(self):
        """استخراج حاشیه‌نویسی‌ها با PyMuPDF"""
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
        """تشخیص معادلات ریاضی و بلوک‌های کد"""
        # الگوهای معادلات ریاضی
        equation_patterns = [
            r'\$[^$]+\$',  # معادلات inline
            r'\\\[.*?\\\]',  # معادلات display
            r'\\\(.*?\\\)',  # معادلات inline با LaTeX
            r'\\begin\{equation\}.*?\\end\{equation\}',
            r'\\begin\{align\}.*?\\end\{align\}',
            r'\\frac\{.*?\}\{.*?\}',  # کسرها
            r'\\sum_\{.*?\}\^\{.*?\}',  # سیگما
            r'\\int_\{.*?\}\^\{.*?\}',  # انتگرال
        ]

        # الگوهای بلوک‌های کد
        code_patterns = [
            r'```.*?```',  # بلوک کد با backticks
            r'def\s+\w+\(.*?\):',  # تعریف تابع پایتون
            r'function\s+\w+\(.*?\)\s*\{',  # تعریف تابع جاوااسکریپت
            r'class\s+\w+',  # تعریف کلاس
            r'import\s+\w+',  # import statement
            r'#include\s+<.*?>',  # include در C++
            r'public\s+class',  # کلاس در جاوا
        ]

        for text_obj in self.extracted_texts:
            text = text_obj.text

            # بررسی معادلات ریاضی
            for pattern in equation_patterns:
                if re.search(pattern, text, re.DOTALL):
                    text_obj.structural_type = "equation"
                    self.stats.equations += 1
                    break

            # بررسی بلوک‌های کد
            for pattern in code_patterns:
                if re.search(pattern, text):
                    text_obj.structural_type = "code_block"
                    self.stats.code_blocks += 1
                    break

    def extract_metadata(self) -> dict[str, Any]:
        """
        استخراج متادیتای PDF
        
        Returns:
            دیکشنری متادیتا
        """
        metadata = {}

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # متادیتای اصلی
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

                # اطلاعات اضافی
                # Access attributes from the PDF stream object (pdfplumber's internal PDF object)
                metadata['pdf_version'] = getattr(pdf.stream, 'pdf_version', None)
                metadata['is_encrypted'] = getattr(pdf.stream, 'is_encrypted', False)

                # جمع‌آوری اطلاعات فونت‌ها
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
            print(f"خطا در استخراج متادیتا: {e}")
            metadata['error'] = str(e)

        return metadata

    def export_to_json(self, output_path: str):
        """
        خروجی نتایج به فرمت JSON
        
        Args:
            output_path: مسیر فایل خروجی
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

        # حذف image_data از JSON (حجم زیاد)
        for img in results['images']:
            if 'image_data' in img:
                del img['image_data']

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    def export_to_csv(self, output_dir: str | Path):
        """
        خروجی نتایج به فرمت CSV
        
        Args:
            output_dir: دایرکتوری خروجی
        """
        import csv

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # ذخیره متن‌ها
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

        # ذخیره جداول
        if self.extracted_tables and HAS_PANDAS:
            for i, table in enumerate(self.extracted_tables):
                table_path = output_dir / f"table_{i+1}.csv"
                table.to_csv(str(table_path))

    def _detect_language(self, text: str) -> str:
        """
        تشخیص زبان متن
        
        Args:
            text: متن ورودی
            
        Returns:
            کد زبان ('fa', 'en', 'ar', 'mixed')
        """
        if not text.strip():
            return 'unknown'

        # کاراکترهای فارسی/عربی
        persian_arabic_chars = re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text)

        # کاراکترهای انگلیسی
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
        """تشخیص زبان‌های موجود در متن"""
        languages = set()

        # تقسیم متن به جملات
        sentences = re.split(r'[.!?]', text)

        for sentence in sentences:
            lang = self._detect_language(sentence)
            if lang != 'unknown':
                languages.add(lang)

        return list(languages)

    def _extract_urls_from_text(self, text: str) -> list[str]:
        """استخراج URL از متن"""
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.\-?=&%#+]*'
        return re.findall(url_pattern, text)

    def _detect_image_format(self, image_data: bytes) -> str:
        """تشخیص فرمت تصویر"""
        try:
            image = Image.open(io.BytesIO(image_data))
            return image.format or 'UNKNOWN'
        except:
            return 'UNKNOWN'

    def get_summary(self) -> dict[str, Any]:
        """
        دریافت خلاصه‌ای از نتایج استخراج
        
        Returns:
            دیکشنری خلاصه نتایج
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


# تابع کمکی برای استفاده سریع
def extract_content_from_pdf(pdf_path: str,
                           use_ocr: bool = False,
                           output_json: str | None = None,
                           output_dir: str | None = None) -> dict[str, Any]:
    """
    تابع کمکی برای استخراج محتوای PDF
    
    Args:
        pdf_path: مسیر فایل PDF
        use_ocr: استفاده از OCR
        output_json: مسیر ذخیره JSON (اختیاری)
        output_dir: دایرکتوری ذخیره CSV و تصاویر (اختیاری)
        
    Returns:
        نتایج استخراج
    """
    extractor = ContentExtractor(pdf_path, use_ocr=use_ocr)
    results = extractor.extract_all()

    # ذخیره خروجی JSON
    if output_json:
        extractor.export_to_json(output_json)

    # ذخیره خروجی CSV
    if output_dir:
        extractor.export_to_csv(output_dir)

        # ذخیره تصاویر
        images_dir = Path(output_dir) / "images"
        images_dir.mkdir(exist_ok=True)

        for i, image in enumerate(extractor.extracted_images):
            image_path = images_dir / f"image_{i+1}_{image.page_num}.{image.image_format.lower()}"
            image.save(str(image_path))

    return results


# if __name__ == "__main__":
#     # مثال استفاده
#     pdf_path = "sample.pdf"

#     # ایجاد نمونه استخراج کننده
#     extractor = ContentExtractor(pdf_path, use_ocr=True)

#     # استخراج تمام محتوا
#     results = extractor.extract_all()

#     # نمایش خلاصه
#     summary = extractor.get_summary()
#     print("📊 خلاصه استخراج:")
#     for key, value in summary.items():
#         print(f"  {key}: {value}")

#     # ذخیره نتایج
#     extractor.export_to_json("extraction_results.json")
#     extractor.export_to_csv("extraction_output")

#     print(f"✅ استخراج کامل شد! نتایج در extraction_results.json ذخیره شد.")
