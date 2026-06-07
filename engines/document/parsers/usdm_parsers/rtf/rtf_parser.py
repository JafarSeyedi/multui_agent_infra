from __future__ import annotations

import re
import uuid
from collections.abc import AsyncIterator
from copy import deepcopy
from pathlib import Path
from typing import Any

from ....models.base import ElementType
from ....models.exceptions import DocumentParseError
from ....models.media_detection import detect_by_extension
from ....models.usdm_models import CharacterStyle
from ....models.usdm_models import DocumentElement
from ....models.usdm_models import FooterContent
from ....models.usdm_models import FootnoteContent
from ....models.usdm_models import HeaderContent
from ....models.usdm_models import ImageContent
from ....models.usdm_models import LogicalElement
from ....models.usdm_models import PageBreakContent
from ....models.usdm_models import ParagraphContent
from ....models.usdm_models import ParagraphStyle
from ....models.usdm_models import RichTextContent
from ....models.usdm_models import RichTextSpan
from ....models.usdm_models import Section
from ....models.usdm_models import StyleSheet
from ....models.usdm_models import TableCell
from ....models.usdm_models import TableContent
from ....models.usdm_models import TableRow
from ....models.usdm_models import USDMDocument
from ..base import BaseDocumentParser
from ..base import ParseOptions


class RtfState:
    """Tracks the current formatting state during RTF parsing."""

    def __init__(self) -> None:
        self.font_index: int = 0
        self.font_size: float = 24.0
        self.text_color: str | None = None
        self.background_color: str | None = None
        self.highlight_color: str | None = None
        self.bold: bool = False
        self.italic: bool = False
        self.underline: bool = False
        self.strikethrough: bool = False
        self.superscript: bool = False
        self.subscript: bool = False
        self.small_caps: bool = False
        self.all_caps: bool = False
        self.alignment: str | None = None
        self.indent_left: float = 0.0
        self.indent_right: float = 0.0
        self.first_line_indent: float = 0.0
        self.spacing_before: float = 0.0
        self.spacing_after: float = 0.0
        self.line_spacing: float | None = None
        self.in_table: bool = False
        self.in_header: bool = False
        self.in_footer: bool = False
        self.in_footnote: bool = False
        self.hidden: bool = False
        self.list_level: int = 0
        self.list_override: int = 0
        self.tab_stops: list[float] = []

    def clone(self) -> RtfState:
        return deepcopy(self)

    def to_character_style_name(self) -> str | None:
        parts = []
        if self.bold:
            parts.append("bold")
        if self.italic:
            parts.append("italic")
        if self.underline:
            parts.append("underline")
        if self.strikethrough:
            parts.append("strike")
        if self.superscript:
            parts.append("super")
        if self.subscript:
            parts.append("sub")
        if self.small_caps:
            parts.append("scaps")
        if self.all_caps:
            parts.append("caps")
        if self.font_size != 24.0:
            parts.append(f"fs{int(self.font_size)}")
        for attr, prefix in [("text_color", "tc"), ("background_color", "bc"), ("highlight_color", "hl")]:
            val = getattr(self, attr)
            if val:
                parts.append(f"{prefix}{val}")
        if self.font_index > 0:
            parts.append(f"f{self.font_index}")
        return "_".join(parts) if parts else None


