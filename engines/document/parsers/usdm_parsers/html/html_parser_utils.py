# engines/document/parsers/usdm_parsers/html/html_parser_utils.py
"""Utility functions for the HTML parser."""

from __future__ import annotations

import re
from typing import Any

from ....models.usdm_models import CharacterStyle
from .html_parser_constants import ARIA_STATES_PROPERTIES, INLINE_STYLE_PROPERTY_MAP


def parse_inline_style(style_str: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for declaration in style_str.split(";"):
        declaration = declaration.strip()
        if ":" not in declaration:
            continue
        prop, _, value = declaration.partition(":")
        prop = prop.strip().lower()
        value = value.strip()
        if not prop or not value:
            continue
        if prop in INLINE_STYLE_PROPERTY_MAP:
            key = INLINE_STYLE_PROPERTY_MAP[prop]
            result[key] = value
    return result


def parse_css_style_element(css_text: str) -> list[dict[str, Any]]:
    styles: list[dict[str, Any]] = []
    rule_pattern = re.compile(r'([^{]+)\{([^}]+)\}', re.DOTALL)
    for selector_match, body_match in rule_pattern.findall(css_text):
        selector = selector_match.strip()
        props = parse_inline_style(body_match)
        if props:
            styles.append({"selector": selector, "properties": props})
    return styles


def attrs_to_dict(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in attrs:
        if value is not None:
            result[key] = value
    return result


def extract_aria(attrs: dict[str, str]) -> tuple[str | None, dict[str, str]]:
    role = attrs.get("role")
    aria_attrs: dict[str, str] = {}
    for key, value in attrs.items():
        if key in ARIA_STATES_PROPERTIES:
            aria_attrs[key] = value
    return role, aria_attrs


def extract_microdata(attrs: dict[str, str]) -> dict[str, str]:
    keys = ("itemscope", "itemtype", "itemprop", "itemid", "itemref")
    return {k: attrs[k] for k in keys if k in attrs}


def extract_rdfa(attrs: dict[str, str]) -> dict[str, str]:
    keys = ("vocab", "typeof", "property", "resource", "prefix", "content", "datatype", "rel", "rev")
    return {k: attrs[k] for k in keys if k in attrs}


def safe_int(value: str | None, default: int = 1) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def build_character_style_from_css(css_props: dict[str, Any]) -> CharacterStyle:
    kwargs: dict[str, Any] = {}
    if "font" in css_props:
        kwargs["font_family"] = css_props["font"]
    if "size" in css_props:
        try:
            kwargs["size"] = float(css_props["size"].replace("px", "").replace("pt", "").replace("em", ""))
        except (ValueError, TypeError):
            pass
    if "weight" in css_props:
        w = css_props["weight"]
        if w in ("bold", "bolder") or (w.isdigit() and int(w) >= 700):
            kwargs["bold"] = True
    if "style" in css_props:
        if "italic" in css_props["style"] or "oblique" in css_props["style"]:
            kwargs["italic"] = True
    if "decoration" in css_props:
        dec = css_props["decoration"]
        if "underline" in dec:
            kwargs["underline"] = True
        if "line-through" in dec:
            kwargs["strike"] = True
    if "color" in css_props:
        kwargs["color"] = css_props["color"]
    if "background" in css_props:
        kwargs["background"] = css_props["background"]
        kwargs["highlight"] = css_props["background"]
    if "transform" in css_props:
        t = css_props["transform"]
        if t == "uppercase":
            kwargs["all_caps"] = True
    if "alignment" in css_props:
        kwargs["alignment"] = css_props["alignment"]
    return CharacterStyle(name="inline", **kwargs) if kwargs else CharacterStyle(name="inline")
