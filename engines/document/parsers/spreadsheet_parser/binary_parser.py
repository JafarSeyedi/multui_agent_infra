# engines/document/parsers/spreadsheet_parser/binary_parser.py
"""
Parsers for binary columnar formats: Parquet, Arrow IPC (Feather v2), Feather.
Produces an ESDM Workbook with a single Worksheet (or one per sheet if partitioned).
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.feather as pf
import pyarrow.parquet as pq

from ...models.esdm_models import Cell
from ...models.esdm_models import Row
from ...models.esdm_models import Workbook
from ...models.esdm_models import Worksheet
from ..base import ParseOptions
from ..spreadsheet_parser.base_spreadsheet_parser import BaseSpreadsheetParser


class ColumnarBinaryParser(BaseSpreadsheetParser):
    """
    Base parser for columnar binary formats.
    Subclasses override _read_table().
    """

    async def _parse_to_workbook(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> Workbook:
        table = self._read_table(data, options)

        # Determine sheet name
        sheet_name = self._get_sheet_name(source_name, options)
        ws = Worksheet(name=sheet_name)

        # Column names
        column_names = table.column_names

        # Header row (row 1)
        header_row = Row(index=1)
        for col_idx, name in enumerate(column_names, start=1):
            header_row.cells[col_idx] = Cell(row=1, col=col_idx, value=name)
        ws.rows[1] = header_row

        # Data rows
        for row_idx in range(table.num_rows):
            r = Row(index=row_idx + 2)
            for col_idx in range(table.num_columns):
                val = table.column(col_idx)[row_idx].as_py()
                # Convert complex Arrow scalars to a string representation if needed
                cell_value = self._convert_arrow_value(val)
                r.cells[col_idx + 1] = Cell(row=row_idx + 2, col=col_idx + 1, value=cell_value)
            ws.rows[row_idx + 2] = r

        # Update dimensions
        if ws.rows:
            ws.dimensions.min_row = 1  # header always included
            ws.dimensions.max_row = table.num_rows + 1
            ws.dimensions.min_col = 1
            ws.dimensions.max_col = table.num_columns

        wb = Workbook()
        wb.sheets.append(ws)
        return wb

    def _convert_arrow_value(self, val: Any) -> Any:
        """
        Convert a PyArrow scalar to a Python native or string.
        Handles nested types by serialising to string.
        """
        if val is None:
            return None
        if isinstance(val, (bytes, bytearray)):
            # Binary → base64 string for safe storage (optional)
            import base64
            return base64.b64encode(val).decode("ascii")
        if isinstance(val, (list, dict)):
            # Struct/List → string representation
            return str(val)
        if isinstance(val, (pa.TimestampScalar, pa.Date32Scalar, pa.Date64Scalar)):
            return str(val)
        # Numeric, boolean, string – keep as is
        return val

    def _read_table(self, data: bytes, options: ParseOptions) -> pa.Table:
        raise NotImplementedError  # subclass responsibility

    def _get_sheet_name(self, source_name: str, options: ParseOptions) -> str:
        if options.sheet_names and options.sheet_names:
            return options.sheet_names[0]
        base = Path(source_name).stem
        return base if base else "Sheet1"


class ParquetParser(ColumnarBinaryParser):
    """Parser for Apache Parquet files (.parquet)."""
    name = "parquet"
    supported_extensions = (".parquet",)

    def _read_table(self, data: bytes, options: ParseOptions) -> pa.Table:
        buf = io.BytesIO(data)
        return pq.read_table(buf)


class ArrowIPCParser(ColumnarBinaryParser):
    """Parser for Apache Arrow IPC files (Feather v2)."""
    name = "arrow"
    supported_extensions = (".arrow", ".feather")  # modern Feather is Arrow IPC

    def _read_table(self, data: bytes, options: ParseOptions) -> pa.Table:
        buf = io.BytesIO(data)
        # Try Arrow IPC first (Feather v2), fallback to legacy Feather v1
        try:
            return pa.ipc.open_file(buf).read_all()
        except pa.ArrowInvalid:
            # Legacy Feather v1
            return pf.read_table(buf)


class FeatherParser(ColumnarBinaryParser):
    """Parser for legacy Feather v1 files (.feather)."""
    name = "feather"
    supported_extensions = (".feather",)

    def _read_table(self, data: bytes, options: ParseOptions) -> pa.Table:
        buf = io.BytesIO(data)
        return pf.read_table(buf)
