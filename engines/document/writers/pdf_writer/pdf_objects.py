"""
کلاس‌های اشیاء PDF سطح پایین
"""

import io
import zlib
import hashlib
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import struct


@dataclass
class PDFObject:
    """کلاس پایه برای اشیاء PDF"""
    obj_id: int
    generation: int = 0
    data: Any = None
    
    def to_bytes(self) -> bytes:
        """تبدیل شیء به بایت‌های PDF"""
        raise NotImplementedError
    
    def get_reference(self) -> str:
        """دریافت رشته مرجع شیء"""
        return f"{self.obj_id} {self.generation} R"


@dataclass
class PDFDictionary(PDFObject):
    """شیء دیکشنری PDF"""
    entries: Dict[str, Any] = field(default_factory=dict)
    
    def to_bytes(self) -> bytes:
        result = []
        result.append(b"<<\n")
        
        for key, value in self.entries.items():
            if isinstance(value, str):
                # رشته‌های UTF-16 برای پشتیبانی از فارسی
                if any(ord(c) > 127 for c in value):
                    encoded = value.encode('utf-16-be')
                    result.append(f"/{key} ".encode('utf-8'))
                    result.append(b"<FEFF")
                    result.append(encoded)
                    result.append(b">\n")
                else:
                    result.append(f"/{key} ({value})\n".encode('utf-8'))
            elif isinstance(value, bool):
                result.append(f"/{key} {'true' if value else 'false'}\n".encode('utf-8'))
            elif isinstance(value, int):
                result.append(f"/{key} {value}\n".encode('utf-8'))
            elif isinstance(value, float):
                result.append(f"/{key} {value:.2f}\n".encode('utf-8'))
            elif isinstance(value, PDFObject):
                result.append(f"/{key} {value.obj_id} {value.generation} R\n".encode('utf-8'))
            elif isinstance(value, list):
                result.append(f"/{key} [".encode('utf-8'))
                for item in value:
                    if isinstance(item, PDFObject):
                        result.append(f" {item.obj_id} {item.generation} R".encode('utf-8'))
                    elif isinstance(item, int):
                        result.append(f" {item}".encode('utf-8'))
                    elif isinstance(item, float):
                        result.append(f" {item:.2f}".encode('utf-8'))
                result.append(b" ]\n")
            elif value is None:
                result.append(f"/{key} null\n".encode('utf-8'))
            elif isinstance(value, dict):
                # دیکشنری تو در تو
                nested_dict = PDFDictionary(obj_id=0, entries=value)
                result.append(f"/{key} ".encode('utf-8'))
                result.append(nested_dict.to_bytes())
                result.append(b"\n")
        
        result.append(b">>")
        return b''.join(result)


@dataclass
class PDFStream(PDFObject):
    """شیء استریم PDF"""
    data: bytes = b''
    filters: List[str] = field(default_factory=list)
    length: Optional[int] = None
    
    def to_bytes(self) -> bytes:
        # ایجاد دیکشنری استریم
        dict_entries = {
            'Length': len(self.data) if self.length is None else self.length
        }
        
        if self.filters:
            if len(self.filters) == 1:
                dict_entries['Filter'] = f"/{self.filters[0]}"
            else:
                dict_entries['Filter'] = [f"/{f}" for f in self.filters]
        
        dict_obj = PDFDictionary(
            obj_id=self.obj_id,
            generation=self.generation,
            entries=dict_entries
        )
        
        # فشرده‌سازی اگر نیاز باشد
        stream_data = self.data
        if 'FlateDecode' in self.filters:
            stream_data = zlib.compress(stream_data)
        
        result = []
        result.append(dict_obj.to_bytes())
        result.append(b"\nstream\n")
        result.append(stream_data)
        result.append(b"\nendstream")
        
        return b''.join(result)


