"""
Markdown parser for converting .md files to USDM model
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

from ..models.base import ElementType
from ..models.exceptions import DocumentParseError
from ..models.media_types import MEDIA_TYPES
from ..models.usdm_models import CharacterStyle
from ..models.usdm_models import CodeContent
from ..models.usdm_models import DocumentElement
from ..models.usdm_models import HeadingContent
from ..models.usdm_models import ImageContent
from ..models.usdm_models import LinkContent
from ..models.usdm_models import ListContent
from ..models.usdm_models import ListItemContent
from ..models.usdm_models import LogicalElement
from ..models.usdm_models import ParagraphContent
from ..models.usdm_models import ParagraphStyle
from ..models.usdm_models import QuoteContent
from ..models.usdm_models import RichTextContent
from ..models.usdm_models import RichTextSpan
from ..models.usdm_models import Section
from ..models.usdm_models import StyleSheet
from ..models.usdm_models import USDMDocument
from .base import BaseDocumentParser
from .base import ParseOptions


class MarkdownTreeProcessor(Treeprocessor):
    """HTML tree processor for semantic structure extraction"""

    def __init__(self, md):
        super().__init__(md)
        self.sections = []
        self.current_section = None
        self.elements = []
        self.logical_elements = []
        self.element_counter = 0

    def run(self, root):
        """پردازش درخت HTML"""
        self._process_node(root, level=0)
        return root

    def _generate_id(self, prefix="elem"):
        """تولید شناسه یکتا"""
        self.element_counter += 1
        return f"{prefix}_{self.element_counter}"

    def _process_node(self, node, level=0):
        """پردازش بازگشتی گره‌های HTML"""
        tag = node.tag.lower() if hasattr(node, 'tag') else None

        # ایجاد بخش جدید برای هدینگ‌ها
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            heading_level = int(tag[1])
            heading_text = self._extract_text(node)

            # ایجاد بخش جدید
            self.current_section = Section(
                title=HeadingContent(
                    level=heading_level,
                    text=RichTextContent(spans=[
                        RichTextSpan(text=heading_text)
                    ])
                ),
                section_type="section"
            )
            self.sections.append(self.current_section)

            # ایجاد المنت منطقی
            elem_id = self._generate_id("heading")
            logical_elem = LogicalElement(
                element_id=elem_id,
                element_type=ElementType.HEADING,
                content=HeadingContent(
                    level=heading_level,
                    text=RichTextContent(spans=[
                        RichTextSpan(text=heading_text)
                    ])
                ),
                metadata={"level": heading_level}
            )
            self.logical_elements.append(logical_elem)

            # ایجاد المنت سند
            doc_elem = DocumentElement(
                element_id=elem_id,
                element_type=ElementType.HEADING,
                metadata={"level": heading_level}
            )
            self.elements.append(doc_elem)

            if self.current_section:
                self.current_section.elements.append(doc_elem)

        # پردازش پاراگراف
        elif tag == 'p':
            paragraph_text = self._extract_text(node)
            if paragraph_text.strip():
                elem_id = self._generate_id("para")

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
                self.logical_elements.append(logical_elem)

                # ایجاد المنت سند
                doc_elem = DocumentElement(
                    element_id=elem_id,
                    element_type=ElementType.PARAGRAPH
                )
                self.elements.append(doc_elem)

                if self.current_section:
                    self.current_section.elements.append(doc_elem)

        # پردازش لیست
        elif tag in ['ul', 'ol']:
            self._process_list(node, tag == 'ol')

        # پردازش کد
        elif tag in ['pre', 'code']:
            self._process_code(node)

        # پردازش نقل قول
        elif tag == 'blockquote':
            self._process_quote(node)

        # پردازش تصویر
        elif tag == 'img':
            self._process_image(node)

        # پردازش لینک
        elif tag == 'a':
            self._process_link(node)

        # پردازش بازگشتی فرزندان
        for child in node:
            self._process_node(child, level + 1)

    def _extract_text(self, node):
        """استخراج متن از گره"""
        text_parts = []
        if node.text:
            text_parts.append(node.text.strip())
        for child in node:
            text_parts.append(self._extract_text(child))
        if node.tail:
            text_parts.append(node.tail.strip())
        return ' '.join(filter(None, text_parts))

    def _process_list(self, node, ordered=False):
        """پردازش لیست"""
        elem_id = self._generate_id("list")
        items = []

        for li in node.findall('.//li'):
            item_text = self._extract_text(li)
            if item_text.strip():
                # ایجاد آیتم لیست
                list_item_elem = LogicalElement(
                    element_id=self._generate_id("list_item"),
                    element_type=ElementType.LIST_ITEM,
                    content=ListItemContent(
                        elements=[
                            LogicalElement(
                                element_id=self._generate_id("para"),
                                element_type=ElementType.PARAGRAPH,
                                content=ParagraphContent(
                                    text=RichTextContent(spans=[
                                        RichTextSpan(text=item_text)
                                    ])
                                )
                            )
                        ]
                    )
                )
                self.logical_elements.append(list_item_elem)
                items.append(ListItemContent(elements=[list_item_elem]))

        if items:
            # ایجاد المنت منطقی لیست
            logical_elem = LogicalElement(
                element_id=elem_id,
                element_type=ElementType.LIST,
                content=ListContent(ordered=ordered, items=items)
            )
            self.logical_elements.append(logical_elem)

            # ایجاد المنت سند
            doc_elem = DocumentElement(
                element_id=elem_id,
                element_type=ElementType.LIST
            )
            self.elements.append(doc_elem)

            if self.current_section:
                self.current_section.elements.append(doc_elem)

    def _process_code(self, node):
        """پردازش بلوک کد"""
        code_text = node.text or ""
        if hasattr(node, 'tag') and node.tag == 'pre':
            # بلوک کد
            code_elem = node.find('code')
            if code_elem is not None:
                code_text = code_elem.text or ""
                language = code_elem.get('class', '').replace('language-', '') if code_elem.get('class') else None
        else:
            # کد درون خطی
            language = None

        if code_text.strip():
            elem_id = self._generate_id("code")

            # ایجاد المنت منطقی
            logical_elem = LogicalElement(
                element_id=elem_id,
                element_type=ElementType.CODE,
                content=CodeContent(code=code_text, language=language)
            )
            self.logical_elements.append(logical_elem)

            # ایجاد المنت سند
            doc_elem = DocumentElement(
                element_id=elem_id,
                element_type=ElementType.CODE
            )
            self.elements.append(doc_elem)

            if self.current_section:
                self.current_section.elements.append(doc_elem)

    def _process_quote(self, node):
        """پردازش نقل قول"""
        quote_text = self._extract_text(node)
        if quote_text.strip():
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
                                    RichTextSpan(text=quote_text)
                                ])
                            )
                        )
                    ]
                )
            )
            self.logical_elements.append(logical_elem)

            # ایجاد المنت سند
            doc_elem = DocumentElement(
                element_id=elem_id,
                element_type=ElementType.QUOTE
            )
            self.elements.append(doc_elem)

            if self.current_section:
                self.current_section.elements.append(doc_elem)

    def _process_image(self, node):
        """پردازش تصویر"""
        src = node.get('src', '')
        alt = node.get('alt', '')

        if src:
            elem_id = self._generate_id("img")

            # ایجاد المنت منطقی
            logical_elem = LogicalElement(
                element_id=elem_id,
                element_type=ElementType.IMAGE,
                content=ImageContent(src=src, alt=alt)
            )
            self.logical_elements.append(logical_elem)

            # ایجاد المنت سند
            doc_elem = DocumentElement(
                element_id=elem_id,
                element_type=ElementType.IMAGE
            )
            self.elements.append(doc_elem)

            if self.current_section:
                self.current_section.elements.append(doc_elem)

    def _process_link(self, node):
        """پردازش لینک"""
        href = node.get('href', '')
        link_text = self._extract_text(node)

        if href:
            elem_id = self._generate_id("link")

            # ایجاد المنت منطقی
            logical_elem = LogicalElement(
                element_id=elem_id,
                element_type=ElementType.LINK,
                content=LinkContent(
                    url=href,
                    text=RichTextContent(spans=[
                        RichTextSpan(text=link_text)
                    ])
                )
            )
            self.logical_elements.append(logical_elem)

            # ایجاد المنت سند
            doc_elem = DocumentElement(
                element_id=elem_id,
                element_type=ElementType.LINK
            )
            self.elements.append(doc_elem)

            if self.current_section:
                self.current_section.elements.append(doc_elem)


class MarkdownExtension(Extension):
    """اکستنشن markdown برای پردازش ساختاری"""

    def extendMarkdown(self, md):
        processor = MarkdownTreeProcessor(md)
        md.treeprocessors.register(processor, 'usdm_processor', 20)


class MarkdownParser(BaseDocumentParser):
    """پارسر مارک‌داون"""

    name: str = "markdown"
    supported_extensions: tuple[str, ...] = (".md", ".markdown")

    def __init__(self):
        super().__init__()
        self.md = markdown.Markdown(extensions=[MarkdownExtension()])

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str,
                         metadata: dict[str, Any] | None = None,
                         options: ParseOptions | None = None) -> USDMDocument:
        """
        پارس کردن داده‌های بایت مارک‌داون
        """
        try:
            # تنظیمات پیش‌فرض
            opts = options or ParseOptions()

            # تبدیل بایت به متن
            text = data.decode(opts.encoding, errors='replace')

            # پردازش مارک‌داون
            self.md.reset()
            self.md.convert(text)

            # استخراج ساختار از پردازنده
            processor = self.md.treeprocessors['usdm_processor']

            # ایجاد استایل‌شیت پایه
            stylesheet = StyleSheet(
                character_styles={
                    "code": CharacterStyle(name="code", font="monospace"),
                    "emphasis": CharacterStyle(name="emphasis", italic=True),
                    "strong": CharacterStyle(name="strong", bold=True)
                },
                paragraph_styles={
                    "normal": ParagraphStyle(name="normal"),
                    "heading1": ParagraphStyle(name="heading1", spacing_after=12.0),
                    "heading2": ParagraphStyle(name="heading2", spacing_after=10.0),
                    "heading3": ParagraphStyle(name="heading3", spacing_after=8.0)
                }
            )

            # ایجاد سند USDM
            usdm_doc = USDMDocument(
                document_id=document_id,
                title=source_name.replace('.md', '').replace('.markdown', ''),
                media_type=MEDIA_TYPES["markdown"],
                file_extension=".md",
                sections=processor.sections,
                elements=processor.elements,
                logical_elements=processor.logical_elements,
                stylesheet=stylesheet,
                pages=[],  # مارک‌داون صفحه‌بندی ندارد
                metadata=metadata or {},
                raw_text=text
            )

            return usdm_doc

        except Exception as e:
            raise DocumentParseError(f"خطا در پارس کردن مارک‌داون: {e}")

    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str,
                          source_name: str, metadata: dict[str, Any] | None = None,
                          options: ParseOptions | None = None) -> USDMDocument:
        """
        پارس کردن از استریم
        """
        try:
            # جمع‌آوری تمام داده‌های استریم
            data_chunks = []
            async for chunk in stream:
                data_chunks.append(chunk)

            data = b''.join(data_chunks)
            return await self.parse_bytes(data, document_id, source_name, metadata, options)

        except Exception as e:
            raise DocumentParseError(f"خطا در پارس کردن استریم مارک‌داون: {e}")
