"""
Plain text parser for the USDM document engine.
"""
from __future__ import annotations

import re
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ....models.base import ElementType
from ....models.exceptions import DocumentParseError
from ....models.media_types import MEDIA_TYPES
from ....models.usdm_models import CodeContent
from ....models.usdm_models import DocumentElement
from ....models.usdm_models import HeadingContent
from ....models.usdm_models import LineBreakContent
from ....models.usdm_models import ListContent
from ....models.usdm_models import ListItemContent
from ....models.usdm_models import LogicalElement
from ....models.usdm_models import ParagraphContent
from ....models.usdm_models import RichTextContent
from ....models.usdm_models import RichTextSpan
from ....models.usdm_models import Section
from ....models.usdm_models import USDMDocument
from ..base import BaseDocumentParser
from ..base import ParseOptions


def _detect_encoding(data: bytes) -> str:
    """
    Detect the encoding of raw byte data.

    Uses BOM detection for UTF-16/UTF-32, then chardet if available,
    then heuristic fallback detection.
    """
    if data[:4] == b'\x00\x00\xfe\xff':
        return 'utf-32-be'
    if data[:4] == b'\xff\xfe\x00\x00':
        return 'utf-32-le'
    if data[:2] == b'\xff\xfe':
        return 'utf-16-le'
    if data[:2] == b'\xfe\xff':
        return 'utf-16-be'

    try:
        import chardet
        result = chardet.detect(data)
        if result and result.get('encoding') and result.get('confidence', 0) > 0.5:
            enc = result['encoding']
            if enc is not None:
                return enc
    except ImportError:
        pass

    try:
        data.decode('utf-8')
        return 'utf-8'
    except UnicodeDecodeError:
        pass

    try:
        data.decode('ascii')
        return 'ascii'
    except UnicodeDecodeError:
        pass

    try:
        data.decode('utf-16-le')
        return 'utf-16-le'
    except (UnicodeDecodeError, ValueError):
        pass

    try:
        data.decode('utf-16-be')
        return 'utf-16-be'
    except (UnicodeDecodeError, ValueError):
        pass

    return 'windows-1252'


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs separated by double newlines."""
    raw_blocks = re.split(r'\n\s*\n', text)
    return [block.strip() for block in raw_blocks if block.strip()]


_UNDERLINE_RE = re.compile(r'^[=\-]{3,}\s*$')

_PATTERNS_BULLET = re.compile(r'^[-*+•]\s+')
_PATTERNS_DECIMAL = re.compile(r'^\d+\.\s+')
_PATTERNS_DECIMAL_PAREN = re.compile(r'^\d+\)\s+')
_PATTERNS_ALPHA = re.compile(r'^[a-zA-Z]\.\s+')
_PATTERNS_ALPHA_PAREN = re.compile(r'^[a-zA-Z]\)\s+')
_PATTERNS_ROMAN = re.compile(r'^[ivxIVX]+\.\s+')
_PATTERNS_ROMAN_PAREN = re.compile(r'^[ivxIVX]+\)\s+')

_LIST_CLEAN_RE = re.compile(
    r'^[-*+•]\s+|^\d+\.\s+|^\d+\)\s+|'
    r'^[a-zA-Z]\.\s+|^[a-zA-Z]\)\s+|'
    r'^[ivxIVX]+\.\s+|^[ivxIVX]+\)\s+'
)


def _is_heading_line(lines: list[str], index: int) -> tuple[bool, int]:
    """
    Heuristic detection of heading lines.

    Returns (is_heading, heading_level).
    A line is a heading if followed by === (level 1) or --- (level 2),
    or if it is all caps containing at least one letter and is either
    more than 3 characters or contains a space.
    """
    line = lines[index]
    stripped = line.strip()

    if not stripped:
        return False, 0

    if index + 1 < len(lines) and _UNDERLINE_RE.match(lines[index + 1].strip()):
        char = lines[index + 1].strip()[0]
        level = 1 if char == '=' else 2
        return True, level

    if len(stripped) > 1 and stripped == stripped.upper() and re.search(r'[A-Z]', stripped):
        if ' ' in stripped or len(stripped) > 3:
            return True, 1

    return False, 0


def _is_list_item(line: str) -> bool:
    """Check if a line matches list item patterns."""
    stripped = line.lstrip()
    if not stripped:
        return False

    return bool(
        _PATTERNS_BULLET.match(stripped)
        or _PATTERNS_DECIMAL.match(stripped)
        or _PATTERNS_DECIMAL_PAREN.match(stripped)
        or _PATTERNS_ALPHA.match(stripped)
        or _PATTERNS_ALPHA_PAREN.match(stripped)
        or _PATTERNS_ROMAN.match(stripped)
        or _PATTERNS_ROMAN_PAREN.match(stripped)
    )


def _is_indented_code_line(line: str) -> bool:
    """Check if a line has consistent leading indentation (4+ spaces or tab)."""
    return line.startswith('\t') or line.startswith('    ')


def _ordered_kind(line: str) -> bool:
    """Determine if a list item line indicates an ordered list."""
    stripped = line.lstrip()
    if _PATTERNS_DECIMAL.match(stripped) or _PATTERNS_DECIMAL_PAREN.match(stripped):
        return True
    if _PATTERNS_ALPHA.match(stripped) or _PATTERNS_ALPHA_PAREN.match(stripped):
        return True
    if _PATTERNS_ROMAN.match(stripped) or _PATTERNS_ROMAN_PAREN.match(stripped):
        return True
    return False


class TXTParser(BaseDocumentParser):
    """Plain text document parser for the USDM document engine."""

    name: str = "txt"
    supported_extensions: tuple[str, ...] = (".txt", ".text", ".log")

    def __init__(self):
        super().__init__()
        self._element_counter = 0

    def _next_id(self, prefix: str = "elem") -> str:
        self._element_counter += 1
        return f"{prefix}_{self._element_counter}"

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str,
                          metadata: dict[str, Any] | None = None,
                          options: ParseOptions | None = None) -> USDMDocument:
        """
        Parse plain text from raw bytes into a USDMDocument.
        """
        try:
            opts = options or ParseOptions()
            encoding = opts.encoding or _detect_encoding(data)
            text = data.decode(encoding, errors='replace')
            return self._build_document(text, document_id, source_name, metadata, encoding)
        except DocumentParseError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Error parsing TXT document: {e}")

    async def parse_path(self, path: str | Path, document_id: str,
                        metadata: dict[str, Any] | None = None,
                        options: ParseOptions | None = None) -> USDMDocument:
        """
        Parse a plain text file from a filesystem path.
        """
        try:
            opts = options or ParseOptions()
            file_path = Path(path)
            data = file_path.read_bytes()
            encoding = opts.encoding or _detect_encoding(data)
            text = data.decode(encoding, errors='replace')
            return self._build_document(text, document_id, file_path.name, metadata, encoding)
        except DocumentParseError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Error parsing TXT file: {e}")

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str,
                          source_name: str, metadata: dict[str, Any] | None = None,
                          options: ParseOptions | None = None) -> USDMDocument:
        """
        Parse plain text from an async byte stream.
        """
        try:
            opts = options or ParseOptions()
            chunks: list[bytes] = []
            async for chunk in stream:
                chunks.append(chunk)
            data = b''.join(chunks)
            encoding = opts.encoding or _detect_encoding(data)
            text = data.decode(encoding, errors='replace')
            return self._build_document(text, document_id, source_name, metadata, encoding)
        except DocumentParseError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Error parsing TXT stream: {e}")

    def _build_document(self, text: str, document_id: str, source_name: str,
                        metadata: dict[str, Any] | None, encoding: str) -> USDMDocument:
        """Build a USDMDocument from decoded plain text."""
        self._element_counter = 0
        section = Section(
            section_id="section_1",
            title=None,
            elements=[],
            section_type="body"
        )

        elements: list[DocumentElement] = []
        logical_elements: list[LogicalElement] = []

        paragraphs = _split_paragraphs(text)

        for para_text in paragraphs:
            para_lines = para_text.splitlines()
            self._process_block(para_lines, section, elements, logical_elements)

        merged_metadata: dict[str, Any] = {
            "source_format": "txt",
            "encoding": encoding,
        }
        if metadata:
            merged_metadata.update(metadata)

        title = source_name
        for ext in (".txt", ".text", ".log"):
            if title.lower().endswith(ext):
                title = title[:-len(ext)]
                break

        return USDMDocument(
            document_id=document_id,
            title=title,
            media_type=MEDIA_TYPES["txt"],
            file_extension=".txt",
            sections=[section],
            elements=elements,
            logical_elements=logical_elements,
            pages=[],
            metadata=merged_metadata,
            raw_text=text
        )

    def _process_block(self, lines: list[str], section: Section,
                       elements: list[DocumentElement],
                       logical_elements: list[LogicalElement]) -> None:
        """Process a text block and classify lines into headings, lists, code, or paragraphs."""
        if not lines:
            return

        classified: list[tuple[str, str] | tuple[str, str, int]] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            is_heading, level = _is_heading_line(lines, i)
            if is_heading:
                consumed = 1
                if i + 1 < len(lines) and _UNDERLINE_RE.match(lines[i + 1].strip()):
                    consumed = 2
                classified.append(('heading', stripped, level))
                i += consumed
                continue

            is_list = _is_list_item(line)
            if is_list:
                classified.append(('list', stripped))
                i += 1
                continue

            if _is_indented_code_line(line):
                classified.append(('code', stripped))
                i += 1
                continue

            classified.append(('text', stripped))
            i += 1

        self._emit_elements(classified, section, elements, logical_elements)

    def _emit_elements(self, classified: list[tuple[str, str] | tuple[str, str, Any]],
                       section: Section, elements: list[DocumentElement],
                       logical_elements: list[LogicalElement]) -> None:
        """Convert classified lines into USDM elements."""
        idx = 0
        while idx < len(classified):
            entry = classified[idx]
            kind = entry[0]

            if kind == 'heading':
                content = entry[1]
                level: int = entry[2] if len(entry) > 2 else 1
                elem_id = self._next_id("heading")

                heading_content = HeadingContent(
                    level=level,
                    text=RichTextContent(spans=[RichTextSpan(text=content)])
                )

                logical_elem = LogicalElement(
                    element_id=elem_id,
                    element_type=ElementType.HEADING,
                    content=heading_content,
                    metadata={"level": level}
                )
                logical_elements.append(logical_elem)

                doc_elem = DocumentElement(
                    element_id=elem_id,
                    element_type=ElementType.HEADING,
                    metadata={"level": level}
                )
                elements.append(doc_elem)
                section.elements.append(doc_elem)
                idx += 1

            elif kind == 'list':
                list_items_lines: list[tuple[bool, str, str]] = []
                ordered = False
                while idx < len(classified) and classified[idx][0] == 'list':
                    lst_content = classified[idx][1]
                    is_ord = _ordered_kind(lst_content)
                    if is_ord:
                        ordered = True
                    clean_text = _LIST_CLEAN_RE.sub('', lst_content)
                    list_items_lines.append((is_ord, lst_content, clean_text))
                    idx += 1

                list_item_contents: list[ListItemContent] = []
                for _, _, item_text in list_items_lines:
                    item_para_elem = LogicalElement(
                        element_id=self._next_id("para"),
                        element_type=ElementType.PARAGRAPH,
                        content=ParagraphContent(
                            text=RichTextContent(spans=[RichTextSpan(text=item_text)])
                        )
                    )
                    logical_elements.append(item_para_elem)
                    item_doc_elem = DocumentElement(
                        element_id=item_para_elem.element_id,
                        element_type=ElementType.PARAGRAPH
                    )
                    elements.append(item_doc_elem)
                    section.elements.append(item_doc_elem)

                    list_item_contents.append(ListItemContent(elements=[item_para_elem]))

                list_elem_id = self._next_id("list")
                list_content = ListContent(ordered=ordered, items=list_item_contents)
                list_logical = LogicalElement(
                    element_id=list_elem_id,
                    element_type=ElementType.LIST,
                    content=list_content
                )
                logical_elements.append(list_logical)

                list_doc_elem = DocumentElement(
                    element_id=list_elem_id,
                    element_type=ElementType.LIST,
                    metadata={"ordered": ordered}
                )
                elements.append(list_doc_elem)
                section.elements.append(list_doc_elem)

            elif kind == 'code':
                code_lines: list[str] = []
                while idx < len(classified) and classified[idx][0] == 'code':
                    # Preserve original indentation relative to the block
                    code_lines.append(classified[idx][1])
                    idx += 1

                code_text = '\n'.join(code_lines)
                elem_id = self._next_id("code")

                code_content = CodeContent(code=code_text, language=None)
                code_logical = LogicalElement(
                    element_id=elem_id,
                    element_type=ElementType.CODE,
                    content=code_content
                )
                logical_elements.append(code_logical)

                code_doc_elem = DocumentElement(
                    element_id=elem_id,
                    element_type=ElementType.CODE
                )
                elements.append(code_doc_elem)
                section.elements.append(code_doc_elem)

            elif kind == 'text':
                text_lines: list[str] = []
                while idx < len(classified) and classified[idx][0] == 'text':
                    text_lines.append(classified[idx][1])
                    idx += 1

                if not text_lines:
                    continue

                self._emit_paragraph(text_lines, section, elements, logical_elements)

    def _emit_paragraph(self, text_lines: list[str], section: Section,
                        elements: list[DocumentElement],
                        logical_elements: list[LogicalElement]) -> None:
        """Emit a paragraph with line breaks preserved as LineBreakContent."""
        elem_id = self._next_id("para")

        spans: list[RichTextSpan]
        if len(text_lines) == 1:
            spans = [RichTextSpan(text=text_lines[0])]
        else:
            spans = []
            for line_idx, line in enumerate(text_lines):
                if line_idx > 0:
                    break_logical = LogicalElement(
                        element_id=self._next_id("linebreak"),
                        element_type=ElementType.LINE_BREAK,
                        content=LineBreakContent()
                    )
                    logical_elements.append(break_logical)
                    break_doc_elem = DocumentElement(
                        element_id=break_logical.element_id,
                        element_type=ElementType.LINE_BREAK
                    )
                    elements.append(break_doc_elem)
                    section.elements.append(break_doc_elem)
                spans.append(RichTextSpan(text=line))

        para_content = ParagraphContent(
            text=RichTextContent(spans=spans)
        )
        para_logical = LogicalElement(
            element_id=elem_id,
            element_type=ElementType.PARAGRAPH,
            content=para_content
        )
        logical_elements.append(para_logical)

        para_doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.PARAGRAPH
        )
        elements.append(para_doc_elem)
        section.elements.append(para_doc_elem)