class RtfInterpreter:
    """Walks the RTF token tree and converts to USDM model."""

    def __init__(self) -> None:
        self.sections: list[Section] = []
        self.elements: list[DocumentElement] = []
        self.logical_elements: list[LogicalElement] = []
        self.character_styles: dict[str, CharacterStyle] = {}
        self.paragraph_styles: dict[str, ParagraphStyle] = {}
        self.font_table: dict[int, dict[str, Any]] = {}
        self.color_table: dict[int, str] = {}
        self.info: dict[str, str] = {}
        self.headers: list[HeaderContent] = []
        self.footers: list[FooterContent] = []
        self.footnotes: list[FootnoteContent] = []
        self.state = RtfState()
        self.state_stack: list[RtfState] = []
        self.current_text: list[str] = []
        self.current_spans: list[RichTextSpan] = []
        self.current_section: Section | None = None
        self.element_counter: int = 0
        self.current_table_rows: list[TableRow] = []
        self.current_row_cells: list[TableCell] = []
        self.current_footnote_id: str | None = None
        self.ansi_codepage: int = 1252
        self.unicode_fallback_char: str = "?"
        self.document_title: str | None = None
        self._skip_group_depth: int = 0

    def _generate_id(self) -> str:
        self.element_counter += 1
        return f"rtf_elem_{self.element_counter}"

    def _ensure_section(self) -> Section:
        if self.current_section is None:
            self.current_section = Section(
                section_id=f"section_{len(self.sections) + 1}",
                title=None, elements=[], metadata={},
            )
            self.sections.append(self.current_section)
        return self.current_section

    def _add_element(self, logical_elem: LogicalElement) -> None:
        self.logical_elements.append(logical_elem)
        self.elements.append(DocumentElement(
            element_id=logical_elem.element_id,
            element_type=logical_elem.element_type,
            metadata=logical_elem.metadata,
        ))
        self._ensure_section().elements.append(self.elements[-1])

    def _flush_spans(self) -> list[RichTextSpan]:
        if self.current_text:
            text = "".join(self.current_text)
            if text:
                style_name = self.state.to_character_style_name()
                if style_name and style_name not in self.character_styles:
                    self._build_character_style(style_name)
                self.current_spans.append(RichTextSpan(
                    text=text, character_style=style_name or None,
                    bold=self.state.bold, italic=self.state.italic,
                    underline=self.state.underline, color=self.state.text_color,
                    font=self._get_font_name(),
                ))
            self.current_text = []
        return self.current_spans

    def _get_font_name(self) -> str | None:
        if self.state.font_index in self.font_table:
            return self.font_table[self.state.font_index].get("name")
        return None

    def _build_character_style(self, name: str) -> None:
        if name in self.character_styles:
            return
        s = self.state
        self.character_styles[name] = CharacterStyle(
            name=name,
            bold=s.bold if s.bold else None,
            italic=s.italic if s.italic else None,
            underline=s.underline if s.underline else None,
            strike=s.strikethrough if s.strikethrough else None,
            superscript=s.superscript if s.superscript else None,
            subscript=s.subscript if s.subscript else None,
            small_caps=s.small_caps if s.small_caps else None,
            all_caps=s.all_caps if s.all_caps else None,
            color=s.text_color, highlight=s.highlight_color,
            background=s.background_color, font=self._get_font_name(),
            size=s.font_size if s.font_size != 24.0 else None,
        )

    def _build_paragraph_style(self, name: str) -> None:
        if name in self.paragraph_styles:
            return
        s = self.state
        self.paragraph_styles[name] = ParagraphStyle(
            name=name, alignment=s.alignment,
            indent_left=s.indent_left if s.indent_left > 0 else None,
            indent_right=s.indent_right if s.indent_right > 0 else None,
            first_line_indent=s.first_line_indent if s.first_line_indent != 0 else None,
            spacing_before=s.spacing_before if s.spacing_before > 0 else None,
            spacing_after=s.spacing_after if s.spacing_after > 0 else None,
            line_spacing=s.line_spacing,
        )

    def _resolve_color(self, index: int) -> str | None:
        return self.color_table.get(index)

    def _emit_paragraph(self) -> None:
        self._flush_spans()
        if not self.current_spans:
            return
        para_style_name = None
        s = self.state
        if s.alignment or s.indent_left or s.indent_right:
            pp = []
            if s.alignment:
                pp.append(s.alignment)
            if s.indent_left:
                pp.append(f"li{int(s.indent_left)}")
            if s.indent_right:
                pp.append(f"ri{int(s.indent_right)}")
            if s.first_line_indent:
                pp.append(f"fi{int(s.first_line_indent)}")
            para_style_name = "_".join(pp)
            self._build_paragraph_style(para_style_name)
        self._add_element(LogicalElement(
            element_id=self._generate_id(), element_type=ElementType.PARAGRAPH,
            content=ParagraphContent(
                text=RichTextContent(spans=list(self.current_spans)),
                style=para_style_name,
            ),
            metadata={"source": "rtf"},
        ))
        self.current_spans = []

    def _emit_page_break(self) -> None:
        self._add_element(LogicalElement(
            element_id=self._generate_id(), element_type=ElementType.PAGE_BREAK,
            content=PageBreakContent(), metadata={"source": "rtf"},
        ))

    def _start_table_row(self) -> None:
        self.state.in_table = True
        self.current_row_cells = []

    def _end_table_cell(self) -> None:
        self._flush_spans()
        cell_elements: list[LogicalElement] = []
        if self.current_spans:
            cell_elements.append(LogicalElement(
                element_id=self._generate_id(), element_type=ElementType.PARAGRAPH,
                content=ParagraphContent(text=RichTextContent(spans=list(self.current_spans))),
                metadata={},
            ))
            self.current_spans = []
        self.current_row_cells.append(TableCell(content=cell_elements, is_header=False, metadata={}))

    def _end_table_row(self) -> None:
        if self.current_row_cells:
            self.current_table_rows.append(TableRow(cells=list(self.current_row_cells), is_header=False, metadata={}))
        self.current_row_cells = []
        self.state.in_table = False

    def _emit_table(self) -> None:
        if not self.current_table_rows:
            return
        self._add_element(LogicalElement(
            element_id=self._generate_id(), element_type=ElementType.TABLE,
            content=TableContent(rows=list(self.current_table_rows), metadata={"source": "rtf"}),
            metadata={"source": "rtf"},
        ))
        self.current_table_rows = []

    def _emit_footnote(self) -> None:
        self._flush_spans()
        if not self.current_spans or not self.current_footnote_id:
            return
        self.footnotes.append(FootnoteContent(
            note_id=self.current_footnote_id,
            elements=[LogicalElement(
                element_id=self._generate_id(), element_type=ElementType.PARAGRAPH,
                content=ParagraphContent(text=RichTextContent(spans=list(self.current_spans))),
                metadata={},
            )],
        ))
        self.current_spans = []
        self.current_footnote_id = None

    def _emit_header(self) -> None:
        self._flush_spans()
        if not self.current_spans:
            return
        self.headers.append(HeaderContent(elements=[LogicalElement(
            element_id=self._generate_id(), element_type=ElementType.PARAGRAPH,
            content=ParagraphContent(text=RichTextContent(spans=list(self.current_spans))),
            metadata={},
        )]))
        self.current_spans = []

    def _emit_footer(self) -> None:
        self._flush_spans()
        if not self.current_spans:
            return
        self.footers.append(FooterContent(elements=[LogicalElement(
            element_id=self._generate_id(), element_type=ElementType.PARAGRAPH,
            content=ParagraphContent(text=RichTextContent(spans=list(self.current_spans))),
            metadata={},
        )]))
        self.current_spans = []

    def parse(self, data: bytes) -> USDMDocument:
        text = data.decode("ascii", errors="replace")
        tokens = self._tokenize(text)
        self._process_tokens(tokens)
        if self.current_spans:
            self._emit_paragraph()
        if self.current_table_rows:
            self._emit_table()
        metadata: dict[str, Any] = {
            "source_format": "rtf", "parser": "RTFParser",
            "font_count": len(self.font_table), "color_count": len(self.color_table),
        }
        if self.info:
            metadata["info"] = self.info
        for key, val in [("headers", self.headers), ("footers", self.footers), ("footnotes", self.footnotes)]:
            if val:
                metadata[f"{key}_count"] = len(val)  # type: ignore[arg-type]
        if not self.sections:
            self._ensure_section()
        return USDMDocument(
            document_id=str(uuid.uuid4()),
            title=self.document_title or "Untitled RTF Document",
            media_type=detect_by_extension(".rtf"),
            sections=self.sections, elements=self.elements,
            logical_elements=self.logical_elements,
            stylesheet=StyleSheet(
                character_styles=dict(self.character_styles),
                paragraph_styles=dict(self.paragraph_styles),
            ),
            metadata=metadata,
        )

    def _tokenize(self, text: str) -> list[tuple[str, Any]]:
        tokens: list[tuple[str, Any]] = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == "{":
                tokens.append(("GROUP_START", None))
                i += 1
            elif ch == "}":
                tokens.append(("GROUP_END", None))
                i += 1
            elif ch == "\\":
                i += 1
                if i >= len(text):
                    break
                next_ch = text[i]
                if next_ch in ("\\", "{", "}"):
                    tokens.append(("TEXT", next_ch))
                    i += 1
                elif next_ch == "~":
                    tokens.append(("SYMBOL", "\u00a0"))
                    i += 1
                elif next_ch == "-":
                    tokens.append(("SYMBOL", "\u00ad"))
                    i += 1
                elif next_ch == "'":
                    hex_str = text[i + 1 : i + 3]
                    try:
                        tokens.append(("HEX", int(hex_str, 16)))
                    except (ValueError, IndexError):
                        tokens.append(("TEXT", "?"))
                    i += 3
                elif next_ch == "*":
                    tokens.append(("STAR", None))
                    i += 1
                elif next_ch == "|":
                    tokens.append(("SYMBOL", "\u00b6"))
                    i += 1
                elif next_ch == ":":
                    tokens.append(("SYMBOL", "\u00a7"))
                    i += 1
                elif next_ch in ("\n", "\r"):
                    i += 1
                elif next_ch.isalpha():
                    ws = i
                    while i < len(text) and text[i].isalpha():
                        i += 1
                    word = text[ws:i]
                    param = None
                    if i < len(text) and (text[i] == "-" or text[i].isdigit()):
                        ps = i
                        i += 1
                        while i < len(text) and text[i].isdigit():
                            i += 1
                        param = int(text[ps:i])
                    if i < len(text) and text[i] == " ":
                        i += 1
                    tokens.append(("CONTROL", (word, param)))
                else:
                    tokens.append(("TEXT", next_ch))
                    i += 1
            elif ch in ("\r", "\n"):
                i += 1
            else:
                ts = i
                while i < len(text) and text[i] not in ("\\", "{", "}", "\r", "\n"):
                    i += 1
                tokens.append(("TEXT_CONTENT", text[ts:i]))
        return tokens

    def _process_tokens(self, tokens: list[tuple[str, Any]]) -> None:
        i = 0
        while i < len(tokens):
            tok_type, tok_val = tokens[i]
            if tok_type == "GROUP_START":
                i += 1
                if i < len(tokens) and tokens[i][0] == "STAR":
                    i += 1
                    if i < len(tokens) and tokens[i][0] == "CONTROL":
                        word, param = tokens[i][1]
                        dispatch = {
                            "fonttbl": self._parse_font_table,
                            "colortbl": self._parse_color_table,
                            "info": self._parse_info,
                            "pict": self._parse_pict,
                            "field": self._parse_field,
                        }
                        if word in dispatch:
                            i = dispatch[word](tokens, i + 1)
                        elif word in ("stylesheet", "object", "pn"):
                            i = self._skip_group(tokens, i)
                        else:
                            i = self._skip_group(tokens, i - 1)
                    else:
                        i = self._skip_group(tokens, i - 1)
                else:
                    self.state_stack.append(self.state.clone())
                    self._skip_group_depth += 1
            elif tok_type == "GROUP_END":
                if self.state_stack and self._skip_group_depth > 0:
                    self.state = self.state_stack.pop()
                    self._skip_group_depth -= 1
                i += 1
            elif tok_type == "CONTROL":
                i = self._handle_control_word(tokens, i)
            elif tok_type == "TEXT_CONTENT":
                if not self.state.hidden and self._skip_group_depth == 0:
                    self.current_text.append(tok_val)
                i += 1
            elif tok_type == "HEX":
                if not self.state.hidden and self._skip_group_depth == 0:
                    try:
                        self.current_text.append(bytes([tok_val]).decode(f"cp{self.ansi_codepage}", errors="replace"))
                    except (LookupError, ValueError):
                        self.current_text.append("?")
                i += 1
            elif tok_type == "SYMBOL":
                if not self.state.hidden and self._skip_group_depth == 0:
                    self.current_text.append(tok_val)
                i += 1
            else:
                i += 1

    def _skip_group(self, tokens: list[tuple[str, Any]], start: int) -> int:
        depth = 1
        i = start
        while i < len(tokens) and depth > 0:
            if tokens[i][0] == "GROUP_START":
                depth += 1
            elif tokens[i][0] == "GROUP_END":
                depth -= 1
            i += 1
        return i

    def _parse_font_table(self, tokens: list[tuple[str, Any]], start: int) -> int:
        depth = 1
        i = start
        current_font: dict[str, Any] = {}
        font_index = 0
        font_name_parts: list[str] = []
        while i < len(tokens) and depth > 0:
            tok_type, tok_val = tokens[i]
            if tok_type == "GROUP_START":
                depth += 1
                if depth == 2:
                    current_font = {}
                    font_name_parts = []
                i += 1
            elif tok_type == "GROUP_END":
                depth -= 1
                if depth == 1 and current_font:
                    if font_name_parts:
                        current_font["name"] = " ".join(font_name_parts).rstrip(";")
                    self.font_table[font_index] = current_font
                    font_index += 1
                i += 1
            elif tok_type == "CONTROL" and depth == 2:
                word, param = tok_val
                if word == "f" and param is not None:
                    current_font["index"] = param
                    font_index = param
                elif word in ("fnil", "froman", "fswiss", "fmodern", "fscript", "fdecor", "ftech", "fbidi"):
                    current_font["family"] = word[1:]
                elif word == "fcharset" and param is not None:
                    current_font["charset"] = param
                elif word == "fprq" and param is not None:
                    current_font["pitch"] = param
                i += 1
            elif tok_type == "TEXT_CONTENT" and depth >= 2:
                font_name_parts.append(tok_val)
                i += 1
            else:
                i += 1
        return i

    def _parse_color_table(self, tokens: list[tuple[str, Any]], start: int) -> int:
        i = start
        depth = 1
        r, g, b = 0, 0, 0
        index = 0
        while i < len(tokens) and depth > 0:
            tok_type, tok_val = tokens[i]
            if tok_type == "GROUP_START":
                depth += 1
                i += 1
            elif tok_type == "GROUP_END":
                depth -= 1
                if depth == 1:
                    self.color_table[index] = f"#{r:02x}{g:02x}{b:02x}"
                    index += 1
                    r, g, b = 0, 0, 0
                i += 1
            elif tok_type == "CONTROL":
                word, param = tok_val
                if word == "red" and param is not None:
                    r = param
                elif word == "green" and param is not None:
                    g = param
                elif word == "blue" and param is not None:
                    b = param
                i += 1
            else:
                i += 1
        return i

    def _parse_info(self, tokens: list[tuple[str, Any]], start: int) -> int:
        depth = 1
        i = start
        current_key = ""
        text_parts: list[str] = []
        info_keys = {
            "title", "author", "subject", "keywords", "operator",
            "company", "creatim", "revtim", "version", "edmins",
            "nofpages", "nofwords", "nofchars", "doccomm", "hlinkbase",
        }
        while i < len(tokens) and depth > 0:
            tok_type, tok_val = tokens[i]
            if tok_type == "GROUP_START":
                depth += 1
                i += 1
            elif tok_type == "GROUP_END":
                depth -= 1
                if depth == 1 and current_key:
                    self.info[current_key] = "".join(text_parts).strip()
                    current_key = ""
                    text_parts = []
                i += 1
            elif tok_type == "CONTROL":
                word, param = tok_val
                if word in info_keys:
                    current_key = word
                i += 1
            elif tok_type == "TEXT_CONTENT" and current_key:
                text_parts.append(tok_val)
                if current_key == "title" and not self.document_title:
                    self.document_title = tok_val.strip()
                i += 1
            else:
                i += 1
        return i

    def _parse_pict(self, tokens: list[tuple[str, Any]], start: int) -> int:
        depth = 1
        i = start
        has_data = False
        pict_format = "unknown"
        while i < len(tokens) and depth > 0:
            tok_type, tok_val = tokens[i]
            if tok_type == "GROUP_START":
                depth += 1
                i += 1
            elif tok_type == "GROUP_END":
                depth -= 1
                i += 1
            elif tok_type == "CONTROL":
                word, param = tok_val
                if word == "pngblip":
                    pict_format = "png"
                elif word == "jpegblip":
                    pict_format = "jpeg"
                elif word == "wmetafile" and param is not None:
                    pict_format = f"wmf{param}"
                i += 1
            elif tok_type == "TEXT_CONTENT":
                if re.match(r"^[0-9a-fA-F\s]+$", tok_val.strip()):
                    has_data = True
                i += 1
            else:
                i += 1
        if has_data:
            self._add_element(LogicalElement(
                element_id=self._generate_id(), element_type=ElementType.IMAGE,
                content=ImageContent(
                    src=f"pict_{pict_format}", alt=f"Embedded image ({pict_format})",
                    metadata={"format": pict_format, "source": "rtf"},
                ),
                metadata={"source": "rtf", "format": pict_format},
            ))
        return i

    def _parse_field(self, tokens: list[tuple[str, Any]], start: int) -> int:
        depth = 1
        i = start
        field_result_parts: list[str] = []
        in_result = False
        while i < len(tokens) and depth > 0:
            tok_type, tok_val = tokens[i]
            if tok_type == "GROUP_START":
                depth += 1
                i += 1
            elif tok_type == "GROUP_END":
                depth -= 1
                i += 1
            elif tok_type == "CONTROL":
                word, param = tok_val
                if word == "fldrslt":
                    in_result = True
                elif word == "fldinst":
                    in_result = False
                i += 1
            elif tok_type == "TEXT_CONTENT" and in_result:
                field_result_parts.append(tok_val)
                i += 1
            else:
                i += 1
        if field_result_parts:
            result_text = "".join(field_result_parts).strip()
            if result_text:
                self.current_text.append(result_text)
        return i

    def _handle_control_word(self, tokens: list[tuple[str, Any]], i: int) -> int:
        word, param = tokens[i][1]
        if self._skip_group_depth > 0 and not self.state_stack:
            return i + 1
        s = self.state
        if word == "par":
            self._end_table_cell() if s.in_table else self._emit_paragraph()
        elif word == "line":
            self.current_text.append("\n")
        elif word == "tab":
            self.current_text.append("\t")
        elif word in ("page", "column"):
            self._emit_page_break()
        elif word == "sect":
            self._emit_paragraph()
            self.sections.append(Section(
                section_id=f"section_{len(self.sections) + 1}",
                title=None, elements=[],
                metadata={"source": "rtf", "break_type": "section"},
            ))
            self.current_section = self.sections[-1]
        elif word in ("header", "headerf"):
            self._emit_paragraph()
            s.in_header = True
        elif word in ("footer", "footerf"):
            self._emit_paragraph()
            s.in_footer = True
        elif word == "footnote":
            self._emit_paragraph()
            s.in_footnote = True
            self.current_footnote_id = f"fn_{len(self.footnotes) + 1}"
        elif word == "trowd":
            self._start_table_row()
        elif word == "row":
            self._end_table_row()
        elif word == "cell":
            self._end_table_cell()
        elif word == "intbl":
            s.in_table = True
        elif word == "b":
            s.bold = param != 0 if param is not None else True
        elif word == "i":
            s.italic = param != 0 if param is not None else True
        elif word == "ul":
            s.underline = True
        elif word == "ulnone":
            s.underline = False
        elif word == "strike":
            s.strikethrough = param != 0 if param is not None else True
        elif word == "super":
            s.superscript = True
            s.subscript = False
        elif word == "sub":
            s.subscript = True
            s.superscript = False
        elif word == "nosupersub":
            s.superscript = False
            s.subscript = False
        elif word == "scaps":
            s.small_caps = param != 0 if param is not None else True
        elif word == "caps":
            s.all_caps = param != 0 if param is not None else True
        elif word == "fs" and param is not None:
            s.font_size = param
        elif word == "f" and param is not None:
            s.font_index = param
        elif word == "cf" and param is not None:
            s.text_color = self._resolve_color(param)
        elif word == "cb" and param is not None:
            s.background_color = self._resolve_color(param)
        elif word == "highlight" and param is not None:
            s.highlight_color = self._resolve_color(param)
        elif word == "ql":
            s.alignment = "left"
        elif word == "qr":
            s.alignment = "right"
        elif word == "qc":
            s.alignment = "center"
        elif word == "qj":
            s.alignment = "justify"
        elif word == "li" and param is not None:
            s.indent_left = param
        elif word == "fi" and param is not None:
            s.first_line_indent = param
        elif word == "ri" and param is not None:
            s.indent_right = param
        elif word == "sb" and param is not None:
            s.spacing_before = param
        elif word == "sa" and param is not None:
            s.spacing_after = param
        elif word == "sl" and param is not None:
            s.line_spacing = param
        elif word == "tx" and param is not None:
            s.tab_stops.append(param)
        elif word == "ls" and param is not None:
            s.list_override = param
        elif word == "ansicpg" and param is not None:
            self.ansi_codepage = param
        elif word == "deff" and param is not None:
            s.font_index = param
        elif word == "u" and param is not None:
            try:
                self.current_text.append(chr(param))
            except (ValueError, OverflowError):
                self.current_text.append(self.unicode_fallback_char)
        elif word == "up" and param is not None:
            s.superscript = True
        elif word == "dn" and param is not None:
            s.subscript = True
        elif word == "plain":
            s.bold = s.italic = s.underline = s.strikethrough = False
            s.superscript = s.subscript = s.small_caps = s.all_caps = False
            s.font_size = 24.0
            s.text_color = s.background_color = s.highlight_color = None
        return i + 1


