"""RTF writer for converting USDM documents back to RTF 1.9.1 format."""
from __future__ import annotations

import base64
import re
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ....models.base import BaseDocument
from ....models.exceptions import DocumentWriteError
from ....models.usdm_models import BookmarkContent
from ....models.usdm_models import CodeContent
from ....models.usdm_models import FooterContent
from ....models.usdm_models import FootnoteContent
from ....models.usdm_models import HeaderContent
from ....models.usdm_models import HeadingContent
from ....models.usdm_models import ImageContent
from ....models.usdm_models import LineBreakContent
from ....models.usdm_models import LinkContent
from ....models.usdm_models import ListContent
from ....models.usdm_models import ListItemContent
from ....models.usdm_models import LogicalElement
from ....models.usdm_models import MathContent
from ....models.usdm_models import PageBreakContent
from ....models.usdm_models import ParagraphContent
from ....models.usdm_models import QuoteContent
from ....models.usdm_models import RichTextContent
from ....models.usdm_models import Section
from ....models.usdm_models import TableContent
from ....models.usdm_models import USDMDocument
from ...base import BaseDocumentWriter
from ...base import WriteOptions


class RTFWriter(BaseDocumentWriter):
    """RTF 1.9.1 writer for USDM documents."""

    def __init__(self, options: WriteOptions | None = None):
        super().__init__(options)
        self.options = options or WriteOptions()
        self._font_table: dict[str, int] = {}
        self._color_table: dict[str, int] = {}
        self._font_list: list[str] = []
        self._color_list: list[str] = []
        self._list_depth = 0
        self._list_stack: list[dict[str, Any]] = []

    async def write(self, document: BaseDocument) -> bytes:
        """Convert document to RTF bytes."""
        if self.options is None:
            raise DocumentWriteError("WriteOptions not initialized")
        if not isinstance(document, USDMDocument):
            raise DocumentWriteError("Document must be USDMDocument")

        try:
            self._build_font_table(document)
            self._build_color_table(document)
            rtf_content = self._convert_usdm_to_rtf(document)
            return rtf_content.encode(self.options.encoding)
        except Exception as e:
            raise DocumentWriteError(f"Error writing RTF: {e}")

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """Write document as a stream."""
        try:
            data = await self.write(document)
            yield data
        except Exception as e:
            raise DocumentWriteError(f"Error writing RTF stream: {e}")

    async def write_to_file(self, document: BaseDocument, target: Path,
                            options: dict[str, Any] | None = None) -> None:
        """Write document to file."""
        try:
            data = await self.write(document)
            target.write_bytes(data)
        except Exception as e:
            raise DocumentWriteError(f"Error writing RTF file: {e}")

    def get_supported_media_types(self) -> list[str]:
        return ["application/rtf"]

    def get_supported_extensions(self) -> list[str]:
        return [".rtf"]

    def _build_font_table(self, document: USDMDocument) -> None:
        """Collect all fonts used in the document."""
        self._font_table = {}
        self._font_list = []
        standard_fonts = ["Arial", "Courier"]
        for font in standard_fonts:
            self._font_table[font] = len(self._font_list)
            self._font_list.append(font)

        for elem in document.logical_elements:
            self._collect_fonts_from_element(elem)

    def _collect_fonts_from_element(self, element: LogicalElement) -> None:
        """Recursively collect font names from an element."""
        content = element.content
        if isinstance(content, ParagraphContent):
            self._collect_fonts_from_rich_text(content.text)
        elif isinstance(content, HeadingContent):
            self._collect_fonts_from_rich_text(content.text)
        elif isinstance(content, CodeContent):
            font = "Courier"
            if font not in self._font_table:
                self._font_table[font] = len(self._font_list)
                self._font_list.append(font)
        elif isinstance(content, ListContent):
            for item in content.items:
                if isinstance(item, LogicalElement):
                    self._collect_fonts_from_element(item)
                elif isinstance(item, ListItemContent):
                    for sub in item.elements:
                        self._collect_fonts_from_element(sub)
        elif isinstance(content, TableContent):
            for row in content.rows:
                for cell in row.cells:
                    for sub in cell.content:
                        self._collect_fonts_from_element(sub)
        elif isinstance(content, QuoteContent):
            for sub in content.elements:
                self._collect_fonts_from_element(sub)
        elif isinstance(content, HeaderContent):
            for sub in content.elements:
                self._collect_fonts_from_element(sub)
        elif isinstance(content, FooterContent):
            for sub in content.elements:
                self._collect_fonts_from_element(sub)
        elif isinstance(content, FootnoteContent):
            for sub in content.elements:
                self._collect_fonts_from_element(sub)

    def _collect_fonts_from_rich_text(self, rich_text: RichTextContent) -> None:
        """Collect font names from rich text spans."""
        if not rich_text or not rich_text.spans:
            return
        for span in rich_text.spans:
            if span.font:
                if span.font not in self._font_table:
                    self._font_table[span.font] = len(self._font_list)
                    self._font_list.append(span.font)

    def _build_color_table(self, document: USDMDocument) -> None:
        """Collect all colors used in the document."""
        self._color_table = {}
        self._color_list = []

        for elem in document.logical_elements:
            self._collect_colors_from_element(elem)

    def _collect_colors_from_element(self, element: LogicalElement) -> None:
        """Recursively collect color values from an element."""
        content = element.content
        if isinstance(content, (ParagraphContent, HeadingContent)):
            rt = content.text
            if rt and rt.spans:
                for span in rt.spans:
                    if span.color:
                        self._add_color(span.color)
                    if span.background:
                        self._add_color(span.background)
        elif isinstance(content, ListContent):
            for item in content.items:
                if isinstance(item, LogicalElement):
                    self._collect_colors_from_element(item)
                elif isinstance(item, ListItemContent):
                    for sub in item.elements:
                        self._collect_colors_from_element(sub)
        elif isinstance(content, TableContent):
            for row in content.rows:
                for cell in row.cells:
                    for sub in cell.content:
                        self._collect_colors_from_element(sub)
        elif isinstance(content, QuoteContent):
            for sub in content.elements:
                self._collect_colors_from_element(sub)

    def _add_color(self, color: str) -> None:
        """Add a color to the color table if not already present."""
        if color not in self._color_table:
            self._color_table[color] = len(self._color_list)
            self._color_list.append(color)

    def _color_to_rgb(self, color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        if color.startswith("#") and len(color) == 7:
            return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        return 0, 0, 0

    def _convert_usdm_to_rtf(self, document: USDMDocument) -> str:
        """Convert USDM document to RTF string."""
        lines: list[str] = []

        lines.append(r"{\rtf1\ansi\ansicpg1252\deff0")

        lines.append(self._generate_font_table())
        lines.append(self._generate_color_table())

        if document.stylesheet and document.stylesheet.character_styles:
            lines.append(self._generate_stylesheet(document))

        for section in document.sections:
            section_rtf = self._section_to_rtf(section, document)
            if section_rtf:
                lines.append(section_rtf)

        for elem in document.elements:
            in_section = False
            for section in document.sections:
                if any(se.element_id == elem.element_id for se in section.elements):
                    in_section = True
                    break
            if not in_section:
                logical_elem = self._find_logical_element(document, elem.element_id)
                if logical_elem:
                    elem_rtf = self._element_to_rtf(logical_elem)
                    if elem_rtf:
                        lines.append(elem_rtf)

        lines.append("}")
        return "".join(lines)

    def _find_logical_element(self, document: USDMDocument, element_id: str) -> LogicalElement | None:
        """Find a logical element by ID."""
        for elem in document.logical_elements:
            if elem.element_id == element_id:
                return elem
        return None

    def _generate_font_table(self) -> str:
        """Generate the RTF font table."""
        parts: list[str] = [r"{\fonttbl"]
        for i, font_name in enumerate(self._font_list):
            escaped_name = self._escape_rtf(font_name)
            if "Courier" in font_name:
                parts.append(f"{{\\f{i}\\fmodern\\fcharset0 {escaped_name};}}")
            else:
                parts.append(f"{{\\f{i}\\fswiss\\fcharset0 {escaped_name};}}")
        parts.append("}")
        return "".join(parts)

    def _generate_color_table(self) -> str:
        """Generate the RTF color table."""
        if not self._color_list:
            return r"{\colortbl;}"
        parts: list[str] = [r"{\colortbl;"]
        for color in self._color_list:
            r, g, b = self._color_to_rgb(color)
            parts.append(f"\\red{r}\\green{g}\\blue{b};")
        parts.append("}")
        return "".join(parts)

    def _generate_stylesheet(self, document: USDMDocument) -> str:
        """Generate the RTF stylesheet."""
        parts: list[str] = [r"{\stylesheet"]
        for name, style in document.stylesheet.character_styles.items():
            props: list[str] = []
            if style.bold:
                props.append(r"\b")
            if style.italic:
                props.append(r"\i")
            if style.underline:
                props.append(r"\ul")
            if style.strike:
                props.append(r"\strike")
            if style.font and style.font in self._font_table:
                props.append(f"\\f{self._font_table[style.font]}")
            if style.size:
                props.append(f"\\fs{int(style.size)}")
            if style.color and style.color in self._color_table:
                props.append(f"\\cf{self._color_table[style.color]}")
            if style.highlight and style.highlight in self._color_table:
                props.append(f"\\highlight{self._color_table[style.highlight]}")
            parts.append(f"{{{''.join(props)} {self._escape_rtf(name)};}}")
        parts.append("}")
        return "".join(parts)

    def _section_to_rtf(self, section: Section, document: USDMDocument) -> str:
        """Convert a section to RTF."""
        parts: list[str] = []

        if section.title and isinstance(section.title, HeadingContent):
            heading_rtf = self._heading_to_rtf(section.title)
            if heading_rtf:
                parts.append(heading_rtf)

        for elem in section.elements:
            logical_elem = self._find_logical_element(document, elem.element_id)
            if logical_elem:
                elem_rtf = self._element_to_rtf(logical_elem)
                if elem_rtf:
                    parts.append(elem_rtf)

        return "".join(parts)

    def _element_to_rtf(self, element: LogicalElement) -> str:
        """Convert a logical element to RTF."""
        content = element.content

        if isinstance(content, ParagraphContent):
            return self._paragraph_to_rtf(content)
        elif isinstance(content, HeadingContent):
            return self._heading_to_rtf(content)
        elif isinstance(content, CodeContent):
            return self._code_to_rtf(content)
        elif isinstance(content, ListContent):
            return self._list_to_rtf(content)
        elif isinstance(content, ListItemContent):
            return self._list_item_to_rtf(content)
        elif isinstance(content, QuoteContent):
            return self._quote_to_rtf(content)
        elif isinstance(content, ImageContent):
            return self._image_to_rtf(content)
        elif isinstance(content, LinkContent):
            return self._link_to_rtf(content)
        elif isinstance(content, MathContent):
            return self._math_to_rtf(content)
        elif isinstance(content, TableContent):
            return self._table_to_rtf(content)
        elif isinstance(content, PageBreakContent):
            return r"\page "
        elif isinstance(content, LineBreakContent):
            return r"\line "
        elif isinstance(content, BookmarkContent):
            return self._bookmark_to_rtf(content)
        elif isinstance(content, FootnoteContent):
            return self._footnote_to_rtf(content)
        elif isinstance(content, HeaderContent):
            return self._header_to_rtf(content)
        elif isinstance(content, FooterContent):
            return self._footer_to_rtf(content)

        return ""

    def _paragraph_to_rtf(self, content: ParagraphContent) -> str:
        """Convert paragraph to RTF."""
        if not content or not content.text:
            return ""

        text_rtf = self._rich_text_to_rtf(content.text)
        if not text_rtf.strip():
            return ""

        props: list[str] = []
        if content.style:
            style = content.style.lower()
            if "center" in style:
                props.append(r"\qc")
            elif "right" in style:
                props.append(r"\qr")
            elif "justify" in style:
                props.append(r"\qj")
            else:
                props.append(r"\ql")
            match = re.search(r"li(\d+)", style)
            if match:
                props.append(f"\\li{match.group(1)}")
            match = re.search(r"ri(\d+)", style)
            if match:
                props.append(f"\\ri{match.group(1)}")
            match = re.search(r"fi(\d+)", style)
            if match:
                props.append(f"\\fi{match.group(1)}")

        return "".join(props) + text_rtf + r"\par "

    def _heading_to_rtf(self, content: HeadingContent) -> str:
        """Convert heading to RTF."""
        if not content or not content.text:
            return ""

        text_rtf = self._rich_text_to_rtf(content.text)
        if not text_rtf.strip():
            return ""

        level_sizes = {1: 48, 2: 40, 3: 36, 4: 32, 5: 28, 6: 26}
        font_size = level_sizes.get(content.level, 32)

        return f"\\b\\fs{font_size} " + text_rtf + r"\b0\par "

    def _code_to_rtf(self, content: CodeContent) -> str:
        """Convert code block to RTF."""
        if not content or not content.code:
            return ""

        font_idx = self._font_table.get("Courier", 1)
        escaped_code = self._escape_rtf(content.code)
        escaped_code = escaped_code.replace("\n", r"\par ")

        return f"\\f{font_idx}\\fs20 {escaped_code}\\par "

    def _list_to_rtf(self, content: ListContent) -> str:
        """Convert list to RTF."""
        if not content or not content.items:
            return ""

        parts: list[str] = []
        self._list_depth += 1
        self._list_stack.append({"ordered": content.ordered, "depth": self._list_depth})

        for i, item in enumerate(content.items):
            if isinstance(item, LogicalElement):
                item_rtf = self._element_to_rtf(item)
            elif isinstance(item, ListItemContent):
                item_rtf = self._list_item_to_rtf(item)
            else:
                item_rtf = ""
            if item_rtf:
                if content.ordered:
                    prefix = f"\\pnseclvl1\\pnucrm\\pnstart{i + 1}\\pndec{{{i + 1}}}\\tab "
                else:
                    prefix = r"\pnbody\pnlvlblt\pnf1\pnfs20{\\'b7}\tab "
                parts.append(prefix + item_rtf)

        if self._list_stack:
            self._list_stack.pop()
        self._list_depth -= 1

        return "".join(parts)

    def _list_item_to_rtf(self, content: ListItemContent) -> str:
        """Convert list item to RTF."""
        if not content or not content.elements:
            return ""

        parts: list[str] = []
        for elem in content.elements:
            elem_rtf = self._element_to_rtf(elem)
            if elem_rtf:
                parts.append(elem_rtf)

        return "".join(parts)

    def _quote_to_rtf(self, content: QuoteContent) -> str:
        """Convert quote to RTF."""
        if not content or not content.elements:
            return ""

        parts: list[str] = []
        for elem in content.elements:
            elem_rtf = self._element_to_rtf(elem)
            if elem_rtf:
                parts.append(elem_rtf)

        return r"\li720\ri720 " + "".join(parts)

    def _image_to_rtf(self, content: ImageContent) -> str:
        """Convert image to RTF."""
        parts: list[str] = [r"{\pict"]

        fmt = content.metadata.get("format", "png") if content.metadata else "png"
        if fmt == "jpeg":
            parts.append(r"\jpegblip")
        else:
            parts.append(r"\pngblip")

        if content.width:
            parts.append(f"\\picwgoal{int(content.width * 15)}")
        if content.height:
            parts.append(f"\\pichgoal{int(content.height * 15)}")

        if content.src and not content.src.startswith("pict_"):
            try:
                if content.src.startswith("data:"):
                    data = base64.b64decode(content.src.split(",", 1)[1])
                else:
                    data = Path(content.src).read_bytes()
                hex_data = data.hex()
                parts.append(f"\n{hex_data}")
            except Exception:
                pass

        parts.append("}")
        return "".join(parts)

    def _link_to_rtf(self, content: LinkContent) -> str:
        """Convert link to RTF."""
        if not content or not content.url:
            return ""

        text_rtf = self._rich_text_to_rtf(content.text) if content.text else self._escape_rtf(content.url)
        return (r"{\field{\*\fldinst{HYPERLINK \"" + self._escape_rtf(content.url) + r"\"}}"
                r"{\fldrslt{" + text_rtf + r"}}}")

    def _math_to_rtf(self, content: MathContent) -> str:
        """Convert math to RTF (plain text in parentheses)."""
        if not content or not content.latex:
            return ""

        return f"({self._escape_rtf(content.latex)}) "

    def _table_to_rtf(self, content: TableContent) -> str:
        """Convert table to RTF."""
        if not content or not content.rows:
            return ""

        parts: list[str] = []
        num_columns = 0
        if content.rows:
            num_columns = max(len(row.cells) for row in content.rows)

        if num_columns == 0:
            return ""

        col_width = 1000
        cellx_positions: list[str] = []
        pos = col_width
        for _ in range(num_columns):
            cellx_positions.append(f"\\cellx{pos}")
            pos += col_width

        for row in content.rows:
            parts.append(r"\trowd ")
            parts.append("".join(cellx_positions))

            for cell in row.cells:
                cell_parts: list[str] = []
                for elem in cell.content:
                    elem_rtf = self._element_to_rtf(elem)
                    if elem_rtf:
                        cell_parts.append(elem_rtf)
                cell_text = "".join(cell_parts) if cell_parts else ""
                parts.append(r"\intbl " + cell_text + r"\cell")

            parts.append(r"\row ")

        return "".join(parts)

    def _bookmark_to_rtf(self, content: BookmarkContent) -> str:
        """Convert bookmark to RTF."""
        if not content:
            return ""
        name = self._escape_rtf(content.name)
        return f"{{\\*\\bkmkstart {name}}}{{\\*\\bkmkend {name}}}"

    def _footnote_to_rtf(self, content: FootnoteContent) -> str:
        """Convert footnote to RTF."""
        if not content or not content.elements:
            return ""

        parts: list[str] = [r"{\footnote"]
        for elem in content.elements:
            elem_rtf = self._element_to_rtf(elem)
            if elem_rtf:
                parts.append(elem_rtf)
        parts.append("}")
        return "".join(parts)

    def _header_to_rtf(self, content: HeaderContent) -> str:
        """Convert header to RTF."""
        if not content or not content.elements:
            return ""

        parts: list[str] = [r"\header "]
        for elem in content.elements:
            elem_rtf = self._element_to_rtf(elem)
            if elem_rtf:
                parts.append(elem_rtf)
        return "".join(parts)

    def _footer_to_rtf(self, content: FooterContent) -> str:
        """Convert footer to RTF."""
        if not content or not content.elements:
            return ""

        parts: list[str] = [r"\footer "]
        for elem in content.elements:
            elem_rtf = self._element_to_rtf(elem)
            if elem_rtf:
                parts.append(elem_rtf)
        return "".join(parts)

    def _rich_text_to_rtf(self, rich_text: RichTextContent) -> str:
        """Convert rich text content to RTF."""
        if not rich_text or not rich_text.spans:
            return ""

        parts: list[str] = []
        for span in rich_text.spans:
            if not span.text and not span.math:
                continue

            text = span.math if span.math else span.text
            text = self._escape_rtf(text)

            if span.code:
                font_idx = self._font_table.get("Courier", 1)
                text = f"\\f{font_idx}\\fs20 {text}"

            if span.bold:
                text = f"\\b {text}\\b0"
            if span.italic:
                text = f"\\i {text}\\i0"
            if span.underline:
                text = f"\\ul {text}\\ulnone"
            if span.color and span.color in self._color_table:
                text = f"\\cf{self._color_table[span.color]} {text}"
            if span.font and span.font in self._font_table:
                text = f"\\f{self._font_table[span.font]} {text}"

            parts.append(text)

        return "".join(parts)

    def _escape_rtf(self, text: str) -> str:
        """Escape special RTF characters and encode non-ASCII."""
        if not text:
            return ""

        result: list[str] = []
        for ch in text:
            if ch == "\\":
                result.append("\\\\")
            elif ch == "{":
                result.append("\\{")
            elif ch == "}":
                result.append("\\}")
            elif ch == "\n":
                result.append("\\par ")
            elif ch == "\t":
                result.append("\\tab ")
            elif ord(ch) > 127:
                result.append(f"\\u{ord(ch)}?")
            else:
                result.append(ch)
        return "".join(result)
