"""
Low-level PDF object classes
"""
import hashlib
import zlib
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any
from typing import Optional


@dataclass
class PDFObject:
    """Base class for PDF objects"""
    obj_id: int
    generation: int = 0
    data: Any = None

    def to_bytes(self) -> bytes:
        """Convert object to PDF bytes"""
        raise NotImplementedError

    def get_reference(self) -> str:
        """Get object reference string"""
        return f"{self.obj_id} {self.generation} R"


@dataclass
class PDFDictionary(PDFObject):
    """PDF dictionary object"""
    entries: dict[str, Any] = field(default_factory=dict)

    def to_bytes(self) -> bytes:
        result = []
        result.append(b"<<\n")

        for key, value in self.entries.items():
            if isinstance(value, str):
                # UTF-16 strings for Persian support
                if any(ord(c) > 127 for c in value):
                    encoded = value.encode('utf-16-be')
                    result.append(f"/{key} ".encode())
                    result.append(b"<FEFF")
                    result.append(encoded)
                    result.append(b">\n")
                else:
                    result.append(f"/{key} ({value})\n".encode())
            elif isinstance(value, bool):
                result.append(f"/{key} {'true' if value else 'false'}\n".encode())
            elif isinstance(value, int):
                result.append(f"/{key} {value}\n".encode())
            elif isinstance(value, float):
                result.append(f"/{key} {value:.2f}\n".encode())
            elif isinstance(value, PDFObject):
                result.append(f"/{key} {value.obj_id} {value.generation} R\n".encode())
            elif isinstance(value, list):
                result.append(f"/{key} [".encode())
                for item in value:
                    # Cast to Any to avoid false mypy error (items are int, float, or PDFObject)
                    item_typed: Any = item
                    if isinstance(item_typed, PDFObject):
                        result.append(f" {item_typed.obj_id} {item_typed.generation} R".encode())
                    elif isinstance(item_typed, int):
                        result.append(f" {item_typed}".encode())
                    elif isinstance(item_typed, float):
                        result.append(f" {item_typed:.2f}".encode())
                result.append(b" ]\n")
            elif value is None:
                result.append(f"/{key} null\n".encode())
            elif isinstance(value, dict):
                # Nested dictionary
                nested_dict = PDFDictionary(obj_id=0, entries=value)
                result.append(f"/{key} ".encode())
                result.append(nested_dict.to_bytes())
                result.append(b"\n")

        result.append(b">>")
        return b''.join(result)


