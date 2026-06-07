from __future__ import annotations

import re
import html as html_module
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from engines.document.models.base import ElementType
from engines.document.models.exceptions import DocumentParseError
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.usdm_models import (
    CharacterStyle,
    CodeContent,
    DocumentElement,
    FootnoteContent,
    HeadingContent,
    ListContent,
    ListItemContent,
    LogicalElement,
    PageBreakContent,
    ParagraphContent,
    ParagraphStyle,
    QuoteContent,
    RichTextContent,
    RichTextSpan,
    Section,
    StyleSheet,
    TableCell,
    TableContent,
    TableRow,
    TOCContent,
    USDMDocument,
)

_INDENTED_CODE_RE = re.compile(r'^(    |\t)')
from engines.document.parsers.base import BaseDocumentParser, ParseOptions


class _SourcePos:
    __slots__ = ("line", "col")

    def __init__(self, line: int = 1, col: int = 1):
        self.line = line
        self.col = col


class _BlockNode:
    __slots__ = ("type", "children", "data", "pos")

    def __init__(self, type_: str, data: dict[str, Any] | None = None, pos: _SourcePos | None = None):
        self.type = type_
        self.children: list[_BlockNode] = []
        self.data = data or {}
        self.pos = pos or _SourcePos()


_FRONT_MATTER_RE = re.compile(r'^---\r?\n', re.MULTILINE)
_ATX_HEADING_RE = re.compile(r'^( {0,3})(#+)(?:\s+|$)(.*?)(?:\s+#*\s*)?$')
_SETEXT_UNDERLINE_RE = re.compile(r'^( {0,3})([=])\2*\s*$|^( {0,3})([-])\4*\s*$')
_THEMATIC_BREAK_RE = re.compile(r'^( {0,3})([*\-_])(\s*\2){2,}\s*$')
_FENCED_CODE_RE = re.compile(r'^( {0,3})(`{3,}|~{3,})([^`\s]*)\s*$')
_BLOCKQUOTE_RE = re.compile(r'^(?: {0,3})?(> ?)?')
_BULLET_LIST_RE = re.compile(r'^( {0,3})([-*+])(?=\s)')
_ORDERED_LIST_RE = re.compile(r'^( {0,3})(\d{1,9})([.)])(?=\s)')
_DEFINITION_LIST_RE = re.compile(r'^( {0,3}):(\s+)')
_TOC_RE = re.compile(r'^\[TOC\]\s*$')
_ATTRIBUTES_RE = re.compile(
    r'\{(?:\s*#([A-Za-z_\-][A-Za-z0-9_\-]*))?'
    r'(?:\s*\.([A-Za-z0-9_\-\s]+))?'
    r'(?:\s+([^\}]+?))?\}'
)
_ABBREV_RE = re.compile(r'^\*\[([^\]]+)\]:\s+(.+)$')
_LINK_REF_RE = re.compile(
    r'^( {0,3})\[([^\]^][^\]]*)\]\s*:\s*<?([^\s>]+)>?(?:\s+"([^"]*)"|\s+\'([^\']*)\')?\s*$'
)
_FOOTNOTE_DEF_RE = re.compile(r'^( {0,3})\[\^([^\]]+)\]:\s?(.*)$')
_TABLE_SEPARATOR_RE = re.compile(r'^( {0,3})\|?(?:\s*[:-][- ]*\|[- :|]*)+\s*$')
_TABLE_ROW_RE = re.compile(r'^( {0,3})\|(.+)\|\s*$')
_HTML_BLOCK_TYPE1_RE = re.compile(
    r'^(?: {0,3})<(?:script|pre|style)(?:\s|>|$)', re.IGNORECASE
)
_HTML_BLOCK_TYPE6_STARTS = (
    'address', 'article', 'aside', 'base', 'basefont', 'blockquote', 'body',
    'caption', 'center', 'col', 'colgroup', 'dd', 'details', 'dialog',
    'dir', 'div', 'dl', 'dt', 'fieldset', 'figcaption', 'figure', 'footer',
    'form', 'frame', 'frameset', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head',
    'header', 'hr', 'html', 'iframe', 'legend', 'li', 'link', 'main',
    'menu', 'menuitem', 'nav', 'noframes', 'ol', 'optgroup', 'option',
    'p', 'param', 'section', 'source', 'summary', 'table', 'tbody', 'td',
    'tfoot', 'th', 'thead', 'title', 'tr', 'track', 'ul',
)
_INLINE_ENTITY_RE = re.compile(r'&(?:(?:#[0-9]{1,7})|#x[0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]*);')
_VALID_HTML_TAGS_FOR_INLINE = {
    'a', 'abbr', 'b', 'bdo', 'br', 'cite', 'code', 'data', 'dfn', 'em',
    'i', 'img', 'input', 'kbd', 'mark', 'q', 'rp', 'rt', 'ruby', 's',
    'samp', 'small', 'span', 'strong', 'sub', 'sup', 'time', 'u', 'var', 'wbr',
}


