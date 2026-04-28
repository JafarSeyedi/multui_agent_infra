# engines/document/models/standards.py

from enum import Enum
from typing import Dict, Any

class DocumentStandard(str, Enum):
    """Supported document standards."""

    DSDM = "dsdm"  # Data Structured Document Model
    USDM = "usdm"  # Unified Structured Document Model
    ESDM = "esdm"  # Excel/Spreadsheet Structured Document Model
    PSDM = "psdm"  # Presentation Structured Document Model
    CSDM = "csdm"  # CAD/Geometric Structured Document Model
    MSDM = "msdm"  # Metadata (of data) Structured Definition Model
    SSDM = "ssdm"  # Service Structured Definition Model
    GENERIC = "generic"
    UNKNOWN = "unknown"

    @property
    def full_name(self) -> str:
        names = {
            "dsdm": "Data Structured Document Model",
            "usdm": "Unified Structured Document Model",
            "esdm": "Excel/Spreadsheet Structured Document Model",
            "psdm": "Presentation Structured Document Model",
            "csdm": "CAD/Geometric Structured Document Model",
            "msdm": "Metadata Structured Definition Model",
            "ssdm": "Service Structured Definition Model",
            "generic": "Generic Text/Binary",
            "unknown": "Unknown",
        }
        return names.get(self.value, self.value)

    @property
    def description(self) -> str:
        descriptions = {
            "dsdm": "Structured data document model for JSON, XML, YAML, etc.",
            "usdm": "Unified structured document model for textual/page-based documents",
            "esdm": "Structured document model for tabular data and spreadsheets",
            "psdm": "Structured document model for presentations",
            "csdm": "Structured document model for CAD models and geometric data",
            "msdm": "Structured document model for data structure definitions (schemas, DDL, ERD, etc.)",
            "ssdm": "Structured document model for service/API definitions (OpenAPI, WSDL, etc.)",
            "generic": "No specific structure enforced",
            "unknown": "Unknown",
        }
        return descriptions.get(self.value, "")

class MediaCategory(str, Enum):
    STRUCTURED_DATA = "structured_data"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    CAD_GEOMETRIC = "cad_geometric"
    SCHEMA_DEFINITION = "schema_definition"
    SERVICE_DEFINITION = "service_definition"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    EXECUTABLE = "executable"
    DATABASE = "database"
    OTHER = "other"

STANDARD_TO_CATEGORY: Dict[DocumentStandard, MediaCategory] = {
    DocumentStandard.DSDM: MediaCategory.STRUCTURED_DATA,
    DocumentStandard.USDM: MediaCategory.DOCUMENT,
    DocumentStandard.ESDM: MediaCategory.SPREADSHEET,
    DocumentStandard.PSDM: MediaCategory.PRESENTATION,
    DocumentStandard.CSDM: MediaCategory.CAD_GEOMETRIC,
    DocumentStandard.MSDM: MediaCategory.SCHEMA_DEFINITION,
    DocumentStandard.SSDM: MediaCategory.SERVICE_DEFINITION,
}

# تعاریف مخفف‌ها برای مستندات
ABBREVIATIONS: Dict[str, str] = {
    # استانداردها
    "DSDM": "Data Structured Document Model",
    "USDM": "Unified Structured Document Model",
    "ESDM": "Excel/Spreadsheet Document Model",
    "PSDM": "Presentation Document Model",
    "CSDM": "CAD/Geometric Structured Document Model",
    "MSDM": "Metadata Standard Definition Model",
    "SSDM": "Service Standard Definition Model",
    
    # کامپوننت‌ها
    "MIME": "Multipurpose Internet Mail Extensions",
    "API": "Application Programming Interface",
    "JSON": "JavaScript Object Notation",
    "XML": "eXtensible Markup Language",
    "YAML": "YAML Ain't Markup Language",
    "CSV": "Comma-Separated Values",
    "PDF": "Portable Document Format",
    "HTML": "HyperText Markup Language",
    "DOCX": "Microsoft Word Document",
    "XLSX": "Microsoft Excel Spreadsheet",
    
    # مفاهیم
    "AST": "Abstract Syntax Tree",
    "DOM": "Document Object Model",
    "SAX": "Simple API for XML",
    "STAX": "Streaming API for XML",
}

def get_standard_info(standard: DocumentStandard) -> Dict[str, Any]:
    """دریافت اطلاعات کامل یک استاندارد"""
    return {
        "code": standard.value,
        "name": standard.full_name,
        "description": standard.description,
        "category": STANDARD_TO_CATEGORY.get(standard),
        "common_formats": get_common_formats(standard)
    }

def get_common_formats(standard: DocumentStandard) -> list[str]:
    """دریافت فرمت‌های رایج برای هر استاندارد"""
    formats = {
        DocumentStandard.DSDM: ["json", "xml", "yaml", "toml", "csv", "tsv"],
        DocumentStandard.USDM: ["pdf", "docx", "html", "md", "txt", "rtf"],
        DocumentStandard.ESDM: ["xlsx", "xls", "csv", "tsv", "prn", "ods", "parquet", "feather", "arrow", "txt"],
        DocumentStandard.CSDM: ["dxf", "dwg", "ifc", "stl", "step"]
        DocumentStandard.PSDM: ["pptx", "ppt", "odp"],
        DocumentStandard.CSDM: ["dxf", "dwg", "ifc", "stl", "step"],
        DocumentStandard.MSDM: [
            "xsd", "json_schema", "sql_ddl", "cql", "mongodb_schema",
            "influxdb_schema", "elasticsearch_mapping", "neo4j_schema",
            "proto", "avro_schema", "thrift_idl", "graphql_schema",
            "owl", "cue", "plantuml",
            "python_model", "typescript_interface"
        ],
        DocumentStandard.SSDM: ["openapi", "swagger", "wsdl", "yang", "mib", "asyncapi", "raml", "apib"],

    }
    return formats.get(standard, [])


