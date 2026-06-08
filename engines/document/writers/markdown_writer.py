"""
Markdown writer for converting USDM model to .md file
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ..models.base import BaseDocument
from ..models.exceptions import DocumentWriteError
from ..models.usdm_models import CodeContent
from ..models.usdm_models import ElementType
from ..models.usdm_models import HeadingContent
from ..models.usdm_models import ImageContent
from ..models.usdm_models import LinkContent
from ..models.usdm_models import ListContent
from ..models.usdm_models import LogicalElement
from ..models.usdm_models import ParagraphContent
from ..models.usdm_models import QuoteContent
from ..models.usdm_models import RichTextContent
from ..models.usdm_models import TableCell
from ..models.usdm_models import TableContent
from ..models.usdm_models import USDMDocument
from .base import BaseDocumentWriter
from .base import WriteOptions


class MarkdownWriter(BaseDocumentWriter):
    """Markdown writer"""

    def __init__(self, options: WriteOptions | None = None):
        super().__init__(options)
        self.options = options or WriteOptions()

    async def write(self, document: BaseDocument) -> bytes:
        """
        Convert document to Markdown (bytes)
        """
        assert self.options is not None, "WriteOptions not initialized"
        if not isinstance(document, USDMDocument):
            raise DocumentWriteError("Document must be of type USDMDocument")

        try:
            markdown_text = self._convert_usdm_to_markdown(document)
            return markdown_text.encode(self.options.encoding)

        except Exception as e:
            raise DocumentWriteError(f"Error writing Markdown: {e}")

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """
        Write as stream
        """
        try:
            data = await self.write(document)
            yield data

        except Exception as e:
            raise DocumentWriteError(f"Error writing Markdown stream: {e}")

    async def write_to_file(self, document: BaseDocument, target: Path,
                           options: dict[str, Any] | None = None) -> None:
        """
        Write document to file
        """
        try:
            data = await self.write(document)
            target.write_bytes(data)

        except Exception as e:
            raise DocumentWriteError(f"Error writing Markdown file: {e}")

    def get_supported_media_types(self) -> list[str]:
        """Get supported media types"""
        return ["text/markdown"]

    def get_supported_extensions(self) -> list[str]:
        """Get supported extensions"""
        return [".md", ".markdown"]

    def _convert_usdm_to_markdown(self, document: USDMDocument) -> str:
        """Convert USDM to Markdown text"""
        lines = []

        # Add title
        if document.title:
            lines.append(f"# {document.title}\n")

        # Process sections
        for section in document.sections:
            if section.title:
                # Add section title
                heading_level = section.title.level
                heading_text = self._rich_text_to_plain(section.title.text)
                heading_prefix = "#" * min(heading_level, 6)
                lines.append(f"{heading_prefix} {heading_text}\n")

            # Process section elements
            for elem in section.elements:
                logical_elem = self._find_logical_element(document, elem.element_id)
                if logical_elem:
                    lines.append(self._element_to_markdown(logical_elem))

        # Process standalone elements
        for elem in document.elements:
            if not any(elem.element_id in [se.element_id for se in s.elements] for s in document.sections):
                logical_elem = self._find_logical_element(document, elem.element_id)
                if logical_elem:
                    lines.append(self._element_to_markdown(logical_elem))

        return "\n".join(lines)

    def _find_logical_element(self, document: USDMDocument, element_id: str) -> LogicalElement | None:
        """Find logical element by ID"""
        for elem in document.logical_elements:
            if elem.element_id == element_id:
                return elem
        return None

    def _element_to_markdown(self, element: LogicalElement) -> str:
        """Convert logical element to Markdown"""
        content = element.content

        if element.element_type == ElementType.PARAGRAPH and isinstance(content, ParagraphContent):
            return self._paragraph_to_markdown(content) + "\n"

        elif element.element_type == ElementType.HEADING and isinstance(content, HeadingContent):
            return self._heading_to_markdown(content) + "\n"

        elif element.element_type == ElementType.CODE and isinstance(content, CodeContent):
            return self._code_to_markdown(content) + "\n"

        elif element.element_type == ElementType.LIST and isinstance(content, ListContent):
            return self._list_to_markdown(content) + "\n"

        elif element.element_type == ElementType.QUOTE and isinstance(content, QuoteContent):
            return self._quote_to_markdown(content) + "\n"

        elif element.element_type == ElementType.IMAGE and isinstance(content, ImageContent):
            return self._image_to_markdown(content) + "\n"

        elif element.element_type == ElementType.LINK and isinstance(content, LinkContent):
            return self._link_to_markdown(content) + "\n"

        elif element.element_type == ElementType.TABLE and isinstance(content, TableContent):
            return self._table_to_markdown(content) + "\n"

        return ""

    def _rich_text_to_plain(self, rich_text: RichTextContent) -> str:
        """Convert RichText to plain text with Markdown formatting"""
        result = []
        for span in rich_text.spans:
            text = span.text

            # Apply formatting
            if span.code:
                text = f"`{text}`"
            elif span.math:
                text = f"$${span.math}$$"

            # Apply text styles
            if span.character_style:
                if "bold" in span.character_style.lower():
                    text = f"**{text}**"
                elif "italic" in span.character_style.lower():
                    text = f"*{text}*"
                elif "underline" in span.character_style.lower():
                    text = f"<u>{text}</u>"

            # Add link
            if span.href:
                text = f"[{text}]({span.href})"

            result.append(text)

        return "".join(result)

    def _paragraph_to_markdown(self, content: ParagraphContent) -> str:
        """Convert paragraph to Markdown"""
        return self._rich_text_to_plain(content.text)

    def _heading_to_markdown(self, content: HeadingContent) -> str:
        """Convert heading to Markdown"""
        heading_text = self._rich_text_to_plain(content.text)
        heading_prefix = "#" * min(content.level, 6)
        return f"{heading_prefix} {heading_text}"

    def _code_to_markdown(self, content: CodeContent) -> str:
        """Convert code to Markdown"""
        assert self.options is not None, "WriteOptions not initialized"
        language = content.language or ""
        if self.options.code_block_style == "~~~":
            return f"~~~{language}\n{content.code}\n~~~"
        else:
            return f"```{language}\n{content.code}\n```"

    def _list_to_markdown(self, content: ListContent) -> str:
        """Convert list to Markdown"""
        assert self.options is not None, "WriteOptions not initialized"
        lines = []
        bullet = self.options.bullet_style

        for i, item in enumerate(content.items):
            prefix = f"{i + 1}. " if content.ordered else f"{bullet} "

            # Process list items
            for sub_elem in item.elements:
                if isinstance(sub_elem, LogicalElement):
                    if sub_elem.element_type == ElementType.PARAGRAPH:
                        para_content = sub_elem.content
                        if isinstance(para_content, ParagraphContent):
                            text = self._rich_text_to_plain(para_content.text)
                            lines.append(f"{prefix}{text}")
                    else:
                        # For other element types
                        elem_md = self._element_to_markdown(sub_elem).strip()
                        lines.append(f"{prefix}{elem_md}")

            # Add blank line between items
            lines.append("")

        return "\n".join(lines)

    def _quote_to_markdown(self, content: QuoteContent) -> str:
        """Convert quote to Markdown"""
        lines = []
        for elem in content.elements:
            if isinstance(elem, LogicalElement):
                elem_md = self._element_to_markdown(elem).strip()
                # Add > to beginning of each line
                for line in elem_md.split('\n'):
                    lines.append(f"> {line}")

        return "\n".join(lines)

    def _image_to_markdown(self, content: ImageContent) -> str:
        """Convert image to Markdown"""
        alt = content.alt or ""
        return f"![{alt}]({content.src})"

    def _link_to_markdown(self, content: LinkContent) -> str:
        """Convert link to Markdown"""
        link_text = self._rich_text_to_plain(content.text)
        return f"[{link_text}]({content.url})"

    def _table_to_markdown(self, content: TableContent) -> str:
        """Convert table to Markdown"""
        if not content.rows:
            return ""

        lines = []

        # Header row (assumed)
        if content.rows:
            header_cells = []
            for cell in content.rows[0].cells:
                cell_text = self._cell_content_to_text(cell)
                header_cells.append(cell_text)

            lines.append("| " + " | ".join(header_cells) + " |")
            lines.append("|" + "|".join(["---"] * len(header_cells)) + "|")

        # Data rows
        for row in content.rows[1:] if len(content.rows) > 1 else content.rows:
            row_cells = []
            for cell in row.cells:
                cell_text = self._cell_content_to_text(cell)
                row_cells.append(cell_text)

            lines.append("| " + " | ".join(row_cells) + " |")

        return "\n".join(lines)

    def _cell_content_to_text(self, cell: TableCell) -> str:
        """Convert table cell content to text"""
        texts = []
        for elem in cell.content:
            if isinstance(elem, LogicalElement):
                if elem.element_type == ElementType.PARAGRAPH:
                    para_content = elem.content
                    if isinstance(para_content, ParagraphContent):
                        texts.append(self._rich_text_to_plain(para_content.text))

        return " ".join(texts)
