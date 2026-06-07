# engines/document/writers/spreadsheet_writer/csv_writer.py
"""
CSV and TSV writer for ESDM (Excel Spreadsheet Data Model).
Converts a Workbook to CSV or TSV format (only first worksheet is written).
"""
from __future__ import annotations

import csv
import io
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import cast

from ...models.base import BaseDocument
from ...models.esdm_models import Cell
from ...models.esdm_models import ESDMDocument
from ...models.esdm_models import Workbook
from ...models.esdm_models import Worksheet
from .base import ESDMBaseWriter
from .base import ESDMWriteOptions


class CSVWriter(ESDMBaseWriter):
    """
    Writer for CSV (Comma-Separated Values) files.
    Exports the first worksheet of the workbook.
    """

    def __init__(self, options: ESDMWriteOptions | None = None):
        super().__init__(options)
        self.delimiter = ','

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """Yield CSV content in chunks."""
        doc = cast(ESDMDocument, document)
        workbook = doc.workbook
        if workbook is None:
            raise ValueError("Document has no workbook data")
        content = await self._write_csv(workbook)
        chunk_size = 64 * 1024
        for i in range(0, len(content), chunk_size):
            yield content[i:i+chunk_size]

    async def write(self, document: BaseDocument) -> bytes:
        """Return full CSV content as bytes."""
        doc = cast(ESDMDocument, document)
        workbook = doc.workbook
        if workbook is None:
            raise ValueError("Document has no workbook data")
        return await self._write_csv(workbook)

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None
    ) -> None:
        """Write CSV directly to a file."""
        doc = cast(ESDMDocument, document)
        workbook = doc.workbook
        if workbook is None:
            raise ValueError("Document has no workbook data")
        content = await self._write_csv(workbook)
        target.write_bytes(content)

    async def _write_csv(self, workbook: Workbook) -> bytes:
        """Generate CSV bytes from the first worksheet."""
        if not workbook.sheets:
            return b''

        sheet = workbook.sheets[0]
        output = io.StringIO()
        
        # Determine encoding
        encoding = getattr(self._esdm_options, 'encoding', 'utf-8')
        if not encoding:
            encoding = 'utf-8'
            
        # Determine quoting behavior
        quoting_val: int = csv.QUOTE_MINIMAL
        if self._esdm_options.custom and 'quoting' in self._esdm_options.custom:
            quoting_map: dict[str, int] = {
                'MINIMAL': csv.QUOTE_MINIMAL,
                'ALL': csv.QUOTE_ALL,
                'NONNUMERIC': csv.QUOTE_NONNUMERIC,
                'NONE': csv.QUOTE_NONE
            }
            quoting_str = str(self._esdm_options.custom['quoting']).upper()
            quoting_val = quoting_map.get(quoting_str, csv.QUOTE_MINIMAL)
        quoting = cast(Any, quoting_val)
        
        # Determine line terminator
        lineterminator = getattr(self._esdm_options, 'line_terminator', '\r\n')
        if not lineterminator:
            lineterminator = '\r\n'

        writer = csv.writer(
            output,
            delimiter=self.delimiter,
            quoting=quoting,
            lineterminator=lineterminator
        )

        # Determine maximum column index
        max_col = self._get_max_columns(sheet)
        if max_col == 0:
            max_col = 1

        for row_idx in sorted(sheet.rows.keys()):
            row = sheet.rows[row_idx]
            row_data = []
            for col_idx in range(1, max_col + 1):
                cell = row.cells.get(col_idx)
                row_data.append(self._cell_to_csv_value(cell))
            writer.writerow(row_data)

        return output.getvalue().encode(encoding)

    def _get_max_columns(self, sheet: Worksheet) -> int:
        """Return the highest column index with any cell in the sheet."""
        max_col = 0
        for row in sheet.rows.values():
            if row.cells:
                max_col = max(max_col, max(row.cells.keys()))
        return max_col

    def _cell_to_csv_value(self, cell: Cell | None) -> str:
        """Convert a cell value to CSV string."""
        if cell is None or cell.value is None:
            return ''
        val = cell.value
        if isinstance(val, bool):
            return 'TRUE' if val else 'FALSE'
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, datetime):
            return val.isoformat()
        # For strings, we keep as is; csv.writer will quote if needed
        return str(val)

    # ------------------------------------------------------------------
    # Abstract methods from ESDMBaseWriter (not used for CSV)
    # ------------------------------------------------------------------
    def _write_workbook_xml(self, workbook: Workbook) -> str:
        raise NotImplementedError("CSVWriter does not generate XML")

    def _write_worksheet_xml(self, worksheet: Worksheet, sheet_id: int) -> str:
        raise NotImplementedError("CSVWriter does not generate XML")

    def _write_styles_xml(self) -> str:
        raise NotImplementedError("CSVWriter does not generate XML")

    # ------------------------------------------------------------------
    # Supported types
    # ------------------------------------------------------------------
    def get_supported_media_types(self) -> list[str]:
        return ["text/csv"]

    def get_supported_extensions(self) -> list[str]:
        return [".csv"]


class TSVWriter(CSVWriter):
    """Writer for TSV (Tab-Separated Values) files. Inherits CSVWriter with tab delimiter."""

    def __init__(self, options: ESDMWriteOptions | None = None):
        super().__init__(options)
        self.delimiter = '\t'

    def get_supported_media_types(self) -> list[str]:
        return ["text/tab-separated-values"]

    def get_supported_extensions(self) -> list[str]:
        return [".tsv"]
