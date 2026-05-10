"""
رایتر LaTeX برای تبدیل مدل USDM به فایل .tex
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ..models.base import BaseDocument
from ..models.exceptions import DocumentWriteError
from ..models.usdm_models import CodeContent
from ..models.usdm_models import ElementType
from ..models.usdm_models import HeadingContent
from ..models.usdm_models import ImageContent
from ..models.usdm_models import LinkContent
from ..models.usdm_models import ListContent
from ..models.usdm_models import ListItemContent
from ..models.usdm_models import LogicalElement
from ..models.usdm_models import MathContent
from ..models.usdm_models import ParagraphContent
from ..models.usdm_models import QuoteContent
from ..models.usdm_models import RichTextContent
from ..models.usdm_models import Section
from ..models.usdm_models import TableCell
from ..models.usdm_models import TableContent
from ..models.usdm_models import USDMDocument
from .base import BaseDocumentWriter
from .base import WriteOptions


class LatexWriter(BaseDocumentWriter):
    """رایتر LaTeX"""

    def __init__(self, options: WriteOptions | None = None):
        super().__init__(options)
        self.options = options or WriteOptions()
        self._indent_level = 0
        self._in_list = False
        self._list_depth = 0
        self._list_is_ordered = False
        self._list_stack: list[dict[str, Any]] = []

    async def write(self, document: BaseDocument) -> bytes:
        """
        تبدیل سند به LaTeX (بایت)
        """
        if self.options is None:
            raise DocumentWriteError("WriteOptions not initialized")
        if not isinstance(document, USDMDocument):
            raise DocumentWriteError("سند باید از نوع USDMDocument باشد")

        try:
            latex_content = self._convert_usdm_to_latex(document)
            return latex_content.encode(self.options.encoding)

        except Exception as e:
            raise DocumentWriteError(f"خطا در نوشتن LaTeX: {e}")

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """
        نوشتن به صورت استریم
        """
        try:
            data = await self.write(document)
            yield data

        except Exception as e:
            raise DocumentWriteError(f"خطا در نوشتن استریم LaTeX: {e}")

    async def write_to_file(self, document: BaseDocument, target: Path,
                           options: dict[str, Any] | None = None) -> None:
        """
        نوشتن سند به فایل
        """
        try:
            data = await self.write(document)
            target.write_bytes(data)

        except Exception as e:
            raise DocumentWriteError(f"خطا در نوشتن فایل LaTeX: {e}")

    def get_supported_media_types(self) -> list[str]:
        """دریافت انواع رسانه پشتیبانی شده"""
        return ["application/x-latex", "text/x-tex"]

    def get_supported_extensions(self) -> list[str]:
        """دریافت پسوندهای پشتیبانی شده"""
        return [".tex", ".latex"]

    def _convert_usdm_to_latex(self, document: USDMDocument) -> str:
        """تبدیل USDM به LaTeX"""
        lines: list[str] = []

        # افزودن پیش‌آمده LaTeX
        lines.append(r"\\documentclass{article}")
        lines.append(r"\\usepackage[utf8]{inputenc}")
        lines.append(r"\\usepackage{graphicx}")
        lines.append(r"\\usepackage{amsmath}")
        lines.append(r"\\usepackage{amssymb}")
        lines.append(r"\\usepackage{hyperref}")
        lines.append(r"\\usepackage{listings}")
        lines.append(r"\\usepackage{xcolor}")
        lines.append(r"\\usepackage{booktabs}")  # برای جداول بهتر
        lines.append(r"\\usepackage{multirow}")  # برای سلول‌های ادغامی
        lines.append("")

        # تنظیمات listings برای کد
        lines.append(r"\\lstset{")
        lines.append(r"  basicstyle=\\ttfamily\small,")
        lines.append(r"  breaklines=true,")
        lines.append(r"  frame=single,")
        lines.append(r"  numbers=left,")
        lines.append(r"  numberstyle=\\tiny,")
        lines.append(r"  keywordstyle=\\color{blue},")
        lines.append(r"  commentstyle=\\color{green},")
        lines.append(r"  stringstyle=\\color{red}")
        lines.append(r"}")
        lines.append("")

        # افزودن عنوان
        if document.title:
            lines.append(r"\\title{" + self._escape_latex(document.title) + "}")
            lines.append(r"\\author{}")
            lines.append(r"\\date{}")
            lines.append("")

        lines.append(r"\\begin{document}")
        lines.append("")

        if document.title:
            lines.append(r"\\maketitle")
            lines.append("")

        # پردازش بخش‌ها
        for section in document.sections:
            section_latex = self._section_to_latex(section, document)
            if section_latex:
                lines.append(section_latex)

        # پردازش المنت‌های مستقل
        for elem in document.elements:
            # بررسی اینکه آیا المنت در بخشی قرار دارد
            in_section = False
            for section in document.sections:
                if any(se.element_id == elem.element_id for se in section.elements):
                    in_section = True
                    break

            if not in_section:
                logical_elem = self._find_logical_element(document, elem.element_id)
                if logical_elem:
                    elem_latex = self._element_to_latex(logical_elem)
                    if elem_latex:
                        lines.append(elem_latex)

        lines.append("")
        lines.append(r"\\end{document}")

        return "\n".join(lines)

    def _find_logical_element(self, document: USDMDocument, element_id: str) -> LogicalElement | None:
        """یافتن المنت منطقی بر اساس شناسه"""
        for elem in document.logical_elements:
            if elem.element_id == element_id:
                return elem
        return None

    def _escape_latex(self, text: str) -> str:
        """فرار کردن کاراکترهای خاص LaTeX"""
        if not text:
            return ""

        escape_chars = {
            '&': r'\\&',
            '%': r'\\%',
            '$': r'\\$',
            '#': r'\\#',
            '_': r'\\_',
            '{': r'\\{',
            '}': r'\\}',
            '~': r'\\textasciitilde{}',
            '^': r'\\^{}',
            '\\': r'\\textbackslash{}',
            '<': r'\\textless{}',
            '>': r'\\textgreater{}',
            '|': r'\\textbar{}'
        }

        result = []
        i = 0
        while i < len(text):
            char = text[i]

            # بررسی دستورات LaTeX
            if char == '\\' and i + 1 < len(text):
                next_char = text[i + 1]
                if next_char in escape_chars:
                    result.append(char + next_char)
                    i += 2
                    continue

            if char in escape_chars:
                result.append(escape_chars[char])
            else:
                result.append(char)

            i += 1

        return ''.join(result)

    def _section_to_latex(self, section: Section, document: USDMDocument) -> str:
        """تبدیل بخش به LaTeX"""
        lines: list[str] = []

        # افزودن عنوان بخش
        if section.title and isinstance(section.title, HeadingContent):
            heading_text = self._rich_text_to_latex(section.title.text)
            level = section.title.level

            if level == 1:
                lines.append(r"\\chapter{" + heading_text + "}")
            elif level == 2:
                lines.append(r"\\section{" + heading_text + "}")
            elif level == 3:
                lines.append(r"\\subsection{" + heading_text + "}")
            elif level == 4:
                lines.append(r"\\subsubsection{" + heading_text + "}")
            elif level == 5:
                lines.append(r"\\paragraph{" + heading_text + "}")
            elif level == 6:
                lines.append(r"\\subparagraph{" + heading_text + "}")
            else:
                lines.append(r"\\section*{" + heading_text + "}")

            lines.append("")

        # پردازش المنت‌های بخش
        for elem in section.elements:
            logical_elem = self._find_logical_element(document, elem.element_id)
            if logical_elem:
                elem_latex = self._element_to_latex(logical_elem)
                if elem_latex:
                    lines.append(elem_latex)

        return "\n".join(lines)

    def _element_to_latex(self, element: LogicalElement) -> str:
        """تبدیل المنت منطقی به LaTeX"""
        content = element.content

        if element.element_type == ElementType.PARAGRAPH and isinstance(content, ParagraphContent):
            return self._paragraph_to_latex(content)

        elif element.element_type == ElementType.HEADING and isinstance(content, HeadingContent):
            return self._heading_to_latex(content)

        elif element.element_type == ElementType.CODE and isinstance(content, CodeContent):
            return self._code_to_latex(content)

        elif element.element_type == ElementType.LIST and isinstance(content, ListContent):
            return self._list_to_latex(content)

        elif element.element_type == ElementType.LIST_ITEM and isinstance(content, ListItemContent):
            return self._list_item_to_latex(content)

        elif element.element_type == ElementType.QUOTE and isinstance(content, QuoteContent):
            return self._quote_to_latex(content)

        elif element.element_type == ElementType.IMAGE and isinstance(content, ImageContent):
            return self._image_to_latex(content)

        elif element.element_type == ElementType.LINK and isinstance(content, LinkContent):
            return self._link_to_latex(content)

        elif element.element_type == ElementType.MATH and isinstance(content, MathContent):
            return self._math_to_latex(content)

        elif element.element_type == ElementType.TABLE and isinstance(content, TableContent):
            return self._table_to_latex(content)

        return ""

    def _rich_text_to_latex(self, rich_text: RichTextContent) -> str:
        """تبدیل RichText به LaTeX"""
        if not rich_text or not rich_text.spans:
            return ""

        result_parts: list[str] = []

        for span in rich_text.spans:
            if not span.text and not span.math:
                continue

            text_to_format = span.math if span.math else self._escape_latex(span.text)

            # اعمال فرمت‌بندی LaTeX
            formatted_text = text_to_format

            # اولویت با math
            if span.math:
                if span.display_math:
                    formatted_text = r"\\[" + formatted_text + r"\\]"
                else:
                    formatted_text = r"$" + formatted_text + r"$"

            # اعمال استایل‌های متنی
            elif span.text:
                if span.code:
                    formatted_text = r"\\texttt{" + formatted_text + "}"

                if span.character_style:
                    style_lower = span.character_style.lower()
                    if "bold" in style_lower or "textbf" in style_lower:
                        formatted_text = r"\\textbf{" + formatted_text + "}"
                    if "italic" in style_lower or "textit" in style_lower or "emph" in style_lower:
                        formatted_text = r"\\textit{" + formatted_text + "}"
                    if "underline" in style_lower:
                        formatted_text = r"\\underline{" + formatted_text + "}"
                    if "monospace" in style_lower or "texttt" in style_lower:
                        formatted_text = r"\\texttt{" + formatted_text + "}"

                # افزودن لینک
                if span.href:
                    formatted_text = r"\\href{" + self._escape_latex(span.href) + "}{" + formatted_text + "}"

            result_parts.append(formatted_text)

        return "".join(result_parts)

    def _paragraph_to_latex(self, content: ParagraphContent) -> str:
        """تبدیل پاراگراف به LaTeX"""
        if not content or not content.text:
            return ""

        latex_text = self._rich_text_to_latex(content.text)
        if not latex_text.strip():
            return ""

        return latex_text + "\n\n"

    def _heading_to_latex(self, content: HeadingContent) -> str:
        """تبدیل هدینگ به LaTeX"""
        if not content or not content.text:
            return ""

        heading_text = self._rich_text_to_latex(content.text)
        if not heading_text.strip():
            return ""

        level = content.level

        if level == 1:
            return r"\\chapter{" + heading_text + "}\n"
        elif level == 2:
            return r"\\section{" + heading_text + "}\n"
        elif level == 3:
            return r"\\subsection{" + heading_text + "}\n"
        elif level == 4:
            return r"\\subsubsection{" + heading_text + "}\n"
        elif level == 5:
            return r"\\paragraph{" + heading_text + "}\n"
        elif level == 6:
            return r"\\subparagraph{" + heading_text + "}\n"
        else:
            return r"\\section*{" + heading_text + "}\n"

    def _code_to_latex(self, content: CodeContent) -> str:
        """تبدیل کد به LaTeX"""
        if not content or not content.code:
            return ""

        code = content.code.rstrip()
        if not code:
            return ""

        lines: list[str] = []

        # تعیین محیط مناسب
        if content.language:
            language = content.language.lower()
            if language in ["python", "java", "c++", "c", "javascript", "typescript"]:
                lines.append(r"\\begin{lstlisting}[language=" + language + "]")
                lines.append(code)
                lines.append(r"\\end{lstlisting}")
            else:
                lines.append(r"\\begin{verbatim}")
                lines.append(code)
                lines.append(r"\\end{verbatim}")
        else:
            lines.append(r"\\begin{verbatim}")
            lines.append(code)
            lines.append(r"\\end{verbatim}")

        lines.append("")  # خط خالی بعد از کد
        return "\n".join(lines)

    def _list_to_latex(self, content: ListContent) -> str:
        """تبدیل لیست به LaTeX"""
        if not content or not content.items:
            return ""

        lines: list[str] = []

        # تعیین نوع لیست
        if content.ordered:
            lines.append(r"\\begin{enumerate}")
        else:
            lines.append(r"\\begin{itemize}")

        # پردازش آیتم‌ها
        for item in content.items:
            if isinstance(item, LogicalElement) and item.element_type == ElementType.LIST_ITEM:
                if isinstance(item.content, ListItemContent):
                    item_latex = self._list_item_content_to_latex(item.content)
                    if item_latex:
                        lines.append(item_latex)
            elif isinstance(item, ListItemContent):
                item_latex = self._list_item_content_to_latex(item)
                if item_latex:
                    lines.append(item_latex)

        if content.ordered:
            lines.append(r"\\end{enumerate}")
        else:
            lines.append(r"\\end{itemize}")

        lines.append("")  # خط خالی بعد از لیست
        return "\n".join(lines)

    def _list_item_to_latex(self, content: ListItemContent) -> str:
        """تبدیل آیتم لیست به LaTeX"""
        return self._list_item_content_to_latex(content)

    def _list_item_content_to_latex(self, content: ListItemContent) -> str:
        """تبدیل محتوای آیتم لیست به LaTeX"""
        if not content or not content.elements:
            return r"\\item"

        lines: list[str] = []

        # پردازش اولین المنت برای \item
        first_elem = content.elements[0]
        if isinstance(first_elem, LogicalElement):
            if first_elem.element_type == ElementType.PARAGRAPH and isinstance(first_elem.content, ParagraphContent):
                item_text = self._rich_text_to_latex(first_elem.content.text)
                lines.append(r"\\item " + item_text)
            else:
                lines.append(r"\\item")
                elem_latex = self._element_to_latex(first_elem)
                if elem_latex:
                    lines.append(elem_latex)
        else:
            lines.append(r"\\item")

        # پردازش المنت‌های باقی‌مانده
        for elem in content.elements[1:]:
            if isinstance(elem, LogicalElement):
                elem_latex = self._element_to_latex(elem)
                if elem_latex:
                    lines.append(elem_latex)

        return "\n".join(lines)

    def _quote_to_latex(self, content: QuoteContent) -> str:
        """تبدیل نقل قول به LaTeX"""
        if not content or not content.elements:
            return ""

        lines: list[str] = []
        lines.append(r"\\begin{quote}")

        for elem in content.elements:
            if isinstance(elem, LogicalElement):
                elem_latex = self._element_to_latex(elem)
                if elem_latex:
                    lines.append(elem_latex)

        lines.append(r"\\end{quote}")
        lines.append("")  # خط خالی بعد از نقل قول
        return "\n".join(lines)

    def _image_to_latex(self, content: ImageContent) -> str:
        """تبدیل تصویر به LaTeX"""
        if not content or not content.src:
            return ""

        lines: list[str] = []

        # ساخت options
        options_parts = []
        if content.width:
            width = content.width
            unit = content.metadata.get("width_unit", "cm") if content.metadata else "cm"
            options_parts.append(f"width={width}{unit}")

        if content.height:
            height = content.height
            unit = content.metadata.get("height_unit", "cm") if content.metadata else "cm"
            options_parts.append(f"height={height}{unit}")

        options_str = ""
        if options_parts:
            options_str = "[" + ",".join(options_parts) + "]"

        # ساخت دستور includegraphics
        src_escaped = self._escape_latex(content.src)
        alt_escaped = self._escape_latex(content.alt) if content.alt else ""

        lines.append(r"\\begin{figure}[htbp]")
        lines.append(r"  \\centering")
        lines.append(r"  \\includegraphics" + options_str + "{" + src_escaped + "}")

        if alt_escaped:
            lines.append(r"  \\caption{" + alt_escaped + "}")

        lines.append(r"\\end{figure}")
        lines.append("")  # خط خالی بعد از تصویر

        return "\n".join(lines)

    def _link_to_latex(self, content: LinkContent) -> str:
        """تبدیل لینک به LaTeX"""
        if not content or not content.url:
            return ""

        href_escaped = self._escape_latex(content.url)

        if content.text and content.text.spans:
            link_text = self._rich_text_to_latex(content.text)
            return r"\\href{" + href_escaped + "}{" + link_text + "}"
        else:
            return r"\\url{" + href_escaped + "}"

    def _math_to_latex(self, content: MathContent) -> str:
        """تبدیل ریاضی به LaTeX"""
        if not content or not content.latex:
            return ""

        latex_math = content.latex.strip()

        if content.display:
            # محیط‌های نمایشی
            return r"\\[" + latex_math + r"\\]"
            # if content.metadata and content.metadata.get("environment") == "align":
            #     lines = []
            #     lines.append(r"\\begin{align*}")
            #     lines.append("  " + latex_math)
            #     lines.append(r"\\end{align*}")
            #     return "\n".join(lines)
            # elif content.metadata and content.metadata.get("environment") == "equation":
            #     lines = []
            #     lines.append(r"\\begin{equation*}")
            #     lines.append("  " + latex_math)
            #     lines.append(r"\\end{equation*}")
            #     return "\n".join(lines)
            # else:
            #     return r"\\[" + latex_math + r"\\]"
        else:
            # ریاضی درون خطی
            return r"$" + latex_math + r"$"

    def _table_to_latex(self, content: TableContent) -> str:
        """تبدیل جدول به LaTeX"""
        if not content or not content.rows:
            return ""

        lines: list[str] = []

        # تعیین تعداد ستون‌ها
        num_columns = 0
        if content.rows:
            num_columns = max(len(row.cells) for row in content.rows)

        if num_columns == 0:
            return ""

        # ساخت مشخصات ستون‌ها
        column_spec = content.metadata.get("column_specification", "l") if content.metadata else "l"
        if len(column_spec) < num_columns:
            column_spec = column_spec[0] * num_columns

        lines.append(r"\\begin{table}[htbp]")
        lines.append(r"  \\centering")
        lines.append(r"  \\begin{tabular}{" + column_spec + "}")
        lines.append(r"    \\toprule")

        # پردازش سطرها
        for i, row in enumerate(content.rows):
            if not row.cells:
                continue

            row_cells = []
            for cell in row.cells:
                cell_content = self._table_cell_to_latex(cell)
                row_cells.append(cell_content)

            # پر کردن سلول‌های خالی
            while len(row_cells) < num_columns:
                row_cells.append("")

            lines.append("    " + " & ".join(row_cells) + r" \\")

            # خط جداکننده
            if i == 0 and content.metadata and content.metadata.get("has_header", False):
                lines.append(r"    \\midrule")

        lines.append(r"    \\bottomrule")
        lines.append(r"  \\end{tabular}")

        # کپشن
        caption_text = content.caption
        if caption_text:
            caption_text_escaped = self._escape_latex(caption_text)
            lines.append(r"  \\caption{" + caption_text_escaped + "}")

        lines.append(r"\\end{table}")
        lines.append("")  # خط خالی بعد از جدول

        return "\n".join(lines)

    def _table_cell_to_latex(self, cell: TableCell) -> str:
        """تبدیل سلول جدول به LaTeX"""
        if not cell or not cell.content:
            return ""

        cell_parts = []
        for elem in cell.content:
            if isinstance(elem, LogicalElement):
                elem_latex = self._element_to_latex(elem)
                if elem_latex:
                    # حذف خطوط خالی اضافی
                    elem_lines = elem_latex.strip().split('\n')
                    cell_parts.append(' '.join(line.strip() for line in elem_lines if line.strip()))

        return ' '.join(cell_parts)
