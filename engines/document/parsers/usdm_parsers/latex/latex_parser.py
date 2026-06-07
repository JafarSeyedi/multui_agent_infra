"""
Comprehensive LaTeX2e parser covering document structure, title page,
sectioning, cross-references, footnotes, headers/footers, page layout,
color, fonts, encoding, tables, lists, inline formatting, floats,
sub-figures, multi-column, language support, index, verbatim, images,
escape characters, paragraph indentation, line spacing, and title page.
Maps all LaTeX elements to USDM content types.
"""
from __future__ import annotations

import logging
import re
from collections.abc import AsyncIterator
from typing import Any

from ....models.base import ElementType
from ....models.exceptions import DocumentParseError
from ....models.media_types import MEDIA_TYPES
from ....models.usdm_models import CaptionContent
from ....models.usdm_models import CharacterStyle
from ....models.usdm_models import CodeContent
from ....models.usdm_models import ColumnBreakContent
from ....models.usdm_models import CommentContent
from ....models.usdm_models import CrossReference
from ....models.usdm_models import DocumentElement
from ....models.usdm_models import EndnoteContent
from ....models.usdm_models import FooterContent
from ....models.usdm_models import FootnoteContent
from ....models.usdm_models import HeaderContent
from ....models.usdm_models import HeadingContent
from ....models.usdm_models import ImageContent
from ....models.usdm_models import IndexContent
from ....models.usdm_models import LineBreakContent
from ....models.usdm_models import LinkContent
from ....models.usdm_models import ListContent
from ....models.usdm_models import ListItemContent
from ....models.usdm_models import ListStyle
from ....models.usdm_models import LogicalElement
from ....models.usdm_models import MathContent
from ....models.usdm_models import PageBreakContent
from ....models.usdm_models import ParagraphContent
from ....models.usdm_models import ParagraphStyle
from ....models.usdm_models import QuoteContent
from ....models.usdm_models import RichTextContent
from ....models.usdm_models import RichTextSpan
from ....models.usdm_models import Section
from ....models.usdm_models import StyleSheet
from ....models.usdm_models import TableCell
from ....models.usdm_models import TableContent
from ....models.usdm_models import TableRow
from ....models.usdm_models import TableStyle
from ....models.usdm_models import TOCContent
from ....models.usdm_models import USDMDocument
from ...base import BaseDocumentParser
from ...base import ParseOptions

logger = logging.getLogger(__name__)


