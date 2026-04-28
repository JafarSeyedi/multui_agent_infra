# engines/document/models/media_detection.py
import os
import re
import io
import json
import zipfile
import xml.etree.ElementTree as ET

from typing import Optional
from .media_types import MEDIA_TYPES, MediaType


# -------------------------------
# 1) DETECT BY EXTENSION
# -------------------------------
def detect_by_extension(ext: str) -> MediaType:
    for mt in MEDIA_TYPES.values():
        if ext in mt.extensions:
            return mt
    return MEDIA_TYPES["text_generic"]


def detect_by_file_extension(path: str) -> Optional[MediaType]:
    ext = os.path.splitext(path)[1].lower()
    for mt in MEDIA_TYPES.values():
        if ext in mt.extensions:
            return mt
    return None


# -------------------------------
# 2) DETECT BY MIME-TYPE
# -------------------------------
def detect_by_mime(mime: str) -> Optional[MediaType]:
    mime = mime.lower()
    for mt in MEDIA_TYPES.values():
        if mt.mime.lower() == mime:
            return mt
    return None


# ------------------------------------------------------
# 3) CONTENT SNIFFING HELPERS
# ------------------------------------------------------
def _is_pdf(data: bytes) -> bool:
    return data.startswith(b"%PDF")


def _is_zip_based(data: bytes) -> bool:
    return data[:4] in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


def _detect_zip_sub_type(data: bytes) -> MediaType:
    """Open a ZIP and inspect [Content_Types].xml to distinguish DOCX/XLSX/PPTX."""
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
            ct_xml = zf.read("[Content_Types].xml")
            root = ET.fromstring(ct_xml)
            ns = {"ct": "http://schemas.openxmlformats.org/package/2006/content-types"}
            for elem in root.iter():
                tag = elem.tag.split("}")[-1]
                if tag == "Default":
                    ct = elem.get("ContentType", "")
                    if "spreadsheet" in ct:
                        return MEDIA_TYPES["xlsx"]
                    if "wordprocessing" in ct:
                        return MEDIA_TYPES["docx"]
                    if "presentation" in ct:
                        return MEDIA_TYPES["pptx"]
                elif tag == "Override":
                    part = elem.get("PartName", "")
                    ct = elem.get("ContentType", "")
                    if "/workbook.xml" in part or "spreadsheet" in ct:
                        return MEDIA_TYPES["xlsx"]
                    if "/document.xml" in part or "wordprocessing" in ct:
                        return MEDIA_TYPES["docx"]
                    if "/presentation.xml" in part or "presentation" in ct:
                        return MEDIA_TYPES["pptx"]
    except Exception:
        pass
    return MEDIA_TYPES["binary"]


def _is_binary(data: bytes) -> bool:
    if b"\x00" in data:
        return True
    nontext = sum(1 for b in data if b > 0x7F)
    return nontext / max(1, len(data)) > 0.2


# ---- Text-based detectors ----
def _is_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except Exception:
        return False


def _is_xml(text: str) -> bool:
    try:
        ET.fromstring(text)
        return True
    except Exception:
        return False


def _is_yaml(text: str) -> bool:
    return any(c in text for c in [": ", "- ", "..."])


def _is_toml(text: str) -> bool:
    return ("[" in text and "]" in text and "=" in text)


def _is_json_schema(text: str) -> bool:
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            if "$schema" in data or "type" in data or "properties" in data:
                return True
        return False
    except Exception:
        return False


def _is_xsd(text: str) -> bool:
    try:
        root = ET.fromstring(text)
        return root.tag == '{http://www.w3.org/2001/XMLSchema}schema' or root.tag == 'xs:schema'
    except Exception:
        return False


def _is_wsdl(text: str) -> bool:
    try:
        root = ET.fromstring(text)
        return root.tag == '{http://schemas.xmlsoap.org/wsdl/}definitions' or 'wsdl' in root.tag.lower()
    except Exception:
        return False


