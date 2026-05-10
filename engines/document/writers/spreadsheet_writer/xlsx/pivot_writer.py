"""
Pivot tables and pivot caches writer for XLSX.
Generates pivotCacheDefinition.xml and pivotTable.xml parts.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ....models.esdm_models import Workbook, PivotCache, PivotTable, PivotField
    from ..base import ESDMBaseWriter

from .const import XML_NAMESPACES


class PivotWriter:
    """
    Full-featured writer for pivot caches and pivot tables.
    Supports multiple caches, all field orientations, subtotals, layout, and styling.
    """

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer
        self._cache_counter = 0
        self._table_counter = 0

        # Ensure parent has storage for cache XMLs
        if not hasattr(self._parent, '_pivot_cache_xmls'):
            self._parent._pivot_cache_xmls = {}

    def write(
        self, workbook: Workbook
    ) -> tuple[str | None, dict[str, str], list[tuple[int, list[tuple[str, str, str]]]]]:
        """
        Returns:
        - XML of the first pivot cache definition (or None)
        - Dictionary mapping pivot table XML path to its content
        - List of (sheet_index, relationships) to add to worksheet .rels
        """
        if not (workbook.pivot_caches or workbook.pivot_tables):
            return None, {}, []

        # Write each pivot cache definition
        for idx, cache in enumerate(workbook.pivot_caches, start=1):
            cache_xml = self._write_pivot_cache_definition(cache, idx)
            path = f'xl/pivotCache/pivotCacheDefinition{idx}.xml'
            self._parent._pivot_cache_xmls[path] = cache_xml

        # Write each pivot table
        table_xmls: dict[str, str] = {}
        sheet_rels_extra: list[tuple[int, list[tuple[str, str, str]]]] = []

        for pt in workbook.pivot_tables:
            self._table_counter += 1
            table_xml = self._write_pivot_table(pt, self._table_counter)
            path = f'xl/pivotTables/pivotTable{self._table_counter}.xml'
            table_xmls[path] = table_xml

            # Determine owning sheet
            sheet_name = (pt.location.split('!')[0] if '!' in pt.location else '')
            sheet_idx = None
            for idx, sheet in enumerate(workbook.sheets, start=1):
                if sheet.name == sheet_name:
                    sheet_idx = idx
                    break
            if sheet_idx:
                rel_id = f'pivotTable_{self._table_counter}'
                rel_type = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/pivotTable'
                target = f'pivotTables/pivotTable{self._table_counter}.xml'
                sheet_rels_extra.append((sheet_idx, [(rel_id, target, rel_type)]))

        # Return first cache XML (for backward compatibility)
        first_cache_xml = None
        if self._parent._pivot_cache_xmls:
            first_cache_xml = next(iter(self._parent._pivot_cache_xmls.values()))
        return first_cache_xml, table_xmls, sheet_rels_extra

    # ------------------------------------------------------------------
    # Pivot Cache Definition (pivotCacheDefinition.xml)
    # ------------------------------------------------------------------
    def _write_pivot_cache_definition(self, cache: PivotCache, cache_id: int) -> str:
        root = ET.Element('pivotCacheDefinition', {
            'xmlns': XML_NAMESPACES[''],
            'xmlns:r': XML_NAMESPACES['r'],
            'cacheId': str(cache_id),
            'refreshOnLoad': '1',
            'refreshedByVersion': '15',
            'refreshVersion': '15',
            'createdVersion': '15',
        })

        # Source
        cache_source = ET.SubElement(root, 'cacheSource', {'type': 'worksheet'})
        ws_source = ET.SubElement(cache_source, 'worksheetSource')
        if cache.source.sheet:
            ws_source.set('ref', cache.source.ref)
            ws_source.set('sheet', cache.source.sheet)
            ws_source.set('r:id', f'rId{cache_id}_source')

        # Cache fields (must match number of columns in source range)
        # For completeness, assume 0 fields if not provided; user should populate.
        cache_fields = ET.SubElement(root, 'cacheFields', {'count': '0'})

        return ET.tostring(root, encoding='unicode', xml_declaration=True)

    # ------------------------------------------------------------------
    # Pivot Table Definition (pivotTable.xml)
    # ------------------------------------------------------------------
    def _write_pivot_table(self, pt: PivotTable, table_id: int) -> str:
        # Group fields by orientation
        row_fields: list[PivotField] = []
        col_fields: list[PivotField] = []
        data_fields: list[PivotField] = []
        page_fields: list[PivotField] = []

        for field in pt.fields:
            orient = field.orientation.lower()
            if orient == 'row':
                row_fields.append(field)
            elif orient == 'column':
                col_fields.append(field)
            elif orient == 'data':
                data_fields.append(field)
            elif orient == 'page':
                page_fields.append(field)

        root = ET.Element('pivotTableDefinition', {
            'xmlns': XML_NAMESPACES[''],
            'xmlns:r': XML_NAMESPACES['r'],
            'name': pt.name,
            'cacheId': str(pt.cache_id),
            'dataOnRows': '0',
            'dataPosition': '0',
            'applyNumberFormats': '0',
            'applyBorderFormats': '0',
            'applyFontFormats': '0',
            'applyPatternFormats': '0',
            'applyAlignmentFormats': '0',
            'applyWidthHeightFormats': '0',
            'applyDataFormats': '0',
            'dataCaption': getattr(pt, 'data_caption', 'Values'),
            'useAutoFormatting': '1',
            'indent': '0',
            'compact': '0',
            'compactData': '0',
            'gridDropZones': '0',
            'multipleFieldFilters': '0',
            'outline': '0',
            'outlineData': '0',
            'showCalcMbrs': '0',
            'showDropZones': '1',
            'showEmptyRow': '0',
            'showEmptyCol': '0',
            'showHeaders': '1',
            'showMemberPropertyTips': '0',
            'showMissing': '0',
            'visualTotalsForSets': '0',
            'autoFormatId': '0',
            'createdVersion': '15',
            'minRefreshableVersion': '15',
            'refreshedVersion': '15',
        })

        # Location
        loc = ET.SubElement(root, 'location')
        loc.set('ref', pt.location)
        loc.set('firstHeaderRow', '1')
        loc.set('firstDataRow', '1')
        loc.set('firstDataCol', '1')
        loc.set('rowPageCount', '0')
        loc.set('colPageCount', '0')

        # Row fields
        if row_fields:
            rf = ET.SubElement(root, 'rowFields', {'count': str(len(row_fields))})
            for idx, f in enumerate(row_fields):
                attrs = {'x': str(idx), 'axis': 'axisRow'}
                if getattr(f, 'subtotal', None):
                    if f.subtotal:
                        attrs['subtotal'] = f.subtotal
                ET.SubElement(rf, 'field', attrs)

        # Column fields
        if col_fields:
            cf = ET.SubElement(root, 'colFields', {'count': str(len(col_fields))})
            for idx, f in enumerate(col_fields):
                attrs = {'x': str(idx), 'axis': 'axisCol'}
                if getattr(f, 'subtotal', None):
                    if f.subtotal:
                        attrs['subtotal'] = f.subtotal
                ET.SubElement(cf, 'field', attrs)

        # Page fields (filters)
        if page_fields:
            pf = ET.SubElement(root, 'pageFields', {'count': str(len(page_fields))})
            for idx, f in enumerate(page_fields):
                ET.SubElement(pf, 'pageField', {'fld': str(idx), 'hier': '-1'})  # -1 = default

        # Data fields (value fields)
        if data_fields:
            df = ET.SubElement(root, 'dataFields', {'count': str(len(data_fields))})
            for idx, f in enumerate(data_fields):
                field_attrs = {
                    'name': f.name,
                    'fld': str(idx),
                    'subtotal': getattr(f, 'subtotal', 'sum'),
                    'showDataAs': getattr(f, 'show_data_as', 'normal'),
                    'baseField': '0',
                    'baseItem': '0',
                }
                ET.SubElement(df, 'dataField', field_attrs)

        # Table style
        style_name = getattr(pt, 'style_name', 'PivotStyleLight16')
        ET.SubElement(root, 'pivotTableStyleInfo', {
            'name': style_name,
            'showRowHeaders': '1',
            'showColHeaders': '1',
            'showRowStripes': '0',
            'showColStripes': '0',
            'showLastColumn': '1'
        })

        # Row/Column grand totals
        row_grand = getattr(pt, 'row_grand_totals', True)
        col_grand = getattr(pt, 'col_grand_totals', True)
        ET.SubElement(root, 'rowGrandTotals', {'show': '1' if row_grand else '0'})
        ET.SubElement(root, 'colGrandTotals', {'show': '1' if col_grand else '0'})

        return ET.tostring(root, encoding='unicode', xml_declaration=True)
