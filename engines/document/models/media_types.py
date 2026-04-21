# engines/document/models/media_types.py

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel
from .standard import DocumentStandard


# ------------------------
# Document Formats
# ------------------------
class DocumentFormat(str, Enum):

    # USDM
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    MARKDOWN = "markdown"
    LATEX = "latex"
    PPT = "ppt"

    # ESDM
    XLSX = "xlsx"
    CSV = "csv"
    TSV = "tsv"
    PARQUET = "parquet"
    ARROW = "arrow"
    FEATHER = "feather"

    # DSDM
    JSON = "json"
    XML = "xml"
    YAML = "yaml"
    BSON = "bson"
    CBOR = "cbor"
    MESSAGEPACK = "messagepack"

    # CSDM
    DXF = "dxf"
    DWG = "dwg"
    IFC = "ifc"

    TEXT = "txt"
    UNKNOWN = "unknown"


# ------------------------
# Media classification
# ------------------------
class MediaContentKind(str, Enum):
    TEXT = "text"
    BINARY = "binary"
    STRUCTURED = "structured"
    TABULAR = "tabular"
    HIERARCHICAL = "hierarchical"
    MIXED = "mixed"
    VECTOR = "vector"
    GEOMETRIC = "geometric"
    UNKNOWN = "unknown"


# ------------------------
# Fallback: raw bytes or raw text?
# ------------------------
class MediaRawType(str, Enum):
    TEXT = "text"
    BINARY = "binary"


# ------------------------
# Core MediaType Model
# ------------------------
class MediaType(BaseModel):
    mime: str
    format: DocumentFormat
    standard: DocumentStandard
    extensions: List[str]
    kind: MediaContentKind
    raw_type: MediaRawType
    description: Optional[str] = None

    # model_config = ConfigDict(frozen=True)  # به جای class Config