class MarkdownInlineParser:
    """Recursive-descent inline parser for emphasis, links, images, code spans, and more."""

    def __init__(self, link_refs: dict[str, tuple[str, str | None]] | None = None,
                 footnotes: dict[str, list[_BlockNode]] | None = None):
        self.link_refs = link_refs or {}
        self.footnotes: dict[str, list[_BlockNode]] = footnotes or {}
        self._pos = 0
        self._text = ""
        self._spans: list[RichTextSpan] = []

    def parse(self, text: str) -> list[RichTextSpan]:
        self._text = text
        self._pos = 0
        self._spans = []
        self._parse_inlines()
        return self._spans

    def _peek(self, offset: int = 0) -> str:
        pos = self._pos + offset
        if pos < len(self._text):
            return self._text[pos]
        return ''

    def _peek_str(self, length: int) -> str:
        return self._text[self._pos:self._pos + length]

    def _advance(self, count: int = 1) -> str:
        result = self._text[self._pos:self._pos + count]
        self._pos += count
        return result

    def _at_end(self) -> bool:
        return self._pos >= len(self._text)

    def _parse_inlines(self) -> None:
        while not self._at_end():
            if self._try_code_span():
                continue
            if self._try_math():
                continue
            if self._try_strikethrough():
                continue
            if self._try_image():
                continue
            if self._try_link():
                continue
            if self._try_footnote_ref():
                continue
            if self._try_html_tag():
                continue
            if self._try_autolink():
                continue
            if self._try_emphasis():
                continue
            if self._try_line_break():
                continue
            if self._try_entity():
                continue
            if self._try_escape():
                continue
            self._spans.append(RichTextSpan(text=self._advance(1)))

    def _try_code_span(self) -> bool:
        if self._peek() != '`':
            return False
        start = self._pos
        backtick_char = '`'
        count = 0
        while not self._at_end() and self._peek() == backtick_char:
            count += 1
            self._advance()
        closing = '`' * count
        text_start = self._pos
        idx = self._text.find(closing, self._pos)
        if idx == -1:
            self._pos = start
            return False
        code_text = self._text[text_start:idx]
        if code_text and code_text[0] == ' ' and code_text[-1] == ' ':
            code_text = code_text[1:-1]
        self._pos = idx + count
        self._spans.append(RichTextSpan(text=code_text, code=True))
        return True

    def _try_math(self) -> bool:
        if self._peek_str(2) == '$$':
            self._advance(2)
            start = self._pos
            idx = self._text.find('$$', self._pos)
            if idx == -1:
                self._pos = start - 2
                return False
            latex = self._text[start:idx]
            self._pos = idx + 2
            self._spans.append(RichTextSpan(text=latex, math=latex, display_math=True))
            return True
        if self._peek() == '$' and self._pos + 1 < len(self._text) and self._text[self._pos + 1] != '$':
            self._advance()
            start = self._pos
            idx = self._text.find('$', self._pos)
            if idx == -1:
                self._pos = start - 1
                return False
            latex = self._text[start:idx]
            self._pos = idx + 1
            self._spans.append(RichTextSpan(text=latex, math=latex))
            return True
        return False

    def _try_strikethrough(self) -> bool:
        if self._peek_str(2) != '~~':
            return False
        self._advance(2)
        start = self._pos
        idx = self._text.find('~~', self._pos)
        if idx == -1:
            self._pos = start - 2
            return False
        inner = self._text[start:idx]
        self._pos = idx + 2
        inner_spans = MarkdownInlineParser(self.link_refs, self.footnotes).parse(inner)
        for span in inner_spans:
            span.character_style = "strikethrough"
        self._spans.extend(inner_spans)
        return True

    def _try_image(self) -> bool:
        if self._peek_str(2) != '![':
            return False
        saved = self._pos
        self._advance(2)
        alt_start = self._pos
        bracket_depth = 1
        while not self._at_end() and bracket_depth > 0:
            ch = self._advance()
            if ch == '[':
                bracket_depth += 1
            elif ch == ']':
                bracket_depth -= 1
        alt_text = self._text[alt_start:self._pos - 1]
        if self._at_end():
            self._pos = saved
            return False
        if self._peek() == '(':
            self._advance()
            url, title = self._parse_link_destination()
            if url is not None:
                self._spans.append(RichTextSpan(text=f"image:{alt_text}", href=url))
                return True
            self._pos = saved
            return False
        if self._peek() == '[':
            self._advance()
            ref_start = self._pos
            idx = self._text.find(']', self._pos)
            if idx == -1:
                self._pos = saved
                return False
            ref_label = self._text[ref_start:idx].lower()
            self._pos = idx + 1
            if ref_label == '':
                ref_label = alt_text.lower()
            if ref_label in self.link_refs:
                url, title = self.link_refs[ref_label]
                self._spans.append(RichTextSpan(text=f"image:{alt_text}", href=url))
                return True
            self._pos = saved
            return False
        ref_label = alt_text.lower()
        if ref_label in self.link_refs:
            url, title = self.link_refs[ref_label]
            self._spans.append(RichTextSpan(text=f"image:{alt_text}", href=url))
            return True
        self._pos = saved
        return False

    def _try_link(self) -> bool:
        if self._peek() != '[':
            return False
        saved = self._pos
        self._advance()
        text_start = self._pos
        bracket_depth = 1
        while not self._at_end() and bracket_depth > 0:
            ch = self._advance()
            if ch == '[':
                bracket_depth += 1
            elif ch == ']':
                bracket_depth -= 1
        link_text = self._text[text_start:self._pos - 1]
        if self._at_end():
            self._pos = saved
            return False
        if self._peek() == '(':
            self._advance()
            url, title = self._parse_link_destination()
            if url is not None:
                inner_spans = MarkdownInlineParser(self.link_refs, self.footnotes).parse(link_text)
                for span in inner_spans:
                    span.href = url
                self._spans.extend(inner_spans)
                return True
            self._pos = saved
            return False
        if self._peek() == '[':
            self._advance()
            ref_start = self._pos
            idx = self._text.find(']', self._pos)
            if idx == -1:
                self._pos = saved
                return False
            ref_label = self._text[ref_start:idx].lower()
            self._pos = idx + 1
            if ref_label == '':
                ref_label = link_text.lower()
            if ref_label in self.link_refs:
                url, title = self.link_refs[ref_label]
                inner_spans = MarkdownInlineParser(self.link_refs, self.footnotes).parse(link_text)
                for span in inner_spans:
                    span.href = url
                self._spans.extend(inner_spans)
                return True
            self._pos = saved
            return False
        ref_label = link_text.lower()
        if ref_label in self.link_refs:
            url, title = self.link_refs[ref_label]
            inner_spans = MarkdownInlineParser(self.link_refs, self.footnotes).parse(link_text)
            for span in inner_spans:
                span.href = url
            self._spans.extend(inner_spans)
            return True
        self._pos = saved
        return False

    def _parse_link_destination(self) -> tuple[str | None, str | None]:
        while not self._at_end() and self._peek() in ' \t\n':
            self._advance()
        if self._at_end():
            return None, None
        if self._peek() == '<':
            self._advance()
            start = self._pos
            idx = self._text.find('>', self._pos)
            if idx == -1:
                return None, None
            url = self._text[start:idx]
            self._pos = idx + 1
        else:
            start = self._pos
            while not self._at_end() and self._peek() not in ' \t\n)':
                self._advance()
            url = self._text[start:self._pos]
        while not self._at_end() and self._peek() in ' \t\n':
            self._advance()
        title = None
        if not self._at_end() and self._peek() in '"\'(':
            quote = self._advance()
            end_quote = '"' if quote == '"' else ("'" if quote == "'" else ')')
            t_start = self._pos
            idx = self._text.find(end_quote, self._pos)
            if idx != -1:
                title = self._text[t_start:idx]
                self._pos = idx + 1
        while not self._at_end() and self._peek() in ' \t\n':
            self._advance()
        if not self._at_end() and self._peek() == ')':
            self._advance()
            return url, title
        return None, None

    def _try_footnote_ref(self) -> bool:
        if self._peek_str(2) != '[^':
            return False
        saved = self._pos
        self._advance(2)
        start = self._pos
        idx = self._text.find(']', self._pos)
        if idx == -1:
            self._pos = saved
            return False
        label = self._text[start:idx]
        self._pos = idx + 1
        self._spans.append(RichTextSpan(text=f"[^{label}]", href=f"#footnote-{label}"))
        return True

    def _try_html_tag(self) -> bool:
        if self._peek() != '<':
            return False
        saved = self._pos
        self._advance()
        if self._peek() == '/':
            self._advance()
        tag_start = self._pos
        while not self._at_end() and self._peek().isalnum():
            self._advance()
        tag_name = self._text[tag_start:self._pos].lower()
        if not tag_name:
            self._pos = saved
            return False
        while not self._at_end() and self._peek() not in '>/':
            self._advance()
        if self._peek() == '>':
            self._advance()
            self._spans.append(RichTextSpan(text=self._text[saved:self._pos]))
            return True
        if self._peek_str(2) == '/>':
            self._advance(2)
            self._spans.append(RichTextSpan(text=self._text[saved:self._pos]))
            return True
        self._pos = saved
        return False

    def _try_autolink(self) -> bool:
        if self._peek() != '<':
            return False
        saved = self._pos
        self._advance()
        start = self._pos
        idx = self._text.find('>', self._pos)
        if idx == -1:
            self._pos = saved
            return False
        content = self._text[start:idx]
        self._pos = idx + 1
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://[^\s]+$', content):
            self._spans.append(RichTextSpan(text=content, href=content))
            return True
        if re.match(r'^[\w.+-]+@[\w-]+\.[\w.-]+$', content):
            self._spans.append(RichTextSpan(text=content, href=f"mailto:{content}"))
            return True
        self._pos = saved
        return False

    def _try_emphasis(self) -> bool:
        ch = self._peek()
        if ch not in ('*', '_'):
            return False
        saved = self._pos
        delimiter_run = ""
        while not self._at_end() and self._peek() == ch:
            delimiter_run += self._advance()
        length = len(delimiter_run)
        if length >= 3:
            if self._try_emph_delim(delimiter_run[:2], True):
                self._spans.append(RichTextSpan(text=delimiter_run[2], bold=True, italic=True))
                return True
            self._pos = saved
            return False
        if length == 2:
            if self._try_emph_delim(delimiter_run, True):
                return True
            self._pos = saved
            return False
        if self._try_emph_delim(delimiter_run, False):
            return True
        self._pos = saved
        return False

    def _try_emph_delim(self, closer: str, is_bold: bool) -> bool:
        inner_spans = self._parse_until_closer(closer)
        if inner_spans is None:
            return False
        if is_bold:
            for span in inner_spans:
                span.bold = True
        else:
            for span in inner_spans:
                span.italic = True
        self._spans.extend(inner_spans)
        return True

    def _parse_until_closer(self, closer: str) -> list[RichTextSpan] | None:
        saved_pos = self._pos
        result: list[RichTextSpan] = []
        while not self._at_end():
            if self._peek_str(len(closer)) == closer:
                self._advance(len(closer))
                return result
            if self._peek() == '`':
                code_spans = self._try_code_span_inline()
                if code_spans is not None:
                    result.extend(code_spans)
                    continue
            if self._peek() == '[':
                link_saved = self._pos
                if self._try_link():
                    continue
                self._pos = link_saved
            if self._peek() == '!' and self._pos + 1 < len(self._text) and self._text[self._pos + 1] == '[':
                img_saved = self._pos
                if self._try_image():
                    continue
                self._pos = img_saved
            if self._peek() == '\\':
                self._advance()
                if not self._at_end():
                    result.append(RichTextSpan(text=self._advance()))
                continue
            if self._peek() == '<':
                tag_saved = self._pos
                if self._try_html_tag():
                    continue
                self._pos = tag_saved
            if self._peek_str(2) == '~~':
                strike_saved = self._pos
                if self._try_strikethrough():
                    continue
                self._pos = strike_saved
            if self._peek() == '$':
                math_saved = self._pos
                if self._try_math():
                    continue
                self._pos = math_saved
            if self._peek() in ('*', '_'):
                emph_saved = self._pos
                if self._try_emphasis():
                    continue
                self._pos = emph_saved
            result.append(RichTextSpan(text=self._advance(1)))
        self._pos = saved_pos
        return None

    def _try_code_span_inline(self) -> list[RichTextSpan] | None:
        saved = self._pos
        if self._peek() != '`':
            return None
        backtick_char = '`'
        count = 0
        while not self._at_end() and self._peek() == backtick_char:
            count += 1
            self._advance()
        closing = '`' * count
        text_start = self._pos
        idx = self._text.find(closing, self._pos)
        if idx == -1:
            self._pos = saved
            return None
        code_text = self._text[text_start:idx]
        if code_text and code_text[0] == ' ' and code_text[-1] == ' ':
            code_text = code_text[1:-1]
        self._pos = idx + count
        return [RichTextSpan(text=code_text, code=True)]

    def _try_line_break(self) -> bool:
        if self._peek() == '\\' and not self._at_end():
            self._advance()
            if self._peek() in ('\n', '\r'):
                self._advance()
                if self._peek() == '\n':
                    self._advance()
                self._spans.append(RichTextSpan(text='\n'))
                return True
            return False
        if self._peek_str(2) == '  ':
            idx = self._pos
            while idx < len(self._text) and self._text[idx] == ' ':
                idx += 1
            if idx < len(self._text) and self._text[idx] in ('\n', '\r'):
                self._pos = idx + 1
                if self._pos < len(self._text) and self._text[self._pos] == '\n':
                    self._pos += 1
                self._spans.append(RichTextSpan(text='\n'))
                return True
        return False

    def _try_entity(self) -> bool:
        remaining = self._text[self._pos:]
        m = _INLINE_ENTITY_RE.match(remaining)
        if not m:
            return False
        entity = m.group(0)
        decoded = html_module.unescape(entity)
        self._pos += len(entity)
        self._spans.append(RichTextSpan(text=decoded))
        return True

    def _try_escape(self) -> bool:
        if self._peek() != '\\':
            return False
        self._advance()
        if self._at_end():
            return False
        ch = self._advance()
        self._spans.append(RichTextSpan(text=ch))
        return True


