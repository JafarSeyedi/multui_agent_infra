"""Plain text writer for converting USDM documents to TXT format."""
from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ....models.base import BaseDocument
from ....models.exceptions import DocumentWriteError
from ....models.usdm_models import CodeContent
from ....models.usdm_models import FootnoteContent
from ....models.usdm_models import HeadingContent
from ....models.usdm_models import ImageContent
from ....models.usdm_models import LineBreakContent
from ....models.usdm_models import LinkContent
from ....models.usdm_models import ListContent
from ....models.usdm_models import ListItemContent
from ....models.usdm_models import LogicalElement
from ....models.usdm_models import MathContent
from ....models.usdm_models import PageBreakContent
from ....models.usdm_models import ParagraphContent
from ....models.usdm_models import QuoteContent
from ....models.usdm_models import RichTextContent
from ....models.usdm_models import Section
from ....models.usdm_models import TableContent
from ....models.usdm_models import USDMDocument
from ...base import BaseDocumentWriter
from ...base import WriteOptions


class TXTWriter(BaseDocumentWriter):
    """Plain text writer for USDM documents."""

    def __init__(self, options: WriteOptions | None = None):
        super().__init__(options)
        self.options = options or WriteOptions()
        self._list_depth = 0
        self._list_counters: list[int] = []
        self._footnote_counter = 0
        self._footnotes: list[str] = []

    async def write(self, document: BaseDocument) -> bytes:
        """Convert document to plain text bytes."""
        if self.options is None:
            raise DocumentWriteError("WriteOptions not initialized")
        if not isinstance(document, USDMDocument):
            raise DocumentWriteError("Document must be USDMDocument")

        try:
            txt_content = self._convert_usdm_to_txt(document)
            encoding = self.options.custom.get("encoding", self.options.encoding) if self.options.custom else self.options.encoding
            return txt_content.encode(encoding)
        except Exception as e:
            raise DocumentWriteError(f"Error writing TXT: {e}")

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """Write document as a stream."""
        try:
            data = await self.write(document)
            yield data
        except Exception as e:
            raise DocumentWriteError(f"Error writing TXT stream: {e}")

    async def write_to_file(self, document: BaseDocument, target: Path,
                            options: dict[str, Any] | None = None) -> None:
        """Write document to file."""
        try:
            data = await self.write(document)
            target.write_bytes(data)
        except Exception as e:
            raise DocumentWriteError(f"Error writing TXT file: {e}")

    def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    def get_supported_extensions(self) -> list[str]:
        return [".txt", ".text"]

    def _convert_usdm_to_txt(self, document: USDMDocument) -> str:
        """Convert USDM document to plain text."""
        lines: list[str] = []
        self._list_depth = 0
        self._list_counters = []
        self._footnote_counter = 0
        self._footnotes = []

        if document.title:
            lines.append(document.title)
            lines.append("=" * len(document.title))
            lines.append("")

        for section in document.sections:
            section_txt = self._section_to_txt(section, document)
            if section_txt:
                lines.append(section_txt)

        for elem in document.elements:
            in_section = False
            for section in document.sections:
                if any(se.element_id == elem.element_id for se in section.elements):
                    in_section = True
                    break
            if not in_section:
                logical_elem = self._find_logical_element(document, elem.element_id)
                if logical_elem:
                    elem_txt = self._element_to_txt(logical_elem)
                    if elem_txt:
                        lines.append(elem_txt)

        if self._footnotes:
            lines.append("")
            lines.append("-" * 40)
            lines.append("")
            for i, fn in enumerate(self._footnotes, 1):
                lines.append(f"[{i}] {fn}")

        return "\n".join(lines)

    def _find_logical_element(self, document: USDMDocument, element_id: str) -> LogicalElement | None:
        """Find a logical element by ID."""
        for elem in document.logical_elements:
            if elem.element_id == element_id:
                return elem
        return None

    def _section_to_txt(self, section: Section, document: USDMDocument) -> str:
        """Convert a section to plain text."""
        lines: list[str] = []

        if section.title and isinstance(section.title, HeadingContent):
            heading_txt = self._heading_to_txt(section.title)
            if heading_txt:
                lines.append(heading_txt)

        for elem in section.elements:
            logical_elem = self._find_logical_element(document, elem.element_id)
            if logical_elem:
                elem_txt = self._element_to_txt(logical_elem)
                if elem_txt:
                    lines.append(elem_txt)

        return "\n".join(lines)

    def _element_to_txt(self, element: LogicalElement) -> str:
        """Convert a logical element to plain text."""
        content = element.content

        if isinstance(content, ParagraphContent):
            return self._paragraph_to_txt(content)
        elif isinstance(content, HeadingContent):
            return self._heading_to_txt(content)
        elif isinstance(content, CodeContent):
            return self._code_to_txt(content)
        elif isinstance(content, ListContent):
            return self._list_to_txt(content)
        elif isinstance(content, ListItemContent):
            return self._list_item_to_txt(content)
        elif isinstance(content, QuoteContent):
            return self._quote_to_txt(content)
        elif isinstance(content, ImageContent):
            return self._image_to_txt(content)
        elif isinstance(content, LinkContent):
            return self._link_to_txt(content)
        elif isinstance(content, MathContent):
            return self._math_to_txt(content)
        elif isinstance(content, TableContent):
            return self._table_to_txt(content)
        elif isinstance(content, PageBreakContent):
            return "\f"
        elif isinstance(content, LineBreakContent):
            return ""
        elif isinstance(content, FootnoteContent):
            return self._footnote_to_txt(content)

        return ""

    def _rich_text_to_txt(self, rich_text: RichTextContent) -> str:
        """Convert rich text to plain text."""
        if not rich_text or not rich_text.spans:
            return ""

        parts: list[str] = []
        for span in rich_text.spans:
            if span.math:
                parts.append(span.math)
            elif span.text:
                parts.append(span.text)
        return "".join(parts)

    def _paragraph_to_txt(self, content: ParagraphContent) -> str:
        """Convert paragraph to plain text."""
        if not content or not content.text:
            return ""
        text = self._rich_text_to_txt(content.text)
        if not text.strip():
            return ""
        return text

    def _heading_to_txt(self, content: HeadingContent) -> str:
        """Convert heading to plain text."""
        if not content or not content.text:
            return ""

        text = self._rich_text_to_txt(content.text)
        if not text.strip():
            return ""

        level = content.level
        prefix = "#" * level + " "
        return f"{prefix}{text}"

    def _code_to_txt(self, content: CodeContent) -> str:
        """Convert code block to plain text."""
        if not content or not content.code:
            return ""

        code = content.code.rstrip()
        if not code:
            return ""

        lines = code.split("\n")
        return "\n".join(f"    {line}" for line in lines)

    def _list_to_txt(self, content: ListContent) -> str:
        """Convert list to plain text."""
        if not content or not content.items:
            return ""

        self._list_depth += 1
        self._list_counters.append(0)

        lines: list[str] = []
        for item in content.items:
            if isinstance(item, LogicalElement):
                item_txt = self._element_to_txt(item)
            elif isinstance(item, ListItemContent):
                item_txt = self._list_item_to_txt(item)
            else:
                item_txt = ""
            if item_txt:
                self._list_counters[-1] += 1
                indent = "  " * (self._list_depth - 1)
                if content.ordered:
                    num = self._list_counters[-1]
                    lines.append(f"{indent}{num}. {item_txt}")
                else:
                    lines.append(f"{indent}- {item_txt}")

        self._list_counters.pop()
        self._list_depth -= 1

        return "\n".join(lines)

    def _list_item_to_txt(self, content: ListItemContent) -> str:
        """Convert list item to plain text."""
        if not content or not content.elements:
            return ""

        parts: list[str] = []
        for elem in content.elements:
            elem_txt = self._element_to_txt(elem)
            if elem_txt:
                parts.append(elem_txt)

        return " ".join(parts)

    def _quote_to_txt(self, content: QuoteContent) -> str:
        """Convert quote to plain text."""
        if not content or not content.elements:
            return ""

        lines: list[str] = []
        for elem in content.elements:
            elem_txt = self._element_to_txt(elem)
            if elem_txt:
                for line in elem_txt.split("\n"):
                    lines.append(f"> {line}")

        return "\n".join(lines)

    def _image_to_txt(self, content: ImageContent) -> str:
        """Convert image to plain text."""
        alt = content.alt or content.src or "image"
        return f"[Image: {alt}]"

    def _link_to_txt(self, content: LinkContent) -> str:
        """Convert link to plain text."""
        if not content:
            return ""

        text = self._rich_text_to_txt(content.text) if content.text else content.url
        if content.url and content.url != text:
            return f"{text} ({content.url})"
        return text

    def _math_to_txt(self, content: MathContent) -> str:
        """Convert math to plain text."""
        if not content or not content.latex:
            return ""
        return f"[{content.latex}]"

    def _table_to_txt(self, content: TableContent) -> str:
        """Convert table to ASCII-art plain text."""
        if not content or not content.rows:
            return ""

        rows_data: list[list[str]] = []
        for row in content.rows:
            row_cells: list[str] = []
            for table_cell in row.cells:
                cell_parts: list[str] = []
                for elem in table_cell.content:
                    elem_txt = self._element_to_txt(elem)
                    if elem_txt:
                        cell_parts.append(elem_txt)
                row_cells.append(" ".join(cell_parts).strip())
            rows_data.append(row_cells)

        if not rows_data:
            return ""

        num_cols = max(len(r) for r in rows_data)
        for r in rows_data:
            while len(r) < num_cols:
                r.append("")

        col_widths: list[int] = [0] * num_cols
        for row_cells in rows_data:
            for i, cell_text in enumerate(row_cells):
                col_widths[i] = max(col_widths[i], len(cell_text))

        lines: list[str] = []
        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

        for row_idx, row_cells in enumerate(rows_data):
            if row_idx == 0:
                lines.append(separator)

            cells: list[str] = []
            for i, cell_text in enumerate(row_cells):
                cells.append(f" {cell_text:<{col_widths[i]}} ")
            lines.append("|" + "|".join(cells) + "|")

            if row_idx == 0:
                lines.append("+" + "+".join("=" * (w + 2) for w in col_widths) + "+")
            else:
                lines.append(separator)

        return "\n".join(lines)

    def _footnote_to_txt(self, content: FootnoteContent) -> str:
        """Convert footnote to plain text reference."""
        if not content or not content.elements:
            return ""

        self._footnote_counter += 1
        parts: list[str] = []
        for elem in content.elements:
            elem_txt = self._element_to_txt(elem)
            if elem_txt:
                parts.append(elem_txt)

        fn_text = " ".join(parts)
        self._footnotes.append(fn_text)
        return f"[{self._footnote_counter}]"
