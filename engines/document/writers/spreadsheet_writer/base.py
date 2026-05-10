# engines/document/writers/spreadsheet_writer/base.py
"""
Base classes and shared utilities for ESDM writers (Excel, CSV, TSV).
"""
from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile
from abc import abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from zipfile import ZipFile, ZIP_DEFLATED

from ...models.base import BaseDocument
from ...models.esdm_models import Border
from ...models.esdm_models import BorderSide
from ...models.esdm_models import CellFormat
from ...models.esdm_models import Fill
from ...models.esdm_models import Font
from ...models.esdm_models import NumberFormat
from ...models.esdm_models import Workbook
from ...models.esdm_models import Worksheet
from ...writers.base import BaseDocumentWriter
from ...writers.base import WriteOptions


class ESDMWriteOptions(WriteOptions):
    """Extended write options for spreadsheet formats."""

    # XLSX specific
    use_shared_strings: bool = True          # Use shared string table or inline strings
    optimize_for_memory: bool = False        # For huge sheets (stream row by row)
    write_macros: bool = True                # Include VBA project if present

    # CSV / TSV specific
    delimiter: str = ","                     # For CSV
    line_terminator: str = "\n"
    quote_all: bool = False
    encoding: str = "utf-8"                  # Override base default


class ESDMBaseWriter(BaseDocumentWriter):
    """
    Abstract base for all ESDM writers.

    Provides shared logic for XLSX packaging (ZIP, XML namespaces, shared strings,
    style caching). CSV/TSV writers may not need all of this but can still inherit.
    """

    # Excel XML namespaces
    NAMESPACES = {
        '': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'vt': 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes',
    }

    def __init__(self, options: ESDMWriteOptions | None = None):
        # Ensure options are of the correct type
        if options is None:
            options = ESDMWriteOptions()
        elif not isinstance(options, ESDMWriteOptions):
            # Convert if a plain WriteOptions is passed
            options = ESDMWriteOptions(**options.model_dump())
        super().__init__(options)
        self._esdm_options = options

        # Caches for XLSX generation
        self._shared_strings: list[str] = []              # index -> string
        self._shared_strings_index: dict[str, int] = {}   # string -> index

        self._style_cache: dict[tuple, int] = {}          # (key) -> xf_id
        self._font_cache: dict[tuple, int] = {}
        self._fill_cache: dict[tuple, int] = {}
        self._border_cache: dict[tuple, int] = {}
        self._numfmt_cache: dict[str, int] = {}           # format_code -> custom id

        # We will store the actual objects for later XML generation
        self._fonts: list[Font] = []
        self._fills: list[Fill] = []
        self._borders: list[Border] = []
        self._numfmts: list[NumberFormat] = []
        self._cell_formats: list[CellFormat] = []

        self._extra_parts: dict[str, str | bytes] = {}
        self._image_binaries: dict[str, bytes] = {}
        self._chart_xmls: dict[str, str] = {}
        self._pivot_cache_xmls: dict[str, str] = {}
        self._comment_authors: list[str] = []

    # ------------------------------------------------------------------
    # Abstract methods from BaseDocumentWriter (must be overridden)
    # ------------------------------------------------------------------
    @abstractmethod
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """Yield chunks of the resulting file."""
        yield b""

    @abstractmethod
    async def write(self, document: BaseDocument) -> bytes:
        """Return full file content as bytes."""
        return b""

    @abstractmethod
    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None
    ) -> None:
        """Write directly to a file."""

    # ------------------------------------------------------------------
    # Shared string table management
    # ------------------------------------------------------------------
    def _add_shared_string(self, value: str) -> int:
        """Register a string and return its index."""
        if value not in self._shared_strings_index:
            idx = len(self._shared_strings)
            self._shared_strings_index[value] = idx
            self._shared_strings.append(value)
            return idx
        return self._shared_strings_index[value]

    def _get_shared_strings_xml(self) -> str:
        """Generate the sharedStrings.xml part."""
        if not self._shared_strings:
            return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="0" uniqueCount="0" />'''
        root = ET.Element('sst', {
            'xmlns': self.NAMESPACES[''],
            'count': str(len(self._shared_strings)),
            'uniqueCount': str(len(self._shared_strings))
        })
        for s in self._shared_strings:
            si = ET.SubElement(root, 'si')
            t = ET.SubElement(si, 't')
            t.text = s
        return ET.tostring(root, encoding='unicode', xml_declaration=True)

    # ------------------------------------------------------------------
    # Style subsystem (fonts, fills, borders, number formats, cellXfs)
    # ------------------------------------------------------------------
    def _normalize_color(self, color: str | None) -> str | None:
        """Convert color to RRGGBB (no leading #) or None."""
        if color is None:
            return None
        color = color.lstrip('#').upper()
        if len(color) == 3:
            color = ''.join([c*2 for c in color])
        return color if len(color) == 6 else None

    def _register_font(self, font: Font) -> int:
        """Register a font and return its index."""
        key = (
            font.name, font.size, font.bold, font.italic,
            font.underline.value, font.strike, self._normalize_color(font.color),
            font.charset, font.family, font.scheme
        )
        if key in self._font_cache:
            return self._font_cache[key]
        idx = len(self._fonts)
        self._font_cache[key] = idx
        self._fonts.append(font)
        return idx

    def _register_fill(self, fill: Fill) -> int:
        """Register a fill (pattern or gradient) and return its index."""
        key: tuple
        if fill.pattern:
            key = ('pattern',
                   fill.pattern.pattern_type.value,
                   self._normalize_color(fill.pattern.fg_color),
                   self._normalize_color(fill.pattern.bg_color))
        elif fill.gradient:
            # simplified key; full implementation would include stops
            key = ('gradient', fill.gradient.degree, len(fill.gradient.stops))
        else:
            key = ('none',)
        if key in self._fill_cache:
            return self._fill_cache[key]
        idx = len(self._fills)
        self._fill_cache[key] = idx
        self._fills.append(fill)
        return idx

    def _register_border(self, border: Border) -> int:
        """Register a border and return its index."""
        def side_key(side: BorderSide):
            return (side.style.value, self._normalize_color(side.color))
        key = (
            side_key(border.left), side_key(border.right),
            side_key(border.top), side_key(border.bottom),
            border.diagonal_up, border.diagonal_down
        )
        if key in self._border_cache:
            return self._border_cache[key]
        idx = len(self._borders)
        self._border_cache[key] = idx
        self._borders.append(border)
        return idx

    def _register_number_format(self, fmt_code: str) -> int:
        """Register a custom number format, return its ID (>=164)."""
        if fmt_code in self._numfmt_cache:
            return self._numfmt_cache[fmt_code]
        # Custom IDs start at 164
        new_id = 164 + len(self._numfmt_cache)
        self._numfmt_cache[fmt_code] = new_id
        self._numfmts.append(NumberFormat(id=new_id, format_code=fmt_code))
        return new_id

    def _register_cell_format(self, cell_format: CellFormat) -> int:
        """Register a cell format (xf) and return its index."""
        key = (
            cell_format.number_format_id,
            cell_format.font_id,
            cell_format.fill_id,
            cell_format.border_id,
            (cell_format.alignment.horizontal.value if cell_format.alignment else None),
            (cell_format.alignment.vertical.value if cell_format.alignment else None),
            cell_format.alignment.wrap_text if cell_format.alignment else False,
            cell_format.alignment.shrink_to_fit if cell_format.alignment else False,
            cell_format.alignment.indent if cell_format.alignment else 0,
            cell_format.alignment.text_rotation if cell_format.alignment else 0,
            cell_format.protection.locked if cell_format.protection else True,
            cell_format.protection.hidden if cell_format.protection else False,
        )
        if key in self._style_cache:
            return self._style_cache[key]
        idx = len(self._cell_formats)
        self._style_cache[key] = idx
        self._cell_formats.append(cell_format)
        return idx

    # ------------------------------------------------------------------
    # ZIP packaging helpers for XLSX
    # ------------------------------------------------------------------
    async def _build_zip_package(
        self,
        workbook: Workbook,
        parts: dict[str, str | bytes]
    ) -> bytes:
        """
        Build a ZIP archive from a dictionary of internal paths -> content.
        Adds mandatory [Content_Types].xml and _rels/.rels.
        """
        with io.BytesIO() as buffer:
            with ZipFile(buffer, 'w', ZIP_DEFLATED) as zf:
                # Write provided parts
                for path, content in parts.items():
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    zf.writestr(path, content)
                # Add required core files
                types_xml = self._make_content_types_xml(workbook)
                zf.writestr('[Content_Types].xml', types_xml.encode('utf-8'))
                rels_xml = self._make_root_rels_xml(workbook)
                zf.writestr('_rels/.rels', rels_xml.encode('utf-8'))
            return buffer.getvalue()

    def _make_content_types_xml(self, workbook: Workbook) -> str:
        """Generate [Content_Types].xml with overrides for sheets and other parts."""
        overrides = [
            ('/xl/workbook.xml', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'),
            ('/xl/styles.xml', 'application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml'),
            ('/xl/sharedStrings.xml', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml'),
        ]
        for i, _ in enumerate(workbook.sheets, start=1):
            overrides.append((f'/xl/worksheets/sheet{i}.xml',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'))
        # TODO: add overrides for tables, drawings, pivot tables, VBA project if present

        root = ET.Element('Types', xmlns='http://schemas.openxmlformats.org/package/2006/content-types')
        for part, content_type in overrides:
            ET.SubElement(root, 'Override', {'PartName': part, 'ContentType': content_type})
        # Add default for XML
        ET.SubElement(root, 'Default', {'Extension': 'xml', 'ContentType': 'application/xml'})
        ET.SubElement(root, 'Default', {'Extension': 'rels', 'ContentType': 'application/vnd.openxmlformats-package.relationships+xml'})
        return ET.tostring(root, encoding='unicode', xml_declaration=True)

    def _make_root_rels_xml(self, workbook: Workbook) -> str:
        """Create _rels/.rels linking to workbook.xml and core properties."""
        root = ET.Element('Relationships', xmlns='http://schemas.openxmlformats.org/package/2006/relationships')
        ET.SubElement(root, 'Relationship', {
            'Id': 'rId1',
            'Type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument',
            'Target': 'xl/workbook.xml'
        })
        # Core properties (optional)
        ET.SubElement(root, 'Relationship', {
            'Id': 'rId2',
            'Type': 'http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties',
            'Target': 'docProps/core.xml'
        })
        return ET.tostring(root, encoding='unicode', xml_declaration=True)

    # ------------------------------------------------------------------
    # To be implemented by concrete writers
    # ------------------------------------------------------------------
    @abstractmethod
    def _write_workbook_xml(self, workbook: Workbook) -> str:
        """Generate workbook.xml content."""

    @abstractmethod
    def _write_worksheet_xml(self, worksheet: Worksheet, sheet_id: int) -> str:
        """Generate sheetX.xml for a single worksheet."""

    @abstractmethod
    def _write_styles_xml(self) -> str:
        """Generate styles.xml from collected fonts, fills, borders, etc."""
