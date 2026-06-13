# mypy: disable-error-code="attr-defined"

from __future__ import annotations

from typing import Any
from typing import cast

from ....models.base import ElementType
from ....models.usdm_models import (
    AnnotationObject, DocumentElement, HeadingContent, ImageObject,
    ListContent, ListItemContent, LogicalElement, Page,
    ParagraphContent, QuoteContent, RichTextContent, RichTextSpan,
    Section, TableCell, TableContent, TableRow, TextRun, VectorPath,
)
from .docx_models import DOCXParagraph, DOCXSection, DOCXTable, TextDirection, VerticalAlignment


class DOCXParserSections:
    """Mixin providing DOCX parser sections/pages/tables methods."""

    def _convert_table(self, table: DOCXTable) -> LogicalElement | None:
        rows: list[TableRow] = []
        for row in table.rows:
            cells: list[TableCell] = []
            for cell in row.cells:
                cell_elements: list[LogicalElement] = []
                for item in cell.content:
                    if isinstance(item, DOCXParagraph):
                        para: DOCXParagraph = item
                        elem = self._convert_paragraph(para)
                        if elem:
                            cell_elements.append(elem)
                    elif isinstance(item, DOCXTable):
                        sub_table: DOCXTable = item
                        elem = self._convert_table(sub_table)
                        if elem:
                            cell_elements.append(elem)
                cell_md: dict[str, Any] = {}
                if cell.properties.text_direction == TextDirection.RTL:
                    cell_md["text_direction"] = "rtl"
                if cell.properties.vertical_alignment != VerticalAlignment.TOP:
                    cell_md["vertical_alignment"] = cell.properties.vertical_alignment.value
                cells.append(TableCell(content=cell_elements, metadata=cell_md if cell_md else None))
            rows.append(TableRow(cells=cells))
        content = TableContent(rows=rows)
        table_md: dict[str, Any] = {"style_id": table.properties.style_id if table.properties else None}
        rtl_md = self._apply_rtl_to_table(table)
        table_md.update(rtl_md)
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.TABLE,
            content=content,
            metadata=table_md
        )


    def _merge_consecutive_lists(self, elements: list[LogicalElement]) -> list[LogicalElement]:
        merged: list[LogicalElement] = []
        i = 0
        while i < len(elements):
            elem = elements[i]
            if elem.element_type == ElementType.LIST_ITEM:
                # Start a potential list group
                list_items: list[ListItemContent] = []
                # Determine if this is an ordered list from the first item's metadata
                numbering = elem.metadata.get('numbering', {})
                is_ordered = not numbering.get('format', '').startswith('bullet') if numbering else False

                while i < len(elements) and elements[i].element_type == ElementType.LIST_ITEM:
                    item = elements[i]
                    if isinstance(item.content, ListItemContent):
                        list_items.append(item.content)
                    i += 1

                # Create a single ListContent element
                list_elem = LogicalElement(
                    element_id=self._generate_element_id(),
                    element_type=ElementType.LIST,
                    content=ListContent(ordered=is_ordered, items=list_items),
                    metadata={"ordered": is_ordered}
                )
                merged.append(list_elem)
            else:
                merged.append(elem)
                i += 1

        return merged

    # ============================================================
    # PUBLIC API
    # ============================================================


    def _convert_sections(self, logical_elements: list[LogicalElement]) -> list[Section]:
        sections: list[Section] = []
        current_section_elements: list[DocumentElement | LogicalElement] = []
        current_title: HeadingContent | None = None

        for elem in logical_elements:
            # Start new section on certain conditions
            if elem.element_type == ElementType.HEADING and getattr(elem.metadata, 'level', 0) == 1:
                # Save previous section if any
                if current_section_elements:
                    sections.append(Section(title=current_title, elements=current_section_elements))
                    current_section_elements = []
                current_title = cast(HeadingContent, elem.content) if isinstance(elem.content, HeadingContent) else None
            elif elem.element_type in (ElementType.PAGE_BREAK, ElementType.SECTION_BREAK):
                if current_section_elements:
                    sections.append(Section(title=current_title, elements=current_section_elements))
                    current_section_elements = []
                current_title = None
            else:
                current_section_elements.append(DocumentElement(element_id=elem.element_id,element_type=elem.element_type,metadata=elem.metadata))

        # Final section
        if current_section_elements:
            sections.append(Section(title=current_title, elements=current_section_elements))

        return sections


    def _build_pages(self, logical_elements: list[LogicalElement]) -> list[Page]:
        pages: list[Page] = []
        current_page_objects: list[TextRun | ImageObject | VectorPath | AnnotationObject] = []
        # For now, we only split by page breaks; TextRun objects could be created elsewhere.
        # This is a simple placeholder that groups elements per page.

        page_number = 0
        for elem in logical_elements:
            if elem.element_type == ElementType.PAGE_BREAK:
                pages.append(Page(page_number=page_number, width=0, height=0, elements=current_page_objects))
                page_number += 1
                current_page_objects = []
            else:
                # In a real PDF‑like output, you'd create TextRun etc. here.
                pass

        # Last page
        if current_page_objects or page_number == 0:   # at least one page even if no breaks
            pages.append(Page(page_number=page_number, width=0, height=0, elements=current_page_objects))

        return pages


    def _flatten_logical_elements(self, logical_elements: list[LogicalElement]) -> list[DocumentElement]:
        flat: list[DocumentElement] = []

        def flatten(elem: LogicalElement):
            flat.append(DocumentElement(
                element_id=elem.element_id,
                element_type=elem.element_type,
                metadata=elem.metadata
            ))
            # Recurse into nested elements if content contains a list of LogicalElements
            content = elem.content
            if isinstance(content, ListItemContent):
                for sub in content.elements:
                    flatten(sub)
            elif isinstance(content, QuoteContent):
                for sub in content.elements:
                    flatten(sub)
            # add other containers (FootnoteContent, EndnoteContent) if needed

        for le in logical_elements:
            flatten(le)

        return flat