# ------------------------
# FULL REGISTRY
# ------------------------
MEDIA_TYPES: Dict[str, MediaType] = {

    # ======================
    # USDM
    # ======================
    "pdf": MediaType(
        mime="application/pdf",
        format=DocumentFormat.PDF,
        standard=DocumentStandard.USDM,
        extensions=[".pdf"],
        kind=MediaContentKind.BINARY,
        raw_type=MediaRawType.BINARY,
        description="Portable Document Format"
    ),

    "docx": MediaType(
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        format=DocumentFormat.DOCX,
        standard=DocumentStandard.USDM,
        extensions=[".docx"],
        kind=MediaContentKind.STRUCTURED,
        raw_type=MediaRawType.BINARY
    ),

    "html": MediaType(
        mime="text/html",
        format=DocumentFormat.HTML,
        standard=DocumentStandard.USDM,
        extensions=[".html", ".htm"],
        kind=MediaContentKind.MIXED,
        raw_type=MediaRawType.TEXT
    ),

    "markdown": MediaType(
        mime="text/markdown",
        format=DocumentFormat.MARKDOWN,
        standard=DocumentStandard.USDM,
        extensions=[".md", ".markdown"],
        kind=MediaContentKind.TEXT,
        raw_type=MediaRawType.TEXT
    ),

    "latex": MediaType(
        mime="application/x-latex",
        format=DocumentFormat.LATEX,
        standard=DocumentStandard.USDM,
        extensions=[".tex"],
        kind=MediaContentKind.TEXT,
        raw_type=MediaRawType.TEXT
    ),


    # ======================
    # ESDM (with XLSX variants)
    # ======================
    "xlsx": MediaType(
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        format=DocumentFormat.XLSX,
        standard=DocumentStandard.ESDM,
        extensions=[".xlsx", ".xlsm", ".xltx", ".xltm"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.BINARY
    ),

    "csv": MediaType(
        mime="text/csv",
        format=DocumentFormat.CSV,
        standard=DocumentStandard.ESDM,
        extensions=[".csv"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.TEXT
    ),

    "tsv": MediaType(
        mime="text/tab-separated-values",
        format=DocumentFormat.TSV,
        standard=DocumentStandard.ESDM,
        extensions=[".tsv"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.TEXT
    ),

    "parquet": MediaType(
        mime="application/parquet",
        format=DocumentFormat.PARQUET,
        standard=DocumentStandard.ESDM,
        extensions=[".parquet"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.BINARY
    ),

    "arrow": MediaType(
        mime="application/vnd.apache.arrow.file",
        format=DocumentFormat.ARROW,
        standard=DocumentStandard.ESDM,
        extensions=[".arrow"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.BINARY
    ),

    "feather": MediaType(
        mime="application/vnd.apache.feather",
        format=DocumentFormat.FEATHER,
        standard=DocumentStandard.ESDM,
        extensions=[".feather"],
        kind=MediaContentKind.TABULAR,
        raw_type=MediaRawType.BINARY
    ),


    # ======================
    # DSDM
    # ======================
    "json": MediaType(
        mime="application/json",
        format=DocumentFormat.JSON,
        standard=DocumentStandard.DSDM,
        extensions=[".json"],
        kind=MediaContentKind.STRUCTURED,
        raw_type=MediaRawType.TEXT
    ),

    "xml": MediaType(
        mime="application/xml",
        format=DocumentFormat.XML,
        standard=DocumentStandard.DSDM,
        extensions=[".xml"],
        kind=MediaContentKind.HIERARCHICAL,
        raw_type=MediaRawType.TEXT
    ),

    "yaml": MediaType(
        mime="application/x-yaml",
        format=DocumentFormat.YAML,
        standard=DocumentStandard.DSDM,
        extensions=[".yaml", ".yml"],
        kind=MediaContentKind.STRUCTURED,
        raw_type=MediaRawType.TEXT
    ),

    "bson": MediaType(
        mime="application/bson",
        format=DocumentFormat.BSON,
        standard=DocumentStandard.DSDM,
        extensions=[".bson"],
        kind=MediaContentKind.BINARY,
        raw_type=MediaRawType.BINARY
    ),

    "cbor": MediaType(
        mime="application/cbor",
        format=DocumentFormat.CBOR,
        standard=DocumentStandard.DSDM,
        extensions=[".cbor"],
        kind=MediaContentKind.BINARY,
        raw_type=MediaRawType.BINARY
    ),

    "messagepack": MediaType(
        mime="application/msgpack",
        format=DocumentFormat.MESSAGEPACK,
        standard=DocumentStandard.DSDM,
        extensions=[".msgpack"],
        kind=MediaContentKind.BINARY,
        raw_type=MediaRawType.BINARY
    ),


    # ======================
    # CSDM
    # ======================
    "dxf": MediaType(
        mime="image/vnd.dxf",
        format=DocumentFormat.DXF,
        standard=DocumentStandard.CSDM,
        extensions=[".dxf"],
        kind=MediaContentKind.VECTOR,
        raw_type=MediaRawType.BINARY
    ),

    "dwg": MediaType(
        mime="image/vnd.dwg",
        format=DocumentFormat.DWG,
        standard=DocumentStandard.CSDM,
        extensions=[".dwg"],
        kind=MediaContentKind.VECTOR,
        raw_type=MediaRawType.BINARY
    ),

    "ifc": MediaType(
        mime="application/ifc",
        format=DocumentFormat.IFC,
        standard=DocumentStandard.CSDM,
        extensions=[".ifc"],
        kind=MediaContentKind.GEOMETRIC,
        raw_type=MediaRawType.BINARY
    ),


    # ======================
    # FALLBACK TYPES
    # ======================
    "binary": MediaType(
        mime="application/octet-stream",
        format=DocumentFormat.UNKNOWN,
        standard=DocumentStandard.UNKNOWN,
        extensions=[".bin"],
        kind=MediaContentKind.BINARY,
        raw_type=MediaRawType.BINARY
    ),

    "text": MediaType(
        mime="text/plain",
        format=DocumentFormat.TEXT,
        standard=DocumentStandard.UNKNOWN,
        extensions=[".txt"],
        kind=MediaContentKind.TEXT,
        raw_type=MediaRawType.TEXT
    ),
}


class MediaTypeRegistry:
    """Logical wrapper around MEDIA_TYPES data."""
    
    _items = MEDIA_TYPES

    @classmethod
    def get_by_format(cls, fmt: DocumentFormat) -> Optional[MediaType]:
        for mt in cls._items.values():
            if mt.format == fmt:
                return mt
        return None

    @classmethod
    def get_by_extension(cls, ext: str) -> Optional[MediaType]:
        if not ext.startswith("."): ext = f".{ext}"
        for mt in cls._items.values():
            if ext.lower() in [e.lower() for e in mt.extensions]:
                return mt
        return None

    @classmethod
    def get_by_mime(cls, mime: str) -> Optional[MediaType]:
        for mt in cls._items.values():
            if mt.mime == mime:
                return mt
        return None

    @classmethod
    def all(cls) -> List[MediaType]:
        return list(cls._items.values())