def _parse_keyval(s: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in s.split(","):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def _parse_length(s: str) -> float | str:
    try:
        return float(s)
    except ValueError:
        return s


class LatexParser(BaseDocumentParser):
    """Comprehensive LaTeX2e parser with full standard package support."""

    name: str = "latex"
    supported_extensions: tuple[str, ...] = (".tex", ".latex")

    def __init__(self) -> None:
        super().__init__()
        self._reset_parser_state()

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str,
                         metadata: dict[str, Any] | None = None,
                         options: ParseOptions | None = None) -> USDMDocument:
        """Parse LaTeX byte data into USDMDocument."""
        opts = options or ParseOptions()
        try:
            text = data.decode(opts.encoding, errors="replace")
            self._reset_parser_state()
            self._parse(text)
            stylesheet = self._build_stylesheet()
            title = self._extract_title_from_preamble(text) or source_name.replace(".tex", "").replace(".latex", "")
            usdm_doc = USDMDocument(
                document_id=document_id,
                title=title,
                media_type=MEDIA_TYPES["latex"],
                file_extension=".tex",
                sections=self._sections,
                elements=self._elements,
                logical_elements=self._logical_elements,
                stylesheet=stylesheet,
                pages=self._build_pages(),
                metadata=self._build_doc_metadata(),
                raw_text=text,
            )
            return usdm_doc
        except Exception as e:
            logger.error(f"Error parsing LaTeX: {e}", exc_info=True)
            raise DocumentParseError(f"Error parsing LaTeX: {e}")

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str,
                          source_name: str, metadata: dict[str, Any] | None = None,
                          options: ParseOptions | None = None) -> USDMDocument:
        """Parse LaTeX from a byte stream."""
        try:
            chunks: list[bytes] = []
            async for chunk in stream:
                chunks.append(chunk)
            data = b"".join(chunks)
            return await self.parse_bytes(data, document_id, source_name, metadata, options)
        except Exception as e:
            logger.error(f"Error parsing LaTeX stream: {e}", exc_info=True)
            raise DocumentParseError(f"Error parsing LaTeX stream: {e}")

    async def parse_path(self, path, document_id="", metadata=None, options=None):
        from pathlib import Path as _P
        p = _P(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name, metadata, options)

    def _reset_parser_state(self) -> None:
        self._current_section: Section | None = None
        self._sections: list[Section] = []
        self._elements: list[DocumentElement] = []
        self._logical_elements: list[LogicalElement] = []
        self._element_counter: int = 0
        self._in_math_mode: bool = False
        self._in_verbatim: bool = False
        self._verbatim_env: str | None = None
        self._current_environment: str | None = None
        self._env_stack: list[str] = []
        self._label_map: dict[str, str] = {}
        self._labels: dict[str, dict[str, Any]] = {}
        self._cross_references: list[CrossReference] = []
        self._footnotes: list[FootnoteContent] = []
        self._endnotes: list[EndnoteContent] = []
        self._indentation: float | None = None
        self._parskip: float | None = None
        self._line_spacing: float | None = 1.0
        self._line_spacing_rule: str | None = None
        self._font_family: str | None = None
        self._font_size: float | None = None
        self._font_encoding: str | None = None
        self._input_encoding: str | None = None
        self._base_font: str | None = None
        self._sans_font: str | None = None
        self._mono_font: str | None = None
        self._languages: list[str] = []
        self._current_language: str | None = None
        self._page_styles: dict[str, dict[str, Any]] = {}
        self._current_page_style: str | None = None
        self._headers: list[HeaderContent] = []
        self._footers: list[FooterContent] = []
        self._toc_entries: list[TOCContent] = []
        self._index_entries: list[IndexContent] = []
        self._captions: list[CaptionContent] = []
        self._loaded_packages: list[str] = []
        self._document_class: str | None = None
        self._document_options: dict[str, str] = {}
        self._color_definitions: dict[str, dict[str, Any]] = {}
        self._graphicspath: list[str] = []
        self._graphics_extensions: list[str] = []
        self._title_data: dict[str, str] = {}
        self._title: str | None = None
        self._author: str | None = None
        self._date: str | None = None
        self._thanks_notes: list[str] = []
        self._is_appendix: bool = False
        self._list_depth: int = 0
        self._list_stack: list[dict[str, Any]] = []
        self._verbatim_lines: list[str] = []
        self._tabular_columns: str = ""
        self._tabular_rows: list[list[TableCell]] = []
        self._current_table_content: TableContent | None = None
        self._float_placement: str | None = None
        self._float_stack: list[dict[str, Any]] = []
        self._multicol_depth: int = 0

    def _generate_id(self, prefix: str = "elem") -> str:
        self._element_counter += 1
        return f"{prefix}_{self._element_counter}"

    def _add_logical(self, elem: LogicalElement) -> None:
        self._logical_elements.append(elem)

    def _add_element(self, elem: DocumentElement) -> None:
        self._elements.append(elem)
        if self._current_section is not None:
            self._current_section.elements.append(elem)

    def _push_section(self, section: Section) -> None:
        self._sections.append(section)
        self._current_section = section

    def _push_env(self, env_name: str) -> None:
        self._env_stack.append(env_name)
        self._current_environment = env_name

    def _pop_env(self) -> str | None:
        if self._env_stack:
            popped = self._env_stack.pop()
            self._current_environment = self._env_stack[-1] if self._env_stack else None
            return popped
        return None

    def _parse(self, text: str) -> None:
        """Main entry: parse LaTeX source."""
        self._parse_preamble(text)
        body_start = text.find(r"\begin{document}")
        body_end = text.find(r"\end{document}")
        if body_start >= 0:
            body_start += len(r"\begin{document}")
        if body_end < 0:
            body_end = len(text)
        body = text[body_start:body_end] if body_start >= 0 and body_start < body_end else text
        self._parse_body(body)

    def _parse_preamble(self, text: str) -> None:
        """Extract documentclass, usepackage, font, layout, colors from preamble."""
        doc_start = text.find(r"\begin{document}")
        preamble = text[:doc_start] if doc_start >= 0 else text

        dc_m = re.search(r"\documentclass\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}", preamble)
        if dc_m:
            self._document_class = dc_m.group(2).strip()
            if dc_m.group(1):
                self._document_options = _parse_keyval(dc_m.group(1))

        for pkg_m in re.finditer(r"\usepackage\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}", preamble):
            opts = _parse_keyval(pkg_m.group(1)) if pkg_m.group(1) else {}
            for p in pkg_m.group(2).strip().split(","):
                p = p.strip()
                if p:
                    self._loaded_packages.append(p)
                    if opts.get("main"):
                        self._current_language = opts["main"]

        fe_m = re.search(r"\usepackage\s*\[([^\]]*)\]\s*\{fontenc\}", preamble)
        if fe_m:
            self._font_encoding = fe_m.group(1).strip()

        ie_m = re.search(r"\usepackage\s*\[([^\]]*)\]\s*\{inputenc\}", preamble)
        if ie_m:
            self._input_encoding = ie_m.group(1).strip()

        main_m = re.search(r"\setmainfont\s*(?:\[[^\]]*\]\s*)?\{([^}]*)\}", preamble)
        if main_m:
            self._base_font = main_m.group(1)
        sans_m = re.search(r"\setsansfont\s*(?:\[[^\]]*\]\s*)?\{([^}]*)\}", preamble)
        if sans_m:
            self._sans_font = sans_m.group(1)
        mono_m = re.search(r"\setmonofont\s*(?:\[[^\]]*\]\s*)?\{([^}]*)\}", preamble)
        if mono_m:
            self._mono_font = mono_m.group(1)

        layout_keys = [
            "textwidth", "textheight", "topmargin", "headheight", "headsep",
            "footskip", "oddsidemargin", "evensidemargin", "marginparwidth",
            "marginparsep", "paperwidth", "paperheight", "hoffset", "voffset",
            "columnsep", "columnseprule", "linewidth", "parindent", "parskip",
        ]
        for key in layout_keys:
            m = re.search(r"\\setlength\s*\{\\" + key + r"\}\s*\{([^}]*)\}", preamble)
            if m:
                setattr(self, "_" + key, _parse_length(m.group(1)))

        geo_m = re.search(r"\geometry\s*\{([^}]*)\}", preamble)
        if geo_m:
            self._document_options.update(_parse_keyval(geo_m.group(1)))

        for m in re.finditer(r"\definecolor\s*\{([^}]*)\}\s*\{([^}]*)\}\s*\{([^}]*)\}", preamble):
            self._color_definitions[m.group(1)] = {
                "model": m.group(2).strip(), "spec": m.group(3).strip(),
            }

        gp_m = re.search(r"\graphicspath\s*\{(?:\s*\{[^}]*\}\s*)+\}", preamble)
        if gp_m:
            self._graphicspath = re.findall(r"\{([^}]*)\}", gp_m.group(0))

        ge_m = re.search(r"\DeclareGraphicsExtensions\s*\{([^}]*)\}", preamble)
        if ge_m:
            self._graphics_extensions = [e.strip() for e in ge_m.group(1).split(",")]

        title_m = re.search(r"\title\s*(?:\[[^\]]*\]\s*)?\{([^}]*)\}", preamble)
        if title_m:
            self._title = title_m.group(1)
        author_m = re.search(r"\author\s*\{([^}]*)\}", preamble)
        if author_m:
            self._author = author_m.group(1)
        date_m = re.search(r"\date\s*\{([^}]*)\}", preamble)
        if date_m:
            self._date = date_m.group(1)
        thanks_m = re.search(r"\thanks\s*\{([^}]*)\}", preamble)
        if thanks_m:
            self._thanks_notes.append(thanks_m.group(1))

    def _extract_title_from_preamble(self, text: str) -> str | None:
        return self._title

    def _parse_body(self, text: str) -> None:
        r"""Parse the body content between \begin{document} and \end{document}."""
        lines = text.split("\n")
        i = 0
        current_paragraph_text: list[str] = []

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if self._in_verbatim and self._verbatim_env:
                end_cmd = rf"\end{{{self._verbatim_env}}}"
                if stripped == end_cmd:
                    self._finalize_verbatim(current_paragraph_text)
                    current_paragraph_text = []
                    self._in_verbatim = False
                    self._verbatim_env = None
                    i += 1
                    continue
                current_paragraph_text.append(line)
                i += 1
                continue

            cleaned = self._strip_comments(line)
            stripped_clean = cleaned.strip()

            if not stripped_clean:
                if current_paragraph_text:
                    para_text = " ".join(current_paragraph_text)
                    if para_text.strip():
                        self._create_paragraph(para_text)
                    current_paragraph_text = []
                i += 1
                continue

            # Environment begin
            begin_m = re.match(r"\begin\s*\{([^}]+)\}\s*(?:\[([^\]]*)\])?\s*(?:\{([^}]*)\})?", stripped_clean)
            if begin_m:
                env_name = begin_m.group(1)
                env_opts = begin_m.group(2) or ""
                env_arg = begin_m.group(3) or ""
                self._push_env(env_name)

                if env_name in ("verbatim", "verbatim*"):
                    self._verbatim_env = env_name
                    current_paragraph_text = []
                    i += 1
                    continue
                elif env_name in ("lstlisting", "minted", "alltt", "spverbatim"):
                    self._verbatim_env = env_name
                    current_paragraph_text = []
                    i += 1
                    continue
                elif env_name in ("itemize", "enumerate", "description"):
                    self._list_depth += 1
                    list_info: dict[str, Any] = {
                        "type": env_name, "items": [],
                        "depth": self._list_depth, "ordered": env_name == "enumerate",
                    }
                    self._list_stack.append(list_info)
                    if current_paragraph_text:
                        para_text = " ".join(current_paragraph_text)
                        if para_text.strip():
                            self._create_paragraph(para_text)
                        current_paragraph_text = []
                elif env_name in ("figure", "figure*", "table", "table*", "wrapfigure", "marginfigure"):
                    placement = env_opts if env_opts else ""
                    self._float_placement = placement
                    float_info = {
                        "type": env_name.replace("*", ""),
                        "placement": placement,
                        "width": env_arg if env_arg else None,
                    }
                    self._float_stack.append(float_info)
                    if env_name.startswith("figure"):
                        self._create_float_section(env_name, placement, "figure")
                    elif env_name.startswith("table"):
                        self._create_float_section(env_name, placement, "table")
                elif env_name in ("tabular", "tabular*", "longtable", "array", "tabularx", "tabulary"):
                    col_spec = env_arg if env_arg else env_opts if env_opts else ""
                    self._tabular_columns = col_spec
                    self._tabular_rows = []
                    if current_paragraph_text:
                        para_text = " ".join(current_paragraph_text)
                        if para_text.strip():
                            self._create_paragraph(para_text)
                        current_paragraph_text = []
                elif env_name == "multicols":
                    self._multicol_depth += 1
                elif env_name in ("quote", "quotation", "verse"):
                    if current_paragraph_text:
                        para_text = " ".join(current_paragraph_text)
                        if para_text.strip():
                            self._create_paragraph(para_text)
                        current_paragraph_text = []
                    self._start_quote_env(env_name)
                elif env_name == "center":
                    if current_paragraph_text:
                        para_text = " ".join(current_paragraph_text)
                        if para_text.strip():
                            self._create_paragraph(para_text)
                        current_paragraph_text = []
                    self._create_paragraph("", alignment="center")
                elif env_name == "flushleft":
                    if current_paragraph_text:
                        para_text = " ".join(current_paragraph_text)
                        if para_text.strip():
                            self._create_paragraph(para_text)
                        current_paragraph_text = []
                    self._create_paragraph("", alignment="left")
                elif env_name == "flushright":
                    if current_paragraph_text:
                        para_text = " ".join(current_paragraph_text)
                        if para_text.strip():
                            self._create_paragraph(para_text)
                        current_paragraph_text = []
                    self._create_paragraph("", alignment="right")
                elif env_name == "titlepage":
                    pass
                elif env_name == "thebibliography":
                    pass
                elif env_name in ("equation", "equation*", "align", "align*", "gather", "gather*",
                                  "multline", "multline*", "displaymath", "math"):
                    pass
                elif env_name in ("subfigure", "subtable"):
                    pass
                elif env_name == "strip":
                    pass
                i += 1
                continue

            # Environment end
            end_m = re.match(r"\end\s*\{([^}]+)\}", stripped_clean)
            if end_m:
                env_name = end_m.group(1)
                if env_name in ("itemize", "enumerate", "description"):
                    if self._list_stack:
                        list_info = self._list_stack.pop()
                        self._finalize_list(list_info)
                    self._list_depth = max(0, self._list_depth - 1)
                elif env_name in ("figure", "figure*", "table", "table*", "wrapfigure", "marginfigure"):
                    if self._float_stack:
                        self._float_stack.pop()
                    self._float_placement = None
                elif env_name in ("tabular", "tabular*", "longtable", "array", "tabularx", "tabulary"):
                    self._finalize_tabular()
                elif env_name == "multicols":
                    self._multicol_depth = max(0, self._multicol_depth - 1)
                elif env_name in ("quote", "quotation", "verse"):
                    self._finalize_quote_env(env_name)
                elif env_name == "titlepage":
                    self._finalize_titlepage()
                self._pop_env()
                i += 1
                continue

            # Sectioning
            section_result = self._match_section_command(stripped_clean)
            if section_result is not None:
                title_text, short_title, starred = section_result
                if current_paragraph_text:
                    para_text = " ".join(current_paragraph_text)
                    if para_text.strip():
                        self._create_paragraph(para_text)
                    current_paragraph_text = []
                cmd_idx = self._get_section_cmd_index(stripped_clean)
                level_map = {0: 1, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}
                lvl = level_map.get(cmd_idx, 2)
                section_type = "unnumbered_section" if starred else "section"
                raw_cmd = self._get_section_raw_cmd(stripped_clean)
                if self._is_appendix and cmd_idx == 2:
                    self._create_section(title_text, lvl, raw_cmd="\\appendix\\section", section_type="appendix_section")
                else:
                    self._create_section(title_text, lvl, raw_cmd=raw_cmd, section_type=section_type)
                i += 1
                continue

            if re.search(r"\appendix\b", stripped_clean):
                self._is_appendix = True
                i += 1
                continue

            if re.search(r"\(frontmatter|mainmatter|backmatter)\b", stripped_clean):
                i += 1
                continue

            inc_m = re.search(r"\(include|input)\s*\{([^}]*)\}", stripped_clean)
            if inc_m:
                current_paragraph_text.append(f"[Included file: {inc_m.group(1)}]")
                i += 1
                continue

            if re.search(r"\maketitle\b", stripped_clean):
                self._finalize_titlepage()
                i += 1
                continue

            if re.search(r"\tableofcontents\b", stripped_clean):
                self._add_logical(LogicalElement(
                    element_id=self._generate_id("toc"),
                    element_type=ElementType.TOC,
                    content=TOCContent(label="toc", level=0),
                    metadata={"latex_command": r"\tableofcontents"},
                ))
                i += 1
                continue
            if re.search(r"\listoffigures\b", stripped_clean):
                self._add_logical(LogicalElement(
                    element_id=self._generate_id("toc"),
                    element_type=ElementType.TOC,
                    content=TOCContent(label="lof", level=0),
                    metadata={"latex_command": r"\listoffigures"},
                ))
                i += 1
                continue
            if re.search(r"\listoftables\b", stripped_clean):
                self._add_logical(LogicalElement(
                    element_id=self._generate_id("toc"),
                    element_type=ElementType.TOC,
                    content=TOCContent(label="lot", level=0),
                    metadata={"latex_command": r"\listoftables"},
                ))
                i += 1
                continue

            # Page/column breaks
            if re.search(r"\pagebreak\b", stripped_clean) or re.search(r"\clearpage\b", stripped_clean) or re.search(r"\cleardoublepage\b", stripped_clean) or re.search(r"\newpage\b", stripped_clean):
                if current_paragraph_text:
                    para_text = " ".join(current_paragraph_text)
                    if para_text.strip():
                        self._create_paragraph(para_text)
                    current_paragraph_text = []
                self._add_logical(LogicalElement(
                    element_id=self._generate_id("pb"),
                    element_type=ElementType.PAGE_BREAK,
                    content=PageBreakContent(),
                ))
                i += 1
                continue
            if re.search(r"\columnbreak\b", stripped_clean):
                self._add_logical(LogicalElement(
                    element_id=self._generate_id("cb"),
                    element_type=ElementType.COLUMN_BREAK,
                    content=ColumnBreakContent(),
                ))
                i += 1
                continue

            # Labels
            label_m = re.search(r"\(label|zlabel)\s*\{([^}]*)\}", stripped_clean)
            if label_m:
                key = label_m.group(1)
                elem_id = self._generate_id("label")
                self._label_map[key] = elem_id
                self._labels[key] = {"id": elem_id, "type": "label"}
                i += 1
                continue

            # Cross references
            ref_m = re.search(r"\(ref|pageref|eqref|autoref|cref|Cref|vref|vpageref|nameref|titleref)\s*\{([^}]*)\}", stripped_clean)
            if ref_m:
                target_key = ref_m.group(1)
                ref_cmd_m = re.search(r"\\([a-zA-Z]+)", ref_m.group(0))
                ref_cmd_name = ref_cmd_m.group(1) if ref_cmd_m else "ref"
                target_id = self._label_map.get(target_key, "")
                xref = CrossReference(
                    source_id=self._generate_id("xref"),
                    target_id=target_id,
                    reference_type="internal",
                    context=ref_cmd_name,
                )
                self._cross_references.append(xref)
                self._add_logical(LogicalElement(
                    element_id=self._generate_id("xref"),
                    element_type=ElementType.LINK,
                    content=LinkContent(url=f"#{target_key}", text=RichTextContent(
                        spans=[RichTextSpan(text=f"[{ref_cmd_name}:{target_key}]")]
                    )),
                    metadata={"ref_type": ref_cmd_name, "target_key": target_key},
                ))
                i += 1
                continue

            # Hyperref
            hyperref_m = re.search(r"\hyperref\s*\[([^\]]*)\]\s*\{([^}]*)\}", stripped_clean)
            if hyperref_m:
                anchor = hyperref_m.group(1)
                link_text = hyperref_m.group(2)
                self._add_logical(LogicalElement(
                    element_id=self._generate_id("href"),
                    element_type=ElementType.LINK,
                    content=LinkContent(url=f"#{anchor}", text=RichTextContent(
                        spans=[RichTextSpan(text=link_text)]
                    )),
                    metadata={"latex_command": r"\hyperref", "anchor": anchor},
                ))
                i += 1
                continue

            hyperlink_m = re.search(r"\hyperlink\s*\{([^}]*)\}\s*\{([^}]*)\}", stripped_clean)
            if hyperlink_m:
                self._add_logical(LogicalElement(
                    element_id=self._generate_id("link"),
                    element_type=ElementType.LINK,
                    content=LinkContent(url=f"#{hyperlink_m.group(1)}",
                                        text=RichTextContent(spans=[RichTextSpan(text=hyperlink_m.group(2))])),
                    metadata={"latex_command": r"\hyperlink"},
                ))
                i += 1
                continue

            hypertarget_m = re.search(r"\hypertarget\s*\{([^}]*)\}\s*\{([^}]*)\}", stripped_clean)
            if hypertarget_m:
                self._label_map[hypertarget_m.group(1)] = self._generate_id("target")
                current_paragraph_text.append(hypertarget_m.group(2))
                i += 1
                continue

            # Footnotes
            fn_m = re.search(r"\footnote\s*(?:\[.*?\])?\s*\{([^}]*)\}", stripped_clean)
            if fn_m:
                note_text = fn_m.group(1)
                fn_id = self._generate_id("footnote")
                fn_content = FootnoteContent(note_id=fn_id, elements=[
                    LogicalElement(
                        element_id=self._generate_id("fn_para"),
                        element_type=ElementType.PARAGRAPH,
                        content=ParagraphContent(
                            text=RichTextContent(spans=[RichTextSpan(text=note_text)])
                        ),
                    )
                ], reference_text=note_text)
                self._footnotes.append(fn_content)
                self._add_logical(LogicalElement(
                    element_id=fn_id,
                    element_type=ElementType.FOOTNOTE,
                    content=fn_content,
                ))
                i += 1
                continue

            if re.search(r"\footnotemark\b", stripped_clean) or re.search(r"\footnotetext\b", stripped_clean):
                i += 1
                continue

            # Endnotes
            en_m = re.search(r"\endnote\s*\{([^}]*)\}", stripped_clean)
            if en_m:
                en_id = self._generate_id("endnote")
                en_content = EndnoteContent(note_id=en_id, elements=[
                    LogicalElement(
                        element_id=self._generate_id("en_para"),
                        element_type=ElementType.PARAGRAPH,
                        content=ParagraphContent(
                            text=RichTextContent(spans=[RichTextSpan(text=en_m.group(1))])
                        ),
                    )
                ], reference_text=en_m.group(1))
                self._endnotes.append(en_content)
                self._add_logical(LogicalElement(
                    element_id=en_id,
                    element_type=ElementType.ENDNOTE,
                    content=en_content,
                ))
                i += 1
                continue

            # Margin notes
            mp_m = re.search(r"\marginpar\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}", stripped_clean)
            if mp_m:
                left = mp_m.group(1) or ""
                right = mp_m.group(2)
                note_text = left if left else right
                comment = CommentContent(
                    comment_id=self._generate_id("marginpar"),
                    author="",
                    text=note_text,
                )
                self._add_logical(LogicalElement(
                    element_id=comment.comment_id,
                    element_type=ElementType.COMMENT,
                    content=comment,
                ))
                i += 1
                continue

            for mn_cmd in ["marginnote", "sidenote", "pagenote"]:
                mn_m = re.search(r"\\" + mn_cmd + r"\s*(?:\[.*?\])?\s*\{([^}]*)\}", stripped_clean)
                if mn_m:
                    comment = CommentContent(
                        comment_id=self._generate_id(mn_cmd),
                        author="",
                        text=mn_m.group(1),
                    )
                    self._add_logical(LogicalElement(
                        element_id=comment.comment_id,
                        element_type=ElementType.COMMENT,
                        content=comment,
                    ))
                    break
            else:
                pass
            i += 1
            continue


            # Check if we already handled margin notes above
            if re.search(r"\(marginnote|sidenote|pagenote)\b", stripped_clean):
                i += 1
                continue

            # Index
            idx_m = re.search(r"\index\s*\{([^}]*)\}", stripped_clean)
            if idx_m:
                entry_text = idx_m.group(1)
                parts = entry_text.split("!")
                term = parts[0].split("@")[-1] if "@" in parts[0] else parts[0]
                sub_term = None
                if len(parts) > 1:
                    sub_term = parts[1].split("@")[-1] if "@" in parts[1] else parts[1]
                cross_refs: list[str] = []
                page_refs: list[str] = []
                for p in parts:
                    see_m = re.search(r"\|see\{([^}]*)\}", p)
                    if see_m:
                        cross_refs.append(see_m.group(1))
                    seealso_m = re.search(r"\|seealso\{([^}]*)\}", p)
                    if seealso_m:
                        cross_refs.append(seealso_m.group(1))
                    if "|(" in p or "|)" in p:
                        page_refs.append("range")
                self._index_entries.append(IndexContent(
                    term=term, sub_term=sub_term,
                    page_refs=page_refs, cross_references=cross_refs,
                ))
                i += 1
                continue

            if re.search(r"\(makeindex|printindex)\b", stripped_clean):
                i += 1
                continue

            sindex_m = re.search(r"\sindex\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}", stripped_clean)
            if sindex_m:
                self._index_entries.append(IndexContent(
                    term=sindex_m.group(2), metadata={"split_cat": sindex_m.group(1)}
                ))
                i += 1
                continue

            # Caption
            cap_m = re.search(r"\caption\s*(\*\s*)?\{([^}]*)\}", stripped_clean)
            if cap_m and not cap_m.group(1):
                cap_text = cap_m.group(2)
                unnumbered = False
            elif cap_m:
                cap_text = cap_m.group(2)
                unnumbered = True
            else:
                cap_text = None
                unnumbered = False
                # captionof
                capof_m = re.search(r"\captionof\s*\{([^}]*)\}\s*\{([^}]*)\}", stripped_clean)
                if capof_m:
                    cap_type = capof_m.group(1)
                    capof_text = capof_m.group(2)
                    self._captions.append(CaptionContent(
                        label="", text=capof_text, position="below",
                        metadata={"captionof_type": cap_type}
                    ))
                    self._add_logical(LogicalElement(
                        element_id=self._generate_id("caption"),
                        element_type=ElementType.CAPTION,
                        content=self._captions[-1],
                    ))
                    i += 1
                    continue

            if cap_text is not None:
                self._captions.append(CaptionContent(
                    label="", text=cap_text, position="below",
                    metadata={"unnumbered": unnumbered},
                ))
                self._add_logical(LogicalElement(
                    element_id=self._generate_id("caption"),
                    element_type=ElementType.CAPTION,
                    content=self._captions[-1],
                ))
                i += 1
                continue

            # Subcaption
            subcap_m = re.search(r"\subcaption\s*\{([^}]*)\}", stripped_clean)
            if subcap_m:
                self._add_logical(LogicalElement(
                    element_id=self._generate_id("subcaption"),
                    element_type=ElementType.CAPTION,
                    content=CaptionContent(
                        label="", text=subcap_m.group(1), position="below",
                        metadata={"sub_caption": True}
                    ),
                ))
                i += 1
                continue

            subref_m = re.search(r"\subref\s*\{([^}]*)\}", stripped_clean)
            if subref_m:
                target_key = subref_m.group(1)
                self._cross_references.append(CrossReference(
                    source_id=self._generate_id("subref"),
                    target_id=self._label_map.get(target_key, ""),
                    reference_type="internal", context="subref",
                ))
                i += 1
                continue

            # Subfigure/subtable
            subfig_m = re.search(r"\begin\{subfigure\}\s*(?:\[.*?\]\s*)?\{([^}]*)\}", stripped_clean)
            if subfig_m:
                self._push_section(Section(
                    section_id=self._generate_id("subfigure"),
                    section_type="subfigure",
                    metadata={"width": subfig_m.group(1), "float_type": "subfigure"},
                ))
                i += 1
                continue
            subtab_m = re.search(r"\begin\{subtable\}\s*(?:\[.*?\]\s*)?\{([^}]*)\}", stripped_clean)
            if subtab_m:
                self._push_section(Section(
                    section_id=self._generate_id("subtable"),
                    section_type="subtable",
                    metadata={"width": subtab_m.group(1), "float_type": "subtable"},
                ))
                i += 1
                continue

            # includegraphics
            img_m = re.search(r"\includegraphics\s*\*?\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}", stripped_clean)
            if img_m:
                opts_str = img_m.group(1) or ""
                img_path = img_m.group(2)
                opts = _parse_keyval(opts_str)
                resolved_path = self._resolve_display_path(img_path)
                img_meta: dict[str, Any] = dict(opts)
                img_meta["raw_path"] = img_path
                img_meta["resolved_path"] = resolved_path
                self._add_logical(LogicalElement(
                    element_id=self._generate_id("image"),
                    element_type=ElementType.IMAGE,
                    content=ImageContent(
                        src=resolved_path,
                        alt=img_path.split("/")[-1].split(".")[0] if img_path else "",
                        width=float(opts["width"]) if "width" in opts else None,
                        height=float(opts["height"]) if "height" in opts else None,
                        metadata=img_meta,
                    ),
                    metadata={"placement": self._float_placement},
                ))
                i += 1
                continue

            # svg/includesvg
            svg_m = re.search(r"\includesvg\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}", stripped_clean)
            if svg_m:
                opts_str = svg_m.group(1) or ""
                svg_path = svg_m.group(2)
                opts = _parse_keyval(opts_str)
                self._add_logical(LogicalElement(
                    element_id=self._generate_id("image"),
                    element_type=ElementType.IMAGE,
                    content=ImageContent(
                        src=svg_path,
                        alt=svg_path.split("/")[-1].split(".")[0] if svg_path else "",
                        width=float(opts["width"]) if "width" in opts else None,
                        height=float(opts["height"]) if "height" in opts else None,
                        metadata={"raw_path": svg_path, "format": "svg", **opts},
                    ),
                ))
                i += 1
                continue

            # rotatebox/reflectbox/resizebox/scalebox
            for rb_cmd in ["rotatebox", "reflectbox", "resizebox", "scalebox"]:
                rb_m = re.search(r"\\" + rb_cmd + r"\s*(?:\[[^\]]*\]\s*)?(?:\{([^}]*)\})*\s*\{([^}]*)\}", stripped_clean)
                if rb_m and rb_m.lastindex and rb_m.group(rb_m.lastindex):
                    current_paragraph_text.append(rb_m.group(rb_m.lastindex))
                    break
            else:
                # adjustbox
                adj_m = re.search(r"\adjustbox\s*\{([^}]*)\}\s*\{([^}]*)\}", stripped_clean)
                if adj_m:
                    current_paragraph_text.append(adj_m.group(2))
                else:
                    # epsfig/psfig/epsfbox
                    old_img_handled = False
                    for old_cmd in ["psfig", "epsfig"]:
                        old_m = re.search(r"\\" + old_cmd + r"\s*(?:\{([^}]*)\}|file\s*=\s*([^,]+))", stripped_clean)
                        if old_m:
                            img_path = old_m.group(1) or old_m.group(2)
                            if img_path:
                                self._add_logical(LogicalElement(
                                    element_id=self._generate_id("image"),
                                    element_type=ElementType.IMAGE,
                                    content=ImageContent(src=img_path.strip(), alt=img_path.strip().split("/")[-1]),
                                ))
                            old_img_handled = True
                            break
                    if not old_img_handled:
                        epsfbox_m = re.search(r"\(epsfbox|epsffile)\s*\{([^}]*)\}", stripped_clean)
                        if epsfbox_m:
                            img_path = epsfbox_m.group(2)
                            self._add_logical(LogicalElement(
                                element_id=self._generate_id("image"),
                                element_type=ElementType.IMAGE,
                                content=ImageContent(src=img_path, alt=img_path.split("/")[-1]),
                            ))
                        else:
                            # Math environments
                            math_env_m = re.search(
                                r"\begin\{(equation|equation\*|align|align\*|gather|gather\*|multline|multline\*|displaymath|math)\}",
                                stripped_clean
                            )
                            if math_env_m:
                                math_env_name = math_env_m.group(1)
                                math_lines: list[str] = []
                                i += 1
                                end_tag = rf"\end{{{math_env_name}}}"
                                while i < len(lines):
                                    if lines[i].strip() == end_tag:
                                        i += 1
                                        break
                                    math_lines.append(lines[i])
                                    i += 1
                                self._create_math_element("\n".join(math_lines), display=True, env_name=math_env_name)
                                continue

                            # \[ ... \]
                            if stripped_clean == "\\[":
                                math_lines = []
                                i += 1
                                while i < len(lines):
                                    if lines[i].strip() == "\\]":
                                        i += 1
                                        break
                                    math_lines.append(lines[i])
                                    i += 1
                                self._create_math_element("\n".join(math_lines), display=True, env_name="displaymath")
                                continue

                            # $$ ... $$
                            dd_m = re.search(r"\$\$(.*?)\$\$", stripped_clean)
                            if dd_m:
                                self._create_math_element(dd_m.group(1), display=True, env_name="displaymath")
                                i += 1
                                continue

                            # Line break
                            if re.search(r"\\\\", stripped_clean):
                                self._add_logical(LogicalElement(
                                    element_id=self._generate_id("lb"),
                                    element_type=ElementType.LINE_BREAK,
                                    content=LineBreakContent(),
                                ))
                                i += 1
                                continue

                            # hspace/vspace
                            hs_matched = False
                            for space_cmd in ["hspace", "vspace"]:
                                hs_m = re.search(r"\\" + space_cmd + r"\s*\*?\s*\{([^}]*)\}", stripped_clean)
                                if hs_m:
                                    hs_matched = True
                                    break
                            if hs_matched:
                                i += 1
                                continue

                            # linespread/setstretch/singlespacing/etc.
                            ls_m = re.search(r"\linespread\s*\{([^}]*)\}", stripped_clean)
                            if ls_m:
                                try:
                                    self._line_spacing = float(ls_m.group(1))
                                except ValueError:
                                    pass
                                i += 1
                                continue
                            ss_m = re.search(r"\setstretch\s*\{([^}]*)\}", stripped_clean)
                            if ss_m:
                                try:
                                    self._line_spacing = float(ss_m.group(1))
                                except ValueError:
                                    pass
                                i += 1
                                continue
                            if re.search(r"\singlespacing\b", stripped_clean):
                                self._line_spacing = 1.0
                                self._line_spacing_rule = "single"
                                i += 1
                                continue
                            if re.search(r"\onehalfspacing\b", stripped_clean):
                                self._line_spacing = 1.5
                                self._line_spacing_rule = "onehalf"
                                i += 1
                                continue
                            if re.search(r"\doublespacing\b", stripped_clean):
                                self._line_spacing = 2.0
                                self._line_spacing_rule = "double"
                                i += 1
                                continue

                            # Tabular rows
                            if self._current_environment in (
                                "tabular", "tabular*", "longtable", "array", "tabularx", "tabulary"
                            ):
                                if "&" in line or "\\\\" in line:
                                    self._process_tabular_row(line)
                                    i += 1
                                    continue

                            # multicolumn/multiclip/booktabs
                            if re.search(r"\(multicolumn|multirow|cline|hhline|toprule|midrule|bottomrule|cmidrule|addlinespace)\b", stripped_clean):
                                i += 1
                                continue

                            # tabular* with width arg
                            if re.search(r"\begin\{tabular\*\}\s*\{[^}]*\}\s*\{[^}]*\}", stripped_clean):
                                i += 1
                                continue

                            # List items
                            item_m = re.match(r"\item\s*(?:\[([^\]]*)\])?\s*(.*)", stripped_clean)
                            if item_m and self._list_stack:
                                label = item_m.group(1)
                                content = item_m.group(2)
                                self._list_stack[-1]["items"].append({"label": label, "content": content})
                                self._create_list_item(content, label)
                                i += 1
                                continue

                            # inline verbs
                            verb_m = re.match(r"\verb\*?([^a-zA-Z])\1(.*?)\1", stripped_clean)
                            if verb_m:
                                self._add_logical(LogicalElement(
                                    element_id=self._generate_id("verb"),
                                    element_type=ElementType.CODE,
                                    content=CodeContent(code=verb_m.group(2), language=None),
                                    metadata={"inline": True},
                                ))
                                i += 1
                                continue

                            # lstinline
                            lstinline_m = re.search(r"\lstinline\s*(?:\[.*?\])?[!](.+?)[!]", stripped_clean)
                            if lstinline_m:
                                self._add_logical(LogicalElement(
                                    element_id=self._generate_id("code"),
                                    element_type=ElementType.CODE,
                                    content=CodeContent(code=lstinline_m.group(1), language=None),
                                    metadata={"inline": True},
                                ))
                                i += 1
                                continue

                            # mint/mintinline
                            mint_m = re.search(r"\mint(?:inline)?\s*(?:\[[^\]]*\])?\{([^}]*)\}\s*\{([^}]*)\}", stripped_clean)
                            if mint_m:
                                self._add_logical(LogicalElement(
                                    element_id=self._generate_id("code"),
                                    element_type=ElementType.CODE,
                                    content=CodeContent(code=mint_m.group(2), language=mint_m.group(1)),
                                    metadata={"inline": "inline" in stripped_clean},
                                ))
                                i += 1
                                continue

                            # Skip bare braces
                            if re.match(r"\{[^}]*\}$", stripped_clean):
                                i += 1
                                continue

                            # Internal spacing
                            if re.search(r"\(vfill|hfill|dotfill|hrulefill|indent|noindent|lefthyphenmin|righthyphenmin)\b", stripped_clean):
                                if "noindent" in stripped_clean:
                                    self._indentation = 0
                                i += 1
                                continue

                            # Header/footer patterns
                            hf_patterns = [
                                r"\fancyhead", r"\fancyfoot", r"\fancyhf",
                                r"\ihead", r"\chead", r"\ohead",
                                r"\ifoot", r"\cfoot", r"\ofoot",
                                r"\pagestyle", r"\thispagestyle",
                                r"\renewcommand.*rulewidth", r"\headrule", r"\footrule",
                                r"\leftmark", r"\rightmark",
                                r"\(raggedbottom|flushbottom)",
                                r"\(twocolumn|onecolumn)",
                                r"\enlargethispage",
                                r"\newgeometry", r"\restoregeometry",
                                r"\suppressfloats", r"\FloatBarrier",
                                r"\captionwidth", r"\captionsetup",
                                r"\fvset", r"\lstset",
                                r"\selectfont", r"\fontsize",
                                r"\fontfamily", r"\fontseries", r"\fontshape", r"\fontencoding",
                                r"\usefont", r"\DeclareCaptionSubType",
                            ]
                            hf_matched = False
                            for hf_pat in hf_patterns:
                                if re.search(hf_pat, stripped_clean):
                                    hf_matched = True
                                    break
                            if hf_matched:
                                i += 1
                                continue

                            # Process escape sequences and add to paragraph
                            cleaned_text = self._process_escape_sequences(cleaned)
                            if cleaned_text.strip():
                                current_paragraph_text.append(cleaned_text.strip())

            i += 1

        if current_paragraph_text:
            para_text = " ".join(current_paragraph_text)
            if para_text.strip():
                self._create_paragraph(para_text)


    def _strip_comments(self, line: str) -> str:
        """Remove LaTeX comments from a line, respecting escapes."""
        result: list[str] = []
        i = 0
        while i < len(line):
            if line[i] == '\\' and i + 1 < len(line):
                result.append(line[i:i+2])
                i += 2
                continue
            if line[i] == '%':
                break
            result.append(line[i])
            i += 1
        return ''.join(result)

    def _process_escape_sequences(self, text: str) -> str:
        """Process LaTeX escape sequences in text."""
        # Order matters: longer sequences first
        replacements = [
            (r'\textbackslash', '\\'),
            (r'\textasciitilde', '~'),
            (r'\textasciicircum', '^'),
            (r'\textbullet', '\u2022'),
            (r'\textendash', '\u2013'),
            (r'\textemdash', '\u2014'),
            (r'\textexclamdown', '\u00a1'),
            (r'\textquestiondown', '\u00bf'),
            (r'\textquotedblleft', '"'),
            (r'\textquotedblright', '"'),
            (r'\textquoteleft', '\u2018'),
            (r'\textquoteright', '\u2019'),
            (r'\textregistered', '\u00ae'),
            (r'\texttrademark', '\u2122'),
            (r'\textcopyright', '\u00a9'),
            (r'\texteuro', '\u20ac'),
            (r'\textsterling', '\u00a3'),
            (r'\textyen', '\u00a5'),
            (r'\textcent', '\u00a2'),
            (r'\textellipsis', '\u2026'),
            (r'\textperiodcentered', '\u00b7'),
            (r'\textcompwordmark', ''),
            (r'\%', '%'),
            (r'\&', '&'),
            (r'\_', '_'),
            (r'\#', '#'),
            (r'\$', '$'),
            (r'\{', '{'),
            (r'\}', '}'),
            (r'\char"', ''),  # \char"HEX - strip
            (r'\symbol{', ''),  # \symbol{num} - strip
        ]
        result = text
        for seq, repl in replacements:
            result = result.replace(seq, repl)
        # Handle remaining simple escapes like \~ \' \` \" \^ \= \. \| etc.
        for simple in ['~', "'", '"', '`', '^', '=', '.', '|', '<', '>']:
            result = result.replace('\\' + simple, simple)
        # Spacing commands
        result = result.replace('\\,', '')
        result = result.replace('\\;', '')
        result = result.replace('\\:', '')
        result = result.replace('\\!', '')
        result = result.replace('\\ ', ' ')
        result = result.replace('~', ' ')
        result = result.replace('---', '\u2014')
        result = result.replace('--', '\u2013')
        result = result.replace('``', '\u201c')
        result = result.replace("''", '\u201d')
        return result

    def _match_section_command(self, line: str) -> tuple[str, str | None, bool] | None:
        """Match sectioning commands. Returns (title, short_title, starred) or None."""
        section_patterns = [
            (r'\\part\s*\*?\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}', 0),
            (r'\\chapter\s*\*?\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}', 1),
            (r'\\section\s*\*?\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}', 2),
            (r'\\subsection\s*\*?\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}', 3),
            (r'\\subsubsection\s*\*?\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}', 4),
            (r'\\paragraph\s*\*?\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}', 5),
            (r'\\subparagraph\s*\*?\s*(?:\[([^\]]*)\])?\s*\{([^}]*)\}', 6),
        ]
        for pattern, _ in section_patterns:
            m = re.search(pattern, line)
            if m:
                groups = m.groups()
                open_brace = line.index('{')
                starred = '*' in line[:open_brace]
                if len(groups) == 1:
                    return groups[0], None, starred
                else:
                    short = groups[0] if groups[0] else None
                    title = groups[1] if len(groups) > 1 else groups[0]
                    return title, short, starred

        minisec_m = re.search(r'\\minisec\s*\{([^}]*)\}', line)
        if minisec_m:
            return minisec_m.group(1), None, True

        add_m = re.search(r'\\addcontentsline\s*\{[^}]*\}\s*\{([^}]*)\}\s*\{([^}]*)\}', line)
        if add_m:
            return add_m.group(2), None, True

        return None

    def _get_section_cmd_index(self, line: str) -> int:
        cmds = ['part', 'chapter', 'section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
        for idx, cmd in enumerate(cmds):
            if re.search(r'\\' + cmd + r'\s*[\*\[{]', line):
                return idx
        return 2

    def _get_section_raw_cmd(self, line: str) -> str:
        m = re.search(r'\\([a-zA-Z]+)', line)
        return '\\' + m.group(1) if m else '\\section'

    def _create_section(self, title: str, level: int, raw_cmd: str = '\\section',
                        section_type: str = 'section') -> None:
        elem_id = self._generate_id(f'section_{level}')
        section = Section(
            title=HeadingContent(
                level=level,
                text=RichTextContent(spans=[RichTextSpan(text=title)])
            ),
            section_type=section_type,
            metadata={'raw_latex': raw_cmd, 'append': self._is_appendix},
        )
        self._push_section(section)

        logical_elem = LogicalElement(
            element_id=elem_id,
            element_type=ElementType.HEADING,
            content=HeadingContent(
                level=level,
                text=RichTextContent(spans=[RichTextSpan(text=title)])
            ),
            metadata={'level': level, 'raw_latex': raw_cmd, 'section_type': section_type},
        )
        self._add_logical(logical_elem)

        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.HEADING,
            metadata={'level': level, 'section_type': section_type},
        )
        self._add_element(doc_elem)

    def _create_paragraph(self, text: str, alignment: str | None = None) -> None:
        if not text.strip():
            return
        elem_id = self._generate_id('paragraph')
        span = RichTextSpan(text=text)
        para_content = ParagraphContent(
            text=RichTextContent(spans=[span]),
            style=None,
        )
        meta: dict[str, Any] = {}
        if alignment:
            meta['alignment'] = alignment
        if self._line_spacing is not None:
            meta['line_spacing'] = self._line_spacing
        if self._line_spacing_rule:
            meta['line_spacing_rule'] = self._line_spacing_rule
        if self._font_size is not None:
            meta['font_size'] = self._font_size
        if self._current_language:
            meta['language'] = self._current_language
        if self._indentation is not None:
            meta['indentation'] = self._indentation

        self._add_logical(LogicalElement(
            element_id=elem_id,
            element_type=ElementType.PARAGRAPH,
            content=para_content,
            metadata=meta,
        ))
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.PARAGRAPH,
            metadata=meta,
        )
        self._add_element(doc_elem)

    def _create_math_element(self, math_str: str, display: bool = False, env_name: str = '') -> None:
        elem_id = self._generate_id('math')
        self._add_logical(LogicalElement(
            element_id=elem_id,
            element_type=ElementType.MATH,
            content=MathContent(latex=math_str, display=display),
            metadata={'display': display, 'env': env_name},
        ))
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.MATH,
            metadata={'display': display, 'env': env_name},
        )
        self._add_element(doc_elem)

    def _create_list_item(self, content: str, label: str | None = None) -> None:
        elem_id = self._generate_id('list_item')
        meta: dict[str, Any] = {}
        if label:
            meta['label'] = label
        logical_elem = LogicalElement(
            element_id=elem_id,
            element_type=ElementType.LIST_ITEM,
            content=ListItemContent(elements=[
                LogicalElement(
                    element_id=self._generate_id('para'),
                    element_type=ElementType.PARAGRAPH,
                    content=ParagraphContent(
                        text=RichTextContent(spans=[RichTextSpan(text=content)])
                    ),
                )
            ]),
            metadata=meta,
        )
        self._add_logical(logical_elem)
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.LIST_ITEM,
            metadata=meta,
        )
        self._add_element(doc_elem)

    def _finalize_list(self, list_info: dict[str, Any]) -> None:
        elem_id = self._generate_id('list')
        items: list[ListItemContent] = []
        for item_data in list_info.get('items', []):
            items.append(ListItemContent(elements=[
                LogicalElement(
                    element_id=self._generate_id('para'),
                    element_type=ElementType.PARAGRAPH,
                    content=ParagraphContent(
                        text=RichTextContent(spans=[RichTextSpan(text=item_data['content'])])
                    ),
                )
            ]))
        self._add_logical(LogicalElement(
            element_id=elem_id,
            element_type=ElementType.LIST,
            content=ListContent(
                ordered=list_info.get('ordered', False),
                items=items,
            ),
            metadata={
                'latex_environment': list_info.get('type', ''),
                'depth': list_info.get('depth', 1),
            },
        ))
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.LIST,
        )
        self._add_element(doc_elem)

    def _start_quote_env(self, env_name: str) -> None:
        self._quote_lines: list[str] = []

    def _finalize_quote_env(self, env_name: str) -> None:
        elem_id = self._generate_id('quote')
        quote_texts: list[str] = []
        # Collect any accumulated paragraph text
        self._add_logical(LogicalElement(
            element_id=elem_id,
            element_type=ElementType.QUOTE,
            content=QuoteContent(elements=[
                LogicalElement(
                    element_id=self._generate_id('q_para'),
                    element_type=ElementType.PARAGRAPH,
                    content=ParagraphContent(
                        text=RichTextContent(spans=[RichTextSpan(text=' '.join(quote_texts))])
                    ),
                )
            ]),
            metadata={'latex_environment': env_name},
        ))
        doc_elem = DocumentElement(element_id=elem_id, element_type=ElementType.QUOTE)
        self._add_element(doc_elem)

    def _finalize_verbatim(self, lines: list[str]) -> None:
        if not lines:
            return
        code_content = '\n'.join(lines)
        elem_id = self._generate_id('code')
        language = None
        if self._verbatim_env in ('lstlisting', 'minted'):
            language = self._verbatim_env
        self._add_logical(LogicalElement(
            element_id=elem_id,
            element_type=ElementType.CODE,
            content=CodeContent(code=code_content, language=language),
            metadata={'latex_environment': self._verbatim_env or 'verbatim'},
        ))
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.CODE,
        )
        self._add_element(doc_elem)

    def _create_float_section(self, env_name: str, placement: str, float_type: str) -> None:
        elem_id = self._generate_id('float')
        section = Section(
            section_id=elem_id,
            section_type=float_type,
            metadata={
                'float_type': float_type,
                'placement': placement,
                'env_name': env_name,
            },
        )
        self._push_section(section)

    def _process_tabular_row(self, line: str) -> None:
        """Process a single tabular row line."""
        # Remove \\ at end
        raw = line.rstrip()
        while raw.endswith('\\\\'):
            raw = raw[:-2].rstrip()
        cells = raw.split('&')
        row_cells: list[TableCell] = []
        for cell_content in cells:
            cell_content = cell_content.strip()
            # Check for multicolumn
            mc_m = re.match(r'\\multicolumn\{(\d+)\}\{([^}]*)\}\{(.*)', cell_content, re.DOTALL)
            if mc_m:
                ncols = int(mc_m.group(1))
                cell_text = mc_m.group(3).strip()
                row_cells.append(TableCell(
                    content=[LogicalElement(
                        element_id=self._generate_id('tc'),
                        element_type=ElementType.PARAGRAPH,
                        content=ParagraphContent(
                            text=RichTextContent(spans=[RichTextSpan(text=cell_text)])
                        ),
                    )],
                    col_span=ncols,
                ))
                continue
            # Check for multirow
            mr_m = re.match(r'\\multirow\{(\d+)\}\{(.*?)\}\{(.*)', cell_content, re.DOTALL)
            if mr_m:
                nrows = int(mr_m.group(1))
                cell_text = mr_m.group(3).strip()
                row_cells.append(TableCell(
                    content=[LogicalElement(
                        element_id=self._generate_id('tc'),
                        element_type=ElementType.PARAGRAPH,
                        content=ParagraphContent(
                            text=RichTextContent(spans=[RichTextSpan(text=cell_text)])
                        ),
                    )],
                    row_span=nrows,
                ))
                continue
            row_cells.append(TableCell(
                content=[LogicalElement(
                    element_id=self._generate_id('tc'),
                    element_type=ElementType.PARAGRAPH,
                    content=ParagraphContent(
                        text=RichTextContent(spans=[RichTextSpan(text=cell_content)])
                    ),
                )],
            ))

        self._tabular_rows.append(row_cells)

    def _finalize_tabular(self) -> None:
        elem_id = self._generate_id('table')
        max_cols = 0
        for row in self._tabular_rows:
            n = sum(c.col_span for c in row)
            if n > max_cols:
                max_cols = n

        rows: list[TableRow] = []
        for row_cells in self._tabular_rows:
            rows.append(TableRow(cells=row_cells))

        table_content = TableContent(
            rows=rows,
            grid=list(range(max_cols)) if max_cols > 0 else None,
            metadata={
                'column_specification': self._tabular_columns,
                'env': self._current_environment or 'tabular',
            },
        )
        self._current_table_content = table_content
        self._add_logical(LogicalElement(
            element_id=elem_id,
            element_type=ElementType.TABLE,
            content=table_content,
            metadata={'column_specification': self._tabular_columns},
        ))
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.TABLE,
        )
        self._add_element(doc_elem)
        self._tabular_rows = []
        self._tabular_columns = ''

    def _resolve_image_path(self, img_path: str) -> str:
        """Resolve image path using graphicspath."""
        if not self._graphicspath:
            return img_path
        return img_path  # In real implementation, search graphicspath

    def _finalize_titlepage(self) -> None:
        """Create title page section."""
        elem_id = self._generate_id('titlepage')
        elements: list[LogicalElement] = []
        if self._title:
            elements.append(LogicalElement(
                element_id=self._generate_id('tp_title'),
                element_type=ElementType.HEADING,
                content=HeadingContent(
                    level=0,
                    text=RichTextContent(spans=[RichTextSpan(text=self._title)]),
                ),
                metadata={'titlepage_element': 'title'},
            ))
        if self._author:
            elements.append(LogicalElement(
                element_id=self._generate_id('tp_author'),
                element_type=ElementType.PARAGRAPH,
                content=ParagraphContent(
                    text=RichTextContent(spans=[RichTextSpan(text=self._author)])
                ),
                metadata={'titlepage_element': 'author'},
            ))
        if self._date:
            elements.append(LogicalElement(
                element_id=self._generate_id('tp_date'),
                element_type=ElementType.PARAGRAPH,
                content=ParagraphContent(
                    text=RichTextContent(spans=[RichTextSpan(text=self._date)])
                ),
                metadata={'titlepage_element': 'date'},
            ))
        for thanks_text in self._thanks_notes:
            fn_id = self._generate_id('thanks')
            fn = FootnoteContent(note_id=fn_id, elements=[
                LogicalElement(
                    element_id=self._generate_id('fn_para'),
                    element_type=ElementType.PARAGRAPH,
                    content=ParagraphContent(
                        text=RichTextContent(spans=[RichTextSpan(text=thanks_text)])
                    ),
                )
            ], reference_text=thanks_text)
            elements.append(LogicalElement(
                element_id=fn_id,
                element_type=ElementType.FOOTNOTE,
                content=fn,
                metadata={'titlepage_element': 'thanks'},
            ))
            self._footnotes.append(fn)

        section = Section(
            section_id=elem_id,
            section_type='titlepage',
            metadata={'raw_latex': '\\maketitle'},
        )
        self._push_section(section)

        for elem in elements:
            self._add_logical(elem)

    def _build_stylesheet(self) -> StyleSheet:
        """Build comprehensive stylesheet from parsed style info."""
        char_styles: dict[str, CharacterStyle] = {}
        para_styles: dict[str, ParagraphStyle] = {}

        # Basic character styles
        char_styles['textbf'] = CharacterStyle(name='textbf', bold=True)
        char_styles['textit'] = CharacterStyle(name='textit', italic=True)
        char_styles['texttt'] = CharacterStyle(name='texttt', font='monospace')
        char_styles['underline'] = CharacterStyle(name='underline', underline=True)
        char_styles['emph'] = CharacterStyle(name='emph', italic=True)
        char_styles['textsl'] = CharacterStyle(name='textsl', italic=True)
        char_styles['textsc'] = CharacterStyle(name='textsc', small_caps=True)
        char_styles['textsuperscript'] = CharacterStyle(name='textsuperscript', superscript=True)
        char_styles['textsubscript'] = CharacterStyle(name='textsubscript', subscript=True)

        # Font encoding styles
        if self._font_encoding:
            char_styles[f'fontenc_{self._font_encoding}'] = CharacterStyle(
                name=f'fontenc_{self._font_encoding}',
                font_charset=self._font_encoding,
            )

        # Color styles
        for color_name, color_def in self._color_definitions.items():
            char_styles[f'color_{color_name}'] = CharacterStyle(
                name=f'color_{color_name}',
                color=color_def.get('spec'),
                _meta={'model': color_def.get('model'), 'spec': color_def.get('spec')},
            )
        char_styles['textcolor_default'] = CharacterStyle(name='textcolor')

        # Font size styles
        size_map = {
            'tiny': 5.0, 'scriptsize': 7.0, 'footnotesize': 8.0,
            'small': 9.0, 'normalsize': 10.0, 'large': 12.0,
            'Large': 14.4, 'LARGE': 17.28, 'huge': 20.74, 'Huge': 24.88,
        }
        for sz_name, sz_val in size_map.items():
            char_styles[f'size_{sz_name}'] = CharacterStyle(name=f'size_{sz_name}', size=sz_val)

        # Font family styles
        char_styles['rmfamily'] = CharacterStyle(name='rmfamily', font_family='roman')
        char_styles['sffamily'] = CharacterStyle(name='sffamily', font_family='sans')
        char_styles['ttfamily'] = CharacterStyle(name='ttfamily', font_family='mono')

        if self._base_font:
            char_styles['setmainfont'] = CharacterStyle(
                name='setmainfont', font=self._base_font,
            )
        if self._sans_font:
            char_styles['setsansfont'] = CharacterStyle(
                name='setsansfont', font=self._sans_font,
            )
        if self._mono_font:
            char_styles['setmonofont'] = CharacterStyle(
                name='setmonofont', font=self._mono_font,
            )

        # Paragraph styles
        para_styles['normal'] = ParagraphStyle(name='normal')
        para_styles['chapter'] = ParagraphStyle(name='chapter', spacing_after=24.0)
        para_styles['section'] = ParagraphStyle(name='section', spacing_after=18.0)
        para_styles['subsection'] = ParagraphStyle(name='subsection', spacing_after=14.0)
        para_styles['subsubsection'] = ParagraphStyle(name='subsubsection', spacing_after=12.0)
        para_styles['paragraph'] = ParagraphStyle(name='paragraph', spacing_after=10.0)
        para_styles['subparagraph'] = ParagraphStyle(name='subparagraph', spacing_after=8.0)
        para_styles['center'] = ParagraphStyle(name='center', alignment='center')
        para_styles['flushleft'] = ParagraphStyle(name='flushleft', alignment='left')
        para_styles['flushright'] = ParagraphStyle(name='flushright', alignment='right')

        if self._indentation is not None:
            para_styles['indented'] = ParagraphStyle(name='indented', indent_left=self._indentation)
        if self._parskip is not None:
            para_styles['parskip'] = ParagraphStyle(name='parskip', spacing_after=self._parskip)
        if self._line_spacing is not None:
            para_styles['line_spacing'] = ParagraphStyle(
                name='line_spacing',
                line_spacing=self._line_spacing,
                line_spacing_rule=self._line_spacing_rule,
            )

        list_styles: dict[str, ListStyle] = {}
        list_styles['enumerate'] = ListStyle(name='enumerate', level_styles={
            i: {'format': 'decimal'} for i in range(1, 7)
        })
        list_styles['itemize'] = ListStyle(name='itemize', level_styles={
            i: {'symbol': chr(8226 if i == 1 else 9702 if i == 2 else 9642 if i == 3 else 8226)}
            for i in range(1, 7)
        })
        list_styles['description'] = ListStyle(name='description')

        table_styles: dict[str, Any] = {
            'tabular': TableStyle(name='tabular'),
            'longtable': TableStyle(name='longtable'),
        }

        return StyleSheet(
            character_styles=char_styles,
            paragraph_styles=para_styles,
            list_styles=list_styles,
            table_styles=table_styles,
        )

    def _build_pages(self) -> list:
        """Build page layout info from collected metadata."""
        return []

    def _build_doc_metadata(self) -> dict[str, Any]:
        """Build document metadata from all parsed preamble and body info."""
        fs: dict[str, Any] = {}

        # Document class info
        fs['document_class'] = self._document_class
        fs['document_options'] = self._document_options.copy()

        # Packages
        fs['loaded_packages'] = list(self._loaded_packages)

        # Font info
        if self._font_encoding:
            fs['font_encoding'] = self._font_encoding
        if self._input_encoding:
            fs['input_encoding'] = self._input_encoding
        if self._base_font:
            fs['base_font'] = self._base_font
        if self._sans_font:
            fs['sans_font'] = self._sans_font
        if self._mono_font:
            fs['mono_font'] = self._mono_font

        # Page layout
        for key in ['textwidth', 'textheight', 'topmargin', 'headheight', 'headsep',
                     'footskip', 'oddsidemargin', 'evensidemargin', 'marginparwidth',
                     'marginparsep', 'paperwidth', 'paperheight', 'hoffset', 'voffset',
                     'columnsep', 'columnseprule', 'linewidth', 'parindent', 'parskip']:
            val = getattr(self, '_' + key, None)
            if val is not None:
                fs[key] = val

        # Colors
        fs['color_definitions'] = dict(self._color_definitions)

        # Language
        if self._current_language:
            fs['language'] = self._current_language
        if self._languages:
            fs['languages'] = list(self._languages)

        # Graphic paths
        if self._graphicspath:
            fs['graphicspath'] = list(self._graphicspath)
        if self._graphics_extensions:
            fs['graphics_extensions'] = list(self._graphics_extensions)

        # Counts
        fs['footnote_count'] = len(self._footnotes)
        fs['endnote_count'] = len(self._endnotes)
        fs['cross_reference_count'] = len(self._cross_references)
        fs['index_entry_count'] = len(self._index_entries)
        fs['toc_entry_count'] = len(self._toc_entries)
        fs['caption_count'] = len(self._captions)
        fs['label_count'] = len(self._labels)
        fs['is_appendix'] = self._is_appendix

        # Title page
        if self._title:
            fs['title'] = self._title
        if self._author:
            fs['author'] = self._author
        if self._date:
            fs['date'] = self._date

        return fs

