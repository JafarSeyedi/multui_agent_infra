# engines/document/writers/spreadsheet_writer/xlsx/conditional_formatting_writer.py
"""
Conditional formatting writer for XLSX.
Generates <conditionalFormatting> elements for a worksheet.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from ....models.esdm_models import Worksheet, CFRule
from ..base import ESDMBaseWriter




class ConditionalFormattingWriter:
    """
    Writes conditional formatting for a worksheet.
    Returns a list of XML elements to be inserted into the worksheet root.
    """

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer

    def write(self, worksheet: Worksheet) -> list[ET.Element]:
        """
        Generate a list of <conditionalFormatting> elements.
        Returns empty list if there are no conditional formattings.
        """
        if not worksheet.conditional_formattings:
            return []

        elements = []
        for cf in worksheet.conditional_formattings:
            cf_elem = ET.Element('conditionalFormatting', {'sqref': cf.ref})
            for rule in cf.rules:
                rule_elem = self._write_rule(rule)
                cf_elem.append(rule_elem)
            elements.append(cf_elem)
        return elements

    def _write_rule(self, rule: CFRule) -> ET.Element:
        """Convert a CFRule model to an Excel <cfRule> element."""
        attrs = {
            'type': self._get_cf_type(rule.type),
            'priority': str(rule.priority),
        }
        if rule.stop_if_true:
            attrs['stopIfTrue'] = '1'
        if rule.dxf_id is not None:
            attrs['dxfId'] = str(rule.dxf_id)
        if rule.operator is not None:
            attrs['operator'] = self._get_cf_operator(rule.operator)

        rule_elem = ET.Element('cfRule', attrs)

        # Formulas
        for formula in rule.formula:
            f_elem = ET.SubElement(rule_elem, 'formula')
            f_elem.text = formula

        # Color scale
        if rule.color_scale:
            self._write_color_scale(rule_elem, rule.color_scale)

        # Data bar
        if rule.data_bar:
            self._write_data_bar(rule_elem, rule.data_bar)

        # Icon set
        if rule.icon_set:
            self._write_icon_set(rule_elem, rule.icon_set)

        return rule_elem

    def _get_cf_type(self, cf_type) -> str:
        """Map CFType enum to Excel type string."""
        mapping = {
            'cellIs': 'cellIs',
            'expression': 'expression',
            'colorScale': 'colorScale',
            'dataBar': 'dataBar',
            'iconSet': 'iconSet',
            'top10': 'top10',
            'uniqueValues': 'uniqueValues',
            'duplicateValues': 'duplicateValues',
            'containsText': 'containsText',
            'notContainsText': 'notContainsText',
            'beginsWith': 'beginsWith',
            'endsWith': 'endsWith',
            'containsBlanks': 'containsBlanks',
            'notContainsBlanks': 'notContainsBlanks',
            'containsErrors': 'containsErrors',
            'notContainsErrors': 'notContainsErrors',
            'timePeriod': 'timePeriod',
            'aboveAverage': 'aboveAverage',
        }
        return mapping.get(cf_type.value, 'expression')

    def _get_cf_operator(self, op) -> str:
        """Map CFOperator enum to Excel operator string."""
        mapping = {
            'lessThan': 'lessThan',
            'lessThanOrEqual': 'lessThanOrEqual',
            'greaterThan': 'greaterThan',
            'greaterThanOrEqual': 'greaterThanOrEqual',
            'equal': 'equal',
            'notEqual': 'notEqual',
            'between': 'between',
            'notBetween': 'notBetween',
        }
        return mapping.get(op.value, 'equal')

    def _write_color_scale(self, parent: ET.Element, cs):
        """Add a <colorScale> element."""
        cs_elem = ET.SubElement(parent, 'colorScale')
        for cv in cs.values:
            cfvo = ET.SubElement(cs_elem, 'cfvo')
            cfvo.set('type', cv.type)
            if cv.value is not None:
                cfvo.set('val', str(cv.value))
        for color in cs.colors:
            color_elem = ET.SubElement(cs_elem, 'color')
            n_color=self._normalize_color(color)
            if n_color:
                color_elem.set('rgb', n_color)

    def _write_data_bar(self, parent: ET.Element, db):
        """Add a <dataBar> element."""
        db_elem = ET.SubElement(parent, 'dataBar')
        # Min value
        cfvo_min = ET.SubElement(db_elem, 'cfvo')
        cfvo_min.set('type', db.min_value.type)
        if db.min_value.value is not None:
            cfvo_min.set('val', str(db.min_value.value))
        # Max value
        cfvo_max = ET.SubElement(db_elem, 'cfvo')
        cfvo_max.set('type', db.max_value.type)
        if db.max_value.value is not None:
            cfvo_max.set('val', str(db.max_value.value))
        # Color
        color_elem = ET.SubElement(db_elem, 'color')
        if db.color:
            n_color=self._normalize_color(db.color)
            if n_color:
                color_elem.set('rgb', n_color)
        # Options
        if not db.show_value:
            db_elem.set('showValue', '0')
        if db.gradient:
            db_elem.set('gradient', '1')
        else:
            db_elem.set('gradient', '0')
        if db.border:
            db_elem.set('border', '1')

    def _write_icon_set(self, parent: ET.Element, icon_set):
        """Add an <iconSet> element."""
        ic_elem = ET.SubElement(parent, 'iconSet')
        ic_elem.set('iconSet', icon_set.icon_set_type.value)
        if not icon_set.show_value:
            ic_elem.set('showValue', '0')
        if icon_set.reverse:
            ic_elem.set('reverse', '1')
        for crit in icon_set.criteria:
            cfvo = ET.SubElement(ic_elem, 'cfvo')
            cfvo.set('type', crit.type)
            if crit.value is not None:
                cfvo.set('val', str(crit.value))
            if crit.operator:
                cfvo.set('gte', '1' if crit.operator == '>=' else '0')

    def _normalize_color(self, color: str | None) -> str | None:
        """Convert color to RRGGBB (no leading #) or None."""
        if color is None:
            return None
        color = color.lstrip('#').upper()
        if len(color) == 3:
            color = ''.join([c*2 for c in color])
        return color if len(color) == 6 else None

