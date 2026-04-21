# engines/document/writers/pdf_writer.py

"""
PDF Writer - تبدیل USDMDocument به PDF با پشتیبانی کامل از انکریپشن، اپتیمایزر و اوتلاین
"""

import io
import os
import tempfile
import hashlib
import asyncio
import struct
import zlib
from typing import Dict, List, Optional, Any, BinaryIO, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..base.writer import BaseDocumentWriter, WriteOptions
from ..models.usdm_models import USDMDocument
from .pdf_writer.content_writer import ContentWriter
from .pdf_writer.font_manager import FontManager
from .pdf_writer.layout_builder import LayoutBuilder, PageLayout
from .pdf_writer.metadata_writer import MetadataWriter
from .pdf_writer.pdf_objects import PDFObjectFactory, PDFPage, PDFCatalog, PDFInfo, PDFStream, PDFDictionary, PDFObject
from .pdf_writer.utils import ColorConverter, UnitConverter, ImageProcessor
from .pdf_writer.annotation_writer import AnnotationWriter, Annotation
from .pdf_writer.encryption import PDFEncryptor
from .pdf_writer.optimizer import PDFOptimizer
from .pdf_writer.outline_generator import OutlineGenerator


@dataclass
class PDFWriteOptions(WriteOptions):
    """گزینه‌های نوشتن PDF"""
    
    # گزینه‌های صفحه
    page_size: str = "A4"  # A4, letter, legal, A3, A5, B4, B5
    page_orientation: str = "portrait"  # portrait, landscape
    margin_top: float = 72.0  # points (1 inch = 72 points)
    margin_bottom: float = 72.0
    margin_left: float = 72.0
    margin_right: float = 72.0
    
    # گزینه‌های فونت
    default_font_family: str = "Helvetica"
    embed_fonts: bool = True
    font_subsetting: bool = True
    
    # گزینه‌های تصویر
    image_quality: int = 85  # 0-100
    image_compression: str = "auto"  # auto, jpeg, flate, none
    max_image_resolution: int = 300  # DPI
    
    # گزینه‌های متادیتا
    include_metadata: bool = True
    include_xmp: bool = True
    producer: str = "USDM PDF Writer"
    
    # گزینه‌های امنیتی
    encrypt: bool = False
    owner_password: Optional[str] = None
    user_password: Optional[str] = None
    permissions: List[str] = field(default_factory=lambda: [
        "print", "modify", "copy", "annotate", "fill_forms", "extract", "assemble", "print_high"
    ])
    
    # گزینه‌های اوتلاین
    create_outline: bool = True
    outline_depth: int = 3  # عمق اوتلاین
    
    # گزینه‌های بهینه‌سازی
    optimize: bool = True
    compress_streams: bool = True
    remove_unused_objects: bool = True
    merge_duplicate_streams: bool = True
    
    # گزینه‌های حاشیه‌نویسی
    preserve_annotations: bool = True
    
    # گزینه‌های دیباگ
    debug_mode: bool = False
    validate_pdf: bool = True
    
    # گزینه‌های رمزنگاری
    encryption_algorithm: str = "AES-256"  # AES-256, AES-128, RC4-128
    key_length: int = 256  # طول کلید بر حسب بیت


