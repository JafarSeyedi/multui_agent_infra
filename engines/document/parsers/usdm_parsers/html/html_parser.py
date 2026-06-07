from __future__ import annotations

import re
import uuid
from collections.abc import AsyncIterator
from html import entities
from html.parser import HTMLParser
from typing import Any

from ....models.base import BaseDocument
from ....models.base import ElementType
from ....models.exceptions import DocumentParseError
from ....models.media_detection import detect_by_extension
from ....models.usdm_models import AudioContent
from ....models.usdm_models import CharacterStyle
from ....models.usdm_models import CodeContent
from ....models.usdm_models import DrawingContent
from ....models.usdm_models import FormFieldContent
from ....models.usdm_models import HeadingContent
from ....models.usdm_models import ImageContent
from ....models.usdm_models import LineBreakContent
from ....models.usdm_models import ListContent
from ....models.usdm_models import ListItemContent
from ....models.usdm_models import LogicalElement
from ....models.usdm_models import PageBreakContent
from ....models.usdm_models import ParagraphContent
from ....models.usdm_models import QuoteContent
from ....models.usdm_models import RichTextContent
from ....models.usdm_models import RichTextSpan
from ....models.usdm_models import Section
from ....models.usdm_models import TableCell
from ....models.usdm_models import TableContent
from ....models.usdm_models import TableRow
from ....models.usdm_models import USDMDocument
from ....models.usdm_models import VideoContent
from ..base import BaseDocumentParser
from ..base import ParseOptions

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


def _parse_inline_style(style_str: str) -> dict[str, Any]:
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


def _parse_css_style_element(css_text: str) -> list[dict[str, Any]]:
    styles: list[dict[str, Any]] = []
    rule_pattern = re.compile(r'([^{]+)\{([^}]+)\}', re.DOTALL)
    for selector_match, body_match in rule_pattern.findall(css_text):
        selector = selector_match.strip()
        props = _parse_inline_style(body_match)
        if props:
            styles.append({"selector": selector, "properties": props})
    return styles


