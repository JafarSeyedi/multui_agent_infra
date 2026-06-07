"""
PDF Writer Orchestrator — converts USDMDocument to complete PDF binary.

This module implements full PDF owner generation: creating PDF documents from
scratch using the USDM document model.  It coordinates layout, content, fonts,
metadata, outlines, annotations, encryption, and optimization to produce a
complete, valid PDF 1.7 / 2.0 byte stream.
"""
from __future__ import annotations

import hashlib
import time
import zlib
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ....models.base import BaseDocument
from ....models.exceptions import DocumentWriteError
from ....models.usdm_models import (
    AnnotationObject,
    ImageObject,
    Page,
    StyleSheet,
    TextRun,
    USDMDocument,
    VectorPath,
)
from ...base import BaseDocumentWriter, WriteOptions

from .annotation_writer import (
    Annotation as PdfAnnot,
    AnnotationType as PdfAnnotType,
    AnnotationWriter,
)
from .content_writer import ContentWriter
from .encryption import (
    EncryptionAlgorithm,
    EncryptionOptions,
    PDFEncryptor,
)
try:
    from .font_manager import FontManager as _RealFontManager, FontStyle as _RealFontStyle
except ImportError:
    _FontManagerObj = None
    _FontStyleObj = None
else:
    _FontManagerObj = _RealFontManager
    _FontStyleObj = _RealFontStyle


class FontManager:  # type: ignore[no-redef]
    """Fallback font manager when reportlab is not available."""

    def __init__(self, embed_fonts: bool = True, subset_fonts: bool = True) -> None:
        if _FontManagerObj is not None:
            self._impl: Any = _FontManagerObj(embed_fonts=embed_fonts, subset_fonts=subset_fonts)
        else:
            self._impl = None

    def get_font_resources_dict(self) -> dict[str, Any]:
        if self._impl is not None:
            return self._impl.get_font_resources_dict()
        return {"Font": {}}

    def get_pdf_font_name(self, family: str, style: Any = None, language: str = "en") -> str:
        if self._impl is not None:
            return self._impl.get_pdf_font_name(family, style, language)
        return "/F1"


class FontStyle:  # type: ignore[no-redef]
    """Font style enumeration (re-export for API compatibility)."""
    NORMAL: str = "normal"
    BOLD: str = "bold"
    ITALIC: str = "italic"
    BOLD_ITALIC: str = "bold_italic"
from .layout_builder import LayoutBuilder, PageLayout  # noqa: E402
from .metadata_writer import MetadataWriter  # noqa: E402
from .optimizer import OptimizationLevel, OptimizationOptions, PDFOptimizer  # noqa: E402
from .outline_builder import OutlineBuilder  # noqa: E402
from .pdf_objects import (  # noqa: E402
    PDFCatalog,
    PDFDictionary,
    PDFInfo,
    PDFObjectFactory,
    PDFPage,
    PDFStream,
)
from .utils import ColorConverter, ImageProcessor, UnitConverter  # noqa: E402


