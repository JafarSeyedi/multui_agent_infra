# mypy: disable-error-code="attr-defined"

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime
from typing import Any

from ....models.base import BinaryPayload
from ....models.base import CompressionMethod
from ....models.base import ElementType
from ....models.exceptions import DocumentParseError
from ....models.usdm_models import (
    FootnoteContent, HeadingContent, ListItemContent, LogicalElement,
    Page, ParagraphContent, QuoteContent, RichTextContent, RichTextSpan,
)
from .docx_models import DOCXParagraph


class DOCXParserUtils:
    """Mixin providing DOCX parser utility methods."""

    def _generate_document_id(self, source_name: str) -> str:
        """Generate a unique document ID."""
        if self._docx_doc:
            content = str(self._docx_doc.core_properties.__dict__)
            hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
            return f"docx_{hash_val}"

        return f"docx_{uuid.uuid4().hex[:16]}"


    def _get_document_title(self) -> str:
        """Get document title from metadata."""
        assert self._docx_doc is not None, "Document not extracted"
        if self._docx_doc.core_properties.title:
            return self._docx_doc.core_properties.title

        # Try to extract from first heading
        for elem in self._docx_doc.body:
            if isinstance(elem, DOCXParagraph):
                if elem.properties.outline_level == 0:
                    text = self._extract_paragraph_text(elem)
                    if text:
                        return text[:100]

        return "Untitled Document"


    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse ISO date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None



    def _extract_raw_binary(self) -> BinaryPayload | None:
        """Extract raw DOCX as binary payload."""
        return None


    def _extract_raw_text(self, logical_elements: list[LogicalElement]) -> str:
        """Extract plain text from logical elements."""
        texts = []

        for elem in logical_elements:
            text = self._extract_text_from_logical_element(elem)
            if text:
                texts.append(text)

        return "\n\n".join(texts)


    def _extract_text_from_logical_element(self, elem: LogicalElement) -> str:
        """Recursively extract text from a logical element."""
        if elem.element_type == ElementType.PARAGRAPH:
            if isinstance(elem.content, ParagraphContent):
                return self._extract_text_from_rich_text(elem.content.text)
        elif elem.element_type == ElementType.HEADING:
            if isinstance(elem.content, HeadingContent):
                return self._extract_text_from_rich_text(elem.content.text)
        elif elem.element_type == ElementType.LIST_ITEM:
            if isinstance(elem.content, ListItemContent):
                texts = []
                for sub_elem in elem.content.elements:
                    text = self._extract_text_from_logical_element(sub_elem)
                    if text:
                        texts.append(text)
                return " ".join(texts)
        elif elem.element_type == ElementType.QUOTE:
            if isinstance(elem.content, QuoteContent):
                texts = []
                for sub_elem in elem.content.elements:
                    text = self._extract_text_from_logical_element(sub_elem)
                    if text:
                        texts.append(text)
                return " ".join(texts)
        elif elem.element_type == ElementType.FOOTNOTE:
            if isinstance(elem.content, FootnoteContent):
                texts = []
                for sub_elem in elem.content.elements:
                    text = self._extract_text_from_logical_element(sub_elem)
                    if text:
                        texts.append(text)
                return " ".join(texts)

        return ""


    def _extract_text_from_rich_text(self, rich_text: RichTextContent) -> str:
        """Extract plain text from rich text content."""
        return "".join(span.text for span in rich_text.spans)

    # ============================================================
    # STYLE CONVERSION
    # ============================================================


    def _build_metadata(self, source_name: str) -> dict[str, Any]:
        """Build metadata dictionary for USDM document."""
        if self._docx_doc is None:
            raise DocumentParseError("No document extracted")
        metadata: dict[str, Any] = {
            "source": source_name,
            "parser": "DOCXParser",
            "parser_version": "1.0",
        }

        cp = self._docx_doc.core_properties
        if cp.creator:
            metadata["author"] = cp.creator
        if cp.subject:
            metadata["subject"] = cp.subject
        if cp.keywords:
            metadata["keywords"] = ", ".join(cp.keywords) if isinstance(cp.keywords, list) else cp.keywords
        if cp.description:
            metadata["description"] = cp.description
        if cp.category:
            metadata["category"] = cp.category

        ep = self._docx_doc.extended_properties
        if ep.pages:
            metadata["page_count"] = str(ep.pages)
        if ep.words:
            metadata["word_count"] = str(ep.words)
        if ep.characters:
            metadata["character_count"] = str(ep.characters)
        if ep.paragraphs:
            metadata["paragraph_count"] = str(ep.paragraphs)
        if ep.company:
            metadata["company"] = ep.company
        if ep.manager:
            metadata["manager"] = ep.manager

        if self._docx_doc.custom_properties.properties:
            metadata["custom"] = self._docx_doc.custom_properties.properties

        return metadata


    def _convert_emu_to_pixels(self, emu: float, dpi: int = 96) -> float:
        """
        Convert EMU (English Metric Units) to pixels.
        
        Args:
            emu: Value in EMU
            dpi: Dots per inch (default 96)
            
        Returns:
            Value in pixels
        """
        # 1 EMU = 1/914400 inch
        inches = emu / 914400.0
        return inches * dpi



    def _convert_plain_text_to_rich_text(self, text: str) -> RichTextContent:
        """
        Convert plain text to RichTextContent.
        
        Args:
            text: Plain text string
            
        Returns:
            RichTextContent object
        """
        return RichTextContent(
            spans=[RichTextSpan(text=text)]
        )


    def _resolve_theme_color(
        self,
        color_value: str | None,
        theme_color: str | None = None,
        theme_tint: float | None = None,
        theme_shade: float | None = None
    ) -> str | None:
        from .docx_color_utils import resolve_theme_color as _rtc
        return _rtc(self._docx_doc, color_value, theme_color, theme_tint, theme_shade)



    def _normalize_color_value(self, color: str) -> str:
        from .docx_color_utils import normalize_color_value
        return normalize_color_value(color)


    def _get_system_color(self, system_color: str) -> str:
        from .docx_color_utils import get_system_color
        return get_system_color(system_color)


    def _apply_tint(self, hex_color: str, tint: float) -> str:
        from .docx_color_utils import apply_tint
        return apply_tint(hex_color, tint)


    def _apply_shade(self, hex_color: str, shade: float) -> str:
        from .docx_color_utils import apply_shade
        return apply_shade(hex_color, shade)



    def _extract_theme_colors_from_document(self) -> dict[str, dict[str, str]]:
        from .docx_color_utils import extract_theme_colors_from_document
        return extract_theme_colors_from_document(self._docx_doc)