@dataclass
class PDFPage(PDFObject):
    """شیء صفحه PDF"""
    media_box: List[float] = field(default_factory=lambda: [0, 0, 595, 842])  # A4
    resources: Dict[str, Any] = field(default_factory=dict)
    contents: List[PDFObject] = field(default_factory=list)
    parent: Optional['PDFObject'] = None
    kids: List['PDFObject'] = field(default_factory=list)
    
    def to_bytes(self) -> bytes:
        entries = {
            'Type': '/Page',
            'MediaBox': self.media_box,
            'Resources': PDFDictionary(
                obj_id=0,  # ID موقت
                generation=0,
                entries=self.resources
            )
        }
        
        if self.contents:
            if len(self.contents) == 1:
                entries['Contents'] = self.contents[0]
            else:
                entries['Contents'] = self.contents
        
        if self.parent:
            entries['Parent'] = self.parent
        
        if self.kids:
            entries['Kids'] = self.kids
        
        dict_obj = PDFDictionary(
            obj_id=self.obj_id,
            generation=self.generation,
            entries=entries
        )
        
        return dict_obj.to_bytes()


@dataclass
class PDFCatalog(PDFObject):
    """کاتالوگ PDF (ریشه سند)"""
    pages: PDFObject = None
    outlines: Optional[PDFObject] = None
    metadata: Optional[PDFObject] = None
    
    def to_bytes(self) -> bytes:
        entries = {
            'Type': '/Catalog',
            'Pages': self.pages
        }
        
        if self.outlines:
            entries['Outlines'] = self.outlines
        if self.metadata:
            entries['Metadata'] = self.metadata
        
        dict_obj = PDFDictionary(
            obj_id=self.obj_id,
            generation=self.generation,
            entries=entries
        )
        
        return dict_obj.to_bytes()


@dataclass
class PDFInfo(PDFObject):
    """اطلاعات متادیتای PDF"""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[datetime] = None
    mod_date: Optional[datetime] = None
    
    def to_bytes(self) -> bytes:
        entries = {}
        
        if self.title:
            entries['Title'] = self.title
        if self.author:
            entries['Author'] = self.author
        if self.subject:
            entries['Subject'] = self.subject
        if self.keywords:
            entries['Keywords'] = self.keywords
        if self.creator:
            entries['Creator'] = self.creator
        if self.producer:
            entries['Producer'] = self.producer or 'USDM PDF Writer'
        
        # فرمت تاریخ PDF
        if self.creation_date:
            entries['CreationDate'] = self._format_pdf_date(self.creation_date)
        if self.mod_date:
            entries['ModDate'] = self._format_pdf_date(self.mod_date)
        
        dict_obj = PDFDictionary(
            obj_id=self.obj_id,
            generation=self.generation,
            entries=entries
        )
        
        return dict_obj.to_bytes()
    
    def _format_pdf_date(self, dt: datetime) -> str:
        """فرمت‌بندی تاریخ برای PDF"""
        return f"D:{dt.strftime('%Y%m%d%H%M%S')}Z"


@dataclass
class PDFXRefEntry:
    """ورودی جدول XRef"""
    offset: int
    generation: int
    in_use: bool = True
    
    def to_bytes(self) -> bytes:
        """تبدیل به فرمت XRef"""
        offset_str = f"{self.offset:010d}"
        generation_str = f"{self.generation:05d}"
        status = "n" if self.in_use else "f"
        return f"{offset_str} {generation_str} {status}\n".encode('utf-8')


@dataclass
class PDFTrailer:
    """تریلر PDF"""
    size: int
    root: PDFObject
    info: Optional[PDFObject] = None
    id: Optional[Tuple[bytes, bytes]] = None
    
    def to_bytes(self) -> bytes:
        entries = {
            'Size': self.size,
            'Root': self.root
        }
        
        if self.info:
            entries['Info'] = self.info
        
        if self.id:
            entries['ID'] = [f"<{self.id[0].hex()}>", f"<{self.id[1].hex()}>"]
        
        dict_obj = PDFDictionary(
            obj_id=0,
            generation=0,
            entries=entries
        )
        
        result = []
        result.append(b"trailer\n")
        result.append(dict_obj.to_bytes())
        result.append(b"\nstartxref\n")
        result.append(b"0\n")  # offset به XRef
        result.append(b"%%EOF")
        
        return b''.join(result)


