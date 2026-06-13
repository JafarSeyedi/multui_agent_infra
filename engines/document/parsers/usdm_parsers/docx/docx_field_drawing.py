# mypy: disable-error-code="attr-defined"

from __future__ import annotations

import json
from typing import Any

from ....models.base import ElementType
from ....models.usdm_models import (
    ChartAxisContent, ChartContent, ChartSeriesContent, CrossReference,
    DataContent, DrawingContent, FormFieldContent, ImageContent,
    LinkContent, ListStyle, LogicalElement, PageReferenceContent,
    RichTextContent, RichTextSpan, TOCContent,
)
from .docx_models import (
    DOCXChartData, DOCXDrawing, DOCXField, DOCXMath, DOCXParagraph,
    DOCXTable, DOCXTextRun, DOCXTOCField, DOCXWatermark, TextDirection,
)


class DOCXFieldDrawing:
    """Mixin providing DOCX field, TOC, chart, and drawing conversion methods."""

    def _apply_rtl_to_paragraph(self, para: DOCXParagraph, elem: LogicalElement) -> LogicalElement:
        if para.properties.text_direction == TextDirection.RTL:
            elem.metadata["text_direction"] = "rtl"
        else:
            elem.metadata["text_direction"] = "ltr"
        return elem

    def _apply_rtl_to_run(self, run: DOCXTextRun) -> dict[str, str]:
        metadata: dict[str, str] = {}
        additional = getattr(run.properties, 'additional_properties', {})
        if additional.get('rtl') is True or additional.get('bidi') is True:
            metadata["rtl"] = "true"
        return metadata

    def _apply_rtl_to_table(self, table: DOCXTable) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if table.properties:
            additional = getattr(table.properties, 'additional_properties', {})
            if additional.get('bidi_visual') is True:
                metadata["bidi_visual"] = True
        for row in table.rows:
            for cell in row.cells:
                if cell.properties.text_direction == TextDirection.RTL:
                    metadata["cell_rtl"] = True
                    break
        return metadata

    def _get_text_direction_value(self, direction_str: str | None) -> str:
        if direction_str is None:
            return "ltr"
        rtl_values = {'rl', 'tbRl', 'btLr', 'rl2lr'}
        vertical_values = {'lrTbV', 'tbRlV', 'tbLrV'}
        if direction_str in rtl_values:
            return "rtl"
        elif direction_str in vertical_values:
            return "vertical"
        return "ltr"

    def _convert_toc_fields(self) -> list[LogicalElement]:
        toc_elements: list[LogicalElement] = []
        assert self._docx_doc is not None
        for toc_field in self._docx_doc.toc_fields:
            toc_elem = self._convert_single_toc_field(toc_field)
            if toc_elem:
                toc_elements.append(toc_elem)
        return toc_elements

    def _convert_single_toc_field(self, toc_field: DOCXTOCField) -> LogicalElement | None:
        level = toc_field.heading_range[1] if toc_field.heading_range else 3
        content = TOCContent(label="Table of Contents", level=level, anchor_id="")
        metadata: dict[str, Any] = {
            "instruction": toc_field.instruction,
            "hyperlinks": toc_field.hyperlinks,
            "hide_web_layout": toc_field.hide_web_layout,
            "use_paragraph_levels": toc_field.use_paragraph_levels,
            "preserve_tabs": toc_field.preserve_tabs,
            "preserve_newlines": toc_field.preserve_newlines,
        }
        if toc_field.heading_range:
            metadata["heading_range"] = list(toc_field.heading_range)
        if toc_field.styles_included:
            metadata["styles_included"] = toc_field.styles_included
        if toc_field.level_range:
            metadata["level_range"] = toc_field.level_range
        if toc_field.switches:
            metadata["switches"] = toc_field.switches
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.TOC,
            content=content, metadata=metadata
        )

    def _convert_advanced_field(
        self, field: DOCXField
    ) -> DataContent | TOCContent | LinkContent | PageReferenceContent | CrossReference | FormFieldContent | None:
        if self._docx_doc is None:
            return None
        field_type = field.field_type.upper() if field.field_type else ""
        field_value = field.result
        if isinstance(field_value, DOCXMath):
            field_value = field_value.root.text if field_value.root and field_value.root.text else ""
        field_value_str = str(field_value) if field_value else ""

        if field_type in ("PAGE", "NUMPAGES", "SECTIONPAGES"):
            return DataContent(field_type=field_type, value=field_value_str, format=field.instruction)
        elif field_type in ("DATE", "TIME"):
            return DataContent(field_type=field_type, value=field_value_str, format=field.instruction)
        elif field_type == "SECTION":
            return DataContent(field_type="SECTION", value=field_value_str, format=field.instruction)
        elif field_type == "AUTHOR":
            return DataContent(
                field_type="AUTHOR",
                value=field_value_str or self._docx_doc.core_properties.creator or "", format=None
            )
        elif field_type == "TITLE":
            return DataContent(
                field_type="TITLE",
                value=field_value_str or (self._docx_doc.core_properties.title or "")
            )
        elif field_type == "TOC":
            return TOCContent(label="Table of Contents", level=3, anchor_id="")
        elif field_type == "HYPERLINK":
            target = field.hyperlink_target or ""
            text_content = RichTextContent(spans=[RichTextSpan(text=field_value_str)])
            return LinkContent(url=target, text=text_content)
        elif field_type in ("REF", "PAGEREF"):
            target_id = field.target_bookmark or field_value_str
            if field_type == "PAGEREF":
                return PageReferenceContent(target_id=target_id, display_text=field_value_str)
            return DataContent(field_type=field_type, value=field_value_str, format=field.instruction)
        elif field_type in ("NOTEREF", "FOOTNOTEREF"):
            return CrossReference(
                source_id="", target_id=field.target_bookmark or field_value_str,
                reference_type="footnote", context=field_value_str
            )
        elif field_type in ("SEQ", "STYLEREF"):
            return DataContent(field_type=field_type, value=field_value_str, format=field.instruction)
        elif field_type in ("INCLUDETEXT", "LINK"):
            return DataContent(field_type=field_type, value=field_value_str, format=field.instruction)
        elif field_type in ("FORMTEXT", "FORMCHECKBOX", "FORMDD"):
            return FormFieldContent(
                field_name=field.form_field_name or "",
                field_type=field.form_field_type or field_type.lower(),
                value=field_value_str, default_value=field.form_field_default or ""
            )
        elif field_type == "MERGEFIELD":
            return DataContent(
                field_type="MERGEFIELD", value=field_value_str,
                format=field.instruction, metadata={"merge_field": True}
            )
        elif field_type in ("CITATION", "BIBLIOGRAPHY"):
            return DataContent(field_type=field_type, value=field_value_str, format=field.instruction)
        return DataContent(field_type=field_type, value=field_value_str, format=field.instruction)

    def _convert_complex_field(
        self, field: DOCXField
    ) -> DataContent | TOCContent | LinkContent | PageReferenceContent | CrossReference | FormFieldContent | None:
        if not field.field_type:
            return None
        return self._convert_advanced_field(field)

    def _convert_field(
        self, field: DOCXField
    ) -> DataContent | LogicalElement | None:
        if self._docx_doc is None:
            return None
        field_type = field.field_type.upper() if field.field_type else ""
        field_value = field.result
        if isinstance(field_value, DOCXMath):
            field_value = field_value.root.text if field_value.root and field_value.root.text else ""
        if field_type in ("PAGE", "NUMPAGES", "SECTIONPAGES"):
            return DataContent(field_type=field_type, value=str(field_value), format=field.instruction)
        elif field_type == "DATE":
            return DataContent(field_type="DATE", value=str(field_value), format=field.instruction)
        elif field_type == "TIME":
            return DataContent(field_type="TIME", value=str(field_value), format=field.instruction)
        elif field_type == "AUTHOR":
            return DataContent(
                field_type="AUTHOR",
                value=str(field_value or self._docx_doc.core_properties.creator or ""), format=None
            )
        elif field_type == "TITLE":
            return DataContent(
                field_type="TITLE",
                value=str(field_value or (self._docx_doc.core_properties.title or ""))
            )
        return None

    def _convert_chart_xml_parts(self) -> list[LogicalElement]:
        chart_elements: list[LogicalElement] = []
        assert self._docx_doc is not None
        for rel_id, chart_data in self._docx_doc.chart_data.items():
            chart_elem = self._convert_single_chart_data(rel_id, chart_data)
            if chart_elem:
                chart_elements.append(chart_elem)
        return chart_elements

    def _convert_single_chart_data(self, rel_id: str, chart_data: DOCXChartData) -> LogicalElement | None:
        type_map = {
            'bar': 'bar', 'line': 'line', 'pie': 'pie', 'area': 'area',
            'scatter': 'scatter', 'radar': 'radar', 'surface': 'surface',
            'bubble': 'bubble', 'stock': 'stock', 'doughnut': 'doughnut',
            'ofPie': 'ofPie',
        }
        chart_type = type_map.get(chart_data.chart_type, chart_data.chart_type)
        series_list = [
            ChartSeriesContent(
                name=s.get('name'), categories_ref=s.get('categories_ref'),
                values_ref=s.get('values_ref'), fill_color=s.get('fill_color'),
                line_color=s.get('line_color'),
            )
            for s in chart_data.series
        ]
        cat_axis = ChartAxisContent(
            axis_type='category', title=None,
            min_value=chart_data.category_axis.get('min') if chart_data.category_axis else None,
            max_value=chart_data.category_axis.get('max') if chart_data.category_axis else None,
            format_code=chart_data.category_axis.get('format_code') if chart_data.category_axis else None,
        ) if chart_data.category_axis else None
        val_axis = ChartAxisContent(
            axis_type='value', title=None,
            min_value=chart_data.value_axis.get('min') if chart_data.value_axis else None,
            max_value=chart_data.value_axis.get('max') if chart_data.value_axis else None,
            format_code=chart_data.value_axis.get('format_code') if chart_data.value_axis else None,
        ) if chart_data.value_axis else None
        content = ChartContent(
            chart_type=chart_type, grouping=chart_data.grouping,
            direction=chart_data.direction, title=chart_data.title,
            series=series_list, category_axis=cat_axis, value_axis=val_axis,
            _chart_rId=rel_id,
        )
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.CHART, content=content,
            metadata={"relationship_id": rel_id, "chart_id": chart_data.chart_id}
        )

    def _convert_drawing(self, drawing: DOCXDrawing) -> LogicalElement | None:
        if drawing.drawing_type == "image":
            return self._convert_image_drawing(drawing)
        elif drawing.drawing_type == "chart":
            return self._convert_chart_drawing(drawing)
        elif drawing.drawing_type == "shape":
            return self._convert_shape_drawing(drawing)
        elif drawing.drawing_type == "diagram":
            return self._convert_diagram_drawing(drawing)
        return self._convert_image_drawing(drawing)

    def _convert_image_drawing(self, drawing: DOCXDrawing) -> LogicalElement | None:
        image_data = None
        assert self._docx_doc is not None
        if drawing.relationship_id in self._docx_doc.binary_parts:
            image_data = self._docx_doc.binary_parts[drawing.relationship_id]
        width = self._convert_emu_to_pixels(drawing.width) if drawing.width else None
        height = self._convert_emu_to_pixels(drawing.height) if drawing.height else None
        content = ImageContent(
            src=f"rel:{drawing.relationship_id}",
            width=width, height=height,
            alt=drawing.alt_text or drawing.description or drawing.name
        )
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.IMAGE, content=content,
            metadata={
                "relationship_id": drawing.relationship_id, "name": drawing.name,
                "description": drawing.description, "alt_text": drawing.alt_text,
                "width_emu": drawing.width, "height_emu": drawing.height,
                "has_image_data": image_data is not None,
            }
        )

    def _convert_chart_drawing(self, drawing: DOCXDrawing) -> LogicalElement | None:
        chart_content = drawing.chart or ChartContent(chart_type='bar', title=drawing.name)
        if drawing.width:
            chart_content.width = self._convert_emu_to_pixels(drawing.width)
        if drawing.height:
            chart_content.height = self._convert_emu_to_pixels(drawing.height)
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.CHART, content=chart_content,
            metadata={
                "relationship_id": drawing.relationship_id,
                "name": drawing.name, "description": drawing.description,
                "width_emu": drawing.width, "height_emu": drawing.height,
            }
        )

    def _convert_shape_drawing(self, drawing: DOCXDrawing) -> LogicalElement | None:
        content = drawing.shape
        if content is None:
            return None
        if drawing.width:
            content.width = int(self._convert_emu_to_pixels(drawing.width))
        if drawing.height:
            content.height = int(self._convert_emu_to_pixels(drawing.height))
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.SHAPE, content=content,
            metadata={
                "relationship_id": drawing.relationship_id, "name": drawing.name,
                "description": drawing.description,
                "width_emu": drawing.width, "height_emu": drawing.height,
            }
        )

    def _convert_diagram_drawing(self, drawing: DOCXDrawing) -> LogicalElement | None:
        diagram = drawing.diagram
        if diagram is None:
            return None
        width = self._convert_emu_to_pixels(drawing.width) if drawing.width else None
        height = self._convert_emu_to_pixels(drawing.height) if drawing.height else None

        def node_to_dict(node):
            if node is None:
                return None
            return {
                "id": node.id, "text": node.text, "shape": node.shape_type,
                "fill": node.fill_color, "line": node.line_color,
                "children": [node_to_dict(child) for child in node.children] if node.children else []
            }

        tree_dict = node_to_dict(diagram.root)
        vector_data = json.dumps({
            "type": diagram.layout_type or "unknown",
            "name": diagram.name or drawing.name,
            "root": tree_dict
        }, ensure_ascii=False)
        content = DrawingContent(vector_data=vector_data, width=width, height=height)
        return LogicalElement(
            element_id=self._generate_element_id(),
            element_type=ElementType.DRAWING, content=content,
            metadata={
                "relationship_id": drawing.relationship_id, "name": drawing.name,
                "description": drawing.description, "diagram_type": diagram.layout_type,
                "width_emu": drawing.width, "height_emu": drawing.height,
            }
        )

    def _convert_list_styles_with_overrides(self) -> dict[str, ListStyle]:
        list_styles: dict[str, ListStyle] = {}
        assert self._docx_doc is not None
        for abs_id, definition in self._docx_doc.numbering_definitions.items():
            style_name = definition.name or f"ListStyle_{abs_id}"
            level_styles: dict[int, dict[str, Any]] = {}
            for level_num, level_def in definition.levels.items():
                level_info = {
                    "format": level_def.format, "start": level_def.start,
                    "text_template": level_def.text_template,
                    "alignment": level_def.alignment.value if level_def.alignment else "left",
                    "indent_left": level_def.indent_left,
                    "indent_hanging": level_def.indent_hanging,
                    "font_name": level_def.font_name, "font_size": level_def.font_size,
                    "bold": level_def.bold, "italic": level_def.italic,
                    "suffix": level_def.suffix.value if level_def.suffix else "tab",
                    "is_legal": level_def.is_legal,
                }
                if level_def.paragraph_props:
                    level_info["paragraph_props"] = level_def.paragraph_props
                if level_def.run_props:
                    level_info["run_props"] = level_def.run_props
                if level_def.restart_condition:
                    level_info["restart_condition"] = level_def.restart_condition
                level_styles[level_num] = level_info
            list_styles[style_name] = ListStyle(name=style_name, level_styles=level_styles)

        for num_id, instance in self._docx_doc.numbering_instances.items():
            if instance.levels_overrides:
                override_style_name = f"ListOverride_{num_id}"
                override_levels: dict[int, dict[str, Any]] = {}
                for level_num, level_def in instance.levels_overrides.items():
                    override_levels[level_num] = {
                        "format": level_def.format, "start": level_def.start,
                        "text_template": level_def.text_template,
                        "alignment": level_def.alignment.value if level_def.alignment else "left",
                        "indent_left": level_def.indent_left,
                        "indent_hanging": level_def.indent_hanging,
                        "font_name": level_def.font_name, "font_size": level_def.font_size,
                        "bold": level_def.bold, "italic": level_def.italic,
                        "is_legal": level_def.is_legal,
                    }
                if override_levels:
                    list_styles[override_style_name] = ListStyle(
                        name=override_style_name, level_styles=override_levels
                    )
        return list_styles