class PDFWriter(BaseDocumentWriter):
    """کلاس اصلی برای نوشتن PDF با پشتیبانی کامل"""
    
    def __init__(self, options: Optional[PDFWriteOptions] = None):
        super().__init__(options or PDFWriteOptions())
        self.options = options or PDFWriteOptions()
        
        # ماژول‌های کمکی
        self.unit_converter = UnitConverter()
        self.color_converter = ColorConverter()
        self.image_processor = ImageProcessor()
        self.font_manager = FontManager()
        self.layout_builder = LayoutBuilder(self.unit_converter)
        self.metadata_writer = MetadataWriter()
        self.content_writer = ContentWriter(self.font_manager, self.unit_converter)
        self.annotation_writer = AnnotationWriter()
        self.encryptor = PDFEncryptor()
        self.optimizer = PDFOptimizer()
        self.outline_generator = OutlineGenerator()
        self.pdf_factory = PDFObjectFactory()
        
        # وضعیت نوشتن
        self.objects: List[PDFObject] = []
        self.object_offsets: Dict[int, int] = {}
        self.current_object_num = 1
        self.xref_table: List[str] = []
        self.trailer_dict: Dict[str, Any] = {}
        
        # منابع
        self.resources: Dict[str, Any] = {
            'fonts': {},
            'images': {},
            'xobjects': {},
            'patterns': {},
            'shadings': {},
            'extgstate': {}
        }
        
        # صفحات
        self.pages: List[PDFPage] = []
        self.page_refs: Dict[int, str] = {}
        
        # اوتلاین
        self.outline_items: List[Dict[str, Any]] = []
        
        # انکریپشن
        self.encryption_dict: Optional[Dict[str, Any]] = None
        self.encryption_key: Optional[bytes] = None
        
    async def write_stream(self, document: USDMDocument) -> AsyncIterator[bytes]:
        """
        نوشتن سند به صورت استریم باینری
        
        Args:
            document: سند USDM
            
        Yields:
            بایت‌های PDF
        """
        try:
            # مرحله 1: آماده‌سازی اولیه
            yield b"%PDF-1.7\n%\xc2\xb5\xc2\xb6\n\n"
            
            # مرحله 2: آماده‌سازی انکریپشن (اگر فعال باشد)
            if self.options.encrypt:
                await self._prepare_encryption()
                yield from self._write_encryption_header()
            
            # مرحله 3: ایجاد منابع
            await self._prepare_resources(document)
            yield from self._write_resources()
            
            # مرحله 4: ایجاد صفحات
            await self._create_pages(document)
            yield from self._write_pages()
            
            # مرحله 5: ایجاد اوتلاین
            if self.options.create_outline:
                await self._create_outline(document)
                yield from self._write_outline()
            
            # مرحله 6: نوشتن متادیتا
            if self.options.include_metadata:
                yield from self._write_metadata(document)
            
            # مرحله 7: نوشتن حاشیه‌نویسی‌ها
            if self.options.preserve_annotations and hasattr(document, 'annotations'):
                yield from self._write_annotations(document)
            
            # مرحله 8: نوشتن ساختار سند
            yield from self._write_document_structure()
            
            # مرحله 9: نوشتن کراس‌رفرنس
            yield from self._write_xref_table()
            
            # مرحله 10: نوشتن تریلر
            yield from self._write_trailer()
            
            # مرحله 11: بهینه‌سازی (اگر فعال باشد)
            if self.options.optimize:
                yield from self._optimize_stream()
            
        except Exception as e:
            raise Exception(f"خطا در نوشتن PDF: {e}")
    
    async def write(self, document: BaseDocument) -> bytes:
        """
        نوشتن سند و بازگرداندن بایت‌ها
        
        Args:
            document: سند USDM
            
        Returns:
            بایت‌های PDF
        """
        if not isinstance(document, USDMDocument):
            raise TypeError("سند باید از نوع USDMDocument باشد")
        
        chunks = []
        async for chunk in self.write_stream(document):
            chunks.append(chunk)
        
        # ترکیب تمام chunk ها
        pdf_bytes = b''.join(chunks)
        
        # اعمال انکریپشن نهایی اگر نیاز باشد
        if self.options.encrypt and self.encryption_key:
            pdf_bytes = self.encryptor.encrypt_document(pdf_bytes, self.encryption_key)
        
        return pdf_bytes
    
    async def write_to_file(
        self, 
        document: BaseDocument, 
        target: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        نوشتن سند به فایل
        
        Args:
            document: سند USDM
            target: مسیر فایل خروجی
            options: گزینه‌های اضافی
        """
        if not isinstance(document, USDMDocument):
            raise TypeError("سند باید از نوع USDMDocument باشد")
        
        # اعمال گزینه‌های اضافی
        if options:
            for key, value in options.items():
                if hasattr(self.options, key):
                    setattr(self.options, key, value)
        
        # تولید PDF
        pdf_bytes = await self.write(document)
        
        # نوشتن به فایل
        with open(target, 'wb') as f:
            f.write(pdf_bytes)
        
        # اعتبارسنجی PDF اگر نیاز باشد
        if self.options.validate_pdf:
            await self._validate_pdf(target)
    
    def get_supported_media_types(self) -> List[str]:
        """دریافت لیست media type های پشتیبانی شده"""
        return [
            "application/pdf",
            "application/x-pdf"
        ]
    
    def get_supported_extensions(self) -> List[str]:
        """دریافت لیست پسوندهای پشتیبانی شده"""
        return [".pdf"]
    
    async def _prepare_encryption(self):
        """آماده‌سازی انکریپشن"""
        if not self.options.encrypt:
            return
        
        # تولید کلید انکریپشن
        self.encryption_key = self.encryptor.generate_encryption_key(
            owner_password=self.options.owner_password,
            user_password=self.options.user_password,
            key_length=self.options.key_length
        )
        
        # ایجاد دیکشنری انکریپشن
        self.encryption_dict = self.encryptor.create_encryption_dict(
            key_length=self.options.key_length,
            permissions=self.options.permissions
        )
    
    async def _write_encryption_header(self) -> AsyncIterator[bytes]:
        """نوشتن هدر انکریپشن"""
        if not self.encryption_dict:
            return
        
        encryption_obj = self.pdf_factory.create_dictionary(self.encryption_dict)
        encryption_obj.obj_id = self._get_next_object_num()
        
        # نوشتن شیء انکریپشن
        yield self._object_to_bytes(encryption_obj)
        
        # ذخیره مرجع انکریپشن
        self.trailer_dict['Encrypt'] = f"{encryption_obj.obj_id} 0 R"
    
    async def _prepare_resources(self, document: USDMDocument):
        """آماده‌سازی منابع PDF"""
        # فونت‌ها
        if document.stylesheet and document.stylesheet.character_styles:
            for style_id, style in document.stylesheet.character_styles.items():
                if style.font_family:
                    font_name = self.font_manager.register_font(
                        font_family=style.font_family,
                        font_style="bold" if style.bold else "normal",
                        language=style.language or "en",
                        embed=self.options.embed_fonts,
                        subset=self.options.font_subsetting
                    )
                    self.resources['fonts'][font_name] = style
        
        # تصاویر
        for page in document.pages:
            for element in page.elements:
                if hasattr(element, 'image_data') and element.image_data:
                    image_id = f"Im{len(self.resources['images']) + 1}"
                    self.resources['images'][image_id] = element
        
        # XObjects
        self.resources['xobjects'].update(self.resources['images'])
    
    async def _write_resources(self) -> AsyncIterator[bytes]:
        """نوشتن منابع"""
        # نوشتن فونت‌ها
        if self.resources['fonts']:
            font_dict = self.font_manager.get_font_resources_dict()
            font_obj = self.pdf_factory.create_dictionary(font_dict.entries)
            font_obj.obj_id = self._get_next_object_num()
            yield self._object_to_bytes(font_obj)
            self.resources['Font'] = f"{font_obj.obj_id} 0 R"
        
        # نوشتن تصاویر
        for image_id, image_element in self.resources['images'].items():
            image_stream = self.content_writer.create_image_stream(
                image_element,
                quality=self.options.image_quality,
                compression=self.options.image_compression,
                max_resolution=self.options.max_image_resolution
            )
            if image_stream:
                image_stream.obj_id = self._get_next_object_num()
                yield self._object_to_bytes(image_stream)
                self.resources['xobjects'][image_id] = f"{image_stream.obj_id} 0 R"
        
        # نوشتن دیکشنری منابع
        resources_dict = {
            'Font': self.resources.get('Font', {}),
            'XObject': self.resources.get('xobjects', {}),
            'ProcSet': ['/PDF', '/Text', '/ImageB', '/ImageC', '/ImageI'],
            'ExtGState': self.resources.get('extgstate', {}),
            'Pattern': self.resources.get('patterns', {}),
            'Shading': self.resources.get('shadings', {})
        }
        
        resources_obj = self.pdf_factory.create_dictionary(resources_dict)
        resources_obj.obj_id = self._get_next_object_num()
        yield self._object_to_bytes(resources_obj)
        self.resources['Resources'] = f"{resources_obj.obj_id} 0 R"
    
    async def _create_pages(self, document: USDMDocument):
        """ایجاد صفحات PDF"""
        # ایجاد طرح‌بندی صفحات
        layouts = self.layout_builder.create_page_layouts(document, {
            'page_size': self.options.page_size,
            'page_orientation': self.options.page_orientation,
            'margin_top': self.options.margin_top,
            'margin_bottom': self.options.margin_bottom,
            'margin_left': self.options.margin_left,
            'margin_right': self.options.margin_right
        })
        
        # ایجاد اشیاء PDF Page
        for i, layout in enumerate(layouts):
            page_obj = self.pdf_factory.create_page(
                media_box=[0, 0, layout.width, layout.height],
                resources_ref=self.resources.get('Resources'),
                parent_ref=None  # بعداً تنظیم می‌شود
            )
            
            page_obj.obj_id = self._get_next_object_num()
            self.pages.append(page_obj)
            self.page_refs[i + 1] = f"{page_obj.obj_id} 0 R"
            
            # ایجاد محتوای صفحه
            content_streams = []
            
            # محتوای منطقی
            if document.logical_elements:
                logical_stream = await self._create_logical_content_stream(
                    document.logical_elements, 
                    document.stylesheet,
                    layout,
                    page_number=i + 1
                )
                if logical_stream:
                    logical_stream.obj_id = self._get_next_object_num()
                    content_streams.append(logical_stream)
            
            # محتوای فیزیکی
            if i < len(document.pages):
                usdm_page = document.pages[i]
                physical_stream = await self._create_physical_content_stream(
                    usdm_page,
                    layout,
                    page_number=i + 1
                )
                if physical_stream:
                    physical_stream.obj_id = self._get_next_object_num()
                    content_streams.append(physical_stream)
            
            # ترکیب استریم‌ها
            if content_streams:
                combined_stream = self._combine_page_streams(content_streams)
                combined_stream.obj_id = self._get_next_object_num()
                page_obj.contents = [f"{combined_stream.obj_id} 0 R"]
                
                # ذخیره استریم‌ها
                for stream in content_streams:
                    self.objects.append(stream)
                self.objects.append(combined_stream)
            
            # ذخیره صفحه
            self.objects.append(page_obj)
    
    async def _write_pages(self) -> AsyncIterator[bytes]:
        """نوشتن صفحات"""
        # نوشتن اشیاء صفحه
        for page_obj in self.pages:
            yield self._object_to_bytes(page_obj)
        
        # نوشتن اشیاء محتوا
        for obj in self.objects:
            if isinstance(obj, PDFStream) and 'Contents' in str(obj.data):
                yield self._object_to_bytes(obj)
    
    async def _create_logical_content_stream(self, elements: List, 
                                           stylesheet: Any,
                                           layout: PageLayout,
                                           page_number: int) -> Optional[PDFStream]:
        """ایجاد استریم محتوای منطقی"""
        stream_data = io.BytesIO()
        
        # شروع وضعیت گرافیکی
        stream_data.write(b"q\n")
        
        current_y = layout.height - layout.margin_top
        
        for element in elements:
            element_type = type(element).__name__
            
            if element_type == 'ParagraphContent':
                # نوشتن پاراگراف
                if hasattr(element, 'text_runs') and element.text_runs:
                    for text_run in element.text_runs:
                        x, y, width = self.layout_builder.calculate_text_position(
                            text_run, layout, current_y
                        )
                        
                        # به‌روزرسانی موقعیت
                        current_y = y
                        
                        # نوشتن TextRun
                        text_stream = self.content_writer.create_text_stream(
                            [text_run], stylesheet, layout.width, layout.height
                        )
                        if text_stream:
                            stream_data.write(text_stream.data)
            
            elif element_type == 'HeadingContent':
                # نوشتن هدینگ
                if hasattr(element, 'text_runs') and element.text_runs:
                    for text_run in element.text_runs:
                        x, y, width = self.layout_builder.calculate_text_position(
                            text_run, layout, current_y
                        )
                        current_y = y
                        
                        text_stream = self.content_writer.create_text_stream(
                            [text_run], stylesheet, layout.width, layout.height
                        )
                        if text_stream:
                            stream_data.write(text_stream.data)
                        
                        # اضافه کردن به اوتلاین
                        if self.options.create_outline:
                            self._add_to_outline(element, page_number, y)
            
            elif element_type == 'TableContent':
                # نوشتن جدول
                table_stream = self.content_writer.create_table_stream(
                    element, stylesheet, layout.width, layout.height
                )
                if table_stream:
                    stream_data.write(table_stream.data)
                    current_y -= 100  # فضای جدول
            
            elif element_type == 'ImageContent':
                # نوشتن تصویر
                if hasattr(element, 'image_object') and element.image_object:
                    x, y, width, height = self.layout_builder.calculate_image_position(
                        element.image_object, layout, current_y
                    )
                    current_y = y
                    
                    image_stream = self.content_writer.create_image_stream(element.image_object)
                    if image_stream:
                        stream_data.write(image_stream.data)
            
            # فاصله بین عناصر
            current_y -= 20
        
        # پایان وضعیت گرافیکی
        stream_data.write(b"Q\n")
        
        if stream_data.tell() > 0:
            return PDFStream(data=stream_data.getvalue())
        return None
    
    async def _create_physical_content_stream(self, page: Any, 
                                            layout: PageLayout,
                                            page_number: int) -> Optional[PDFStream]:
        """ایجاد استریم محتوای فیزیکی"""
        stream_data = io.BytesIO()
        
        if not hasattr(page, 'elements'):
            return None
        
        stream_data.write(b"q\n")
        
        for element in page.elements:
            element_type = type(element).__name__
            
            if element_type == 'TextRun':
                # TextRun از صفحه
                text_stream = self.content_writer.create_text_stream(
                    [element], None, layout.width, layout.height
                )
                if text_stream:
                    stream_data.write(text_stream.data)
            
            elif element_type == 'ImageObject':
                # ImageObject از صفحه
                image_stream = self.content_writer.create_image_stream(element)
                if image_stream:
                    stream_data.write(image_stream.data)
            
            elif element_type == 'VectorPath':
                # VectorPath از صفحه
                vector_stream = self.content_writer.create_vector_stream(element, layout.height)
                if vector_stream:
                    stream_data.write(vector_stream.data)
        
        stream_data.write(b"Q\n")
        
        if stream_data.tell() > 0:
            return PDFStream(data=stream_data.getvalue())
        return None
    
    def _combine_page_streams(self, streams: List[PDFStream]) -> PDFStream:
        """ترکیب چند استریم صفحه"""
        combined_data = io.BytesIO()
        
        for stream in streams:
            combined_data.write(stream.data)
        
        return PDFStream(data=combined_data.getvalue())
    
    def _add_to_outline(self, element: Any, page_number: int, y_position: float):
        """اضافه کردن عنصر به اوتلاین"""
        if hasattr(element, 'text_runs') and element.text_runs:
            text = ' '.join([tr.text for tr in element.text_runs if tr.text])
            if text:
                outline_item = {
                    'title': text[:100],  # محدود کردن طول عنوان
                    'page': page_number,
                    'y_position': y_position,
                    'level': getattr(element, 'level', 1),
                    'element': element
                }
                self.outline_items.append(outline_item)
    
    async def _create_outline(self, document: USDMDocument):
        """ایجاد اوتلاین"""
        if not self.outline_items:
            return
        
        # مرتب‌سازی اوتلاین آیتم‌ها
        self.outline_items.sort(key=lambda x: (x['page'], -x['y_position']))
        
        # ایجاد ساختار سلسله‌مراتبی اوتلاین
        outline_structure = self.outline_generator.generate_outline_structure(
            self.outline_items,
            max_depth=self.options.outline_depth
        )
        
        # ایجاد اشیاء اوتلاین
        outline_objects = self.outline_generator.create_outline_objects(
            outline_structure,
            self.page_refs
        )
        
        # ذخیره اشیاء اوتلاین
        for obj in outline_objects:
            obj.obj_id = self._get_next_object_num()
            self.objects.append(obj)
    
    async def _write_outline(self) -> AsyncIterator[bytes]:
        """نوشتن اوتلاین"""
        for obj in self.objects:
            if hasattr(obj, 'type') and getattr(obj, 'type', '') == 'outline':
                yield self._object_to_bytes(obj)
    
    async def _write_metadata(self, document: USDMDocument) -> AsyncIterator[bytes]:
        """نوشتن متادیتای PDF"""
        metadata = self.metadata_writer.create_pdf_metadata(document, self.options)
        metadata.obj_id = self._get_next_object_num()
        
        yield self._object_to_bytes(metadata)
        
        # ذخیره مرجع متادیتا
        self.trailer_dict['Info'] = f"{metadata.obj_id} 0 R"
    
    async def _write_annotations(self, document: USDMDocument) -> AsyncIterator[bytes]:
        """نوشتن حاشیه‌نویسی‌ها"""
        if not hasattr(document, 'annotations') or not document.annotations:
            return
        
        # پردازش حاشیه‌نویسی‌ها
        for page_num, page_annots in document.annotations.items():
            if page_num in self.page_refs:
                for annotation in page_annots:
                    # ایجاد شیء حاشیه‌نویسی
                    annot_obj = self.annotation_writer.create_annotation_object(
                        annotation,
                        self.page_refs[page_num]
                    )
                    if annot_obj:
                        annot_obj.obj_id = self._get_next_object_num()
                        yield self._object_to_bytes(annot_obj)
                        
                        # اضافه کردن به صفحه
                        page_obj = next((p for p in self.pages if p.obj_id == int(self.page_refs[page_num].split()[0])), None)
                        if page_obj:
                            if 'Annots' not in page_obj.entries:
                                page_obj.entries['Annots'] = []
                            page_obj.entries['Annots'].append(f"{annot_obj.obj_id} 0 R")
    
    async def _write_document_structure(self) -> AsyncIterator[bytes]:
        """نوشتن ساختار سند"""
        # ایجاد شیء Pages
        pages_obj = self.pdf_factory.create_dictionary({
            'Type': '/Pages',
            'Kids': [page_ref for page_ref in self.page_refs.values()],
            'Count': len(self.pages)
        })
        pages_obj.obj_id = self._get_next_object_num()
        yield self._object_to_bytes(pages_obj)
        
        # ایجاد کاتالوگ
        catalog_entries = {
            'Type': '/Catalog',
            'Pages': f"{pages_obj.obj_id} 0 R"
        }
        
        # اضافه کردن اوتلاین اگر وجود دارد
        outline_objs = [obj for obj in self.objects if hasattr(obj, 'type') and getattr(obj, 'type', '') == 'outline']
        if outline_objs:
            catalog_entries['Outlines'] = f"{outline_objs[0].obj_id} 0 R"
        
        catalog = self.pdf_factory.create_catalog(catalog_entries)
        catalog.obj_id = self._get_next_object_num()
        yield self._object_to_bytes(catalog)
        
        # ذخیره مرجع کاتالوگ
        self.trailer_dict['Root'] = f"{catalog.obj_id} 0 R"
        self.trailer_dict['Size'] = self.current_object_num
    
    async def _write_xref_table(self) -> AsyncIterator[bytes]:
        """نوشتن جدول کراس‌رفرنس"""
        # جمع‌آوری تمام اشیاء
        all_objects = []
        
        # اضافه کردن اشیاء از لیست‌های مختلف
        all_objects.extend(self.objects)
        all_objects.extend(self.pages)
        
        # مرتب‌سازی بر اساس object_id
        all_objects.sort(key=lambda x: x.obj_id)
        
        # ایجاد xref
        xref_data = io.BytesIO()
        xref_data.write(b"xref\n")
        xref_data.write(f"0 {len(all_objects) + 1}\n".encode())
        xref_data.write(b"0000000000 65535 f \n")
        
        # محاسبه آفست‌ها
        current_offset = 0
        offsets = [0]  # آفست برای object 0
        
        for obj in all_objects:
            obj_bytes = self._object_to_bytes(obj)
            offsets.append(current_offset)
            current_offset += len(obj_bytes)
        
        # نوشتن آفست‌ها
        for offset in offsets[1:]:  # از object 1 شروع می‌کنیم
            xref_data.write(f"{offset:010d} 00000 n \n".encode())
        
        yield xref_data.getvalue()
        
        # ذخیره آفست startxref
        self.trailer_dict['startxref'] = current_offset
    
    async def _write_trailer(self) -> AsyncIterator[bytes]:
        """نوشتن تریلر"""
        trailer_data = io.BytesIO()
        trailer_data.write(b"trailer\n")
        
        # اضافه کردن ID منحصر به فرد
        file_id = self._generate_file_id()
        self.trailer_dict['ID'] = [file_id, file_id]
        
        # ایجاد دیکشنری تریلر
        trailer_dict_obj = self.pdf_factory.create_dictionary(self.trailer_dict)
        trailer_data.write(trailer_dict_obj.to_bytes())
        
        # نوشتن startxref
        trailer_data.write(b"\nstartxref\n")
        trailer_data.write(f"{self.trailer_dict['startxref']}\n".encode())
        trailer_data.write(b"%%EOF")
        
        yield trailer_data.getvalue()
    
    async def _optimize_stream(self) -> AsyncIterator[bytes]:
        """بهینه‌سازی استریم خروجی"""
        if not self.options.optimize:
            return
        
        # جمع‌آوری تمام داده‌ها
        all_data = io.BytesIO()
        async for chunk in self.write_stream:
            all_data.write(chunk)
        
        # اعمال بهینه‌سازی
        optimized_data = self.optimizer.optimize_pdf(
            all_data.getvalue(),
            compress_streams=self.options.compress_streams,
            remove_unused=self.options.remove_unused_objects,
            merge_duplicates=self.options.merge_duplicate_streams
        )
        
        yield optimized_data
    
    def _get_next_object_num(self) -> int:
        """دریافت شماره شیء بعدی"""
        num = self.current_object_num
        self.current_object_num += 1
        return num
    
    def _object_to_bytes(self, obj: PDFObject) -> bytes:
        """تبدیل شیء PDF به بایت‌ها"""
        result = io.BytesIO()
        result.write(f"{obj.obj_id} {obj.generation} obj\n".encode())
        
        # اعمال انکریپشن اگر فعال باشد
        if self.options.encrypt and self.encryption_key and isinstance(obj, PDFStream):
            encrypted_data = self.encryptor.encrypt_stream(obj.data, self.encryption_key, obj.obj_id)
            obj.data = encrypted_data
        
        result.write(obj.to_bytes())
        result.write(b"\nendobj\n\n")
        return result.getvalue()
    
    def _generate_file_id(self) -> str:
        """تولید شناسه منحصر به فایل"""
        import uuid
        import time
        
        # ترکیب timestamp و UUID
        timestamp = int(time.time() * 1000)
        unique_id = uuid.uuid4().hex[:16]
        
        # ایجاد هش
        combined = f"{timestamp}{unique_id}".encode()
        file_id = hashlib.md5(combined).hexdigest().upper()
        
        # فرمت PDF ID
        return f"<{file_id}>"
    
    async def _validate_pdf(self, filepath: Path) -> bool:
        """اعتبارسنجی فایل PDF تولید شده"""
        try:
            # خواندن فایل و بررسی ساختار پایه
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # بررسی هدر PDF
            if not content.startswith(b'%PDF-'):
                if self.options.debug_mode:
                    print("هشدار: فایل PDF هدر معتبر ندارد")
                return False
            
            # بررسی EOF
            if b'%%EOF' not in content[-100:]:  # جستجو در 100 بایت آخر
                if self.options.debug_mode:
                    print("هشدار: فایل PDF پایان‌بندی معتبر ندارد")
                return False
            
            # بررسی ساختار xref
            if b'xref' not in content:
                if self.options.debug_mode:
                    print("هشدار: فایل PDF جدول xref ندارد")
                return False
            
            # بررسی startxref
            if b'startxref' not in content:
                if self.options.debug_mode:
                    print("هشدار: فایل PDF startxref ندارد")
                return False
            
            if self.options.debug_mode:
                print(f"فایل PDF با موفقیت اعتبارسنجی شد: {filepath}")
                print(f"حجم فایل: {len(content)} بایت")
            
            return True
            
        except Exception as e:
            if self.options.debug_mode:
                print(f"خطا در اعتبارسنجی PDF: {e}")
            return False
