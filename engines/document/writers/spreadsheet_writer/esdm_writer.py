# engines/document/writers/spreadsheet_writer/esdm_writer.py
"""
Facade for ESDM writers – automatically selects XLSX, CSV, or TSV writer.
Delegates to XLSXWriter for .xlsx/.xlsm, handles CSV/TSV internally.
"""

from __future__ import annotations
import csv
import io
from pathlib import Path
from typing import Optional, Dict, Any, AsyncIterator, cast
from datetime import datetime

from ...models.base import BaseDocument
from ...models.esdm_models import ESDMDocument, Workbook
from ...models.media_types import DocumentFormat
from ...models.exceptions import UnsupportedFormatError
from .base import ESDMWriteOptions
from .xlsx import XLSXWriter      # import from package, not inner module


class ESDMWriter:
    def __init__(self, options: Optional[ESDMWriteOptions] = None):
        self._options = options or ESDMWriteOptions()

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        data = await self.write(document)
        chunk_size = 64 * 1024
        for i in range(0, len(data), chunk_size):
            yield data[i:i+chunk_size]

    async def write(self, document: BaseDocument) -> bytes:
        doc = cast(ESDMDocument, document)
        workbook = doc.workbook
        fmt = self._determine_format(workbook)
        if fmt == DocumentFormat.XLSX:
            writer = XLSXWriter(self._options)
            return await writer.write(document)   # document is BaseDocument, writer accepts BaseDocument
        elif fmt == DocumentFormat.CSV:
            return await self._write_csv(workbook, delimiter=',')
        elif fmt == DocumentFormat.TSV:
            return await self._write_csv(workbook, delimiter='\t')
        else:
            raise UnsupportedFormatError(fmt.value, ["xlsx", "csv", "tsv"])

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        doc = cast(ESDMDocument, document)
        workbook = doc.workbook
        fmt = self._determine_format(workbook, target.suffix)
        if fmt == DocumentFormat.XLSX:
            writer = XLSXWriter(self._options)
            await writer.write_to_file(document, target, options)
        elif fmt == DocumentFormat.CSV:
            data = await self._write_csv(workbook, delimiter=',')
            target.write_bytes(data)
        elif fmt == DocumentFormat.TSV:
            data = await self._write_csv(workbook, delimiter='\t')
            target.write_bytes(data)
        else:
            raise UnsupportedFormatError(fmt.value, ["xlsx", "csv", "tsv"])

    async def _write_csv(self, workbook: Workbook, delimiter: str) -> bytes:
        if not workbook.sheets:
            return b''
        sheet = workbook.sheets[0]

        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL,
                            lineterminator=self._options.line_terminator)

        # Determine maximum column index
        max_col = 0
        for row in sheet.rows.values():
            if row.cells:
                max_col = max(max_col, max(row.cells.keys()))
        if max_col == 0:
            max_col = 1

        for row_idx in sorted(sheet.rows.keys()):
            row = sheet.rows[row_idx]
            row_data = []
            for col_idx in range(1, max_col + 1):
                cell = row.cells.get(col_idx)
                if cell is None:
                    row_data.append('')
                else:
                    val = cell.value
                    if isinstance(val, (int, float)):
                        row_data.append(str(val))
                    elif isinstance(val, datetime):
                        row_data.append(val.isoformat())
                    elif val is None:
                        row_data.append('')
                    else:
                        row_data.append(str(val))
            writer.writerow(row_data)

        return output.getvalue().encode(self._options.encoding)

    # ------------------------------------------------------------------
    # Format detection
    # ------------------------------------------------------------------
    def _determine_format(self, workbook: Workbook, extension_hint: Optional[str] = None) -> DocumentFormat:
        """Determine output format from document metadata or file extension."""
        # 1) From existing media_type
        if hasattr(workbook, 'media_type') and workbook.media_type:
            mt = workbook.media_type
            if mt.format in (DocumentFormat.XLSX, DocumentFormat.CSV, DocumentFormat.TSV):
                return mt.format

        # 2) From extension hint
        if extension_hint:
            ext = extension_hint.lower().lstrip('.')
            if ext in ('xlsx', 'xlsm'):
                return DocumentFormat.XLSX
            if ext == 'csv':
                return DocumentFormat.CSV
            if ext == 'tsv':
                return DocumentFormat.TSV

        # 3) Heuristic: multiple sheets, formulas, rich formatting → XLSX
        if len(workbook.sheets) > 1 or workbook.stylesheet.cell_formats.formats:
            return DocumentFormat.XLSX
        for sheet in workbook.sheets:
            for row in sheet.rows.values():
                for cell in row.cells.values():
                    if cell.formula or cell.rich_text or cell.style_id is not None:
                        return DocumentFormat.XLSX

        # 4) Default to CSV
        return DocumentFormat.CSV