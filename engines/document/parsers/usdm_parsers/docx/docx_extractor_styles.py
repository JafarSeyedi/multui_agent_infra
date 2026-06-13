# mypy: disable-error-code="attr-defined"

from __future__ import annotations

import os
import re
from datetime import datetime
from io import BytesIO
from typing import Any
from typing import BinaryIO
from typing import cast
from typing import Literal
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from zipfile import BadZipFile

from ....models.base import BinaryEncoding
from .docx_chart_extractor import parse_docx_chart
from .docx_diagram_extractor import parse_diagram
from .docx_image_extractor import DOCXImageExtractor
from .docx_math_parser import OMMLParser
from .docx_models import (
    DOCXBreak, DOCXChartData, DOCXColumns, DOCXComment, DOCXComplexField,
    DOCXCoreProperties, DOCXCustomProperties, DOCXDocument, DOCXDrawing,
    DOCXExtendedProperties, DOCXField, DOCXFootnoteEndnote, DOCXHeaderFooter,
    DOCXNumberingDefinition, DOCXNumberingInstance, DOCXNumberingLevel,
    DOCXPageMargins, DOCXPageSize, DOCXParagraph, DOCXParagraphProperties,
    DOCXRTLProperties, DOCXRunContent, DOCXRunProperties, DOCXSection,
    DOCXStyle, DOCXSymbol, DOCXTab, DOCXTable, DOCXTableCell,
    DOCXTableCellProperties, DOCXTableGrid, DOCXTableProperties, DOCXTableRow,
    DOCXTextRun, DOCXTOCField, DOCXWatermark, NumberingLevelSuffix,
    ParagraphAlignment, SectionType, TextDirection, VerticalAlignment,
)
from .docx_style_parser import DocxStyleParser
from .docx_table_parser import DocxTableParser
from .docx_utils import get_element_text, NS, parse_border_element
from .docx_utils import parse_dxa_to_points, parse_shading_element
from .docx_utils import safe_find, safe_findall