class RTFParser(BaseDocumentParser):
    """RTF parser for converting Rich Text Format files to USDM."""

    name = "rtf"
    supported_extensions = (".rtf",)

    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> USDMDocument:
        try:
            interpreter = RtfInterpreter()
            document = interpreter.parse(data)
            if document_id:
                document.document_id = document_id
            if source_name:
                document.title = source_name
            merged_metadata: dict[str, Any] = {"source_format": "rtf", "parser": "RTFParser"}
            if metadata:
                merged_metadata.update(metadata)
            document.metadata.update(merged_metadata)
            return document
        except DocumentParseError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Error parsing RTF: {e}")

    async def parse_path(
        self,
        path: str | Path,
        document_id: str = "",
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> USDMDocument:
        file_path = Path(path)
        return await self.parse_bytes(
            data=file_path.read_bytes(),
            document_id=document_id or str(uuid.uuid4()),
            source_name=file_path.name,
            metadata=metadata,
            options=options,
        )

    async def parse_stream(
        self,
        stream: AsyncIterator[bytes],
        document_id: str = "",
        source_name: str = "",
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> USDMDocument:
        try:
            chunks: list[bytes] = []
            async for chunk in stream:
                chunks.append(chunk)
            return await self.parse_bytes(
                data=b"".join(chunks),
                document_id=document_id or str(uuid.uuid4()),
                source_name=source_name,
                metadata=metadata,
                options=options,
            )
        except DocumentParseError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Error parsing RTF stream: {e}")
