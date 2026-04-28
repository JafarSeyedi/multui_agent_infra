# engines/document/parsers/spreadsheet_parser/fixed_width_parser.py
"""
Parser for fixed‑width (fixed‑column) text files.
Column widths are passed via ParseOptions.custom["column_widths"].
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, Dict, Any, List

from engines.document.parsers.spreadsheet_parser.base_spreadsheet_parser import BaseSpreadsheetParser
from engines.document.parsers.base import ParseOptions
from engines.document.models.esdm_models import Workbook, Worksheet, Row, Cell


class FixedWidthParser(BaseSpreadsheetParser):
    """Parser for fixed‑width text files (e.g., .prn, .txt with fixed columns)."""

    name = "fixed_width"
    supported_extensions = (".prn", ".txt")  # typical extensions

    async def _parse_to_workbook(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> Workbook:
        # --- Configuration -------------------------------------------------------
        encoding = options.encoding or "utf-8"
        skip_rows = max(0, options.skip_rows)
        header_row_idx = options.header_row  # 0‑based after skipping

        # Column widths must be supplied in the custom options.
        # Example: options.custom["column_widths"] = [10, 15, 20]
        column_widths: List[int] = []
        custom = options.custom or {}
        if "column_widths" in custom:
            # Accept a list of ints
            column_widths = [int(w) for w in custom["column_widths"]]
        if not column_widths:
            raise ValueError(
                "FixedWidthParser requires 'column_widths' in options.custom "
                "(e.g., [10, 20, 30])."
            )

        # --- Decode and split lines ----------------------------------------------
        text = data.decode(encoding, errors="replace")
        all_lines = text.splitlines()

        # Apply skip rows
        lines_after_skip = all_lines[skip_rows:]

        # --- Header handling -----------------------------------------------------
        has_header = header_row_idx is not None and header_row_idx >= 0
        column_names: List[str] = []
        data_start_idx = 0

        if has_header and header_row_idx < len(lines_after_skip):
            header_line = lines_after_skip[header_row_idx]
            column_names = self._slice_line(header_line, column_widths)
            data_start_idx = header_row_idx + 1
        else:
            has_header = False

        data_lines = lines_after_skip[data_start_idx:]

        # --- Build worksheet -----------------------------------------------------
        sheet_name = self._get_sheet_name(source_name, options)
        ws = Worksheet(name=sheet_name)

        # Header row
        current_row = 1
        if has_header:
            r = Row(index=current_row)
            for col_idx, value in enumerate(column_names, start=1):
                r.cells[col_idx] = Cell(row=current_row, col=col_idx, value=value)
            ws.rows[current_row] = r
            current_row += 1

        # Data rows
        for row_idx, line in enumerate(data_lines, start=current_row):
            if not line:
                continue   # skip completely empty lines
            r = Row(index=row_idx)
            fields = self._slice_line(line, column_widths)
            for col_idx, value in enumerate(fields, start=1):
                # Store even empty fields
                r.cells[col_idx] = Cell(row=row_idx, col=col_idx, value=value)
            ws.rows[row_idx] = r

        # Update dimensions
        if ws.rows:
            ws.dimensions.min_row = min(ws.rows.keys())
            ws.dimensions.max_row = max(ws.rows.keys())
            ws.dimensions.min_col = 1
            ws.dimensions.max_col = len(column_widths)

        wb = Workbook()
        wb.sheets.append(ws)
        return wb

    @staticmethod
    def _slice_line(line: str, widths: List[int]) -> List[str]:
        """
        Slice a line into fields of given widths, stripping trailing spaces.
        If the line is shorter than total widths, remaining fields are empty.
        """
        fields = []
        start = 0
        for w in widths:
            end = start + w
            field = line[start:end] if start < len(line) else ""
            fields.append(field.rstrip())
            start = end
        return fields

    def _get_sheet_name(self, source_name: str, options: ParseOptions) -> str:
        if options.sheet_names and options.sheet_names:
            return options.sheet_names[0]
        base = Path(source_name).stem
        return base if base else "Sheet1"
    
    
# usage:
# options = ParseOptions(
#     custom={"column_widths": [10, 15, 12, 8]},
#     header_row=0,      # if first row contains column names
#     skip_rows=0,
#     encoding="utf-8"
# )
# parser = FixedWidthParser()
# doc = await parser.parse_path("data.prn", "doc-1", options=options)    