class DOCXExtractorStyles:
    """Mixin providing DOCX extractor styles methods."""

    def _extract_styles(self) -> dict[str, DOCXStyle]:
        """Extract styles from styles.xml."""
        styles_xml = self._get_xml_document('word/styles.xml')
        if styles_xml is None:
            return {}
        assert self.style_parser is not None
        return self.style_parser.parse_styles(styles_xml)


    def _extract_default_style_ids(self) -> tuple[str | None, str | None, str | None]:
        """Extract default style IDs from styles.xml."""
        styles_xml = self._get_xml_document('word/styles.xml')
        if styles_xml is None:
            return None, None, None

        para_default = None
        char_default = None
        table_default = None

        doc_defaults = safe_find(styles_xml, './/w:docDefaults')
        if doc_defaults is not None:
            para_def = safe_find(doc_defaults, './/w:pPrDefault/w:pPr')
            if para_def is not None:
                style_elem = safe_find(para_def, './/w:pStyle')
                if style_elem is not None:
                    para_default = style_elem.get(f'{{{NS["w"]}}}val')

            char_def = safe_find(doc_defaults, './/w:rPrDefault/w:rPr')
            if char_def is not None:
                style_elem = safe_find(char_def, './/w:rStyle')
                if style_elem is not None:
                    char_default = style_elem.get(f'{{{NS["w"]}}}val')

        return para_default, char_default, table_default


    def _extract_numbering(self) -> tuple[dict[str, DOCXNumberingDefinition], dict[str, DOCXNumberingInstance]]:
        """Extract numbering definitions and instances from numbering.xml."""
        num_xml = self._get_xml_document('word/numbering.xml')
        if num_xml is None:
            return {}, {}

        definitions: dict[str, DOCXNumberingDefinition] = {}
        instances: dict[str, DOCXNumberingInstance] = {}

        # Parse abstract numbering definitions
        for abs_num_elem in safe_findall(num_xml, './/w:abstractNum'):
            abs_id = abs_num_elem.get(f'{{{NS["w"]}}}abstractNumId')
            if abs_id:
                definition = self._parse_abstract_numbering(abs_num_elem)
                definitions[abs_id] = definition

        # Parse numbering instances
        for num_elem in safe_findall(num_xml, './/w:num'):
            num_id = num_elem.get(f'{{{NS["w"]}}}numId')
            if num_id:
                instance = self._parse_numbering_instance(num_elem, definitions)
                instances[num_id] = instance

        self._num_definitions = definitions
        self._num_instances = instances

        return definitions, instances


    def _parse_abstract_numbering(self, elem: ET.Element) -> DOCXNumberingDefinition:
        """Parse an abstract numbering definition."""
        abs_id = elem.get(f'{{{NS["w"]}}}abstractNumId', '')

        definition = DOCXNumberingDefinition(abstract_id=abs_id)

        # Name
        name_elem = safe_find(elem, './/w:name')
        if name_elem is not None:
            definition.name = name_elem.get(f'{{{NS["w"]}}}val')

        # Style link
        style_link_elem = safe_find(elem, './/w:styleLink')
        if style_link_elem is not None:
            definition.style_link = style_link_elem.get(f'{{{NS["w"]}}}val')

        # Multi-level type
        multi_level_elem = safe_find(elem, './/w:multiLevelType')
        if multi_level_elem is not None:
            val = multi_level_elem.get(f'{{{NS["w"]}}}val', '')
            definition.is_multi_level = val == 'multilevel' or val == 'hybridMultilevel'

        # Parse each level
        for lvl_elem in safe_findall(elem, './/w:lvl'):
            level_num = self._parse_int(lvl_elem.get(f'{{{NS["w"]}}}ilvl'))
            if level_num is not None:
                level = self._parse_numbering_level(lvl_elem, level_num)
                definition.levels[level_num] = level

        return definition


    def _parse_numbering_level(self, elem: ET.Element, level_num: int) -> DOCXNumberingLevel:
        """Parse a numbering level definition."""
        level = DOCXNumberingLevel(level=level_num)

        # Start value
        start_elem = safe_find(elem, './/w:start')
        if start_elem is not None:
            level.start = self._parse_int(start_elem.get(f'{{{NS["w"]}}}val')) or 1

        # Number format
        format_elem = safe_find(elem, './/w:numFmt')
        if format_elem is not None:
            level.format = format_elem.get(f'{{{NS["w"]}}}val', 'decimal')

        # Text template
        text_elem = safe_find(elem, './/w:lvlText')
        if text_elem is not None:
            level.text_template = text_elem.get(f'{{{NS["w"]}}}val', '%1.')

        # Alignment
        align_elem = safe_find(elem, './/w:lvlJc')
        if align_elem is not None:
            val = align_elem.get(f'{{{NS["w"]}}}val', 'left')
            level.alignment = ParagraphAlignment(val) if val in [e.value for e in ParagraphAlignment] else ParagraphAlignment.LEFT

        # Suffix
        suffix_elem = safe_find(elem, './/w:suff')
        if suffix_elem is not None:
            val = suffix_elem.get(f'{{{NS["w"]}}}val', 'tab')
            if val == 'space':
                level.suffix = NumberingLevelSuffix.SPACE
            elif val == 'nothing':
                level.suffix = NumberingLevelSuffix.NOTHING
            else:
                level.suffix = NumberingLevelSuffix.TAB

        # Indentation
        indent_elem = safe_find(elem, './/w:ind')
        if indent_elem is not None:
            level.indent_left = parse_dxa_to_points(indent_elem.get(f'{{{NS["w"]}}}left'))
            level.indent_hanging = parse_dxa_to_points(indent_elem.get(f'{{{NS["w"]}}}hanging'))

        # Font properties
        rpr_elem = safe_find(elem, './/w:rPr')
        if rpr_elem is not None:
            font_elem = safe_find(rpr_elem, './/w:rFonts')
            if font_elem is not None:
                level.font_name = font_elem.get(f'{{{NS["w"]}}}ascii') or font_elem.get(f'{{{NS["w"]}}}hAnsi')

            sz_elem = safe_find(rpr_elem, './/w:sz')
            if sz_elem is not None:
                level.font_size = parse_dxa_to_points(self._parse_int(sz_elem.get(f'{{{NS["w"]}}}val')))

            level.bold = safe_find(rpr_elem, './/w:b') is not None
            level.italic = safe_find(rpr_elem, './/w:i') is not None

        return level


    def _parse_numbering_instance(
        self,
        elem: ET.Element,
        definitions: dict[str, DOCXNumberingDefinition]
    ) -> DOCXNumberingInstance:
        num_id = elem.get(f'{{{NS["w"]}}}numId', '')

        instance = DOCXNumberingInstance(instance_id=num_id)

        abs_ref_elem = safe_find(elem, './/w:abstractNumId')
        if abs_ref_elem is not None:
            instance.abstract_definition_id = abs_ref_elem.get(f'{{{NS["w"]}}}val', '')

        for ovr_elem in safe_findall(elem, './/w:lvlOverride'):
            level_num = self._parse_int(ovr_elem.get(f'{{{NS["w"]}}}ilvl'))
            if level_num is not None:
                start_ovr_elem = safe_find(ovr_elem, './/w:startOverride')
                start_val = None
                if start_ovr_elem is not None:
                    start_val = self._parse_int(start_ovr_elem.get(f'{{{NS["w"]}}}val'))
                    if start_val is not None:
                        instance.start_overrides[level_num] = start_val

                lvl_elem = safe_find(ovr_elem, './/w:lvl')
                if lvl_elem is not None:
                    level = self._parse_numbering_level(lvl_elem, level_num)
                    instance.levels_overrides[level_num] = level
                elif start_val is not None and instance.abstract_definition_id:
                    base_def = definitions.get(instance.abstract_definition_id)
                    if base_def and level_num in base_def.levels:
                        base_lvl = base_def.levels[level_num]
                        level = DOCXNumberingLevel(
                            level=level_num,
                            start=start_val,
                            format=base_lvl.format,
                            text_template=base_lvl.text_template,
                            alignment=base_lvl.alignment,
                            suffix=base_lvl.suffix,
                            indent_left=base_lvl.indent_left,
                            indent_hanging=base_lvl.indent_hanging,
                            font_name=base_lvl.font_name,
                            font_size=base_lvl.font_size,
                            bold=base_lvl.bold,
                            italic=base_lvl.italic
                        )
                        instance.levels_overrides[level_num] = level

        return instance
