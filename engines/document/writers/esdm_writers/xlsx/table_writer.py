# engines/document/writers/spreadsheet_writer/xlsx/table_writer.py
"""
Table (ListObject) writer for XLSX.
Generates tableX.xml files for each table in a worksheet.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET


from .const import XML_NAMESPACES
from ....models.esdm_models import Table
from ..base import ESDMBaseWriter


class TableWriter:
    """
    Writes table XML parts and returns relationship info.
    Each table gets its own XML file.
    """

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer

    def write(self, table: Table, table_id: int) -> tuple[str, tuple[str, str, str]]:
        """
        Generate tableX.xml content and the relationship needed by the worksheet.
        Returns (table_xml_str, (rel_id, target, rel_type)).
        """
        root = ET.Element('table', {
            'xmlns': XML_NAMESPACES[''],
            'id': str(table_id),
            'name': table.name,
            'displayName': table.display_name or table.name,
            'ref': table.ref or self._calculate_ref_from_rows(table),
            'headerRowCount': str(table.header_row_count),
            'totalsRowCount': str(table.totals_row_count),
        })

        # AutoFilter (if present)
        if table.auto_filter and table.auto_filter.ref:
            ET.SubElement(root, 'autoFilter', {'ref': table.auto_filter.ref})

        # Table columns
        table_columns = ET.SubElement(root, 'tableColumns', {'count': str(len(table.columns))})
        for col in table.columns:
            col_attrs = {'id': str(col.id), 'name': col.name}
            if col.totals_row_function:
                col_attrs['totalsRowFunction'] = col.totals_row_function
            if col.totals_row_label:
                col_attrs['totalsRowLabel'] = col.totals_row_label
            if col.calculated_column_formula:
                col_attrs['calculatedColumnFormula'] = col.calculated_column_formula
            ET.SubElement(table_columns, 'tableColumn', col_attrs)

        # Table style info
        if table.table_style_info:
            tsi = table.table_style_info
            style_attrs = {
                'name': tsi.name,
                'showFirstColumn': '1' if tsi.show_first_column else '0',
                'showLastColumn': '1' if tsi.show_last_column else '0',
                'showRowStripes': '1' if tsi.show_row_stripes else '0',
                'showColumnStripes': '1' if tsi.show_column_stripes else '0',
            }
            ET.SubElement(root, 'tableStyleInfo', style_attrs)

        # Table rows data (optional) – Excel stores row data in the worksheet, not inside table XML.
        # But we can add a <tableRows> element if needed for some applications.
        # Typically not required.

        xml_str = ET.tostring(root, encoding='unicode', xml_declaration=True)
        rel_id = f'table_{table_id}'
        target = f'tables/table{table_id}.xml'
        rel_type = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/table'
        return xml_str, (rel_id, target, rel_type)

    def _calculate_ref_from_rows(self, table: Table) -> str:
        """
        Compute the range reference from table rows and columns if 'ref' is missing.
        Returns something like "A1:D20".
        """
        if not table.rows:
            return 'A1:A1'
        # Find min/max row and column from row data
        min_row = min(row.index for row in table.rows)
        max_row = max(row.index for row in table.rows)
        # Columns: use table column ids
        min_col = min(col.id for col in table.columns) if table.columns else 1
        max_col = max(col.id for col in table.columns) if table.columns else 1
        start_cell = f"{self._col_letter(min_col)}{min_row}"
        end_cell = f"{self._col_letter(max_col)}{max_row}"
        return f"{start_cell}:{end_cell}"

    def _col_letter(self, col_num: int) -> str:
        """Convert 1-based column number to Excel column letters."""
        result = ''
        while col_num > 0:
            col_num, remainder = divmod(col_num - 1, 26)
            result = chr(65 + remainder) + result
        return result

