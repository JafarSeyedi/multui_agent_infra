# engines/document/parsers/usdm_parsers/docx/docx_color_utils.py
"""Color utility functions for the DOCX parser — theme resolution, normalization, tint/shade."""

from __future__ import annotations

import re


def normalize_color_value(color: str) -> str:
    """Normalize a color value to hex format."""
    if not color:
        return "#000000"

    color = color.strip()

    if color.startswith("#"):
        if len(color) == 4:
            return f"#{color[1]*2}{color[2]*2}{color[3]*2}"
        return color

    if re.match(r"^[0-9A-Fa-f]{6}$", color):
        return f"#{color.upper()}"

    if re.match(r"^[0-9A-Fa-f]{3}$", color):
        return f"#{color[0]*2}{color[1]*2}{color[2]*2}".upper()

    named_colors = {
        "black": "#000000", "white": "#FFFFFF", "red": "#FF0000",
        "green": "#00FF00", "blue": "#0000FF", "yellow": "#FFFF00",
        "cyan": "#00FFFF", "magenta": "#FF00FF", "gray": "#808080",
        "grey": "#808080", "auto": "#000000", "window": "#000000",
        "windowtext": "#000000",
    }

    return named_colors.get(color.lower(), "#000000")


def get_system_color(system_color: str) -> str:
    """Get system color mapping."""
    system_colors = {
        "windowText": "#000000", "window": "#FFFFFF", "btnFace": "#F0F0F0",
        "btnText": "#000000", "highlight": "#3399FF", "highlightText": "#FFFFFF",
        "menuText": "#000000", "menu": "#FFFFFF", "scrollbar": "#D3D3D3",
        "inactiveCaption": "#D3D3D3", "activeCaption": "#3399FF",
    }
    return system_colors.get(system_color, "#000000")


def apply_tint(hex_color: str, tint: float) -> str:
    """Apply tint (lighten) to a hex color."""
    hex_color = normalize_color_value(hex_color)

    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    r = int(r + (255 - r) * tint)
    g = int(g + (255 - g) * tint)
    b = int(b + (255 - b) * tint)

    return f"#{r:02X}{g:02X}{b:02X}"


def apply_shade(hex_color: str, shade: float) -> str:
    """Apply shade (darken) to a hex color."""
    hex_color = normalize_color_value(hex_color)

    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    r = int(r * (1 - shade))
    g = int(g * (1 - shade))
    b = int(b * (1 - shade))

    return f"#{r:02X}{g:02X}{b:02X}"


def resolve_theme_color(
    docx_doc,
    color_value: str | None,
    theme_color: str | None = None,
    theme_tint: float | None = None,
    theme_shade: float | None = None,
) -> str | None:
    """Resolve a color value using theme information from a DOCX document."""
    assert docx_doc is not None, "Document not extracted"

    if color_value and color_value.lower() != "auto":
        return normalize_color_value(color_value)

    if theme_color and docx_doc.theme:
        theme_colors = docx_doc.theme.get("colors", {})

        if theme_color in theme_colors:
            color_info = theme_colors[theme_color]

            if color_info.get("type") == "srgb":
                base_color = color_info.get("value", "")
            elif color_info.get("type") == "system":
                base_color = get_system_color(color_info.get("value", ""))
            else:
                base_color = color_info.get("value", "")

            if base_color:
                if theme_tint is not None and theme_tint > 0:
                    base_color = apply_tint(base_color, theme_tint)
                if theme_shade is not None and theme_shade > 0:
                    base_color = apply_shade(base_color, theme_shade)
                return normalize_color_value(base_color)

    return None


def extract_theme_colors_from_document(docx_doc) -> dict[str, dict[str, str]]:
    """Extract theme colors from the document theme."""
    theme_colors: dict[str, dict[str, str]] = {}
    assert docx_doc is not None, "Document not extracted"
    if not docx_doc.theme:
        return theme_colors

    colors = docx_doc.theme.get("colors", {})

    for color_name, color_info in colors.items():
        theme_colors[color_name] = {
            "type": color_info.get("type", "srgb"),
            "value": color_info.get("value", ""),
        }

    return theme_colors
