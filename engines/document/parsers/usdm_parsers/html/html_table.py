# mypy: disable-error-code="attr-defined"

from __future__ import annotations

from typing import Any

from ....models.base import ElementType
from ....models.usdm_models import (
    LogicalElement, ParagraphContent, RichTextContent, TableCell,
    TableContent, TableRow,
)
from .html_parser_utils import safe_int


class HTMLTableParser:
    """Mixin providing HTML table parsing methods."""

    current_table: dict[str, Any] | None
    table_stack: list[dict[str, Any]]
    current_row: dict[str, Any] | None
    current_cell: dict[str, Any] | None

    def _handle_table_start(self, attrs: dict[str, str]) -> None:
        table_info: dict[str, Any] = {
            "type": ElementType.TABLE,
            "attrs": attrs,
            "rows": [],
            "current_row": None,
            "current_cell": None,
            "has_header": False,
            "caption": None,
        }
        self.table_stack.append(table_info)
        self.current_table = table_info

    def _handle_table_row_group_start(self, group_tag: str, attrs: dict[str, str]) -> None:
        if self.current_table:
            self.current_table["_current_group"] = group_tag

    def _handle_table_row_group_end(self, group_tag: str) -> None:
        if self.current_table:
            self.current_table.pop("_current_group", None)

    def _handle_table_row_start(self, attrs: dict[str, str]) -> None:
        if self.current_table:
            group = self.current_table.get("_current_group", "tbody")
            is_header = group == "thead"
            self.current_table["current_row"] = {
                "cells": [],
                "is_header": is_header,
                "attrs": attrs,
            }
            if is_header:
                self.current_table["has_header"] = True

    def _handle_table_row_end(self) -> None:
        if self.current_table and self.current_table["current_row"]:
            row_info = self.current_table["current_row"]
            if row_info["cells"]:
                table_row = TableRow(
                    cells=row_info["cells"],
                    is_header=row_info["is_header"],
                    metadata=row_info.get("attrs", {}),
                )
                self.current_table["rows"].append(table_row)
            self.current_table["current_row"] = None

    def _handle_table_cell_start(self, tag: str, attrs: dict[str, str]) -> None:
        if self.current_table and self.current_table["current_row"]:
            is_header = tag == "th"
            self.current_table["current_cell"] = {
                "elements": [],
                "is_header": is_header,
                "attrs": attrs,
                "col_span": safe_int(attrs.get("colspan")),
                "row_span": safe_int(attrs.get("rowspan")),
                "text_parts": [],
            }

    def _handle_table_cell_end(self) -> None:
        if (self.current_table and self.current_table["current_row"] and
                self.current_table["current_cell"]):
            cell_info = self.current_table["current_cell"]
            cell_text = "".join(cell_info.get("text_parts", [])).strip()
            cell_elements: list[LogicalElement] = []
            if cell_text:
                para = ParagraphContent(
                    text=RichTextContent(spans=[self._create_rich_text_span(cell_text)]),
                )
                cell_elements.append(
                    self._create_logical_element(ElementType.PARAGRAPH, para),
                )
            table_cell = TableCell(
                content=cell_elements,
                is_header=cell_info["is_header"],
                col_span=cell_info["col_span"],
                row_span=cell_info["row_span"],
                metadata=cell_info.get("attrs", {}),
            )
            self.current_table["current_row"]["cells"].append(table_cell)
            self.current_table["current_cell"] = None

    def _handle_table_end(self) -> None:
        if self.table_stack:
            table_info = self.table_stack.pop()
            if table_info["rows"]:
                content = TableContent(
                    rows=table_info["rows"],
                    caption=table_info.get("caption"),
                    metadata={
                        "has_header": table_info["has_header"],
                        **table_info.get("attrs", {}),
                    },
                )
                element = self._create_logical_element(
                    ElementType.TABLE,
                    content,
                    table_info.get("attrs", {}),
                )
                self._add_element(element)
            if self.table_stack:
                self.current_table = self.table_stack[-1]
            else:
                self.current_table = None
