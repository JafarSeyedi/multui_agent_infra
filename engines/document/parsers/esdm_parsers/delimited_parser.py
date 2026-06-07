# engines/document/parsers/esdm_parsers/delimited_parser.py
"""
Parsers for CSV and TSV files.
Produces an ESDM Workbook with a single Worksheet.
"""
from __future__ import annotations

import csv
import io
import chardet
from pathlib import Path
from typing import Any
from typing import cast

from ...models.esdm_models import Cell
from ...models.esdm_models import Row
from ...models.esdm_models import Workbook
from ...models.esdm_models import Worksheet
from ..base import ParseOptions
from .base_spreadsheet_parser import BaseSpreadsheetParser


class DelimitedParser(BaseSpreadsheetParser):
    """
    Base parser for character-delimited text files.

    Subclasses set `delimiter` and `supported_extensions`.
    """

    delimiter: str = ","

    async def _parse_to_workbook(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> Workbook:
        # Detect encoding if not specified
        if options.encoding:
            encoding = options.encoding
        else:
            # Use chardet to detect encoding
            detection = chardet.detect(data)
            encoding = detection['encoding'] or 'utf-8'
            # Fallback to utf-8 if confidence is too low
            if detection['confidence'] < 0.5:
                encoding = 'utf-8'
        
        try:
            text = data.decode(encoding, errors="strict")
        except UnicodeDecodeError:
            # Fallback to replace errors if strict decoding fails
            text = data.decode(encoding, errors="replace")

        # Configure CSV reader based on options
        quoting_val: int = csv.QUOTE_MINIMAL
        if options.custom and 'quoting' in options.custom:
            quoting_map: dict[str, int] = {
                'MINIMAL': csv.QUOTE_MINIMAL,
                'ALL': csv.QUOTE_ALL,
                'NONNUMERIC': csv.QUOTE_NONNUMERIC,
                'NONE': csv.QUOTE_NONE
            }
            quoting_str = str(options.custom['quoting']).upper()
            quoting_val = quoting_map.get(quoting_str, csv.QUOTE_MINIMAL)
        quoting = cast(Any, quoting_val)

        # Read all rows with csv module
        reader = csv.reader(
            io.StringIO(text), 
            delimiter=self.delimiter, 
            quotechar='"',
            quoting=quoting
        )
        all_rows = list(reader)

        # Apply skip_rows
        skip = max(0, options.skip_rows)
        rows_after_skip = all_rows[skip:]

        # Determine header row (0‑based index relative to rows_after_skip)
        header_row_idx = options.header_row
        has_header = header_row_idx is not None and header_row_idx >= 0

        column_names: list[str] = []
        data_start_idx = 0

        if has_header and header_row_idx < len(rows_after_skip):
            column_names = [str(cell) if cell is not None else "" for cell in rows_after_skip[header_row_idx]]
            data_start_idx = header_row_idx + 1
        else:
            has_header = False

        # Data rows
        data_rows = rows_after_skip[data_start_idx:]

        # Max columns across header + data
        max_col = len(column_names) if column_names else 0
        for row in data_rows:
            max_col = max(max_col, len(row))

        # Build worksheet
        sheet_name = self._get_sheet_name(source_name, options)
        ws = Worksheet(name=sheet_name)

        # Write header row as row 1 (if present)
        current_row = 1
        if has_header:
            r = Row(index=current_row)
            for col_idx, value in enumerate(column_names, start=1):
                r.cells[col_idx] = Cell(row=current_row, col=col_idx, value=value)
            ws.rows[current_row] = r
            current_row += 1

        # Write data rows
        for row_idx, row_data in enumerate(data_rows, start=current_row):
            r = Row(index=row_idx)
            for col_idx, value in enumerate(row_data, start=1):
                # Keep empty strings, convert None to empty string for consistency
                cell_value = "" if value is None else str(value)
                r.cells[col_idx] = Cell(row=row_idx, col=col_idx, value=cell_value)
            ws.rows[row_idx] = r

        # Update dimensions based on actual content
        if ws.rows:
            ws.dimensions.min_row = min(ws.rows.keys())
            ws.dimensions.max_row = max(ws.rows.keys())
            ws.dimensions.min_col = 1
            ws.dimensions.max_col = max_col

        wb = Workbook()
        wb.sheets.append(ws)
        return wb

    def _get_sheet_name(self, source_name: str, options: ParseOptions) -> str:
        """Pick sheet name from options or derive from file name."""
        if options.sheet_names and len(options.sheet_names) > 0:
            return options.sheet_names[0]
        base = Path(source_name).stem
        return base if base else "Sheet1"


class CSVParser(DelimitedParser):
    """Parser for CSV files."""
    name = "csv"
    delimiter = ","
    supported_extensions = (".csv",)


class TSVParser(DelimitedParser):
    """Parser for TSV files."""
    name = "tsv"
    delimiter = "\t"
    supported_extensions = (".tsv",)