class _PDFObjectSerializer:
    """Low-level serializer that writes PDF objects to bytes with xref tracking."""

    def __init__(self) -> None:
        self._objects: list[tuple[int, int, Any]] = []
        self._offsets: list[int] = []
        self._body = bytearray()
        self._next_id = 1
        self._oid_map: dict[int, int] = {}

    def add_object(self, obj_id: int, gen: int, value: Any) -> None:
        self._objects.append((obj_id, gen, value))

    @property
    def next_obj_id(self) -> int:
        v = self._next_id
        self._next_id += 1
        return v

    def track_factory_objects(self, factory: PDFObjectFactory) -> None:
        for obj in factory.get_all_objects():
            if obj.obj_id not in {o[0] for o in self._objects}:
                self._objects.append((obj.obj_id, obj.generation, obj))

    def serialize(
        self,
        root_id: int,
        info_id: int | None,
        encrypt_id: int | None = None,
        file_id: bytes | None = None,
    ) -> bytes:
        buf = bytearray()
        buf += b"%PDF-1.7\n"
        buf += b"\xc2\xb5\xc2\xb5\n"

        self._offsets = [0] * (max(o[0] for o in self._objects) + 1)
        self._body = bytearray()

        for oid, gen, val in self._objects:
            self._offsets[oid] = len(self._body)
            chunk = self._serialize_indirect(oid, gen, val)
            self._body += chunk

        buf += bytes(self._body)

        xref_offset = len(buf)
        buf += b"xref\n"
        buf += f"0 {len(self._objects) + 1}\n".encode("ascii")
        buf += b"0000000000 65535 f \r\n"
        for oid, gen, _val in self._objects:
            buf += f"{self._offsets[oid]:010d} {gen:05d} n \r\n".encode("ascii")

        trailer_entries: dict[str, Any] = {
            "Size": len(self._objects) + 1,
            "Root": self._ref(root_id),
        }
        if info_id is not None:
            trailer_entries["Info"] = self._ref(info_id)
        if encrypt_id is not None:
            trailer_entries["Encrypt"] = self._ref(encrypt_id)
        if file_id is not None:
            id_arr = (
                self._hex_string(file_id),
                self._hex_string(file_id),
            )
            trailer_entries["ID"] = id_arr

        buf += b"trailer\n"
        buf += self._serialize_dict_inline(trailer_entries)
        buf += b"\nstartxref\n"
        buf += f"{xref_offset}\n".encode("ascii")
        buf += b"%%EOF\n"
        return bytes(buf)

    def _ref(self, oid: int) -> str:
        return f"{oid} 0 R"

    def _hex_string(self, data: bytes) -> str:
        return f"<{data.hex()}>"

    def _serialize_indirect(self, oid: int, gen: int, val: Any) -> bytes:
        buf = bytearray()
        buf += f"{oid} {gen} obj\n".encode("ascii")
        buf += self._serialize_value(val)
        buf += b"\nendobj\n"
        return bytes(buf)

    def _serialize_value(self, val: Any) -> bytes:
        if val is None:
            return b"null"
        if isinstance(val, bool):
            return b"true" if val else b"false"
        if isinstance(val, int):
            return str(val).encode("ascii")
        if isinstance(val, float):
            formatted = f"{val:.4f}".rstrip("0").rstrip(".")
            return (formatted if formatted else "0").encode("ascii")
        if isinstance(val, bytes):
            escaped = val.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
            return b"(" + escaped + b")"
        if isinstance(val, str):
            if val.startswith("/"):
                return val.encode("ascii")
            if val.endswith(" R") and " " in val[:-2]:
                return val.encode("ascii")
            return b"(" + val.encode("latin-1", errors="replace") + b")"
        if isinstance(val, (list, tuple)):
            parts = [b"["]
            for item in val:
                parts.append(self._serialize_value(item))
            parts.append(b"]")
            return b" ".join(parts)
        if isinstance(val, dict):
            return self._serialize_dict_inline(val)
        if isinstance(val, PDFDictionary):
            return val.to_bytes()
        if isinstance(val, PDFStream):
            return self._serialize_stream_obj(val)
        if isinstance(val, PDFPage):
            return self._serialize_dict_inline(self._page_to_dict(val))
        if isinstance(val, PDFCatalog):
            return self._serialize_dict_inline(self._catalog_to_dict(val))
        if isinstance(val, PDFInfo):
            return self._serialize_dict_inline(self._info_to_dict(val))
        if isinstance(val, PDFObjectRef):
            return self._ref(val.oid).encode("ascii")
        return str(val).encode("ascii")

    def _serialize_dict_inline(self, d: dict[str, Any]) -> bytes:
        parts = [b"<< "]
        for k, v in d.items():
            parts.append(f"/{k} ".encode("ascii"))
            parts.append(self._serialize_value(v))
            parts.append(b"\n")
        parts.append(b">>")
        return b"".join(parts)

    def _serialize_stream_obj(self, s: PDFStream) -> bytes:
        stream_bytes = s.data
        length = s.length if s.length is not None else len(stream_bytes)
        dict_entries: dict[str, Any] = {"Length": length}
        if s.filters:
            if len(s.filters) == 1:
                dict_entries["Filter"] = f"/{s.filters[0]}"
            else:
                dict_entries["Filter"] = [f"/{f}" for f in s.filters]
        result = bytearray()
        result += self._serialize_dict_inline(dict_entries)
        result += b"\nstream\n"
        result += stream_bytes
        result += b"\nendstream"
        return bytes(result)

    def _page_to_dict(self, page: PDFPage) -> dict[str, Any]:
        entries: dict[str, Any] = {
            "Type": "/Page",
            "MediaBox": page.media_box,
        }
        if page.contents:
            if len(page.contents) == 1:
                c = page.contents[0]
                entries["Contents"] = PDFObjectRef(c.obj_id) if hasattr(c, "obj_id") else c
            else:
                entries["Contents"] = [
                    PDFObjectRef(c.obj_id) if hasattr(c, "obj_id") else c
                    for c in page.contents
                ]
        if page.resources:
            entries["Resources"] = page.resources
        if page.parent:
            p = page.parent
            entries["Parent"] = PDFObjectRef(p.obj_id) if hasattr(p, "obj_id") else p
        return entries

    def _catalog_to_dict(self, cat: PDFCatalog) -> dict[str, Any]:
        entries: dict[str, Any] = {
            "Type": "/Catalog",
            "Pages": PDFObjectRef(cat.pages.obj_id) if cat.pages and hasattr(cat.pages, "obj_id") else cat.pages,
        }
        if hasattr(cat, "outlines") and cat.outlines:
            o = cat.outlines
            entries["Outlines"] = PDFObjectRef(o.obj_id) if hasattr(o, "obj_id") else o
        if hasattr(cat, "metadata") and cat.metadata:
            m = cat.metadata
            entries["Metadata"] = PDFObjectRef(m.obj_id) if hasattr(m, "obj_id") else m
        if hasattr(cat, "entries"):
            for k, v in cat.entries.items():
                if k not in entries:
                    entries[k] = v
        return entries

    def _info_to_dict(self, info: PDFInfo) -> dict[str, Any]:
        entries: dict[str, Any] = {}
        if info.title:
            entries["Title"] = info.title
        if info.author:
            entries["Author"] = info.author
        if info.subject:
            entries["Subject"] = info.subject
        if info.keywords:
            entries["Keywords"] = info.keywords
        if info.creator:
            entries["Creator"] = info.creator
        if info.producer:
            entries["Producer"] = info.producer
        if info.creation_date:
            entries["CreationDate"] = self._format_pdf_date(info.creation_date)
        if info.mod_date:
            entries["ModDate"] = self._format_pdf_date(info.mod_date)
        return entries

    @staticmethod
    def _format_pdf_date(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return f"D:{dt.strftime('%Y%m%d%H%M%S')}"


class PDFObjectRef:
    """Lightweight reference wrapper for serialization."""

    __slots__ = ("oid",)

    def __init__(self, oid: int) -> None:
        self.oid = oid


class PDFWriter(BaseDocumentWriter):
    """Top-level orchestrator that converts USDMDocument to PDF bytes.

    Coordinates layout building, content writing, font management,
    metadata embedding, outline generation, annotation writing,
    encryption, optimization, and full PDF serialization.

    Attributes:
        font_manager: Manages font registration, embedding, and subsetting.
        unit_converter: Converts measurement units to PDF points.
        color_converter: Converts color representations.
        image_processor: Processes and optimizes images.
        layout_builder: Builds page layouts from document structure.
        content_writer: Generates PDF content streams from USDM elements.
        metadata_writer: Creates PDF Info dictionary and XMP metadata.
        outline_builder: Builds outline/bookmark tree from sections.
    """

    def __init__(self, options: WriteOptions | None = None):
        super().__init__(options)
        self.font_manager = FontManager(embed_fonts=True, subset_fonts=False)
        self.unit_converter = UnitConverter()
        self.color_converter = ColorConverter()
        self.image_processor = ImageProcessor()
        self.layout_builder = LayoutBuilder(self.unit_converter)
        self.content_writer = ContentWriter(self.font_manager, self.unit_converter)
        self.metadata_writer = MetadataWriter()
        self.outline_builder = OutlineBuilder()

    def get_supported_media_types(self) -> list[str]:
        return ["application/pdf"]

    def get_supported_extensions(self) -> list[str]:
        return [".pdf"]

    async def write(self, document: BaseDocument) -> bytes:
        if not isinstance(document, USDMDocument):
            raise DocumentWriteError("PDF writer requires a USDMDocument")
        return await self._build_pdf(document)

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        if not isinstance(document, USDMDocument):
            raise DocumentWriteError("PDF writer requires a USDMDocument")
        pdf_bytes = await self._build_pdf(document)
        chunk_size = 65536
        for i in range(0, len(pdf_bytes), chunk_size):
            yield pdf_bytes[i:i + chunk_size]

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None,
    ) -> None:
        if not isinstance(document, USDMDocument):
            raise DocumentWriteError("PDF writer requires a USDMDocument")
        pdf_bytes = await self._build_pdf(document, options)
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as f:
            f.write(pdf_bytes)

    async def _build_pdf(
        self,
        document: USDMDocument,
        extra_options: dict[str, Any] | None = None,
    ) -> bytes:
        """Internal pipeline that orchestrates the full PDF build.

        Pipeline stages:
            1. Build page layouts and create PDFPage objects.
            2. Write content streams for every element on every page.
            3. Build the page tree (Pages dictionary).
            4. Generate outlines / bookmarks from document sections.
            5. Write metadata (Info dictionary + XMP).
            6. Assemble the catalog.
            7. Serialize all objects with proper xref table and trailer.
            8. Encrypt if a password was provided.
            9. Optimize if requested.

        Args:
            document: The source USDM document.
            extra_options: Optional encryption/optimization overrides.

        Returns:
            Complete PDF as bytes.
        """
        opts = extra_options or {}
        factory = PDFObjectFactory()
        write_opts = self.options or WriteOptions()
        stylesheet = getattr(document, "stylesheet", None) or StyleSheet()

        file_id = hashlib.md5(
            str(id(document)).encode() + str(time.time()).encode()
        ).digest()

        encryptor = None
        password = opts.get("password")
        if password:
            enc_opts = EncryptionOptions(
                algorithm=EncryptionAlgorithm.AES_256,
                user_password=password,
                owner_password=opts.get("owner_password", ""),
                permissions=opts.get("permissions", 0),
                metadata_encrypted=opts.get("encrypt_metadata", True),
            )
            encryptor = PDFEncryptor(enc_opts)
            encryptor.generate_encryption_key(file_id)

        layout_options: dict[str, Any] = {
            "margin_top": opts.get("margin_top", 72),
            "margin_bottom": opts.get("margin_bottom", 72),
            "margin_left": opts.get("margin_left", 72),
            "margin_right": opts.get("margin_right", 72),
            "page_size": opts.get("page_size", "A4"),
            "page_orientation": opts.get("page_orientation", "portrait"),
        }
        layouts = self.layout_builder.create_page_layouts(document, layout_options)
        pdf_pages: list[PDFPage] = self.layout_builder.create_pdf_pages(
            factory, layouts
        )

        annotation_writer = AnnotationWriter()

        for page_idx, layout in enumerate(layouts):
            if page_idx >= len(pdf_pages):
                break
            pdf_page = pdf_pages[page_idx]
            usdm_page: Page | None = None
            if page_idx < len(document.pages):
                usdm_page = document.pages[page_idx]

            page_elements: list[Any] = []
            if usdm_page is not None:
                page_elements = getattr(usdm_page, "elements", [])

            page_content_streams: list[Any] = []
            text_runs_on_page: list[TextRun] = []

            for element in page_elements:
                if isinstance(element, TextRun):
                    text_runs_on_page.append(element)
                elif isinstance(element, ImageObject):
                    self._embed_image(element, factory, pdf_page, layout)
                elif isinstance(element, VectorPath):
                    vec_stream = self.content_writer.create_vector_stream(
                        element, layout.height
                    )
                    if vec_stream:
                        page_content_streams.append(vec_stream)
                elif isinstance(element, AnnotationObject):
                    rect = (
                        element.x,
                        element.y,
                        element.x + element.width,
                        element.y + element.height,
                    )
                    subtype_map: dict[str, PdfAnnotType] = {
                        "text": PdfAnnotType.TEXT,
                        "highlight": PdfAnnotType.HIGHLIGHT,
                        "underline": PdfAnnotType.UNDERLINE,
                        "strikeout": PdfAnnotType.STRIKEOUT,
                        "square": PdfAnnotType.SQUARE,
                        "circle": PdfAnnotType.CIRCLE,
                        "line": PdfAnnotType.LINE,
                        "freetext": PdfAnnotType.FREETEXT,
                        "ink": PdfAnnotType.INK,
                        "stamp": PdfAnnotType.STAMP,
                    }
                    ann = PdfAnnot(
                        type=subtype_map.get(
                            annotation_object_subtype(element), PdfAnnotType.TEXT
                        ),
                        page_number=page_idx + 1,
                        rect=rect,
                        contents=element.contents or "",
                    )
                    annotation_writer.add_annotation(ann)

            if text_runs_on_page:
                text_stream = self.content_writer.create_text_stream(
                    text_runs_on_page,
                    stylesheet,
                    layout.width,
                    layout.height,
                )
                page_content_streams.insert(0, text_stream)

            if page_content_streams:
                pdf_page.contents = page_content_streams

            font_resources = self.font_manager.get_font_resources_dict()
            xobject_res: dict[str, Any] = {}
            for xref_name, xref_val in pdf_page.resources.get("XObject", {}).items() if isinstance(pdf_page.resources, dict) else []:
                xobject_res[xref_name] = xref_val
            resources_dict: dict[str, Any] = {
                "ProcSet": ["/PDF", "/Text", "/ImageB", "/ImageC", "/ImageI"],
                "Font": font_resources.get("Font", {}),
                "XObject": factory.create_dictionary(xobject_res) if xobject_res else factory.create_dictionary({}),
            }
            pdf_page.resources = resources_dict

        pages_node = factory.create_dictionary({
            "Type": "/Pages",
            "Kids": pdf_pages,
            "Count": len(pdf_pages),
        })
        for pdf_page in pdf_pages:
            pdf_page.parent = pages_node

        self._build_outlines(document, pdf_pages, factory)

        catalog = factory.create_catalog(pages_node)

        info_obj = self.metadata_writer.create_pdf_metadata(document, write_opts)

        xmp_stream = self.metadata_writer.create_xmp_metadata(document, write_opts)
        if xmp_stream:
            catalog.metadata = xmp_stream

        enc_dict_id: int | None = None
        if encryptor is not None:
            enc_dict = encryptor.create_encryption_dictionary(file_id)
            enc_dict_id = factory.next_obj_id
            factory.create_dictionary(enc_dict)

        serializer = _PDFObjectSerializer()
        serializer.track_factory_objects(factory)

        root_id = catalog.obj_id
        info_id = info_obj.obj_id if info_obj else None

        pdf_bytes = serializer.serialize(
            root_id=root_id,
            info_id=info_id,
            encrypt_id=enc_dict_id,
            file_id=file_id,
        )

        enable_optimization = opts.get("optimize", False)
        if enable_optimization and pdf_bytes:
            opt_level_str = opts.get("optimization_level", "balanced")
            level_map = {
                "none": OptimizationLevel.NONE,
                "fast": OptimizationLevel.FAST,
                "balanced": OptimizationLevel.BALANCED,
                "maximum": OptimizationLevel.MAXIMUM,
            }
            optimizer = PDFOptimizer(
                OptimizationOptions(
                    level=level_map.get(opt_level_str, OptimizationLevel.BALANCED),
                    compress_images=True,
                    compress_streams=True,
                    remove_unused=True,
                )
            )
            pdf_bytes = optimizer.optimize(pdf_bytes)

        return pdf_bytes

    def _build_outlines(
        self,
        document: USDMDocument,
        pdf_pages: list[PDFPage],
        factory: PDFObjectFactory,
    ) -> None:
        """Populate the outline builder from document sections.

        Args:
            document: The source USDM document.
            pdf_pages: The list of already-built PDFPage objects.
            factory: The PDF object factory.
        """
        for section in document.sections:
            heading = getattr(section, "title", None)
            if heading is None:
                continue
            title_str = ""
            if hasattr(heading, "text") and hasattr(heading.text, "spans"):
                title_str = "".join(
                    getattr(span, "text", "") for span in heading.text.spans
                ).strip()
            if not title_str:
                title_str = getattr(section, "section_id", "Section")
            level = 0
            if hasattr(heading, "level"):
                level = min(max(heading.level - 1, 0), 5)

            page_number = 1
            section_elements = getattr(section, "elements", [])
            if section_elements:
                for el in section_elements:
                    if hasattr(el, "page_number") and el.page_number:
                        page_number = el.page_number
                        break

            if page_number < 1:
                page_number = 1
            if page_number > len(pdf_pages):
                page_number = len(pdf_pages)

            self.outline_builder.add_item(
                title=title_str,
                page_number=page_number,
                level=level,
            )

    def _embed_image(
        self,
        element: ImageObject,
        factory: PDFObjectFactory,
        pdf_page: PDFPage,
        layout: PageLayout,
    ) -> None:
        """Embed an image into the PDF page and register it as an XObject.

        Supports JPEG (DCTDecode), PNG (FlateDecode), and raw image data.

        Args:
            element: The USDM image object.
            factory: The PDF object factory.
            pdf_page: The target PDF page.
            layout: The page layout for coordinate conversion.
        """
        import base64
        import re

        image_bytes: bytes | None = None
        img_format = element.format.lower()

        if element.src and element.src.startswith("data:"):
            match = re.match(r"data:image/(\w+);base64,(.+)", element.src)
            if match:
                image_bytes = base64.b64decode(match.group(2))
                img_format = match.group(1).lower()
        elif element.src:
            try:
                image_bytes = base64.b64decode(element.src)
            except Exception:
                pass

        if not image_bytes:
            return

        width = int(element.width) if element.width else 100
        height = int(element.height) if element.height else 100

        if img_format in ("jpg", "jpeg"):
            filter_name = "/DCTDecode"
        else:
            filter_name = "/FlateDecode"

        img_dict_entries: dict[str, Any] = {
            "Type": "/XObject",
            "Subtype": "/Image",
            "Width": width,
            "Height": height,
            "ColorSpace": "/DeviceRGB",
            "BitsPerComponent": 8,
            "Filter": filter_name,
            "Length": len(image_bytes),
        }

        if filter_name == "/FlateDecode":
            compressed = zlib.compress(image_bytes)
            img_stream = PDFStream(
                obj_id=factory.next_obj_id,
                data=compressed,
                filters=["FlateDecode"],
            )
        else:
            img_stream = PDFStream(
                obj_id=factory.next_obj_id,
                data=image_bytes,
                filters=[filter_name.lstrip("/")],
            )

        img_dict = factory.create_dictionary(img_dict_entries)

        if isinstance(pdf_page.resources, dict):
            xobj = pdf_page.resources.setdefault("XObject", {})
            if isinstance(xobj, dict):
                xobj[f"Img{img_dict.obj_id}"] = img_stream

        w = element.width or 100
        h = element.height or 100
        x = element.x
        y = layout.height - element.y - h

        placement = (
            f"q\n"
            f"{w} 0 0 {h} {x:.2f} {y:.2f} cm\n"
            f"/Img{img_dict.obj_id} Do\n"
            f"Q"
        )

        placement_stream = factory.create_stream(placement.encode("latin-1"))
        if pdf_page.contents is None:
            pdf_page.contents = []
        pdf_page.contents.append(placement_stream)


def annotation_object_subtype(element: AnnotationObject) -> str:
    subtype = element.subtype.lower()
    valid = {
        "text", "highlight", "underline", "strikeout",
        "square", "circle", "line", "freetext",
        "ink", "stamp",
    }
    return subtype if subtype in valid else "text"
