"""
Worksheet XML writer for XLSX.
Generates sheetX.xml files with rows, cells, formulas, merged cells, hyperlinks,
data validations, conditional formatting, tables references, and drawings.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ....models.esdm_models import Worksheet, Workbook
    from ..base import ESDMBaseWriter

from .const import XML_NAMESPACES
from .data_validation_writer import DataValidationWriter
from .conditional_formatting_writer import ConditionalFormattingWriter
from .extra_writers import HyperlinkWriter, CommentWriter
from .drawing_writer import DrawingsWriter


class WorksheetWriter:
    """
    Writes worksheet XML and collects relationships.
    Delegates data validations, conditional formatting, hyperlinks, comments, and drawings
    to dedicated sub-writers.
    """

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer
        self._dv_writer = DataValidationWriter(parent_writer)
        self._cf_writer = ConditionalFormattingWriter(parent_writer)
        self._hyperlink_writer = HyperlinkWriter(parent_writer)
        self._comment_writer = CommentWriter(parent_writer)
        self._drawing_writer = DrawingsWriter(parent_writer)

    def write(self, worksheet: Worksheet, sheet_index: int, workbook: Workbook) -> tuple[str, list[tuple[str, str, str]]]:
        """
        Generate the sheetX.xml content and the list of relationships for this worksheet.
        Returns (xml_string, relationships_list).
        """
        root = ET.Element('worksheet', {'xmlns': XML_NAMESPACES['']})
        rels: list[tuple[str, str, str]] = []

        # 1. Dimension
        dim = self._get_sheet_dimension(worksheet)
        if dim:
            ET.SubElement(root, 'dimension', {'ref': dim})

        # 2. Sheet views
        sheet_views = ET.SubElement(root, 'sheetViews')
        show_grid = '1' if getattr(worksheet.properties, 'show_gridlines', True) else '0'
        view_attrs: dict[str, str] = {
            'workbookViewId': '0',
            'showGridLines': show_grid,
        }
        if worksheet.properties.tab_color:
            view_attrs['tabSelected'] = '1'
        sheet_view = ET.SubElement(sheet_views, 'sheetView', view_attrs)
        if worksheet.properties.tab_color:
            color_normalized = self._normalize_color(worksheet.properties.tab_color)
            if color_normalized:
                ET.SubElement(sheet_view, 'tabColor', {'rgb': color_normalized})

        # 3. Sheet format defaults
        ET.SubElement(root, 'sheetFormatPr', {
            'defaultRowHeight': '15',
            'baseColWidth': '10'
        })

        # 4. Columns
        if worksheet.columns:
            cols = ET.SubElement(root, 'cols')
            for col in worksheet.columns.values():
                col_attrs = {
                    'min': str(col.index),
                    'max': str(col.index),
                    'width': str(col.width) if col.width is not None else '10.0',
                    'hidden': '1' if col.hidden else '0'
                }
                if hasattr(col, 'style_id') and col.style_id is not None:
                    col_attrs['style'] = str(col.style_id)
                ET.SubElement(cols, 'col', col_attrs)

        # 5. Sheet data (rows and cells)
        sheet_data = ET.SubElement(root, 'sheetData')
        for row_idx in sorted(worksheet.rows.keys()):
            row = worksheet.rows[row_idx]
            row_attrs = {
                'r': str(row_idx),
                'ht': str(row.height) if row.height is not None else '15',
                'hidden': '1' if row.hidden else '0'
            }
            if hasattr(row, 'style_id') and row.style_id is not None:
                row_attrs['s'] = str(row.style_id)
            row_elem = ET.SubElement(sheet_data, 'row', row_attrs)
            for col_idx in sorted(row.cells.keys()):
                cell = row.cells[col_idx]
                cell_elem = self._write_cell(cell, row_idx, col_idx, sheet_index, workbook, rels)
                if cell_elem is not None:
                    row_elem.append(cell_elem)

        # 6. Merged cells
        if worksheet.merged_cells:
            merge_cells = ET.SubElement(root, 'mergeCells')
            for mc in worksheet.merged_cells:
                ET.SubElement(merge_cells, 'mergeCell', {'ref': self._range_to_ref(mc)})

        # 7. Data validations
        dv_elem = self._dv_writer.write(worksheet)
        if dv_elem is not None:
            root.append(dv_elem)

        # 8. Conditional formatting
        cf_elems = self._cf_writer.write(worksheet)
        for cf_elem in cf_elems:
            root.append(cf_elem)

        # 9. Hyperlinks (and their relationships)
        if worksheet.hyperlinks:
            hyperlinks_elem, hyperlink_rels = self._hyperlink_writer.write_hyperlinks_and_rels(
                worksheet.hyperlinks, sheet_index
            )
            for hl_elem in hyperlinks_elem:
                root.append(hl_elem)
            rels.extend(hyperlink_rels)

        # 10. Comments (legacy VML)
        legacy_comments = getattr(worksheet, 'comments', None)
        if legacy_comments and legacy_comments.comments:
            vml_drawing_xml = self._comment_writer.write_legacy_comments_vml(
                legacy_comments.comments, sheet_index
            )
            if vml_drawing_xml:
                vml_path = f'xl/drawings/vmlDrawing{sheet_index}.vml'
                if not hasattr(self._parent, '_extra_parts'):
                    self._parent._extra_parts = {}
                self._parent._extra_parts[vml_path] = vml_drawing_xml
                vml_rel_id = f'vml_{sheet_index}'
                rels.append((vml_rel_id, f'../drawings/vmlDrawing{sheet_index}.vml',
                            'http://schemas.openxmlformats.org/officeDocument/2006/relationships/vmlDrawing'))

        # 11. Drawings (images, charts, shapes)
        drawing_xml, drawing_rels = self._drawing_writer.write_drawing(worksheet, sheet_index, workbook)
        if drawing_xml and drawing_rels:
            drawing_path = f'xl/drawings/drawing{sheet_index}.xml'
            if not hasattr(self._parent, '_extra_parts'):
                self._parent._extra_parts = {}
            self._parent._extra_parts[drawing_path] = drawing_xml
            drawing_rel_id = f'drawing_{sheet_index}'
            rels.append((drawing_rel_id, f'../drawings/drawing{sheet_index}.xml',
                        'http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing'))
            drawing_ref = ET.SubElement(root, 'drawing')
            ET.SubElement(drawing_ref, 'r:id', {'r:id': drawing_rel_id})

        # 12. AutoFilter (if present)
        if hasattr(worksheet, 'auto_filter') and worksheet.auto_filter and worksheet.auto_filter.ref:
            ET.SubElement(root, 'autoFilter', {'ref': worksheet.auto_filter.ref})

        # 13. Page setup
        if worksheet.page_setup:
            ps = ET.SubElement(root, 'pageSetup')
            ps.set('orientation', worksheet.page_setup.orientation.value)
            ps.set('scale', str(worksheet.page_setup.scale))
            ps.set('paperSize', str(worksheet.page_setup.paper_size))
            if worksheet.page_setup.fit_to_width:
                ps.set('fitToWidth', str(worksheet.page_setup.fit_to_width))
            if worksheet.page_setup.fit_to_height:
                ps.set('fitToHeight', str(worksheet.page_setup.fit_to_height))

        # 14. Page margins
        if worksheet.margins:
            margins = worksheet.margins
            ET.SubElement(root, 'pageMargins', {
                'left': str(margins.left),
                'right': str(margins.right),
                'top': str(margins.top),
                'bottom': str(margins.bottom),
                'header': str(margins.header),
                'footer': str(margins.footer)
            })

        xml_str = ET.tostring(root, encoding='unicode', xml_declaration=True)
        return xml_str, rels

    # ------------------------------------------------------------------
    # Cell writing (formats, formulas, values, rich text)
    # ------------------------------------------------------------------
    def _write_cell(self, cell, row: int, col: int, sheet_idx: int,
                   workbook: Workbook, rels: list) -> ET.Element | None:
        """Create <c> element for a cell."""
        if cell.value is None and not cell.formula and not cell.rich_text:
            return None

        attrs = {'r': f"{self._col_letter(col)}{row}"}
        # Determine type and style
        if cell.formula:
            attrs['t'] = 'str' if isinstance(cell.value, str) else 'n'
        elif isinstance(cell.value, str):
            attrs['t'] = 's'
        elif isinstance(cell.value, bool):
            attrs['t'] = 'b'
        else:
            attrs['t'] = 'n'

        if cell.style_id is not None:
            attrs['s'] = str(cell.style_id)

        cell_elem = ET.Element('c', attrs)

        # Formula
        if cell.formula:
            f_elem = ET.SubElement(cell_elem, 'f')
            formula_text = cell.formula
            if formula_text.startswith('='):
                formula_text = formula_text[1:]
            f_elem.text = formula_text
            if hasattr(cell, 'formula_array') and cell.formula_array:
                f_elem.set('t', 'array')
                if hasattr(cell, 'formula_ref') and cell.formula_ref:
                    f_elem.set('ref', cell.formula_ref)

        # Value
        if cell.value is not None:
            v_elem = ET.SubElement(cell_elem, 'v')
            v_elem.text = self._format_cell_value(cell)

        # Rich text (inline string) – only if not using shared strings
        if cell.rich_text and not self._parent._esdm_options.use_shared_strings:
            is_elem = ET.SubElement(cell_elem, 'is')
            for run in cell.rich_text.spans:
                r_elem = ET.SubElement(is_elem, 'r')
                if run.character_style:
                    rPr = ET.SubElement(r_elem, 'rPr')
                    self._write_run_properties(rPr, run.character_style)
                t_elem = ET.SubElement(r_elem, 't')
                t_elem.text = run.text

        return cell_elem

    def _write_run_properties(self, rPr: ET.Element, style):
        """Convert CharacterStyle to XML run properties."""
        if style.bold:
            ET.SubElement(rPr, 'b')
        if style.italic:
            ET.SubElement(rPr, 'i')
        if style.underline:
            ET.SubElement(rPr, 'u')
        if style.strike:
            ET.SubElement(rPr, 'strike')
        if style.color:
            color_val = self._normalize_color(style.color)
            if color_val:
                ET.SubElement(rPr, 'color', {'rgb': color_val})
        if style.font:
            ET.SubElement(rPr, 'rFont', {'val': style.font})
        if style.size:
            ET.SubElement(rPr, 'sz', {'val': str(style.size)})

    def _format_cell_value(self, cell) -> str:
        if cell.value is None:
            return ''
        if isinstance(cell.value, bool):
            return '1' if cell.value else '0'
        if isinstance(cell.value, datetime):
            base = datetime(1899, 12, 30)
            delta = cell.value - base
            return str(delta.total_seconds() / 86400)
        if isinstance(cell.value, str):
            if self._parent._esdm_options.use_shared_strings:
                idx = self._parent._add_shared_string(cell.value)
                return str(idx)
            else:
                return cell.value
        return str(cell.value)

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    def _get_sheet_dimension(self, worksheet: Worksheet) -> str | None:
        if not worksheet.rows:
            return None
        min_row = min(worksheet.rows.keys())
        max_row = max(worksheet.rows.keys())
        min_col = 1
        max_col = 1
        for row in worksheet.rows.values():
            if row.cells:
                min_col = min(min_col, min(row.cells.keys()))
                max_col = max(max_col, max(row.cells.keys()))
        return f"{self._col_letter(min_col)}{min_row}:{self._col_letter(max_col)}{max_row}"

    def _range_to_ref(self, rng):
        return f"{self._col_letter(rng.min_col)}{rng.min_row}:{self._col_letter(rng.max_col)}{rng.max_row}"

    def _col_letter(self, col_num: int) -> str:
        result = ''
        while col_num > 0:
            col_num, remainder = divmod(col_num - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def _normalize_color(self, color: str | None) -> str | None:
        if color is None:
            return None
        color = color.lstrip('#').upper()
        if len(color) == 3:
            color = ''.join([c*2 for c in color])
        return color if len(color) == 6 else None
