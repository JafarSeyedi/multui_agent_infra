# engines/document/writers/spreadsheet_writer/xlsx/workbook_writer.py
"""
Writes workbook.xml and defined names.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET


from .const import XML_NAMESPACES  # shared constant (we'll define in a common place)
from ..base import ESDMBaseWriter
from ....models.esdm_models import Workbook


class WorkbookWriter:
    """Generates workbook.xml and definedNames."""

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer

    def write(self, workbook: Workbook) -> str:
        root = ET.Element('workbook', {
            'xmlns': XML_NAMESPACES[''],
            'xmlns:r': XML_NAMESPACES['r']
        })

        # Workbook properties
        if workbook.properties:
            wb_pr = ET.SubElement(root, 'workbookPr')
            if workbook.properties.date_1904:
                wb_pr.set('date1904', '1')
            wb_pr.set('defaultThemeVersion', str(workbook.properties.default_theme_version))

        # Sheets
        sheets_elem = ET.SubElement(root, 'sheets')
        # rId1 is workbook relationships, rId2 is core properties, sheets start at rId3
        for idx, sheet in enumerate(workbook.sheets, start=1):
            ET.SubElement(sheets_elem, 'sheet', {
                'name': sheet.name,
                'sheetId': str(idx),
                'r:id': f'rId{idx+2}'
            })

        # Defined names
        if workbook.defined_names:
            defined_names = ET.SubElement(root, 'definedNames')
            for dn in workbook.defined_names:
                attrs = {'name': dn.name}
                if dn.local_sheet_id is not None:
                    attrs['localSheetId'] = str(dn.local_sheet_id)
                elem = ET.SubElement(defined_names, 'definedName', attrs)
                elem.text = dn.formula

        # Calculation properties
        calc_pr = ET.SubElement(root, 'calcPr')
        calc_pr.set('calcId', '124519')
        calc_pr.set('fullCalcOnLoad', '1' if workbook.full_calculation_on_load else '0')

        return ET.tostring(root, encoding='unicode', xml_declaration=True)

