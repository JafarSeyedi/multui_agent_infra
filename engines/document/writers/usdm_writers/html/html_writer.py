"""
HTML5 writer for converting USDM documents to HTML5 output.
"""
from __future__ import annotations

import html as html_module
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ....models.base import BaseDocument
from ....models.exceptions import DocumentWriteError
from ....models.usdm_models import (
    AudioContent, BookmarkContent, CaptionContent, ChartContent, CodeContent,
    ColumnBreakContent, CommentContent, DataContent, DrawingContent,
    ElementType, EndnoteContent, FooterContent, FootnoteContent, FormFieldContent,
    HeaderContent, HeadingContent, ImageContent, LaTeXCommandContent,
    LaTeXEnvironmentContent, LineBreakContent, LinkContent, ListContent,
    ListItemContent, LogicalElement, PageBreakContent, ParagraphContent,
    QuoteContent, RichTextContent, RichTextSpan, SectionBreakContent,
    SemanticHTMLContent, ShapeContent, TableCell, TableContent,
    TableRow, TOCContent, USDMDocument, VideoContent,
)
from ..base import BaseDocumentWriter, WriteOptions



class HTMLWriter(BaseDocumentWriter):
    """Writer that converts USDM documents to HTML5."""

    def __init__(self, options: WriteOptions | None = None):
        super().__init__(options)
        self.options = options or WriteOptions()
        self._footnote_counter = 0
        self._endnote_counter = 0
        self._footnotes: list[tuple[str, str]] = []
        self._endnotes: list[tuple[str, str]] = []
    async def write(self, document: BaseDocument) -> bytes:
        """Convert document to HTML5 bytes."""
        if not isinstance(document, USDMDocument):
            raise DocumentWriteError("Document must be a USDMDocument")
        try:
            html_text = self._convert_usdm_to_html(document)
            encoding = self.options.encoding if self.options else "utf-8"
            return html_text.encode(encoding)
        except Exception as e:
            raise DocumentWriteError(f"Error writing HTML: {e}")
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """Write document as a stream of bytes."""
        try:
            data = await self.write(document)
            yield data
        except Exception as e:
            raise DocumentWriteError(f"Error streaming HTML: {e}")

    async def write_to_file(
        self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None
    ) -> None:
        """Write document to an HTML file."""
        try:
            data = await self.write(document)
            target.write_bytes(data)
        except Exception as e:
            raise DocumentWriteError(f"Error writing HTML file: {e}")
    def get_supported_media_types(self) -> list[str]:
        """Return supported media types."""
        return ["text/html"]

    def get_supported_extensions(self) -> list[str]:
        """Return supported file extensions."""
        return [".html", ".htm"]

    def _convert_usdm_to_html(self, document: USDMDocument) -> str:
        """Convert a USDMDocument to a complete HTML5 string."""
        self._footnote_counter = 0
        self._endnote_counter = 0
        self._footnotes = []
        self._endnotes = []
        lines: list[str] = []
        lines.append("<!DOCTYPE html>")
        lines.append('<html lang="en"><head>')
        lines.append('  <meta charset="UTF-8">')
        lines.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        title_text = self._escape_html(document.title) if document.title else "Document"
        lines.append(f"  <title>{title_text}</title>")
        if document.metadata:
            for key, value in document.metadata.items():
                if key.startswith("meta_"):
                    mn = key[5:]
                    lines.append(f'  <meta name="{self._escape_html(mn)}" content="{self._escape_html(str(value))}">')
        css = self._generate_stylesheet(document)
        if css:
            lines.append("  <style>")
            for cl in css.split("\n"):
                lines.append(f"    {cl}")
            lines.append("  </style>")
        lines.append("</head><body>")
        for section in document.sections:
            sh = self._section_to_html(section, document)
            if sh:
                lines.append(sh)
        for elem_ref in document.elements:
            in_section = any(
                any(se.element_id == elem_ref.element_id for se in s.elements)
                for s in document.sections
            )
            if not in_section:
                le = self._find_logical_element(document, elem_ref.element_id)
                if le:
                    eh = self._element_to_html(le)
                    if eh:
                        lines.append(eh)
        if self._footnotes:
            lines.append('  <div class="footnotes"><hr><ol>')
            for fn_id, fn_html in self._footnotes:
                lines.append(f'      <li id="fn-{fn_id}">{fn_html}</li>')
            lines.append("    </ol></div>")
        if self._endnotes:
            lines.append('  <div class="endnotes"><hr><ol>')
            for en_id, en_html in self._endnotes:
                lines.append(f'      <li id="en-{en_id}">{en_html}</li>')
            lines.append("    </ol></div>")
        lines.append("</body></html>")
        return "\n".join(lines)

    def _find_logical_element(self, document: USDMDocument, element_id: str) -> LogicalElement | None:
        """Find a logical element by its ID."""
        for elem in document.logical_elements:
            if elem.element_id == element_id:
                return elem
        return None

    def _section_to_html(self, section: Any, document: USDMDocument) -> str:
        """Convert a section to HTML."""
        tag = "section"
        if section.section_type == "header":
            tag = "header"
        elif section.section_type == "footer":
            tag = "footer"
        sid = f' id="{self._escape_html(section.section_id)}"' if section.section_id else ""
        lines: list[str] = [f"  <{tag}{sid}>"]
        if section.title and isinstance(section.title, HeadingContent):
            hh = self._heading_to_html(section.title)
            if hh:
                lines.append(f"  {hh}")
        for elem_ref in section.elements:
            le = self._find_logical_element(document, elem_ref.element_id)
            if le:
                eh = self._element_to_html(le)
                if eh:
                    lines.append(eh)
        lines.append(f"  </{tag}>")
        return "\n".join(lines)

    def _element_to_html(self, element: LogicalElement) -> str:
        """Convert a single logical element to HTML."""
        content = element.content
        et = element.element_type
        dispatch: dict[ElementType, tuple[type, Any]] = {
            ElementType.PARAGRAPH: (ParagraphContent, self._paragraph_to_html),
            ElementType.HEADING: (HeadingContent, self._heading_to_html),
            ElementType.CODE: (CodeContent, self._code_to_html),
            ElementType.LIST: (ListContent, self._list_to_html),
            ElementType.LIST_ITEM: (ListItemContent, self._list_item_to_html),
            ElementType.QUOTE: (QuoteContent, self._quote_to_html),
            ElementType.IMAGE: (ImageContent, self._image_to_html),
            ElementType.LINK: (LinkContent, self._link_to_html),
            ElementType.TABLE: (TableContent, self._table_to_html),
            ElementType.PAGE_BREAK: (PageBreakContent, lambda c: '  <hr class="page-break">'),
            ElementType.LINE_BREAK: (LineBreakContent, lambda c: "  <br>"),
            ElementType.COLUMN_BREAK: (ColumnBreakContent, lambda c: '  <div class="column-break"></div>'),
            ElementType.FOOTNOTE: (FootnoteContent, self._footnote_to_html),
            ElementType.ENDNOTE: (EndnoteContent, self._endnote_to_html),
            ElementType.COMMENT: (CommentContent, self._comment_to_html),
            ElementType.BOOKMARK: (BookmarkContent, self._bookmark_to_html),
            ElementType.HEADER: (HeaderContent, self._header_to_html),
            ElementType.FOOTER: (FooterContent, self._footer_to_html),
            ElementType.TOC: (TOCContent, self._toc_to_html),
            ElementType.FORM_FIELD: (FormFieldContent, self._form_field_to_html),
            ElementType.VIDEO: (VideoContent, self._video_to_html),
            ElementType.AUDIO: (AudioContent, self._audio_to_html),
            ElementType.SHAPE: (ShapeContent, self._shape_to_html),
            ElementType.DRAWING: (DrawingContent, self._drawing_to_html),
            ElementType.CHART: (ChartContent, self._chart_to_html),
            ElementType.CAPTION: (CaptionContent, self._caption_to_html),
            ElementType.DATA: (DataContent, self._data_to_html),
        }
        if et in dispatch:
            type_cls, handler = dispatch[et]
            if isinstance(content, type_cls):
                return handler(content)
        if et == ElementType.SECTION_BREAK and isinstance(content, SectionBreakContent):
            bt = getattr(content, "break_type", "")
            return f'  <div class="section-break" data-type="{self._escape_html(bt)}"></div>'
        if et == ElementType.SEMANTIC_HTML and isinstance(content, SemanticHTMLContent):
            return self._semantic_html_to_html(content)
        if et == ElementType.LATEX_COMMAND and isinstance(content, LaTeXCommandContent):
            return self._latex_command_to_html(content)
        if et == ElementType.LATEX_ENVIRONMENT and isinstance(content, LaTeXEnvironmentContent):
            return self._latex_environment_to_html(content)
        return ""
    def _paragraph_to_html(self, content: ParagraphContent) -> str:
        """Convert paragraph content to HTML <p>."""
        if not content or not content.text:
            return ""
        th = self._rich_text_to_html(content.text)
        if not th.strip():
            return ""
        cls = f' class="{self._escape_html(content.style)}"' if content.style else ""
        return f"  <p{cls}>{th}</p>"

    def _heading_to_html(self, content: HeadingContent) -> str:
        """Convert heading content to HTML <h1>-<h6>."""
        if not content or not content.text:
            return ""
        th = self._rich_text_to_html(content.text)
        if not th.strip():
            return ""
        level = max(1, min(content.level, 6))
        return f"  <h{level}>{th}</h{level}>"

    def _code_to_html(self, content: CodeContent) -> str:
        """Convert code content to HTML <pre><code>."""
        if not content or not content.code:
            return ""
        ce = self._escape_html(content.code)
        lang = f' class="language-{self._escape_html(content.language)}"' if content.language else ""
        return f"  <pre><code{lang}>{ce}</code></pre>"

    def _list_to_html(self, content: ListContent) -> str:
        """Convert list content to HTML <ol> or <ul>."""
        if not content or not content.items:
            return ""
        tag = "ol" if content.ordered else "ul"
        lines: list[str] = [f"  <{tag}>"]
        for item in content.items:
            lic = item.content if isinstance(item, LogicalElement) and isinstance(item.content, ListItemContent) else (item if isinstance(item, ListItemContent) else None)
            if lic:
                ih = self._list_item_to_html(lic)
                if ih:
                    lines.append(ih)
        lines.append(f"  </{tag}>")
        return "\n".join(lines)

    def _list_item_to_html(self, content: ListItemContent) -> str:
        """Convert list item content to HTML <li>."""
        if not content or not content.elements:
            return "    <li></li>"
        parts: list[str] = []
        for sub in content.elements:
            if isinstance(sub, LogicalElement):
                if sub.element_type == ElementType.PARAGRAPH and isinstance(sub.content, ParagraphContent):
                    ph = self._rich_text_to_html(sub.content.text)
                    if ph:
                        parts.append(ph.strip())
                else:
                    eh = self._element_to_html(sub)
                    if eh:
                        parts.append(eh.strip())
        return f"    <li>{' '.join(parts)}</li>"

    def _quote_to_html(self, content: QuoteContent) -> str:
        """Convert quote content to HTML <blockquote>."""
        if not content or not content.elements:
            return ""
        lines: list[str] = ["  <blockquote>"]
        for elem in content.elements:
            if isinstance(elem, LogicalElement):
                eh = self._element_to_html(elem)
                if eh:
                    lines.append(f"  {eh}")
        lines.append("  </blockquote>")
        return "\n".join(lines)

    def _image_to_html(self, content: ImageContent) -> str:
        """Convert image content to HTML <img>."""
        if not content or not content.src:
            return ""
        attrs = f'src="{self._escape_html(content.src)}" alt="{self._escape_html(content.alt or "")}"'
        if content.width:
            attrs += f' width="{content.width}"'
        if content.height:
            attrs += f' height="{content.height}"'
        if content.metadata:
            for k in ("title", "class", "style"):
                if content.metadata.get(k):
                    attrs += f' {k}="{self._escape_html(content.metadata[k])}"'
        if content.caption or (content.metadata and content.metadata.get("use_figure")):
            lines = ["  <figure>", f"    <img {attrs}>"]
            if content.caption:
                lines.append(f"    <figcaption>{self._escape_html(content.caption)}</figcaption>")
            lines.append("  </figure>")
            return "\n".join(lines)
        return f"  <img {attrs}>"

    def _link_to_html(self, content: LinkContent) -> str:
        """Convert link content to HTML <a>."""
        if not content or not content.url:
            return ""
        href = self._escape_html(content.url)
        th = self._rich_text_to_html(content.text)
        if not th.strip():
            th = href
        cls = f' class="{self._escape_html(content.metadata["class"])}"' if content.metadata and content.metadata.get("class") else ""
        return f'  <a href="{href}"{cls}>{th}</a>'

    def _table_to_html(self, content: TableContent) -> str:
        """Convert table content to HTML <table>."""
        if not content or not content.rows:
            return ""
        lines: list[str] = ["  <table>"]
        if content.caption:
            lines.append(f"    <caption>{self._escape_html(content.caption)}</caption>")
        in_header = False
        in_body = False
        for row in content.rows:
            if row.is_header and not in_header:
                if in_body:
                    lines.append("    </tbody>")
                    in_body = False
                lines.append("    <thead>")
                in_header = True
            elif not row.is_header and not in_body:
                if in_header:
                    lines.append("    </thead>")
                    in_header = False
                lines.append("    <tbody>")
                in_body = True
            rh = self._table_row_to_html(row)
            if rh:
                lines.append(rh)
        if in_header:
            lines.append("    </thead>")
        if in_body:
            lines.append("    </tbody>")
        lines.append("  </table>")
        return "\n".join(lines)

    def _table_row_to_html(self, row: TableRow) -> str:
        """Convert a table row to HTML <tr>."""
        if not row or not row.cells:
            return ""
        lines: list[str] = ["      <tr>"]
        for cell in row.cells:
            ch = self._table_cell_to_html(cell, row.is_header)
            if ch:
                lines.append(ch)
        lines.append("      </tr>")
        return "\n".join(lines)

    def _table_cell_to_html(self, cell: TableCell, is_header_row: bool = False) -> str:
        """Convert a table cell to HTML <th> or <td>."""
        if not cell:
            return ""
        tag = "th" if (cell.is_header or is_header_row) else "td"
        attrs = ""
        if cell.col_span and cell.col_span > 1:
            attrs += f' colspan="{cell.col_span}"'
        if cell.row_span and cell.row_span > 1:
            attrs += f' rowspan="{cell.row_span}"'
        if cell.metadata:
            if cell.metadata.get("class"):
                attrs += f' class="{self._escape_html(cell.metadata["class"])}"'
            if cell.metadata.get("style"):
                attrs += f' style="{self._escape_html(cell.metadata["style"])}"'
        parts: list[str] = []
        if cell.content:
            for item in cell.content:
                if isinstance(item, LogicalElement):
                    if item.element_type == ElementType.PARAGRAPH and isinstance(item.content, ParagraphContent):
                        ph = self._rich_text_to_html(item.content.text)
                        if ph:
                            parts.append(ph.strip())
                    else:
                        eh = self._element_to_html(item)
                        if eh:
                            parts.append(eh.strip())
        return f"        <{tag}{attrs}>{' '.join(parts)}</{tag}>"

    def _footnote_to_html(self, content: FootnoteContent) -> str:
        """Convert footnote content to HTML superscript link."""
        self._footnote_counter += 1
        fn_id = content.note_id or str(self._footnote_counter)
        body = " ".join(
            eh.strip() for elem in (content.elements or [])
            if isinstance(elem, LogicalElement)
            for eh in [self._element_to_html(elem)] if eh
        )
        self._footnotes.append((fn_id, body))
        n = self._footnote_counter
        return f'  <sup class="footnote"><a href="#fn-{fn_id}" id="fn-ref-{fn_id}">{n}</a></sup>'

    def _endnote_to_html(self, content: EndnoteContent) -> str:
        """Convert endnote content to HTML superscript link."""
        self._endnote_counter += 1
        en_id = content.note_id or str(self._endnote_counter)
        body = " ".join(
            eh.strip() for elem in (content.elements or [])
            if isinstance(elem, LogicalElement)
            for eh in [self._element_to_html(elem)] if eh
        )
        self._endnotes.append((en_id, body))
        n = self._endnote_counter
        return f'  <sup class="endnote"><a href="#en-{en_id}" id="en-ref-{en_id}">{n}</a></sup>'

    def _header_to_html(self, content: HeaderContent) -> str:
        if not content or not content.elements:
            return ""
        return self._container_to_html("header", content.elements)

    def _footer_to_html(self, content: FooterContent) -> str:
        if not content or not content.elements:
            return ""
        return self._container_to_html("footer", content.elements)

    def _comment_to_html(self, content: CommentContent) -> str:
        """Convert comment content to HTML comment."""
        author = self._escape_html(content.author) if content.author else ""
        text = self._escape_html(content.text) if content.text else ""
        return f"  <!-- comment by {author}: {text} -->"

    def _bookmark_to_html(self, content: BookmarkContent) -> str:
        """Convert bookmark content to HTML anchor."""
        return f'  <a id="{self._escape_html(content.name)}" class="bookmark"></a>'

    def _container_to_html(self, tag: str, elements: list[LogicalElement]) -> str:
        """Convert a list of elements wrapped in a container tag to HTML."""
        lines: list[str] = [f"  <{tag}>"]
        for elem in elements:
            if isinstance(elem, LogicalElement):
                eh = self._element_to_html(elem)
                if eh:
                    lines.append(f"  {eh}")
        lines.append(f"  </{tag}>")
        return "\n".join(lines)

    def _toc_to_html(self, content: TOCContent) -> str:
        """Convert TOC content to HTML <nav>."""
        label = self._escape_html(content.label) if content.label else "Table of Contents"
        anchor = f' id="{self._escape_html(content.anchor_id)}"' if content.anchor_id else ""
        return f'  <nav class="toc"{anchor}>{label}</nav>'

    def _form_field_to_html(self, content: FormFieldContent) -> str:
        """Convert form field content to HTML form element."""
        name = self._escape_html(content.field_name)
        ft = content.field_type
        va = f' value="{self._escape_html(content.value)}"' if content.value else ""
        ph = f' placeholder="{self._escape_html(content.placeholder)}"' if content.placeholder else ""
        req = " required" if content.required else ""
        ro = " readonly" if content.read_only else ""
        fid = f' id="field-{name}"'
        if ft == "textarea":
            dv = self._escape_html(content.default_value) if content.default_value else ""
            return f'  <textarea name="{name}"{fid}{ph}{req}{ro}>{dv}</textarea>'
        if ft == "select":
            opts = "\n".join(f'    <option value="{self._escape_html(o)}">{self._escape_html(o)}</option>' for o in content.options)
            return f'  <select name="{name}"{fid}{req}{ro}>\n{opts}\n  </select>'
        if ft == "checkbox":
            ck = " checked" if content.value and content.value.lower() in ("true", "1", "yes", "on") else ""
            return f'  <input type="checkbox" name="{name}"{fid}{va}{ck}{req}{ro}>'
        ml = f' maxlength="{content.max_length}"' if content.max_length else ""
        return f'  <input type="{self._escape_html(ft)}" name="{name}"{fid}{va}{ph}{ml}{req}{ro}>'

    def _video_to_html(self, content: VideoContent) -> str:
        """Convert video content to HTML <video>."""
        if not content or not content.src:
            return ""
        src = self._escape_html(content.src)
        attrs = " ".join(filter(None, [
            "controls" if content.controls else "",
            "autoplay" if content.autoplay else "",
            f'width="{content.width}"' if content.width else "",
            f'height="{content.height}"' if content.height else "",
        ]))
        poster = f' poster="{self._escape_html(content.poster)}"' if content.poster else ""
        return f'  <video src="{src}" {attrs}{poster}></video>'

    def _audio_to_html(self, content: AudioContent) -> str:
        """Convert audio content to HTML <audio>."""
        if not content or not content.src:
            return ""
        src = self._escape_html(content.src)
        attrs = " ".join(filter(None, [
            "controls" if content.controls else "",
            "autoplay" if content.autoplay else "",
            "loop" if content.loop else "",
        ]))
        return f'  <audio src="{src}" {attrs}></audio>'

    def _shape_to_html(self, content: ShapeContent) -> str:
        """Convert shape content to HTML <div> with inline styles."""
        if not content:
            return ""
        sp = [f"left:{content.x}px", f"top:{content.y}px", f"width:{content.width}px", f"height:{content.height}px"]
        if content.fill_color:
            sp.append(f"background-color:{content.fill_color}")
        if content.line_color:
            sp.extend([f"border-color:{content.line_color}", f"border-width:{max(1, content.line_width // 12700)}px", "border-style:solid"])
        if content.rotation:
            sp.append(f"transform:rotate({content.rotation}deg)")
        if content.hidden:
            sp.append("display:none")
        sc = self._escape_html(content.shape_type)
        th = self._rich_text_to_html(content.text) if content.text else ""
        return f'  <div class="shape shape-{sc}" style="{";".join(sp)}">{th}</div>'

    def _drawing_to_html(self, content: DrawingContent) -> str:
        """Convert drawing content to embedded SVG."""
        if not content or not content.vector_data:
            return ""
        wa = f' width="{content.width}"' if content.width else ""
        ha = f' height="{content.height}"' if content.height else ""
        return f'  <div class="drawing"{wa}{ha}>{content.vector_data}</div>'

    def _chart_to_html(self, content: ChartContent) -> str:
        """Convert chart content to HTML <div> with data attributes."""
        if not content:
            return ""
        attrs: list[str] = [f'data-chart-type="{self._escape_html(content.chart_type)}"']
        for k in ("title", "grouping", "direction"):
            v = getattr(content, k, None)
            if v:
                attrs.append(f'data-{k}="{self._escape_html(v)}"')
        if content.width:
            attrs.append(f'data-width="{content.width}"')
        if content.height:
            attrs.append(f'data-height="{content.height}"')
        for i, series in enumerate(content.series):
            if series.name:
                attrs.append(f'data-series-{i}-name="{self._escape_html(series.name)}"')
            if series.fill_color:
                attrs.append(f'data-series-{i}-fill="{self._escape_html(series.fill_color)}"')
        return f'  <div class="chart" {" ".join(attrs)}></div>'

    def _semantic_html_to_html(self, content: SemanticHTMLContent) -> str:
        """Convert semantic HTML content to its element."""
        if not content:
            return ""
        aa: list[str] = []
        if content.role:
            aa.append(f'role="{self._escape_html(content.role)}"')
        for k, v in content.aria_attributes.items():
            aa.append(f'{k}="{self._escape_html(v)}"')
        attr_str = f" {' '.join(aa)}" if aa else ""
        return f"  <{content.element_type}{attr_str}></{content.element_type}>"

    def _latex_command_to_html(self, content: LaTeXCommandContent) -> str:
        """Convert LaTeX command content to HTML <span>."""
        if not content:
            return ""
        cmd = self._escape_html(content.command)
        args = ", ".join(content.arguments) if content.arguments else ""
        return f'  <span class="latex-cmd">{cmd}({self._escape_html(args)})</span>'

    def _latex_environment_to_html(self, content: LaTeXEnvironmentContent) -> str:
        """Convert LaTeX environment content to HTML <div>."""
        if not content:
            return ""
        et = self._escape_html(content.environment_type)
        la = f' data-label="{self._escape_html(content.label)}"' if content.label else ""
        ch = f'\n    <div class="latex-caption">{self._escape_html(content.caption)}</div>' if content.caption else ""
        body = "\n".join(
            f"    {eh.strip()}" for item in (content.content or [])
            if isinstance(item, LogicalElement)
            for eh in [self._element_to_html(item)]
            if eh
        )
        return f'  <div class="latex-env latex-env-{et}"{la}>{ch}\n{body}\n  </div>'

    def _caption_to_html(self, content: CaptionContent) -> str:
        """Convert caption content to HTML <figcaption>."""
        if not content:
            return ""
        parts = [self._escape_html(p) for p in (content.label, content.number, content.text) if p]
        return f"  <figcaption>{' '.join(parts)}</figcaption>"

    def _data_to_html(self, content: DataContent) -> str:
        """Convert data field content to HTML <span>."""
        if not content:
            return ""
        ft = self._escape_html(content.field_type)
        val = self._escape_html(content.value) if content.value else ""
        return f'  <span class="field field-{ft.lower()}">{val}</span>'

    def _rich_text_to_html(self, rich_text: RichTextContent) -> str:
        """Convert RichTextContent to HTML inline elements."""
        if not rich_text or not rich_text.spans:
            return ""
        parts: list[str] = []
        for span in rich_text.spans:
            sh = self._span_to_html(span)
            if sh:
                parts.append(sh)
        return "".join(parts)

    def _span_to_html(self, span: RichTextSpan) -> str:
        """Convert a single RichTextSpan to HTML."""
        text = span.text if span.text else ""
        if span.math:
            em = self._escape_html(span.math)
            cls = "math-display" if span.display_math else "math-inline"
            return f'<span class="math {cls}">$${em}$$</span>'
        if not text:
            return ""
        result = self._escape_html(text)
        if span.code:
            result = f"<code>{result}</code>"
        else:
            if span.bold:
                result = f"<strong>{result}</strong>"
            if span.italic:
                result = f"<em>{result}</em>"
            if span.underline:
                result = f'<span style="text-decoration:underline">{result}</span>'
        if span.color or span.font:
            sp: list[str] = []
            if span.color:
                sp.append(f"color:{span.color}")
            if span.font:
                sp.append(f"font-family:{span.font}")
            result = f'<span style="{";".join(sp)}">{result}</span>'
        if span.href:
            result = f'<a href="{self._escape_html(span.href)}">{result}</a>'
        if span.character_style:
            result = f'<span class="{self._escape_html(span.character_style)}">{result}</span>'
        return result

    def _style_to_css(self, cn: str, props: list[str], prefix: str = "") -> list[str]:
        """Helper to emit a CSS rule block."""
        if not props:
            return []
        return [f"{prefix}.{cn} {{"] + props + ["}"]

    def _generate_stylesheet(self, document: USDMDocument) -> str:
        """Generate CSS from the document's StyleSheet."""
        if not document.stylesheet:
            return ""
        lines: list[str] = []
        char_map = [
            ("bold", "  font-weight: bold;"), ("italic", "  font-style: italic;"),
            ("underline", "  text-decoration: underline;"), ("strike", "  text-decoration: line-through;"),
            ("double_strike", "  text-decoration: line-through;"), ("small_caps", "  font-variant: small-caps;"),
            ("all_caps", "  text-transform: uppercase;"),
        ]
        for name, char_style in document.stylesheet.character_styles.items():
            cn = self._css_class_name(name)
            props = [css for attr, css in char_map if getattr(char_style, attr, None)]
            if char_style.color:
                props.append(f"  color: {char_style.color};")
            if char_style.font or char_style.font_family:
                props.append(f"  font-family: {char_style.font or char_style.font_family};")
            if char_style.size:
                props.append(f"  font-size: {char_style.size}pt;")
            if char_style.background or char_style.highlight:
                props.append(f"  background-color: {char_style.background or char_style.highlight};")
            if char_style.superscript:
                props.append("  vertical-align: super; font-size: smaller;")
            if char_style.subscript:
                props.append("  vertical-align: sub; font-size: smaller;")
            lines.extend(self._style_to_css(cn, props))
        for name, para_style in document.stylesheet.paragraph_styles.items():
            cn = self._css_class_name(name)
            props = []
            if para_style.alignment:
                props.append(f"  text-align: {para_style.alignment};")
            if para_style.spacing_before:
                props.append(f"  margin-top: {para_style.spacing_before}pt;")
            if para_style.spacing_after:
                props.append(f"  margin-bottom: {para_style.spacing_after}pt;")
            if para_style.line_spacing:
                props.append(f"  line-height: {para_style.line_spacing};")
            if para_style.indent_left:
                props.append(f"  margin-left: {para_style.indent_left}pt;")
            if para_style.indent_right:
                props.append(f"  margin-right: {para_style.indent_right}pt;")
            if para_style.first_line_indent:
                props.append(f"  text-indent: {para_style.first_line_indent}pt;")
            lines.extend(self._style_to_css(cn, props))
        for name, tbl_style in document.stylesheet.table_styles.items():
            cn = self._css_class_name(name)
            props = ["  border-collapse: collapse;"]
            if tbl_style.border_width:
                props.append(f"  border: {tbl_style.border_width}px solid {tbl_style.border_color or '#000'};")
            if tbl_style.width:
                props.append(f"  width: {tbl_style.width}pt;")
            if tbl_style.alignment == "center":
                props.append("  margin-left: auto; margin-right: auto;")
            elif tbl_style.alignment == "right":
                props.append("  margin-left: auto;")
            lines.extend(self._style_to_css(cn, props, prefix="table"))
        for name, lst_style in document.stylesheet.list_styles.items():
            cn = self._css_class_name(name)
            for level, ls in lst_style.level_styles.items():
                props = []
                if ls.get("list-style-type"):
                    props.append(f"  list-style-type: {ls['list-style-type']};")
                if ls.get("padding-left"):
                    props.append(f"  padding-left: {ls['padding-left']}pt;")
                if props:
                    lines.append(f"ol.{cn}-level-{level}, ul.{cn}-level-{level} {{")
                    lines.extend(props)
                    lines.append("}")
        return "\n".join(lines)

    def _css_class_name(self, name: str) -> str:
        """Convert a style name to a valid CSS class name."""
        return name.lower().replace(" ", "-").replace("_", "-").replace(".", "-")

    def _escape_html(self, text: str) -> str:
        """Escape special HTML characters."""
        if not text:
            return ""
        return html_module.escape(text, quote=True)