def _is_proto(text: str) -> bool:
    return bool(re.search(r'\bsyntax\s*=\s*"proto[23]"', text))


def _is_graphql_schema(text: str) -> bool:
    return bool(re.search(r'\b(type|enum|input|interface|union|schema)\s+\w+\s*\{', text))


def _is_openapi(text: str) -> bool:
    if _is_json(text):
        data = json.loads(text)
        if isinstance(data, dict) and ("openapi" in data or "swagger" in data):
            return True
    elif _is_yaml(text):
        if re.search(r'^(openapi|swagger)\s*:', text, re.MULTILINE):
            return True
    return False


def _is_sql_ddl(text: str) -> bool:
    return bool(re.search(r'\b(CREATE|ALTER|DROP)\s+(TABLE|INDEX|VIEW|DATABASE)', text, re.IGNORECASE))


def _is_cql(text: str) -> bool:
    return bool(re.search(r'CREATE\s+TABLE\s+.*PRIMARY\s+KEY\s*\(\(', text, re.IGNORECASE))


def _is_mongodb_schema(text: str) -> bool:
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            if "validator" in data or "mongoose" in data.get("$jsonSchema", {}):
                return True
            if "collection" in data and "schema" in data:
                return True
    except Exception:
        pass
    return False


def _is_influxdb_schema(text: str) -> bool:
    return bool(re.search(r'CREATE\s+MEASUREMENT\s+', text, re.IGNORECASE)) or \
           bool(re.search(r'^from\(', text, re.MULTILINE))


def _is_elasticsearch_mapping(text: str) -> bool:
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "mappings" in data:
            return True
    except Exception:
        pass
    return False


def _is_neo4j_schema(text: str) -> bool:
    return bool(re.search(r'CREATE\s+(NODE|RELATIONSHIP|CONSTRAINT|INDEX)', text, re.IGNORECASE)) or \
           bool(re.search(r':\w+\s*\{', text))


def _is_plantuml(text: str) -> bool:
    return bool(re.search(r'@startuml|@start\w+\b', text))


def _is_erd(text: str) -> bool:
    if _is_xml(text):
        root = ET.fromstring(text)
        return root.tag == 'EntityRelationship' or root.find('Entity') is not None
    if _is_json(text):
        data = json.loads(text)
        if isinstance(data, dict) and ("entities" in data or "relationships" in data):
            return True
    return False


def _is_python_model(text: str) -> bool:
    if re.search(r'class\s+\w+\s*\(\s*BaseModel\s*\)', text):
        return True
    if re.search(r'@dataclass\s*\nclass\s+\w+', text):
        return True
    return False


def _is_typescript_interface(text: str) -> bool:
    if re.search(r'\binterface\s+\w+\s*\{', text):
        return True
    if re.search(r'\btype\s+\w+\s*=\s*\{', text):
        return True
    return False


def _detect_csv_tsv(text: str) -> Optional[str]:
    lines = text.splitlines()
    if not lines:
        return None
    commas = sum(line.count(",") for line in lines)
    tabs = sum(line.count("\t") for line in lines)
    if commas > tabs and commas > 0:
        return "csv"
    if tabs > 0:
        return "tsv"
    return None


