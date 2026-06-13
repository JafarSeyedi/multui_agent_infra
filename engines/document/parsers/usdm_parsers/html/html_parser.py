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
from .html_form import HTMLFormParser
from .html_media import HTMLMediaParser
from .html_parser_constants import (
    ARIA_ROLE_MAP, ARIA_STATES_PROPERTIES, FORM_INPUT_TYPES,
    INLINE_STYLE_PROPERTY_MAP, RAW_TEXT_ELEMENTS, RCDATA_ELEMENTS,
    SEMANTIC_HEADING, SEMANTIC_INLINE_FORMAT, SEMANTIC_SECTION_MAP,
    VOID_ELEMENTS,
)
from .html_parser_utils import (
    attrs_to_dict, build_character_style_from_css, extract_aria,
    extract_microdata, extract_rdfa, parse_css_style_element,
    parse_inline_style, safe_float, safe_int,
)
from .html_semantic import HTMLSemanticParser
from .html_table import HTMLTableParser


class HTMLDocumentParser(
    HTMLParser,
    HTMLMediaParser,
    HTMLTableParser,
    HTMLFormParser,
    HTMLSemanticParser,
):

    _START_TAG_HANDLERS: dict[str, tuple[str, str]] = {
        "html": ("_handle_html", "attrs"),
        "head": ("_start_head_impl", "attrs"),
        "body": ("_start_body_impl", "attrs"),
        "title": ("_set_in_title_impl", "attrs"),
        "base": ("_handle_base", "attrs"),
        "meta": ("_handle_meta", "attrs"),
        "link": ("_handle_link", "attrs"),
        "style": ("_handle_style_start_impl", "attrs"),
        "script": ("_handle_script_start_impl", "attrs"),
        "template": ("_handle_template_start_impl", "attrs"),
        "p": ("_handle_paragraph_start", "attrs"),
        "pre": ("_handle_pre_start", "attrs"),
        "code": ("_start_code_block_impl", "attrs"),
        "hr": ("_handle_horizontal_rule", "noargs"),
        "br": ("_start_br_wbr_impl", "attrs"),
        "wbr": ("_start_br_wbr_impl", "attrs"),
        "div": ("_handle_div_start", "attrs"),
        "a": ("_handle_link_start", "attrs"),
        "b": ("_set_bold_impl", "attrs"),
        "strong": ("_set_bold_impl", "attrs"),
        "i": ("_set_italic_impl", "attrs"),
        "em": ("_set_italic_impl", "attrs"),
        "u": ("_set_underline_impl", "attrs"),
        "ins": ("_set_underline_impl", "attrs"),
        "s": ("_set_strikethrough_impl", "attrs"),
        "del": ("_set_strikethrough_impl", "attrs"),
        "strike": ("_set_strikethrough_impl", "attrs"),
        "small": ("_set_small_impl", "attrs"),
        "sub": ("_set_subscript_impl", "attrs"),
        "sup": ("_set_superscript_impl", "attrs"),
        "mark": ("_set_mark_impl", "attrs"),
        "abbr": ("_set_abbr_impl", "attrs"),
        "q": ("_set_quote_impl", "attrs"),
        "bdi": ("_set_bdi_impl", "attrs"),
        "bdo": ("_set_bdo_impl", "attrs"),
        "time": ("_set_time_impl", "attrs"),
        "data": ("_set_data_impl", "attrs"),
        "dfn": ("_set_italic_impl", "attrs"),
        "cite": ("_set_italic_impl", "attrs"),
        "samp": ("_set_inline_code_impl", "attrs"),
        "kbd": ("_set_inline_code_impl", "attrs"),
        "var": ("_set_italic_impl", "attrs"),
        "big": ("_set_big_impl", "attrs"),
        "tt": ("_set_inline_code_impl", "attrs"),
        "ul": ("_handle_ul_start_impl", "attrs"),
        "ol": ("_handle_ol_start_impl", "attrs"),
        "li": ("_handle_list_item_start", "attrs"),
        "dl": ("_handle_dl_start_impl", "attrs"),
        "dt": ("_handle_list_item_start", "attrs"),
        "dd": ("_handle_list_item_start", "attrs"),
        "blockquote": ("_handle_blockquote_start", "attrs"),
        "figure": ("_handle_figure_start", "attrs"),
        "figcaption": ("_set_figcaption_impl", "attrs"),
        "img": ("_handle_image", "attrs"),
        "audio": ("_handle_audio", "attrs"),
        "video": ("_handle_video", "attrs"),
        "source": ("_noop", "noargs"),
        "track": ("_noop", "noargs"),
        "picture": ("_noop", "noargs"),
        "map": ("_noop", "noargs"),
        "area": ("_noop", "noargs"),
        "table": ("_handle_table_start", "attrs"),
        "caption": ("_set_caption_impl", "attrs"),
        "colgroup": ("_noop", "noargs"),
        "col": ("_noop", "noargs"),
        "thead": ("_handle_thead_start_impl", "attrs"),
        "tbody": ("_handle_tbody_start_impl", "attrs"),
        "tfoot": ("_handle_tfoot_start_impl", "attrs"),
        "tr": ("_handle_table_row_start", "attrs"),
        "th": ("_handle_th_start_impl", "attrs"),
        "td": ("_handle_td_start_impl", "attrs"),
        "form": ("_handle_form_start", "attrs"),
        "label": ("_set_label_impl", "attrs"),
        "input": ("_handle_input", "attrs"),
        "textarea": ("_handle_textarea_start", "attrs"),
        "select": ("_handle_select_start", "attrs"),
        "optgroup": ("_handle_optgroup_start", "attrs"),
        "option": ("_handle_option_start", "attrs"),
        "button": ("_handle_button_start", "attrs"),
        "fieldset": ("_handle_fieldset_start", "attrs"),
        "legend": ("_set_legend_impl", "attrs"),
        "progress": ("_handle_progress", "attrs"),
        "meter": ("_handle_meter", "attrs"),
        "details": ("_handle_details_start", "attrs"),
        "summary": ("_set_summary_impl", "attrs"),
        "dialog": ("_handle_dialog_start", "attrs"),
        "iframe": ("_handle_iframe", "attrs"),
        "embed": ("_handle_embed", "attrs"),
        "object": ("_handle_object", "attrs"),
        "param": ("_noop", "noargs"),
        "canvas": ("_handle_canvas", "attrs"),
        "article": ("_handle_article_start_impl", "attrs"),
        "section": ("_handle_section_start_impl", "attrs"),
        "nav": ("_handle_nav_start_impl", "attrs"),
        "aside": ("_handle_aside_start_impl", "attrs"),
        "header": ("_handle_header_start", "attrs"),
        "footer": ("_handle_footer_start", "attrs"),
        "main": ("_handle_main_start_impl", "attrs"),
        "address": ("_handle_address_start", "attrs"),
        "font": ("_handle_legacy_font", "attrs"),
        "center": ("_handle_legacy_center", "attrs"),
        "dir": ("_handle_dir_start_impl", "attrs"),
        "menu": ("_handle_menu_start_impl", "attrs"),
        "applet": ("_handle_legacy_applet", "attrs"),
        "frame": ("_handle_legacy_frame", "attrs"),
        "frameset": ("_noop", "noargs"),
        "noframes": ("_noop", "noargs"),
        "marquee": ("_noop", "noargs"),
        "blink": ("_noop", "noargs"),
        "basefont": ("_noop", "noargs"),
        "bgsound": ("_noop", "noargs"),
        "spacer": ("_noop", "noargs"),
        "xmp": ("_noop", "noargs"),
        "listing": ("_noop", "noargs"),
        "plaintext": ("_noop", "noargs"),
    }

    _END_TAG_HANDLERS: dict[str, tuple[str, str]] = {
        "title": ("_end_title_impl", "noargs"),
        "p": ("_handle_paragraph_end", "noargs"),
        "pre": ("_handle_pre_end", "noargs"),
        "code": ("_end_code_impl", "noargs"),
        "div": ("_handle_div_end", "noargs"),
        "ul": ("_handle_list_end", "noargs"),
        "ol": ("_handle_list_end", "noargs"),
        "dl": ("_handle_list_end", "noargs"),
        "li": ("_handle_list_item_end", "noargs"),
        "dt": ("_handle_list_item_end", "noargs"),
        "dd": ("_handle_list_item_end", "noargs"),
        "blockquote": ("_handle_blockquote_end", "noargs"),
        "figure": ("_handle_figure_end", "noargs"),
        "figcaption": ("_pop_figcaption_impl", "noargs"),
        "table": ("_handle_table_end", "noargs"),
        "caption": ("_pop_caption_impl", "noargs"),
        "thead": ("_pop_thead_impl", "noargs"),
        "tbody": ("_pop_tbody_impl", "noargs"),
        "tfoot": ("_pop_tfoot_impl", "noargs"),
        "tr": ("_handle_table_row_end", "noargs"),
        "th": ("_handle_table_cell_end", "noargs"),
        "td": ("_handle_table_cell_end", "noargs"),
        "form": ("_handle_form_end", "noargs"),
        "textarea": ("_handle_textarea_end", "noargs"),
        "select": ("_handle_select_end", "noargs"),
        "optgroup": ("_handle_optgroup_end", "noargs"),
        "option": ("_handle_option_end", "noargs"),
        "button": ("_handle_button_end", "noargs"),
        "fieldset": ("_handle_fieldset_end", "noargs"),
        "legend": ("_pop_legend_impl", "noargs"),
        "details": ("_handle_details_end", "noargs"),
        "summary": ("_pop_summary_impl", "noargs"),
        "dialog": ("_handle_dialog_end", "noargs"),
        "article": ("_pop_article_impl", "noargs"),
        "section": ("_pop_section_impl", "noargs"),
        "nav": ("_pop_nav_impl", "noargs"),
        "aside": ("_pop_aside_impl", "noargs"),
        "header": ("_handle_header_end", "noargs"),
        "footer": ("_handle_footer_end", "noargs"),
        "main": ("_pop_main_impl", "noargs"),
        "address": ("_handle_address_end", "noargs"),
        "style": ("_pop_style_impl", "noargs"),
        "script": ("_pop_script_impl", "noargs"),
        "template": ("_pop_template_impl", "noargs"),
        "dir": ("_handle_list_end", "noargs"),
        "menu": ("_handle_list_end", "noargs"),
        "b": ("_pop_bold_impl", "noargs"),
        "strong": ("_pop_bold_impl", "noargs"),
        "i": ("_pop_italic_impl", "noargs"),
        "em": ("_pop_italic_impl", "noargs"),
        "u": ("_pop_underline_impl", "noargs"),
        "ins": ("_pop_underline_impl", "noargs"),
        "s": ("_pop_strikethrough_impl", "noargs"),
        "del": ("_pop_strikethrough_impl", "noargs"),
        "strike": ("_pop_strikethrough_impl", "noargs"),
        "small": ("_pop_small_impl", "noargs"),
        "sub": ("_pop_subscript_impl", "noargs"),
        "sup": ("_pop_superscript_impl", "noargs"),
        "mark": ("_pop_mark_impl", "noargs"),
        "abbr": ("_pop_abbr_impl", "noargs"),
        "q": ("_pop_quote_impl", "noargs"),
        "bdi": ("_pop_bdi_impl", "noargs"),
        "bdo": ("_pop_bdo_impl", "noargs"),
        "time": ("_pop_time_impl", "noargs"),
        "data": ("_pop_data_impl", "noargs"),
        "dfn": ("_pop_italic_impl", "noargs"),
        "samp": ("_pop_code_impl", "noargs"),
        "kbd": ("_pop_code_impl", "noargs"),
        "var": ("_pop_italic_impl", "noargs"),
        "cite": ("_pop_italic_impl", "noargs"),
        "big": ("_pop_big_impl", "noargs"),
        "tt": ("_pop_code_impl", "noargs"),
        "font": ("_pop_font_impl", "noargs"),
        "center": ("_pop_center_impl", "noargs"),
    }




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
        role, aria_attrs = extract_aria(attrs)
        if role:
            meta["aria_role"] = role
        if aria_attrs:
            meta["aria_attributes"] = aria_attrs
        microdata = extract_microdata(attrs)
        if microdata:
            meta["microdata"] = microdata
        rdfa = extract_rdfa(attrs)
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
        attrs_dict = attrs_to_dict(attrs)
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

    def _call_handler(self, handler: tuple[str, str], attrs: dict[str, str]) -> None:
        method_name, call_style = handler
        method = getattr(self, method_name)
        if call_style == "attrs":
            method(attrs)
        elif call_style == "noargs":
            method()

    def _handle_starttag_impl(self, tag: str, attrs: dict[str, str]) -> None:
        self._flush_current_text()
        self._push_style_stack(tag, attrs)
        if tag in SEMANTIC_HEADING:
            self._handle_heading_start(tag, attrs)
        elif tag in ("ruby", "rt", "rp"):
            return
        else:
            handler = self._START_TAG_HANDLERS.get(tag)
            if handler:
                self._call_handler(handler, attrs)

    def _push_style_stack(self, tag: str, attrs: dict[str, str]) -> None:
        self.element_stack.append({
            "tag": tag,
            "attrs": attrs,
            "style": self._current_style().copy(),
        })
        style = self._current_style()
        style["tag"] = tag
        if "style" in attrs:
            css_props = parse_inline_style(attrs["style"])
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
                        width=safe_float(self._get_parsed_attr("width")),
                        height=safe_float(self._get_parsed_attr("height")),
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
        elif tag_lower == "code" and self.in_code_block:
            self.in_code_block = False
        elif tag_lower == "br":
            pass
        else:
            handler = self._END_TAG_HANDLERS.get(tag_lower)
            if handler:
                self._call_handler(handler, {})

        if self.element_stack:
            while self.element_stack and self.element_stack[-1]["tag"] != tag_lower:
                self.element_stack.pop()
            if self.element_stack:
                self.element_stack.pop()

    # ── Tag handler implementations (called by _START/END_TAG_HANDLERS dicts) ──

    def _noop(self) -> None:
        pass

    def _start_head_impl(self, attrs: dict[str, str]) -> None:
        self.in_head = True

    def _start_body_impl(self, attrs: dict[str, str]) -> None:
        self.in_head = False

    def _set_in_title_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("in_title", True)

    def _handle_style_start_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("in_style", True)
        self.current_text = []

    def _handle_script_start_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("in_script", True)
        self.current_text = []
        self._set_style_attr("script_type", attrs.get("type", "classic"))

    def _handle_template_start_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("in_template", True)
        self.current_text = []

    def _start_code_block_impl(self, attrs: dict[str, str]) -> None:
        if not self._get_code():
            self.in_code_block = True

    def _start_br_wbr_impl(self, attrs: dict[str, str]) -> None:
        self._flush_current_text()
        lb_content = LineBreakContent()
        elem = self._create_logical_element(ElementType.LINE_BREAK, lb_content, attrs)
        self._add_element(elem)

    def _set_bold_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("bold", True)

    def _set_italic_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("italic", True)

    def _set_underline_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("underline", True)

    def _set_strikethrough_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("strikethrough", True)

    def _set_small_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("small", True)

    def _set_subscript_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("subscript", True)

    def _set_superscript_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("superscript", True)

    def _set_mark_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("highlight", attrs.get("background", "yellow"))

    def _set_abbr_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("abbr_title", attrs.get("title"))

    def _set_quote_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("quote_cite", attrs.get("cite"))

    def _set_bdi_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("bdi_dir", attrs.get("dir", "auto"))

    def _set_bdo_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("bdo_dir", attrs.get("dir", "ltr"))

    def _set_time_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("datetime", attrs.get("datetime"))

    def _set_data_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("data_value", attrs.get("value"))

    def _set_inline_code_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("code", True)

    def _set_big_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("big", True)

    def _handle_ul_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_list_start("ul", attrs)

    def _handle_ol_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_list_start("ol", attrs)

    def _handle_dl_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_list_start("ul", attrs)

    def _set_figcaption_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("in_figcaption", True)

    def _set_caption_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("table_caption", True)

    def _handle_thead_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_table_row_group_start("thead", attrs)

    def _handle_tbody_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_table_row_group_start("tbody", attrs)

    def _handle_tfoot_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_table_row_group_start("tfoot", attrs)

    def _handle_th_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_table_cell_start("th", attrs)

    def _handle_td_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_table_cell_start("td", attrs)

    def _set_label_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("label_for", attrs.get("for"))

    def _set_legend_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("in_legend", True)

    def _set_summary_impl(self, attrs: dict[str, str]) -> None:
        self._set_style_attr("in_summary", True)

    def _handle_article_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_semantic_section_start("article", attrs)

    def _handle_section_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_semantic_section_start("section", attrs)

    def _handle_nav_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_semantic_section_start("nav", attrs)

    def _handle_aside_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_semantic_section_start("aside", attrs)

    def _handle_main_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_semantic_section_start("main", attrs)

    def _handle_dir_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_list_start("ul", attrs)

    def _handle_menu_start_impl(self, attrs: dict[str, str]) -> None:
        self._handle_list_start("ul", attrs)

    # ── End-tag handler implementations ──

    def _end_title_impl(self) -> None:
        self._pop_style_attr("in_title")

    def _end_code_impl(self) -> None:
        if not self.in_code_block:
            self._pop_style_attr("code")

    def _pop_figcaption_impl(self) -> None:
        self._pop_style_attr("in_figcaption")

    def _pop_caption_impl(self) -> None:
        self._pop_style_attr("table_caption")

    def _pop_thead_impl(self) -> None:
        self._handle_table_row_group_end("thead")

    def _pop_tbody_impl(self) -> None:
        self._handle_table_row_group_end("tbody")

    def _pop_tfoot_impl(self) -> None:
        self._handle_table_row_group_end("tfoot")

    def _pop_legend_impl(self) -> None:
        self._pop_style_attr("in_legend")

    def _pop_summary_impl(self) -> None:
        self._pop_style_attr("in_summary")

    def _pop_article_impl(self) -> None:
        self._handle_semantic_section_end("article")

    def _pop_section_impl(self) -> None:
        self._handle_semantic_section_end("section")

    def _pop_nav_impl(self) -> None:
        self._handle_semantic_section_end("nav")

    def _pop_aside_impl(self) -> None:
        self._handle_semantic_section_end("aside")

    def _pop_main_impl(self) -> None:
        self._handle_semantic_section_end("main")

    def _pop_style_impl(self) -> None:
        self._pop_style_attr("in_style")

    def _pop_script_impl(self) -> None:
        self._pop_style_attr("in_script")

    def _pop_template_impl(self) -> None:
        self._pop_style_attr("in_template")

    def _pop_bold_impl(self) -> None:
        self._pop_style_attr("bold")

    def _pop_italic_impl(self) -> None:
        self._pop_style_attr("italic")

    def _pop_underline_impl(self) -> None:
        self._pop_style_attr("underline")

    def _pop_strikethrough_impl(self) -> None:
        self._pop_style_attr("strikethrough")

    def _pop_small_impl(self) -> None:
        self._pop_style_attr("small")

    def _pop_subscript_impl(self) -> None:
        self._pop_style_attr("subscript")

    def _pop_superscript_impl(self) -> None:
        self._pop_style_attr("superscript")

    def _pop_mark_impl(self) -> None:
        self._pop_style_attr("highlight")

    def _pop_abbr_impl(self) -> None:
        self._pop_style_attr("abbr_title")

    def _pop_quote_impl(self) -> None:
        self._pop_style_attr("quote_cite")

    def _pop_bdi_impl(self) -> None:
        self._pop_style_attr("bdi_dir")

    def _pop_bdo_impl(self) -> None:
        self._pop_style_attr("bdo_dir")

    def _pop_time_impl(self) -> None:
        self._pop_style_attr("datetime")

    def _pop_data_impl(self) -> None:
        self._pop_style_attr("data_value")

    def _pop_code_impl(self) -> None:
        self._pop_style_attr("code")

    def _pop_big_impl(self) -> None:
        self._pop_style_attr("big")

    def _pop_font_impl(self) -> None:
        self._pop_style_attr("font_color")
        self._pop_style_attr("font_face")
        self._pop_style_attr("font_size")

    def _pop_center_impl(self) -> None:
        self._pop_style_attr("center")

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
            self.css_styles = parse_css_style_element(raw_content)
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
