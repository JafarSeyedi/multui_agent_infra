# engines/document/models/document_registry.py
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .media_detection import detect_media_type
from .media_types import DocumentFormat
from .media_types import MEDIA_TYPES
from .media_types import MediaContentKind
from .media_types import MediaRawType
from .media_types import MediaType
from .media_types import MediaTypeRegistry
from ..parsers.base import BaseDocumentParser
from ..writers.base import BaseDocumentWriter


# ==========================================================
# CORE REGISTRY
# ==========================================================
class DocumentRegistry:
    """
    - Resolution 3-layered (Magic Bytes → MIME → Extension)
    - Registry override system (اصلی نسخه قبلی)
    - Plugin-based Parser/Writer mapping (نسخه جدید)
    - Ingestion Pipeline Integration
    - Smart Workflow Recommendation
    - Format fallbacks
    - MediaTypeRegistry-driven
    """

    # ------------------------------------------------------
    # INIT
    # ------------------------------------------------------
    def __init__(self) -> None:

        self.media_registry = MediaTypeRegistry

        # plugin-based mapping (نسخه جدید)
        self._parser_plugins: dict[DocumentFormat, type[BaseDocumentParser]] = {}
        self._writer_plugins: dict[DocumentFormat, type[BaseDocumentWriter]] = {}

    # ==========================================================
    # PLUGIN-BASED REGISTRATION (نسخه جدید)
    # ==========================================================
    def register_parser_plugin(
        self,
        fmt: DocumentFormat,
        parser_cls: type[BaseDocumentParser],
    ) -> None:
        self._parser_plugins[fmt] = parser_cls

    def register_writer_plugin(
        self,
        fmt: DocumentFormat,
        writer_cls: type[BaseDocumentWriter],
    ) -> None:
        self._writer_plugins[fmt] = writer_cls

    # ==========================================================
    # ADVANCED MEDIA DETECTION
    # در DocumentRegistry._detect_magic_mime
    def _detect_magic_mime(self, src: str | Path | bytes) -> str | None:
        try:
            # سعی در import magic
            import magic
            if isinstance(src, bytes):
                return magic.from_buffer(src[:4096], mime=True)
            path = Path(src)
            if path.exists() and path.is_file():
                return magic.from_file(str(path), mime=True)
        except ImportError:
            # اگر magic نصب نیست، از fallback استفاده کن
            return self._fallback_mime_detection(src)
        except Exception:
            pass
        return None

    def _fallback_mime_detection(self, src: str | Path | bytes) -> str | None:
        """Fallback MIME detection بدون magic"""
        if isinstance(src, bytes):
            data = src[:1024]  # فقط ابتدای فایل را بررسی کن
        else:
            try:
                path = Path(src)
                if path.exists() and path.is_file():
                    with open(path, 'rb') as f:
                        data = f.read(1024)
                else:
                    return None
            except Exception:
                return None

        # بررسی magic bytes ساده
        if data.startswith(b"%PDF"):
            return "application/pdf"
        elif data.startswith(b"PK\x03\x04"):
            return "application/zip"  # برای docx, xlsx, etc.
        elif data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        elif data.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        elif data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
            return "image/gif"
        elif data.startswith(b"<?xml"):
            return "application/xml"
        elif data.startswith(b"{"):
            return "application/json"
        # ... سایر فرمت‌ها

        return None


    def resolve_media_type(
        self, src: str | Path | bytes
    ) -> MediaType:
        """
        لایه تشخیص ۳-مرحله‌ای:

        1. Magic Bytes → MIME
        2. MIME → MediaTypeRegistry
        3. Extension → MediaTypeRegistry
        4. Fallback → Unknown Text/Binary
        """

        # 1) Magic bytes
        mime = self._detect_magic_mime(src)
        if mime:
            mt = self.media_registry.get_by_mime(mime)
            if mt:
                return mt

        # 2) fallback به detect_media_type (نسخه قبلی)
        if isinstance(src, (str, Path)):
            try:
                mt = detect_media_type(str(src))
                if mt:
                    return mt
            except Exception:
                pass

        # 3) extension detection
        if isinstance(src, (str, Path)):
            ext = Path(src).suffix
            mt = self.media_registry.get_by_extension(ext)
            if mt:
                return mt

        # 4) fallback to binary/text guess
        if isinstance(src, bytes):
            # heuristic text check
            try:
                src.decode("utf-8")
                mt = self.media_registry.get_by_extension(".txt")
                if mt:
                    return mt
            except Exception:
                pass

        mt = self.media_registry.get_by_extension(".bin")
        if mt:
            return mt
        return MEDIA_TYPES["binary"]

    # ==========================================================
    # FORMAT RESOLUTION
    # ==========================================================
    def resolve_format(self, src: str | Path | bytes) -> DocumentFormat:
        mt = self.resolve_media_type(src)
        return mt.format

    # ==========================================================
    # PARSER RESOLUTION (ترکیبی + Override)
    # ==========================================================
    def get_parser(
        self,
        src: str | Path | bytes,
    ) -> BaseDocumentParser | None:

        mt = self.resolve_media_type(src)
        fmt = mt.format

        # 1) plugin
        if fmt in self._parser_plugins:
            return self._parser_plugins[fmt]()

        return None

    # ==========================================================
    # WRITER RESOLUTION (ترکیبی + Override)
    # ==========================================================
    def get_writer(
        self,
        src_or_format: str | Path | bytes | DocumentFormat,
    ) -> BaseDocumentWriter | None:

        if isinstance(src_or_format, DocumentFormat):
            fmt = src_or_format
        else:
            mt = self.resolve_media_type(src_or_format)
            fmt = mt.format

        # 1) plugin
        if fmt in self._writer_plugins:
            return self._writer_plugins[fmt]()

        return None


    # ==========================================================
    # INGESTION PIPELINE INTEGRATION
    # ==========================================================
    def prepare_ingestion(
        self,
        src: str | Path | bytes,
    ) -> dict[str, Any]:

        mt = self.resolve_media_type(src)

        parser = None
        try:
            parser = self.get_parser(src)
        except Exception:
            pass

        return {
            "media_type": mt,
            "format": mt.format,
            "parser": parser,
            "ingestion_workflow": self._suggest_workflow(mt),
            "is_binary": mt.raw_type == MediaRawType.BINARY,
            "kind": mt.kind,
            "standard": mt.standard,
        }

    # ==========================================================
    # SMART WORKFLOW LEVEL (industrial routing)
    # ==========================================================
    def _suggest_workflow(self, mt: MediaType) -> str:
        # این بخش به صورت تخصصی برای مسیرهای ingestion کاربرد دارد
        if mt.format == DocumentFormat.PDF:
            return "workflow_pdf_extraction"

        if mt.format in {DocumentFormat.JSON, DocumentFormat.XML, DocumentFormat.YAML}:
            return "workflow_structured_data"

        if mt.kind == MediaContentKind.TABULAR:
            return "workflow_tabular_analytics"

        if mt.standard == "csdm":
            return "workflow_cad_pipeline"

        if mt.raw_type == MediaRawType.TEXT:
            return "workflow_text_ingestion"

        return "workflow_generic_binary"

    # ==========================================================
    # SUPPORTED FORMATS
    # ==========================================================
    def supported_formats(self) -> Sequence[DocumentFormat]:
        return [mt.format for mt in self.media_registry.all()]
