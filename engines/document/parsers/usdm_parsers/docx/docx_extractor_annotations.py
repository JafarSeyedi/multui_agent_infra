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


class DOCXExtractorAnnotations:
    """Mixin providing DOCX extractor annotations methods."""

    def _resolve_diagrams(self, doc: DOCXDocument):
        """Resolve diagram relationship IDs, parse diagram XML, attach DOCXDiagram."""

        def _iter_drawings(content_list):
            for item in content_list:
                if isinstance(item, (DOCXParagraph,)):
                    for run_item in item.content.items:
                        if isinstance(run_item, DOCXDrawing):
                            yield run_item
                elif isinstance(item, DOCXTable):
                    for row in item.rows:
                        for cell in row.cells:
                            for cell_item in cell.content:
                                if isinstance(cell_item, DOCXParagraph):
                                    for run_item in cell_item.content.items:
                                        if isinstance(run_item, DOCXDrawing):
                                            yield run_item
                                elif isinstance(cell_item, DOCXTable):
                                    for inner_row in cell_item.rows:
                                        for inner_cell in inner_row.cells:
                                            for inner_item in inner_cell.content:
                                                if isinstance(inner_item, DOCXParagraph):
                                                    for r_item in inner_item.content.items:
                                                        if isinstance(r_item, DOCXDrawing):
                                                            yield r_item

        all_drawings = []
        all_drawings.extend(_iter_drawings(doc.body))
        for hf in doc.headers.values():
            all_drawings.extend(_iter_drawings(hf.content))
        for hf in doc.footers.values():
            all_drawings.extend(_iter_drawings(hf.content))

        doc_rels = self._relationships.get('document', {})
        for drawing in all_drawings:
            if drawing.drawing_type == 'diagram' and drawing.relationship_id:
                rel_target = doc_rels.get(drawing.relationship_id)
                if rel_target:
                    diagram_path = f'word/{rel_target}'
                    diagram_xml = self._get_xml_document(diagram_path)
                    if diagram_xml is not None:
                        drawing.diagram = parse_diagram(diagram_xml)


    def _resolve_charts(self, doc: DOCXDocument):
        """Resolve chart relationship IDs, parse chart XML, and attach ChartContent."""
        # Collect all drawings from paragraphs, headers, footers
        def _iter_drawings(content_list):
            for item in content_list:
                if isinstance(item, (DOCXParagraph,)):
                    for run_item in item.content.items:
                        if isinstance(run_item, DOCXDrawing):
                            yield run_item
                elif isinstance(item, DOCXTable):
                    for row in item.rows:
                        for cell in row.cells:
                            for cell_item in cell.content:
                                if isinstance(cell_item, DOCXParagraph):
                                    for run_item in cell_item.content.items:
                                        if isinstance(run_item, DOCXDrawing):
                                            yield run_item
                                elif isinstance(cell_item, DOCXTable):
                                    for inner_row in cell_item.rows:
                                        for inner_cell in inner_row.cells:
                                            for inner_item in inner_cell.content:
                                                if isinstance(inner_item, DOCXParagraph):
                                                    for r_item in inner_item.content.items:
                                                        if isinstance(r_item, DOCXDrawing):
                                                            yield r_item

        # Process all drawings in body, headers, footers
        all_drawings = []
        all_drawings.extend(_iter_drawings(doc.body))
        for hf in doc.headers.values():
            all_drawings.extend(_iter_drawings(hf.content))
        for hf in doc.footers.values():
            all_drawings.extend(_iter_drawings(hf.content))

        # Now for each chart drawing, resolve and parse
        doc_rels = self._relationships.get('document', {})
        for drawing in all_drawings:
            if drawing.drawing_type == 'chart' and drawing.relationship_id:
                rel_target = doc_rels.get(drawing.relationship_id)
                if rel_target:
                    # Target is relative to word/, e.g., 'charts/chart1.xml'
                    chart_path = f'word/{rel_target}'
                    chart_xml = self._get_xml_document(chart_path)
                    if chart_xml is not None:
                        drawing.chart = parse_docx_chart(chart_xml)

        # Also parse chart XML parts directly for chart relationship types
        self._extract_chart_xml_parts(doc)


    def _extract_chart_xml_parts(self, doc: DOCXDocument):
        """Extract chart XML parts referenced via chart relationship type."""
        self._relationships.get('document', {})
        chart_ns = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart'
        for rel_id, (target, rel_type) in self._get_typed_relationships('document', chart_ns):
            chart_path = f'word/{target}' if not target.startswith('word/') else target
            chart_xml = self._get_xml_document(chart_path)
            if chart_xml is not None:
                chart_data = self._parse_chart_xml_to_data(chart_xml, rel_id)
                doc.chart_data[rel_id] = chart_data


    def _parse_chart_xml_to_data(self, chart_xml: ET.Element, chart_id: str) -> DOCXChartData:
        """Parse chart XML into DOCXChartData."""
        C_NS = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
        A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        chart_data = DOCXChartData(chart_id=chart_id)

        chart_el = chart_xml.find(f'.//{{{C_NS}}}chart')
        if chart_el is None:
            return chart_data

        chart_data.chart_type, type_el = self._identify_chart_type(chart_el)

        if type_el is not None:
            chart_data.grouping = type_el.get('grouping')
            chart_data.direction = type_el.get('barDir')

        title_el = chart_el.find(f'.//{{{C_NS}}}title')
        if title_el is not None:
            rich = title_el.find(f'.//{{{C_NS}}}tx/{{{A_NS}}}rich')
            if rich is not None:
                parts = []
                for p in rich.findall(f'{{{A_NS}}}p'):
                    for r in p.findall(f'{{{A_NS}}}r'):
                        t = r.find(f'{{{A_NS}}}t')
                        if t is not None and t.text:
                            parts.append(t.text)
                chart_data.title = ''.join(parts)

        if type_el is not None:
            for ser in type_el.findall(f'{{{C_NS}}}ser'):
                series_data = {}
                name_el = ser.find(f'.//{{{C_NS}}}tx/{{{C_NS}}}strRef/{{{C_NS}}}f')
                if name_el is None:
                    name_el = ser.find(f'.//{{{C_NS}}}tx/{{{C_NS}}}v')
                if name_el is not None:
                    series_data['name'] = name_el.text or ''

                cat_f = ser.find(f'.//{{{C_NS}}}cat/{{{C_NS}}}strRef/{{{C_NS}}}f')
                if cat_f is None:
                    cat_f = ser.find(f'.//{{{C_NS}}}cat/{{{C_NS}}}numRef/{{{C_NS}}}f')
                if cat_f is not None:
                    series_data['categories_ref'] = cat_f.text

                val_f = ser.find(f'.//{{{C_NS}}}val/{{{C_NS}}}numRef/{{{C_NS}}}f')
                if val_f is None:
                    val_f = ser.find(f'.//{{{C_NS}}}val/{{{C_NS}}}strRef/{{{C_NS}}}f')
                if val_f is not None:
                    series_data['values_ref'] = val_f.text

                spPr = ser.find(f'{{{C_NS}}}spPr')
                if spPr is not None:
                    fill_el = spPr.find(f'.//{{{A_NS}}}solidFill/{{{A_NS}}}srgbClr')
                    if fill_el is not None:
                        series_data['fill_color'] = f"#{fill_el.get('val', '')}"

                chart_data.series.append(series_data)

        cat_ax = chart_el.find(f'.//{{{C_NS}}}catAx')
        val_ax = chart_el.find(f'.//{{{C_NS}}}valAx')
        if cat_ax is not None:
            chart_data.category_axis = self._parse_chart_axis_data(cat_ax)
        if val_ax is not None:
            chart_data.value_axis = self._parse_chart_axis_data(val_ax)

        return chart_data


    def _identify_chart_type(self, chart_el: ET.Element):
        C_NS = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
        for tag in [
            'barChart', 'lineChart', 'pieChart', 'areaChart', 'scatterChart',
            'radarChart', 'surfaceChart', 'bubbleChart', 'stockChart',
            'doughnutChart', 'ofPieChart',
        ]:
            el = chart_el.find(f'.//{{{C_NS}}}{tag}')
            if el is not None:
                return tag.replace('Chart', ''), el
        return 'unknown', None


    def _parse_chart_axis_data(self, axis_el: ET.Element) -> dict[str, Any]:
        C_NS = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
        axis_data: dict[str, Any] = {}
        scaling = axis_el.find(f'.//{{{C_NS}}}scaling')
        if scaling is not None:
            min_val = scaling.get('min')
            if min_val is not None:
                axis_data['min'] = float(min_val)
            max_val = scaling.get('max')
            if max_val is not None:
                axis_data['max'] = float(max_val)
        num_fmt = axis_el.find(f'{{{C_NS}}}numFmt')
        if num_fmt is not None:
            axis_data['format_code'] = num_fmt.get('formatCode')
        return axis_data


    def _collect_watermarks(self, doc: DOCXDocument):
        """Detect watermarks in header XML content."""
        for header in doc.headers.values():
            for para in header.content:
                if not isinstance(para, DOCXParagraph):
                    continue
                for item in para.content.items:
                    if not isinstance(item, DOCXDrawing):
                        continue
                    watermark = self._detect_watermark_in_drawing(item)
                    if watermark is not None:
                        header.watermarks.append(watermark)
                        doc.watermarks.append(watermark)


    def _detect_watermark_in_drawing(self, drawing: DOCXDrawing) -> DOCXWatermark | None:
        """Detect watermark properties from a drawing element."""
        watermark = DOCXWatermark()
        if drawing.description and 'watermark' in drawing.description.lower():
            watermark.text = drawing.name
            return watermark
        if drawing.name and 'watermark' in drawing.name.lower():
            watermark.text = drawing.name
            return watermark
        return None


    def _collect_complex_fields(self, doc: DOCXDocument):
        """Parse complex (multi-run) fields from document body."""
        for item in doc.body:
            if isinstance(item, DOCXParagraph):
                self._parse_complex_fields_in_paragraph(item, doc)
        for header in doc.headers.values():
            for item in header.content:
                if isinstance(item, DOCXParagraph):
                    self._parse_complex_fields_in_paragraph(item, doc)
        for footer in doc.footers.values():
            for item in footer.content:
                if isinstance(item, DOCXParagraph):
                    self._parse_complex_fields_in_paragraph(item, doc)


    def _parse_complex_fields_in_paragraph(self, para: DOCXParagraph, doc: DOCXDocument):
        """Parse complex fields within a paragraph's items."""
        in_field = False
        current_field = DOCXComplexField()

        for item in para.content.items:
            if isinstance(item, DOCXField):
                if item.field_type:
                    in_field = True
                    current_field.field_type = item.field_type
                    current_field.instruction = item.instruction or ''
                    if item.instruction:
                        pass
                    if item.field_type.upper() == 'TOC':
                        current_field.field_data['toc_switches'] = item.field_data.get('toc_switches', {})
                    if item.field_type.upper() in ('REF', 'PAGEREF', 'NOTEREF', 'FOOTNOTEREF'):
                        current_field.target_bookmark = item.target_bookmark
            elif in_field:
                if isinstance(item, DOCXTextRun) and item.text:
                    current_field.result = (current_field.result or '') + item.text
                elif isinstance(item, DOCXField) and item.result:
                    current_field.result = str(item.result)


    def _collect_toc_fields(self, doc: DOCXDocument):
        """Collect TOC field data from all paragraphs."""
        for item in doc.body:
            if isinstance(item, DOCXParagraph):
                self._parse_toc_in_paragraph(item, doc)


    def _parse_toc_in_paragraph(self, para: DOCXParagraph, doc: DOCXDocument):
        """Parse TOC field instructions and switches."""
        for item in para.content.items:
            if isinstance(item, DOCXField) and item.field_type.upper() == 'TOC':
                toc = DOCXTOCField()
                toc.instruction = item.instruction or ''
                toc.hyperlinks = '\\h' in (item.instruction or '')
                toc.hide_web_layout = '\\z' in (item.instruction or '')
                toc.use_paragraph_levels = '\\u' in (item.instruction or '')
                toc.preserve_tabs = '\\w' in (item.instruction or '')
                toc.preserve_newlines = '\\x' in (item.instruction or '')

                instr = item.instruction or ''
                o_match = re.search(r'\\o\s+"([^"]+)"', instr)
                if o_match:
                    range_str = o_match.group(1)
                    parts = range_str.split('-')
                    if len(parts) == 2:
                        try:
                            toc.heading_range = (int(parts[0]), int(parts[1]))
                        except ValueError:
                            pass

                t_match = re.search(r'\\t\s+"([^"]+)"', instr)
                if t_match:
                    styles_str = t_match.group(1)
                    pairs = styles_str.split(',')
                    for i in range(0, len(pairs) - 1, 2):
                        try:
                            toc.styles_included.append((pairs[i].strip(), int(pairs[i + 1])))
                        except (ValueError, IndexError):
                            pass

                n_match = re.search(r'\\n\s+"([^"]+)"', instr)
                if n_match:
                    toc.switches['suppress_page_numbers'] = n_match.group(1)

                b_match = re.search(r'\\b\s+"([^"]+)"', instr)
                if b_match:
                    toc.switches['bookmark_range'] = b_match.group(1)

                p_match = re.search(r'\\p\s+"([^"]+)"', instr)
                if p_match:
                    toc.switches['separator'] = p_match.group(1)

                l_match = re.search(r'\\l\s+"([^"]+)"', instr)
                if l_match:
                    toc.level_range = l_match.group(1)

                d_match = re.search(r'\\d\s+"([^"]+)"', instr)
                if d_match:
                    toc.switches['seq_separator'] = d_match.group(1)

                c_match = re.search(r'\\c\s+"([^"]+)"', instr)
                if c_match:
                    toc.switches['table_sequence'] = c_match.group(1)

                s_match = re.search(r'\\s\s+"([^"]+)"', instr)
                if s_match:
                    toc.switches['sequence_id'] = s_match.group(1)

                a_match = re.search(r'\\a\s+"([^"]+)"', instr)
                if a_match:
                    toc.switches['auto_labels'] = a_match.group(1)

                f_match = re.search(r'\\f\s*', instr)
                if f_match:
                    toc.switches['tc_entries'] = True

                item.toc_switches = toc.switches
                doc.toc_fields.append(toc)


