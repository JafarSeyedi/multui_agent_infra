"""
پارسر LaTeX برای تبدیل فایل‌های .tex به مدل USDM
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any, AsyncIterator, List, Tuple, Union
from dataclasses import asdict
import logging

from engines.document.parsers.base import BaseDocumentParser, ParseOptions
from engines.document.models.base import BaseDocument, ElementType
from engines.document.models.media_types import MEDIA_TYPES, MediaType
from engines.document.models.usdm import (
    USDMDocument,
    DocumentElement,
    LogicalElement,
    Section,
    Page,
    RichTextSpan,
    RichTextContent,
    ParagraphContent,
    HeadingContent,
    CodeContent,
    ListContent,
    ListItemContent,
    TableContent,
    TableRow,
    TableCell,
    QuoteContent,
    ImageContent,
    LinkContent,
    MathContent,
    StyleSheet,
    CharacterStyle,
    ParagraphStyle
)
from engines.document.models.exceptions import DocumentParseError

logger = logging.getLogger(__name__)


class LatexParser(BaseDocumentParser):
    """پارسر LaTeX"""
    
    name: str = "latex"
    supported_extensions: tuple[str, ...] = (".tex", ".latex")
    
    def __init__(self):
        super().__init__()
        self._current_section: Optional[Section] = None
        self._sections: List[Section] = []
        self._elements: List[DocumentElement] = []
        self._logical_elements: List[LogicalElement] = []
        self._element_counter: int = 0
        self._brace_stack: List[int] = []
        self._in_math_mode: bool = False
        self._in_verbatim: bool = False
        self._current_environment: Optional[str] = None
    
    async def parse_bytes(self, data: bytes, document_id: str, source_name: str, 
                         metadata: Optional[Dict[str, Any]] = None, 
                         options: Optional[ParseOptions] = None) -> USDMDocument:
        """
        پارس کردن داده‌های بایت LaTeX
        """
        try:
            # تنظیمات پیش‌فرض
            opts = options or ParseOptions()
            
            # تبدیل بایت به متن
            text = data.decode(opts.encoding, errors='replace')
            
            # پردازش LaTeX
            self._reset_parser_state()
            self._parse_latex_content(text)
            
            # ایجاد استایل‌شیت پایه برای LaTeX
            stylesheet = self._create_latex_stylesheet()
            
            # استخراج عنوان از LaTeX
            title = self._extract_title(text) or source_name.replace('.tex', '').replace('.latex', '')
            
            # ایجاد سند USDM
            usdm_doc = USDMDocument(
                document_id=document_id,
                title=title,
                media_type=MEDIA_TYPES["latex"],
                file_extension=".tex",
                sections=self._sections,
                elements=self._elements,
                logical_elements=self._logical_elements,
                stylesheet=stylesheet,
                pages=[],  # LaTeX صفحه‌بندی ندارد
                metadata=metadata or {},
                raw_text=text
            )
            
            return usdm_doc
            
        except Exception as e:
            logger.error(f"خطا در پارس کردن LaTeX: {e}", exc_info=True)
            raise DocumentParseError(f"خطا در پارس کردن LaTeX: {e}")
    
    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str, 
                          source_name: str, metadata: Optional[Dict[str, Any]] = None,
                          options: Optional[ParseOptions] = None) -> USDMDocument:
        """
        پارس کردن از استریم
        """
        try:
            # جمع‌آوری تمام داده‌های استریم
            data_chunks: List[bytes] = []
            async for chunk in stream:
                data_chunks.append(chunk)
            
            data = b''.join(data_chunks)
            return await self.parse_bytes(data, document_id, source_name, metadata, options)
            
        except Exception as e:
            logger.error(f"خطا در پارس کردن استریم LaTeX: {e}", exc_info=True)
            raise DocumentParseError(f"خطا در پارس کردن استریم LaTeX: {e}")
    
    def _reset_parser_state(self) -> None:
        """بازنشانی وضعیت پارسر"""
        self._current_section = None
        self._sections = []
        self._elements = []
        self._logical_elements = []
        self._element_counter = 0
        self._brace_stack = []
        self._in_math_mode = False
        self._in_verbatim = False
        self._current_environment = None
    
    def _generate_id(self, prefix: str = "elem") -> str:
        """تولید شناسه یکتا"""
        self._element_counter += 1
        return f"{prefix}_{self._element_counter}"
    
    def _extract_title(self, text: str) -> Optional[str]:
        """استخراج عنوان از LaTeX"""
        # جستجوی \title{}
        title_match = re.search(r'\\title\s*{([^}]*)}', text)
        if title_match:
            return title_match.group(1).strip()
        
        # جستجوی \maketitle
        if r'\maketitle' in text:
            # سعی در یافتن عنوان در بخش document
            doc_match = re.search(r'\\begin\s*{document}(.*?)\\maketitle', text, re.DOTALL)
            if doc_match:
                content = doc_match.group(1)
                # جستجوی اولین بخش
                section_match = re.search(r'\\(section|chapter|part)\s*{([^}]*)}', content)
                if section_match:
                    return section_match.group(2).strip()
        
        return None
    
    def _create_latex_stylesheet(self) -> StyleSheet:
        """ایجاد استایل‌شیت برای LaTeX"""
        return StyleSheet(
            character_styles={
                "textbf": CharacterStyle(name="textbf", bold=True),
                "textit": CharacterStyle(name="textit", italic=True),
                "texttt": CharacterStyle(name="texttt", font="monospace"),
                "underline": CharacterStyle(name="underline", underline=True),
                "emph": CharacterStyle(name="emph", italic=True),
                "math": CharacterStyle(name="math", font="math")
            },
            paragraph_styles={
                "normal": ParagraphStyle(name="normal"),
                "chapter": ParagraphStyle(name="chapter", spacing_after=24.0),
                "section": ParagraphStyle(name="section", spacing_after=18.0),
                "subsection": ParagraphStyle(name="subsection", spacing_after=14.0),
                "subsubsection": ParagraphStyle(name="subsubsection", spacing_after=12.0),
                "paragraph": ParagraphStyle(name="paragraph", spacing_after=10.0),
                "subparagraph": ParagraphStyle(name="subparagraph", spacing_after=8.0)
            }
        )
    
    def _parse_latex_content(self, text: str) -> None:
        """پردازش محتوای LaTeX"""
        lines = text.split('\n')
        current_paragraph: List[str] = []
        in_paragraph = False
        
        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()
            
            # پردازش خط
            processed_line = self._process_latex_line(line, line_num)
            
            if processed_line:
                current_paragraph.append(processed_line)
                in_paragraph = True
            elif in_paragraph:
                # پایان پاراگراف
                self._finalize_paragraph(current_paragraph)
                current_paragraph = []
                in_paragraph = False
        
        # پاراگراف پایانی
        if in_paragraph:
            self._finalize_paragraph(current_paragraph)
    
    def _process_latex_line(self, line: str, line_num: int) -> Optional[str]:
        """پردازش یک خط LaTeX"""
        # حذف کامنت‌ها
        line = self._remove_comments(line)
        
        # بررسی محیط‌های verbatim
        if self._in_verbatim:
            return self._process_verbatim_line(line)
        
        # بررسی شروع/پایان محیط‌ها
        env_match = self._check_environment_boundaries(line)
        if env_match:
            return None
        
        # بررسی دستورات بخش‌بندی
        section_match = self._process_section_commands(line)
        if section_match is not None:
            return None
        
        # بررسی دستورات ریاضی
        math_match = self._process_math_commands(line)
        if math_match is not None:
            return None
        
        # بررسی دستورات لیست
        list_match = self._process_list_commands(line)
        if list_match is not None:
            return None
        
        # بررسی دستورات جدول
        table_match = self._process_table_commands(line)
        if table_match is not None:
            return None
        
        # بررسی دستورات تصویر
        image_match = self._process_image_commands(line)
        if image_match is not None:
            return None
        
        # بررسی دستورات نقل قول
        quote_match = self._process_quote_commands(line)
        if quote_match is not None:
            return None
        
        # بررسی دستورات کد
        code_match = self._process_code_commands(line)
        if code_match is not None:
            return None
        
        # اگر خط خالی است
        if not line.strip():
            return None
        
        # پردازش خط عادی
        return self._process_normal_line(line)
    
    def _remove_comments(self, line: str) -> str:
        """حذف کامنت‌های LaTeX"""
        # حذف کامنت‌های خطی
        if '%' in line:
            # بررسی اینکه % در محیط ریاضی نباشد
            if not self._in_math_mode:
                # بررسی اینکه % در رشته نباشد
                in_string = False
                result = []
                i = 0
                while i < len(line):
                    if line[i] == '\\' and i + 1 < len(line):
                        result.append(line[i:i+2])
                        i += 2
                        continue
                    elif line[i] == '%' and not in_string:
                        break
                    elif line[i] in ['"', "'"]:
                        in_string = not in_string
                    result.append(line[i])
                    i += 1
                return ''.join(result)
        return line
    
    def _process_verbatim_line(self, line: str) -> Optional[str]:
        """پردازش خط در محیط verbatim"""
        # بررسی پایان محیط verbatim
        if self._current_environment == "verbatim" and line.strip() == r'\end{verbatim}':
            self._in_verbatim = False
            self._current_environment = None
            return None
        
        # اضافه کردن خط به بلوک کد فعلی
        return line
    
    def _check_environment_boundaries(self, line: str) -> bool:
        """بررسی مرزهای محیط LaTeX"""
        line = line.strip()
        
        # بررسی شروع محیط
        begin_match = re.match(r'\\begin\s*{([^}]+)}', line)
        if begin_match:
            env_name = begin_match.group(1)
            self._current_environment = env_name
            
            if env_name in ["verbatim", "lstlisting", "minted", "code"]:
                self._in_verbatim = True
                # ایجاد المنت کد
                self._start_code_environment(env_name)
            elif env_name in ["quote", "quotation"]:
                self._start_quote_environment(env_name)
            elif env_name in ["itemize", "enumerate", "description"]:
                self._start_list_environment(env_name)
            elif env_name == "tabular":
                self._start_table_environment(line)
            
            return True
        
        # بررسی پایان محیط
        end_match = re.match(r'\\end\s*{([^}]+)}', line)
        if end_match:
            env_name = end_match.group(1)
            
            if env_name in ["verbatim", "lstlisting", "minted", "code"]:
                self._in_verbatim = False
                self._finalize_code_environment()
            elif env_name in ["quote", "quotation"]:
                self._finalize_quote_environment()
            elif env_name in ["itemize", "enumerate", "description"]:
                self._finalize_list_environment()
            elif env_name == "tabular":
                self._finalize_table_environment()
            
            if self._current_environment == env_name:
                self._current_environment = None
            
            return True
        
        return False
    
    def _process_section_commands(self, line: str) -> Optional[bool]:
        """پردازش دستورات بخش‌بندی"""
        section_patterns = [
            (r'\\(chapter|part)\s*{([^}]*)}', 1),
            (r'\\section\s*{([^}]*)}', 2),
            (r'\\subsection\s*{([^}]*)}', 3),
            (r'\\subsubsection\s*{([^}]*)}', 4),
            (r'\\paragraph\s*{([^}]*)}', 5),
            (r'\\subparagraph\s*{([^}]*)}', 6)
        ]
        
        for pattern, level in section_patterns:
            match = re.search(pattern, line)
            if match:
                title = match.group(2) if 'chapter' in pattern or 'part' in pattern else match.group(1)
                self._create_section(title.strip(), level)
                return True
        
        return None
    
    def _process_math_commands(self, line: str) -> Optional[bool]:
        """پردازش دستورات ریاضی"""
        # بررسی محیط‌های ریاضی
        math_env_patterns = [
            r'\\begin\s*{equation}',
            r'\\begin\s*{align}',
            r'\\begin\s*{gather}',
            r'\\begin\s*{multline}',
            r'\\begin\s*{math}',
            r'\\begin\s*{displaymath}',
            r'\\[',
            r'\\]',
            r'\$\$',
            r'\$'
        ]
        
        for pattern in math_env_patterns:
            if re.search(pattern, line):
                # استخراج محتوای ریاضی
                math_content = self._extract_math_content(line)
                if math_content:
                    self._create_math_element(math_content)
                return True
        
        return None
    
    def _process_list_commands(self, line: str) -> Optional[bool]:
        """پردازش دستورات لیست"""
        # بررسی \item
        item_match = re.match(r'\\item\s*(?:\[([^\]]*)\])?\s*(.*)', line.strip())
        if item_match:
            label = item_match.group(1)
            content = item_match.group(2)
            self._create_list_item(content.strip(), label)
            return True
        
        return None
    
    def _process_table_commands(self, line: str) -> Optional[bool]:
        """پردازش دستورات جدول"""
        # بررسی خطوط جدول
        if self._current_environment == "tabular":
            if '&' in line and '\\' in line:
                self._process_table_row(line)
                return True
        
        return None
    
    def _process_image_commands(self, line: str) -> Optional[bool]:
        """پردازش دستورات تصویر"""
        # بررسی \includegraphics
        graphics_match = re.search(r'\\includegraphics\s*(?:\[([^\]]*)\])?\s*{([^}]*)}', line)
        if graphics_match:
            options = graphics_match.group(1)
            filename = graphics_match.group(2)
            self._create_image_element(filename, options)
            return True
        
        return None
    
    def _process_quote_commands(self, line: str) -> Optional[bool]:
        """پردازش دستورات نقل قول"""
        # بررسی \quote یا \begin{quote}
        if line.strip().startswith('\\quote') or (self._current_environment in ["quote", "quotation"]):
            # پردازش در _check_environment_boundaries انجام می‌شود
            return True
        
        return None
    
    def _process_code_commands(self, line: str) -> Optional[bool]:
        """پردازش دستورات کد"""
        # بررسی \begin{verbatim} یا \begin{lstlisting}
        if line.strip().startswith('\\begin{verbatim}') or line.strip().startswith('\\begin{lstlisting}'):
            # پردازش در _check_environment_boundaries انجام می‌شود
            return True
        
        return None
    
    def _process_normal_line(self, line: str) -> str:
        """پردازش خط عادی متن"""
        # حذف دستورات LaTeX اضافی
        line = re.sub(r'\\[a-zA-Z]+\s*', ' ', line)
        line = re.sub(r'\\[^a-zA-Z]', '', line)
        
        # حذف براکت‌های اضافی
        line = re.sub(r'{[^}]*}', '', line)
        
        return line.strip()
    
    def _create_section(self, title: str, level: int) -> None:
        """ایجاد بخش جدید"""
        elem_id = self._generate_id(f"section_{level}")
        
        # ایجاد بخش
        section = Section(
            title=HeadingContent(
                level=level,
                text=RichTextContent(spans=[
                    RichTextSpan(text=title)
                ])
            ),
            section_type="section"
        )
        self._sections.append(section)
        self._current_section = section
        
        # ایجاد المنت منطقی
        logical_elem = LogicalElement(
            element_id=elem_id,
            element_type=ElementType.HEADING,
            content=HeadingContent(
                level=level,
                text=RichTextContent(spans=[
                    RichTextSpan(text=title)
                ])
            ),
            metadata={"level": level, "latex_command": f"\\{'chapter' if level == 1 else 'section' if level == 2 else 'subsection' if level == 3 else 'subsubsection' if level == 4 else 'paragraph'}"}
        )
        self._logical_elements.append(logical_elem)
        
        # ایجاد المنت سند
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.HEADING,
            metadata={"level": level}
        )
        self._elements.append(doc_elem)
        
        if self._current_section:
            self._current_section.elements.append(doc_elem)
    
    def _extract_math_content(self, line: str) -> Optional[str]:
        """استخراج محتوای ریاضی"""
        # استخراج محیط‌های ریاضی
        math_patterns = [
            (r'\\begin\s*{equation\*?}(.*?)\\end\s*{equation\*?}', re.DOTALL),
            (r'\\begin\s*{align\*?}(.*?)\\end\s*{align\*?}', re.DOTALL),
            (r'\\begin\s*{gather\*?}(.*?)\\end\s*{gather\*?}', re.DOTALL),
            (r'\\begin\s*{multline\*?}(.*?)\\end\s*{multline\*?}', re.DOTALL),
            (r'\\begin\s*{math}(.*?)\\end\s*{math}', re.DOTALL),
            (r'\\begin\s*{displaymath}(.*?)\\end\s*{displaymath}', re.DOTALL),
            (r'\\\[(.*?)\\\]', re.DOTALL),
            (r'\$\$(.*?)\$\$', re.DOTALL),
            (r'\$(.*?)\$', re.DOTALL)
        ]
        
        for pattern, flags in math_patterns:
            match = re.search(pattern, line, flags)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _create_math_element(self, math_content: str) -> None:
        """ایجاد المنت ریاضی"""
        elem_id = self._generate_id("math")
        
        # ایجاد المنت منطقی
        logical_elem = LogicalElement(
            element_id=elem_id,
            element_type=ElementType.MATH,
            content=MathContent(
                latex=math_content,
                display_mode=True if '$$' in math_content or '\\[' in math_content else False
            ),
            metadata={"latex_environment": "equation" if '\\begin{equation' in math_content else "inline"}
        )
        self._logical_elements.append(logical_elem)
        
        # ایجاد المنت سند
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.MATH
        )
        self._elements.append(doc_elem)
        
        if self._current_section:
            self._current_section.elements.append(doc_elem)
    
    def _create_list_item(self, content: str, label: Optional[str] = None) -> None:
        """ایجاد آیتم لیست"""
        elem_id = self._generate_id("list_item")
        
        # ایجاد المنت منطقی
        logical_elem = LogicalElement(
            element_id=elem_id,
            element_type=ElementType.LIST_ITEM,
            content=ListItemContent(
                elements=[
                    LogicalElement(
                        element_id=self._generate_id("para"),
                        element_type=ElementType.PARAGRAPH,
                        content=ParagraphContent(
                            text=RichTextContent(spans=[
                                RichTextSpan(text=content)
                            ])
                        )
                    )
                ]
            ),
            metadata={"label": label} if label else {}
        )
        self._logical_elements.append(logical_elem)
        
        # ایجاد المنت سند
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.LIST_ITEM
        )
        self._elements.append(doc_elem)
        
        if self._current_section:
            self._current_section.elements.append(doc_elem)
    
    def _start_code_environment(self, env_name: str) -> None:
        """شروع محیط کد"""
        self._current_code_lines: List[str] = []
        self._current_code_env = env_name
    
    def _finalize_code_environment(self) -> None:
        """پایان محیط کد"""
        if hasattr(self, '_current_code_lines') and self._current_code_lines:
            code_content = '\n'.join(self._current_code_lines)
            elem_id = self._generate_id("code")
            
            # ایجاد المنت منطقی
            logical_elem = LogicalElement(
                element_id=elem_id,
                element_type=ElementType.CODE,
                content=CodeContent(
                    code=code_content,
                    language=self._current_code_env if self._current_code_env != "verbatim" else None
                ),
                metadata={"latex_environment": self._current_code_env}
            )
            self._logical_elements.append(logical_elem)
            
            # ایجاد المنت سند
            doc_elem = DocumentElement(
                element_id=elem_id,
                element_type=ElementType.CODE
            )
            self._elements.append(doc_elem)
            
            if self._current_section:
                self._current_section.elements.append(doc_elem)
        
        # پاکسازی
        if hasattr(self, '_current_code_lines'):
            delattr(self, '_current_code_lines')
        if hasattr(self, '_current_code_env'):
            delattr(self, '_current_code_env')
    
    def _start_quote_environment(self, env_name: str) -> None:
        """شروع محیط نقل قول"""
        self._current_quote_lines: List[str] = []
        self._current_quote_env = env_name
    
    def _finalize_quote_environment(self) -> None:
        """پایان محیط نقل قول"""
        if hasattr(self, '_current_quote_lines') and self._current_quote_lines:
            quote_content = '\n'.join(self._current_quote_lines)
            elem_id = self._generate_id("quote")
            
            # ایجاد المنت منطقی
            logical_elem = LogicalElement(
                element_id=elem_id,
                element_type=ElementType.QUOTE,
                content=QuoteContent(
                    elements=[
                        LogicalElement(
                            element_id=self._generate_id("para"),
                            element_type=ElementType.PARAGRAPH,
                            content=ParagraphContent(
                                text=RichTextContent(spans=[
                                    RichTextSpan(text=quote_content)
                                ])
                            )
                        )
                    ]
                ),
                metadata={"latex_environment": self._current_quote_env}
            )
            self._logical_elements.append(logical_elem)
            
            # ایجاد المنت سند
            doc_elem = DocumentElement(
                element_id=elem_id,
                element_type=ElementType.QUOTE
            )
            self._elements.append(doc_elem)
            
            if self._current_section:
                self._current_section.elements.append(doc_elem)
        
        # پاکسازی
        if hasattr(self, '_current_quote_lines'):
            delattr(self, '_current_quote_lines')
        if hasattr(self, '_current_quote_env'):
            delattr(self, '_current_quote_env')
    
    def _start_list_environment(self, env_name: str) -> None:
        """شروع محیط لیست"""
        elem_id = self._generate_id("list")
        
        # ایجاد المنت منطقی
        logical_elem = LogicalElement(
            element_id=elem_id,
            element_type=ElementType.LIST,
            content=ListContent(
                ordered=(env_name == "enumerate"),
                items=[]
            ),
            metadata={"latex_environment": env_name}
        )
        self._logical_elements.append(logical_elem)
        
        # ایجاد المنت سند
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.LIST
        )
        self._elements.append(doc_elem)
        
        if self._current_section:
            self._current_section.elements.append(doc_elem)
    
    def _finalize_list_environment(self) -> None:
        """پایان محیط لیست"""
        # در این پیاده‌سازی ساده، لیست‌ها به صورت تودرتو پردازش نمی‌شوند
        pass
    
    def _start_table_environment(self, line: str) -> None:
        """شروع محیط جدول"""
        # استخراج مشخصات جدول
        col_spec_match = re.search(r'\\begin\s*{tabular}\s*{([^}]*)}', line)
        col_spec = col_spec_match.group(1) if col_spec_match else "l"
        
        elem_id = self._generate_id("table")
        
        # ایجاد المنت منطقی
        logical_elem = LogicalElement(
            element_id=elem_id,
            element_type=ElementType.TABLE,
            content=TableContent(
                rows=[],
                metadata={"column_specification": col_spec}
            ),
            metadata={"latex_environment": "tabular"}
        )
        self._logical_elements.append(logical_elem)
        
        # ایجاد المنت سند
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.TABLE
        )
        self._elements.append(doc_elem)
        
        if self._current_section:
            self._current_section.elements.append(doc_elem)
    
    def _process_table_row(self, line: str) -> None:
        """پردازش سطر جدول"""
        # تقسیم خط به سلول‌ها
        cells = [cell.strip() for cell in line.split('&')]
        # حذف \\ انتهایی
        cells = [cell.rstrip('\\\\').strip() for cell in cells]
        
        # ایجاد سطر
        row_cells = []
        for cell_content in cells:
            if cell_content:
                cell_elem = TableCell(
                    content=[
                        LogicalElement(
                            element_id=self._generate_id("table_cell"),
                            element_type=ElementType.PARAGRAPH,
                            content=ParagraphContent(
                                text=RichTextContent(spans=[
                                    RichTextSpan(text=cell_content)
                                ])
                            )
                        )
                    ]
                )
                row_cells.append(cell_elem)
        
        if row_cells:
            table_row = TableRow(cells=row_cells)
            
            # یافتن جدول فعلی
            for elem in reversed(self._logical_elements):
                if elem.element_type == ElementType.TABLE and isinstance(elem.content, TableContent):
                    elem.content.rows.append(table_row)
                    break
    
    def _finalize_table_environment(self) -> None:
        """پایان محیط جدول"""
        # در این پیاده‌سازی، جدول قبلاً پردازش شده
        pass
    
    def _create_image_element(self, filename: str, options: Optional[str] = None) -> None:
        """ایجاد المنت تصویر"""
        elem_id = self._generate_id("image")
        
        # تجزیه options
        metadata = {}
        if options:
            # استخراج width و height از options
            width_match = re.search(r'width=([\d.]+)(cm|in|pt|mm|ex|em)?', options)
            height_match = re.search(r'height=([\d.]+)(cm|in|pt|mm|ex|em)?', options)
            
            if width_match:
                metadata["width"] = width_match.group(1)
                if width_match.group(2):
                    metadata["width_unit"] = width_match.group(2)
            
            if height_match:
                metadata["height"] = height_match.group(1)
                if height_match.group(2):
                    metadata["height_unit"] = height_match.group(2)
        
        # ایجاد المنت منطقی
        logical_elem = LogicalElement(
            element_id=elem_id,
            element_type=ElementType.IMAGE,
            content=ImageContent(
                src=filename,
                alt=filename.split('/')[-1].split('.')[0]  # نام فایل بدون مسیر و پسوند
            ),
            metadata=metadata
        )
        self._logical_elements.append(logical_elem)
        
        # ایجاد المنت سند
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.IMAGE
        )
        self._elements.append(doc_elem)
        
        if self._current_section:
            self._current_section.elements.append(doc_elem)
    
    def _finalize_paragraph(self, lines: List[str]) -> None:
        """پایان پاراگراف"""
        if not lines:
            return
        
        paragraph_text = ' '.join(lines).strip()
        if not paragraph_text:
            return
        
        elem_id = self._generate_id("paragraph")
        
        # ایجاد المنت منطقی
        logical_elem = LogicalElement(
            element_id=elem_id,
            element_type=ElementType.PARAGRAPH,
            content=ParagraphContent(
                text=RichTextContent(spans=[
                    RichTextSpan(text=paragraph_text)
                ])
            )
        )
        self._logical_elements.append(logical_elem)
        
        # ایجاد المنت سند
        doc_elem = DocumentElement(
            element_id=elem_id,
            element_type=ElementType.PARAGRAPH
        )
        self._elements.append(doc_elem)
        
        if self._current_section:
            self._current_section.elements.append(doc_elem)