class MarkdownBlockParser:
    """Block-level parser implementing CommonMark 0.30 + GFM."""

    def __init__(self):
        self.lines: list[str] = []
        self.pos = 0
        self.link_refs: dict[str, tuple[str, str | None]] = {}
        self.footnotes: dict[str, list[_BlockNode]] = {}
        self.abbreviations: dict[str, str] = {}
        self.front_matter: dict[str, Any] | None = None
        self.root = _BlockNode("root")
        self._element_counter = 0

    def parse(self, text: str) -> _BlockNode:
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        self.lines = text.split('\n')
        self.pos = 0
        self._extract_front_matter()
        self._extract_link_refs()
        self._extract_abbreviations()
        self._parse_blocks(self.root)
        return self.root

    def _generate_id(self, prefix: str = "elem") -> str:
        self._element_counter += 1
        return f"{prefix}_{self._element_counter}"

    def _current_line(self) -> str | None:
        if self.pos < len(self.lines):
            return self.lines[self.pos]
        return None

    def _peek_line(self, offset: int = 1) -> str | None:
        idx = self.pos + offset
        if idx < len(self.lines):
            return self.lines[idx]
        return None

    def _advance(self, count: int = 1) -> None:
        self.pos += count

    def _is_blank(self, line: str | None) -> bool:
        return line is not None and line.strip() == ''

    def _extract_front_matter(self) -> None:
        if not self.lines:
            return
        first = self.lines[0]
        if first.strip() != '---':
            return
        end_idx = None
        for i in range(1, len(self.lines)):
            if self.lines[i].strip() == '---':
                end_idx = i
                break
        if end_idx is None:
            return
        fm_lines = self.lines[1:end_idx]
        fm_data: dict[str, Any] = {}
        current_key = None
        current_val: list[str] = []
        for line in fm_lines:
            if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
                if current_key is not None:
                    fm_data[current_key] = '\n'.join(current_val).strip()
                key, _, val = line.partition(':')
                current_key = key.strip()
                current_val = [val.strip()]
            else:
                current_val.append(line)
        if current_key is not None:
            fm_data[current_key] = '\n'.join(current_val).strip()
        self.front_matter = fm_data
        self.pos = end_idx + 1

    def _extract_link_refs(self) -> None:
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            m = _LINK_REF_RE.match(line)
            if m:
                label = m.group(2).lower()
                url = m.group(3)
                title = m.group(4) or m.group(5)
                self.link_refs[label] = (url, title)
                self.lines[i] = ''
            i += 1

    def _extract_abbreviations(self) -> None:
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            m = _ABBREV_RE.match(line)
            if m:
                abbr = m.group(1)
                expansion = m.group(2).strip()
                self.abbreviations[abbr] = expansion
                self.lines[i] = ''
            i += 1

    def _parse_blocks(self, parent: _BlockNode) -> None:
        while self.pos < len(self.lines):
            line = self._current_line()
            if line is None:
                break
            if self._is_blank(line):
                self._advance()
                continue
            node = self._parse_block()
            if node is not None:
                parent.children.append(node)

    def _parse_block(self) -> _BlockNode | None:
        line = self._current_line()
        if line is None or self._is_blank(line):
            return None
        pos = _SourcePos(self.pos + 1, 1)
        if self._try_thematic_break():
            return _BlockNode("thematic_break", pos=pos)
        if self._try_atx_heading():
            return self._build_atx_heading(pos)
        if self._try_setext_heading():
            return self._build_setext_heading(pos)
        if self._try_fenced_code():
            return self._build_fenced_code(pos)
        if self._try_display_math():
            return self._build_display_math(pos)
        if self._try_indented_code():
            return self._build_indented_code(pos)
        if self._try_html_block():
            return self._build_html_block(pos)
        if self._try_blockquote():
            return self._build_blockquote(pos)
        if self._try_list():
            return self._build_list(pos)
        if self._try_table():
            return self._build_table(pos)
        if self._try_footnote_def():
            return self._build_footnote_def(pos)
        if self._try_definition_list():
            return self._build_definition_list(pos)
        if self._try_toc():
            return _BlockNode("toc", pos=pos)
        return self._build_paragraph(pos)

    def _try_thematic_break(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        if _THEMATIC_BREAK_RE.match(line):
            self._advance()
            return True
        return False

    def _try_atx_heading(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        return _ATX_HEADING_RE.match(line) is not None

    def _build_atx_heading(self, pos: _SourcePos) -> _BlockNode:
        line = self._current_line()
        assert line is not None
        m = _ATX_HEADING_RE.match(line)
        assert m is not None
        hashes = m.group(2)
        text = m.group(3).strip()
        level = len(hashes)
        attrs = self._extract_attributes(text)
        self._advance()
        return _BlockNode("heading", data={"level": level, "text": text, "attrs": attrs}, pos=pos)

    def _try_setext_heading(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        next_line = self._peek_line()
        if next_line is None:
            return False
        return _SETEXT_UNDERLINE_RE.match(next_line) is not None and line.strip() != ''

    def _build_setext_heading(self, pos: _SourcePos) -> _BlockNode:
        line = self._current_line()
        assert line is not None
        text = line.strip()
        self._advance()
        underline = self._current_line()
        assert underline is not None
        m = _SETEXT_UNDERLINE_RE.match(underline)
        assert m is not None
        level = 1 if m.group(2) else 2
        attrs = self._extract_attributes(text)
        self._advance()
        return _BlockNode("heading", data={"level": level, "text": text, "attrs": attrs}, pos=pos)

    def _try_fenced_code(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        return _FENCED_CODE_RE.match(line) is not None

    def _build_fenced_code(self, pos: _SourcePos) -> _BlockNode:
        line = self._current_line()
        assert line is not None
        m = _FENCED_CODE_RE.match(line)
        assert m is not None
        fence_char = m.group(2)[0]
        fence_len = len(m.group(2))
        info_string = m.group(3).strip()
        language = None
        if info_string:
            language = info_string.split()[0]
        self._advance()
        code_lines: list[str] = []
        while self.pos < len(self.lines):
            cl = self._current_line()
            if cl is not None:
                cm = _FENCED_CODE_RE.match(cl)
                if cm and cm.group(2)[0] == fence_char and len(cm.group(2)) >= fence_len:
                    self._advance()
                    break
            code_lines.append(self._current_line() or '')
            self._advance()
        return _BlockNode("code_block", data={
            "code": '\n'.join(code_lines),
            "language": language,
            "info_string": info_string,
        }, pos=pos)

    def _try_display_math(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        stripped = line.strip()
        return stripped.startswith('$$')

    def _build_display_math(self, pos: _SourcePos) -> _BlockNode:
        lines: list[str] = []
        line = self._current_line()
        assert line is not None
        first = line.strip()
        if first == '$$':
            self._advance()
            while self.pos < len(self.lines):
                cl = self._current_line()
                if cl is not None and cl.strip() == '$$':
                    self._advance()
                    break
                lines.append(cl or '')
                self._advance()
            latex = '\n'.join(lines)
            return _BlockNode("display_math", data={"latex": latex, "info_string": ""}, pos=pos)
        else:
            latex = first[2:]
            remaining = latex
            if remaining.endswith('$$'):
                latex = remaining[:-2]
                self._advance()
                return _BlockNode("display_math", data={"latex": latex, "info_string": ""}, pos=pos)
            self._advance()
            while self.pos < len(self.lines):
                cl = self._current_line()
                if cl is not None and '$$' in cl:
                    idx = cl.index('$$')
                    lines.append(cl[:idx])
                    self._advance()
                    break
                lines.append(cl or '')
                self._advance()
            latex = (remaining + '\n' + '\n'.join(lines)).strip()
            return _BlockNode("display_math", data={"latex": latex, "info_string": ""}, pos=pos)

    def _try_indented_code(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        return _INDENTED_CODE_RE.match(line) is not None

    def _build_indented_code(self, pos: _SourcePos) -> _BlockNode:
        code_lines: list[str] = []
        while self.pos < len(self.lines):
            line = self._current_line()
            if line is None:
                break
            if _INDENTED_CODE_RE.match(line):
                code_lines.append(line[4:] if line.startswith('    ') else line[1:])
                self._advance()
            elif line.strip() == '':
                if self.pos + 1 < len(self.lines) and _INDENTED_CODE_RE.match(self.lines[self.pos + 1]):
                    code_lines.append('')
                    self._advance()
                else:
                    break
            else:
                break
        return _BlockNode("code_block", data={"code": '\n'.join(code_lines), "language": None, "info_string": ""}, pos=pos)

    def _try_html_block(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        stripped = line.lstrip()
        if _HTML_BLOCK_TYPE1_RE.match(stripped):
            return True
        for tag in _HTML_BLOCK_TYPE6_STARTS:
            if stripped.startswith(f'<{tag}') or stripped.startswith(f'<{tag} ') or stripped.startswith(f'<{tag}>') or stripped.startswith(f'</{tag}>') or stripped.startswith(f'</{tag} '):
                return True
        if stripped.startswith('<?') or stripped.startswith('<!'):
            return True
        return False

    def _build_html_block(self, pos: _SourcePos) -> _BlockNode:
        html_lines: list[str] = []
        while self.pos < len(self.lines):
            line = self._current_line()
            if line is None:
                break
            if self._is_blank(line):
                break
            html_lines.append(line)
            self._advance()
        return _BlockNode("html_block", data={"html": '\n'.join(html_lines)}, pos=pos)

    def _try_blockquote(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        m = _BLOCKQUOTE_RE.match(line)
        if m is None:
            return False
        return m.group(1) is not None

    def _build_blockquote(self, pos: _SourcePos) -> _BlockNode:
        bq_node = _BlockNode("blockquote", pos=pos)
        while self.pos < len(self.lines):
            line = self._current_line()
            if line is None:
                break
            m = _BLOCKQUOTE_RE.match(line)
            assert m is not None
            if m.group(1) is None:
                if self._is_blank(line):
                    next_line = self._peek_line()
                    if next_line is not None:
                        nm = _BLOCKQUOTE_RE.match(next_line)
                        assert nm is not None
                        if nm.group(1) is not None:
                            self._advance()
                            continue
                break
            content = line[m.end():] if m.group(1) else line
            self.lines[self.pos] = content
            self._advance()
        inner_parser = MarkdownBlockParser()
        inner_parser.lines = []
        i = pos.line - 1
        while i < self.pos:
            if i < len(self.lines):
                inner_parser.lines.append(self.lines[i])
            i += 1
        inner_parser.pos = 0
        inner_parser.link_refs = self.link_refs
        inner_parser.footnotes = self.footnotes
        inner_parser._parse_blocks(bq_node)
        return bq_node

    def _try_list(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        return _BULLET_LIST_RE.match(line) is not None or _ORDERED_LIST_RE.match(line) is not None

    def _build_list(self, pos: _SourcePos) -> _BlockNode:
        line = self._current_line()
        assert line is not None
        m_bullet = _BULLET_LIST_RE.match(line)
        m_ordered = _ORDERED_LIST_RE.match(line)
        if m_bullet:
            ordered = False
            start_num = 1
            delimiter = ''
        else:
            assert m_ordered is not None
            ordered = True
            start_num = int(m_ordered.group(2))
            delimiter = m_ordered.group(3)
        list_node = _BlockNode("list", data={
            "ordered": ordered, "start": start_num, "delimiter": delimiter,
        }, pos=pos)
        while self.pos < len(self.lines):
            line = self._current_line()
            if line is None:
                break
            if self._is_blank(line):
                next_line = self._peek_line()
                if next_line is not None and (_BULLET_LIST_RE.match(next_line) or _ORDERED_LIST_RE.match(next_line)):
                    self._advance()
                    continue
                break
            mb = _BULLET_LIST_RE.match(line)
            mo = _ORDERED_LIST_RE.match(line)
            if mb is None and mo is None:
                break
            item_node = self._parse_list_item(list_node)
            if item_node is not None:
                list_node.children.append(item_node)
        return list_node

    def _parse_list_item(self, list_node: _BlockNode) -> _BlockNode | None:
        line = self._current_node_line()
        if line is None:
            return None
        m_b = _BULLET_LIST_RE.match(line)
        m_o = _ORDERED_LIST_RE.match(line)
        if m_b:
            marker_len = len(m_b.group(1)) + 2
        elif m_o:
            marker_len = len(m_o.group(1)) + len(m_o.group(2)) + 2
        else:
            return None
        item_pos = _SourcePos(self.pos + 1, 1)
        item_node = _BlockNode("list_item", pos=item_pos)
        content_lines: list[str] = []
        first_content = line[marker_len:]
        if first_content.strip():
            content_lines.append(first_content)
        self._advance()
        indent = marker_len
        while self.pos < len(self.lines):
            line = self._current_line()
            if line is None:
                break
            if self._is_blank(line):
                content_lines.append('')
                self._advance()
                continue
            leading = len(line) - len(line.lstrip())
            if leading >= indent or (leading > 0 and leading < 4):
                content_lines.append(line.lstrip() if leading < 4 else line[indent:])
                self._advance()
                continue
            if _BULLET_LIST_RE.match(line) or _ORDERED_LIST_RE.match(line):
                break
            if leading == 0:
                break
            content_lines.append(line[indent:])
            self._advance()
        inner_text = '\n'.join(content_lines).strip()
        inner_parser = MarkdownBlockParser()
        inner_parser.link_refs = self.link_refs
        inner_parser.footnotes = self.footnotes
        inner_root = inner_parser.parse(inner_text)
        item_node.children = inner_root.children
        stripped = inner_text.strip()
        if stripped.startswith('[ ]') or stripped.startswith('[x]') or stripped.startswith('[X]'):
            item_node.data["task"] = True
            item_node.data["checked"] = stripped[1].lower() == 'x'
        return item_node

    def _current_node_line(self) -> str | None:
        return self._current_line()

    def _try_table(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        if '|' not in line:
            return False
        next_line = self._peek_line()
        if next_line is None:
            return False
        return _TABLE_SEPARATOR_RE.match(next_line) is not None

    def _build_table(self, pos: _SourcePos) -> _BlockNode:
        header_line = self._current_line()
        assert header_line is not None
        self._advance()
        sep_line = self._current_line()
        assert sep_line is not None
        self._advance()
        alignments = self._parse_table_alignments(sep_line)
        headers = self._parse_table_row(header_line)
        rows_data: list[list[str]] = [headers]
        while self.pos < len(self.lines):
            line = self._current_line()
            if line is None or self._is_blank(line):
                break
            if '|' not in line:
                break
            rows_data.append(self._parse_table_row(line))
            self._advance()
        return _BlockNode("table", data={"rows": rows_data, "alignments": alignments}, pos=pos)

    def _parse_table_alignments(self, sep_line: str) -> list[str]:
        cells = sep_line.strip().strip('|').split('|')
        alignments = []
        for cell in cells:
            cell = cell.strip()
            if cell.startswith(':') and cell.endswith(':'):
                alignments.append('center')
            elif cell.endswith(':'):
                alignments.append('right')
            elif cell.startswith(':'):
                alignments.append('left')
            else:
                alignments.append('')
        return alignments

    def _parse_table_row(self, line: str) -> list[str]:
        stripped = line.strip()
        if stripped.startswith('|'):
            stripped = stripped[1:]
        if stripped.endswith('|'):
            stripped = stripped[:-1]
        cells = []
        current = []
        i = 0
        while i < len(stripped):
            if stripped[i] == '\\' and i + 1 < len(stripped):
                current.append(stripped[i + 1])
                i += 2
                continue
            if stripped[i] == '|':
                cells.append(''.join(current).strip())
                current = []
                i += 1
                continue
            current.append(stripped[i])
            i += 1
        cells.append(''.join(current).strip())
        return cells

    def _try_footnote_def(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        return _FOOTNOTE_DEF_RE.match(line) is not None

    def _build_footnote_def(self, pos: _SourcePos) -> _BlockNode | None:
        line = self._current_line()
        if line is None:
            return None
        m = _FOOTNOTE_DEF_RE.match(line)
        if not m:
            return None
        label = m.group(2)
        content = m.group(3)
        self._advance()
        content_lines = [content]
        while self.pos < len(self.lines):
            cl = self._current_line()
            if cl is None or self._is_blank(cl):
                break
            if cl.startswith('    ') or cl.startswith('\t'):
                content_lines.append(cl[4:] if cl.startswith('    ') else cl[1:])
                self._advance()
            else:
                break
        fn_node = _BlockNode("footnote_def", data={"label": label, "content": '\n'.join(content_lines)}, pos=pos)
        inner_parser = MarkdownBlockParser()
        inner_parser.link_refs = self.link_refs
        inner_parser.footnotes = self.footnotes
        inner_root = inner_parser.parse('\n'.join(content_lines))
        fn_node.children = inner_root.children
        self.footnotes[label] = fn_node.children
        return fn_node

    def _try_definition_list(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        return _DEFINITION_LIST_RE.match(line) is not None

    def _build_definition_list(self, pos: _SourcePos) -> _BlockNode:
        dl_node = _BlockNode("definition_list", pos=pos)
        while self.pos < len(self.lines):
            line = self._current_line()
            if line is None or self._is_blank(line):
                break
            m = _DEFINITION_LIST_RE.match(line)
            if not m:
                break
            term_lines: list[str] = []
            def_lines: list[str] = []
            while self.pos < len(self.lines):
                cl = self._current_line()
                if cl is None or self._is_blank(cl):
                    break
                cm = _DEFINITION_LIST_RE.match(cl)
                if cm:
                    def_lines.append(cm.group(2).lstrip())
                    self._advance()
                else:
                    term_lines.append(cl.strip())
                    self._advance()
            if term_lines or def_lines:
                term_text = ' '.join(term_lines) if term_lines else ''
                def_text = ' '.join(def_lines)
                item_node = _BlockNode("definition_item", data={
                    "term": term_text, "definition": def_text,
                }, pos=pos)
                dl_node.children.append(item_node)
        return dl_node

    def _try_toc(self) -> bool:
        line = self._current_line()
        if line is None:
            return False
        if _TOC_RE.match(line) is not None:
            self._advance()
            return True
        return False

    def _extract_attributes(self, text: str) -> dict[str, str]:
        result: dict[str, str] = {}
        m = _ATTRIBUTES_RE.search(text)
        if m:
            if m.group(1):
                result['id'] = m.group(1)
            if m.group(2):
                result['classes'] = m.group(2).strip()
            if m.group(3):
                for part in m.group(3).split():
                    if '=' in part:
                        k, _, v = part.partition('=')
                        result[k] = v
        return result

    def _build_paragraph(self, pos: _SourcePos) -> _BlockNode:
        para_lines: list[str] = []
        first = True
        while self.pos < len(self.lines):
            line = self._current_line()
            if line is None or self._is_blank(line):
                break
            if not first and self._is_block_start(line):
                break
            first = False
            para_lines.append(line)
            self._advance()
        text = ""
        for i, pl in enumerate(para_lines):
            if i > 0:
                prev = para_lines[i - 1]
                if prev.endswith("  ") or prev.endswith("\\\n") or prev.endswith("\\"):
                    text += "\n"
                else:
                    text += " "
            text += pl.rstrip()
        return _BlockNode("paragraph", data={"text": text}, pos=pos)

    def _is_block_start(self, line: str) -> bool:
        if _ATX_HEADING_RE.match(line):
            return True
        if _THEMATIC_BREAK_RE.match(line):
            return True
        if _FENCED_CODE_RE.match(line):
            return True
        if _INDENTED_CODE_RE.match(line):
            return True
        if line.strip().startswith('$$'):
            return True
        m_bq = _BLOCKQUOTE_RE.match(line)
        if m_bq is not None and m_bq.group(1) is not None:
            return True
        if _BULLET_LIST_RE.match(line) or _ORDERED_LIST_RE.match(line):
            return True
        if _FOOTNOTE_DEF_RE.match(line):
            return True
        if _TOC_RE.match(line):
            return True
        if _DEFINITION_LIST_RE.match(line):
            return True
        if _ABBREV_RE.match(line):
            return True
        return False


class MarkdownTreeProcessor:
    """Converts the block tree into USDM elements."""

    def __init__(self):
        self.sections: list[Section] = []
        self.elements: list[DocumentElement] = []
        self.logical_elements: list[LogicalElement] = []
        self._counter = 0
        self._current_section: Section | None = None
        self._link_refs: dict[str, tuple[str, str | None]] = {}
        self._footnotes: dict[str, list[_BlockNode]] = {}

    def _generate_id(self, prefix: str = "elem") -> str:
        self._counter += 1
        return f"{prefix}_{self._counter}"

    def process(self, root: _BlockNode, front_matter: dict[str, Any] | None = None,
                abbreviations: dict[str, str] | None = None,
                link_refs: dict[str, tuple[str, str | None]] | None = None,
                footnotes: dict[str, list[_BlockNode]] | None = None,
                ) -> tuple[list[Section], list[DocumentElement], list[LogicalElement]]:
        self._link_refs = dict(link_refs) if link_refs else {}
        self._footnotes = dict(footnotes) if footnotes else {}
        for child in root.children:
            self._process_node(child)
        return self.sections, self.elements, self.logical_elements

    def _process_node(self, node: _BlockNode) -> None:
        handler = getattr(self, f"_handle_{node.type}", None)
        if handler:
            handler(node)

    def _ensure_section(self, title: str = "", level: int = 0) -> Section:
        section = Section(
            section_id=self._generate_id("section"),
            title=HeadingContent(level=level, text=RichTextContent(spans=[RichTextSpan(text=title)])) if title else None,
            section_type="body",
        )
        self.sections.append(section)
        self._current_section = section
        return section

    def _add_element(self, elem_id: str, elem_type: ElementType, content: Any, metadata: dict[str, Any] | None = None) -> None:
        log = LogicalElement(element_id=elem_id, element_type=elem_type, content=content, metadata=metadata or {})
        self.logical_elements.append(log)
        doc_elem = DocumentElement(element_id=elem_id, element_type=elem_type, metadata=metadata or {})
        self.elements.append(doc_elem)
        if self._current_section is None:
            self._ensure_section()
        assert self._current_section is not None
        self._current_section.elements.append(doc_elem)

    def _inline_spans(self, text: str, link_refs: dict[str, tuple[str, str | None]] | None = None,
                      footnotes: dict[str, list[_BlockNode]] | None = None) -> list[RichTextSpan]:
        lr = link_refs if link_refs is not None else self._link_refs
        fn = footnotes if footnotes is not None else self._footnotes
        parser = MarkdownInlineParser(lr, fn)
        return parser.parse(text)

    def _handle_heading(self, node: _BlockNode) -> None:
        level = node.data["level"]
        text = node.data["text"]
        attrs = node.data.get("attrs", {})
        elem_id = self._generate_id("heading")
        spans = self._inline_spans(text)
        content = HeadingContent(level=level, text=RichTextContent(spans=spans))
        meta: dict[str, Any] = {"level": level}
        meta.update(attrs)
        self._add_element(elem_id, ElementType.HEADING, content, meta)
        section = Section(
            section_id=self._generate_id("section"),
            title=content,
            section_type="section",
            metadata=meta,
        )
        self.sections.append(section)
        self._current_section = section

    def _handle_paragraph(self, node: _BlockNode) -> None:
        text = node.data["text"]
        elem_id = self._generate_id("para")
        spans = self._inline_spans(text)
        content = ParagraphContent(text=RichTextContent(spans=spans))
        self._add_element(elem_id, ElementType.PARAGRAPH, content)

    def _handle_thematic_break(self, node: _BlockNode) -> None:
        elem_id = self._generate_id("hr")
        self._add_element(elem_id, ElementType.DIVIDER, PageBreakContent())

    def _handle_code_block(self, node: _BlockNode) -> None:
        code = node.data["code"]
        language = node.data.get("language")
        elem_id = self._generate_id("code")
        content = CodeContent(code=code, language=language)
        self._add_element(elem_id, ElementType.CODE, content, {"language": language})

    def _handle_display_math(self, node: _BlockNode) -> None:
        latex = node.data["latex"]
        info = node.data.get("info_string", "")
        lang = "latex" if info == "" else info
        elem_id = self._generate_id("math")
        content = CodeContent(code=latex, language=lang)
        self._add_element(elem_id, ElementType.MATH, content, {"display": True, "latex": latex})

    def _handle_html_block(self, node: _BlockNode) -> None:
        html_text = node.data["html"]
        elem_id = self._generate_id("html")
        spans = [RichTextSpan(text=html_text, code=True)]
        content = ParagraphContent(text=RichTextContent(spans=spans))
        self._add_element(elem_id, ElementType.PARAGRAPH, content, {"raw_html": True})

    def _handle_blockquote(self, node: _BlockNode) -> None:
        elem_id = self._generate_id("quote")
        inner_elems: list[LogicalElement] = []
        for child in node.children:
            child_processor = MarkdownTreeProcessor()
            child_processor._counter = self._counter
            child_processor._current_section = self._current_section
            child_processor._process_node(child)
            self._counter = child_processor._counter
            inner_elems.extend(child_processor.logical_elements)
            self.elements.extend(child_processor.elements)
            self.logical_elements.extend(child_processor.logical_elements)
        content = QuoteContent(elements=inner_elems)
        self._add_element(elem_id, ElementType.QUOTE, content)

    def _handle_list(self, node: _BlockNode) -> None:
        ordered = node.data.get("ordered", False)
        items: list[ListItemContent] = []
        for child in node.children:
            if child.type == "list_item":
                item_elems: list[LogicalElement] = []
                for grandchild in child.children:
                    child_proc = MarkdownTreeProcessor()
                    child_proc._counter = self._counter
                    child_proc._process_node(grandchild)
                    self._counter = child_proc._counter
                    item_elems.extend(child_proc.logical_elements)
                    self.elements.extend(child_proc.elements)
                    self.logical_elements.extend(child_proc.logical_elements)
                is_task = child.data.get("task", False)
                checked = child.data.get("checked", False)
                meta: dict[str, Any] = {}
                if is_task:
                    meta["task"] = True
                    meta["checked"] = checked
                items.append(ListItemContent(elements=item_elems))
        elem_id = self._generate_id("list")
        list_meta: dict[str, Any] = {"ordered": ordered}
        if ordered:
            list_meta["start"] = node.data.get("start", 1)
            list_meta["delimiter"] = node.data.get("delimiter", ".")
        content = ListContent(ordered=ordered, items=items)
        self._add_element(elem_id, ElementType.LIST, content, list_meta)

    def _handle_table(self, node: _BlockNode) -> None:
        rows_data = node.data["rows"]
        alignments = node.data.get("alignments", [])
        table_rows: list[TableRow] = []
        for i, row_cells in enumerate(rows_data):
            is_header = (i == 0)
            cells: list[TableCell] = []
            for j, cell_text in enumerate(row_cells):
                spans = self._inline_spans(cell_text)
                para = ParagraphContent(text=RichTextContent(spans=spans))
                cell_elems = [LogicalElement(
                    element_id=self._generate_id("cell_para"),
                    element_type=ElementType.PARAGRAPH,
                    content=para,
                )]
                align = alignments[j] if j < len(alignments) else ""
                cell_meta: dict[str, Any] = {}
                if align:
                    cell_meta["alignment"] = align
                cells.append(TableCell(content=cell_elems, is_header=is_header, metadata=cell_meta))
            table_rows.append(TableRow(cells=cells, is_header=is_header))
        elem_id = self._generate_id("table")
        content = TableContent(rows=table_rows)
        self._add_element(elem_id, ElementType.TABLE, content)

    def _handle_footnote_def(self, node: _BlockNode) -> None:
        label = node.data["label"]
        elem_id = self._generate_id("footnote")
        inner_elems: list[LogicalElement] = []
        for child in node.children:
            child_proc = MarkdownTreeProcessor()
            child_proc._counter = self._counter
            child_proc._process_node(child)
            self._counter = child_proc._counter
            inner_elems.extend(child_proc.logical_elements)
            self.elements.extend(child_proc.elements)
            self.logical_elements.extend(child_proc.logical_elements)
        content = FootnoteContent(note_id=label, elements=inner_elems)
        self._add_element(elem_id, ElementType.FOOTNOTE, content, {"label": label})

    def _handle_definition_list(self, node: _BlockNode) -> None:
        items: list[ListItemContent] = []
        for child in node.children:
            if child.type == "definition_item":
                term = child.data.get("term", "")
                definition = child.data.get("definition", "")
                term_spans = self._inline_spans(term)
                def_spans = self._inline_spans(definition)
                term_elem = LogicalElement(
                    element_id=self._generate_id("def_term"),
                    element_type=ElementType.PARAGRAPH,
                    content=ParagraphContent(text=RichTextContent(spans=term_spans)),
                    metadata={"definition_term": True},
                )
                def_elem = LogicalElement(
                    element_id=self._generate_id("def_def"),
                    element_type=ElementType.PARAGRAPH,
                    content=ParagraphContent(text=RichTextContent(spans=def_spans)),
                )
                items.append(ListItemContent(elements=[term_elem, def_elem]))
        elem_id = self._generate_id("deflist")
        content = ListContent(ordered=False, items=items)
        self._add_element(elem_id, ElementType.LIST, content, {"definition_list": True})

    def _handle_toc(self, node: _BlockNode) -> None:
        elem_id = self._generate_id("toc")
        content = TOCContent()
        self._add_element(elem_id, ElementType.TOC, content)


class MarkdownParser(BaseDocumentParser):
    """Full CommonMark 0.30 + GFM compliant Markdown parser for USDM."""

    name: str = "markdown"
    supported_extensions: tuple[str, ...] = (".md", ".markdown")

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str,
                         metadata: dict[str, Any] | None = None,
                         options: ParseOptions | None = None) -> USDMDocument:
        opts = options or ParseOptions()
        try:
            text = data.decode(opts.encoding, errors='replace')
        except Exception as e:
            raise DocumentParseError(f"Failed to decode markdown: {e}")
        try:
            block_parser = MarkdownBlockParser()
            root = block_parser.parse(text)
            processor = MarkdownTreeProcessor()
            sections, elements, logical_elements = processor.process(
                root, block_parser.front_matter, block_parser.abbreviations,
                block_parser.link_refs, block_parser.footnotes,
            )
            doc_metadata = self._build_metadata(block_parser.front_matter, metadata)
            title = self._extract_title(block_parser.front_matter, source_name)
            stylesheet = self._build_stylesheet()
            usdm_doc = USDMDocument(
                document_id=document_id,
                title=title,
                media_type=MEDIA_TYPES["markdown"],
                file_extension=".md",
                sections=sections,
                elements=elements,
                logical_elements=logical_elements,
                stylesheet=stylesheet,
                pages=[],
                metadata=doc_metadata,
                raw_text=text,
            )
            return usdm_doc
        except DocumentParseError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Error parsing markdown: {e}")

    async def parse_path(self, path: str | Path, document_id: str,
                        metadata: dict[str, Any] | None = None,
                        options: ParseOptions | None = None) -> USDMDocument:
        """Parse a markdown file from a filesystem path."""
        file_path = Path(path)
        return await self.parse_bytes(
            data=file_path.read_bytes(),
            document_id=document_id,
            source_name=file_path.name,
            metadata=metadata,
            options=options,
        )

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str,
                          source_name: str, metadata: dict[str, Any] | None = None,
                          options: ParseOptions | None = None) -> USDMDocument:
        try:
            chunks: list[bytes] = []
            async for chunk in stream:
                chunks.append(chunk)
            data = b''.join(chunks)
            return await self.parse_bytes(data, document_id, source_name, metadata, options)
        except DocumentParseError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Error parsing markdown stream: {e}")

    def _build_metadata(self, front_matter: dict[str, Any] | None,
                        extra: dict[str, Any] | None) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if front_matter:
            result["front_matter"] = front_matter
            if "title" in front_matter:
                result["title"] = front_matter["title"]
            if "author" in front_matter:
                result["authors"] = [a.strip() for a in str(front_matter["author"]).split(",")]
            if "date" in front_matter:
                result["date"] = front_matter["date"]
        if extra:
            result.update(extra)
        return result

    def _extract_title(self, front_matter: dict[str, Any] | None, source_name: str) -> str:
        if front_matter and "title" in front_matter:
            return str(front_matter["title"])
        name = source_name
        for ext in ('.md', '.markdown'):
            if name.lower().endswith(ext):
                name = name[:-len(ext)]
                break
        return name

    def _build_stylesheet(self) -> StyleSheet:
        return StyleSheet(
            character_styles={
                "code": CharacterStyle(name="code", font="monospace"),
                "emphasis": CharacterStyle(name="emphasis", italic=True),
                "strong": CharacterStyle(name="strong", bold=True),
                "strikethrough": CharacterStyle(name="strikethrough", strike=True),
            },
            paragraph_styles={
                "normal": ParagraphStyle(name="normal"),
                "heading1": ParagraphStyle(name="heading1", spacing_after=12.0),
                "heading2": ParagraphStyle(name="heading2", spacing_after=10.0),
                "heading3": ParagraphStyle(name="heading3", spacing_after=8.0),
                "heading4": ParagraphStyle(name="heading4", spacing_after=6.0),
                "heading5": ParagraphStyle(name="heading5", spacing_after=4.0),
                "heading6": ParagraphStyle(name="heading6", spacing_after=4.0),
            },
        )
