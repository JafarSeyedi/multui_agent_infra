"""
PDF Parser - تبدیل PDF به مدل USDM
"""

import io
import logging
from typing import Dict, List, Optional, Any, BinaryIO, Union
from dataclasses import dataclass, field
from pathlib import Path
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
import hashlib
import base64

from ..models.base import BaseParser, ParserResult
from ..models.usdm_models import (
    USDMDocument, Page, TextRun, ImageObject, VectorPath, 
    ParagraphContent, HeadingContent, TableContent, 
    ImageContent, ListContent, MathContent, StyleSheet,
    CharacterStyle, ParagraphStyle, TableStyle, ListStyle,
    AnnotationObject, LinkContent, FootnoteContent,
    CommentContent, DrawingContent, BinaryContent
)
from ..models.standard import DocumentMetadata, MediaType

logger = logging.getLogger(__name__)


@dataclass
class PDFParseOptions:
    """گزینه‌های پارس PDF"""
    extract_images: bool = True
    extract_tables: bool = True
    extract_annotations: bool = True
    extract_metadata: bool = True
    preserve_layout: bool = True
    ocr_enabled: bool = False
    ocr_language: str = "fas+eng"
    image_dpi: int = 300
    table_strategy: str = "lines"  # "lines", "text", "lattice"
    include_font_info: bool = True
    include_links: bool = True