class PDFObjectFactory:
    """کارخانه تولید اشیاء PDF"""
    
    def __init__(self):
        self.next_obj_id = 1
        self.objects: List[PDFObject] = []
    
    def create_dictionary(self, entries: Dict[str, Any]) -> PDFDictionary:
        """ایجاد دیکشنری جدید"""
        obj = PDFDictionary(obj_id=self.next_obj_id, entries=entries)
        self.next_obj_id += 1
        self.objects.append(obj)
        return obj
    
    def create_stream(self, data: bytes, filters: List[str] = None) -> PDFStream:
        """ایجاد استریم جدید"""
        obj = PDFStream(
            obj_id=self.next_obj_id,
            data=data,
            filters=filters or []
        )
        self.next_obj_id += 1
        self.objects.append(obj)
        return obj
    
    def create_page(self, media_box: List[float] = None) -> PDFPage:
        """ایجاد صفحه جدید"""
        obj = PDFPage(
            obj_id=self.next_obj_id,
            media_box=media_box or [0, 0, 595, 842]
        )
        self.next_obj_id += 1
        self.objects.append(obj)
        return obj
    
    def create_catalog(self, pages: PDFObject) -> PDFCatalog:
        """ایجاد کاتالوگ"""
        obj = PDFCatalog(obj_id=self.next_obj_id, pages=pages)
        self.next_obj_id += 1
        self.objects.append(obj)
        return obj
    
    def create_info(self, **kwargs) -> PDFInfo:
        """ایجاد اطلاعات متادیتا"""
        obj = PDFInfo(obj_id=self.next_obj_id, **kwargs)
        self.next_obj_id += 1  # اصلاح: اضافه کردن +=
        self.objects.append(obj)
        return obj
    
    def create_xref_table(self) -> List[PDFXRefEntry]:
        """ایجاد جدول XRef"""
        xref_entries = []
        
        # ورودی اول (free list head)
        xref_entries.append(PDFXRefEntry(offset=0, generation=65535, in_use=False))
        
        # ورودی‌های اشیاء
        for obj in self.objects:
            # در اینجا offset باید محاسبه شود
            xref_entries.append(PDFXRefEntry(offset=0, generation=obj.generation, in_use=True))
        
        return xref_entries
    
    def create_trailer(self, root: PDFObject, info: Optional[PDFObject] = None) -> PDFTrailer:
        """ایجاد تریلر"""
        # تولید ID منحصر به فرد برای سند
        import time
        import random
        import hashlib
        
        timestamp = str(time.time()).encode('utf-8')
        random_bytes = str(random.random()).encode('utf-8')
        
        id1 = hashlib.md5(timestamp).digest()
        id2 = hashlib.md5(random_bytes).digest()
        
        return PDFTrailer(
            size=len(self.objects) + 1,  # +1 برای free list head
            root=root,
            info=info,
            id=(id1, id2)
        )
    
    def get_all_objects(self) -> List[PDFObject]:
        """دریافت تمام اشیاء"""
        return self.objects
    
    def get_object_by_id(self, obj_id: int) -> Optional[PDFObject]:
        """یافتن شیء بر اساس ID"""
        for obj in self.objects:
            if obj.obj_id == obj_id:
                return obj
        return None


