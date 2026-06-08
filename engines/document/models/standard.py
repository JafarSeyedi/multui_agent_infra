# engines/document/models/standards.py
from enum import Enum
from typing import Any

class DocumentStandard(str, Enum):
    """Supported document standards."""

    DSDM = "dsdm"  # Data Structured Document Model
    USDM = "usdm"  # Unified Structured Document Model
    ESDM = "esdm"  # Excel/Spreadsheet Structured Document Model
    PSDM = "psdm"  # Presentation Structured Document Model
    CSDM = "csdm"  # CAD/Geometric Structured Document Model
    MSDM = "msdm"  # Metadata (of data) Structured Definition Model
    SSDM = "ssdm"  # Service Structured Definition Model
    TSDM = "tsdm"   # Tools Standard Definition Model
    OSDM = "osdm"   # Orchestration Standard Definition Model
    KSDM = "ksdm"   # Knowledge Structured Definition Model
    LSDM = "lsdm"   # Event Log Standard Definition Model
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
            "tsdm": "Tools Standard Definition Model",
            "osdm": "Orchestration Standard Definition Model",
            "ksdm": "Knowledge Structured Definition Model",
            "lsdm": "Event Log Standard Definition Model",
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
            "tsdm": "Tools Standard Definition Model",
            "osdm": "Orchestration Standard Definition Model including workflows, orchestrations, decisions, case management, and event processing models",
            "ksdm": "Knowledge Structured Definition Model",
            "lsdm": "Event Log Standard Definition Model",
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
    TOOLS_DEFINITION = "service_definition"
    ORCHESTRATION_DEFINITION = "orchestration_definition"
    KNOWLEDGE_EXTRACTION_DEFINITION = "knowledge_extraction_definition"
    EVENT_LOG = "event_log"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    EXECUTABLE = "executable"
    DATABASE = "database"
    OTHER = "other"

# In get_common_formats
STANDARD_TO_CATEGORY: dict[DocumentStandard, MediaCategory] = {
    DocumentStandard.DSDM: MediaCategory.STRUCTURED_DATA,
    DocumentStandard.USDM: MediaCategory.DOCUMENT,
    DocumentStandard.ESDM: MediaCategory.SPREADSHEET,
    DocumentStandard.PSDM: MediaCategory.PRESENTATION,
    DocumentStandard.CSDM: MediaCategory.CAD_GEOMETRIC,
    DocumentStandard.MSDM: MediaCategory.SCHEMA_DEFINITION,
    DocumentStandard.SSDM: MediaCategory.SERVICE_DEFINITION,
    DocumentStandard.TSDM: MediaCategory.TOOLS_DEFINITION,
    DocumentStandard.OSDM: MediaCategory.ORCHESTRATION_DEFINITION,
    DocumentStandard.KSDM: MediaCategory.KNOWLEDGE_EXTRACTION_DEFINITION,
    DocumentStandard.LSDM: MediaCategory.EVENT_LOG,
}

# Abbreviation definitions for documentation
ABBREVIATIONS: dict[str, str] = {
    # Standards
    "DSDM": "Data Structured Document Model",
    "USDM": "Unified Structured Document Model",
    "ESDM": "Excel/Spreadsheet Document Model",
    "PSDM": "Presentation Document Model",
    "CSDM": "CAD/Geometric Structured Document Model",
    "MSDM": "Metadata Standard Definition Model",
    "SSDM": "Service Standard Definition Model",
    "TSDM": "Tool Standard Definition Model",
    "OSDM": "Orchestration Standard Definition Model",
    "KSDM": "Knowledge Structured Definition Model",
    "LSDM": "Event Log Standard Definition Model",

    # Components
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

    # Concepts
    "AST": "Abstract Syntax Tree",
    "DOM": "Document Object Model",
    "SAX": "Simple API for XML",
    "STAX": "Streaming API for XML",
}

def get_standard_info(standard: DocumentStandard) -> dict[str, Any]:
    """Get complete information for a standard"""
    return {
        "code": standard.value,
        "name": standard.full_name,
        "description": standard.description,
        "category": STANDARD_TO_CATEGORY.get(standard),
        "common_formats": get_common_formats(standard)
    }

def get_common_formats(standard: DocumentStandard) -> list[str]:
    """Get common formats for each standard"""
    formats = {
        DocumentStandard.DSDM: ["json", "xml", "yaml", "toml", "csv", "tsv"],
        DocumentStandard.USDM: ["pdf", "docx", "html", "md", "txt", "rtf"],
        DocumentStandard.ESDM: ["xlsx", "xls", "csv", "tsv", "prn", "ods", "parquet", "feather", "arrow", "txt"],
        DocumentStandard.CSDM: ["dxf", "dwg", "ifc", "stl", "step"],
        DocumentStandard.PSDM: ["pptx", "ppt", "odp"],
        DocumentStandard.CSDM: ["dxf", "dwg", "ifc", "stl", "step"],
        DocumentStandard.MSDM: [
            "xsd", "json_schema", "sql_ddl", "cql", "mongodb_schema",
            "influxdb_schema", "elasticsearch_mapping", "neo4j_schema",
            "proto", "thrift_idl", "graphql_schema", #"avro_schema", 
            "owl", "plantuml", # "cue", 
            "python_model", "typescript_interface"
        ],
        DocumentStandard.SSDM: ["openapi", "wsdl", "yang", "asyncapi", "proto", "py", "gql", "graphql", "mcp.json"],
        DocumentStandard.TSDM: ["tsdm_json"],
        DocumentStandard.OSDM: ["bpmn", "cmmn", "dmn", "pnml", "graphml", "serverless_workflow_json", "serverless_workflow_yaml"],
        DocumentStandard.LSDM: ["xes", "syslog", "cef", "es_bulk"],
        DocumentStandard.KSDM: [
            "xmla_discover_xml", "mondrian_schema", "cwm_xmi",
            "pmml_xml", "onnx_protobuf", "rdf_turtle", "rml_yaml",
            "jprm_json", "yprm_yaml",
        ],

    }
    return formats.get(standard, [])
