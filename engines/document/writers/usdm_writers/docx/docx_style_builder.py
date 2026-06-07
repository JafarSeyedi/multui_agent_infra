from __future__ import annotations

from typing import Any


def character_style_to_ooxml(style: Any) -> str:
    """
    Convert a USDM CharacterStyle to OOXML w:rPr XML fragment.

    Maps bold, italic, underline, color, font, size, highlight, strike,
    superscript/subscript, small_caps, all_caps, spacing, kerning, position,
    vanish, shadow, outline, emboss, imprint, language to OOXML run properties.
    """
    parts: list[str] = []

    if style.bold:
        parts.append("<w:b/>")
    if style.italic:
        parts.append("<w:i/>")
    if style.underline:
        u_val = getattr(style, "underline_type", None) or "single"
        parts.append(f'<w:u w:val="{_escape_attr(u_val)}"/>')
    if style.color and style.color.lower() != "auto":
        color_val = _normalize_color(style.color)
        parts.append(f'<w:color w:val="{color_val}"/>')
    if style.font:
        font_name = _escape_attr(style.font)
        parts.append(
            f'<w:rFonts w:ascii="{font_name}" w:hAnsi="{font_name}"/>'
        )
    if style.size is not None:
        sz_half = int(style.size * 2)
        parts.append(f'<w:sz w:val="{sz_half}"/>')
        parts.append(f'<w:szCs w:val="{sz_half}"/>')
    if style.highlight and style.highlight.lower() != "none":
        parts.append(f'<w:highlight w:val="{_escape_attr(style.highlight)}"/>')
    if style.background and style.background.lower() != "auto":
        bg = _normalize_color(style.background)
        parts.append(f'<w:shd w:fill="{bg}" w:val="clear"/>')
    if style.strike:
        parts.append("<w:strike/>")
    if getattr(style, "double_strike", False):
        parts.append("<w:dstrike/>")
    if style.superscript:
        parts.append('<w:vertAlign w:val="superscript"/>')
    if style.subscript:
        parts.append('<w:vertAlign w:val="subscript"/>')
    if getattr(style, "small_caps", False):
        parts.append("<w:smallCaps/>")
    if getattr(style, "all_caps", False):
        parts.append("<w:caps/>")
    if getattr(style, "kerning", None) is not None:
        parts.append(f'<w:kern w:val="{int(style.kerning * 2)}"/>')
    if getattr(style, "spacing", None) is not None:
        parts.append(f'<w:spacing w:val="{int(style.spacing * 2)}"/>')
    if getattr(style, "position", None) is not None:
        parts.append(f'<w:position w:val="{int(style.position * 2)}"/>')
    if getattr(style, "shadow", False):
        parts.append("<w:shadow/>")
    if getattr(style, "outline", False):
        parts.append("<w:outline/>")
    if getattr(style, "emboss", False):
        parts.append("<w:emboss/>")
    if getattr(style, "imprint", False):
        parts.append("<w:imprint/>")
    if getattr(style, "vanished", False):
        parts.append("<w:vanish/>")
    if getattr(style, "web_hidden", False):
        parts.append("<w:webHidden/>")
    if getattr(style, "language", None):
        parts.append(
            f'<w:lang w:val="{_escape_attr(style.language)}"/>'
        )

    return "".join(parts)


