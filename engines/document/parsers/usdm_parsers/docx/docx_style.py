# mypy: disable-error-code="attr-defined"

from __future__ import annotations

from typing import Any

from ....models.usdm_models import (
    CharacterStyle, ListStyle, ParagraphStyle, StyleSheet, TableStyle,
)
from .docx_models import DOCXStyle, ParagraphAlignment


class DOCXStyleConverter:
    """Mixin providing DOCX style conversion methods."""

    def _convert_styles(self) -> StyleSheet:
        """Convert DOCX styles to USDM StyleSheet."""
        style_sheet = StyleSheet()
        assert self._docx_doc is not None, "Document not extracted"
        for style_id, docx_style in self._docx_doc.styles.items():
            if docx_style.style_type == "character":
                char_style = self._convert_character_style(docx_style)
                if char_style:
                    style_sheet.character_styles[docx_style.name or style_id] = char_style

            elif docx_style.style_type == "paragraph":
                para_style = self._convert_paragraph_style(docx_style)
                if para_style:
                    style_sheet.paragraph_styles[docx_style.name or style_id] = para_style

            elif docx_style.style_type == "table":
                table_style = self._convert_table_style(docx_style)
                if table_style:
                    style_sheet.table_styles[docx_style.name or style_id] = table_style

        # Convert list styles from numbering definitions
        list_styles = self._convert_list_styles()
        style_sheet.list_styles.update(list_styles)

        return style_sheet


    def _convert_character_style(self, docx_style: DOCXStyle) -> CharacterStyle | None:
        """
        Convert DOCX character style to USDM CharacterStyle with all properties.
        
        Args:
            docx_style: DOCXStyle object
            
        Returns:
            CharacterStyle object or None
        """
        if not docx_style.run_properties:
            return None

        props = docx_style.run_properties.properties
        additional_properties=getattr(props, 'additional_properties', {})
        # Map theme colors if used
        color = self._resolve_theme_color(
            props.color,
            additional_properties.get('theme_color'),
            additional_properties.get('theme_tint'),
            additional_properties.get('theme_shade')
        )

        highlight_color = self._resolve_theme_color(
            props.highlight,
            additional_properties.get('highlight_theme_color')
        )

        # Build comprehensive character style
        return CharacterStyle(
            name=docx_style.name or docx_style.style_id,

            # Basic font properties
            bold=props.bold,
            italic=props.italic,
            underline=props.underline is not None,
            underline_type=props.underline if isinstance(props.underline, str) else None,

            # Color properties
            color=color,
            highlight=highlight_color,
            background=additional_properties.get('shading_fill'),

            # Font properties
            font=props.font_name,
            font_family=additional_properties.get('font_family'),
            font_charset=additional_properties.get('font_charset'),
            font_pitch=additional_properties.get('font_pitch'),
            size=props.font_size,
            size_cs=props.font_size_cs,  # Complex script font size

            # Text effects
            strike=props.strike,
            double_strike=props.double_strike,
            superscript=props.superscript,
            subscript=props.subscript,
            small_caps=props.small_caps,
            all_caps=props.all_caps,

            # Advanced typography
            kerning=props.kerning,
            spacing=props.spacing,
            position=props.position,  # Raised/lowered text

            # Effects
            shadow=props.shadow,
            outline=props.outline,
            emboss=props.emboss,
            imprint=props.imprint,

            # Visibility
            vanished=props.vanished,  # Hidden text
            web_hidden=props.web_hidden,

            # Language and proofing
            language=props.language,
            no_proof=props.no_proof,

            # Additional metadata
            style_id=docx_style.style_id,
            based_on=docx_style.based_on,
            next_style=docx_style.next_style,
            linked_style=docx_style.linked_style_id,
        )


    def _convert_paragraph_style(self, docx_style: DOCXStyle) -> ParagraphStyle | None:
        """
        Convert DOCX paragraph style to USDM ParagraphStyle with borders and shading.
        
        Args:
            docx_style: DOCXStyle object
            
        Returns:
            ParagraphStyle object or None
        """
        if not docx_style.paragraph_properties:
            return None

        props = docx_style.paragraph_properties.properties
        additional_properties=getattr(props, 'additional_properties', {})

        # Alignment mapping
        alignment_map = {
            ParagraphAlignment.LEFT: "left",
            ParagraphAlignment.CENTER: "center",
            ParagraphAlignment.RIGHT: "right",
            ParagraphAlignment.BOTH: "justify",
            ParagraphAlignment.DISTRIBUTE: "justify",
        }

        # Convert borders
        borders: dict[str, dict[str, Any]] = {}
        for border_pos in ['top', 'bottom', 'left', 'right']:
            border_attr = getattr(props, f'border_{border_pos}', None)
            if border_attr:
                border_info = self._convert_border_to_style(border_attr)
                if border_info:
                    borders[border_pos] = border_info

        # Convert shading
        shading = None
        if props.shading_fill or props.shading_pattern:
            shading = {
                'fill': self._resolve_theme_color(
                    props.shading_fill,
                    additional_properties.get('shading_theme_color'),
                    additional_properties.get('shading_theme_tint'),
                    additional_properties.get('shading_theme_shade')
                ),
                'pattern': props.shading_pattern,
                'color': self._resolve_theme_color(
                    additional_properties.get('shading_color'),
                    additional_properties.get('shading_color_theme')
                )
            }
            # Remove None values
            shading = {k: v for k, v in shading.items() if v is not None}

        # Convert tabs
        tabs = []
        for tab_info in props.tabs:
            tab_style = {
                'position': tab_info.get('position'),
                'alignment': tab_info.get('alignment', 'left'),
                'leader': tab_info.get('leader', 'none')
            }
            tabs.append(tab_style)

        # Build comprehensive paragraph style
        return ParagraphStyle(
            name=docx_style.name or docx_style.style_id,

            # Alignment and spacing
            alignment=alignment_map.get(props.alignment) if props.alignment else None,
            spacing_before=props.spacing_before,
            spacing_after=props.spacing_after,
            line_spacing=props.line_spacing,
            line_spacing_rule=props.line_spacing_rule,

            # Indentation
            indent_left=props.indent_left,
            indent_right=props.indent_right,
            first_line_indent=props.indent_first_line,
            indent_hanging=props.indent_hanging,

            # Pagination
            keep_lines_together=props.keep_lines_together,
            keep_with_next=props.keep_with_next,
            page_break_before=props.page_break_before,
            widow_control=props.widow_control,

            # Borders and shading
            borders=borders if borders else None,
            shading=shading if shading else None,

            # Outline level
            outline_level=props.outline_level,

            # Text direction
            text_direction=props.text_direction.value if props.text_direction else 'ltr',

            # Tabs
            tabs=tabs if tabs else None,

            # Frame properties
            frame_properties=props.frame_properties,

            # Style inheritance
            style_id=docx_style.style_id,
            based_on=docx_style.based_on,
            next_style=docx_style.next_style,
        )


    def _convert_border_to_style(self, border_info: dict[str, Any]) -> dict[str, Any] | None:
        """
        Convert DOCX border information to style dictionary.
        
        Args:
            border_info: Border information from DOCX
            
        Returns:
            Border style dictionary
        """
        style: dict[str, Any] = {}

        if 'style' in border_info:
            style['style'] = border_info['style']

        if 'color' in border_info:
            color = self._resolve_theme_color(
                border_info.get('color'),
                border_info.get('theme_color'),
                border_info.get('theme_tint'),
                border_info.get('theme_shade')
            )
            style['color'] = color

        if 'width' in border_info:
            style['width'] = border_info['width']

        if 'space' in border_info:
            style['space'] = border_info['space']

        return style if style else None



    def _convert_table_style(self, docx_style: DOCXStyle) -> TableStyle | None:
        """
        Convert DOCX table style to USDM TableStyle with borders and banding.
        
        Args:
            docx_style: DOCXStyle object
            
        Returns:
            TableStyle object or None
        """
        if not docx_style.table_properties:
            return None

        props = docx_style.table_properties.properties

        # Convert borders
        borders: dict[str, dict[str, Any]] = {}
        border_mapping = {
            'border_top': 'top',
            'border_bottom': 'bottom',
            'border_left': 'left',
            'border_right': 'right',
            'border_inside_horizontal': 'inside_horizontal',
            'border_inside_vertical': 'inside_vertical',
        }

        for attr_name, border_name in border_mapping.items():
            border_attr = getattr(props, attr_name, None)
            if border_attr:
                border_info = self._convert_border_to_style(border_attr)
                if border_info:
                    borders[border_name] = border_info

        # Convert cell margins
        cell_margins = {}
        if props.cell_margin_default:
            for margin_pos, margin_val in props.cell_margin_default.items():
                cell_margins[margin_pos] = margin_val

        # Convert shading
        shading = None
        additional_properties = getattr(props, 'additional_properties', {})
        shading_info = additional_properties.get('shading')
        if shading_info:
            shading = {
                'fill': self._resolve_theme_color(
                    shading_info.get('fill'),
                    shading_info.get('theme_color'),
                    shading_info.get('theme_tint'),
                    shading_info.get('theme_shade')
                ),
                'pattern': shading_info.get('pattern'),
            }
            shading = {k: v for k, v in shading.items() if v is not None}

        # Build comprehensive table style
        return TableStyle(
            name=docx_style.name or docx_style.style_id,

            # Positioning
            alignment=props.alignment.value if props.alignment else 'left',
            indent_left=props.indent_left,
            width=props.width,
            layout_type=props.layout_type,

            # Borders
            borders=borders if borders else None,

            # Cell properties
            cell_margins=cell_margins if cell_margins else None,
            cell_spacing=props.cell_spacing,

            # Shading
            shading=shading if shading else None,

            # Banding options
            header_row=props.header_row_repeat,
            banded_rows=additional_properties.get('banded_rows', True),
            banded_columns=additional_properties.get('banded_columns', False),
            first_row=additional_properties.get('first_row_formatting'),
            last_row=additional_properties.get('last_row_formatting'),
            first_column=additional_properties.get('first_column_formatting'),
            last_column=additional_properties.get('last_column_formatting'),

            # Style inheritance
            style_id=docx_style.style_id,
            based_on=docx_style.based_on,
        )


    def _convert_list_styles(self) -> dict[str, ListStyle]:
        """
        Convert DOCX numbering definitions to USDM ListStyle objects.
        
        Returns:
            Dictionary mapping style name to ListStyle
        """
        list_styles: dict[str, ListStyle] = {}
        assert self._docx_doc is not None, "Document not extracted"
        for abs_id, definition in self._docx_doc.numbering_definitions.items():
            style_name = definition.name or f"ListStyle_{abs_id}"

            level_styles: dict[int, dict[str, Any]] = {}
            for level_num, level_def in definition.levels.items():
                level_styles[level_num] = {
                    "format": level_def.format,
                    "start": level_def.start,
                    "text_template": level_def.text_template,
                    "alignment": level_def.alignment.value if level_def.alignment else "left",
                    "indent_left": level_def.indent_left,
                    "indent_hanging": level_def.indent_hanging,
                    "font_name": level_def.font_name,
                    "font_size": level_def.font_size,
                    "bold": level_def.bold,
                    "italic": level_def.italic,
                }

            list_style = ListStyle(
                name=style_name,
                level_styles=level_styles
            )
            list_styles[style_name] = list_style

        return list_styles

    # ============================================================
    # BODY CONVERSION
    # ============================================================


