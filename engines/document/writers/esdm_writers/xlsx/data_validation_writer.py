# engines/document/writers/spreadsheet_writer/xlsx/data_validation_writer.py
"""
Data validation writer for XLSX.
Generates the <dataValidations> element for a worksheet.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from ....models.esdm_models import Worksheet, DataValidation
from ..base import ESDMBaseWriter




class DataValidationWriter:
    """
    Writes data validations for a worksheet.
    Returns an XML element to be inserted into the worksheet root.
    """

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer

    def write(self, worksheet: Worksheet) -> ET.Element | None:
        """
        Generate the <dataValidations> element for the worksheet.
        Returns None if there are no data validations.
        """
        if not worksheet.data_validations:
            return None

        dvs_elem = ET.Element('dataValidations', {
            'count': str(len(worksheet.data_validations))
        })

        for dv in worksheet.data_validations:
            dv_elem = self._write_data_validation(dv)
            dvs_elem.append(dv_elem)

        return dvs_elem

    def _write_data_validation(self, dv: DataValidation) -> ET.Element:
        """
        Convert a DataValidation model to an Excel <dataValidation> element.
        """
        rule = dv.rule
        attrs = {
            'type': self._get_validation_type(rule.type),
            'sqref': dv.ref,
            'allowBlank': '1' if rule.allow_blank else '0',
            'showInputMessage': '1' if rule.show_input_message else '0',
            'showErrorMessage': '1' if rule.show_error_message else '0',
        }

        # Add operator if present (not for 'list', 'custom')
        if rule.operator is not None:
            attrs['operator'] = self._get_validation_operator(rule.operator)

        # Add optional error/style
        if rule.error_title:
            attrs['errorTitle'] = rule.error_title
        if rule.error_message:
            attrs['error'] = rule.error_message
        if rule.prompt_title:
            attrs['promptTitle'] = rule.prompt_title
        if rule.prompt_message:
            attrs['prompt'] = rule.prompt_message

        # For list type, set inCellDropdown default
        if rule.type.value == 'list':
            attrs['inCellDropdown'] = '1'

        dv_elem = ET.Element('dataValidation', attrs)

        # Add formula1 and formula2 if present
        if rule.formula1:
            f1 = ET.SubElement(dv_elem, 'formula1')
            f1.text = rule.formula1
        if rule.formula2:
            f2 = ET.SubElement(dv_elem, 'formula2')
            f2.text = rule.formula2

        return dv_elem

    def _get_validation_type(self, vt) -> str:
        """
        Map ESDM DataValidationType to Excel type string.
        """
        mapping = {
            'whole': 'whole',
            'decimal': 'decimal',
            'list': 'list',
            'date': 'date',
            'time': 'time',
            'textLength': 'textLength',
            'custom': 'custom',
        }
        return mapping.get(vt.value, 'custom')

    def _get_validation_operator(self, op) -> str:
        """
        Map ESDM DataValidationOperator to Excel operator string.
        """
        mapping = {
            'between': 'between',
            'notBetween': 'notBetween',
            'equal': 'equal',
            'notEqual': 'notEqual',
            'lessThan': 'lessThan',
            'lessThanOrEqual': 'lessThanOrEqual',
            'greaterThan': 'greaterThan',
            'greaterThanOrEqual': 'greaterThanOrEqual',
        }
        return mapping.get(op.value, 'between')