@dataclass
class PDFStream(PDFObject):
    """PDF stream object"""
    data: bytes = b''
    filters: list[str] = field(default_factory=list)
    length: int | None = None

    def to_bytes(self) -> bytes:
        # Create stream dictionary
        dict_entries: dict[str, Any] = {                     # <-- add type annotation
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

        # Compress if needed
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
    """PDF page object"""
    media_box: list[float] = field(default_factory=lambda: [0, 0, 595, 842])  # A4
    resources: dict[str, Any] = field(default_factory=dict)
    contents: list[PDFObject] = field(default_factory=list)
    parent: Optional['PDFObject'] = None
    kids: list['PDFObject'] = field(default_factory=list)

    def to_bytes(self) -> bytes:
        entries = {
            'Type': '/Page',
            'MediaBox': self.media_box,
            'Resources': PDFDictionary(
                obj_id=0,  # Temporary ID
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
    """PDF catalog (document root)"""
    pages: PDFObject | None = None
    outlines: PDFObject | None = None
    metadata: PDFObject | None = None

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
    """PDF metadata information"""
    title: str | None = None
    author: str | None = None
    subject: str | None = None
    keywords: str | None = None
    creator: str | None = None
    producer: str | None = None
    creation_date: datetime | None = None
    mod_date: datetime | None = None

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

        # PDF date format
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
        """Format date for PDF"""
        return f"D:{dt.strftime('%Y%m%d%H%M%S')}Z"


@dataclass
class PDFXRefEntry:
    """XRef table entry"""
    offset: int
    generation: int
    in_use: bool = True

    def to_bytes(self) -> bytes:
        """Convert to XRef format"""
        offset_str = f"{self.offset:010d}"
        generation_str = f"{self.generation:05d}"
        status = "n" if self.in_use else "f"
        return f"{offset_str} {generation_str} {status}\n".encode()


@dataclass
class PDFTrailer:
    """PDF trailer"""
    size: int
    root: PDFObject
    info: PDFObject | None = None
    id: tuple[bytes, bytes] | None = None

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
        result.append(b"0\n")  # offset to XRef
        result.append(b"%%EOF")

        return b''.join(result)


class PDFObjectFactory:
    """PDF object factory"""

    def __init__(self) -> None:
        self.next_obj_id = 1
        self.objects: list[PDFObject] = []

    def create_dictionary(self, entries: dict[str, Any]) -> PDFDictionary:
        """Create new dictionary"""
        obj = PDFDictionary(obj_id=self.next_obj_id, entries=entries)
        self.next_obj_id += 1
        self.objects.append(obj)
        return obj

    def create_stream(self, data: bytes, filters: list[str] | None = None) -> PDFStream:
        """Create new stream"""
        obj = PDFStream(
            obj_id=self.next_obj_id,
            data=data,
            filters=filters or []
        )
        self.next_obj_id += 1
        self.objects.append(obj)
        return obj

    def create_page(self, media_box: list[float] | None = None) -> PDFPage:
        """Create new page"""
        obj = PDFPage(
            obj_id=self.next_obj_id,
            media_box=media_box or [0, 0, 595, 842]
        )
        self.next_obj_id += 1
        self.objects.append(obj)
        return obj

    def create_catalog(self, pages: PDFObject) -> PDFCatalog:
        """Create catalog"""
        obj = PDFCatalog(obj_id=self.next_obj_id, pages=pages)
        self.next_obj_id += 1
        self.objects.append(obj)
        return obj

    def create_info(self, **kwargs) -> PDFInfo:
        """Create metadata information"""
        obj = PDFInfo(obj_id=self.next_obj_id, **kwargs)
        self.next_obj_id += 1  # Fix: added +=
        self.objects.append(obj)
        return obj

    def create_xref_table(self) -> list[PDFXRefEntry]:
        """Create XRef table"""
        xref_entries = []

        # First entry (free list head)
        xref_entries.append(PDFXRefEntry(offset=0, generation=65535, in_use=False))

        # Object entries
        for obj in self.objects:
            # Offset should be calculated here
            xref_entries.append(PDFXRefEntry(offset=0, generation=obj.generation, in_use=True))

        return xref_entries

    def create_trailer(self, root: PDFObject, info: PDFObject | None = None) -> PDFTrailer:
        """Create trailer"""
        # Generate unique document ID
        import time
        import random

        timestamp = str(time.time()).encode('utf-8')
        random_bytes = str(random.random()).encode('utf-8')

        id1 = hashlib.md5(timestamp).digest()
        id2 = hashlib.md5(random_bytes).digest()

        return PDFTrailer(
            size=len(self.objects) + 1,  # +1 for free list head
            root=root,
            info=info,
            id=(id1, id2)
        )

    def get_all_objects(self) -> list[PDFObject]:
        """Get all objects"""
        return self.objects

    def get_object_by_id(self, obj_id: int) -> PDFObject | None:
        """Find object by ID"""
        for obj in self.objects:
            if obj.obj_id == obj_id:
                return obj
        return None


class PDFWriter:
    """Main class for writing PDF"""

    def __init__(self) -> None:
        self.factory = PDFObjectFactory()
        self.pages: list[PDFPage] = []
        self.current_offset = 0
        self.object_offsets: dict[int, int] = {}

    def add_page(self, media_box: list[float] | None = None) -> PDFPage:
        """Add new page"""
        page = self.factory.create_page(media_box)
        self.pages.append(page)
        return page

    def add_text(self, page: PDFPage, text: str, x: float, y: float,
                 font_name: str = "F1", font_size: float = 12) -> None:
        """Add text to page"""
        # Create text content
        content = f"BT\n/F{font_name} {font_size} Tf\n{x} {y} Td\n({text}) Tj\nET"

        # Create content stream
        stream = self.factory.create_stream(content.encode('utf-8'))

        # Add to page content
        if not page.contents:
            page.contents = []
        page.contents.append(stream)

        # Add font to page resources
        if 'Font' not in page.resources:
            page.resources['Font'] = {}

        # Actual font should be added here
        page.resources['Font'][font_name] = {
            'Type': '/Font',
            'Subtype': '/Type1',
            'BaseFont': '/Helvetica',
            'Encoding': '/WinAnsiEncoding'
        }

    def build_pdf(self) -> bytes:
        """Build complete PDF file"""
        result = []

        # PDF header
        result.append(b"%PDF-1.7\n")
        result.append(b"%\xc2\xb5\xc2\xb5\n")  # Binary marker

        # Create pages object
        pages_obj = self.factory.create_dictionary({
            'Type': '/Pages',
            'Kids': self.pages,
            'Count': len(self.pages)
        })

        # Create catalog
        catalog = self.factory.create_catalog(pages_obj)

        # Create info
        info = self.factory.create_info(
            title="PDF Document",
            author="USDM PDF Writer",
            creator="USDM PDF Writer",
            producer="USDM PDF Writer",
            creation_date=datetime.now()
        )

        # Write objects
        all_objects = self.factory.get_all_objects()

        # Save offsets
        for obj in all_objects:
            self.object_offsets[obj.obj_id] = len(b''.join(result))
            result.append(f"{obj.obj_id} {obj.generation} obj\n".encode())
            result.append(obj.to_bytes())
            result.append(b"\nendobj\n")

        # Create XRef table
        len(b''.join(result))
        result.append(b"xref\n")
        result.append(f"0 {len(all_objects) + 1}\n".encode())

        # Free list head
        result.append(b"0000000000 65535 f \n")

        # Objects
        for obj in all_objects:
            offset = self.object_offsets.get(obj.obj_id, 0)
            result.append(f"{offset:010d} {obj.generation:05d} n \n".encode())

        # Create trailer
        trailer = self.factory.create_trailer(catalog, info)
        result.append(trailer.to_bytes())

        return b''.join(result)

    def save(self, filepath: str) -> None:
        """Save PDF to file"""
        pdf_data = self.build_pdf()
        with open(filepath, 'wb') as f:
            f.write(pdf_data)


# # Example usage
# if __name__ == "__main__":
#     # Create a simple PDF document
#     writer = PDFWriter()
#
#     # Add page
#     page1 = writer.add_page()
#
#     # Add text
#     writer.add_text(page1, "Hello دنیا!", 100, 700, font_size=20)
#     writer.add_text(page1, "این یک سند PDF تست است.", 100, 650, font_size=14)
#     writer.add_text(page1, "This is English text.", 100, 600, font_size=14)
#
#     # Save file
#     writer.save("test_output.pdf")
#     print("فایل PDF با موفقیت ایجاد شد: test_output.pdf")