def paragraph_style_to_ooxml(style: Any) -> str:
    """
    Convert a USDM ParagraphStyle to OOXML w:pPr XML fragment.

    Maps alignment, spacing, indentation, borders, shading, pagination,
    outline level, tabs, text direction to OOXML paragraph properties.
    """
    parts: list[str] = []

    if style.alignment:
        jc_map = {
            "left": "left",
            "right": "right",
            "center": "center",
            "justify": "both",
            "both": "both",
        }
        jc_val = jc_map.get(style.alignment, style.alignment)
        parts.append(f'<w:jc w:val="{_escape_attr(jc_val)}"/>')

    spacing_parts: list[str] = []
    if style.spacing_before is not None:
        spacing_parts.append(f'w:before="{int(style.spacing_before)}"')
    if style.spacing_after is not None:
        spacing_parts.append(f'w:after="{int(style.spacing_after)}"')
    if style.line_spacing is not None:
        rule = getattr(style, "line_spacing_rule", "auto") or "auto"
        if rule == "exact":
            spacing_parts.append(f'w:line="{int(style.line_spacing * 20)}"')
            spacing_parts.append('w:lineRule="exact"')
        elif rule == "at_least":
            spacing_parts.append(f'w:line="{int(style.line_spacing * 20)}"')
            spacing_parts.append('w:lineRule="atLeast"')
        else:
            spacing_parts.append(f'w:line="{int(style.line_spacing * 240)}"')
            spacing_parts.append('w:lineRule="auto"')
    if spacing_parts:
        parts.append(f'<w:spacing {" ".join(spacing_parts)}/>')

    indent_parts: list[str] = []
    if style.indent_left is not None:
        indent_parts.append(f'w:left="{int(style.indent_left)}"')
    if style.indent_right is not None:
        indent_parts.append(f'w:right="{int(style.indent_right)}"')
    if getattr(style, "first_line_indent", None) is not None:
        indent_parts.append(f'w:firstLine="{int(style.first_line_indent)}"')
    if getattr(style, "indent_hanging", None) is not None:
        indent_parts.append(f'w:hanging="{int(style.indent_hanging)}"')
    if indent_parts:
        parts.append(f'<w:ind {" ".join(indent_parts)}/>')

    if getattr(style, "borders", None):
        border_xml = _build_borders(style.borders)
        if border_xml:
            parts.append(border_xml)

    if getattr(style, "shading", None):
        shd = style.shading
        fill = shd.get("fill", "")
        pattern = shd.get("pattern", "clear")
        color = shd.get("color", "auto")
        if fill and fill.lower() != "auto":
            parts.append(
                f'<w:shd w:fill="{_normalize_color(fill)}" '
                f'w:val="{_escape_attr(pattern)}" w:color="{_escape_attr(color)}"/>'
            )

    if getattr(style, "page_break_before", False):
        parts.append("<w:pageBreakBefore/>")
    if getattr(style, "keep_lines_together", False):
        parts.append("<w:keepLines/>")
    if getattr(style, "keep_with_next", False):
        parts.append("<w:keepNext/>")
    if getattr(style, "widow_control", False):
        parts.append("<w:widowControl/>")
    if getattr(style, "outline_level", None) is not None:
        parts.append(f'<w:outlineLvl w:val="{style.outline_level}"/>')

    if getattr(style, "tabs", None):
        for tab in style.tabs:
            tab_pos = tab.get("position", 0)
            tab_align = tab.get("alignment", "left")
            tab_leader = tab.get("leader", "none")
            parts.append(
                f'<w:tabs w:pos="{int(tab_pos)}" '
                f'w:val="{_escape_attr(tab_align)}" '
                f'w:leader="{_escape_attr(tab_leader)}"/>'
            )

    return "".join(parts)


def table_style_to_ooxml(style: Any) -> str:
    """
    Convert a USDM TableStyle to OOXML w:tblPr XML fragment.

    Maps alignment, width, layout, borders, cell margins, shading,
    banding options to OOXML table properties.
    """
    parts: list[str] = []

    if style.alignment:
        jc_map = {
            "left": "left",
            "right": "right",
            "center": "center",
        }
        jc_val = jc_map.get(style.alignment, style.alignment)
        parts.append(f'<w:jc w:val="{_escape_attr(jc_val)}"/>')

    if getattr(style, "width", None) is not None:
        w_type = getattr(style, "layout_type", "auto") or "auto"
        parts.append(
            f'<w:tblW w:w="{int(style.width)}" w:type="{_escape_attr(w_type)}"/>'
        )
    else:
        layout = getattr(style, "layout_type", None)
        if layout == "fixed":
            parts.append('<w:tblLayout w:type="fixed"/>')
        else:
            tbl_w_type = getattr(style, "tbl_w_type", "auto") or "auto"
            if getattr(style, "tbl_w_val", None) is not None:
                parts.append(
                    f'<w:tblW w:w="{int(style.tbl_w_val)}" w:type="{_escape_attr(tbl_w_type)}"/>'
                )
            else:
                parts.append('<w:tblLayout w:type="autofit"/>')

    if getattr(style, "borders", None):
        border_xml = _build_table_borders(style.borders)
        if border_xml:
            parts.append(border_xml)

    if getattr(style, "cell_margins", None):
        margin_parts: list[str] = []
        for pos, val in style.cell_margins.items():
            margin_parts.append(
                f'<w:{pos} w:w="{int(val)}" w:type="dxa"/>'
            )
        if margin_parts:
            parts.append(f'<w:tblCellMar{"".join(margin_parts)}</w:tblCellMar>')

    if getattr(style, "cell_spacing", None) is not None:
        parts.append(
            f'<w:tblCellSpacing w:w="{int(style.cell_spacing)}" w:type="dxa"/>'
        )

    if getattr(style, "shading", None):
        shd = style.shading
        fill = shd.get("fill", "")
        pattern = shd.get("pattern", "clear")
        if fill and fill.lower() != "auto":
            parts.append(
                f'<w:shd w:fill="{_normalize_color(fill)}" w:val="{_escape_attr(pattern)}"/>'
            )

    if getattr(style, "header_row", False):
        parts.append('<w:tblHeader xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')

    return "".join(parts)


