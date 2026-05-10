"""
پارسر HTML برای تبدیل فایل‌های HTML به مدل USDM
"""
from __future__ import annotations

import re
import uuid
from collections.abc import AsyncIterator
from html import entities
from html.parser import HTMLParser
from typing import Any

from ..models.base import BaseDocument
from ..models.base import ElementType
from ..models.exceptions import DocumentParseError
from ..models.media_detection import detect_by_extension
from ..models.usdm_models import CodeContent
from ..models.usdm_models import DocumentElement
from ..models.usdm_models import HeadingContent
from ..models.usdm_models import ImageContent
from ..models.usdm_models import ListContent
from ..models.usdm_models import ListItemContent
from ..models.usdm_models import LogicalElement
from ..models.usdm_models import ParagraphContent
from ..models.usdm_models import QuoteContent
from ..models.usdm_models import RichTextContent
from ..models.usdm_models import RichTextSpan
from ..models.usdm_models import Section
from ..models.usdm_models import TableCell
from ..models.usdm_models import TableContent
from ..models.usdm_models import TableRow
from ..models.usdm_models import USDMDocument
from .base import BaseDocumentParser
from .base import ParseOptions


class HTMLDocumentParser(HTMLParser):
    """پارسر HTML داخلی برای پردازش ساختار"""

    def __init__(self) -> None:
        super().__init__()
        self.current_element: dict[str, Any] | None = None
        self.element_stack: list[dict[str, Any]] = []
        self.sections: list[Section] = []
        self.elements: list[DocumentElement] = []
        self.logical_elements: list[LogicalElement] = []
        self.current_text: list[str] = []
        self.current_spans: list[RichTextSpan] = []
        self.current_style: dict[str, Any] = {}
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

    def _generate_id(self) -> str:
        """تولید شناسه یکتا برای المنت"""
        self.element_counter += 1
        return f"elem_{self.element_counter}"

    def _create_rich_text_span(self, text: str) -> RichTextSpan:
        """ایجاد یک RichTextSpan با استایل فعلی"""
        return RichTextSpan(
            text=text,
            character_style=self.current_style.get("character_style"),
            code=self.current_style.get("code", False),
            href=self.current_style.get("href"),
            math=self.current_style.get("math"),
            display_math=self.current_style.get("display_math", False)
        )

    def _flush_current_text(self) -> None:
        """ذخیره متن جاری به عنوان span"""
        if self.current_text:
            text = "".join(self.current_text).strip()
            if text:
                span = self._create_rich_text_span(text)
                self.current_spans.append(span)
            self.current_text = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """پردازش تگ شروع"""
        attrs_dict = dict(attrs)

        # ذخیره متن جاری قبل از تگ جدید
        self._flush_current_text()

        # پردازش بر اساس تگ
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self._handle_heading_start(tag, attrs_dict)
        elif tag == "p":
            self._handle_paragraph_start(attrs_dict)
        elif tag in ["pre", "code"]:
            self._handle_code_start(tag, attrs_dict)
        elif tag in ["ul", "ol"]:
            self._handle_list_start(tag, attrs_dict)
        elif tag == "li":
            self._handle_list_item_start(attrs_dict)
        elif tag in ["blockquote", "q"]:
            self._handle_quote_start(tag, attrs_dict)
        elif tag == "img":
            self._handle_image_start(attrs_dict)
        elif tag == "a":
            self._handle_link_start(attrs_dict)
        elif tag == "table":
            self._handle_table_start(attrs_dict)
        elif tag in ["tr", "thead", "tbody", "tfoot"]:
            self._handle_table_row_start(tag, attrs_dict)
        elif tag in ["td", "th"]:
            self._handle_table_cell_start(tag, attrs_dict)
        elif tag in ["b", "strong"]:
            self.current_style["character_style"] = "bold"
        elif tag in ["i", "em"]:
            self.current_style["character_style"] = "italic"
        elif tag in ["u", "ins"]:
            self.current_style["character_style"] = "underline"
        elif tag in ["s", "del", "strike"]:
            self.current_style["character_style"] = "strikethrough"
        elif tag == "br":
            self.current_text.append("\n")
        elif tag == "hr":
            self._handle_horizontal_rule()
        elif tag == "title":
            self.current_style["in_title"] = True
        elif tag == "div" and attrs_dict.get("class") == "math":
            self.in_math = True
            self.math_buffer = []
        elif tag == "span" and attrs_dict.get("class") == "math":
            self.in_math = True
            self.math_buffer = []
        elif tag == "script" and attrs_dict.get("type") == "math/tex":
            self.in_math = True
            self.math_buffer = []
        elif tag == "math":
            self.in_math = True
            self.math_buffer = []

        # ذخیره وضعیت فعلی در استک
        self.element_stack.append({
            "tag": tag,
            "attrs": attrs_dict,
            "style": self.current_style.copy()
        })

    def handle_endtag(self, tag: str) -> None:
        """پردازش تگ پایان"""
        # ذخیره متن جاری
        self._flush_current_text()

        # پردازش ریاضی
        if self.in_math and tag in ["div", "span", "script", "math"]:
            self.in_math = False
            if self.math_buffer:
                math_content = "".join(self.math_buffer).strip()
                if math_content:
                    span = RichTextSpan(
                        text="",
                        math=math_content,
                        display_math=tag == "div"  # div معمولاً نمایشی است
                    )
                    self.current_spans.append(span)
                self.math_buffer = []

        # پردازش بر اساس تگ
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self._handle_heading_end()
        elif tag == "p":
            self._handle_paragraph_end()
        elif tag in ["pre", "code"]:
            self._handle_code_end()
        elif tag in ["ul", "ol"]:
            self._handle_list_end()
        elif tag == "li":
            self._handle_list_item_end()
        elif tag in ["blockquote", "q"]:
            self._handle_quote_end()
        elif tag == "table":
            self._handle_table_end()
        elif tag in ["tr", "thead", "tbody", "tfoot"]:
            self._handle_table_row_end()
        elif tag in ["td", "th"]:
            self._handle_table_cell_end()
        elif tag in ["b", "strong", "i", "em", "u", "ins", "s", "del", "strike"]:
            self.current_style.pop("character_style", None)
        elif tag == "title":
            self.current_style.pop("in_title", None)

        # بازیابی وضعیت از استک
        if self.element_stack:
            self.element_stack.pop()
            if self.element_stack:
                self.current_style = self.element_stack[-1].get("style", {}).copy()
            else:
                self.current_style = {}

    def handle_data(self, data: str) -> None:
        """پردازش داده‌های متنی"""
        if self.in_math:
            self.math_buffer.append(data)
        elif self.current_style.get("in_title"):
            if self.document_title is None:
                self.document_title = data.strip()
            else:
                self.document_title += data.strip()
        elif self.in_code_block:
            self.current_text.append(data)
        else:
            # حذف فضاهای اضافی در متن عادی
            if self.current_text and not self.current_text[-1].endswith(' '):
                self.current_text.append(' ')
            self.current_text.append(data.strip())

    def handle_entityref(self, name: str) -> None:
        """پردازش entityهای HTML"""
        try:
            char = entities.html5.get(f"&{name};", f"&{name};")
            if char.startswith("&") and char.endswith(";"):
                # entity ناشناخته
                self.current_text.append(f"&{name};")
            else:
                self.current_text.append(char)
        except:
            self.current_text.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        """پردازش character referenceهای HTML"""
        try:
            if name.startswith('x'):
                char = chr(int(name[1:], 16))
            else:
                char = chr(int(name))
            self.current_text.append(char)
        except:
            self.current_text.append(f"&#{name};")

    def _handle_heading_start(self, tag: str, attrs: dict[str, Any]) -> None:
        """پردازش شروع هدینگ"""
        level = int(tag[1])  # h1 -> 1, h2 -> 2, etc.

        # ایجاد بخش جدید اگر هدینگ سطح 1-3 باشد
        if level <= 3:
            self.current_section = Section(
                section_id=f"section_{len(self.sections) + 1}",
                title=None,  # بعداً پر می‌شود
                elements=[],
                metadata={"html_tag": tag, **attrs}
            )
            self.sections.append(self.current_section)

        # ذخیره وضعیت هدینگ
        self.current_element = {
            "type": ElementType.HEADING,
            "level": level,
            "attrs": attrs
        }
    def _add_element(self, logical_elem: LogicalElement, caption: HeadingContent | None = None) -> None:
        self.logical_elements.append(logical_elem)
        doc_elem = DocumentElement(
            element_id=logical_elem.element_id,
            element_type=logical_elem.element_type,
            metadata=logical_elem.metadata
        )
        self.elements.append(doc_elem)
        if not self.current_section:
            # به یک بخش پیش‌فرض اضافه کن
            if not self.sections:
                default_section = Section(
                    section_id="section_default",
                    title=None,
                    elements=[],
                    metadata={"auto_generated": True}
                )
                self.sections.append(default_section)
                self.current_section = default_section

        if self.current_section:
            self.current_section.elements.append(doc_elem)
            # اگر عنوان بخش هنوز تنظیم نشده، از هدینگ استفاده کن
            if caption and self.current_section.title is None: #and self.current_element and self.current_element["level"] <= 3
                self.current_section.title = caption


    def _handle_heading_end(self) -> None:
        """پردازش پایان هدینگ"""
        if self.current_element and self.current_element.get("type") == ElementType.HEADING:
            if self.current_spans:
                content = HeadingContent(
                    text=RichTextContent(spans=self.current_spans.copy()),
                    level=self.current_element["level"]
                )

                element = LogicalElement(
                    element_id=self._generate_id(),
                    element_type=ElementType.HEADING,
                    content=content,
                    metadata=self.current_element.get("attrs", {})
                )

                self._add_element(element, content)

            self.current_spans = []
            self.current_element = None

    def _handle_paragraph_start(self, attrs: dict[str, Any]) -> None:
        """پردازش شروع پاراگراف"""
        self.current_element = {
            "type": ElementType.PARAGRAPH,
            "attrs": attrs
        }

    def _handle_paragraph_end(self) -> None:
        """پردازش پایان پاراگراف"""
        if self.current_element and self.current_element.get("type") == ElementType.PARAGRAPH:
            if self.current_spans:
                content = ParagraphContent(
                    text=RichTextContent(spans=self.current_spans.copy())
                )

                element = LogicalElement(
                    element_id=self._generate_id(),
                    element_type=ElementType.PARAGRAPH,
                    content=content,
                    metadata=self.current_element.get("attrs", {})
                )

                self._add_element(element)

            self.current_spans = []
            self.current_element = None

    def _handle_code_start(self, tag: str, attrs: dict[str, Any]) -> None:
        """پردازش شروع بلوک کد"""
        self.in_code_block = True
        self.current_element = {
            "type": ElementType.CODE,
            "tag": tag,
            "attrs": attrs,
            "language": attrs.get("class", "").replace("language-", "").split()[0] if attrs.get("class") else None
        }
        self.current_text = []  # ریست متن برای کد

    def _handle_code_end(self) -> None:
        """پردازش پایان بلوک کد"""
        if self.current_element and self.current_element.get("type") == ElementType.CODE:
            code_text = "".join(self.current_text).rstrip()
            if code_text:
                content = CodeContent(
                    code=code_text,
                    language=self.current_element.get("language")
                )

                element = LogicalElement(
                    element_id=self._generate_id(),
                    element_type=ElementType.CODE,
                    content=content,
                    metadata=self.current_element.get("attrs", {})
                )

                self._add_element(element)

            self.current_text = []
            self.current_element = None
            self.in_code_block = False

    def _handle_list_start(self, tag: str, attrs: dict[str, Any]) -> None:
        """پردازش شروع لیست"""
        list_info = {
            "type": ElementType.LIST,
            "tag": tag,
            "attrs": attrs,
            "ordered": tag == "ol",
            "items": [],
            "current_item": None
        }

        self.list_stack.append(list_info)
        self.current_list = list_info

    def _handle_list_end(self) -> None:
        """پردازش پایان لیست"""
        if self.list_stack:
            list_info = self.list_stack.pop()

            if list_info["items"]:
                content = ListContent(
                    items=list_info["items"],
                    ordered=list_info["ordered"]
                )

                element = LogicalElement(
                    element_id=self._generate_id(),
                    element_type=ElementType.LIST,
                    content=content,
                    metadata=list_info.get("attrs", {})
                )

                self._add_element(element)

            # بازیابی لیست قبلی از استک
            if self.list_stack:
                self.current_list = self.list_stack[-1]
            else:
                self.current_list = None

    def _handle_list_item_start(self, attrs: dict[str, Any]) -> None:
        """پردازش شروع آیتم لیست"""
        if self.current_list:
            self.current_list["current_item"] = {
                "elements": [],
                "attrs": attrs
            }

    def _handle_list_item_end(self) -> None:
        """پردازش پایان آیتم لیست"""
        if self.current_list and self.current_list["current_item"]:
            item_info = self.current_list["current_item"]

            if item_info["elements"]:
                # ایجاد یک المنت منطقی برای آیتم لیست
                item_content = ListItemContent(
                    elements=item_info["elements"]
                )

                item_element = LogicalElement(
                    element_id=self._generate_id(),
                    element_type=ElementType.LIST_ITEM,
                    content=item_content,
                    metadata=item_info.get("attrs", {})
                )

                # اضافه کردن آیتم به لیست
                self.current_list["items"].append(item_element)

            self.current_list["current_item"] = None

    def _handle_quote_start(self, tag: str, attrs: dict[str, Any]) -> None:
        """پردازش شروع نقل قول"""
        self.current_element = {
            "type": ElementType.QUOTE,
            "tag": tag,
            "attrs": attrs,
            "elements": []
        }

    def _handle_quote_end(self) -> None:
        """پردازش پایان نقل قول"""
        if self.current_element and self.current_element.get("type") == ElementType.QUOTE:
            if self.current_element["elements"]:
                content = QuoteContent(
                    elements=self.current_element["elements"]
                )

                element = LogicalElement(
                    element_id=self._generate_id(),
                    element_type=ElementType.QUOTE,
                    content=content,
                    metadata=self.current_element.get("attrs", {})
                )

                self._add_element(element)

            self.current_element = None

    def _handle_image_start(self, attrs: dict[str, Any]) -> None:
        """پردازش شروع تصویر"""
        src = attrs.get("src", "")
        alt = attrs.get("alt", "")

        if src:
            content = ImageContent(
                src=src,
                alt=alt,
                width=float(attrs.get("width", 0)) if attrs.get("width") else None,
                height=float(attrs.get("height", 0)) if attrs.get("height") else None,
                metadata={
                    "html_attrs": attrs,
                    "title": attrs.get("title")
                }
            )

            element = LogicalElement(
                element_id=self._generate_id(),
                element_type=ElementType.IMAGE,
                content=content,
                metadata=attrs
            )

            self._add_element(element)

    def _handle_link_start(self, attrs: dict[str, Any]) -> None:
        """پردازش شروع لینک"""
        href = attrs.get("href", "")
        if href:
            self.current_style["href"] = href

    def _handle_table_start(self, attrs: dict[str, Any]) -> None:
        """پردازش شروع جدول"""
        table_info: dict[str, Any] = {
            "type": ElementType.TABLE,
            "attrs": attrs,
            "rows": [],
            "current_row": None,
            "current_cell": None,
            "has_header": False,
            "caption": None
        }

        self.table_stack.append(table_info)
        self.current_table = table_info

    def _handle_table_row_start(self, tag: str, attrs: dict[str, Any]) -> None:
        """پردازش شروع سطر جدول"""
        if self.current_table:
            self.current_table["current_row"] = {
                "cells": [],
                "is_header": tag in ["thead", "th"],
                "attrs": attrs
            }

            if tag in ["thead", "th"]:
                self.current_table["has_header"] = True

    def _handle_table_row_end(self) -> None:
        """پردازش پایان سطر جدول"""
        if self.current_table and self.current_table["current_row"]:
            row_info = self.current_table["current_row"]

            if row_info["cells"]:
                table_row = TableRow(
                    cells=row_info["cells"],
                    is_header=row_info["is_header"],
                    metadata=row_info.get("attrs", {})
                )
                self.current_table["rows"].append(table_row)

            self.current_table["current_row"] = None

    def _handle_table_cell_start(self, tag: str, attrs: dict[str, Any]) -> None:
        """پردازش شروع سلول جدول"""
        if self.current_table and self.current_table["current_row"]:
            self.current_table["current_cell"] = {
                "elements": [],
                "is_header": tag == "th",
                "attrs": attrs,
                "col_span": int(attrs.get("colspan", 1)),
                "row_span": int(attrs.get("rowspan", 1))
            }

    def _handle_table_cell_end(self) -> None:
        """پردازش پایان سلول جدول"""
        if (self.current_table and self.current_table["current_row"] and
            self.current_table["current_cell"]):

            cell_info = self.current_table["current_cell"]

            # ایجاد سلول جدول
            table_cell = TableCell(
                content=cell_info["elements"],
                is_header=cell_info["is_header"],
                col_span=cell_info["col_span"],
                row_span=cell_info["row_span"],
                metadata=cell_info.get("attrs", {})
            )

            self.current_table["current_row"]["cells"].append(table_cell)
            self.current_table["current_cell"] = None

    def _handle_table_end(self) -> None:
        """پردازش پایان جدول"""
        if self.table_stack:
            table_info = self.table_stack.pop()

            if table_info["rows"]:
                content = TableContent(
                    rows=table_info["rows"],
                    caption=table_info.get("caption"),
                    metadata={
                        "has_header": table_info["has_header"],
                        **table_info.get("attrs", {})
                    }
                )

                element = LogicalElement(
                    element_id=self._generate_id(),
                    element_type=ElementType.TABLE,
                    content=content,
                    metadata=table_info.get("attrs", {})
                )

                self._add_element(element)

            # بازیابی جدول قبلی از استک
            if self.table_stack:
                self.current_table = self.table_stack[-1]
            else:
                self.current_table = None

    def _handle_horizontal_rule(self) -> None:
        """پردازش خط افقی (HR)"""
        # در HTML، HR معمولاً به عنوان یک المنت جداکننده در نظر گرفته می‌شود
        # در USDM می‌توانیم آن را به عنوان یک پاراگراف خاص در نظر بگیریم
        content = ParagraphContent(
            text=RichTextContent(spans=[RichTextSpan(text="---")])
        )

        element = LogicalElement(
            element_id=self._generate_id(),
            element_type=ElementType.PARAGRAPH,
            content=content,
            metadata={"html_tag": "hr", "is_horizontal_rule": True}
        )

        self._add_element(element)


