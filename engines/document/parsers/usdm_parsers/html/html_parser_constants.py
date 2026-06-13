# engines/document/parsers/usdm_parsers/html/html_parser_constants.py
"""Constants and lookup tables for the HTML parser."""

from __future__ import annotations

from ....models.base import ElementType


VOID_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})

RAW_TEXT_ELEMENTS = frozenset({"script", "style"})

RCDATA_ELEMENTS = frozenset({"textarea", "title"})

ARIA_ROLE_MAP: dict[str, ElementType] = {
    "article": ElementType.SECTION,
    "banner": ElementType.HEADER,
    "complementary": ElementType.SECTION,
    "contentinfo": ElementType.FOOTER,
    "dialog": ElementType.SECTION,
    "document": ElementType.SECTION,
    "form": ElementType.FORM_FIELD,
    "img": ElementType.IMAGE,
    "list": ElementType.LIST,
    "listitem": ElementType.LIST_ITEM,
    "main": ElementType.SECTION,
    "navigation": ElementType.SECTION,
    "region": ElementType.SECTION,
    "search": ElementType.SECTION,
    "alert": ElementType.SECTION,
    "alertdialog": ElementType.SECTION,
    "application": ElementType.SECTION,
    "button": ElementType.FORM_FIELD,
    "checkbox": ElementType.FORM_FIELD,
    "columnheader": ElementType.TABLE,
    "combobox": ElementType.FORM_FIELD,
    "definition": ElementType.SECTION,
    "directory": ElementType.SECTION,
    "feed": ElementType.SECTION,
    "figure": ElementType.SECTION,
    "grid": ElementType.TABLE,
    "gridcell": ElementType.TABLE,
    "group": ElementType.SECTION,
    "heading": ElementType.HEADING,
    "link": ElementType.LINK,
    "listbox": ElementType.LIST,
    "log": ElementType.SECTION,
    "marquee": ElementType.SECTION,
    "math": ElementType.MATH,
    "menu": ElementType.SECTION,
    "menubar": ElementType.SECTION,
    "menuitem": ElementType.SECTION,
    "menuitemcheckbox": ElementType.FORM_FIELD,
    "menuitemradio": ElementType.FORM_FIELD,
    "none": ElementType.SECTION,
    "note": ElementType.SECTION,
    "option": ElementType.FORM_FIELD,
    "presentation": ElementType.SECTION,
    "progressbar": ElementType.FORM_FIELD,
    "radio": ElementType.FORM_FIELD,
    "radiogroup": ElementType.FORM_FIELD,
    "row": ElementType.TABLE,
    "rowgroup": ElementType.TABLE,
    "rowheader": ElementType.TABLE,
    "scrollbar": ElementType.FORM_FIELD,
    "searchbox": ElementType.FORM_FIELD,
    "separator": ElementType.DIVIDER,
    "slider": ElementType.FORM_FIELD,
    "spinbutton": ElementType.FORM_FIELD,
    "status": ElementType.SECTION,
    "switch": ElementType.FORM_FIELD,
    "tab": ElementType.SECTION,
    "tablist": ElementType.SECTION,
    "tabpanel": ElementType.SECTION,
    "term": ElementType.SECTION,
    "textbox": ElementType.FORM_FIELD,
    "timer": ElementType.SECTION,
    "toolbar": ElementType.FORM_FIELD,
    "tooltip": ElementType.SECTION,
    "tree": ElementType.SECTION,
    "treegrid": ElementType.TABLE,
    "treeitem": ElementType.SECTION,
}

ARIA_STATES_PROPERTIES = frozenset({
    "aria-label", "aria-labelledby", "aria-describedby",
    "aria-hidden", "aria-expanded", "aria-pressed", "aria-checked",
    "aria-selected", "aria-current", "aria-disabled", "aria-readonly",
    "aria-required", "aria-invalid", "aria-live", "aria-atomic",
    "aria-relevant", "aria-busy", "aria-dropeffect", "aria-grabbed",
    "aria-activedescendant", "aria-controls", "aria-flowto", "aria-owns",
    "aria-posinset", "aria-setsize", "aria-level",
    "aria-valuenow", "aria-valuemin", "aria-valuemax", "aria-valuetext",
    "aria-orientation", "aria-multiselectable", "aria-sort",
    "aria-colcount", "aria-colindex", "aria-colspan",
    "aria-rowcount", "aria-rowindex", "aria-rowspan",
    "aria-details", "aria-errormessage", "aria-keyshortcuts",
    "aria-roledescription",
})

SEMANTIC_SECTION_MAP: dict[str, str] = {
    "article": "article",
    "section": "section",
    "nav": "nav",
    "aside": "aside",
    "main": "main",
}

INLINE_STYLE_PROPERTY_MAP: dict[str, str] = {
    "font-family": "font",
    "font-size": "size",
    "font-weight": "weight",
    "font-style": "style",
    "color": "color",
    "background-color": "background",
    "text-align": "alignment",
    "text-decoration": "decoration",
    "text-transform": "transform",
    "line-height": "line_height",
    "letter-spacing": "letter_spacing",
    "word-spacing": "word_spacing",
    "text-indent": "text_indent",
    "vertical-align": "vertical_align",
    "white-space": "white_space",
    "list-style-type": "list_style",
}

SEMANTIC_HEADING = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
SEMANTIC_INLINE_FORMAT = frozenset({
    "b", "strong", "i", "em", "u", "ins", "s", "del", "strike",
    "sub", "sup", "mark", "small", "big", "abbr", "cite", "code",
    "dfn", "kbd", "q", "samp", "var", "time", "data", "ruby", "rt",
    "rp", "bdi", "bdo", "wbr", "br", "font", "tt", "strike",
})

FORM_INPUT_TYPES = frozenset({
    "text", "password", "email", "tel", "url", "number", "range",
    "date", "time", "datetime-local", "color", "checkbox", "radio",
    "file", "hidden", "submit", "reset", "button", "image", "search",
})