def list_style_to_ooxml(style: Any) -> str:
    """
    Convert a USDM ListStyle to OOXML numbering XML fragment.

    Produces w:abstractNum and w:num entries for multi-level lists
    with format, alignment, text, and indentation per level.
    """

    abstract_id = _escape_attr(style.name)
    parts: list[str] = []
    parts.append(
        f'<w:abstractNum w:abstractNumId="{abstract_id}">'
    )

    level_styles = getattr(style, "level_styles", {}) or {}
    if not level_styles:
        level_styles = {0: {"format": "bullet", "text_template": "•", "alignment": "left"}}

    for level_num, level_def in level_styles.items():
        lvl_parts: list[str] = []
        lvl_parts.append(f'<w:lvl w:ilvl="{level_num}">')

        fmt = level_def.get("format", "bullet")
        lvl_parts.append(f'<w:numFmt w:val="{_escape_attr(fmt)}"/>')

        text_tpl = level_def.get("text_template", f"%{level_num + 1}.")
        if text_tpl:
            lvl_parts.append(f'<w:lvlText w:val="{_escape_attr(text_tpl)}"/>')

        align = level_def.get("alignment", "left")
        lvl_parts.append(f'<w:lvlJc w:val="{_escape_attr(align)}"/>')

        # indentation
        indent_left = level_def.get("indent_left", 720 * (level_num + 1))
        indent_hanging = level_def.get("indent_hanging", 360)
        lvl_parts.append(
            f'<w:pPr><w:ind w:left="{int(indent_left)}" '
            f'w:hanging="{int(indent_hanging)}"/></w:pPr>'
        )

        # run properties for number font
        rpr_parts: list[str] = []
        if level_def.get("bold"):
            rpr_parts.append("<w:b/>")
        if level_def.get("italic"):
            rpr_parts.append("<w:i/>")
        font_name = level_def.get("font_name")
        if font_name:
            rpr_parts.append(
                f'<w:rFonts w:ascii="{_escape_attr(font_name)}" '
                f'w:hAnsi="{_escape_attr(font_name)}"/>'
            )
        font_size = level_def.get("font_size")
        if font_size is not None:
            sz_half = int(font_size * 2)
            rpr_parts.append(f'<w:sz w:val="{sz_half}"/>')
        if rpr_parts:
            lvl_parts.append(f'<w:rPr>{"".join(rpr_parts)}</w:rPr>')

        lvl_parts.append("</w:lvl>")
        parts.append("".join(lvl_parts))

    parts.append("</w:abstractNum>")

    # numbering instance
    num_id = abstract_id
    parts.append(
        f'<w:num w:numId="{num_id}">'
        f'<w:abstractNumId w:val="{abstract_id}"/>'
        "</w:num>"
    )

    return "".join(parts)


def _build_borders(borders: dict[str, Any]) -> str:
    """Build OOXML pBdr element from borders dict."""
    parts: list[str] = ['<w:pBdr>']
    for pos in ("top", "bottom", "left", "right"):
        b = borders.get(pos)
        if not b:
            continue
        b_style = b.get("style", "single")
        b_color = b.get("color", "auto")
        b.get("size", b.get("width", 4))
        b_space = b.get("space", 0)
        parts.append(
            f'<w:{pos} w:val="{_escape_attr(b_style)}" '
            f'w:sz="{b_space}" '
            f'w:space="{b_space}" '
            f'w:color="{_normalize_color(b_color)}"/>'
        )
    parts.append("</w:pBdr>")
    return "".join(parts)


def _build_table_borders(borders: dict[str, Any]) -> str:
    """Build OOXML tblBorders element from borders dict."""
    parts: list[str] = ['<w:tblBorders>']
    for pos in ("top", "bottom", "left", "right", "insideH", "insideV"):
        b = borders.get(pos)
        if not b:
            continue
        b_style = b.get("style", "single")
        b_color = b.get("color", "auto")
        b_size = b.get("size", b.get("width", 4))
        b_space = b.get("space", 0)
        parts.append(
            f'<w:{pos} w:val="{_escape_attr(b_style)}" '
            f'w:sz="{b_size}" '
            f'w:space="{b_space}" '
            f'w:color="{_normalize_color(b_color)}"/>'
        )
    parts.append("</w:tblBorders>")
    return "".join(parts)


def _normalize_color(color: str) -> str:
    """Normalize a color value to 6-char hex without # prefix."""
    if not color or color.lower() in ("auto", "none", "transparent"):
        return "auto"
    c = color.strip().lstrip("#")
    if len(c) == 8:
        c = c[2:]
    if len(c) == 6 and all(ch in "0123456789ABCDEFabcdef" for ch in c):
        return c.upper()
    color_map = {
        "black": "000000", "white": "FFFFFF", "red": "FF0000",
        "green": "008000", "blue": "0000FF", "yellow": "FFFF00",
        "cyan": "00FFFF", "magenta": "FF00FF", "gray": "808080",
        "grey": "808080", "darkred": "8B0000", "darkgreen": "006400",
        "darkblue": "00008B", "orange": "FFA500", "purple": "800080",
        "brown": "A52A2A", "pink": "FFC0CB", "lime": "00FF00",
        "navy": "000080", "teal": "008080", "olive": "808000",
        "maroon": "800000", "silver": "C0C0C0", "aqua": "00FFFF",
    }
    return color_map.get(color.lower(), c[:6].upper())


def _escape_attr(val: str) -> str:
    """Escape special XML characters in attribute values."""
    s = str(val)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    s = s.replace("'", "&apos;")
    return s


def _escape_text(val: str) -> str:
    """Escape special XML characters in text content."""
    s = str(val)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    return s
