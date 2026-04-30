"""
رایتر مارک‌داون برای تبدیل مدل USDM به فایل .md
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, AsyncIterator
import re

from .base import BaseDocumentWriter, WriteOptions
from ..models.base import BaseDocument
from ..models.usdm_models import (
    USDMDocument,
    DocumentElement,
    LogicalElement,
    RichTextSpan,
    RichTextContent,
    ParagraphContent,
    HeadingContent,
    CodeContent,
    ListContent,
    ListItemContent,
    TableContent,
    TableCell,
    QuoteContent,
    ImageContent,
    LinkContent,
    ElementType,
)
from ..models.exceptions import DocumentWriteError


class MarkdownWriter(BaseDocumentWriter):
    """رایتر مارک‌داون"""
    
    def __init__(self, options: Optional[WriteOptions] = None):
        super().__init__(options)
        self.options = options or WriteOptions()
    
    async def write(self, document: BaseDocument) -> bytes:
        """
        تبدیل سند به مارک‌داون (بایت)
        """
        assert self.options is not None, "WriteOptions not initialized"
        if not isinstance(document, USDMDocument):
            raise DocumentWriteError("سند باید از نوع USDMDocument باشد")
        
        try:
            markdown_text = self._convert_usdm_to_markdown(document)
            return markdown_text.encode(self.options.encoding)
            
        except Exception as e:
            raise DocumentWriteError(f"خطا در نوشتن مارک‌داون: {e}")
    
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """
        نوشتن به صورت استریم
        """
        try:
            data = await self.write(document)
            yield data
            
        except Exception as e:
            raise DocumentWriteError(f"خطا در نوشتن استریم مارک‌داون: {e}")
    
    async def write_to_file(self, document: BaseDocument, target: Path,
                           options: Optional[Dict[str, Any]] = None) -> None:
        """
        نوشتن سند به فایل
        """
        try:
            data = await self.write(document)
            target.write_bytes(data)
            
        except Exception as e:
            raise DocumentWriteError(f"خطا در نوشتن فایل مارک‌داون: {e}")
    
    def get_supported_media_types(self) -> list[str]:
        """دریافت انواع رسانه پشتیبانی شده"""
        return ["text/markdown"]
    
    def get_supported_extensions(self) -> list[str]:
        """دریافت پسوندهای پشتیبانی شده"""
        return [".md", ".markdown"]
    
    def _convert_usdm_to_markdown(self, document: USDMDocument) -> str:
        """تبدیل USDM به متن مارک‌داون"""
        lines = []
        
        # افزودن عنوان
        if document.title:
            lines.append(f"# {document.title}\n")
        
        # پردازش بخش‌ها
        for section in document.sections:
            if section.title:
                # افزودن عنوان بخش
                heading_level = section.title.level
                heading_text = self._rich_text_to_plain(section.title.text)
                heading_prefix = "#" * min(heading_level, 6)
                lines.append(f"{heading_prefix} {heading_text}\n")
            
            # پردازش المنت‌های بخش
            for elem in section.elements:
                logical_elem = self._find_logical_element(document, elem.element_id)
                if logical_elem:
                    lines.append(self._element_to_markdown(logical_elem))
        
        # پردازش المنت‌های مستقل
        for elem in document.elements:
            if not any(elem.element_id in [se.element_id for se in s.elements] for s in document.sections):
                logical_elem = self._find_logical_element(document, elem.element_id)
                if logical_elem:
                    lines.append(self._element_to_markdown(logical_elem))
        
        return "\n".join(lines)
    
    def _find_logical_element(self, document: USDMDocument, element_id: str) -> Optional[LogicalElement]:
        """یافتن المنت منطقی بر اساس شناسه"""
        for elem in document.logical_elements:
            if elem.element_id == element_id:
                return elem
        return None
    
    def _element_to_markdown(self, element: LogicalElement) -> str:
        """تبدیل المنت منطقی به مارک‌داون"""
        content = element.content
        
        if element.element_type == ElementType.PARAGRAPH and isinstance(content, ParagraphContent):
            return self._paragraph_to_markdown(content) + "\n"
        
        elif element.element_type == ElementType.HEADING and isinstance(content, HeadingContent):
            return self._heading_to_markdown(content) + "\n"
        
        elif element.element_type == ElementType.CODE and isinstance(content, CodeContent):
            return self._code_to_markdown(content) + "\n"
        
        elif element.element_type == ElementType.LIST and isinstance(content, ListContent):
            return self._list_to_markdown(content) + "\n"
        
        elif element.element_type == ElementType.QUOTE and isinstance(content, QuoteContent):
            return self._quote_to_markdown(content) + "\n"
        
        elif element.element_type == ElementType.IMAGE and isinstance(content, ImageContent):
            return self._image_to_markdown(content) + "\n"
        
        elif element.element_type == ElementType.LINK and isinstance(content, LinkContent):
            return self._link_to_markdown(content) + "\n"
        
        elif element.element_type == ElementType.TABLE and isinstance(content, TableContent):
            return self._table_to_markdown(content) + "\n"
        
        return ""
    
    def _rich_text_to_plain(self, rich_text: RichTextContent) -> str:
        """تبدیل RichText به متن ساده با فرمت‌بندی مارک‌داون"""
        result = []
        for span in rich_text.spans:
            text = span.text
            
            # اعمال فرمت‌بندی
            if span.code:
                text = f"`{text}`"
            elif span.math:
                text = f"$${span.math}$$"
            
            # اعمال استایل‌های متنی
            if span.character_style:
                if "bold" in span.character_style.lower():
                    text = f"**{text}**"
                elif "italic" in span.character_style.lower():
                    text = f"*{text}*"
                elif "underline" in span.character_style.lower():
                    text = f"<u>{text}</u>"
            
            # افزودن لینک
            if span.href:
                text = f"[{text}]({span.href})"
            
            result.append(text)
        
        return "".join(result)
    
    def _paragraph_to_markdown(self, content: ParagraphContent) -> str:
        """تبدیل پاراگراف به مارک‌داون"""
        return self._rich_text_to_plain(content.text)
    
    def _heading_to_markdown(self, content: HeadingContent) -> str:
        """تبدیل هدینگ به مارک‌داون"""
        heading_text = self._rich_text_to_plain(content.text)
        heading_prefix = "#" * min(content.level, 6)
        return f"{heading_prefix} {heading_text}"
    
    def _code_to_markdown(self, content: CodeContent) -> str:
        """تبدیل کد به مارک‌داون"""
        assert self.options is not None, "WriteOptions not initialized"        
        language = content.language or ""
        if self.options.code_block_style == "~~~":
            return f"~~~{language}\n{content.code}\n~~~"
        else:
            return f"```{language}\n{content.code}\n```"
    
    def _list_to_markdown(self, content: ListContent) -> str:
        """تبدیل لیست به مارک‌داون"""
        assert self.options is not None, "WriteOptions not initialized"
        lines = []
        bullet = self.options.bullet_style
        
        for i, item in enumerate(content.items):
            prefix = f"{i + 1}. " if content.ordered else f"{bullet} "
            
            # پردازش آیتم‌های لیست
            for sub_elem in item.elements:
                if isinstance(sub_elem, LogicalElement):
                    if sub_elem.element_type == ElementType.PARAGRAPH:
                        para_content = sub_elem.content
                        if isinstance(para_content, ParagraphContent):
                            text = self._rich_text_to_plain(para_content.text)
                            lines.append(f"{prefix}{text}")
                    else:
                        # برای سایر انواع المنت‌ها
                        elem_md = self._element_to_markdown(sub_elem).strip()
                        lines.append(f"{prefix}{elem_md}")
            
            # افزودن خط خالی بین آیتم‌ها
            lines.append("")
        
        return "\n".join(lines)
    
    def _quote_to_markdown(self, content: QuoteContent) -> str:
        """تبدیل نقل قول به مارک‌داون"""
        lines = []
        for elem in content.elements:
            if isinstance(elem, LogicalElement):
                elem_md = self._element_to_markdown(elem).strip()
                # افزودن > به ابتدای هر خط
                for line in elem_md.split('\n'):
                    lines.append(f"> {line}")
        
        return "\n".join(lines)
    
    def _image_to_markdown(self, content: ImageContent) -> str:
        """تبدیل تصویر به مارک‌داون"""
        alt = content.alt or ""
        return f"![{alt}]({content.src})"
    
    def _link_to_markdown(self, content: LinkContent) -> str:
        """تبدیل لینک به مارک‌داون"""
        link_text = self._rich_text_to_plain(content.text)
        return f"[{link_text}]({content.url})"
    
    def _table_to_markdown(self, content: TableContent) -> str:
        """تبدیل جدول به مارک‌داون"""
        if not content.rows:
            return ""
        
        lines = []
        
        # سطر هدر (فرضی)
        if content.rows:
            header_cells = []
            for cell in content.rows[0].cells:
                cell_text = self._cell_content_to_text(cell)
                header_cells.append(cell_text)
            
            lines.append("| " + " | ".join(header_cells) + " |")
            lines.append("|" + "|".join(["---"] * len(header_cells)) + "|")
        
        # سطرهای داده
        for row in content.rows[1:] if len(content.rows) > 1 else content.rows:
            row_cells = []
            for cell in row.cells:
                cell_text = self._cell_content_to_text(cell)
                row_cells.append(cell_text)
            
            lines.append("| " + " | ".join(row_cells) + " |")
        
        return "\n".join(lines)
    
    def _cell_content_to_text(self, cell: TableCell) -> str:
        """تبدیل محتوای سلول جدول به متن"""
        texts = []
        for elem in cell.content:
            if isinstance(elem, LogicalElement):
                if elem.element_type == ElementType.PARAGRAPH:
                    para_content = elem.content
                    if isinstance(para_content, ParagraphContent):
                        texts.append(self._rich_text_to_plain(para_content.text))
        
        return " ".join(texts)
