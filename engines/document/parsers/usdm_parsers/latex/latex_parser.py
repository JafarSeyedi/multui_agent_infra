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
from ....models.usdm_models import (
    CaptionContent, CodeContent, ColumnBreakContent, CommentContent,
    CrossReference, DocumentElement, EndnoteContent, FooterContent,
    FootnoteContent, HeaderContent, ImageContent, IndexContent,
    LineBreakContent, LinkContent, LogicalElement, PageBreakContent,
    ParagraphContent, RichTextContent, RichTextSpan, Section,
    TableCell, TableContent, TOCContent, USDMDocument,
)
from ...base import BaseDocumentParser
from ...base import ParseOptions
from .latex_elements import LatexElements
from .latex_preamble import LatexPreamble
from .latex_section import LatexSection
from .latex_styles import LatexStyles
from .latex_tables import LatexTables
from .latex_text import LatexText, _parse_keyval

logger = logging.getLogger(__name__)


class LatexParser(BaseDocumentParser, LatexText, LatexPreamble,
                  LatexSection, LatexElements, LatexTables,
                  LatexStyles):
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
                elif env_name in ("titlepage", "thebibliography"):
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
                resolved_path = self._resolve_image_path(img_path)
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
                adj_m = re.search(r"\adjustbox\s*\{([^}]*)\}\s*\{([^}]*)\}", stripped_clean)
                if adj_m:
                    current_paragraph_text.append(adj_m.group(2))
                else:
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

                            dd_m = re.search(r"\$\$(.*?)\$\$", stripped_clean)
                            if dd_m:
                                self._create_math_element(dd_m.group(1), display=True, env_name="displaymath")
                                i += 1
                                continue

                            if re.search(r"\\\\", stripped_clean):
                                self._add_logical(LogicalElement(
                                    element_id=self._generate_id("lb"),
                                    element_type=ElementType.LINE_BREAK,
                                    content=LineBreakContent(),
                                ))
                                i += 1
                                continue

                            hs_matched = False
                            for space_cmd in ["hspace", "vspace"]:
                                hs_m = re.search(r"\\" + space_cmd + r"\s*\*?\s*\{([^}]*)\}", stripped_clean)
                                if hs_m:
                                    hs_matched = True
                                    break
                            if hs_matched:
                                i += 1
                                continue

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

                            if self._current_environment in (
                                "tabular", "tabular*", "longtable", "array", "tabularx", "tabulary"
                            ):
                                if "&" in line or "\\\\" in line:
                                    self._process_tabular_row(line)
                                    i += 1
                                    continue

                            if re.search(r"\(multicolumn|multirow|cline|hhline|toprule|midrule|bottomrule|cmidrule|addlinespace)\b", stripped_clean):
                                i += 1
                                continue

                            if re.search(r"\begin\{tabular\*\}\s*\{[^}]*\}\s*\{[^}]*\}", stripped_clean):
                                i += 1
                                continue

                            item_m = re.match(r"\item\s*(?:\[([^\]]*)\])?\s*(.*)", stripped_clean)
                            if item_m and self._list_stack:
                                label = item_m.group(1)
                                content = item_m.group(2)
                                self._list_stack[-1]["items"].append({"label": label, "content": content})
                                self._create_list_item(content, label)
                                i += 1
                                continue

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

                            if re.match(r"\{[^}]*\}$", stripped_clean):
                                i += 1
                                continue

                            if re.search(r"\(vfill|hfill|dotfill|hrulefill|indent|noindent|lefthyphenmin|righthyphenmin)\b", stripped_clean):
                                if "noindent" in stripped_clean:
                                    self._indentation = 0
                                i += 1
                                continue

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

                            cleaned_text = self._process_escape_sequences(cleaned)
                            if cleaned_text.strip():
                                current_paragraph_text.append(cleaned_text.strip())

            i += 1

        if current_paragraph_text:
            para_text = " ".join(current_paragraph_text)
            if para_text.strip():
                self._create_paragraph(para_text)