class PDFWriter:
    """کلاس اصلی برای نوشتن PDF"""
    
    def __init__(self):
        self.factory = PDFObjectFactory()
        self.pages: List[PDFPage] = []
        self.current_offset = 0
        self.object_offsets: Dict[int, int] = {}
    
    def add_page(self, media_box: List[float] = None) -> PDFPage:
        """افزودن صفحه جدید"""
        page = self.factory.create_page(media_box)
        self.pages.append(page)
        return page
    
    def add_text(self, page: PDFPage, text: str, x: float, y: float, 
                 font_name: str = "F1", font_size: float = 12) -> None:
        """افزودن متن به صفحه"""
        # ایجاد محتوای متن
        content = f"BT\n/F{font_name} {font_size} Tf\n{x} {y} Td\n({text}) Tj\nET"
        
        # ایجاد استریم محتوا
        stream = self.factory.create_stream(content.encode('utf-8'))
        
        # افزودن به محتوای صفحه
        if not page.contents:
            page.contents = []
        page.contents.append(stream)
        
        # افزودن فونت به منابع صفحه
        if 'Font' not in page.resources:
            page.resources['Font'] = {}
        
        # در اینجا باید فونت واقعی اضافه شود
        page.resources['Font'][font_name] = {
            'Type': '/Font',
            'Subtype': '/Type1',
            'BaseFont': '/Helvetica',
            'Encoding': '/WinAnsiEncoding'
        }
    
    def build_pdf(self) -> bytes:
        """ساخت فایل PDF کامل"""
        result = []
        
        # هدر PDF
        result.append(b"%PDF-1.7\n")
        result.append(b"%\xc2\xb5\xc2\xb5\n")  # Binary marker
        
        # ایجاد اشیاء صفحات
        pages_obj = self.factory.create_dictionary({
            'Type': '/Pages',
            'Kids': self.pages,
            'Count': len(self.pages)
        })
        
        # ایجاد کاتالوگ
        catalog = self.factory.create_catalog(pages_obj)
        
        # ایجاد اطلاعات
        info = self.factory.create_info(
            title="سند PDF",
            author="USDM PDF Writer",
            creator="USDM PDF Writer",
            producer="USDM PDF Writer",
            creation_date=datetime.now()
        )
        
        # نوشتن اشیاء
        all_objects = self.factory.get_all_objects()
        
        # ذخیره آفست‌ها
        for obj in all_objects:
            self.object_offsets[obj.obj_id] = len(b''.join(result))
            result.append(f"{obj.obj_id} {obj.generation} obj\n".encode('utf-8'))
            result.append(obj.to_bytes())
            result.append(b"\nendobj\n")
        
        # ایجاد جدول XRef
        xref_start = len(b''.join(result))
        result.append(b"xref\n")
        result.append(f"0 {len(all_objects) + 1}\n".encode('utf-8'))
        
        # free list head
        result.append(b"0000000000 65535 f \n")
        
        # اشیاء
        for obj in all_objects:
            offset = self.object_offsets.get(obj.obj_id, 0)
            result.append(f"{offset:010d} {obj.generation:05d} n \n".encode('utf-8'))
        
        # ایجاد تریلر
        trailer = self.factory.create_trailer(catalog, info)
        result.append(trailer.to_bytes())
        
        return b''.join(result)
    
    def save(self, filepath: str) -> None:
        """ذخیره PDF در فایل"""
        pdf_data = self.build_pdf()
        with open(filepath, 'wb') as f:
            f.write(pdf_data)


# # مثال استفاده
# if __name__ == "__main__":
#     # ایجاد یک سند PDF ساده
#     writer = PDFWriter()
    
#     # افزودن صفحه
#     page1 = writer.add_page()
    
#     # افزودن متن فارسی
#     writer.add_text(page1, "سلام دنیا!", 100, 700, font_size=20)
#     writer.add_text(page1, "این یک سند PDF تست است.", 100, 650, font_size=14)
#     writer.add_text(page1, "This is English text.", 100, 600, font_size=14)
    
#     # ذخیره فایل
#     writer.save("test_output.pdf")
#     print("فایل PDF با موفقیت ایجاد شد: test_output.pdf")