def _detect_fixed_width(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 3:
        return False
    if "," in text or "\t" in text:
        return False
    lengths = {len(line) for line in lines}
    return len(lengths) == 1 and lengths.pop() > 0


# ------------------------------------------------------
# MAIN CONTENT DETECTOR (strictly ordered)
# ------------------------------------------------------
def detect_by_content(data: bytes) -> Optional[MediaType]:

    # 1. Binary signatures first
    if _is_pdf(data):
        return MEDIA_TYPES["pdf"]

    if _is_zip_based(data):
        return _detect_zip_sub_type(data)

    # 2. Structured binary (BSON, MessagePack, CBOR)
    if len(data) > 4:
        total_len = int.from_bytes(data[:4], "little")
        if total_len == len(data):
            return MEDIA_TYPES["bson"]

    first = data[0]
    if 0x80 <= first <= 0x8F or 0x90 <= first <= 0x9F or 0xA0 <= first <= 0xBF:
        return MEDIA_TYPES["messagepack"]

    if first in range(0xA0, 0xC0):
        return MEDIA_TYPES["cbor"]

    # 3. Decode as text (binary fallback)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return MEDIA_TYPES["binary"]

    # 4. JSON-based specific formats (must precede generic JSON)
    if _is_json(text):
        # JSON Schema must be checked before generic JSON
        if _is_json_schema(text):
            return MEDIA_TYPES["json_schema"]
        if _is_mongodb_schema(text):
            return MEDIA_TYPES["mongodb_schema"]
        if _is_elasticsearch_mapping(text):
            return MEDIA_TYPES["elasticsearch_mapping"]
        if _is_erd(text):
            return MEDIA_TYPES["erd"]
        # OpenAPI JSON
        if _is_openapi(text):
            return MEDIA_TYPES["openapi_json"]
        # All other JSON
        return MEDIA_TYPES["json"]

    # 5. XML-based specific formats (must precede generic XML)
    if _is_xml(text):
        if _is_xsd(text):
            return MEDIA_TYPES["xsd"]
        if _is_wsdl(text):
            return MEDIA_TYPES["wsdl"]
        if _is_erd(text):
            return MEDIA_TYPES["erd"]
        return MEDIA_TYPES["xml"]

    # 6. Specific textual DSLs (no JSON/XML dependency)
    if _is_proto(text):
        return MEDIA_TYPES["proto"]
    if _is_graphql_schema(text):
        return MEDIA_TYPES["graphql_schema"]
    if _is_sql_ddl(text):
        return MEDIA_TYPES["sql_ddl"]
    if _is_cql(text):
        return MEDIA_TYPES["cql"]
    if _is_neo4j_schema(text):
        return MEDIA_TYPES["neo4j_schema"]
    if _is_influxdb_schema(text):
        return MEDIA_TYPES["influxdb_schema"]
    if _is_plantuml(text):
        return MEDIA_TYPES["plantuml"]
    if _is_python_model(text):
        return MEDIA_TYPES["python_model"]
    if _is_typescript_interface(text):
        return MEDIA_TYPES["typescript_interface"]

    # 7. YAML-based (after specific text formats that also look like YAML)
    if _is_yaml(text):
        if _is_openapi(text):
            return MEDIA_TYPES["openapi_yaml"]
        # ERD YAML unlikely, but could be placed before generic YAML
        return MEDIA_TYPES["yaml"]

    # 8. TOML (broad pattern – after all specific patterns)
    if _is_toml(text):
        return MEDIA_TYPES["toml"]

    # 9. Delimiter-based (CSV/TSV) – after structured text that may contain commas
    t = _detect_csv_tsv(text)
    if t and t in MEDIA_TYPES:
        return MEDIA_TYPES[t]

    # 10. Fixed‑width (PRN)
    if _detect_fixed_width(text):
        return MEDIA_TYPES["prn"]

    # 11. Markdown (very broad – must be near end)
    if "#" in text or "*" in text or "`" in text:
        return MEDIA_TYPES["markdown"]

    # 12. Plain text fallback
    return MEDIA_TYPES["text_generic"]


def detect_media_type(
    path: Optional[str] = None,
    mime: Optional[str] = None,
    data: Optional[bytes] = None,
) -> MediaType:

    # 1) Extension
    if path:
        mt = detect_by_file_extension(path)
        if mt:
            return mt

    # 2) MIME
    if mime:
        mt = detect_by_mime(mime)
        if mt:
            return mt

    # 3) Sniff content
    if data:
        mt = detect_by_content(data)
        if mt:
            return mt

    # Final fallback
    return MEDIA_TYPES["text_generic"]