class HtmlParser(BaseDocumentParser):
    """پارسر HTML برای تبدیل HTML به USDM"""

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str,
                         metadata: dict[str, Any] | None = None,
                         options: ParseOptions | None = None) -> BaseDocument:
        try:
            encoding = "utf-8"
            if options and options.encoding:
                encoding=options.encoding
            html_content = data.decode(encoding)
            return await self.parse_text(html_content, document_id, source_name, metadata, options)
        except Exception as e:
            raise DocumentParseError(f"خطا در تجزیه HTML: {e}")

    async def parse_text(self, html_content: str, document_id: str, source_name: str,
                         metadata: dict[str, Any] | None = None,
                         options: ParseOptions | None = None) -> BaseDocument:
        try:
            parser = HTMLDocumentParser()
            parser.feed(html_content)

            # ایجاد سند USDM
            merged_metadata={
                "source_format": "html",
                "parser": "HtmlParser",
            }
            if options:
                merged_metadata["encoding"] = options.encoding
            if metadata:
                merged_metadata.update(metadata)
            # ایجاد سند USDM
            if document_id == "":
                document_id = str(uuid.uuid4())
            if parser.document_title:
                source_name=parser.document_title
            if not source_name or source_name == "":
                source_name="Untitled HTML Document"
            mt=detect_by_extension("html")
            document = USDMDocument(
                document_id=document_id,
                title=source_name,
                media_type=mt,
                sections=parser.sections,
                elements=parser.elements,
                logical_elements=parser.logical_elements,  # در این پیاده‌سازی منطقی و المنت‌ها یکی هستند
                metadata=merged_metadata
            )

            return document
        except Exception as e:
            raise DocumentParseError(f"خطا در تجزیه HTML: {e}")

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str = "", source_name: str = "", metadata: dict[str, Any] | None = None, options: ParseOptions | None = None) -> BaseDocument:
        """
        تجزیه HTML از استریم
        """
        try:
            # جمع‌آوری تمام داده‌ها از استریم
            chunks = []
            async for chunk in stream:
                chunks.append(chunk)
            encoding = "utf-8"
            if options and options.encoding:
                encoding=options.encoding
            html_content = b"".join(chunks).decode(encoding)
            return await self.parse_text(html_content, document_id, source_name, metadata, options)

        except Exception as e:
            raise DocumentParseError(f"خطا در تجزیه استریم HTML: {e}")

    def get_supported_media_types(self) -> list[str]:
        """دریافت انواع رسانه پشتیبانی شده"""
        return ["text/html", "application/xhtml+xml"]

    def get_supported_extensions(self) -> list[str]:
        """دریافت پسوندهای پشتیبانی شده"""
        return [".html", ".htm", ".xhtml"]

    def _extract_math_from_html(self, html_content: str) -> list[dict[str, Any]]:
        """استخراج محتوای ریاضی از HTML"""
        math_elements = []

        # جستجوی MathML
        mathml_pattern = r'<math[^>]*>(.*?)</math>'
        for match in re.finditer(mathml_pattern, html_content, re.DOTALL | re.IGNORECASE):
            math_content = match.group(1).strip()
            if math_content:
                math_elements.append({
                    "content": math_content,
                    "format": "mathml",
                    "display_mode": True
                })

        # جستجوی MathJax/KaTeX
        mathjax_patterns = [
            r'<script[^>]*type="math/tex"[^>]*>(.*?)</script>',
            r'<script[^>]*type="math/tex; mode=display"[^>]*>(.*?)</script>',
            r'\\\[(.*?)\\\]',
            r'\\\((.*?)\\\)',
            r'\$\$(.*?)\$\$',
            r'\$(.*?)\$'
        ]

        for pattern in mathjax_patterns:
            for match in re.finditer(pattern, html_content, re.DOTALL):
                math_content = match.group(1).strip()
                if math_content:
                    display_mode = "display" in pattern or "\\[" in pattern or "$$" in pattern
                    math_elements.append({
                        "content": math_content,
                        "format": "latex",
                        "display_mode": display_mode
                    })

        return math_elements
