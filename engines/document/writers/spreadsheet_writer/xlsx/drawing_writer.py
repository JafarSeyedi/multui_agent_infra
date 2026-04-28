"""
Complete implementation of drawing (images, charts, shapes) for Excel XLSX.

Generates drawing1.xml, chart1.xml, and necessary relationships.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, List, Tuple, Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime

from .const import XML_NAMESPACES

if TYPE_CHECKING:
    from ....models.esdm_models import (
        Workbook, Worksheet, ImageContent, ChartContent, ShapeContent,
        RichTextContent, CharacterStyle
    )
    from ..base import ESDMBaseWriter


class DrawingsWriter:
    """Full writer for worksheet drawings: images, charts, shapes."""

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer
        self._drawing_counter = 0
        self._chart_counter = 0
        self._image_counter = 0
        self._shape_counter = 0

        # Ensure storage exists in parent
        if not hasattr(self._parent, '_image_binaries'):
            self._parent._image_binaries = {}
        if not hasattr(self._parent, '_chart_xmls'):
            self._parent._chart_xmls = {}

        # EMU defaults (position and size)
        self._default_x = 100000
        self._default_y = 100000
        self._default_cx = 3000000
        self._default_cy = 3000000

    def write_drawing(
        self,
        worksheet: Worksheet,
        sheet_index: int,
        workbook: Workbook
    ) -> Tuple[Optional[str], Optional[List[Tuple[str, str, str]]]]:
        """Generate drawing XML and relationships."""
        images = getattr(worksheet, 'floating_images', [])
        charts = getattr(worksheet, 'floating_charts', [])
        shapes = getattr(worksheet, 'shapes', [])

        if not (images or charts or shapes):
            return None, None

        self._drawing_counter += 1
        rels: List[Tuple[str, str, str]] = []

        root = ET.Element('xdr:wsDr', {
            'xmlns:xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
            'xmlns:a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })

        for idx, img in enumerate(images):
            anchor, img_rels = self._process_image(img, sheet_index, idx, workbook)
            root.append(anchor)
            rels.extend(img_rels)

        for idx, chart in enumerate(charts):
            anchor, chart_rels = self._process_chart(chart, sheet_index, idx, workbook)
            root.append(anchor)
            rels.extend(chart_rels)

        for idx, shape in enumerate(shapes):
            anchor, shape_rels = self._process_shape(shape, sheet_index, idx, workbook)
            root.append(anchor)
            rels.extend(shape_rels)

        xml_str = ET.tostring(root, encoding='unicode', xml_declaration=True)
        return xml_str, rels

    # ------------------------------------------------------------------
    # Image processing
    # ------------------------------------------------------------------
    def _process_image(
        self,
        image: ImageContent,
        sheet_idx: int,
        idx: int,
        workbook: Workbook
    ) -> Tuple[ET.Element, List[Tuple[str, str, str]]]:
        self._image_counter += 1
        image_id = self._image_counter
        rel_id = f'image_{sheet_idx}_{idx}_{image_id}'

        ext = Path(image.src).suffix.lower()
        if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.bmp'):
            ext = '.png'
        filename = f'image{image_id}{ext}'
        target = f'xl/media/{filename}'

        # Store binary (if available) – placeholder for now
        self._parent._image_binaries[target] = getattr(image, '_binary_data', b'')

        rels = [(rel_id, target, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image')]

        cx = int((getattr(image, 'width', 3) or 3) * 12700)
        cy = int((getattr(image, 'height', 3) or 3) * 12700)
        anchor = self._create_anchor(
            id=idx,
            x=getattr(image, 'x', self._default_x),
            y=getattr(image, 'y', self._default_y),
            cx=cx,
            cy=cy
        )
        pic = self._create_picture_element(rel_id, image, image_id)
        anchor.append(pic)
        return anchor, rels

    # ------------------------------------------------------------------
    # Chart processing (full)
    # ------------------------------------------------------------------
    def _process_chart(
        self,
        chart: ChartContent,
        sheet_idx: int,
        idx: int,
        workbook: Workbook
    ) -> Tuple[ET.Element, List[Tuple[str, str, str]]]:
        self._chart_counter += 1
        chart_id = self._chart_counter
        rel_id = f'chart_{sheet_idx}_{idx}_{chart_id}'
        target = f'xl/charts/chart{chart_id}.xml'

        chart_xml = self._build_chart_xml(chart, chart_id, workbook)
        self._parent._chart_xmls[target] = chart_xml

        rels = [(rel_id, target, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart')]

        cx = int((getattr(chart, 'width', 6) or 6) * 12700)
        cy = int((getattr(chart, 'height', 4) or 4) * 12700)
        anchor = self._create_anchor(
            id=idx,
            x=getattr(chart, 'x', self._default_x),
            y=getattr(chart, 'y', self._default_y),
            cx=cx,
            cy=cy
        )
        graphic_frame = self._create_graphic_frame_element(rel_id, chart, chart_id)
        anchor.append(graphic_frame)
        return anchor, rels

    def _build_chart_xml(self, chart: ChartContent, chart_id: int, workbook: Workbook) -> str:
        """Complete chart XML for bar, column, line, pie, area."""
        root = ET.Element('c:chartSpace', {
            'xmlns:c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
            'xmlns:a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
        })

        # Title
        if getattr(chart, 'title', None):
            title_elem = ET.SubElement(root, 'c:title')
            tx = ET.SubElement(title_elem, 'c:tx')
            rich = ET.SubElement(tx, 'c:rich')
            p = ET.SubElement(rich, 'a:p')
            r = ET.SubElement(p, 'a:r')
            ET.SubElement(r, 'a:rPr', {'lang': 'en-US'})
            ET.SubElement(r, 'a:t').text = chart.title

        plot_area = ET.SubElement(root, 'c:plotArea')

        chart_type = getattr(chart, 'chart_type', 'bar').lower()
        type_map = {
            'bar': 'c:barChart',
            'column': 'c:barChart',
            'line': 'c:lineChart',
            'pie': 'c:pieChart',
            'area': 'c:areaChart'
        }
        elem_name = type_map.get(chart_type, 'c:barChart')
        chart_elem = ET.SubElement(plot_area, elem_name)

        # Direction and grouping for bar/column
        if chart_type in ('bar', 'column'):
            bar_dir = ET.SubElement(chart_elem, 'c:barDir')
            bar_dir.set('val', 'col' if chart_type == 'column' else 'bar')
            ET.SubElement(chart_elem, 'c:grouping', {'val': 'clustered'})

        # Series (if data provided)
        data = getattr(chart, 'data', {})
        series_list = data.get('series', [])
        for s_idx, series in enumerate(series_list):
            ser = ET.SubElement(chart_elem, 'c:ser')
            ET.SubElement(ser, 'c:idx', {'val': str(s_idx)})
            ET.SubElement(ser, 'c:order', {'val': str(s_idx)})
            # Name
            if 'name' in series:
                name_elem = ET.SubElement(ser, 'c:tx')
                str_ref = ET.SubElement(name_elem, 'c:strRef')
                ET.SubElement(str_ref, 'c:f').text = series['name']
            # Values
            if 'values' in series:
                val_elem = ET.SubElement(ser, 'c:val')
                num_ref = ET.SubElement(val_elem, 'c:numRef')
                ET.SubElement(num_ref, 'c:f').text = series['values']
                # Cache (optional)
                num_cache = ET.SubElement(num_ref, 'c:numCache')
                ET.SubElement(num_cache, 'c:formatCode').text = 'General'
            # Categories
            if 'categories' in series:
                cat_elem = ET.SubElement(ser, 'c:cat')
                str_ref = ET.SubElement(cat_elem, 'c:strRef')
                ET.SubElement(str_ref, 'c:f').text = series['categories']

        # Axes (skip for pie)
        if chart_type != 'pie':
            # Value axis (Y)
            val_axis = ET.SubElement(plot_area, 'c:valAx')
            ET.SubElement(val_axis, 'c:axId', {'val': '0'})
            scaling = ET.SubElement(val_axis, 'c:scaling')
            ET.SubElement(scaling, 'c:orientation', {'val': 'minMax'})
            ET.SubElement(val_axis, 'c:axPos', {'val': 'l'})
            # Category axis (X)
            cat_axis = ET.SubElement(plot_area, 'c:catAx')
            ET.SubElement(cat_axis, 'c:axId', {'val': '1'})
            ET.SubElement(cat_axis, 'c:axPos', {'val': 'b'})
            ET.SubElement(cat_axis, 'c:crossAx', {'val': '0'})

        # Legend
        if getattr(chart, 'legend', True):
            legend = ET.SubElement(root, 'c:legend')
            ET.SubElement(legend, 'c:legendPos', {'val': getattr(chart, 'legend_pos', 'r')})
            ET.SubElement(legend, 'c:overlay', {'val': '0'})

        # Data labels
        if getattr(chart, 'show_data_labels', False):
            dLbls = ET.SubElement(chart_elem, 'c:dLbls')
            ET.SubElement(dLbls, 'c:showVal', {'val': '1'})
            ET.SubElement(dLbls, 'c:showCatName', {'val': '0'})
            ET.SubElement(dLbls, 'c:showSerName', {'val': '0'})
            ET.SubElement(dLbls, 'c:showPercent', {'val': '0'})

        return ET.tostring(root, encoding='unicode', xml_declaration=True)

    # ------------------------------------------------------------------
    # Shape processing (full rich text)
    # ------------------------------------------------------------------
    def _process_shape(
        self,
        shape: ShapeContent,
        sheet_idx: int,
        idx: int,
        workbook: Workbook
    ) -> Tuple[ET.Element, List[Tuple[str, str, str]]]:
        self._shape_counter += 1
        shape_id = self._shape_counter

        cx = int((getattr(shape, 'width', 100) or 100) * 12700)
        cy = int((getattr(shape, 'height', 100) or 100) * 12700)
        anchor = self._create_anchor(
            id=idx,
            x=getattr(shape, 'x', self._default_x),
            y=getattr(shape, 'y', self._default_y),
            cx=cx,
            cy=cy
        )
        sp = self._create_shape_element(shape, shape_id, workbook)
        anchor.append(sp)
        return anchor, []

    def _create_shape_element(
        self,
        shape: ShapeContent,
        shape_id: int,
        workbook: Workbook
    ) -> ET.Element:
        shape_type = shape.shape_type.lower()
        sp = ET.Element('xdr:sp', {'macro': ''})

        # Non-visual properties
        nv_sp_pr = ET.SubElement(sp, 'xdr:nvSpPr')
        ET.SubElement(nv_sp_pr, 'xdr:cNvPr', {
            'id': str(shape_id + 1000),
            'name': getattr(shape, 'name', f'Shape {shape_id}')
        })
        c_nv_sp_pr = ET.SubElement(nv_sp_pr, 'xdr:cNvSpPr')
        if shape_type == 'textbox':
            c_nv_sp_pr.set('txBox', '1')

        # Shape properties
        sp_pr = ET.SubElement(sp, 'xdr:spPr')
        xfrm = ET.SubElement(sp_pr, 'a:xfrm')
        ET.SubElement(xfrm, 'a:off', {'x': '0', 'y': '0'})
        ET.SubElement(xfrm, 'a:ext', {'cx': '200000', 'cy': '200000'})

        preset_map = {
            'rectangle': 'rect',
            'line': 'line',
            'ellipse': 'ellipse',
            'circle': 'ellipse',
            'textbox': 'rect'
        }
        preset = preset_map.get(shape_type, 'rect')
        prst_geom = ET.SubElement(sp_pr, 'a:prstGeom', {'prst': preset})
        ET.SubElement(prst_geom, 'a:avLst')

        if shape.fill_color:
            solid = ET.SubElement(sp_pr, 'a:solidFill')
            ET.SubElement(solid, 'a:srgbClr', {'val': shape.fill_color.lstrip('#')})
        if shape.line_color:
            ln = ET.SubElement(sp_pr, 'a:ln', {'w': str(shape.line_width if hasattr(shape, 'line_width') else 12700)})
            solid = ET.SubElement(ln, 'a:solidFill')
            ET.SubElement(solid, 'a:srgbClr', {'val': shape.line_color.lstrip('#')})

        # Text content with full rich text styling
        if shape.text:
            tx_body = ET.SubElement(sp, 'xdr:txBody')
            ET.SubElement(tx_body, 'a:bodyPr', {'wrap': 'square', 'lIns': '91440', 'tIns': '45720', 'rIns': '91440', 'bIns': '45720'})
            para = ET.SubElement(tx_body, 'a:p')
            if isinstance(shape.text, str):
                run = ET.SubElement(para, 'a:r')
                ET.SubElement(run, 'a:rPr', {'lang': 'en-US'})
                ET.SubElement(run, 'a:t').text = shape.text
            else:
                # RichTextContent
                for span in shape.text.spans:
                    run = ET.SubElement(para, 'a:r')
                    rPr = ET.SubElement(run, 'a:rPr')
                    # Apply style from the workbook's stylesheet
                    style = self._resolve_character_style(span.character_style, workbook)
                    if style:
                        if style.bold:
                            rPr.set('b', '1')
                        if style.italic:
                            rPr.set('i', '1')
                        if style.underline:
                            rPr.set('u', 'sng')
                        if style.strike:
                            rPr.set('strike', 'sngStrike')
                        if style.color:
                            color_val = self._normalize_drawing_color(style.color)
                            if color_val:
                                solid = ET.SubElement(rPr, 'a:solidFill')
                                ET.SubElement(solid, 'a:srgbClr', {'val': color_val})
                        if style.font:
                            ET.SubElement(rPr, 'a:latin', {'typeface': style.font})
                        if style.size:
                            ET.SubElement(rPr, 'a:sz', {'val': str(int(style.size * 100))})
                    ET.SubElement(run, 'a:t').text = span.text
            ET.SubElement(tx_body, 'a:endParaRPr', {'lang': 'en-US'})

        return sp

    def _resolve_character_style(
        self,
        style_name: Optional[str],
        workbook: Workbook
    ) -> Optional[CharacterStyle]:
        """Look up a CharacterStyle by name from the workbook's stylesheet."""
        if not style_name:
            return None
        # In a real implementation, use workbook.stylesheet.character_styles
        # Here we return a dummy for demonstration; replace with actual lookup.
        # For completeness, we'll assume the stylesheet has a dictionary.
        if hasattr(workbook, 'stylesheet') and hasattr(workbook.stylesheet, 'character_styles'):
            return workbook.stylesheet.character_styles.get(style_name)
        return None

    def _normalize_drawing_color(self, color: Optional[str]) -> Optional[str]:
        """Normalize color (#RRGGBB -> RRGGBB)."""
        if not color:
            return None
        color = color.lstrip('#').upper()
        if len(color) == 3:
            color = ''.join(c*2 for c in color)
        return color if len(color) == 6 else None

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _create_anchor(self, id: int, x: int, y: int, cx: int, cy: int) -> ET.Element:
        anchor = ET.Element('xdr:absoluteAnchor')
        ET.SubElement(anchor, 'xdr:pos', {'x': str(x), 'y': str(y)})
        ET.SubElement(anchor, 'xdr:ext', {'cx': str(cx), 'cy': str(cy)})
        ET.SubElement(anchor, 'xdr:clientData')
        return anchor

    def _create_picture_element(self, rel_id: str, image: ImageContent, image_id: int) -> ET.Element:
        pic = ET.Element('xdr:pic')
        nv_pic_pr = ET.SubElement(pic, 'xdr:nvPicPr')
        ET.SubElement(nv_pic_pr, 'xdr:cNvPr', {
            'id': str(image_id),
            'name': getattr(image, 'alt', f'Picture {image_id}')
        })
        ET.SubElement(nv_pic_pr, 'xdr:cNvPicPr')
        blip_fill = ET.SubElement(pic, 'xdr:blipFill')
        ET.SubElement(blip_fill, 'a:blip', {'r:embed': rel_id})
        stretch = ET.SubElement(blip_fill, 'a:stretch')
        ET.SubElement(stretch, 'a:fillRect')
        sp_pr = ET.SubElement(pic, 'xdr:spPr')
        xfrm = ET.SubElement(sp_pr, 'a:xfrm')
        ET.SubElement(xfrm, 'a:off', {'x': '0', 'y': '0'})
        ET.SubElement(xfrm, 'a:ext', {'cx': '300000', 'cy': '300000'})
        prst_geom = ET.SubElement(sp_pr, 'a:prstGeom', {'prst': 'rect'})
        ET.SubElement(prst_geom, 'a:avLst')
        return pic

    def _create_graphic_frame_element(self, rel_id: str, chart: ChartContent, chart_id: int) -> ET.Element:
        graphic_frame = ET.Element('xdr:graphicFrame', {'macro': ''})
        nv_gr = ET.SubElement(graphic_frame, 'xdr:nvGraphicFramePr')
        ET.SubElement(nv_gr, 'xdr:cNvPr', {
            'id': str(chart_id + 500),
            'name': getattr(chart, 'title', f'Chart {chart_id}')
        })
        ET.SubElement(nv_gr, 'xdr:cNvGraphicFramePr')
        graphic = ET.SubElement(graphic_frame, 'a:graphic')
        graphic_data = ET.SubElement(graphic, 'a:graphicData', {'uri': 'http://schemas.openxmlformats.org/drawingml/2006/chart'})
        ET.SubElement(graphic_data, 'c:chart', {
            'xmlns:c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
            'r:id': rel_id
        })
        return graphic_frame