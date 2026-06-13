# mypy: disable-error-code="attr-defined"

from __future__ import annotations

from typing import Any

from ....models.base import ElementType
from ....models.usdm_models import (
    BookmarkContent, ColumnBreakContent, CrossReference, DataContent,
    FormFieldContent, HeadingContent, LineBreakContent, LinkContent,
    ListItemContent, LogicalElement, PageBreakContent,
    PageReferenceContent, ParagraphContent, RichTextContent,
    RichTextSpan, TOCContent,
)
from .docx_models import (
    DOCXBreak, DOCXField, DOCXParagraph, DOCXRunContent, DOCXSection,
    DOCXTab, DOCXTable, DOCXTextRun, TextDirection,
)


class DOCXContent:
    """Mixin providing DOCX paragraph/run/body/break conversion methods."""

    def _convert_body_to_logical_elements(self) -> list[LogicalElement]:
        elements = []
        assert self._docx_doc is not None
        for item in self._docx_doc.body:
            if isinstance(item, DOCXParagraph):
                elem = self._convert_paragraph(item)
                if elem:
                    elements.append(elem)
            elif isinstance(item, DOCXTable):
                elem = self._convert_table(item)
                if elem:
                    elements.append(elem)
            elif isinstance(item, DOCXSection):
                elements.append(self._convert_page_break())
        elements = self._merge_consecutive_lists(elements)
        return elements

    def _convert_paragraph(self, para: DOCXParagraph) -> LogicalElement | None:
        if not para.content.items and not para.properties.numbering_id:
            return None
        if para.is_deletion and not self.extract_track_changes:
            return None
        for item in para.content.items:
            if isinstance(item, DOCXBreak):
                if item.break_type == "page":
                    return self._convert_page_break()
                elif item.break_type == "column":
                    return self._convert_column_break()
        if para.properties.outline_level is not None:
            return self._convert_heading(para)
        if para.properties.numbering_id:
            return self._convert_list_item(para)
        return self._convert_regular_paragraph(para)

    def _convert_heading(self, para: DOCXParagraph) -> LogicalElement:
        level = para.properties.outline_level or 0
        rich_text = self._convert_run_content_to_rich_text(para.content)
        text_dir = "rtl" if para.properties.text_direction == TextDirection.RTL else "ltr"
        content = HeadingContent(level=level + 1, text=rich_text)
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.HEADING,
            content=content,
            metadata={
                "style_id": para.properties.style_id,
                "style_name": para.properties.style_name,
                "level": level + 1,
                "text_direction": text_dir,
            }
        )

    def _convert_regular_paragraph(self, para: DOCXParagraph) -> LogicalElement:
        rich_text = self._convert_run_content_to_rich_text(para.content)
        content = ParagraphContent(text=rich_text, style=para.properties.style_id)
        text_dir = "rtl" if para.properties.text_direction == TextDirection.RTL else "ltr"
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.PARAGRAPH,
            content=content,
            metadata={
                "style_id": para.properties.style_id,
                "style_name": para.properties.style_name,
                "alignment": para.properties.alignment.value if para.properties.alignment else None,
                "text_direction": text_dir,
            }
        )

    def _convert_list_item(self, para: DOCXParagraph) -> LogicalElement:
        rich_text = self._convert_run_content_to_rich_text(para.content)
        text_dir = "rtl" if para.properties.text_direction == TextDirection.RTL else "ltr"
        para_elem = LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.PARAGRAPH,
            content=ParagraphContent(text=rich_text, style=para.properties.style_id),
            metadata={"text_direction": text_dir}
        )
        content = ListItemContent(elements=[para_elem])
        num_id = para.properties.numbering_id
        level = para.properties.numbering_level or 0

        numbering_info: dict[str, Any] = {}
        override_info: dict[str, Any] = {}
        if num_id and num_id in self._docx_doc.numbering_instances:
            instance = self._docx_doc.numbering_instances[num_id]
            abs_id = instance.abstract_definition_id
            if level in instance.levels_overrides:
                override_lvl = instance.levels_overrides[level]
                override_info = {
                    "is_override": True,
                    "format": override_lvl.format,
                    "start": override_lvl.start,
                    "text_template": override_lvl.text_template,
                }
                numbering_info["override"] = override_info
            if level in instance.start_overrides:
                numbering_info["start_override"] = instance.start_overrides[level]
            if abs_id in self._docx_doc.numbering_definitions:
                definition = self._docx_doc.numbering_definitions[abs_id]
                if level in definition.levels:
                    lvl_def = definition.levels[level]
                    numbering_info.update({
                        "num_id": num_id, "level": level,
                        "format": lvl_def.format, "start": lvl_def.start,
                        "text_template": lvl_def.text_template,
                        "alignment": lvl_def.alignment.value if lvl_def.alignment else "left",
                        "indent_left": lvl_def.indent_left,
                        "indent_hanging": lvl_def.indent_hanging,
                        "font_name": lvl_def.font_name, "font_size": lvl_def.font_size,
                        "bold": lvl_def.bold, "italic": lvl_def.italic,
                        "is_legal": lvl_def.is_legal,
                    })

        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.LIST_ITEM,
            content=content,
            metadata={
                "style_id": para.properties.style_id,
                "numbering": numbering_info,
                "level": level,
                "text_direction": text_dir,
            }
        )

    def _convert_run_content_to_rich_text(self, content: Any) -> RichTextContent:
        if not isinstance(content, DOCXRunContent):
            return RichTextContent(spans=[])
        spans: list[RichTextSpan] = []
        for item in content.items:
            if isinstance(item, DOCXTextRun):
                span = self._convert_text_run_to_span(item)
                if span:
                    spans.append(span)
            elif isinstance(item, DOCXField):
                field_result = self._convert_advanced_field(item)
                if field_result:
                    if isinstance(field_result, (DataContent, TOCContent)):
                        value = getattr(field_result, 'value', None)
                        label = getattr(field_result, 'label', None)
                        text_value = str(value if value else label if label else "")
                        spans.append(RichTextSpan(text=text_value, character_style=None))
                    elif isinstance(field_result, LinkContent):
                        spans.append(RichTextSpan(
                            text=self._extract_text_from_rich_text(field_result.text),
                            character_style=None, href=field_result.url
                        ))
                    elif isinstance(field_result, PageReferenceContent):
                        spans.append(RichTextSpan(
                            text=field_result.display_text or "",
                            character_style=None, metadata={"page_ref": field_result.target_id}
                        ))
                    elif isinstance(field_result, FormFieldContent):
                        spans.append(RichTextSpan(
                            text=field_result.value or field_result.placeholder or "",
                            character_style=None
                        ))
                    elif isinstance(field_result, CrossReference):
                        spans.append(RichTextSpan(
                            text=field_result.context or "", character_style=None
                        ))
                    elif hasattr(field_result, 'value'):
                        spans.append(RichTextSpan(text=str(field_result.value), character_style=None))
                elif item.result and isinstance(item.result, str):
                    spans.append(RichTextSpan(text=item.result, character_style=None))
            elif isinstance(item, DOCXTab):
                spans.append(RichTextSpan(text="\t"))
            elif isinstance(item, DOCXBreak):
                if item.break_type == "line":
                    spans.append(RichTextSpan(text="\n"))
        return RichTextContent(spans=spans)

    def _convert_text_run_to_span(self, run: DOCXTextRun) -> RichTextSpan | None:
        if run.is_deletion and not self.extract_track_changes:
            return None
        if not run.text:
            return None
        style_props: list[str] = []
        if run.properties.bold:
            style_props.append("bold")
        if run.properties.italic:
            style_props.append("italic")
        if run.properties.underline:
            style_props.append("underline")
        char_style = "_".join(style_props) if style_props else None
        additional = getattr(run.properties, 'additional_properties', {})
        href = additional.get('hyperlink_rel_id') or additional.get('hyperlink_anchor')
        return RichTextSpan(
            text=run.text, character_style=char_style, code=False,
            background=run.properties.highlight, href=href,
            math=additional.get('math'),
        )

    def _extract_paragraph_text(self, para: DOCXParagraph) -> str:
        texts: list[str] = []
        for item in para.content.items:
            if isinstance(item, DOCXTextRun):
                if item.text:
                    texts.append(item.text)
            elif isinstance(item, DOCXField) and item.result and isinstance(item.result, str):
                texts.append(item.result)
            elif isinstance(item, DOCXTab):
                texts.append("\t")
            elif isinstance(item, DOCXBreak) and item.break_type == "line":
                texts.append("\n")
        return "".join(texts)

    def _convert_page_break(self) -> LogicalElement:
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.PAGE_BREAK,
            content=PageBreakContent(),
            metadata={"break_type": "page"}
        )

    def _convert_line_break(self, break_obj: DOCXBreak | None = None) -> LogicalElement:
        metadata = {"break_type": "line"}
        if break_obj and break_obj.clear:
            metadata["clear"] = break_obj.clear
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.LINE_BREAK,
            content=LineBreakContent(),
            metadata=metadata
        )

    def _convert_column_break(self) -> LogicalElement:
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.COLUMN_BREAK,
            content=ColumnBreakContent(),
            metadata={"break_type": "column"}
        )

    def _convert_bookmark(self, bookmark_id: str, bookmark_name: str,
                          position: int) -> LogicalElement:
        element_id = self._generate_element_id()
        self._bookmarks[bookmark_name] = element_id
        content = BookmarkContent(name=bookmark_name, text=None)
        return LogicalElement(
            element_id=element_id,
            element_type=ElementType.BOOKMARK,
            content=content,
            metadata={"bookmark_id": bookmark_id, "bookmark_name": bookmark_name, "position": position}
        )

    def _process_bookmarks_in_paragraph(self, para: DOCXParagraph) -> list[LogicalElement]:
        return []
