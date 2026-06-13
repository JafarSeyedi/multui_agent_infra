# mypy: disable-error-code="attr-defined"

from __future__ import annotations

from ....models.base import ElementType
from ....models.usdm_models import (
    CommentContent, EndnoteContent, FooterContent, FootnoteContent,
    HeaderContent, LogicalElement, Section, WatermarkContent,
)
from .docx_models import (
    DOCXComment, DOCXFootnoteEndnote, DOCXHeaderFooter, DOCXParagraph,
    DOCXTable, DOCXTextRun, DOCXWatermark,
)


class DOCXAnnotation:
    """Mixin providing DOCX annotation conversion methods."""

    def _convert_footnotes(self) -> list[LogicalElement]:
        footnotes: list[LogicalElement] = []
        assert self._docx_doc is not None
        for note_id, footnote in self._docx_doc.footnotes.items():
            footnote_elem = self._convert_single_footnote(footnote)
            if footnote_elem:
                footnotes.append(footnote_elem)
        return footnotes

    def _convert_single_footnote(self, footnote: DOCXFootnoteEndnote) -> LogicalElement | None:
        if not footnote.content:
            return None
        self._footnote_counter += 1
        note_elements = []
        reference_text = None
        for para in footnote.content:
            for item in para.content.items:
                if isinstance(item, DOCXTextRun):
                    if item.text and item.text.strip().isdigit():
                        reference_text = item.text.strip()
                        break
            elem = self._convert_paragraph(para)
            if elem:
                note_elements.append(elem)
        content = FootnoteContent(
            note_id=footnote.note_id,
            elements=note_elements,
            reference_text=reference_text or str(self._footnote_counter)
        )
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.FOOTNOTE,
            content=content,
            metadata={
                "note_id": footnote.note_id,
                "note_type": footnote.note_type,
                "reference": reference_text or str(self._footnote_counter)
            }
        )

    def _convert_endnotes(self) -> list[LogicalElement]:
        endnotes = []
        assert self._docx_doc is not None
        for note_id, endnote in self._docx_doc.endnotes.items():
            endnote_elem = self._convert_single_endnote(endnote)
            if endnote_elem:
                endnotes.append(endnote_elem)
        return endnotes

    def _convert_single_endnote(self, endnote: DOCXFootnoteEndnote) -> LogicalElement | None:
        if not endnote.content:
            return None
        self._endnote_counter += 1
        note_elements = []
        reference_text = None
        for para in endnote.content:
            for item in para.content.items:
                if isinstance(item, DOCXTextRun):
                    if item.text and item.text.strip().isdigit():
                        reference_text = item.text.strip()
                        break
            elem = self._convert_paragraph(para)
            if elem:
                note_elements.append(elem)
        content = EndnoteContent(
            note_id=endnote.note_id,
            elements=note_elements,
            reference_text=reference_text or str(self._endnote_counter)
        )
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.ENDNOTE,
            content=content,
            metadata={
                "note_id": endnote.note_id,
                "note_type": endnote.note_type,
                "reference": reference_text or str(self._endnote_counter)
            }
        )

    def _convert_comments(self) -> list[LogicalElement]:
        if not self.extract_comments:
            return []
        comments = []
        assert self._docx_doc is not None
        for comment_id, comment in self._docx_doc.comments.items():
            comment_elem = self._convert_single_comment(comment)
            if comment_elem:
                comments.append(comment_elem)
        return comments

    def _convert_single_comment(self, comment: DOCXComment) -> LogicalElement | None:
        if not comment.content:
            return None
        comment_elements: list[LogicalElement] = []
        comment_text_parts: list[str] = []
        for para in comment.content:
            elem = self._convert_paragraph(para)
            if elem:
                comment_elements.append(elem)
                text = self._extract_paragraph_text(para)
                if text:
                    comment_text_parts.append(text)
        comment_text = "\n".join(comment_text_parts)
        content = CommentContent(
            comment_id=comment.comment_id,
            author=comment.author,
            date=comment.date,
            text=comment_text,
            elements=comment_elements,
            parent_id=None, resolved=False
        )
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.COMMENT,
            content=content,
            metadata={
                "comment_id": comment.comment_id,
                "author": comment.author,
                "date": comment.date,
                "initials": comment.initials
            }
        )

    def _convert_headers(self) -> list[LogicalElement]:
        headers: list[LogicalElement] = []
        assert self._docx_doc is not None
        for rel_id, header in self._docx_doc.headers.items():
            header_elem = self._convert_single_header(rel_id, header)
            if header_elem:
                headers.append(header_elem)
        return headers

    def _convert_single_header(self, rel_id: str, header: DOCXHeaderFooter) -> LogicalElement | None:
        if not header.content and not header.watermarks:
            return None
        elements: list[LogicalElement] = []
        for item in header.content:
            if isinstance(item, DOCXParagraph):
                elem = self._convert_paragraph(item)
                if elem:
                    elements.append(elem)
            elif isinstance(item, DOCXTable):
                elem = self._convert_table(item)
                if elem:
                    elements.append(elem)
        content = HeaderContent(
            section_id=rel_id,
            page_type=header.header_footer_type,
            elements=elements
        )
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.HEADER,
            content=content,
            metadata={
                "header_footer_id": rel_id,
                "page_type": header.header_footer_type,
                "relationships": header.relationships,
            }
        )

    def _convert_footers(self) -> list[LogicalElement]:
        footers: list[LogicalElement] = []
        assert self._docx_doc is not None
        for rel_id, footer in self._docx_doc.footers.items():
            footer_elem = self._convert_single_footer(rel_id, footer)
            if footer_elem:
                footers.append(footer_elem)
        return footers

    def _convert_single_footer(self, rel_id: str, footer: DOCXHeaderFooter) -> LogicalElement | None:
        if not footer.content:
            return None
        elements: list[LogicalElement] = []
        for item in footer.content:
            if isinstance(item, DOCXParagraph):
                elem = self._convert_paragraph(item)
                if elem:
                    elements.append(elem)
            elif isinstance(item, DOCXTable):
                elem = self._convert_table(item)
                if elem:
                    elements.append(elem)
        content = FooterContent(
            section_id=rel_id,
            page_type=footer.header_footer_type,
            elements=elements
        )
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.FOOTER,
            content=content,
            metadata={
                "header_footer_id": rel_id,
                "page_type": footer.header_footer_type,
                "relationships": footer.relationships,
            }
        )

    def _link_headers_footers_to_sections(self, sections: list[Section]) -> list[Section]:
        assert self._docx_doc is not None
        for i, section in enumerate(sections):
            if i < len(self._docx_doc.sections):
                docx_section = self._docx_doc.sections[i]
                section.metadata["header_default_id"] = docx_section.header_default_id
                section.metadata["header_first_id"] = docx_section.header_first_id
                section.metadata["header_even_id"] = docx_section.header_even_id
                section.metadata["footer_default_id"] = docx_section.footer_default_id
                section.metadata["footer_first_id"] = docx_section.footer_first_id
                section.metadata["footer_even_id"] = docx_section.footer_even_id
                if docx_section.text_direction.value == 'rtl':
                    section.metadata["text_direction"] = "rtl"
                elif docx_section.text_direction.value == 'ltr':
                    section.metadata["text_direction"] = "ltr"
                if docx_section.bidi_enabled:
                    section.metadata["bidi"] = True
                section.metadata["column_count"] = docx_section.columns.count
                if docx_section.page_borders:
                    section.metadata["page_borders"] = docx_section.page_borders
        return sections

    def _convert_watermarks(self) -> list[LogicalElement]:
        watermark_elements: list[LogicalElement] = []
        assert self._docx_doc is not None
        for idx, watermark in enumerate(self._docx_doc.watermarks):
            wm_elem = self._convert_single_watermark(watermark, idx)
            if wm_elem:
                watermark_elements.append(wm_elem)
        return watermark_elements

    def _convert_single_watermark(self, watermark: DOCXWatermark, idx: int) -> LogicalElement | None:
        content = WatermarkContent(
            text=watermark.text or "",
            image_src=watermark.image_src,
            opacity=watermark.opacity,
            angle=watermark.angle,
            font=watermark.font or "Arial",
            font_size=watermark.font_size or 48.0,
            color=watermark.color or "#808080"
        )
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.WATERMARK,
            content=content,
            metadata={
                "watermark_id": watermark.watermark_id or f"wm_{idx}",
                "header_rel_id": watermark.header_rel_id,
                "layout": watermark.layout,
            }
        )