class PDFParser(BaseParser):
    """پارسر PDF با استفاده از PyMuPDF و pdfplumber"""
    
    def __init__(self, options: Optional[PDFParseOptions] = None):
        super().__init__()
        self.options = options or PDFParseOptions()
        self.supported_formats = [".pdf"]
        
    def parse(self, source: Union[str, Path, BinaryIO, bytes], 
              options: Optional[Dict[str, Any]] = None) -> ParserResult:
        """
        پارس فایل PDF و تبدیل به USDMDocument
        
        Args:
            source: مسیر فایل، بایت‌ها یا استریم
            options: گزینه‌های اضافی پارس
            
        Returns:
            ParserResult حاوی USDMDocument
        """
        try:
            # اعمال گزینه‌های اضافی
            parse_options = self._merge_options(options)
            
            # بارگذاری PDF
            pdf_doc, pdf_bytes = self._load_pdf(source)
            
            # استخراج متادیتا
            metadata = self._extract_metadata(pdf_doc, pdf_bytes)
            
            # استخراج صفحات و محتوا
            usdm_document = self._extract_content(pdf_doc, parse_options)
            
            # تنظیم متادیتا
            usdm_document.metadata = metadata
            
            # محاسبه هش
            document_hash = self._calculate_hash(pdf_bytes)
            
            return ParserResult(
                document=usdm_document,
                metadata=metadata,
                raw_data=pdf_bytes,
                document_hash=document_hash,
                warnings=[] if pdf_doc.is_pdf else ["فایل ممکن است PDF معتبر نباشد"]
            )
            
        except Exception as e:
            logger.error(f"خطا در پارس PDF: {e}", exc_info=True)
            raise
    
    def _load_pdf(self, source: Union[str, Path, BinaryIO, bytes]) -> tuple:
        """بارگذاری PDF و برگرداندن document و bytes"""
        if isinstance(source, (str, Path)):
            with open(source, 'rb') as f:
                pdf_bytes = f.read()
            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        elif isinstance(source, bytes):
            pdf_bytes = source
            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        elif hasattr(source, 'read'):
            pdf_bytes = source.read()
            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        else:
            raise ValueError("فرمت منبع پشتیبانی نمی‌شود")
        
        return pdf_doc, pdf_bytes
    
    def _merge_options(self, options: Optional[Dict[str, Any]]) -> PDFParseOptions:
        """ادغام گزینه‌ها"""
        if not options:
            return self.options
        
        merged = PDFParseOptions(**self.options.__dict__)
        for key, value in options.items():
            if hasattr(merged, key):
                setattr(merged, key, value)
        
        return merged
    
    def _extract_metadata(self, pdf_doc: fitz.Document, pdf_bytes: bytes) -> DocumentMetadata:
        """استخراج متادیتای PDF"""
        metadata = DocumentMetadata(
            format_type="application/pdf",
            media_type=MediaType.DOCUMENT
        )
        
        # متادیتای استاندارد PDF
        pdf_metadata = pdf_doc.metadata
        if pdf_metadata:
            metadata.title = pdf_metadata.get('title')
            metadata.author = pdf_metadata.get('author')
            metadata.subject = pdf_metadata.get('subject')
            metadata.keywords = pdf_metadata.get('keywords', '').split(',') if pdf_metadata.get('keywords') else []
            metadata.creator = pdf_metadata.get('creator')
            metadata.producer = pdf_metadata.get('producer')
            
            # تاریخ‌ها
            creation_date = pdf_metadata.get('creationDate')
            mod_date = pdf_metadata.get('modDate')
            
            if creation_date:
                metadata.creation_date = self._parse_pdf_date(creation_date)
            if mod_date:
                metadata.modification_date = self._parse_pdf_date(mod_date)
        
        # اطلاعات فنی
        metadata.page_count = pdf_doc.page_count
        metadata.is_encrypted = pdf_doc.is_encrypted
        metadata.is_pdf = pdf_doc.is_pdf
        
        # اطلاعات فایل
        metadata.file_size = len(pdf_bytes)
        
        # اطلاعات فونت‌ها (اگر موجود باشد)
        fonts = set()
        for page_num in range(min(3, pdf_doc.page_count)):  # فقط 3 صفحه اول برای نمونه
            page = pdf_doc[page_num]
            font_info = page.get_fonts()
            for font in font_info:
                fonts.add(font[3])  # نام فونت
        metadata.fonts = list(fonts)
        
        return metadata
    
    def _parse_pdf_date(self, pdf_date: str) -> Optional[str]:
        """تبدیل تاریخ PDF به فرمت استاندارد"""
        # پیاده‌سازی ساده - در واقعیت نیاز به پارس کامل دارد
        try:
            # فرمت: D:YYYYMMDDHHmmSSOHH'mm'
            if pdf_date.startswith('D:'):
                date_str = pdf_date[2:]
                year = date_str[:4]
                month = date_str[4:6] if len(date_str) >= 6 else '01'
                day = date_str[6:8] if len(date_str) >= 8 else '01'
                return f"{year}-{month}-{day}"
        except:
            pass
        return None
    
    def _extract_content(self, pdf_doc: fitz.Document, options: PDFParseOptions) -> USDMDocument:
        """استخراج محتوای PDF"""
        usdm_document = USDMDocument()
        style_sheet = StyleSheet()
        
        # استخراج هر صفحه
        for page_num in range(pdf_doc.page_count):
            page = pdf_doc[page_num]
            usdm_page = self._extract_page(page, page_num, options, style_sheet)
            usdm_document.pages.append(usdm_page)
            
            # استخراج عناصر منطقی از صفحه
            logical_elements = self._extract_logical_elements(page, page_num, options)
            usdm_document.logical_elements.extend(logical_elements)
        
        # استخراج ساختار سند (اگر موجود باشد)
        if pdf_doc.has_links() or pdf_doc.has_toc():
            structure = self._extract_structure(pdf_doc)
            usdm_document.sections = structure
        
        usdm_document.stylesheet = style_sheet
        return usdm_document
    
    def _extract_page(self, page: fitz.Page, page_num: int, 
                      options: PDFParseOptions, style_sheet: StyleSheet) -> Page:
        """استخراج یک صفحه PDF"""
        usdm_page = Page(
            page_number=page_num + 1,
            width=page.rect.width,
            height=page.rect.height,
            rotation=page.rotation
        )
        
        # استخراج متن
        text_blocks = page.get_text("dict")["blocks"]
        for block in text_blocks:
            if block["type"] == 0:  # متن
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text_run = self._create_text_run(span, page_num, style_sheet)
                        if text_run:
                            usdm_page.elements.append(text_run)
        
        # استخراج تصاویر
        if options.extract_images:
            images = page.get_images()
            for img_index, img_info in enumerate(images):
                image_object = self._extract_image(page, img_info, img_index, page_num)
                if image_object:
                    usdm_page.elements.append(image_object)
        
        # استخراج مسیرهای برداری
        drawings = page.get_drawings()
        for drawing in drawings:
            vector_path = self._extract_vector_path(drawing, page_num)
            if vector_path:
                usdm_page.elements.append(vector_path)
        
        # استخراج حاشیه‌نویسی‌ها
        if options.extract_annotations:
            annotations = page.annots()
            for annot in annotations:
                annotation = self._extract_annotation(annot, page_num)
                if annotation:
                    usdm_page.elements.append(annotation)
        
        return usdm_page
    
    def _create_text_run(self, span: Dict, page_num: int, style_sheet: StyleSheet) -> Optional[TextRun]:
        """ایجاد TextRun از span متن"""
        try:
            text = span.get("text", "").strip()
            if not text:
                return None
            
            # ایجاد استایل کاراکتر
            font_name = span.get("font", "unknown")
            font_size = span.get("size", 12)
            color = span.get("color", 0)
            
            # تبدیل رنگ PDF به hex
            color_hex = self._color_to_hex(color)
            
            # ایجاد یا بازیابی استایل
            style_id = f"char_{font_name}_{font_size}_{color_hex}"
            if style_id not in style_sheet.character_styles:
                char_style = CharacterStyle(
                    id=style_id,
                    font_family=font_name,
                    font_size=font_size,
                    color=color_hex,
                    bold="Bold" in font_name,
                    italic="Italic" in font_name or "Oblique" in font_name
                )
                style_sheet.character_styles[style_id] = char_style
            
            # موقعیت
            bbox = span.get("bbox", [0, 0, 0, 0])
            
            return TextRun(
                text=text,
                bbox={
                    "x": bbox[0],
                    "y": bbox[1],
                    "width": bbox[2] - bbox[0],
                    "height": bbox[3] - bbox[1]
                },
                page_number=page_num + 1,
                style_id=style_id,
                language=self._detect_language(text)
            )
        except Exception as e:
            logger.warning(f"خطا در ایجاد TextRun: {e}")
            return None
    
    def _color_to_hex(self, color: int) -> str:
        """تبدیل رنگ PDF به hex"""
        if color == 0:
            return "#000000"
        
        # رنگ PDF به صورت 0xRRGGBB است
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _detect_language(self, text: str) -> str:
        """تشخیص زبان متن (ساده)"""
        # پیاده‌سازی ساده - در واقعیت از کتابخانه‌هایی مثل langdetect استفاده کنید
        persian_chars = set('آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی')
        if any(char in persian_chars for char in text[:100]):
            return "fa"
        return "en"
    
    def _extract_image(self, page: fitz.Page, img_info: tuple, 
                       img_index: int, page_num: int) -> Optional[ImageObject]:
        """استخراج تصویر از صفحه"""
        try:
            xref = img_info[0]
            base_image = page.parent.extract_image(xref)
            
            if base_image:
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # ایجاد هش برای تصویر
                image_hash = hashlib.sha256(image_bytes).hexdigest()[:16]
                
                # کدگذاری base64
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                # اطلاعات ابعاد
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)
                
                return ImageObject(
                    id=f"img_{page_num}_{img_index}",
                    image_data=image_base64,
                    format=image_ext,
                    width=width,
                    height=height,
                    bbox={"x": 0, "y": 0, "width": width, "height": height},  # نیاز به موقعیت واقعی دارد
                    page_number=page_num + 1,
                    metadata={
                        "hash": image_hash,
                        "colorspace": base_image.get("colorspace", ""),
                        "bpc": base_image.get("bpc", 8)
                    }
                )
        except Exception as e:
            logger.warning(f"خطا در استخراج تصویر: {e}")
        
        return None
    
    def _extract_vector_path(self, drawing: Dict, page_num: int) -> Optional[VectorPath]:
        """استخراج مسیر برداری"""
        try:
            # استخراج نقاط مسیر
            points = []
            for item in drawing.get("items", []):
                if item[0] == "l":  # خط
                    points.extend([{"x": item[1], "y": item[2]}])
                elif item[0] == "c":  # منحنی بزیه
                    points.extend([
                        {"x": item[1], "y": item[2]},
                        {"x": item[3], "y": item[4]},
                        {"x": item[5], "y": item[6]}
                    ])
            
            if not points:
                return None
            
            return VectorPath(
                id=f"path_{page_num}_{hash(str(points))[:8]}",
                points=points,
                stroke_color=self._color_to_hex(drawing.get("color", 0)),
                stroke_width=drawing.get("width", 1.0),
                fill_color=self._color_to_hex(drawing.get("fill", 0)) if drawing.get("fill") else None,
                page_number=page_num + 1,
                bbox=self._calculate_bbox(points)
            )
        except Exception as e:
            logger.warning(f"خطا در استخراج مسیر برداری: {e}")
            return None
    
    def _calculate_bbox(self, points: List[Dict]) -> Dict:
        """محاسبه bounding box از نقاط"""
        if not points:
            return {"x": 0, "y": 0, "width": 0, "height": 0}
        
        xs = [p["x"] for p in points]
        ys = [p["y"] for p in points]
        
        return {
            "x": min(xs),
            "y": min(ys),
            "width": max(xs) - min(xs),
            "height": max(ys) - min(ys)
        }
    
    def _extract_annotation(self, annot: fitz.Annot, page_num: int) -> Optional[AnnotationObject]:
        """استخراج حاشیه‌نویسی"""
        try:
            annot_type = annot.type[1]  # نوع حاشیه‌نویسی
            rect = annot.rect
            
            # استخراج محتوا بر اساس نوع
            content = ""
            if annot_type in [fitz.PDF_ANNOT_TEXT, fitz.PDF_ANNOT_FREE_TEXT]:
                content = annot.info.get("content", "")
            elif annot_type == fitz.PDF_ANNOT_HIGHLIGHT:
                content = "Highlight"
            
            return AnnotationObject(
                id=f"annot_{page_num}_{annot.xref}",
                annotation_type=annot_type,
                content=content,
                bbox={
                    "x": rect.x0,
                    "y": rect.y0,
                    "width": rect.width,
                    "height": rect.height
                },
                page_number=page_num + 1,
                metadata={
                    "author": annot.info.get("title", ""),
                    "created": annot.info.get("creationDate", ""),
                    "modified": annot.info.get("modDate", "")
                }
            )
        except Exception as e:
            logger.warning(f"خطا در استخراج حاشیه‌نویسی: {e}")
            return None
    
    def _extract_logical_elements(self, page: fitz.Page, page_num: int, 
                                  options: PDFParseOptions) -> List:
        """استخراج عناصر منطقی از صفحه"""
        elements = []
        
        # استفاده از pdfplumber برای استخراج ساختاریافته‌تر
        try:
            with pdfplumber.open(stream=page.parent.write()) as pdf:
                pdf_page = pdf.pages[page_num]
                
                # استخراج جداول
                if options.extract_tables:
                    tables = pdf_page.extract_tables({
                        "vertical_strategy": options.table_strategy,
                        "horizontal_strategy": options.table_strategy
                    })
                    
                    for table_idx, table_data in enumerate(tables):
                        if table_data:
                            table_content = TableContent(
                                id=f"table_{page_num}_{table_idx}",
                                rows=table_data,
                                page_number=page_num + 1,
                                metadata={
                                    "strategy": options.table_strategy,
                                    "row_count": len(table_data),
                                    "col_count": len(table_data[0]) if table_data else 0
                                }
                            )
                            elements.append(table_content)
                
                # استخراج متن ساختاریافته
                text = pdf_page.extract_text()
                if text:
                    # تقسیم به پاراگراف‌ها (ساده)
                    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                    for para_idx, para_text in enumerate(paragraphs):
                        if len(para_text.split()) > 1:  # حداقل دو کلمه
                            paragraph = ParagraphContent(
                                id=f"para_{page_num}_{para_idx}",
                                text=para_text,
                                page_number=page_num + 1,
                                language=self._detect_language(para_text)
                            )
                            elements.append(paragraph)
        
        except Exception as e:
            logger.warning(f"خطا در استخراج عناصر منطقی با pdfplumber: {e}")
        
        return elements
    
    def _extract_structure(self, pdf_doc: fitz.Document) -> List[Dict]:
        """استخراج ساختار سند (TOC)"""
        structure = []
        
        try:
            # استخراج TOC
            toc = pdf_doc.get_toc()
            for level, title, page_num in toc:
                structure.append({
                    "level": level,
                    "title": title,
                    "page": page_num,
                    "type": "heading"
                })
        except:
            pass
        
        return structure
    
    def _calculate_hash(self, data: bytes) -> str:
        """محاسبه هش سند"""
        return hashlib.sha256(data).hexdigest()
