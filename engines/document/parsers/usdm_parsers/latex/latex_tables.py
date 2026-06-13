# mypy: disable-error-code="attr-defined"

from __future__ import annotations

import re
from typing import Any

from ....models.base import ElementType
from ....models.usdm_models import (
    DocumentElement, LogicalElement, ParagraphContent, RichTextContent,
    RichTextSpan, TableCell, TableContent, TableRow,
)


class LatexTables:
    """Mixin providing LaTeX table parsing methods."""

    _tabular_rows: list[list[TableCell]]
    _tabular_columns: str
    _current_environment: str | None
    _current_table_content: TableContent | None

    def _process_tabular_row(self, line: str) -> None:
        raw = line.rstrip()
        while raw.endswith('\\\\'):
            raw = raw[:-2].rstrip()
        cells = raw.split('&')
        row_cells: list[TableCell] = []
        for cell_content in cells:
            cell_content = cell_content.strip()
            mc_m = re.match(r'\\multicolumn\{(\d+)\}\{([^}]*)\}\{(.*)', cell_content, re.DOTALL)
            if mc_m:
                ncols = int(mc_m.group(1))
                cell_text = mc_m.group(3).strip()
                row_cells.append(TableCell(
                    content=[LogicalElement(
                        element_id=self._generate_id('tc'),
                        element_type=ElementType.PARAGRAPH,
                        content=ParagraphContent(
                            text=RichTextContent(spans=[RichTextSpan(text=cell_text)])
                        ),
                    )],
                    col_span=ncols,
                ))
                continue
            mr_m = re.match(r'\\multirow\{(\d+)\}\{(.*?)\}\{(.*)', cell_content, re.DOTALL)
            if mr_m:
                nrows = int(mr_m.group(1))
                cell_text = mr_m.group(3).strip()
                row_cells.append(TableCell(
                    content=[LogicalElement(
                        element_id=self._generate_id('tc'),
                        element_type=ElementType.PARAGRAPH,
                        content=ParagraphContent(
                            text=RichTextContent(spans=[RichTextSpan(text=cell_text)])
                        ),
                    )],
                    row_span=nrows,
                ))
                continue
            row_cells.append(TableCell(
                content=[LogicalElement(
                    element_id=self._generate_id('tc'),
                    element_type=ElementType.PARAGRAPH,
                    content=ParagraphContent(
                        text=RichTextContent(spans=[RichTextSpan(text=cell_content)])
                    ),
                )],
            ))

        self._tabular_rows.append(row_cells)

    def _finalize_tabular(self) -> None:
        elem_id = self._generate_id('table')
        max_cols = 0
        for row in self._tabular_rows:
            n = sum(c.col_span for c in row)
            if n > max_cols:
                max_cols = n

        rows: list[TableRow] = []
        for row_cells in self._tabular_rows:
            rows.append(TableRow(cells=row_cells))

        table_content = TableContent(
            rows=rows,
            grid=list(range(max_cols)) if max_cols > 0 else None,
            metadata={
                'column_specification': self._tabular_columns,
                'env': self._current_environment or 'tabular',
            },
        )
        self._current_table_content = table_content
        self._add_logical(LogicalElement(
            element_id=elem_id,
            element_type=ElementType.TABLE,
            content=table_content,
            metadata={'column_specification': self._tabular_columns},
        ))
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.TABLE,
        )
        self._add_element(doc_elem)
        self._tabular_rows = []
        self._tabular_columns = ''

    def _resolve_image_path(self, img_path: str) -> str:
        if not self._graphicspath:
            return img_path
        return img_path