def _attrs_to_dict(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in attrs:
        if value is not None:
            result[key] = value
    return result


def _extract_aria(attrs: dict[str, str]) -> tuple[str | None, dict[str, str]]:
    role = attrs.get("role")
    aria_attrs: dict[str, str] = {}
    for key, value in attrs.items():
        if key in ARIA_STATES_PROPERTIES:
            aria_attrs[key] = value
    return role, aria_attrs


def _extract_microdata(attrs: dict[str, str]) -> dict[str, str]:
    keys = ("itemscope", "itemtype", "itemprop", "itemid", "itemref")
    return {k: attrs[k] for k in keys if k in attrs}


def _extract_rdfa(attrs: dict[str, str]) -> dict[str, str]:
    keys = ("vocab", "typeof", "property", "resource", "prefix", "content", "datatype", "rel", "rev")
    return {k: attrs[k] for k in keys if k in attrs}


def _safe_int(value: str | None, default: int = 1) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _build_character_style_from_css(css_props: dict[str, Any]) -> CharacterStyle:
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


class HTMLDocumentParser(HTMLParser):

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.element_stack: list[dict[str, Any]] = []
        self.sections: list[Section] = []
        self.elements: list[LogicalElement] = []
        self.current_text: list[str] = []
        self.current_spans: list[RichTextSpan] = []
        self.current_style_stack: list[dict[str, Any]] = [{}]
        self.current_list: dict[str, Any] | None = None
        self.list_stack: list[dict[str, Any]] = []
        self.current_table: dict[str, Any] | None = None
        self.table_stack: list[dict[str, Any]] = []
        self.current_row: dict[str, Any] | None = None
        self.current_cell: dict[str, Any] | None = None
        self.in_code_block = False
        self.in_math = False
        self.math_buffer: list[str] = []
        self.current_section: Section | None = None
        self.document_title: str | None = None
        self.element_counter = 0
        self.current_heading: dict[str, Any] | None = None
        self.heading_stack: list[int] = []
        self.in_head = False
        self.metadata: dict[str, str] = {}
        self.base_href: str | None = None
        self.css_styles: list[dict[str, Any]] = []
        self.parsed_figures: list[dict[str, Any]] = []
        self.current_figure: dict[str, Any] | None = None
        self.in_svg = False
        self.svg_buffer: list[str] = []
        self.svg_depth = 0
        self.in_mathml = False
        self.mathml_buffer: list[str] = []
        self.mathml_depth = 0
        self.form_field_stack: list[dict[str, Any]] = []
        self.current_select: dict[str, Any] | None = None
        self.current_details: dict[str, Any] | None = None
        self.in_dialog = False
        self.current_dialog: dict[str, Any] | None = None
        self.skip_depth = 0

    def _generate_id(self) -> str:
        self.element_counter += 1
        return f"elem_{self.element_counter}"

    def _current_style(self) -> dict[str, Any]:
        return self.current_style_stack[-1] if self.current_style_stack else {}

    def _push_style(self) -> None:
        self.current_style_stack.append(self._current_style().copy())

    def _pop_style(self) -> None:
        if len(self.current_style_stack) > 1:
            self.current_style_stack.pop()

    def _get_attr(self, name: str) -> str | None:
        style = self._current_style()
        return style.get(name)

    def _set_style_attr(self, name: str, value: Any) -> None:
        if self.current_style_stack:
            self.current_style_stack[-1][name] = value

    def _get_bold(self) -> bool:
        return self._current_style().get("bold", False)

    def _get_italic(self) -> bool:
        return self._current_style().get("italic", False)

    def _get_underline(self) -> bool:
        return self._current_style().get("underline", False)

    def _get_strikethrough(self) -> bool:
        return self._current_style().get("strikethrough", False)

    def _get_code(self) -> bool:
        return getattr(self, "in_code_block", False) or self._current_style().get("code", False)

    def _get_href(self) -> str | None:
        return self._current_style().get("href")

    def _get_math(self) -> str | None:
        return self._current_style().get("math")

    def _get_display_math(self) -> bool:
        return self._current_style().get("display_math", False)

    def _create_rich_text_span(self, text: str) -> RichTextSpan:
        style = self._current_style()
        return RichTextSpan(
            text=text,
            bold=self._get_bold(),
            italic=self._get_italic(),
            underline=self._get_underline(),
            color=style.get("color"),
            font=style.get("font"),
            code=self._get_code(),
            href=self._get_href(),
            math=self._get_math(),
            display_math=self._get_display_math(),
            background=style.get("background"),
            character_style=style.get("character_style_key"),
        )

    def _flush_current_text(self) -> None:
        if self.current_text:
            text = "".join(self.current_text)
            if text:
                span = self._create_rich_text_span(text)
                self.current_spans.append(span)
            self.current_text = []

    def _flush_text_as_paragraph(self) -> ParagraphContent | None:
        self._flush_current_text()
        if self.current_spans:
            content = ParagraphContent(text=RichTextContent(spans=self.current_spans.copy()))
            self.current_spans = []
            return content
        return None

    def _add_element(self, logical_elem: LogicalElement) -> None:
        self.elements.append(logical_elem)
        if not self.current_section:
            if not self.sections:
                default_section = Section(
                    section_id="section_default",
                    title=None,
                    elements=[],
                    metadata={"auto_generated": True},
                )
                self.sections.append(default_section)
                self.current_section = default_section
        if self.current_section:
            self.current_section.elements.append(logical_elem)

    def _push_section(self, section: Section, heading_content: HeadingContent | None = None) -> None:
        self.sections.append(section)
        self.current_section = section
        if heading_content and section.title is None:
            section.title = heading_content

    def _start_implicit_section(self, level: int, tag: str) -> None:
        while self.heading_stack and self.heading_stack[-1] >= level:
            self.heading_stack.pop()
        self.heading_stack.append(level)

    def _close_implicit_sections_above(self, level: int) -> None:
        while self.heading_stack and self.heading_stack[-1] >= level:
            self.heading_stack.pop()

    def _build_metadata(self, attrs: dict[str, str]) -> dict[str, Any]:
        meta: dict[str, Any] = {"html_attrs": dict(attrs)}
        role, aria_attrs = _extract_aria(attrs)
        if role:
            meta["aria_role"] = role
        if aria_attrs:
            meta["aria_attributes"] = aria_attrs
        microdata = _extract_microdata(attrs)
        if microdata:
            meta["microdata"] = microdata
        rdfa = _extract_rdfa(attrs)
        if rdfa:
            meta["rdfa"] = rdfa
        return meta

    def _create_logical_element(
        self,
        element_type: ElementType,
        content: Any,
        attrs: dict[str, str] | None = None,
    ) -> LogicalElement:
        meta = self._build_metadata(attrs) if attrs else {}
        return LogicalElement(
            element_id=self._generate_id(),
            element_type=element_type,
            content=content,
            metadata=meta,
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = _attrs_to_dict(attrs)
        tag_lower = tag.lower()

        if self.skip_depth > 0:
            self.skip_depth += 1
            return

        if self.in_svg:
            attr_str = " ".join(f'{k}="{v}"' for k, v in attrs_dict.items())
            self.svg_buffer.append(f"<{tag}{' ' + attr_str if attr_str else ''}>")
            if tag_lower in VOID_ELEMENTS:
                pass
            else:
                self.svg_depth += 1
            return

        if self.in_mathml:
            attr_str = " ".join(f'{k}="{v}"' for k, v in attrs_dict.items())
            self.mathml_buffer.append(f"<{tag}{' ' + attr_str if attr_str else ''}>")
            if tag_lower not in VOID_ELEMENTS:
                self.mathml_depth += 1
            return

        if tag_lower == "svg":
            self.in_svg = True
            self.svg_buffer = [f"<svg{' ' + ' '.join(f'{k}=\"{v}\"' for k, v in attrs_dict.items()) if attrs_dict else ''}>"]
            self.svg_depth = 0
            self._push_style_stack(tag_lower, attrs_dict)
            return

        if tag_lower == "math":
            self.in_mathml = True
            self.mathml_buffer = [f"<math{' ' + ' '.join(f'{k}=\"{v}\"' for k, v in attrs_dict.items()) if attrs_dict else ''}>"]
            self.mathml_depth = 0
            self._push_style_stack(tag_lower, attrs_dict)
            return

        if tag_lower in RAW_TEXT_ELEMENTS:
            self.skip_depth = 1

        self._handle_starttag_impl(tag_lower, attrs_dict)

    def _handle_starttag_impl(self, tag: str, attrs: dict[str, str]) -> None:
        self._flush_current_text()
        self._push_style_stack(tag, attrs)

        if tag == "html":
            self._handle_html(attrs)
        elif tag == "head":
            self.in_head = True
        elif tag == "body":
            self.in_head = False
        elif tag == "title":
            self._set_style_attr("in_title", True)
        elif tag == "base":
            self._handle_base(attrs)
        elif tag == "meta":
            self._handle_meta(attrs)
        elif tag == "link":
            self._handle_link(attrs)
        elif tag == "style":
            self._set_style_attr("in_style", True)
            self.current_text = []
        elif tag == "script":
            self._set_style_attr("in_script", True)
            self.current_text = []
            self._set_style_attr("script_type", attrs.get("type", "classic"))
        elif tag == "noscript":
            pass
        elif tag == "template":
            self._set_style_attr("in_template", True)
            self.current_text = []
        elif tag in SEMANTIC_HEADING:
            self._handle_heading_start(tag, attrs)
        elif tag == "p":
            self._handle_paragraph_start(attrs)
        elif tag == "pre":
            self._handle_pre_start(attrs)
        elif tag == "code" and not self._get_code():
            self.in_code_block = True
        elif tag == "hr":
            self._handle_horizontal_rule()
        elif tag == "br":
            self._flush_current_text()
            lb_content = LineBreakContent()
            elem = self._create_logical_element(ElementType.LINE_BREAK, lb_content, attrs)
            self._add_element(elem)
        elif tag == "wbr":
            self._flush_current_text()
            lb_content = LineBreakContent()
            elem = self._create_logical_element(ElementType.LINE_BREAK, lb_content, attrs)
            self._add_element(elem)
        elif tag == "div":
            self._handle_div_start(attrs)
        elif tag == "span":
            pass
        elif tag == "a":
            self._handle_link_start(attrs)
        elif tag in ("b", "strong"):
            self._set_style_attr("bold", True)
        elif tag in ("i", "em"):
            self._set_style_attr("italic", True)
        elif tag in ("u", "ins"):
            self._set_style_attr("underline", True)
        elif tag in ("s", "del", "strike"):
            self._set_style_attr("strikethrough", True)
        elif tag == "small":
            self._set_style_attr("small", True)
        elif tag == "sub":
            self._set_style_attr("subscript", True)
        elif tag == "sup":
            self._set_style_attr("superscript", True)
        elif tag == "mark":
            self._set_style_attr("highlight", attrs.get("background", "yellow"))
        elif tag == "abbr":
            self._set_style_attr("abbr_title", attrs.get("title"))
        elif tag == "q":
            self._set_style_attr("quote_cite", attrs.get("cite"))
        elif tag == "bdi":
            self._set_style_attr("bdi_dir", attrs.get("dir", "auto"))
        elif tag == "bdo":
            self._set_style_attr("bdo_dir", attrs.get("dir", "ltr"))
        elif tag in ("code",):
            self._set_style_attr("code", True)
        elif tag == "time":
            self._set_style_attr("datetime", attrs.get("datetime"))
        elif tag == "data":
            self._set_style_attr("data_value", attrs.get("value"))
        elif tag in ("ruby", "rt", "rp"):
            pass
        elif tag == "dfn":
            self._set_style_attr("italic", True)
        elif tag == "samp":
            self._set_style_attr("code", True)
        elif tag == "kbd":
            self._set_style_attr("code", True)
        elif tag == "var":
            self._set_style_attr("italic", True)
        elif tag == "cite":
            self._set_style_attr("italic", True)
        elif tag == "big":
            self._set_style_attr("big", True)
        elif tag in ("ul", "ol"):
            self._handle_list_start(tag, attrs)
        elif tag == "li":
            self._handle_list_item_start(attrs)
        elif tag == "dl":
            self._handle_list_start("ul", attrs)
        elif tag == "dt":
            self._handle_list_item_start(attrs)
        elif tag == "dd":
            self._handle_list_item_start(attrs)
        elif tag == "blockquote":
            self._handle_blockquote_start(attrs)
        elif tag == "figure":
            self._handle_figure_start(attrs)
        elif tag == "figcaption":
            self._set_style_attr("in_figcaption", True)
        elif tag == "img":
            self._handle_image(attrs)
        elif tag == "audio":
            self._handle_audio(attrs)
        elif tag == "video":
            self._handle_video(attrs)
        elif tag == "source":
            pass
        elif tag == "track":
            pass
        elif tag == "picture":
            pass
        elif tag == "map":
            pass
        elif tag == "area":
            pass
        elif tag == "table":
            self._handle_table_start(attrs)
        elif tag == "caption":
            self._set_style_attr("table_caption", True)
        elif tag == "colgroup":
            pass
        elif tag == "col":
            pass
        elif tag == "thead":
            self._handle_table_row_group_start("thead", attrs)
        elif tag == "tbody":
            self._handle_table_row_group_start("tbody", attrs)
        elif tag == "tfoot":
            self._handle_table_row_group_start("tfoot", attrs)
        elif tag == "tr":
            self._handle_table_row_start(attrs)
        elif tag == "th":
            self._handle_table_cell_start("th", attrs)
        elif tag == "td":
            self._handle_table_cell_start("td", attrs)
        elif tag == "form":
            self._handle_form_start(attrs)
        elif tag == "label":
            self._set_style_attr("label_for", attrs.get("for"))
        elif tag == "input":
            self._handle_input(attrs)
        elif tag == "textarea":
            self._handle_textarea_start(attrs)
        elif tag == "select":
            self._handle_select_start(attrs)
        elif tag == "optgroup":
            self._handle_optgroup_start(attrs)
        elif tag == "option":
            self._handle_option_start(attrs)
        elif tag == "datalist":
            pass
        elif tag == "button":
            self._handle_button_start(attrs)
        elif tag == "fieldset":
            self._handle_fieldset_start(attrs)
        elif tag == "legend":
            self._set_style_attr("in_legend", True)
        elif tag == "output":
            pass
        elif tag == "progress":
            self._handle_progress(attrs)
        elif tag == "meter":
            self._handle_meter(attrs)
        elif tag == "details":
            self._handle_details_start(attrs)
        elif tag == "summary":
            self._set_style_attr("in_summary", True)
        elif tag == "dialog":
            self._handle_dialog_start(attrs)
        elif tag == "iframe":
            self._handle_iframe(attrs)
        elif tag == "embed":
            self._handle_embed(attrs)
        elif tag == "object":
            self._handle_object(attrs)
        elif tag == "param":
            pass
        elif tag == "canvas":
            self._handle_canvas(attrs)
        elif tag == "article":
            self._handle_semantic_section_start("article", attrs)
        elif tag == "section":
            self._handle_semantic_section_start("section", attrs)
        elif tag == "nav":
            self._handle_semantic_section_start("nav", attrs)
        elif tag == "aside":
            self._handle_semantic_section_start("aside", attrs)
        elif tag == "header":
            self._handle_header_start(attrs)
        elif tag == "footer":
            self._handle_footer_start(attrs)
        elif tag == "main":
            self._handle_semantic_section_start("main", attrs)
        elif tag == "address":
            self._handle_address_start(attrs)
        elif tag == "hgroup":
            pass
        elif tag == "font":
            self._handle_legacy_font(attrs)
        elif tag == "center":
            self._handle_legacy_center(attrs)
        elif tag == "tt":
            self._set_style_attr("code", True)
        elif tag == "dir":
            self._handle_list_start("ul", attrs)
        elif tag == "menu":
            self._handle_list_start("ul", attrs)
        elif tag == "applet":
            self._handle_legacy_applet(attrs)
        elif tag == "frame":
            self._handle_legacy_frame(attrs)
        elif tag == "frameset":
            pass
        elif tag == "noframes":
            pass
        elif tag == "marquee":
            pass
        elif tag == "blink":
            pass
        elif tag == "basefont":
            pass
        elif tag == "bgsound":
            pass
        elif tag == "iframe":
            pass
        elif tag == "spacer":
            pass
        elif tag == "xmp":
            pass
        elif tag == "listing":
            pass
        elif tag == "plaintext":
            pass

    def _push_style_stack(self, tag: str, attrs: dict[str, str]) -> None:
        self.element_stack.append({
            "tag": tag,
            "attrs": attrs,
            "style": self._current_style().copy(),
        })
        style = self._current_style()
        style["tag"] = tag
        if "style" in attrs:
            css_props = _parse_inline_style(attrs["style"])
            for key, value in css_props.items():
                if key == "color":
                    style["color"] = value
                elif key == "size":
                    pass
                elif key == "weight":
                    if value in ("bold", "bolder") or (value.isdigit() and int(value) >= 700):
                        style["bold"] = True
                elif key == "style":
                    if "italic" in value:
                        style["italic"] = True
                elif key == "decoration":
                    if "underline" in value:
                        style["underline"] = True
                    if "line-through" in value:
                        style["strikethrough"] = True
                elif key == "background":
                    style["background"] = value

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()

        if self.skip_depth > 0:
            self.skip_depth -= 1
            if self.skip_depth == 0:
                self._handle_raw_text_end(tag_lower)
            return

        if self.in_svg:
            self.svg_buffer.append(f"</{tag}>")
            if tag_lower == "svg":
                svg_content = "".join(self.svg_buffer)
                self.in_svg = False
                self.svg_buffer = []
                svg_element = self._create_logical_element(
                    ElementType.DRAWING,
                    DrawingContent(
                        vector_data=svg_content,
                        width=_safe_float(self._get_parsed_attr("width")),
                        height=_safe_float(self._get_parsed_attr("height")),
                    ),
                    self._get_parsed_attrs_copy(),
                )
                self._add_element(svg_element)
                self._pop_style()
                if self.element_stack:
                    self.element_stack.pop()
                return
            self._pop_style()
            if self.element_stack and self.element_stack[-1]["tag"] == tag_lower:
                self.element_stack.pop()
            return

        if self.in_mathml:
            self.mathml_buffer.append(f"</{tag}>")
            if tag_lower == "math":
                mathml_content = "".join(self.mathml_buffer)
                self.in_mathml = False
                self.mathml_buffer = []
                from ....models.usdm_models import MathContent
                math_element = self._create_logical_element(
                    ElementType.MATH,
                    MathContent(latex=mathml_content, display=True),
                    {},
                )
                self._add_element(math_element)
                self._pop_style()
                if self.element_stack:
                    self.element_stack.pop()
                return
            self._pop_style()
            if self.element_stack and self.element_stack[-1]["tag"] == tag_lower:
                self.element_stack.pop()
            return

        self._flush_current_text()

        if self.current_style_stack and len(self.current_style_stack) > 1:
            self.current_style_stack.pop()

        if self._get_attr("in_title") and tag_lower == "title":
            self._pop_style_attr("in_title")
        elif tag_lower in SEMANTIC_HEADING:
            self._handle_heading_end()
        elif tag_lower == "p":
            self._handle_paragraph_end()
        elif tag_lower == "pre":
            self._handle_pre_end()
        elif tag_lower == "code" and self.in_code_block:
            self.in_code_block = False
        elif tag_lower == "div":
            self._handle_div_end()
        elif tag_lower == "br":
            pass
        elif tag_lower in ("ul", "ol"):
            self._handle_list_end()
        elif tag_lower == "dl":
            self._handle_list_end()
        elif tag_lower == "li":
            self._handle_list_item_end()
        elif tag_lower == "dt":
            self._handle_list_item_end()
        elif tag_lower == "dd":
            self._handle_list_item_end()
        elif tag_lower == "blockquote":
            self._handle_blockquote_end()
        elif tag_lower == "figure":
            self._handle_figure_end()
        elif tag_lower == "figcaption":
            self._pop_style_attr("in_figcaption")
        elif tag_lower == "table":
            self._handle_table_end()
        elif tag_lower == "caption":
            self._pop_style_attr("table_caption")
        elif tag_lower == "thead":
            self._handle_table_row_group_end("thead")
        elif tag_lower == "tbody":
            self._handle_table_row_group_end("tbody")
        elif tag_lower == "tfoot":
            self._handle_table_row_group_end("tfoot")
        elif tag_lower == "tr":
            self._handle_table_row_end()
        elif tag_lower in ("th", "td"):
            self._handle_table_cell_end()
        elif tag_lower == "form":
            self._handle_form_end()
        elif tag_lower == "textarea":
            self._handle_textarea_end()
        elif tag_lower == "select":
            self._handle_select_end()
        elif tag_lower == "optgroup":
            self._handle_optgroup_end()
        elif tag_lower == "option":
            self._handle_option_end()
        elif tag_lower == "button":
            self._handle_button_end()
        elif tag_lower == "fieldset":
            self._handle_fieldset_end()
        elif tag_lower == "legend":
            self._pop_style_attr("in_legend")
        elif tag_lower == "details":
            self._handle_details_end()
        elif tag_lower == "summary":
            self._pop_style_attr("in_summary")
        elif tag_lower == "dialog":
            self._handle_dialog_end()
        elif tag_lower == "article":
            self._handle_semantic_section_end("article")
        elif tag_lower == "section":
            self._handle_semantic_section_end("section")
        elif tag_lower == "nav":
            self._handle_semantic_section_end("nav")
        elif tag_lower == "aside":
            self._handle_semantic_section_end("aside")
        elif tag_lower == "header":
            self._handle_header_end()
        elif tag_lower == "footer":
            self._handle_footer_end()
        elif tag_lower == "main":
            self._handle_semantic_section_end("main")
        elif tag_lower == "address":
            self._handle_address_end()
        elif tag_lower == "style":
            self._pop_style_attr("in_style")
        elif tag_lower == "script":
            self._pop_style_attr("in_script")
        elif tag_lower == "template":
            self._pop_style_attr("in_template")
        elif tag_lower == "dir":
            self._handle_list_end()
        elif tag_lower == "menu":
            self._handle_list_end()
        elif tag_lower in ("b", "strong"):
            self._pop_style_attr("bold")
        elif tag_lower in ("i", "em"):
            self._pop_style_attr("italic")
        elif tag_lower in ("u", "ins"):
            self._pop_style_attr("underline")
        elif tag_lower in ("s", "del", "strike"):
            self._pop_style_attr("strikethrough")
        elif tag_lower == "small":
            self._pop_style_attr("small")
        elif tag_lower == "sub":
            self._pop_style_attr("subscript")
        elif tag_lower == "sup":
            self._pop_style_attr("superscript")
        elif tag_lower == "mark":
            self._pop_style_attr("highlight")
        elif tag_lower == "abbr":
            self._pop_style_attr("abbr_title")
        elif tag_lower == "q":
            self._pop_style_attr("quote_cite")
        elif tag_lower == "bdi":
            self._pop_style_attr("bdi_dir")
        elif tag_lower == "bdo":
            self._pop_style_attr("bdo_dir")
        elif tag_lower == "code":
            if not self.in_code_block:
                self._pop_style_attr("code")
        elif tag_lower == "time":
            self._pop_style_attr("datetime")
        elif tag_lower == "data":
            self._pop_style_attr("data_value")
        elif tag_lower == "dfn":
            self._pop_style_attr("italic")
        elif tag_lower == "samp":
            self._pop_style_attr("code")
        elif tag_lower == "kbd":
            self._pop_style_attr("code")
        elif tag_lower == "var":
            self._pop_style_attr("italic")
        elif tag_lower == "cite":
            self._pop_style_attr("italic")
        elif tag_lower == "big":
            self._pop_style_attr("big")
        elif tag_lower == "tt":
            self._pop_style_attr("code")
        elif tag_lower == "font":
            self._pop_style_attr("font_color")
            self._pop_style_attr("font_face")
            self._pop_style_attr("font_size")
        elif tag_lower == "center":
            self._pop_style_attr("center")

        if self.element_stack:
            while self.element_stack and self.element_stack[-1]["tag"] != tag_lower:
                self.element_stack.pop()
            if self.element_stack:
                self.element_stack.pop()

    def _pop_style_attr(self, name: str) -> None:
        if self.current_style_stack:
            self.current_style_stack[-1].pop(name, None)

    def _get_parsed_attr(self, name: str) -> str | None:
        for entry in reversed(self.element_stack):
            if name in entry.get("attrs", {}):
                return entry["attrs"][name]
        return None

    def _get_parsed_attrs_copy(self) -> dict[str, str]:
        for entry in reversed(self.element_stack):
            return dict(entry.get("attrs", {}))
        return {}

    def _handle_raw_text_end(self, tag: str) -> None:
        raw_content = "".join(self.current_text)
        self.current_text = []
        if tag == "style":
            self.css_styles = _parse_css_style_element(raw_content)
        elif tag == "script":
            script_type = self._get_attr("script_type") or "classic"
            meta: dict[str, Any] = {"script_type": script_type, "raw_content": raw_content}
            elem = self._create_logical_element(ElementType.MACRO, raw_content, meta)
            self._add_element(elem)
        elif tag == "template":
            meta = {"template_content": raw_content}
            elem = self._create_logical_element(ElementType.SECTION, raw_content, meta)
            self._add_element(elem)

    def handle_data(self, data: str) -> None:
        if self.skip_depth > 0:
            self.current_text.append(data)
            return
        if self.in_svg:
            self.svg_buffer.append(data)
            return
        if self.in_mathml:
            self.mathml_buffer.append(data)
            return
        if self._get_attr("in_title"):
            if self.document_title is None:
                self.document_title = data.strip()
            else:
                self.document_title += data.strip()
            return
        if self._get_attr("in_style") or self._get_attr("in_script") or self._get_attr("in_template"):
            self.current_text.append(data)
            return
        if self.in_code_block:
            self.current_text.append(data)
            return
        if self.current_cell is not None:
            self.current_text.append(data)
            return
        if self.current_select is not None and self._get_attr("in_option"):
            self.current_text.append(data)
            return
        if self._get_attr("in_legend"):
            self.current_text.append(data)
            return
        if self._get_attr("in_summary"):
            self.current_text.append(data)
            return
        if self._get_attr("in_figcaption"):
            self.current_text.append(data)
            return
        if self._get_attr("table_caption"):
            self.current_text.append(data)
            return
        if self._get_attr("in_textarea"):
            self.current_text.append(data)
            return
        if self._get_attr("in_label"):
            self.current_text.append(data)
            return
        self.current_text.append(data)

    def handle_entityref(self, name: str) -> None:
        char = entities.html5.get(f"&{name};", f"&{name};")
        self.current_text.append(char)

    def handle_charref(self, name: str) -> None:
        try:
            if name.startswith("x") or name.startswith("X"):
                char = chr(int(name[1:], 16))
            else:
                char = chr(int(name))
            self.current_text.append(char)
        except (ValueError, OverflowError):
            self.current_text.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        pass

    def handle_decl(self, decl: str) -> None:
        if decl.lower().startswith("doctype"):
            self.metadata["doctype"] = decl

    def unknown_decl(self, data: str) -> None:
        pass

    def _handle_html(self, attrs: dict[str, str]) -> None:
        lang = attrs.get("lang")
        direction = attrs.get("dir")
        if lang:
            self.metadata["lang"] = lang
        if direction:
            self.metadata["dir"] = direction

    def _handle_base(self, attrs: dict[str, str]) -> None:
        href = attrs.get("href")
        if href:
            self.base_href = href
            self.metadata["base_href"] = href

    def _handle_meta(self, attrs: dict[str, str]) -> None:
        charset = attrs.get("charset")
        if charset:
            self.metadata["charset"] = charset
            return
        name = attrs.get("name", "").lower()
        content = attrs.get("content", "")
        if name and content:
            self.metadata[f"meta_{name}"] = content
            return
        http_equiv = attrs.get("http-equiv", "").lower()
        if http_equiv and content:
            self.metadata[f"http_equiv_{http_equiv}"] = content
            return
        prop = attrs.get("property", "")
        if prop and content:
            self.metadata[f"og_{prop}"] = content

    def _handle_link(self, attrs: dict[str, str]) -> None:
        rel = attrs.get("rel", "")
        href = attrs.get("href", "")
        if rel and href:
            key = f"link_{rel}"
            if key not in self.metadata:
                self.metadata[key] = href

    def _handle_heading_start(self, tag: str, attrs: dict[str, str]) -> None:
        level = int(tag[1])
        self._close_implicit_sections_above(level)
        self._start_implicit_section(level, tag)
        self.current_heading = {
            "type": ElementType.HEADING,
            "level": level,
            "attrs": attrs,
        }
        if level <= 3:
            section = Section(
                section_id=f"section_{len(self.sections) + 1}",
                title=None,
                elements=[],
                metadata={"html_tag": tag, **attrs},
            )
            self._push_section(section)

    def _handle_heading_end(self) -> None:
        if self.current_heading and self.current_spans:
            content = HeadingContent(
                text=RichTextContent(spans=self.current_spans.copy()),
                level=self.current_heading["level"],
            )
            element = self._create_logical_element(
                ElementType.HEADING,
                content,
                self.current_heading.get("attrs", {}),
            )
            self._add_element(element)
        self.current_spans = []
        self.current_heading = None

    def _handle_paragraph_start(self, attrs: dict[str, str]) -> None:
        pass

    def _handle_paragraph_end(self) -> None:
        para = self._flush_text_as_paragraph()
        if para:
            element = self._create_logical_element(ElementType.PARAGRAPH, para)
            self._add_element(element)

    def _handle_pre_start(self, attrs: dict[str, str]) -> None:
        self.in_code_block = True
        self.current_text = []

    def _handle_pre_end(self) -> None:
        code_text = "".join(self.current_text)
        self.current_text = []
        self.in_code_block = False
        if code_text.strip():
            content = CodeContent(code=code_text, language=None)
            element = self._create_logical_element(ElementType.CODE, content)
            self._add_element(element)

    def _handle_horizontal_rule(self) -> None:
        content = PageBreakContent()
        element = self._create_logical_element(ElementType.PAGE_BREAK, content)
        self._add_element(element)

    def _handle_div_start(self, attrs: dict[str, str]) -> None:
        pass

    def _handle_div_end(self) -> None:
        para = self._flush_text_as_paragraph()
        if para:
            element = self._create_logical_element(ElementType.PARAGRAPH, para)
            self._add_element(element)

    def _handle_link_start(self, attrs: dict[str, str]) -> None:
        href = attrs.get("href", "")
        if href:
            self._set_style_attr("href", href)

    def _handle_list_start(self, tag: str, attrs: dict[str, str]) -> None:
        list_info: dict[str, Any] = {
            "type": ElementType.LIST,
            "tag": tag,
            "attrs": attrs,
            "ordered": tag == "ol",
            "items": [],
            "current_item": None,
        }
        self.list_stack.append(list_info)
        self.current_list = list_info

    def _handle_list_end(self) -> None:
        if self.list_stack:
            list_info = self.list_stack.pop()
            if list_info["items"]:
                content = ListContent(
                    items=list_info["items"],
                    ordered=list_info["ordered"],
                )
                element = self._create_logical_element(
                    ElementType.LIST,
                    content,
                    list_info.get("attrs", {}),
                )
                self._add_element(element)
            if self.list_stack:
                self.current_list = self.list_stack[-1]
            else:
                self.current_list = None

    def _handle_list_item_start(self, attrs: dict[str, str]) -> None:
        if self.current_list:
            self.current_list["current_item"] = {
                "elements": [],
                "attrs": attrs,
            }

    def _handle_list_item_end(self) -> None:
        if self.current_list and self.current_list["current_item"]:
            item_info = self.current_list["current_item"]
            if item_info["elements"]:
                item_content = ListItemContent(elements=item_info["elements"])
                item_element = self._create_logical_element(
                    ElementType.LIST_ITEM,
                    item_content,
                    item_info.get("attrs", {}),
                )
                self.current_list["items"].append(item_element)
            self.current_list["current_item"] = None

    def _handle_blockquote_start(self, attrs: dict[str, str]) -> None:
        pass

    def _handle_blockquote_end(self) -> None:
        self._flush_current_text()
        if self.current_spans:
            content = QuoteContent(elements=[])
            element = self._create_logical_element(ElementType.QUOTE, content)
            self._add_element(element)
            self.current_spans = []

    def _handle_figure_start(self, attrs: dict[str, str]) -> None:
        self.current_figure = {
            "attrs": attrs,
            "elements": [],
            "caption": None,
        }

    def _handle_figure_end(self) -> None:
        if self.current_figure:
            caption = self.current_figure.get("caption")
            meta = dict(self.current_figure.get("attrs", {}))
            if caption:
                meta["caption"] = caption
            section = Section(
                section_id=f"section_figure_{len(self.sections) + 1}",
                title=None,
                elements=[],
                section_type="figure",
                metadata=meta,
            )
            self._push_section(section)
            self.current_figure = None

    def _handle_image(self, attrs: dict[str, str]) -> None:
        src = attrs.get("src", "")
        alt = attrs.get("alt", "")
        if src:
            content = ImageContent(
                src=src,
                alt=alt,
                width=_safe_float(attrs.get("width")),
                height=_safe_float(attrs.get("height")),
                metadata={
                    "html_attrs": dict(attrs),
                    "title": attrs.get("title"),
                    "loading": attrs.get("loading"),
                    "srcset": attrs.get("srcset"),
                    "sizes": attrs.get("sizes"),
                },
            )
            element = self._create_logical_element(ElementType.IMAGE, content, attrs)
            self._add_element(element)

    def _handle_audio(self, attrs: dict[str, str]) -> None:
        src = attrs.get("src", "")
        content = AudioContent(
            src=src,
            autoplay=attrs.get("autoplay") is not None,
            controls=attrs.get("controls") is not None,
            loop=attrs.get("loop") is not None,
        )
        element = self._create_logical_element(ElementType.AUDIO, content, attrs)
        self._add_element(element)

    def _handle_video(self, attrs: dict[str, str]) -> None:
        src = attrs.get("src", "")
        content = VideoContent(
            src=src,
            width=_safe_int(attrs.get("width")) if attrs.get("width") else None,
            height=_safe_int(attrs.get("height")) if attrs.get("height") else None,
            poster=attrs.get("poster"),
            autoplay=attrs.get("autoplay") is not None,
            controls=attrs.get("controls") is not None,
        )
        element = self._create_logical_element(ElementType.VIDEO, content, attrs)
        self._add_element(element)

    def _handle_table_start(self, attrs: dict[str, str]) -> None:
        table_info: dict[str, Any] = {
            "type": ElementType.TABLE,
            "attrs": attrs,
            "rows": [],
            "current_row": None,
            "current_cell": None,
            "has_header": False,
            "caption": None,
        }
        self.table_stack.append(table_info)
        self.current_table = table_info

    def _handle_table_row_group_start(self, group_tag: str, attrs: dict[str, str]) -> None:
        if self.current_table:
            self.current_table["_current_group"] = group_tag

    def _handle_table_row_group_end(self, group_tag: str) -> None:
        if self.current_table:
            self.current_table.pop("_current_group", None)

    def _handle_table_row_start(self, attrs: dict[str, str]) -> None:
        if self.current_table:
            group = self.current_table.get("_current_group", "tbody")
            is_header = group == "thead"
            self.current_table["current_row"] = {
                "cells": [],
                "is_header": is_header,
                "attrs": attrs,
            }
            if is_header:
                self.current_table["has_header"] = True

    def _handle_table_row_end(self) -> None:
        if self.current_table and self.current_table["current_row"]:
            row_info = self.current_table["current_row"]
            if row_info["cells"]:
                table_row = TableRow(
                    cells=row_info["cells"],
                    is_header=row_info["is_header"],
                    metadata=row_info.get("attrs", {}),
                )
                self.current_table["rows"].append(table_row)
            self.current_table["current_row"] = None

    def _handle_table_cell_start(self, tag: str, attrs: dict[str, str]) -> None:
        if self.current_table and self.current_table["current_row"]:
            is_header = tag == "th"
            self.current_table["current_cell"] = {
                "elements": [],
                "is_header": is_header,
                "attrs": attrs,
                "col_span": _safe_int(attrs.get("colspan")),
                "row_span": _safe_int(attrs.get("rowspan")),
                "text_parts": [],
            }

    def _handle_table_cell_end(self) -> None:
        if (self.current_table and self.current_table["current_row"] and
                self.current_table["current_cell"]):
            cell_info = self.current_table["current_cell"]
            cell_text = "".join(cell_info.get("text_parts", [])).strip()
            cell_elements: list[LogicalElement] = []
            if cell_text:
                para = ParagraphContent(
                    text=RichTextContent(spans=[self._create_rich_text_span(cell_text)]),
                )
                cell_elements.append(
                    self._create_logical_element(ElementType.PARAGRAPH, para),
                )
            table_cell = TableCell(
                content=cell_elements,
                is_header=cell_info["is_header"],
                col_span=cell_info["col_span"],
                row_span=cell_info["row_span"],
                metadata=cell_info.get("attrs", {}),
            )
            self.current_table["current_row"]["cells"].append(table_cell)
            self.current_table["current_cell"] = None

    def _handle_table_end(self) -> None:
        if self.table_stack:
            table_info = self.table_stack.pop()
            if table_info["rows"]:
                content = TableContent(
                    rows=table_info["rows"],
                    caption=table_info.get("caption"),
                    metadata={
                        "has_header": table_info["has_header"],
                        **table_info.get("attrs", {}),
                    },
                )
                element = self._create_logical_element(
                    ElementType.TABLE,
                    content,
                    table_info.get("attrs", {}),
                )
                self._add_element(element)
            if self.table_stack:
                self.current_table = self.table_stack[-1]
            else:
                self.current_table = None

    def _handle_form_start(self, attrs: dict[str, str]) -> None:
        self.form_field_stack.append({
            "action": attrs.get("action", ""),
            "method": attrs.get("method", "get"),
            "enctype": attrs.get("enctype", ""),
            "fields": [],
        })

    def _handle_form_end(self) -> None:
        if self.form_field_stack:
            self.form_field_stack.pop()

    def _handle_input(self, attrs: dict[str, str]) -> None:
        input_type = attrs.get("type", "text")
        if input_type not in FORM_INPUT_TYPES:
            input_type = "text"
        field = FormFieldContent(
            field_name=attrs.get("name", ""),
            field_type=input_type,
            value=attrs.get("value", ""),
            default_value=attrs.get("value", ""),
            placeholder=attrs.get("placeholder", ""),
            required=attrs.get("required") is not None,
            read_only=attrs.get("readonly") is not None,
            max_length=_safe_int(attrs.get("maxlength")) if attrs.get("maxlength") else None,
            tooltip=attrs.get("title", ""),
        )
        element = self._create_logical_element(ElementType.FORM_FIELD, field, attrs)
        self._add_element(element)

    def _handle_textarea_start(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("in_textarea", True)
        self.current_text = []
        self.form_field_stack.append({
            "field_name": attrs.get("name", ""),
            "placeholder": attrs.get("placeholder"),
            "required": attrs.get("required") is not None,
            "read_only": attrs.get("readonly") is not None,
        })

    def _handle_textarea_end(self) -> None:
        text_value = "".join(self.current_text)
        self.current_text = []
        self._pop_style_attr("in_textarea")
        if self.form_field_stack:
            info = self.form_field_stack.pop()
            field = FormFieldContent(
                field_name=info.get("field_name", ""),
                field_type="textarea",
                value=text_value,
                placeholder=info.get("placeholder", ""),
                required=info.get("required", False),
                read_only=info.get("read_only", False),
            )
            element = self._create_logical_element(ElementType.FORM_FIELD, field)
            self._add_element(element)

    def _handle_select_start(self, attrs: dict[str, str]) -> None:
        self.current_select = {
            "field_name": attrs.get("name", ""),
            "multiple": attrs.get("multiple") is not None,
            "required": attrs.get("required") is not None,
            "options": [],
            "current_optgroup": None,
        }

    def _handle_select_end(self) -> None:
        if self.current_select:
            field = FormFieldContent(
                field_name=self.current_select["field_name"],
                field_type="select",
                options=[opt["value"] for opt in self.current_select["options"]],
                required=self.current_select["required"],
            )
            element = self._create_logical_element(ElementType.FORM_FIELD, field)
            self._add_element(element)
            self.current_select = None

    def _handle_optgroup_start(self, attrs: dict[str, str]) -> None:
        if self.current_select:
            self.current_select["current_optgroup"] = attrs.get("label", "")

    def _handle_optgroup_end(self) -> None:
        if self.current_select:
            self.current_select["current_optgroup"] = None

    def _handle_option_start(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("in_option", True)
        self.current_text = []
        if self.current_select:
            self.current_select["_current_option"] = {
                "value": attrs.get("value", ""),
                "selected": attrs.get("selected") is not None,
            }

    def _handle_option_end(self) -> None:
        option_text = "".join(self.current_text)
        self.current_text = []
        self._pop_style_attr("in_option")
        if self.current_select and self.current_select.get("_current_option"):
            opt = self.current_select["_current_option"]
            opt["value"] = opt["value"] or option_text
            self.current_select["options"].append(opt)
            self.current_select["_current_option"] = None

    def _handle_button_start(self, attrs: dict[str, str]) -> None:
        pass

    def _handle_button_end(self) -> None:
        self._flush_current_text()
        if self.current_spans:
            btn_text = "".join(s.text for s in self.current_spans)
            self.current_spans = []
            field = FormFieldContent(
                field_name="",
                field_type="button",
                value=btn_text,
            )
            element = self._create_logical_element(ElementType.FORM_FIELD, field)
            self._add_element(element)

    def _handle_fieldset_start(self, attrs: dict[str, str]) -> None:
        pass

    def _handle_fieldset_end(self) -> None:
        pass

    def _handle_progress(self, attrs: dict[str, str]) -> None:
        field = FormFieldContent(
            field_name="",
            field_type="progress",
            value=attrs.get("value", ""),
        )
        element = self._create_logical_element(ElementType.FORM_FIELD, field, attrs)
        self._add_element(element)

    def _handle_meter(self, attrs: dict[str, str]) -> None:
        field = FormFieldContent(
            field_name="",
            field_type="meter",
            value=attrs.get("value", ""),
        )
        element = self._create_logical_element(ElementType.FORM_FIELD, field, attrs)
        self._add_element(element)

    def _handle_details_start(self, attrs: dict[str, str]) -> None:
        self.current_details = {
            "open": attrs.get("open") is not None,
            "summary": None,
            "elements": [],
        }

    def _handle_details_end(self) -> None:
        self.current_details = None

    def _handle_dialog_start(self, attrs: dict[str, str]) -> None:
        self.in_dialog = True
        self.current_dialog = {
            "open": attrs.get("open") is not None,
            "elements": [],
        }

    def _handle_dialog_end(self) -> None:
        self.in_dialog = False
        self.current_dialog = None

    def _handle_iframe(self, attrs: dict[str, str]) -> None:
        meta = {
            "src": attrs.get("src", ""),
            "width": attrs.get("width"),
            "height": attrs.get("height"),
            "sandbox": attrs.get("sandbox"),
            "allow": attrs.get("allow"),
            "loading": attrs.get("loading"),
        }
        element = self._create_logical_element(ElementType.EMBEDDED_OBJECT, meta, attrs)
        self._add_element(element)

    def _handle_embed(self, attrs: dict[str, str]) -> None:
        meta = {
            "src": attrs.get("src", ""),
            "type": attrs.get("type", ""),
            "width": attrs.get("width"),
            "height": attrs.get("height"),
        }
        element = self._create_logical_element(ElementType.EMBEDDED_OBJECT, meta, attrs)
        self._add_element(element)

    def _handle_object(self, attrs: dict[str, str]) -> None:
        meta = {
            "data": attrs.get("data", ""),
            "type": attrs.get("type", ""),
            "width": attrs.get("width"),
            "height": attrs.get("height"),
        }
        element = self._create_logical_element(ElementType.EMBEDDED_OBJECT, meta, attrs)
        self._add_element(element)

    def _handle_canvas(self, attrs: dict[str, str]) -> None:
        meta = {
            "width": attrs.get("width"),
            "height": attrs.get("height"),
        }
        element = self._create_logical_element(ElementType.DRAWING, meta, attrs)
        self._add_element(element)

    def _handle_semantic_section_start(self, section_type: str, attrs: dict[str, str]) -> None:
        section = Section(
            section_id=f"section_{section_type}_{len(self.sections) + 1}",
            title=None,
            elements=[],
            section_type=section_type,
            metadata={"html_tag": section_type, **attrs},
        )
        self._push_section(section)

    def _handle_semantic_section_end(self, section_type: str) -> None:
        pass

    def _handle_header_start(self, attrs: dict[str, str]) -> None:
        section = Section(
            section_id=f"section_header_{len(self.sections) + 1}",
            title=None,
            elements=[],
            section_type="header",
            metadata={"html_tag": "header", **attrs},
        )
        self._push_section(section)

    def _handle_header_end(self) -> None:
        pass

    def _handle_footer_start(self, attrs: dict[str, str]) -> None:
        section = Section(
            section_id=f"section_footer_{len(self.sections) + 1}",
            title=None,
            elements=[],
            section_type="footer",
            metadata={"html_tag": "footer", **attrs},
        )
        self._push_section(section)

    def _handle_footer_end(self) -> None:
        pass

    def _handle_address_start(self, attrs: dict[str, str]) -> None:
        pass

    def _handle_address_end(self) -> None:
        para = self._flush_text_as_paragraph()
        if para:
            element = self._create_logical_element(ElementType.PARAGRAPH, para)
            self._add_element(element)

    def _handle_legacy_font(self, attrs: dict[str, str]) -> None:
        color = attrs.get("color")
        face = attrs.get("face")
        size = attrs.get("size")
        if color:
            self._set_style_attr("font_color", color)
        if face:
            self._set_style_attr("font_face", face)
        if size:
            self._set_style_attr("font_size", size)

    def _handle_legacy_center(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("center", True)

    def _handle_legacy_applet(self, attrs: dict[str, str]) -> None:
        meta = {
            "code": attrs.get("code", ""),
            "archive": attrs.get("archive", ""),
            "width": attrs.get("width"),
            "height": attrs.get("height"),
        }
        element = self._create_logical_element(ElementType.EMBEDDED_OBJECT, meta, attrs)
        self._add_element(element)

    def _handle_legacy_frame(self, attrs: dict[str, str]) -> None:
        meta = {
            "src": attrs.get("src", ""),
            "name": attrs.get("name", ""),
        }
        element = self._create_logical_element(ElementType.EMBEDDED_OBJECT, meta, attrs)
        self._add_element(element)


class HtmlParser(BaseDocumentParser):

    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> BaseDocument:
        try:
            encoding = "utf-8"
            if options and options.encoding:
                encoding = options.encoding
            html_content = data.decode(encoding)
            return await self.parse_text(html_content, document_id, source_name, metadata, options)
        except Exception as e:
            raise DocumentParseError(f"HTML parse error: {e}")

    async def parse_text(
        self,
        html_content: str,
        document_id: str,
        source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> BaseDocument:
        try:
            parser = HTMLDocumentParser()
            parser.feed(html_content)

            merged_metadata: dict[str, Any] = {
                "source_format": "html",
                "parser": "HtmlParser",
            }
            if options:
                merged_metadata["encoding"] = options.encoding
            if metadata:
                merged_metadata.update(metadata)
            if parser.metadata:
                merged_metadata["html_metadata"] = parser.metadata
            if parser.css_styles:
                merged_metadata["css_styles"] = parser.css_styles
            if parser.base_href:
                merged_metadata["base_href"] = parser.base_href

            if document_id == "":
                document_id = str(uuid.uuid4())
            if parser.document_title:
                source_name = parser.document_title
            if not source_name or source_name == "":
                source_name = "Untitled HTML Document"

            mt = detect_by_extension("html")
            document = USDMDocument(
                document_id=document_id,
                title=source_name,
                media_type=mt,
                sections=parser.sections,
                elements=parser.elements,
                logical_elements=parser.elements,
                metadata=merged_metadata,
            )
            return document
        except Exception as e:
            raise DocumentParseError(f"HTML parse error: {e}")

    async def parse_stream(
        self,
        stream: AsyncIterator[bytes],
        document_id: str = "",
        source_name: str = "",
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> BaseDocument:
        try:
            chunks: list[bytes] = []
            async for chunk in stream:
                chunks.append(chunk)
            encoding = "utf-8"
            if options and options.encoding:
                encoding = options.encoding
            html_content = b"".join(chunks).decode(encoding)
            return await self.parse_text(html_content, document_id, source_name, metadata, options)
        except Exception as e:
            raise DocumentParseError(f"HTML stream parse error: {e}")

    def get_supported_media_types(self) -> list[str]:
        return ["text/html", "application/xhtml+xml"]

    def get_supported_extensions(self) -> list[str]:
        return [".html", ".htm", ".xhtml"]

    async def parse_path(self, path, document_id="", metadata=None, options=None):
        from pathlib import Path as _P
        p = _P(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name, metadata, options)
