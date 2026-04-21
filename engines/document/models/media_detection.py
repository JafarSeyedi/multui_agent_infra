# engines/document/models/media_detection.py
import os
import json
import xml.etree.ElementTree as ET

from typing import Optional, Tuple
from .media_types import MEDIA_TYPES, MediaType


# -------------------------------
# 1) DETECT BY EXTENSION
# -------------------------------
def detect_by_extension(ext: str) -> MediaType:
    for mt in MEDIA_TYPES.values():
        if ext in mt.extensions:
            return mt
    return MEDIA_TYPES["text"]

def detect_by_file_extension(path: str) -> Optional[MediaType]:
    ext = os.path.splitext(path)[1].lower()  # ".pdf"
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
# 3) CONTENT SNIFFING (binary + structured + text)
# ------------------------------------------------------
def _is_pdf(data: bytes) -> bool:
    return data.startswith(b"%PDF")


def _is_zip_based(data: bytes) -> bool:
    # ZIP magic numbers: PK\x03\x04 or PK\x05\x06
    return data[:4] in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


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
    # ساده‌ترین تست ممکن، اما کافی برای شروع
    return any(c in text for c in [":", "- ", "..." ])


def _detect_csv_tsv(text: str) -> Optional[str]:
    # CSV detection
    if "," in text and "\n" in text:
        return "csv"
    # TSV detection
    if "\t" in text and "\n" in text:
        return "tsv"
    return None


def _is_binary(data: bytes) -> bool:
    # If NULL bytes exist → almost always binary
    if b"\x00" in data:
        return True
    # heuristic: >20% bytes outside ASCII/text range
    nontext = sum(1 for b in data if b > 0x7F)
    return nontext / max(1, len(data)) > 0.2


# ------------------------------------------------------
# MAIN CONTENT DETECTOR
# ------------------------------------------------------
def detect_by_content(data: bytes) -> Optional[MediaType]:

    # ---- PDF
    if _is_pdf(data):
        return MEDIA_TYPES["pdf"]

    # ---- ZIP-BASED formats (xlsx/docx)
    if _is_zip_based(data):
        # ZIP-based formats → inspect [Content_Types].xml if needed
        # For simplicity, assign XLSX as default; real impl can inspect inner file.
        return MEDIA_TYPES["xlsx"]

    # ---- Structured Binary Formats
    # BSON starts with 4-byte length
    if len(data) > 4:
        total_len = int.from_bytes(data[:4], "little")
        if total_len == len(data):
            return MEDIA_TYPES["bson"]

    # MessagePack detection by prefix ranges
    first = data[0]
    if 0x80 <= first <= 0x8F or 0x90 <= first <= 0x9F or 0xA0 <= first <= 0xBF:
        return MEDIA_TYPES["messagepack"]

    # CBOR: major types + initial bytes (0xA0–0xBF are common)
    if first in range(0xA0, 0xC0):
        return MEDIA_TYPES["cbor"]

    # ---- Try decode as UTF-8 text
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return MEDIA_TYPES["binary"]  # fallback

    # ---- JSON
    if _is_json(text):
        return MEDIA_TYPES["json"]

    # ---- XML
    if _is_xml(text):
        return MEDIA_TYPES["xml"]

    # ---- YAML (heuristic)
    if _is_yaml(text):
        return MEDIA_TYPES["yaml"]

    # ---- CSV / TSV
    t = _detect_csv_tsv(text)
    if t and t in MEDIA_TYPES:
        return MEDIA_TYPES[t]

    # ---- Markdown heuristic
    if "#" in text or "*" in text or "`" in text:
        return MEDIA_TYPES["markdown"]

    # ---- Plain text
    return MEDIA_TYPES["text"]

def detect_media_type(
    path: Optional[str] = None,
    mime: Optional[str] = None,
    data: Optional[bytes] = None
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

    # Fallback
    return MEDIA_TYPES["text"]

