    #                 item_content_lines.append(elem_html.strip())
    #         elif isinstance(elem, str):
    #             item_content_lines.append(self._escape_html(elem))
        
    #     # ترکیب محتوای آیتم
    #     item_content = " ".join(item_content_lines)
        
    #     # افزودن ویژگی‌ها
    #     attrs = ""
    #     if content.metadata:
    #         if content.metadata.get("value"):
    #             attrs += f' value="{content.metadata.get("value")}"'
    #         if content.metadata.get("class"):
    #             attrs += f' class="{content.metadata.get("class")}"'
        
    #     lines.append(f'    <li{attrs}>{item_content}</li>')
        
    #     return "\n".join(lines)
    
    # def _quote_to_html(self, content: QuoteContent) -> str:
    #     """تبدیل نقل قول به HTML"""
    #     if not content or not content.elements:
    #         return ""
        
    #     lines: List[str] = []
    #     lines.append('  <blockquote>')
        
    #     # پردازش المنت‌ها
    #     for elem in content.elements:
    #         if isinstance(elem, LogicalElement):
    #             elem_html = self._element_to_html(elem)
    #             if elem_html:
    #                 lines.append(elem_html)
    #         elif isinstance(elem, str):
    #             escaped_text = self._escape_html(elem)
    #             lines.append(f'    <p>{escaped_text}</p>')
        
    #     # افزودن منبع اگر وجود دارد
    #     if content.source:
    #         source_escaped = self._escape_html(content.source)
    #         lines.append(f'    <footer>— {source_escaped}</footer>')
        
    #     lines.append('  </blockquote>')
        
    #     return "\n".join(lines)
    
    # def _image_to_html(self, content: ImageContent) -> str:
    #     """تبدیل تصویر به HTML"""
    #     if not content or not content.src:
    #         return ""
        
    #     src_escaped = self._escape_html(content.src)
    #     alt_escaped = self._escape_html(content.alt) if content.alt else ""
        
    #     # ساخت ویژگی‌های HTML
    #     attrs = f'src="{src_escaped}" alt="{alt_escaped}"'
        
    #     if content.width:
    #         attrs += f' width="{content.width}"'
    #     if content.height:
    #         attrs += f' height="{content.height}"'
        
    #     if content.metadata:
    #         if content.metadata.get("title"):
    #             title_escaped = self._escape_html(content.metadata.get("title", ""))
    #             attrs += f' title="{title_escaped}"'
    #         if content.metadata.get("class"):
    #             class_escaped = self._escape_html(content.metadata.get("class", ""))
    #             attrs += f' class="{class_escaped}"'
    #         if content.metadata.get("style"):
    #             style_escaped = self._escape_html(content.metadata.get("style", ""))
    #             attrs += f' style="{style_escaped}"'
        
    #     # بررسی برای قرار دادن در figure
    #     if content.caption or (content.metadata and content.metadata.get("use_figure")):
    #         lines: List[str] = []
    #         lines.append('  <figure>')
    #         lines.append(f'    <img {attrs}>')
            
    #         if content.caption:
    #             caption_escaped = self._escape_html(content.caption)
    #             lines.append(f'    <figcaption>{caption_escaped}</figcaption>')
            
    #         lines.append('  </figure>')
    #         return "\n".join(lines)
    #     else:
    #         return f'  <img {attrs}>'
    
    # def _link_to_html(self, content: LinkContent) -> str:
    #     """تبدیل لینک به HTML"""
    #     if not content or not content.href:
    #         return ""
        
    #     href_escaped = self._escape_html(content.href)
    #     text_escaped = self._escape_html(content.text) if content.text else href_escaped
        
    #     # ساخت ویژگی‌های HTML
    #     attrs = f'href="{href_escaped}"'
        
    #     if content.title:
    #         title_escaped = self._escape_html(content.title)
    #         attrs += f' title="{title_escaped}"'
        
    #     if content.target:
    #         target_escaped = self._escape_html(content.target)
    #         attrs += f' target="{target_escaped}"'
        
    #     if content.metadata:
    #         if content.metadata.get("rel"):
    #             rel_escaped = self._escape_html(content.metadata.get("rel", ""))
    #             attrs += f' rel="{rel_escaped}"'
    #         if content.metadata.get("class"):
    #             class_escaped = self._escape_html(content.metadata.get("class", ""))
    #             attrs += f' class="{class_escaped}"'
        
    #     return f'  <a {attrs}>{text_escaped}</a>'
    
    # def _math_to_html(self, content: MathContent) -> str:
    #     """تبدیل محتوای ریاضی به HTML"""
    #     if not content or not content.content:
    #         return ""
        
    #     math_content = content.content.strip()
    #     if not math_content:
    #         return ""
        
    #     escaped_content = self._escape_html(math_content)
        
    #     # تعیین حالت نمایش
    #     if content.display_mode:
    #         return f'  <div class="math math-display">$${escaped_content}$$</div>'
    #     else:
    #         return f'  <span class="math math-inline">${escaped_content}$</span>'
    
    # def _table_to_html(self, content: TableContent) -> str:
    #     """تبدیل جدول به HTML"""
    #     if not content or not content.rows:
    #         return ""
        
    #     lines: List[str] = []
        
    #     # شروع جدول
    #     table_attrs = ""
    #     if content.metadata:
    #         if content.metadata.get("class"):
    #             class_escaped = self._escape_html(content.metadata.get("class", ""))
    #             table_attrs += f' class="{class_escaped}"'
    #         if content.metadata.get("style"):
    #             style_escaped = self._escape_html(content.metadata.get("style", ""))
    #             table_attrs += f' style="{style_escaped}"'
        
    #     lines.append(f'  <table{table_attrs}>')
        
    #     # افزودن caption اگر وجود دارد
    #     if content.caption:
    #         caption_escaped = self._escape_html(content.caption)
    #         lines.append(f'    <caption>{caption_escaped}</caption>')
        
    #     # پردازش سطرها
    #     in_header = False
    #     in_body = False
    #     in_footer = False
        
    #     for row in content.rows:
    #         # تعیین بخش جدول
    #         if row.is_header and not in_header:
    #             lines.append('    <thead>')
    #             in_header = True
    #         elif not row.is_header and not in_body and not in_footer:
    #             if in_header:
    #                 lines.append('    </thead>')
    #                 in_header = False
    #             lines.append('    <tbody>')
    #             in_body = True
            
    #         # پردازش سطر
    #         row_html = self._table_row_to_html(row)
    #         if row_html:
    #             lines.append(row_html)
        
    #     # بستن بخش‌ها
    #     if in_header:
    #         lines.append('    </thead>')
    #     if in_body:
    #         lines.append('    </tbody>')
    #     if in_footer:
    #         lines.append('    </tfoot>')
        
    #     lines.append('  </table>')
        
    #     return "\n".join(lines)
    
    # def _table_row_to_html(self, row: TableRow) -> str:
    #     """تبدیل سطر جدول به HTML"""
    #     if not row or not row.cells:
    #         return ""
        
    #     lines: List[str] = []
        
    #     # ویژگی‌های سطر
    #     row_attrs = ""
    #     if row.metadata:
    #         if row.metadata.get("class"):
    #             class_escaped = self._escape_html(row.metadata.get("class", ""))
    #             row_attrs += f' class="{class_escaped}"'
    #         if row.metadata.get("style"):
    #             style_escaped = self._escape_html(row.metadata.get("style", ""))
    #             row_attrs += f' style="{style_escaped}"'
        
    #     lines.append(f'      <tr{row_attrs}>')
        
    #     # پردازش سلول‌ها
    #     for cell in row.cells:
    #         cell_html = self._table_cell_to_html(cell, row.is_header)
    #         if cell_html:
    #             lines.append(cell_html)
        
    #     lines.append('      </tr>')
        
    #     return "\n".join(lines)
    
    # def _table_cell_to_html(self, cell: TableCell, is_header_row: bool = False) -> str:
    #     """تبدیل سلول جدول به HTML"""
    #     if not cell:
    #         return ""
        
    #     # تعیین تگ سلول
    #     tag = "th" if (cell.is_header or is_header_row) else "td"
        
    #     # ویژگی‌های سلول
    #     attrs = ""
    #     if cell.colspan and cell.colspan > 1:
    #         attrs += f' colspan="{cell.colspan}"'
    #     if cell.rowspan and cell.rowspan > 1:
    #         attrs += f' rowspan="{cell.rowspan}"'
        
    #     if cell.metadata:
    #         if cell.metadata.get("class"):
    #             class_escaped = self._escape_html(cell.metadata.get("class", ""))
    #             attrs += f' class="{class_escaped}"'
    #         if cell.metadata.get("style"):
    #             style_escaped = self._escape_html(cell.metadata.get("style", ""))
    #             attrs += f' style="{style_escaped}"'
        
    #     # محتوای سلول
    #     cell_content = ""
    #     if cell.content:
    #         if isinstance(cell.content, list):
    #             content_parts = []
    #             for item in cell.content:
    #                 if isinstance(item, LogicalElement):
    #                     elem_html = self._element_to_html(item)
    #                     if elem_html:
    #                         content_parts.append(elem_html.strip())
    #                 elif isinstance(item, str):
    #                     content_parts.append(self._escape_html(item))
    #             cell_content = " ".join(content_parts)
    #         elif isinstance(cell.content, str):
    #             cell_content = self._escape_html(cell.content)
        
    #     return f'        <{tag}{attrs}>{cell_content}</{tag}>'
    
    # def _format_metadata(self, metadata: Dict[str, Any]) -> str:
    #     """قالب‌بندی metadata برای HTML"""
    #     if not metadata:
    #         return ""
        
    #     attrs = []
    #     for key, value in metadata.items():
    #         if key.startswith("html_"):
    #             attr_name = key[5:]  # حذف پیشوند html_
    #             if isinstance(value, bool):
    #                 if value:
    #                     attrs.append(attr_name)
    #             elif value is not None:
    #                 escaped_value = self._escape_html(str(value))
    #                 attrs.append(f'{attr_name}="{escaped_value}"')
        
    #     return " ".join(attrs)
