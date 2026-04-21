"""
ابزارهای کمکی برای پارسر DOCX
شامل توابع کمکی برای پردازش استایل‌ها، متن، ریاضیات و مدیریت فایل‌های DOCX
"""

import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Namespaceهای OOXML
OOXML_NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'v': 'urn:schemas-microsoft-com:vml',
    'o': 'urn:schemas-microsoft-com:office:office',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
    'w15': 'http://schemas.microsoft.com/office/word/2012/wordml',
    'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}

# ثبت namespaceها برای ET
for prefix, uri in OOXML_NAMESPACES.items():
    ET.register_namespace(prefix, uri)


@dataclass
class DocxStyleInfo:
    """اطلاعات استایل DOCX"""
    style_id: str
    style_type: str  # 'paragraph', 'character', 'table', 'numbering'
    style_name: Optional[str] = None
    based_on: Optional[str] = None
    next_style: Optional[str] = None
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class DocxNumberingInfo:
    """اطلاعات شماره‌گذاری DOCX"""
    num_id: str
    abstract_num_id: str
    level: int
    format: str  # 'decimal', 'lowerLetter', 'upperLetter', 'lowerRoman', 'upperRoman', 'bullet'
    text: Optional[str] = None
    start: int = 1
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class DocxUtils:
    """کلاس ابزارهای کمکی DOCX"""
    
    @staticmethod
    def extract_text_style(rPr_elem: Optional[ET.Element]) -> Dict[str, Any]:
        """
        استخراج استایل متن از المان rPr
        
        Args:
            rPr_elem: المان rPr (run properties)
            
        Returns:
            Dict[str, Any]: اطلاعات استایل متن
        """
        style_info = {
            'bold': False,
            'italic': False,
            'underline': False,
            'strikethrough': False,
            'font_family': None,
            'font_size': None,
            'color': None,
            'background_color': None,
            'is_code': False,
            'superscript': False,
            'subscript': False,
            'highlight_color': None,
            'language': None,
            'style_id': None,
            'style_name': None
        }
        
        if rPr_elem is None:
            return style_info
        
        try:
            # بررسی bold
            b_elem = rPr_elem.find('.//w:b', OOXML_NAMESPACES)
            if b_elem is not None:
                val_attr = b_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                style_info['bold'] = val_attr is None or val_attr.lower() not in ['false', '0', 'off']
            
            # بررسی italic
            i_elem = rPr_elem.find('.//w:i', OOXML_NAMESPACES)
            if i_elem is not None:
                val_attr = i_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                style_info['italic'] = val_attr is None or val_attr.lower() not in ['false', '0', 'off']
            
            # بررسی underline
            u_elem = rPr_elem.find('.//w:u', OOXML_NAMESPACES)
            if u_elem is not None:
                val_attr = u_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if val_attr and val_attr.lower() != 'none':
                    style_info['underline'] = True
                    style_info['underline_type'] = val_attr
                elif val_attr is None:
                    style_info['underline'] = True
            
            # بررسی strikethrough
            strike_elem = rPr_elem.find('.//w:strike', OOXML_NAMESPACES)
            if strike_elem is not None:
                val_attr = strike_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                style_info['strikethrough'] = val_attr is None or val_attr.lower() not in ['false', '0', 'off']
            
            # بررسی double strikethrough
            dstrike_elem = rPr_elem.find('.//w:dstrike', OOXML_NAMESPACES)
            if dstrike_elem is not None:
                val_attr = dstrike_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if val_attr is None or val_attr.lower() not in ['false', '0', 'off']:
                    style_info['strikethrough'] = True
                    style_info['double_strikethrough'] = True
            
            # بررسی superscript/subscript
            vert_align_elem = rPr_elem.find('.//w:vertAlign', OOXML_NAMESPACES)
            if vert_align_elem is not None:
                val_attr = vert_align_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if val_attr == 'superscript':
                    style_info['superscript'] = True
                elif val_attr == 'subscript':
                    style_info['subscript'] = True
            
            # بررسی فونت
            rFonts_elem = rPr_elem.find('.//w:rFonts', OOXML_NAMESPACES)
            if rFonts_elem is not None:
                ascii_attr = rFonts_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii')
                h_ansi_attr = rFonts_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hAnsi')
                cs_attr = rFonts_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cs')
                
                # اولویت: ascii > hAnsi > cs
                font_family = ascii_attr or h_ansi_attr or cs_attr
                if font_family:
                    style_info['font_family'] = font_family
                    
                    # تشخیص کد (monospace font)
                    monospace_fonts = ['consolas', 'courier', 'monospace', 'monaco', 'source code pro', 
                                      'fira code', 'cascadia code', 'jetbrains mono']
                    if any(mf in font_family.lower() for mf in monospace_fonts):
                        style_info['is_code'] = True
            
            # بررسی سایز فونت
            sz_elem = rPr_elem.find('.//w:sz', OOXML_NAMESPACES)
            if sz_elem is not None:
                sz_val = sz_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if sz_val:
                    try:
                        # تبدیل از half-points به points
                        size_pts = int(sz_val) / 2
                        style_info['font_size'] = f"{size_pts}pt"
                    except ValueError:
                        style_info['font_size'] = sz_val
            
            szCs_elem = rPr_elem.find('.//w:szCs', OOXML_NAMESPACES)
            if szCs_elem is not None and not style_info['font_size']:
                sz_val = szCs_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if sz_val:
                    try:
                        size_pts = int(sz_val) / 2
                        style_info['font_size'] = f"{size_pts}pt"
                    except ValueError:
                        style_info['font_size'] = sz_val
            
            # بررسی رنگ متن
            color_elem = rPr_elem.find('.//w:color', OOXML_NAMESPACES)
            if color_elem is not None:
                color_val = color_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if color_val and color_val.lower() != 'auto':
                    style_info['color'] = f"#{color_val}"
            
            # بررسی رنگ پس‌زمینه
            highlight_elem = rPr_elem.find('.//w:highlight', OOXML_NAMESPACES)
            if highlight_elem is not None:
                highlight_val = highlight_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if highlight_val:
                    style_info['highlight_color'] = highlight_val
            
            shd_elem = rPr_elem.find('.//w:shd', OOXML_NAMESPACES)
            if shd_elem is not None:
                fill_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                if fill_attr and fill_attr.lower() != 'auto':
                    style_info['background_color'] = f"#{fill_attr}"
            
            # بررسی زبان
            lang_elem = rPr_elem.find('.//w:lang', OOXML_NAMESPACES)
            if lang_elem is not None:
                lang_val = lang_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if lang_val:
                    style_info['language'] = lang_val
            
            # بررسی استایل run
            rStyle_elem = rPr_elem.find('.//w:rStyle', OOXML_NAMESPACES)
            if rStyle_elem is not None:
                style_id = rStyle_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if style_id:
                    style_info['style_id'] = style_id
            
        except Exception as e:
            # در صورت خطا، اطلاعات جزئی را لاگ کنید
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج استایل متن: {str(e)}")
        
        return style_info
    
    @staticmethod
    def extract_paragraph_style(pPr_elem: Optional[ET.Element], styles_dict: Dict[str, DocxStyleInfo]) -> Dict[str, Any]:
        """
        استخراج استایل پاراگراف از المان pPr
        
        Args:
            pPr_elem: المان pPr (paragraph properties)
            styles_dict: دیکشنری استایل‌های بارگذاری شده
            
        Returns:
            Dict[str, Any]: اطلاعات استایل پاراگراف
        """
        style_info = {
            'is_heading': False,
            'heading_level': 1,
            'is_list': False,
            'is_quote': False,
            'is_code_block': False,
            'alignment': 'left',
            'indentation': {},
            'spacing': {},
            'style_id': None,
            'style_name': None,
            'list_info': None,
            'keep_lines': False,
            'keep_next': False,
            'page_break_before': False,
            'widow_control': True,
            'orphan_control': True,
            'outline_level': None
        }
        
        if pPr_elem is None:
            return style_info
        
        try:
            # استخراج styleId
            pStyle_elem = pPr_elem.find('.//w:pStyle', OOXML_NAMESPACES)
            if pStyle_elem is not None:
                style_id = pStyle_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if style_id:
                    style_info['style_id'] = style_id
                    
                    # جستجوی استایل در دیکشنری
                    if style_id in styles_dict:
                        style_obj = styles_dict[style_id]
                        style_info['style_name'] = style_obj.style_name
                        
                        # تشخیص نوع استایل
                        if style_obj.style_name:
                            style_name_lower = style_obj.style_name.lower()
                            
                            # تشخیص هدینگ
                            if 'heading' in style_name_lower:
                                style_info['is_heading'] = True
                                # استخراج سطح هدینگ
                                for i in range(1, 10):
                                    if f'heading {i}' in style_name_lower or f'heading{i}' in style_name_lower:
                                        style_info['heading_level'] = i
                                        break
                                # اگر عدد پیدا نشد، از outline level استفاده کن
                                if style_info['heading_level'] == 1 and 'outline_level' in style_obj.properties:
                                    outline_level = style_obj.properties.get('outline_level')
                                    if outline_level and 1 <= outline_level <= 9:
                                        style_info['heading_level'] = outline_level
                            
                            # تشخیص لیست
                            elif any(list_term in style_name_lower for list_term in ['list', 'bullet', 'numbering']):
                                style_info['is_list'] = True
                            
                            # تشخیص نقل قول
                            elif any(quote_term in style_name_lower for quote_term in ['quote', 'blockquote', 'quotation']):
                                style_info['is_quote'] = True
                            
                            # تشخیص بلوک کد
                            elif any(code_term in style_name_lower for code_term in ['code', 'preformatted', 'monospace']):
                                style_info['is_code_block'] = True
            
            # استخراج outline level
            outline_lvl_elem = pPr_elem.find('.//w:outlineLvl', OOXML_NAMESPACES)
            if outline_lvl_elem is not None:
                outline_val = outline_lvl_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if outline_val:
                    try:
                        style_info['outline_level'] = int(outline_val)
                        if not style_info['is_heading']:
                            style_info['is_heading'] = True
                            style_info['heading_level'] = min(style_info['outline_level'] + 1, 9)
                    except ValueError:
                        pass
            
            # استخراج تراز (justification)
            jc_elem = pPr_elem.find('.//w:jc', OOXML_NAMESPACES)
            if jc_elem is not None:
                alignment = jc_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if alignment:
                    alignment_map = {
                        'left': 'left',
                        'right': 'right',
                        'center': 'center',
                        'both': 'justify',
                        'distribute': 'justify',
                        'start': 'left',
                        'end': 'right'
                    }
                    style_info['alignment'] = alignment_map.get(alignment.lower(), 'left')
            
            # استخراج تورفتگی (indentation)
            ind_elem = pPr_elem.find('.//w:ind', OOXML_NAMESPACES)
            if ind_elem is not None:
                indentation = {}
                
                # تورفتگی چپ
                left_attr = ind_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}left')
                if left_attr:
                    try:
                        # تبدیل از twips به points (1 twip = 1/1440 inch, 1 point = 1/72 inch)
                        left_twips = int(left_attr)
                        left_pts = left_twips / 20  # 1440/72 = 20
                        indentation['left'] = f"{left_pts}pt"
                    except ValueError:
                        indentation['left'] = left_attr
                
                # تورفتگی راست
                right_attr = ind_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}right')
                if right_attr:
                    try:
                        right_twips = int(right_attr)
                        right_pts = right_twips / 20
                        indentation['right'] = f"{right_pts}pt"
                    except ValueError:
                        indentation['right'] = right_attr
                
                # تورفتگی خط اول
                first_line_attr = ind_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}firstLine')
                if first_line_attr:
                    try:
                        first_line_twips = int(first_line_attr)
                        first_line_pts = first_line_twips / 20
                        indentation['first_line'] = f"{first_line_pts}pt"
                    except ValueError:
                        indentation['first_line'] = first_line_attr
                
                # تورفتگی آویز (hanging)
                hanging_attr = ind_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hanging')
                if hanging_attr:
                    try:
                        hanging_twips = int(hanging_attr)
                        hanging_pts = hanging_twips / 20
                        indentation['hanging'] = f"{hanging_pts}pt"
                    except ValueError:
                        indentation['hanging'] = hanging_attr
                
                if indentation:
                    style_info['indentation'] = indentation
            
            # استخراج فاصله‌گذاری (spacing)
            spacing_elem = pPr_elem.find('.//w:spacing', OOXML_NAMESPACES)
            if spacing_elem is not None:
                spacing = {}
                
                # فاصله قبل
                before_attr = spacing_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}before')
                if before_attr:
                    try:
                        before_twips = int(before_attr)
                        before_pts = before_twips / 20
                        spacing['before'] = f"{before_pts}pt"
                    except ValueError:
                        spacing['before'] = before_attr
                
                # فاصله بعد
                after_attr = spacing_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}after')
                if after_attr:
                    try:
                        after_twips = int(after_attr)
                        after_pts = after_twips / 20
                        spacing['after'] = f"{after_pts}pt"
                    except ValueError:
                        spacing['after'] = after_attr
                
                # فاصله خط
                line_attr = spacing_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}line')
                if line_attr:
                    try:
                        line_val = int(line_attr)
                        if line_attr.endswith('auto'):
                            spacing['line'] = 'auto'
                        else:
                            # اگر lineRule مشخص نشده، پیش‌فرض atLeast است
                            line_rule = spacing_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}lineRule', 'atLeast')
                            if line_rule == 'exact':
                                spacing['line'] = f"{line_val / 240}pt"  # 240 = 20 * 12
                            else:  # atLeast یا auto
                                spacing['line'] = f"{line_val / 240}pt"
                    except ValueError:
                        spacing['line'] = line_attr
                
                if spacing:
                    style_info['spacing'] = spacing
            
            # استخراج اطلاعات لیست
            numPr_elem = pPr_elem.find('.//w:numPr', OOXML_NAMESPACES)
            if numPr_elem is not None:
                style_info['is_list'] = True
                list_info = {}
                
                # شماره لیست
                numId_elem = numPr_elem.find('.//w:numId', OOXML_NAMESPACES)
                if numId_elem is not None:
                    num_id = numId_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if num_id:
                        list_info['num_id'] = num_id
                
                # سطح لیست
                ilvl_elem = numPr_elem.find('.//w:ilvl', OOXML_NAMESPACES)
                if ilvl_elem is not None:
                    ilvl_val = ilvl_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if ilvl_val:
                        try:
                            list_info['level'] = int(ilvl_val)
                        except ValueError:
                            list_info['level'] = 0
                
                style_info['list_info'] = list_info
            
            # بررسی keepLines (نگه داشتن همه خطوط در یک صفحه)
            keepLines_elem = pPr_elem.find('.//w:keepLines', OOXML_NAMESPACES)
            if keepLines_elem is not None:
                style_info['keep_lines'] = True
            
            # بررسی keepNext (نگه داشتن با پاراگراف بعدی)
            keepNext_elem = pPr_elem.find('.//w:keepNext', OOXML_NAMESPACES)
            if keepNext_elem is not None:
                style_info['keep_next'] = True
            
            # بررسی pageBreakBefore (شکستن صفحه قبل)
            pageBreakBefore_elem = pPr_elem.find('.//w:pageBreakBefore', OOXML_NAMESPACES)
            if pageBreakBefore_elem is not None:
                style_info['page_break_before'] = True
            
            # بررسی widowControl (کنترل بیوه)
            widowControl_elem = pPr_elem.find('.//w:widowControl', OOXML_NAMESPACES)
            if widowControl_elem is not None:
                val_attr = widowControl_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                style_info['widow_control'] = val_attr is None or val_attr.lower() not in ['false', '0', 'off']
            
            # بررسی orphanControl (کنترل یتیم)
            orphanControl_elem = pPr_elem.find('.//w:orphanControl', OOXML_NAMESPACES)
            if orphanControl_elem is not None:
                val_attr = orphanControl_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                style_info['orphan_control'] = val_attr is None or val_attr.lower() not in ['false', '0', 'off']
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج استایل پاراگراف: {str(e)}")
        
        return style_info
    
    @staticmethod
    def extract_style_properties(style_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج ویژگی‌های استایل از المان style
        
        Args:
            style_elem: المان style
            
        Returns:
            Dict[str, Any]: ویژگی‌های استایل
        """
        properties = {}
        
        try:
            # استخراج ویژگی‌های پاراگراف
            pPr_elem = style_elem.find('.//w:pPr', OOXML_NAMESPACES)
            if pPr_elem is not None:
                # outline level
                outline_lvl_elem = pPr_elem.find('.//w:outlineLvl', OOXML_NAMESPACES)
                if outline_lvl_elem is not None:
                    outline_val = outline_lvl_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if outline_val:
                        try:
                            properties['outline_level'] = int(outline_val)
                        except ValueError:
                            properties['outline_level'] = outline_val
                
                # justification
                jc_elem = pPr_elem.find('.//w:jc', OOXML_NAMESPACES)
                if jc_elem is not None:
                    jc_val = jc_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if jc_val:
                        properties['justification'] = jc_val
                
                # indentation
                ind_elem = pPr_elem.find('.//w:ind', OOXML_NAMESPACES)
                if ind_elem is not None:
                    ind_props = {}
                    for attr_name in ['left', 'right', 'firstLine', 'hanging']:
                        attr_val = ind_elem.get(f'{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}{attr_name}')
                        if attr_val:
                            ind_props[attr_name] = attr_val
                    if ind_props:
                        properties['indentation'] = ind_props
                
                # spacing
                spacing_elem = pPr_elem.find('.//w:spacing', OOXML_NAMESPACES)
                if spacing_elem is not None:
                    spacing_props = {}
                    for attr_name in ['before', 'after', 'line', 'lineRule']:
                        attr_val = spacing_elem.get(f'{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}{attr_name}')
                        if attr_val:
                            spacing_props[attr_name] = attr_val
                    if spacing_props:
                        properties['spacing'] = spacing_props
            
            # استخراج ویژگی‌های run
            rPr_elem = style_elem.find('.//w:rPr', OOXML_NAMESPACES)
            if rPr_elem is not None:
                # font
                rFonts_elem = rPr_elem.find('.//w:rFonts', OOXML_NAMESPACES)
                if rFonts_elem is not None:
                    font_props = {}
                    for attr_name in ['ascii', 'hAnsi', 'cs', 'eastAsia']:
                        attr_val = rFonts_elem.get(f'{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}{attr_name}')
                        if attr_val:
                            font_props[attr_name] = attr_val
                    if font_props:
                        properties['font'] = font_props
                
                # font size
                sz_elem = rPr_elem.find('.//w:sz', OOXML_NAMESPACES)
                if sz_elem is not None:
                    sz_val = sz_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if sz_val:
                        properties['font_size'] = sz_val
                
                szCs_elem = rPr_elem.find('.//w:szCs', OOXML_NAMESPACES)
                if szCs_elem is not None and 'font_size' not in properties:
                    sz_val = szCs_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if sz_val:
                        properties['font_size'] = sz_val
                
                # color
                color_elem = rPr_elem.find('.//w:color', OOXML_NAMESPACES)
                if color_elem is not None:
                    color_val = color_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if color_val:
                        properties['color'] = color_val
                
                # bold
                b_elem = rPr_elem.find('.//w:b', OOXML_NAMESPACES)
                if b_elem is not None:
                    b_val = b_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    properties['bold'] = b_val is None or b_val.lower() not in ['false', '0', 'off']
                
                # italic
                i_elem = rPr_elem.find('.//w:i', OOXML_NAMESPACES)
                if i_elem is not None:
                    i_val = i_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    properties['italic'] = i_val is None or i_val.lower() not in ['false', '0', 'off']
                
                # underline
                u_elem = rPr_elem.find('.//w:u', OOXML_NAMESPACES)
                if u_elem is not None:
                    u_val = u_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if u_val:
                        properties['underline'] = u_val
                
                # strikethrough
                strike_elem = rPr_elem.find('.//w:strike', OOXML_NAMESPACES)
                if strike_elem is not None:
                    strike_val = strike_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    properties['strikethrough'] = strike_val is None or strike_val.lower() not in ['false', '0', 'off']
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج ویژگی‌های استایل: {str(e)}")
        
        return properties
    
    @staticmethod
    def extract_numbering_definition(abstract_num_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج تعریف شماره‌گذاری از المان abstractNum
        
        Args:
            abstract_num_elem: المان abstractNum
            
        Returns:
            Dict[str, Any]: اطلاعات شماره‌گذاری
        """
        numbering_info = {
            'levels': {},
            'multi_level': False,
            'restart_numbering': True
        }
        
        try:
            # استخراج restart numbering
            restart_elem = abstract_num_elem.find('.//w:lvlRestart', OOXML_NAMESPACES)
            if restart_elem is not None:
                restart_val = restart_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if restart_val:
                    numbering_info['restart_numbering'] = restart_val.lower() not in ['false', '0', 'off']
            
            # استخراج سطوح
            for lvl_elem in abstract_num_elem.findall('.//w:lvl', OOXML_NAMESPACES):
                ilvl_attr = lvl_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ilvl')
                if ilvl_attr is None:
                    continue
                
                try:
                    level = int(ilvl_attr)
                    level_info = {}
                    
                    # استخراج start
                    start_elem = lvl_elem.find('.//w:start', OOXML_NAMESPACES)
                    if start_elem is not None:
                        start_val = start_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if start_val:
                            try:
                                level_info['start'] = int(start_val)
                            except ValueError:
                                level_info['start'] = 1
                    
                    # استخراج format
                    numFmt_elem = lvl_elem.find('.//w:numFmt', OOXML_NAMESPACES)
                    if numFmt_elem is not None:
                        num_fmt = numFmt_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if num_fmt:
                            format_map = {
                                'decimal': 'decimal',
                                'lowerLetter': 'lowerLetter',
                                'upperLetter': 'upperLetter',
                                'lowerRoman': 'lowerRoman',
                                'upperRoman': 'upperRoman',
                                'bullet': 'bullet',
                                'none': 'none'
                            }
                            level_info['format'] = format_map.get(num_fmt, num_fmt)
                    
                    # استخراج text
                    lvlText_elem = lvl_elem.find('.//w:lvlText', OOXML_NAMESPACES)
                    if lvlText_elem is not None:
                        lvl_text = lvlText_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if lvl_text:
                            level_info['text'] = lvl_text
                    
                    # استخراج justification
                    lvlJc_elem = lvl_elem.find('.//w:lvlJc', OOXML_NAMESPACES)
                    if lvlJc_elem is not None:
                        lvl_jc = lvlJc_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if lvl_jc:
                            level_info['justification'] = lvl_jc
                    
                    numbering_info['levels'][level] = level_info
                    
                except ValueError:
                    continue
            
            # بررسی multi-level
            if len(numbering_info['levels']) > 1:
                numbering_info['multi_level'] = True
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج تعریف شماره‌گذاری: {str(e)}")
        
        return numbering_info
    
    @staticmethod
    def extract_text_from_element(elem: Optional[ET.Element], include_children: bool = True) -> str:
        """
        استخراج متن از یک المان XML و فرزندان آن
        
        Args:
            elem: المان XML
            include_children: آیا متن فرزندان نیز استخراج شود
            
        Returns:
            str: متن استخراج شده
        """
        if elem is None:
            return ""
        
        text_parts = []
        
        try:
            # اگر المان خودش متن دارد
            if elem.text and elem.text.strip():
                text_parts.append(elem.text.strip())
            
            # پردازش فرزندان
            if include_children:
                for child in elem:
                    # استخراج متن از المان‌های w:t
                    if child.tag.endswith('t'):
                        if child.text and child.text.strip():
                            text_parts.append(child.text.strip())
                    # پردازش بازگشتی برای المان‌های دیگر
                    else:
                        child_text = DocxUtils.extract_text_from_element(child, include_children)
                        if child_text:
                            text_parts.append(child_text)
                    
                    # افزودن tail
                    if child.tail and child.tail.strip():
                        text_parts.append(child.tail.strip())
            
            # افزودن tail المان اصلی
            if elem.tail and elem.tail.strip():
                text_parts.append(elem.tail.strip())
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج متن از المان: {str(e)}")
        
        return ' '.join(text_parts).strip()
    
    @staticmethod
    def convert_omml_to_latex(omml_elem: ET.Element) -> Optional[str]:
        """
        تبدیل OMML (Office Math ML) به LaTeX
        
        Args:
            omml_elem: المان OMML
            
        Returns:
            Optional[str]: رشته LaTeX یا None در صورت خطا
        """
        try:
            # این یک تبدیل ساده است. برای تبدیل کامل نیاز به پیاده‌سازی کامل داریم
            latex_parts = []
            
            # پردازش المان‌های ریاضی
            for elem in omml_elem.iter():
                if elem.tag.endswith('oMath'):
                    # المان ریاضی اصلی
                    continue
                elif elem.tag.endswith('acc'):
                    # اکسان (مثل hat, bar)
                    acc_elem = elem.find('.//m:accPr', OOXML_NAMESPACES)
                    if acc_elem is not None:
                        chr_elem = acc_elem.find('.//m:chr', OOXML_NAMESPACES)
                        if chr_elem is not None:
                            chr_val = chr_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                            if chr_val:
                                base_elem = elem.find('.//m:e', OOXML_NAMESPACES)
                                if base_elem is not None:
                                    base_text = DocxUtils.extract_text_from_element(base_elem)
                                    if chr_val == '̂':  # hat
                                        latex_parts.append(f"\\hat{{{base_text}}}")
                                    elif chr_val == '̄':  # bar
                                        latex_parts.append(f"\\bar{{{base_text}}}")
                                    elif chr_val == '⃗':  # vector
                                        latex_parts.append(f"\\vec{{{base_text}}}")
                                    else:
                                        latex_parts.append(f"{base_text}")
                elif elem.tag.endswith('rad'):
                    # رادیکال
                    deg_elem = elem.find('.//m:deg', OOXML_NAMESPACES)
                    rad_elem = elem.find('.//m:e', OOXML_NAMESPACES)
                    
                    if rad_elem is not None:
                        rad_text = DocxUtils.extract_text_from_element(rad_elem)
                        if deg_elem is not None:
                            deg_text = DocxUtils.extract_text_from_element(deg_elem)
                            latex_parts.append(f"\\sqrt[{deg_text}]{{{rad_text}}}")
                        else:
                            latex_parts.append(f"\\sqrt{{{rad_text}}}")
                elif elem.tag.endswith('frac'):
                    # کسر
                    num_elem = elem.find('.//m:num', OOXML_NAMESPACES)
                    den_elem = elem.find('.//m:den', OOXML_NAMESPACES)
                    
                    if num_elem is not None and den_elem is not None:
                        num_text = DocxUtils.extract_text_from_element(num_elem)
                        den_text = DocxUtils.extract_text_from_element(den_elem)
                        latex_parts.append(f"\\frac{{{num_text}}}{{{den_text}}}")
                elif elem.tag.endswith('sup'):
                    # توان
                    base_elem = elem.find('.//m:e', OOXML_NAMESPACES)
                    sup_elem = elem.find('.//m:sup', OOXML_NAMESPACES)
                    
                    if base_elem is not None and sup_elem is not None:
                        base_text = DocxUtils.extract_text_from_element(base_elem)
                        sup_text = DocxUtils.extract_text_from_element(sup_elem)
                        latex_parts.append(f"{{{base_text}}}^{{{sup_text}}}")
                elif elem.tag.endswith('sub'):
                    # اندیس
                    base_elem = elem.find('.//m:e', OOXML_NAMESPACES)
                    sub_elem = elem.find('.//m:sub', OOXML_NAMESPACES)
                    
                    if base_elem is not None and sub_elem is not None:
                        base_text = DocxUtils.extract_text_from_element(base_elem)
                        sub_text = DocxUtils.extract_text_from_element(sub_elem)
                        latex_parts.append(f"{{{base_text}}}_{{{sub_text}}}")
                elif elem.tag.endswith('r'):
                    # متن معمولی
                    text = DocxUtils.extract_text_from_element(elem)
                    if text:
                        latex_parts.append(text)
            
            if latex_parts:
                return ' '.join(latex_parts)
            
            # اگر تبدیل خاصی انجام نشد، متن ساده استخراج شود
            simple_text = DocxUtils.extract_text_from_element(omml_elem)
            if simple_text:
                return f"${simple_text}$"
            
            return None
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در تبدیل OMML به LaTeX: {str(e)}")
            return None
    
    @staticmethod
    def convert_color_from_ooxml(color_value: str) -> str:
        """
        تبدیل رنگ از فرمت OOXML به HEX
        
        Args:
            color_value: مقدار رنگ در OOXML
            
        Returns:
            str: رنگ در فرمت HEX
        """
        if not color_value:
            return "#000000"
        
        color_value = color_value.lower().strip()
        
        # اگر رنگ از قبل HEX است
        if re.match(r'^[0-9a-f]{6}$', color_value):
            return f"#{color_value}"
        
        # اگر رنگ با auto یا none است
        if color_value in ['auto', 'none']:
            return "#000000"
        
        # رنگ‌های نامی
        color_map = {
            'black': '#000000',
            'white': '#FFFFFF',
            'red': '#FF0000',
            'green': '#00FF00',
            'blue': '#0000FF',
            'yellow': '#FFFF00',
            'cyan': '#00FFFF',
            'magenta': '#FF00FF',
            'gray': '#808080',
            'grey': '#808080',
            'darkred': '#8B0000',
            'darkgreen': '#006400',
            'darkblue': '#00008B',
            'darkyellow': '#CCCC00',
            'darkcyan': '#008B8B',
            'darkmagenta': '#8B008B',
            'lightgray': '#D3D3D3',
            'lightgrey': '#D3D3D3',
        }
        
        if color_value in color_map:
            return color_map[color_value]
        
        # اگر مقدار عددی است (مثل "FF0000" بدون #)
        if re.match(r'^[0-9a-f]{6}$', color_value):
            return f"#{color_value}"
        
        # اگر مقدار ARGB است (مثل "FF000000")
        if re.match(r'^[0-9a-f]{8}$', color_value):
            # حذف آلفا و برگرداندن RGB
            return f"#{color_value[2:]}"
        
        # پیش‌فرض
        return "#000000"
    
    @staticmethod
    def get_namespace_tag(tag_name: str, namespace: str = 'w') -> str:
        """
        ساخت تگ با namespace
        
        Args:
            tag_name: نام تگ
            namespace: namespace (پیش‌فرض: 'w')
            
        Returns:
            str: تگ کامل با namespace
        """
        return f"{{{OOXML_NAMESPACES.get(namespace, namespace)}}}{tag_name}"
    
    @staticmethod
    def find_element_with_ns(elem: ET.Element, tag_name: str, namespace: str = 'w') -> Optional[ET.Element]:
        """
        یافتن المان با namespace
        
        Args:
            elem: المان والد
            tag_name: نام تگ
            namespace: namespace (پیش‌فرض: 'w')
            
        Returns:
            Optional[ET.Element]: المان یافت شده یا None
        """
        if elem is None:
            return None
        
        ns_tag = DocxUtils.get_namespace_tag(tag_name, namespace)
        return elem.find(f'.//{ns_tag}', OOXML_NAMESPACES)
    
    @staticmethod
    def find_all_elements_with_ns(elem: ET.Element, tag_name: str, namespace: str = 'w') -> List[ET.Element]:
        """
        یافتن همه المان‌ها با namespace
        
        Args:
            elem: المان والد
            tag_name: نام تگ
            namespace: namespace (پیش‌فرض: 'w')
            
        Returns:
            List[ET.Element]: لیست المان‌های یافت شده
        """
        if elem is None:
            return []
        
        ns_tag = DocxUtils.get_namespace_tag(tag_name, namespace)
        return elem.findall(f'.//{ns_tag}', OOXML_NAMESPACES)
    
    @staticmethod
    def extract_hyperlink_info(hyperlink_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات هایپرلینک از المان hyperlink
        
        Args:
            hyperlink_elem: المان hyperlink
            
        Returns:
            Dict[str, Any]: اطلاعات هایپرلینک
        """
        hyperlink_info = {
            'url': None,
            'anchor': None,
            'tooltip': None,
            'display_text': ''
        }
        
        try:
            # استخراج رابطه (relationship)
            r_id = hyperlink_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            if r_id:
                hyperlink_info['relationship_id'] = r_id
            
            # استخراج anchor
            anchor = hyperlink_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}anchor')
            if anchor:
                hyperlink_info['anchor'] = anchor
            
            # استخراج tooltip
            tooltip = hyperlink_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tooltip')
            if tooltip:
                hyperlink_info['tooltip'] = tooltip
            
            # استخراج متن نمایشی
            runs = hyperlink_elem.findall('.//w:r', OOXML_NAMESPACES)
            text_parts = []
            for run in runs:
                text_elem = run.find('.//w:t', OOXML_NAMESPACES)
                if text_elem is not None and text_elem.text:
                    text_parts.append(text_elem.text.strip())
            
            if text_parts:
                hyperlink_info['display_text'] = ' '.join(text_parts)
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات هایپرلینک: {str(e)}")
        
        return hyperlink_info
    
    @staticmethod
    def extract_image_info(drawing_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات تصویر از المان drawing
        
        Args:
            drawing_elem: المان drawing
            
        Returns:
            Dict[str, Any]: اطلاعات تصویر
        """
        image_info = {
            'relationship_id': None,
            'filename': None,
            'width': None,
            'height': None,
            'title': None,
            'description': None,
            'content_type': None
        }
        
        try:
            # یافتن المان blip (تصویر)
            blip_elem = drawing_elem.find('.//a:blip', OOXML_NAMESPACES)
            if blip_elem is not None:
                r_embed = blip_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                r_link = blip_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}link')
                
                if r_embed:
                    image_info['relationship_id'] = r_embed
                    image_info['embed_type'] = 'embedded'
                elif r_link:
                    image_info['relationship_id'] = r_link
                    image_info['embed_type'] = 'linked'
            
            # یافتن المان pic (تصویر)
            pic_elem = drawing_elem.find('.//pic:pic', OOXML_NAMESPACES)
            if pic_elem is not None:
                # استخراج ابعاد
                ext_elem = pic_elem.find('.//a:ext', OOXML_NAMESPACES)
                if ext_elem is not None:
                    cx_attr = ext_elem.get('cx')
                    cy_attr = ext_elem.get('cy')
                    
                    if cx_attr and cy_attr:
                        try:
                            # تبدیل از EMU به پیکسل (1 EMU = 1/914400 inch)
                            # فرض: 96 DPI
                            width_emu = int(cx_attr)
                            height_emu = int(cy_attr)
                            
                            # تبدیل به پیکسل
                            width_px = width_emu / 914400 * 96
                            height_px = height_emu / 914400 * 96
                            
                            image_info['width'] = round(width_px)
                            image_info['height'] = round(height_px)
                            image_info['width_emu'] = width_emu
                            image_info['height_emu'] = height_emu
                        except ValueError:
                            pass
                
                # استخراج عنوان و توضیحات
                nvPicPr_elem = pic_elem.find('.//pic:nvPicPr', OOXML_NAMESPACES)
                if nvPicPr_elem is not None:
                    cNvPr_elem = nvPicPr_elem.find('.//a:cNvPr', OOXML_NAMESPACES)
                    if cNvPr_elem is not None:
                        title = cNvPr_elem.get('title')
                        desc = cNvPr_elem.get('descr')
                        
                        if title:
                            image_info['title'] = title
                        if desc:
                            image_info['description'] = desc
            
            # یافتن اطلاعات content type
            blipFill_elem = drawing_elem.find('.//a:blipFill', OOXML_NAMESPACES)
            if blipFill_elem is not None:
                srcRect_elem = blipFill_elem.find('.//a:srcRect', OOXML_NAMESPACES)
                if srcRect_elem is not None:
                    # استخراج اطلاعات crop
                    for attr in ['l', 't', 'r', 'b']:
                        val = srcRect_elem.get(attr)
                        if val:
                            image_info[f'crop_{attr}'] = val
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات تصویر: {str(e)}")
        
        return image_info
    
    @staticmethod
    def extract_table_properties(tblPr_elem: Optional[ET.Element]) -> Dict[str, Any]:
        """
        استخراج ویژگی‌های جدول از المان tblPr
        
        Args:
            tblPr_elem: المان tblPr (table properties)
            
        Returns:
            Dict[str, Any]: ویژگی‌های جدول
        """
        table_props = {
            'style_id': None,
            'style_name': None,
            'alignment': 'left',
            'width': None,
            'borders': {},
            'shading': None,
            'layout': 'autofit',
            'indentation': None
        }
        
        if tblPr_elem is None:
            return table_props
        
        try:
            # استخراج استایل جدول
            tblStyle_elem = tblPr_elem.find('.//w:tblStyle', OOXML_NAMESPACES)
            if tblStyle_elem is not None:
                style_id = tblStyle_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if style_id:
                    table_props['style_id'] = style_id
            
            # استخراج تراز جدول
            jc_elem = tblPr_elem.find('.//w:jc', OOXML_NAMESPACES)
            if jc_elem is not None:
                alignment = jc_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if alignment:
                    alignment_map = {
                        'left': 'left',
                        'right': 'right',
                        'center': 'center',
                        'both': 'justify',
                        'distribute': 'justify',
                        'start': 'left',
                        'end': 'right'
                    }
                    table_props['alignment'] = alignment_map.get(alignment.lower(), 'left')
            
            # استخراج عرض جدول
            tblW_elem = tblPr_elem.find('.//w:tblW', OOXML_NAMESPACES)
            if tblW_elem is not None:
                width_type = tblW_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type', 'auto')
                width_val = tblW_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')
                
                if width_val and width_type != 'auto':
                    try:
                        # تبدیل از twips به points
                        width_twips = int(width_val)
                        width_pts = width_twips / 20
                        table_props['width'] = f"{width_pts}pt"
                        table_props['width_type'] = width_type
                    except ValueError:
                        table_props['width'] = width_val
            
            # استخراج حاشیه‌های جدول
            tblBorders_elem = tblPr_elem.find('.//w:tblBorders', OOXML_NAMESPACES)
            if tblBorders_elem is not None:
                borders = {}
                for border_type in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                    border_elem = tblBorders_elem.find(f'.//w:{border_type}', OOXML_NAMESPACES)
                    if border_elem is not None:
                        border_info = {}
                        
                        # استخراج نوع border
                        border_val = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if border_val:
                            border_info['type'] = border_val
                        
                        # استخراج سایز
                        border_sz = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz')
                        if border_sz:
                            try:
                                # تبدیل از 1/8 point به point
                                sz_val = int(border_sz)
                                border_info['size'] = f"{sz_val / 8}pt"
                            except ValueError:
                                border_info['size'] = border_sz
                        
                        # استخراج رنگ
                        border_color = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color')
                        if border_color:
                            border_info['color'] = DocxUtils.convert_color_from_ooxml(border_color)
                        
                        if border_info:
                            borders[border_type] = border_info
                
                if borders:
                    table_props['borders'] = borders
            
            # استخراج سایه‌زنی
            shd_elem = tblPr_elem.find('.//w:shd', OOXML_NAMESPACES)
            if shd_elem is not None:
                shading = {}
                
                fill_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                if fill_attr:
                    shading['fill'] = DocxUtils.convert_color_from_ooxml(fill_attr)
                
                val_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if val_attr:
                    shading['type'] = val_attr
                
                color_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color')
                if color_attr:
                    shading['color'] = DocxUtils.convert_color_from_ooxml(color_attr)
                
                if shading:
                    table_props['shading'] = shading
            
            # استخراج layout
            tblLayout_elem = tblPr_elem.find('.//w:tblLayout', OOXML_NAMESPACES)
            if tblLayout_elem is not None:
                layout_type = tblLayout_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
                if layout_type:
                    table_props['layout'] = 'fixed' if layout_type == 'fixed' else 'autofit'
            
            # استخراج تورفتگی
            tblInd_elem = tblPr_elem.find('.//w:tblInd', OOXML_NAMESPACES)
            if tblInd_elem is not None:
                ind_type = tblInd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type', 'dxa')
                ind_val = tblInd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')
                
                if ind_val:
                    try:
                        if ind_type == 'dxa':  # twips
                            ind_twips = int(ind_val)
                            ind_pts = ind_twips / 20
                            table_props['indentation'] = f"{ind_pts}pt"
                        else:
                            table_props['indentation'] = ind_val
                    except ValueError:
                        table_props['indentation'] = ind_val
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج ویژگی‌های جدول: {str(e)}")
        
        return table_props
    
    @staticmethod
    def extract_cell_properties(tcPr_elem: Optional[ET.Element]) -> Dict[str, Any]:
        """
        استخراج ویژگی‌های سلول جدول از المان tcPr
        
        Args:
            tcPr_elem: المان tcPr (table cell properties)
            
        Returns:
            Dict[str, Any]: ویژگی‌های سلول
        """
        cell_props = {
            'width': None,
            'vertical_align': 'top',
            'grid_span': 1,
            'v_merge': None,
            'shading': None,
            'borders': {},
            'margins': {}
        }
        
        if tcPr_elem is None:
            return cell_props
        
        try:
            # استخراج عرض سلول
            tcW_elem = tcPr_elem.find('.//w:tcW', OOXML_NAMESPACES)
            if tcW_elem is not None:
                width_type = tcW_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type', 'dxa')
                width_val = tcW_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')
                
                if width_val:
                    try:
                        if width_type == 'dxa':  # twips
                            width_twips = int(width_val)
                            width_pts = width_twips / 20
                            cell_props['width'] = f"{width_pts}pt"
                        elif width_type == 'pct':  # درصد
                            cell_props['width'] = f"{width_val}%"
                        else:
                            cell_props['width'] = width_val
                        cell_props['width_type'] = width_type
                    except ValueError:
                        cell_props['width'] = width_val
            
            # استخراج تراز عمودی
            vAlign_elem = tcPr_elem.find('.//w:vAlign', OOXML_NAMESPACES)
            if vAlign_elem is not None:
                align_val = vAlign_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if align_val:
                    align_map = {
                        'top': 'top',
                        'center': 'center',
                        'bottom': 'bottom',
                        'both': 'center'
                    }
                    cell_props['vertical_align'] = align_map.get(align_val.lower(), 'top')
            
            # استخراج grid span (ادغام ستون‌ها)
            gridSpan_elem = tcPr_elem.find('.//w:gridSpan', OOXML_NAMESPACES)
            if gridSpan_elem is not None:
                span_val = gridSpan_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if span_val:
                    try:
                        cell_props['grid_span'] = int(span_val)
                    except ValueError:
                        cell_props['grid_span'] = 1
            
            # استخراج vMerge (ادغام ردیف‌ها)
            vMerge_elem = tcPr_elem.find('.//w:vMerge', OOXML_NAMESPACES)
            if vMerge_elem is not None:
                merge_val = vMerge_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if merge_val:
                    cell_props['v_merge'] = merge_val  # 'restart' یا 'continue'
            
            # استخراج سایه‌زنی سلول
            shd_elem = tcPr_elem.find('.//w:shd', OOXML_NAMESPACES)
            if shd_elem is not None:
                shading = {}
                
                fill_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                if fill_attr:
                    shading['fill'] = DocxUtils.convert_color_from_ooxml(fill_attr)
                
                val_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if val_attr:
                    shading['type'] = val_attr
                
                color_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color')
                if color_attr:
                    shading['color'] = DocxUtils.convert_color_from_ooxml(color_attr)
                
                if shading:
                    cell_props['shading'] = shading
            
            # استخراج حاشیه‌های سلول
            tcBorders_elem = tcPr_elem.find('.//w:tcBorders', OOXML_NAMESPACES)
            if tcBorders_elem is not None:
                borders = {}
                for border_type in ['top', 'left', 'bottom', 'right', 'tl2br', 'tr2bl']:
                    border_elem = tcBorders_elem.find(f'.//w:{border_type}', OOXML_NAMESPACES)
                    if border_elem is not None:
                        border_info = {}
                        
                        border_val = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if border_val:
                            border_info['type'] = border_val
                        
                        border_sz = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz')
                        if border_sz:
                            try:
                                sz_val = int(border_sz)
                                border_info['size'] = f"{sz_val / 8}pt"
                            except ValueError:
                                border_info['size'] = border_sz
                        
                        border_color = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color')
                        if border_color:
                            border_info['color'] = DocxUtils.convert_color_from_ooxml(border_color)
                        
                        if border_info:
                            borders[border_type] = border_info
                
                if borders:
                    cell_props['borders'] = borders
            
            # استخراج حاشیه‌های داخلی سلول
            tcMar_elem = tcPr_elem.find('.//w:tcMar', OOXML_NAMESPACES)
            if tcMar_elem is not None:
                margins = {}
                for margin_type in ['top', 'left', 'bottom', 'right']:
                    margin_elem = tcMar_elem.find(f'.//w:{margin_type}', OOXML_NAMESPACES)
                    if margin_elem is not None:
                        margin_w = margin_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')
                        margin_type_attr = margin_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type', 'dxa')
                        
                        if margin_w:
                            try:
                                if margin_type_attr == 'dxa':  # twips
                                    margin_twips = int(margin_w)
                                    margin_pts = margin_twips / 20
                                    margins[margin_type] = f"{margin_pts}pt"
                                else:
                                    margins[margin_type] = margin_w
                            except ValueError:
                                margins[margin_type] = margin_w
                
                if margins:
                    cell_props['margins'] = margins
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج ویژگی‌های سلول: {str(e)}")
        
        return cell_props
    
    @staticmethod
    def extract_row_properties(trPr_elem: Optional[ET.Element]) -> Dict[str, Any]:
        """
        استخراج ویژگی‌های ردیف جدول از المان trPr
        
        Args:
            trPr_elem: المان trPr (table row properties)
            
        Returns:
            Dict[str, Any]: ویژگی‌های ردیف
        """
        row_props = {
            'height': None,
            'height_rule': 'auto',
            'cant_split': False,
            'header': False,
            'hidden': False
        }
        
        if trPr_elem is None:
            return row_props
        
        try:
            # استخراج ارتفاع ردیف
            trHeight_elem = trPr_elem.find('.//w:trHeight', OOXML_NAMESPACES)
            if trHeight_elem is not None:
                height_val = trHeight_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                height_rule = trHeight_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hRule', 'auto')
                
                if height_val:
                    try:
                        # تبدیل از twips به points
                        height_twips = int(height_val)
                        height_pts = height_twips / 20
                        row_props['height'] = f"{height_pts}pt"
                        row_props['height_rule'] = height_rule
                    except ValueError:
                        row_props['height'] = height_val
            
            # بررسی عدم شکستن ردیف
            cantSplit_elem = trPr_elem.find('.//w:cantSplit', OOXML_NAMESPACES)
            if cantSplit_elem is not None:
                row_props['cant_split'] = True
            
            # بررسی ردیف هدر
            tblHeader_elem = trPr_elem.find('.//w:tblHeader', OOXML_NAMESPACES)
            if tblHeader_elem is not None:
                row_props['header'] = True
            
            # بررسی ردیف مخفی
            hidden_elem = trPr_elem.find('.//w:hidden', OOXML_NAMESPACES)
            if hidden_elem is not None:
                row_props['hidden'] = True
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج ویژگی‌های ردیف: {str(e)}")
        
        return row_props
    
    @staticmethod
    def extract_footnote_info(footnote_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات پاورقی از المان footnote
        
        Args:
            footnote_elem: المان footnote
            
        Returns:
            Dict[str, Any]: اطلاعات پاورقی
        """
        footnote_info = {
            'id': None,
            'type': 'normal',  # 'normal', 'separator', 'continuationSeparator', 'continuationNotice'
            'content': '',
            'reference_mark': None
        }
        
        try:
            # استخراج ID و نوع
            footnote_id = footnote_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
            footnote_type = footnote_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
            
            if footnote_id:
                footnote_info['id'] = footnote_id
            
            if footnote_type:
                type_map = {
                    'normal': 'normal',
                    'separator': 'separator',
                    'continuationSeparator': 'continuationSeparator',
                    'continuationNotice': 'continuationNotice'
                }
                footnote_info['type'] = type_map.get(footnote_type, 'normal')
            
            # استخراج محتوا
            paragraphs = footnote_elem.findall('.//w:p', OOXML_NAMESPACES)
            content_parts = []
            
            for para in paragraphs:
                para_text = DocxUtils.extract_text_from_element(para)
                if para_text:
                    content_parts.append(para_text)
            
            if content_parts:
                footnote_info['content'] = '\n'.join(content_parts)
            
            # استخراج reference mark
            ref_elem = footnote_elem.find('.//w:r/w:footnoteRef', OOXML_NAMESPACES)
            if ref_elem is not None:
                footnote_info['reference_mark'] = True
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات پاورقی: {str(e)}")
        
        return footnote_info
    
    @staticmethod
    def extract_endnote_info(endnote_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات یادداشت پایانی از المان endnote
        
        Args:
            endnote_elem: المان endnote
            
        Returns:
            Dict[str, Any]: اطلاعات یادداشت پایانی
        """
        endnote_info = {
            'id': None,
            'type': 'normal',
            'content': '',
            'reference_mark': None
        }
        
        try:
            # استخراج ID و نوع
            endnote_id = endnote_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
            endnote_type = endnote_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
            
            if endnote_id:
                endnote_info['id'] = endnote_id
            
            if endnote_type:
                type_map = {
                    'normal': 'normal',
                    'separator': 'separator',
                    'continuationSeparator': 'continuationSeparator',
                    'continuationNotice': 'continuationNotice'
                }
                endnote_info['type'] = type_map.get(endnote_type, 'normal')
            
            # استخراج محتوا
            paragraphs = endnote_elem.findall('.//w:p', OOXML_NAMESPACES)
            content_parts = []
            
            for para in paragraphs:
                para_text = DocxUtils.extract_text_from_element(para)
                if para_text:
                    content_parts.append(para_text)
            
            if content_parts:
                endnote_info['content'] = '\n'.join(content_parts)
            
            # استخراج reference mark
            ref_elem = endnote_elem.find('.//w:r/w:endnoteRef', OOXML_NAMESPACES)
            if ref_elem is not None:
                endnote_info['reference_mark'] = True
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات یادداشت پایانی: {str(e)}")
        
        return endnote_info
    
    @staticmethod
    def extract_bookmark_info(bookmark_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات بوکمارک از المان bookmarkStart یا bookmarkEnd
        
        Args:
            bookmark_elem: المان bookmarkStart یا bookmarkEnd
            
        Returns:
            Dict[str, Any]: اطلاعات بوکمارک
        """
        bookmark_info = {
            'id': None,
            'name': None,
            'type': None,  # 'start' یا 'end'
            'col_first': None,
            'col_last': None
        }
        
        try:
            # تعیین نوع بوکمارک
            if bookmark_elem.tag.endswith('bookmarkStart'):
                bookmark_info['type'] = 'start'
            elif bookmark_elem.tag.endswith('bookmarkEnd'):
                bookmark_info['type'] = 'end'
            
            # استخراج ID
            bookmark_id = bookmark_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
            if bookmark_id:
                bookmark_info['id'] = bookmark_id
            
            # استخراج نام (فقط برای bookmarkStart)
            if bookmark_info['type'] == 'start':
                bookmark_name = bookmark_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}name')
                if bookmark_name:
                    bookmark_info['name'] = bookmark_name
            
            # استخراج محدوده ستون‌ها (برای جداول)
            col_first = bookmark_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}colFirst')
            col_last = bookmark_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}colLast')
            
            if col_first:
                try:
                    bookmark_info['col_first'] = int(col_first)
                except ValueError:
                    bookmark_info['col_first'] = col_first
            
            if col_last:
                try:
                    bookmark_info['col_last'] = int(col_last)
                except ValueError:
                    bookmark_info['col_last'] = col_last
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات بوکمارک: {str(e)}")
        
        return bookmark_info
    
    @staticmethod
    def extract_comment_info(comment_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات کامنت از المان comment
        
        Args:
            comment_elem: المان comment
            
        Returns:
            Dict[str, Any]: اطلاعات کامنت
        """
        comment_info = {
            'id': None,
            'author': None,
            'date': None,
            'initials': None,
            'content': '',
            'parent_id': None
        }
        
        try:
            # استخراج ID
            comment_id = comment_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
            if comment_id:
                comment_info['id'] = comment_id
            
            # استخراج author
            author_elem = comment_elem.find('.//w:author', OOXML_NAMESPACES)
            if author_elem is not None and author_elem.text:
                comment_info['author'] = author_elem.text.strip()
            
            # استخراج date
            date_elem = comment_elem.find('.//w:date', OOXML_NAMESPACES)
            if date_elem is not None and date_elem.text:
                comment_info['date'] = date_elem.text.strip()
            
            # استخراج initials
            initials_elem = comment_elem.find('.//w:initials', OOXML_NAMESPACES)
            if initials_elem is not None and initials_elem.text:
                comment_info['initials'] = initials_elem.text.strip()
            
            # استخراج parent comment ID
            parent_id = comment_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}parentId')
            if parent_id:
                comment_info['parent_id'] = parent_id
            
            # استخراج محتوا
            paragraphs = comment_elem.findall('.//w:p', OOXML_NAMESPACES)
            content_parts = []
            
            for para in paragraphs:
                para_text = DocxUtils.extract_text_from_element(para)
                if para_text:
                    content_parts.append(para_text)
            
            if content_parts:
                comment_info['content'] = '\n'.join(content_parts)
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات کامنت: {str(e)}")
        
        return comment_info
    
    @staticmethod
    def extract_field_info(fldChar_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات فیلد از المان fldChar
        
        Args:
            fldChar_elem: المان fldChar
            
        Returns:
            Dict[str, Any]: اطلاعات فیلد
        """
        field_info = {
            'type': None,  # 'begin', 'separate', 'end', 'unknown'
            'field_type': None,  # 'PAGE', 'NUMPAGES', 'DATE', 'TIME', 'TOC', 'HYPERLINK', etc.
            'instructions': '',
            'result': ''
        }
        
        try:
            # استخراج نوع فیلد
            fld_char_type = fldChar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fldCharType')
            if fld_char_type:
                type_map = {
                    'begin': 'begin',
                    'separate': 'separate',
                    'end': 'end'
                }
                field_info['type'] = type_map.get(fld_char_type, 'unknown')
            
            # استخراج دستورات فیلد (از المان‌های run مجاور)
            parent = fldChar_elem.getparent()
            if parent is not None:
                # جستجوی المان‌های run در اطراف
                runs = parent.findall('.//w:r', OOXML_NAMESPACES)
                for run in runs:
                    # بررسی المان instrText (دستورات فیلد)
                    instr_elem = run.find('.//w:instrText', OOXML_NAMESPACES)
                    if instr_elem is not None and instr_elem.text:
                        instructions = instr_elem.text.strip()
                        field_info['instructions'] = instructions
                        
                        # تشخیص نوع فیلد از دستورات
                        if 'PAGE' in instructions:
                            field_info['field_type'] = 'PAGE'
                        elif 'NUMPAGES' in instructions:
                            field_info['field_type'] = 'NUMPAGES'
                        elif 'DATE' in instructions:
                            field_info['field_type'] = 'DATE'
                        elif 'TIME' in instructions:
                            field_info['field_type'] = 'TIME'
                        elif 'TOC' in instructions:
                            field_info['field_type'] = 'TOC'
                        elif 'HYPERLINK' in instructions:
                            field_info['field_type'] = 'HYPERLINK'
                        elif 'REF' in instructions:
                            field_info['field_type'] = 'REF'
                        elif 'SEQ' in instructions:
                            field_info['field_type'] = 'SEQ'
                    
                    # بررسی المان t (نتیجه فیلد)
                    text_elem = run.find('.//w:t', OOXML_NAMESPACES)
                    if text_elem is not None and text_elem.text:
                        result_text = text_elem.text.strip()
                        if result_text:
                            field_info['result'] = result_text
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات فیلد: {str(e)}")
        
        return field_info
    
    @staticmethod
    def extract_smart_tag_info(smartTag_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات Smart Tag از المان smartTag
        
        Args:
            smartTag_elem: المان smartTag
            
        Returns:
            Dict[str, Any]: اطلاعات Smart Tag
        """
        smart_tag_info = {
            'uri': None,
            'element': None,
            'content': ''
        }
        
        try:
            # استخراج URI و element
            uri_attr = smartTag_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}uri')
            element_attr = smartTag_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}element')
            
            if uri_attr:
                smart_tag_info['uri'] = uri_attr
            if element_attr:
                smart_tag_info['element'] = element_attr
            
            # استخراج محتوا
            content = DocxUtils.extract_text_from_element(smartTag_elem)
            if content:
                smart_tag_info['content'] = content
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات Smart Tag: {str(e)}")
        
        return smart_tag_info
    
    @staticmethod
    def extract_sdt_info(sdt_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات Structured Document Tag (کنترل‌های فرم)
        
        Args:
            sdt_elem: المان w:sdt
            
        Returns:
            Dict[str, Any]: اطلاعات SDT شامل:
                - type: نوع SDT (text, richText, comboBox, dropDownList, date, etc.)
                - tag: نام تگ
                - alias: نام نمایشی
                - lock: وضعیت قفل
                - placeholder: متن placeholder
                - content: محتوای فعلی
                - list_items: آیتم‌های لیست (برای comboBox و dropDownList)
                - date_format: فرمت تاریخ (برای date picker)
                - formatting: فرمت‌های اضافی
        """
        sdt_info = {
            'type': 'unknown',
            'tag': None,
            'alias': None,
            'lock': None,
            'placeholder': None,
            'content': None,
            'list_items': None,
            'date_format': None,
            'formatting': {}
        }
        
        try:
            # استخراج خصوصیات SDT
            sdtPr_elem = sdt_elem.find('.//w:sdtPr', OOXML_NAMESPACES)
            if sdtPr_elem is not None:
                # تعیین نوع SDT
                sdt_type = None
                
                # بررسی انواع مختلف SDT
                if sdtPr_elem.find('.//w:text', OOXML_NAMESPACES) is not None:
                    sdt_type = 'text'
                elif sdtPr_elem.find('.//w:richText', OOXML_NAMESPACES) is not None:
                    sdt_type = 'richText'
                elif sdtPr_elem.find('.//w:comboBox', OOXML_NAMESPACES) is not None:
                    sdt_type = 'comboBox'
                elif sdtPr_elem.find('.//w:dropDownList', OOXML_NAMESPACES) is not None:
                    sdt_type = 'dropDownList'
                elif sdtPr_elem.find('.//w:date', OOXML_NAMESPACES) is not None:
                    sdt_type = 'date'
                elif sdtPr_elem.find('.//w:checkBox', OOXML_NAMESPACES) is not None:
                    sdt_type = 'checkBox'
                elif sdtPr_elem.find('.//w:picture', OOXML_NAMESPACES) is not None:
                    sdt_type = 'picture'
                elif sdtPr_elem.find('.//w:group', OOXML_NAMESPACES) is not None:
                    sdt_type = 'group'
                elif sdtPr_elem.find('.//w:repeatingSection', OOXML_NAMESPACES) is not None:
                    sdt_type = 'repeatingSection'
                elif sdtPr_elem.find('.//w:repeatingSectionItem', OOXML_NAMESPACES) is not None:
                    sdt_type = 'repeatingSectionItem'
                elif sdtPr_elem.find('.//w:equation', OOXML_NAMESPACES) is not None:
                    sdt_type = 'equation'
                elif sdtPr_elem.find('.//w:bibliography', OOXML_NAMESPACES) is not None:
                    sdt_type = 'bibliography'
                elif sdtPr_elem.find('.//w:citation', OOXML_NAMESPACES) is not None:
                    sdt_type = 'citation'
                elif sdtPr_elem.find('.//w:docPartObj', OOXML_NAMESPACES) is not None:
                    sdt_type = 'docPartObj'
                
                if sdt_type:
                    sdt_info['type'] = sdt_type
                
                # استخراج تگ
                tag_elem = sdtPr_elem.find('.//w:tag', OOXML_NAMESPACES)
                if tag_elem is not None:
                    sdt_info['tag'] = tag_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                
                # استخراج alias
                alias_elem = sdtPr_elem.find('.//w:alias', OOXML_NAMESPACES)
                if alias_elem is not None:
                    sdt_info['alias'] = alias_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                
                # استخراج وضعیت قفل
                lock_elem = sdtPr_elem.find('.//w:lock', OOXML_NAMESPACES)
                if lock_elem is not None:
                    lock_val = lock_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    sdt_info['lock'] = lock_val if lock_val else 'sdtLocked'
                
                # استخراج placeholder
                placeholder_elem = sdtPr_elem.find('.//w:placeholder', OOXML_NAMESPACES)
                if placeholder_elem is not None:
                    docPart_elem = placeholder_elem.find('.//w:docPart', OOXML_NAMESPACES)
                    if docPart_elem is not None:
                        val_elem = docPart_elem.find('.//w:val', OOXML_NAMESPACES)
                        if val_elem is not None:
                            sdt_info['placeholder'] = val_elem.text
                
                # استخراج فرمت تاریخ (برای date picker)
                if sdt_info['type'] == 'date':
                    date_elem = sdtPr_elem.find('.//w:date', OOXML_NAMESPACES)
                    if date_elem is not None:
                        # استخراج فرمت تاریخ
                        date_format = date_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fullDate')
                        if date_format:
                            sdt_info['date_format'] = date_format
                        
                        # استخراج فرمت نمایش
                        display_format = date_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}dateFormat')
                        if display_format:
                            sdt_info['formatting']['display_format'] = display_format
                        
                        # استخراج زبان
                        lang = date_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}lid')
                        if lang:
                            sdt_info['formatting']['language'] = lang
                
                # استخراج فرمت‌های اضافی برای text و richText
                if sdt_info['type'] in ['text', 'richText']:
                    text_elem = sdtPr_elem.find('.//w:text', OOXML_NAMESPACES)
                    if text_elem is not None:
                        # استخراج فرمت multiline
                        multi_line = text_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}multiLine')
                        if multi_line:
                            sdt_info['formatting']['multi_line'] = multi_line == 'true' or multi_line == '1'
                        
                        # استخراج فرمت maxLength
                        max_length = text_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}maxLength')
                        if max_length:
                            sdt_info['formatting']['max_length'] = int(max_length)
                
                # استخراج وضعیت checkbox
                if sdt_info['type'] == 'checkBox':
                    checkBox_elem = sdtPr_elem.find('.//w:checkBox', OOXML_NAMESPACES)
                    if checkBox_elem is not None:
                        # استخراج وضعیت checked
                        checked_elem = checkBox_elem.find('.//w:checked', OOXML_NAMESPACES)
                        if checked_elem is not None:
                            checked_val = checked_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                            sdt_info['formatting']['checked'] = checked_val == 'true' or checked_val == '1' or checked_val == 'on'
                        
                        # استخراج اندازه
                        size_elem = checkBox_elem.find('.//w:size', OOXML_NAMESPACES)
                        if size_elem is not None:
                            size_val = size_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                            if size_val:
                                sdt_info['formatting']['size'] = int(size_val)
            
            # استخراج محتوا
            sdtContent_elem = sdt_elem.find('.//w:sdtContent', OOXML_NAMESPACES)
            if sdtContent_elem is not None:
                # استخراج متن از محتوا
                content = DocxUtils.extract_text_from_element(sdtContent_elem)
                if content:
                    sdt_info['content'] = content
                
                # برای comboBox و dropDownList، استخراج آیتم‌ها
                if sdt_info['type'] in ['comboBox', 'dropDownList']:
                    if sdtPr_elem is not None:
                        list_items = []
                        # یافتن آیتم‌های لیست
                        for listItem in sdtPr_elem.findall('.//w:listItem', OOXML_NAMESPACES):
                            item_display = listItem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}displayText')
                            item_value = listItem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}value')
                            if item_display or item_value:
                                list_items.append({
                                    'display': item_display,
                                    'value': item_value
                                })
                        if list_items:
                            sdt_info['list_items'] = list_items
                            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات SDT: {str(e)}")
        
        return sdt_info

    @staticmethod
    def extract_math_info(math_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات ریاضیات (OMML)
        
        Args:
            math_elem: المان ریاضیات (w:oMath یا w:oMathPara)
            
        Returns:
            Dict[str, Any]: اطلاعات ریاضیات شامل:
                - type: نوع (inline, paragraph)
                - latex: نمایش LaTeX (در صورت تبدیل موفق)
                - omml_xml: XML اصلی OMML
                - properties: خصوصیات فرمت‌بندی
        """
        math_info = {
            'type': 'inline',
            'latex': None,
            'omml_xml': None,
            'properties': {}
        }
        
        try:
            # تعیین نوع ریاضیات
            if math_elem.tag.endswith('oMathPara'):
                math_info['type'] = 'paragraph'
            
            # استخراج XML اصلی
            import xml.etree.ElementTree as ET
            math_info['omml_xml'] = ET.tostring(math_elem, encoding='unicode')
            
            # تبدیل OMML به LaTeX
            try:
                latex = DocxUtils.convert_omml_to_latex(math_elem)
                if latex:
                    math_info['latex'] = latex
            except Exception as e:
                import logging
                logging.getLogger(__name__).debug(f"خطا در تبدیل OMML به LaTeX: {str(e)}")
            
            # استخراج خصوصیات فرمت‌بندی
            mathPr_elem = math_elem.find('.//m:mathPr', OOXML_NAMESPACES)
            if mathPr_elem is not None:
                # استخراج justify
                justify_elem = mathPr_elem.find('.//m:jc', OOXML_NAMESPACES)
                if justify_elem is not None:
                    justify_val = justify_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if justify_val:
                        math_info['properties']['justify'] = justify_val
                
                # استخراج breakBin
                breakBin_elem = mathPr_elem.find('.//m:brkBin', OOXML_NAMESPACES)
                if breakBin_elem is not None:
                    breakBin_val = breakBin_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if breakBin_val:
                        math_info['properties']['break_bin'] = breakBin_val
                
                # استخراج breakBinSub
                breakBinSub_elem = mathPr_elem.find('.//m:brkBinSub', OOXML_NAMESPACES)
                if breakBinSub_elem is not None:
                    breakBinSub_val = breakBinSub_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if breakBinSub_val:
                        math_info['properties']['break_bin_sub'] = breakBinSub_val
                
                # استخراج smallFrac
                smallFrac_elem = mathPr_elem.find('.//m:smallFrac', OOXML_NAMESPACES)
                if smallFrac_elem is not None:
                    smallFrac_val = smallFrac_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if smallFrac_val:
                        math_info['properties']['small_frac'] = smallFrac_val == 'on'
                
                # استخراج dispDef
                dispDef_elem = mathPr_elem.find('.//m:dispDef', OOXML_NAMESPACES)
                if dispDef_elem is not None:
                    dispDef_val = dispDef_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if dispDef_val:
                        math_info['properties']['disp_def'] = dispDef_val == 'on'
                
                # استخراج lMargin
                lMargin_elem = mathPr_elem.find('.//m:lMargin', OOXML_NAMESPACES)
                if lMargin_elem is not None:
                    lMargin_val = lMargin_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if lMargin_val:
                        math_info['properties']['left_margin'] = int(lMargin_val)
                
                # استخراج rMargin
                rMargin_elem = mathPr_elem.find('.//m:rMargin', OOXML_NAMESPACES)
                if rMargin_elem is not None:
                    rMargin_val = rMargin_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if rMargin_val:
                        math_info['properties']['right_margin'] = int(rMargin_val)
                
                # استخراج defJc
                defJc_elem = mathPr_elem.find('.//m:defJc', OOXML_NAMESPACES)
                if defJc_elem is not None:
                    defJc_val = defJc_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if defJc_val:
                        math_info['properties']['default_justify'] = defJc_val
                
                # استخراج preSp
                preSp_elem = mathPr_elem.find('.//m:preSp', OOXML_NAMESPACES)
                if preSp_elem is not None:
                    preSp_val = preSp_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if preSp_val:
                        math_info['properties']['pre_spacing'] = int(preSp_val)
                
                # استخراج postSp
                postSp_elem = mathPr_elem.find('.//m:postSp', OOXML_NAMESPACES)
                if postSp_elem is not None:
                    postSp_val = postSp_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if postSp_val:
                        math_info['properties']['post_spacing'] = int(postSp_val)
                
                # استخراج interSp
                interSp_elem = mathPr_elem.find('.//m:interSp', OOXML_NAMESPACES)
                if interSp_elem is not None:
                    interSp_val = interSp_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if interSp_val:
                        math_info['properties']['inter_spacing'] = int(interSp_val)
                
                # استخراج intraSp
                intraSp_elem = mathPr_elem.find('.//m:intraSp', OOXML_NAMESPACES)
                if intraSp_elem is not None:
                    intraSp_val = intraSp_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if intraSp_val:
                        math_info['properties']['intra_spacing'] = int(intraSp_val)
                
                # استخراج wrapIndent
                wrapIndent_elem = mathPr_elem.find('.//m:wrapIndent', OOXML_NAMESPACES)
                if wrapIndent_elem is not None:
                    wrapIndent_val = wrapIndent_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if wrapIndent_val:
                        math_info['properties']['wrap_indent'] = int(wrapIndent_val)
                
                # استخراج wrapRight
                wrapRight_elem = mathPr_elem.find('.//m:wrapRight', OOXML_NAMESPACES)
                if wrapRight_elem is not None:
                    wrapRight_val = wrapRight_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if wrapRight_val:
                        math_info['properties']['wrap_right'] = wrapRight_val == 'on'
                
                # استخراج mathFont
                mathFont_elem = mathPr_elem.find('.//m:mathFont', OOXML_NAMESPACES)
                if mathFont_elem is not None:
                    mathFont_val = mathFont_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if mathFont_val:
                        math_info['properties']['math_font'] = mathFont_val
                
                # استخراج brkBin
                brkBin_elem = mathPr_elem.find('.//m:brkBin', OOXML_NAMESPACES)
                if brkBin_elem is not None:
                    brkBin_val = brkBin_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if brkBin_val:
                        math_info['properties']['break_bin'] = brkBin_val
                
                # استخراج brkBinSub
                brkBinSub_elem = mathPr_elem.find('.//m:brkBinSub', OOXML_NAMESPACES)
                if brkBinSub_elem is not None:
                    brkBinSub_val = brkBinSub_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if brkBinSub_val:
                        math_info['properties']['break_bin_sub'] = brkBinSub_val
                
                # استخراج smallFrac
                smallFrac_elem = mathPr_elem.find('.//m:smallFrac', OOXML_NAMESPACES)
                if smallFrac_elem is not None:
                    smallFrac_val = smallFrac_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if smallFrac_val:
                        math_info['properties']['small_frac'] = smallFrac_val == 'on'
                
                # استخراج dispDef
                dispDef_elem = mathPr_elem.find('.//m:dispDef', OOXML_NAMESPACES)
                if dispDef_elem is not None:
                    dispDef_val = dispDef_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if dispDef_val:
                        math_info['properties']['disp_def'] = dispDef_val == 'on'
                
                # استخراج lMargin
                lMargin_elem = mathPr_elem.find('.//m:lMargin', OOXML_NAMESPACES)
                if lMargin_elem is not None:
                    lMargin_val = lMargin_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if lMargin_val:
                        math_info['properties']['left_margin'] = int(lMargin_val)
                
                # استخراج rMargin
                rMargin_elem = mathPr_elem.find('.//m:rMargin', OOXML_NAMESPACES)
                if rMargin_elem is not None:
                    rMargin_val = rMargin_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if rMargin_val:
                        math_info['properties']['right_margin'] = int(rMargin_val)
                
                # استخراج defJc
                defJc_elem = mathPr_elem.find('.//m:defJc', OOXML_NAMESPACES)
                if defJc_elem is not None:
                    defJc_val = defJc_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if defJc_val:
                        math_info['properties']['default_justify'] = defJc_val
                
                # استخراج preSp
                preSp_elem = mathPr_elem.find('.//m:preSp', OOXML_NAMESPACES)
                if preSp_elem is not None:
                    preSp_val = preSp_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if preSp_val:
                        math_info['properties']['pre_spacing'] = int(preSp_val)
                
                # استخراج postSp
                postSp_elem = mathPr_elem.find('.//m:postSp', OOXML_NAMESPACES)
                if postSp_elem is not None:
                    postSp_val = postSp_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if postSp_val:
                        math_info['properties']['post_spacing'] = int(postSp_val)
                
                # استخراج interSp
                interSp_elem = mathPr_elem.find('.//m:interSp', OOXML_NAMESPACES)
                if interSp_elem is not None:
                    interSp_val = interSp_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if interSp_val:
                        math_info['properties']['inter_spacing'] = int(interSp_val)
                
                # استخراج intraSp
                intraSp_elem = mathPr_elem.find('.//m:intraSp', OOXML_NAMESPACES)
                if intraSp_elem is not None:
                    intraSp_val = intraSp_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if intraSp_val:
                        math_info['properties']['intra_spacing'] = int(intraSp_val)
                
                # استخراج wrapIndent
                wrapIndent_elem = mathPr_elem.find('.//m:wrapIndent', OOXML_NAMESPACES)
                if wrapIndent_elem is not None:
                    wrapIndent_val = wrapIndent_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if wrapIndent_val:
                        math_info['properties']['wrap_indent'] = int(wrapIndent_val)
                
                # استخراج wrapRight
                wrapRight_elem = mathPr_elem.find('.//m:wrapRight', OOXML_NAMESPACES)
                if wrapRight_elem is not None:
                    wrapRight_val = wrapRight_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if wrapRight_val:
                        math_info['properties']['wrap_right'] = wrapRight_val == 'on'
                
                # استخراج mathFont
                mathFont_elem = mathPr_elem.find('.//m:mathFont', OOXML_NAMESPACES)
                if mathFont_elem is not None:
                    mathFont_val = mathFont_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if mathFont_val:
                        math_info['properties']['math_font'] = mathFont_val
                        
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات ریاضیات: {str(e)}")
        
        return math_info
    
    @staticmethod
    def extract_drawing_info(drawing_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات Drawing (شامل تصاویر، اشکال، نمودارها)
        
        Args:
            drawing_elem: المان w:drawing
            
        Returns:
            Dict[str, Any]: اطلاعات Drawing شامل:
                - type: نوع (picture, shape, chart, diagram, etc.)
                - id: شناسه
                - name: نام
                - description: توضیحات
                - size: ابعاد (width, height)
                - position: موقعیت
                - properties: خصوصیات اضافی
        """
        drawing_info = {
            'type': 'unknown',
            'id': None,
            'name': None,
            'description': None,
            'size': {'width': 0, 'height': 0},
            'position': {'x': 0, 'y': 0},
            'properties': {}
        }
        
        try:
            # بررسی نوع Drawing
            # بررسی تصویر
            pic_elem = drawing_elem.find('.//pic:pic', OOXML_NAMESPACES)
            if pic_elem is not None:
                drawing_info['type'] = 'picture'
                
                # استخراج اطلاعات تصویر
                nvPicPr_elem = pic_elem.find('.//pic:nvPicPr', OOXML_NAMESPACES)
                if nvPicPr_elem is not None:
                    cNvPr_elem = nvPicPr_elem.find('.//pic:cNvPr', OOXML_NAMESPACES)
                    if cNvPr_elem is not None:
                        drawing_info['id'] = cNvPr_elem.get('id')
                        drawing_info['name'] = cNvPr_elem.get('name')
                        drawing_info['description'] = cNvPr_elem.get('descr')
                
                # استخراج ابعاد
                xfrm_elem = pic_elem.find('.//a:xfrm', OOXML_NAMESPACES)
                if xfrm_elem is not None:
                    ext_elem = xfrm_elem.find('.//a:ext', OOXML_NAMESPACES)
                    if ext_elem is not None:
                        width = ext_elem.get('cx')
                        height = ext_elem.get('cy')
                        if width:
                            drawing_info['size']['width'] = DocxUtils.convert_emu_to_pixels(width)
                        if height:
                            drawing_info['size']['height'] = DocxUtils.convert_emu_to_pixels(height)
            
            # بررسی shape
            elif drawing_elem.find('.//wps:wsp', OOXML_NAMESPACES) is not None:
                drawing_info['type'] = 'shape'
                
                # استخراج اطلاعات shape
                wsp_elem = drawing_elem.find('.//wps:wsp', OOXML_NAMESPACES)
                if wsp_elem is not None:
                    cNvPr_elem = wsp_elem.find('.//wp:cNvPr', OOXML_NAMESPACES)
                    if cNvPr_elem is not None:
                        drawing_info['id'] = cNvPr_elem.get('id')
                        drawing_info['name'] = cNvPr_elem.get('name')
                        drawing_info['description'] = cNvPr_elem.get('descr')
            
            # بررسی chart
            elif drawing_elem.find('.//c:chart', OOXML_NAMESPACES) is not None:
                drawing_info['type'] = 'chart'
                
                # استخراج اطلاعات chart
                chart_elem = drawing_elem.find('.//c:chart', OOXML_NAMESPACES)
                if chart_elem is not None:
                    drawing_info['id'] = chart_elem.get('{http://schemas.openxmlformats.org/drawingml/2006/chart}id')
            
            # بررسی diagram
            elif drawing_elem.find('.//dgm:relIds', OOXML_NAMESPACES) is not None:
                drawing_info['type'] = 'diagram'
            
            # استخراج موقعیت
            inline_elem = drawing_elem.find('.//wp:inline', OOXML_NAMESPACES)
            if inline_elem is not None:
                # استخراج موقعیت
                extent_elem = inline_elem.find('.//wp:extent', OOXML_NAMESPACES)
                if extent_elem is not None:
                    width = extent_elem.get('cx')
                    height = extent_elem.get('cy')
                    if width and not drawing_info['size']['width']:
                        drawing_info['size']['width'] = DocxUtils.convert_emu_to_pixels(width)
                    if height and not drawing_info['size']['height']:
                        drawing_info['size']['height'] = DocxUtils.convert_emu_to_pixels(height)
                
                # استخراج موقعیت نسبی
                docPr_elem = inline_elem.find('.//wp:docPr', OOXML_NAMESPACES)
                if docPr_elem is not None:
                    drawing_info['id'] = docPr_elem.get('id')
                    drawing_info['name'] = docPr_elem.get('name')
                    drawing_info['description'] = docPr_elem.get('descr')
            
            # استخراج موقعیت anchor
            anchor_elem = drawing_elem.find('.//wp:anchor', OOXML_NAMESPACES)
            if anchor_elem is not None:
                # استخراج موقعیت
                simplePos_elem = anchor_elem.find('.//wp:simplePos', OOXML_NAMESPACES)
                if simplePos_elem is not None:
                    x = simplePos_elem.get('x')
                    y = simplePos_elem.get('y')
                    if x:
                        drawing_info['position']['x'] = DocxUtils.convert_emu_to_pixels(x)
                    if y:
                        drawing_info['position']['y'] = DocxUtils.convert_emu_to_pixels(y)
                
                # استخراج موقعیت نسبی
                positionH_elem = anchor_elem.find('.//wp:positionH', OOXML_NAMESPACES)
                if positionH_elem is not None:
                    posOffset = positionH_elem.find('.//wp:posOffset', OOXML_NAMESPACES)
                    if posOffset is not None and posOffset.text:
                        drawing_info['position']['x'] = DocxUtils.convert_emu_to_pixels(posOffset.text)
                
                positionV_elem = anchor_elem.find('.//wp:positionV', OOXML_NAMESPACES)
                if positionV_elem is not None:
                    posOffset = positionV_elem.find('.//wp:posOffset', OOXML_NAMESPACES)
                    if posOffset is not None and posOffset.text:
                        drawing_info['position']['y'] = DocxUtils.convert_emu_to_pixels(posOffset.text)
                
                # استخراج ابعاد
                extent_elem = anchor_elem.find('.//wp:extent', OOXML_NAMESPACES)
                if extent_elem is not None:
                    width = extent_elem.get('cx')
                    height = extent_elem.get('cy')
                    if width and not drawing_info['size']['width']:
                        drawing_info['size']['width'] = DocxUtils.convert_emu_to_pixels(width)
                    if height and not drawing_info['size']['height']:
                        drawing_info['size']['height'] = DocxUtils.convert_emu_to_pixels(height)
                
                # استخراج اطلاعات docPr
                docPr_elem = anchor_elem.find('.//wp:docPr', OOXML_NAMESPACES)
                if docPr_elem is not None:
                    if not drawing_info['id']:
                        drawing_info['id'] = docPr_elem.get('id')
                    if not drawing_info['name']:
                        drawing_info['name'] = docPr_elem.get('name')
                    if not drawing_info['description']:
                        drawing_info['description'] = docPr_elem.get('descr')
                        
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات Drawing: {str(e)}")
        
        return drawing_info
    
    @staticmethod
    def extract_header_footer_info(part_xml: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات هدر و فوتر
        
        Args:
            part_xml: المان ریشه XML هدر یا فوتر
            
        Returns:
            Dict[str, Any]: اطلاعات هدر/فوتر شامل:
                - type: نوع (header, footer)
                - id: شناسه
                - content: محتوای متنی
                - paragraphs: تعداد پاراگراف‌ها
                - images: تعداد تصاویر
                - tables: تعداد جداول
                - fields: تعداد فیلدها
        """
        header_footer_info = {
            'type': 'unknown',
            'id': None,
            'content': '',
            'paragraphs': 0,
            'images': 0,
            'tables': 0,
            'fields': 0
        }
        
        try:
            # تعیین نوع بر اساس ریشه
            root_tag = part_xml.tag
            if 'header' in root_tag:
                header_footer_info['type'] = 'header'
            elif 'footer' in root_tag:
                header_footer_info['type'] = 'footer'
            
            # استخراج شناسه از نام فایل یا خصوصیت
            # (شناسه معمولاً در سطح فایل ZIP است)
            
            # استخراج محتوای متنی
            content = DocxUtils.extract_text_from_element(part_xml)
            if content:
                header_footer_info['content'] = content
            
            # شمارش پاراگراف‌ها
            paragraphs = part_xml.findall('.//w:p', OOXML_NAMESPACES)
            if paragraphs:
                header_footer_info['paragraphs'] = len(paragraphs)
            
            # شمارش تصاویر
            drawings = part_xml.findall('.//w:drawing', OOXML_NAMESPACES)
            if drawings:
                header_footer_info['images'] = len(drawings)
            
            # شمارش جداول
            tables = part_xml.findall('.//w:tbl', OOXML_NAMESPACES)
            if tables:
                header_footer_info['tables'] = len(tables)
            
            # شمارش فیلدها
            fields = part_xml.findall('.//w:fldChar', OOXML_NAMESPACES)
            if fields:
                header_footer_info['fields'] = len(fields)
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات هدر/فوتر: {str(e)}")
        
        return header_footer_info
    
    @staticmethod
    def extract_section_properties(sectPr_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج خصوصیات بخش (Section)
        
        Args:
            sectPr_elem: المان w:sectPr
            
        Returns:
            Dict[str, Any]: اطلاعات بخش شامل:
                - page_size: ابعاد صفحه (width, height)
                - page_margins: حاشیه‌ها (top, right, bottom, left, header, footer, gutter)
                - page_orientation: جهت صفحه (portrait, landscape)
                - page_numbering: شماره‌گذاری صفحه
                - columns: ستون‌ها (count, spacing)
                - header_references: ارجاعات به هدرها
                - footer_references: ارجاعات به فوترها
                - line_numbers: شماره‌گذاری خطوط
                - text_direction: جهت متن
        """
        section_info = {
            'page_size': {'width': 0, 'height': 0},
            'page_margins': {
                'top': 0, 'right': 0, 'bottom': 0, 'left': 0,
                'header': 0, 'footer': 0, 'gutter': 0
            },
            'page_orientation': 'portrait',
            'page_numbering': None,
            'columns': {'count': 1, 'spacing': 0, 'equal_width': True},
            'header_references': [],
            'footer_references': [],
            'line_numbers': None,
            'text_direction': 'lrTb'
        }
        
        try:
            # استخراج ابعاد صفحه
            pgSz_elem = sectPr_elem.find('.//w:pgSz', OOXML_NAMESPACES)
            if pgSz_elem is not None:
                width = pgSz_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')
                height = pgSz_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}h')
                orient = pgSz_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}orient')
                
                if width:
                    section_info['page_size']['width'] = DocxUtils.convert_twips_to_points(width)
                if height:
                    section_info['page_size']['height'] = DocxUtils.convert_twips_to_points(height)
                if orient:
                    section_info['page_orientation'] = orient
            
            # استخراج حاشیه‌های صفحه
            pgMar_elem = sectPr_elem.find('.//w:pgMar', OOXML_NAMESPACES)
            if pgMar_elem is not None:
                top = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}top')
                right = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}right')
                bottom = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}bottom')
                left = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}left')
                header = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}header')
                footer = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}footer')
                gutter = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}gutter')
                
                if top:
                    section_info['page_margins']['top'] = DocxUtils.convert_twips_to_points(top)
                if right:
                    section_info['page_margins']['right'] = DocxUtils.convert_twips_to_points(right)
                if bottom:
                    section_info['page_margins']['bottom'] = DocxUtils.convert_twips_to_points(bottom)
                if left:
                    section_info['page_margins']['left'] = DocxUtils.convert_twips_to_points(left)
                if header:
                    section_info['page_margins']['header'] = DocxUtils.convert_twips_to_points(header)
                if footer:
                    section_info['page_margins']['footer'] = DocxUtils.convert_twips_to_points(footer)
                if gutter:
                    section_info['page_margins']['gutter'] = DocxUtils.convert_twips_to_points(gutter)
            
            # استخراج ستون‌ها
            cols_elem = sectPr_elem.find('.//w:cols', OOXML_NAMESPACES)
            if cols_elem is not None:
                count = cols_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}num')
                spacing = cols_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}space')
                equal_width = cols_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}equalWidth')
                
                if count:
                    section_info['columns']['count'] = int(count)
                if spacing:
                    section_info['columns']['spacing'] = DocxUtils.convert_twips_to_points(spacing)
                if equal_width:
                    section_info['columns']['equal_width'] = equal_width == '1' or equal_width == 'true'
            
            # استخراج ارجاعات به هدرها
            header_refs = sectPr_elem.findall('.//w:headerReference', OOXML_NAMESPACES)
            for ref in header_refs:
                ref_type = ref.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
                ref_id = ref.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                if ref_type and ref_id:
                    section_info['header_references'].append({
                        'type': ref_type,
                        'id': ref_id
                    })
            
            # استخراج ارجاعات به فوترها
            footer_refs = sectPr_elem.findall('.//w:footerReference', OOXML_NAMESPACES)
            for ref in footer_refs:
                ref_type = ref.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
                ref_id = ref.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                if ref_type and ref_id:
                    section_info['footer_references'].append({
                        'type': ref_type,
                        'id': ref_id
                    })
            
            # استخراج شماره‌گذاری صفحه
            pgNumType_elem = sectPr_elem.find('.//w:pgNumType', OOXML_NAMESPACES)
            if pgNumType_elem is not None:
                page_numbering = {}
                
                # استخراج فرمت شماره صفحه
                fmt = pgNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fmt')
                if fmt:
                    page_numbering['format'] = fmt
                
                # استخراج شماره شروع
                start = pgNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}start')
                if start:
                    page_numbering['start'] = int(start)
                
                # استخراج فصل
                chapSep = pgNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}chapSep')
                if chapSep:
                    page_numbering['chapter_separator'] = chapSep
                
                # استخراج سبک فصل
                chapStyle = pgNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}chapStyle')
                if chapStyle:
                    page_numbering['chapter_style'] = chapStyle
                
                if page_numbering:
                    section_info['page_numbering'] = page_numbering
            
            # استخراج شماره‌گذاری خطوط
            lnNumType_elem = sectPr_elem.find('.//w:lnNumType', OOXML_NAMESPACES)
            if lnNumType_elem is not None:
                line_numbers = {}
                
                # استخراج شماره شروع
                start = lnNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}start')
                if start:
                    line_numbers['start'] = int(start)
                
                # استخراج شمارش
                countBy = lnNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}countBy')
                if countBy:
                    line_numbers['count_by'] = int(countBy)
                
                # استخراج فاصله
                distance = lnNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}distance')
                if distance:
                    line_numbers['distance'] = DocxUtils.convert_twips_to_points(distance)
                
                # استخراج restart
                restart = lnNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}restart')
                if restart:
                    line_numbers['restart'] = restart
                
                if line_numbers:
                    section_info['line_numbers'] = line_numbers
            
            # استخراج جهت متن
            textDirection_elem = sectPr_elem.find('.//w:textDirection', OOXML_NAMESPACES)
            if textDirection_elem is not None:
                direction = textDirection_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if direction:
                    section_info['text_direction'] = direction
            
            # استخراج نوع کاغذ
            paperSrc_elem = sectPr_elem.find('.//w:paperSrc', OOXML_NAMESPACES)
            if paperSrc_elem is not None:
                paper_info = {}
                
                # استخراج منبع کاغذ اول
                first = paperSrc_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}first')
                if first:
                    paper_info['first'] = first
                
                # استخراج منبع کاغذ دیگر
                other = paperSrc_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}other')
                if other:
                    paper_info['other'] = other
                
                if paper_info:
                    section_info['paper_source'] = paper_info
            
            # استخراج فواصل عمودی صفحه
            pgBorders_elem = sectPr_elem.find('.//w:pgBorders', OOXML_NAMESPACES)
            if pgBorders_elem is not None:
                page_borders = {}
                
                # استخراج offsetFrom
                offsetFrom = pgBorders_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}offsetFrom')
                if offsetFrom:
                    page_borders['offset_from'] = offsetFrom
                
                # استخراج borderهای مختلف
                borders = {}
                for border_type in ['top', 'left', 'bottom', 'right']:
                    border_elem = pgBorders_elem.find(f'.//w:{border_type}', OOXML_NAMESPACES)
                    if border_elem is not None:
                        border_info = {}
                        
                        # استخراج رنگ
                        color = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color')
                        if color:
                            border_info['color'] = DocxUtils.convert_color_from_ooxml(color)
                        
                        # استخراج space
                        space = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}space')
                        if space:
                            border_info['space'] = int(space)
                        
                        # استخراج sz
                        sz = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz')
                        if sz:
                            border_info['size'] = int(sz)
                        
                        # استخراج val
                        val = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if val:
                            border_info['type'] = val
                        
                        borders[border_type] = border_info
                
                if borders:
                    page_borders['borders'] = borders
                
                if page_borders:
                    section_info['page_borders'] = page_borders
            
            # استخراج فرمت صفحه
            formProt_elem = sectPr_elem.find('.//w:formProt', OOXML_NAMESPACES)
            if formProt_elem is not None:
                form_prot = formProt_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if form_prot:
                    section_info['form_protection'] = form_prot == 'true' or form_prot == '1'
            
            # استخراج vertical alignment
            vAlign_elem = sectPr_elem.find('.//w:vAlign', OOXML_NAMESPACES)
            if vAlign_elem is not None:
                v_align = vAlign_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if v_align:
                    section_info['vertical_alignment'] = v_align
            
            # استخراج noEndnote
            noEndnote_elem = sectPr_elem.find('.//w:noEndnote', OOXML_NAMESPACES)
            if noEndnote_elem is not None:
                section_info['no_endnote'] = True
            
            # استخراج titlePg
            titlePg_elem = sectPr_elem.find('.//w:titlePg', OOXML_NAMESPACES)
            if titlePg_elem is not None:
                section_info['title_page'] = True
            
            # استخراج textboxTightWrap
            textboxTightWrap_elem = sectPr_elem.find('.//w:textboxTightWrap', OOXML_NAMESPACES)
            if textboxTightWrap_elem is not None:
                tight_wrap = textboxTightWrap_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if tight_wrap:
                    section_info['textbox_tight_wrap'] = tight_wrap
            
            # استخراج docGrid
            docGrid_elem = sectPr_elem.find('.//w:docGrid', OOXML_NAMESPACES)
            if docGrid_elem is not None:
                doc_grid = {}
                
                # استخراج type
                grid_type = docGrid_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
                if grid_type:
                    doc_grid['type'] = grid_type
                
                # استخراج linePitch
                line_pitch = docGrid_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}linePitch')
                if line_pitch:
                    doc_grid['line_pitch'] = int(line_pitch)
                
                # استخراج charSpace
                char_space = docGrid_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}charSpace')
                if char_space:
                    doc_grid['char_space'] = int(char_space)
                
                if doc_grid:
                    section_info['doc_grid'] = doc_grid
                    
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج خصوصیات بخش: {str(e)}")
        
        return section_info
    
    @staticmethod
    def extract_page_break_info(br_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات شکست صفحه
        
        Args:
            br_elem: المان w:br
            
        Returns:
            Dict[str, Any]: اطلاعات شکست صفحه شامل:
                - type: نوع (page, column, textWrapping)
                - clear: نوع clear (برای textWrapping)
                - location: موقعیت (before, after)
        """
        page_break_info = {
            'type': 'textWrapping',
            'clear': None,
            'location': 'after'
        }
        
        try:
            # بررسی نوع break
            br_type = br_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
            if br_type:
                if br_type == 'page':
                    page_break_info['type'] = 'page'
                elif br_type == 'column':
                    page_break_info['type'] = 'column'
                elif br_type == 'textWrapping':
                    page_break_info['type'] = 'textWrapping'
            
            # بررسی clear (برای textWrapping)
            if page_break_info['type'] == 'textWrapping':
                clear = br_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}clear')
                if clear:
                    page_break_info['clear'] = clear
            
            # تعیین موقعیت (بر اساس المان والد)
            parent = br_elem.getparent()
            if parent is not None:
                # اگر break در ابتدای پاراگراف باشد
                if parent.tag.endswith('p'):
                    # بررسی موقعیت در پاراگراف
                    index = list(parent).index(br_elem)
                    if index == 0:
                        page_break_info['location'] = 'before'
                    else:
                        page_break_info['location'] = 'after'
                        
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات شکست صفحه: {str(e)}")
        
        return page_break_info
    
    @staticmethod
    def extract_column_break_info(br_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات شکست ستون
        
        Args:
            br_elem: المان w:br با type='column'
            
        Returns:
            Dict[str, Any]: اطلاعات شکست ستون شامل:
                - type: همیشه 'column'
                - location: موقعیت (before, after)
        """
        column_break_info = {
            'type': 'column',
            'location': 'after'
        }
        
        try:
            # تعیین موقعیت (بر اساس المان والد)
            parent = br_elem.getparent()
            if parent is not None:
                # اگر break در ابتدای پاراگراف باشد
                if parent.tag.endswith('p'):
                    # بررسی موقعیت در پاراگراف
                    index = list(parent).index(br_elem)
                    if index == 0:
                        column_break_info['location'] = 'before'
                    else:
                        column_break_info['location'] = 'after'
                        
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات شکست ستون: {str(e)}")
        
        return column_break_info
    
    @staticmethod
    def extract_line_break_info(br_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات شکست خط
        
        Args:
            br_elem: المان w:br با type='textWrapping'
            
        Returns:
            Dict[str, Any]: اطلاعات شکست خط شامل:
                - type: همیشه 'textWrapping'
                - clear: نوع clear (all, left, right, none)
                - location: موقعیت (before, after)
        """
        line_break_info = {
            'type': 'textWrapping',
            'clear': 'none',
            'location': 'after'
        }
        
        try:
            # استخراج clear
            clear = br_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}clear')
            if clear:
                line_break_info['clear'] = clear
            
            # تعیین موقعیت (بر اساس المان والد)
            parent = br_elem.getparent()
            if parent is not None:
                # اگر break در ابتدای پاراگراف باشد
                if parent.tag.endswith('p'):
                    # بررسی موقعیت در پاراگراف
                    index = list(parent).index(br_elem)
                    if index == 0:
                        line_break_info['location'] = 'before'
                    else:
                        line_break_info['location'] = 'after'
                        
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات شکست خط: {str(e)}")
        
        return line_break_info
    
    @staticmethod
    def extract_tab_info(tab_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات تب (Tab)
        
        Args:
            tab_elem: المان w:tab
            
        Returns:
            Dict[str, Any]: اطلاعات تب شامل:
                - type: نوع تب (left, center, right, decimal, bar, clear, leader)
                - leader: کاراکتر leader
                - position: موقعیت (بر حسب points)
        """
        tab_info = {
            'type': 'left',
            'leader': None,
            'position': 0
        }
        
        try:
            # استخراج خصوصیات تب از المان والد (w:tabs)
            parent = tab_elem.getparent()
            if parent is not None and parent.tag.endswith('tabs'):
                # یافتن تعریف تب مربوطه
                for tab_stop in parent.findall('.//w:tab', OOXML_NAMESPACES):
                    # بررسی بر اساس موقعیت (اگر وجود داشته باشد)
                    pos = tab_stop.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pos')
                    if pos:
                        tab_info['position'] = DocxUtils.convert_twips_to_points(pos)
                    
                    # استخراج نوع
                    tab_type = tab_stop.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if tab_type:
                        tab_info['type'] = tab_type
                    
                    # استخراج leader
                    leader = tab_stop.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}leader')
                    if leader:
                        tab_info['leader'] = leader
                    break
                        
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات تب: {str(e)}")
        
        return tab_info
    
    @staticmethod
    def extract_sym_info(sym_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات نماد (Symbol)
        
        Args:
            sym_elem: المان w:sym
            
        Returns:
            Dict[str, Any]: اطلاعات نماد شامل:
                - font: فونت نماد
                - char: کاراکتر نماد (کد یونیکد)
                - unicode: نمایش یونیکد
        """
        sym_info = {
            'font': None,
            'char': None,
            'unicode': None
        }
        
        try:
            # استخراج فونت
            font = sym_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}font')
            if font:
                sym_info['font'] = font
            
            # استخراج کاراکتر
            char = sym_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}char')
            if char:
                sym_info['char'] = char
                # تبدیل به یونیکد
                try:
                    # کاراکتر به صورت هگزادسیمال است
                    if char.startswith('0x') or char.startswith('0X'):
                        char_code = int(char, 16)
                    else:
                        char_code = int(char)
                    sym_info['unicode'] = chr(char_code)
                except (ValueError, OverflowError):
                    sym_info['unicode'] = char
                        
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات نماد: {str(e)}")
        
        return sym_info
    
    @staticmethod
    def extract_fld_char_info(fldChar_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات کاراکتر فیلد
        
        Args:
            fldChar_elem: المان w:fldChar
            
        Returns:
            Dict[str, Any]: اطلاعات کاراکتر فیلد شامل:
                - type: نوع (begin, separate, end)
                - dirty: وضعیت dirty
                - fldLock: وضعیت قفل
                - instrText: متن دستور فیلد
        """
        fld_char_info = {
            'type': None,
            'dirty': False,
            'fldLock': False,
            'instrText': None
        }
        
        try:
            # استخراج نوع
            fld_char_type = fldChar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fldCharType')
            if fld_char_type:
                fld_char_info['type'] = fld_char_type
            
            # استخراج dirty
            dirty = fldChar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}dirty')
            if dirty:
                fld_char_info['dirty'] = dirty == 'true' or dirty == '1'
            
            # استخراج fldLock
            fld_lock = fldChar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fldLock')
            if fld_lock:
                fld_char_info['fldLock'] = fld_lock == 'true' or fld_lock == '1'
            
            # استخراج متن دستور (از المان‌های مجاور)
            parent = fldChar_elem.getparent()
            if parent is not None:
                # جستجوی المان w:instrText در همان سطح
                for sibling in parent:
                    if sibling.tag.endswith('instrText'):
                        fld_char_info['instrText'] = sibling.text
                        break
                        
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات کاراکتر فیلد: {str(e)}")
        
        return fld_char_info
    
    @staticmethod
    def extract_soft_hyphen_info(hyphen_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات هایفن نرم
        
        Args:
            hyphen_elem: المان w:softHyphen یا w:noBreakHyphen
            
        Returns:
            Dict[str, Any]: اطلاعات هایفن شامل:
                - type: نوع (softHyphen, noBreakHyphen)
                - char: کاراکتر هایفن
        """
        hyphen_info = {
            'type': 'softHyphen',
            'char': '­'  # کاراکتر هایفن نرم (U+00AD)
        }
        
        try:
            # تعیین نوع
            if hyphen_elem.tag.endswith('noBreakHyphen'):
                hyphen_info['type'] = 'noBreakHyphen'
                hyphen_info['char'] = '‑'  # کاراکتر هایفن غیرشکستنی (U+2011)
                        
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات هایفن: {str(e)}")
        
        return hyphen_info
    
    @staticmethod
    def extract_year_short_info(year_short_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات سال کوتاه (Year Short)
        
        Args:
            year_short_elem: المان w:yearShort
            
        Returns:
            Dict[str, Any]: اطلاعات سال کوتاه شامل:
                - type: همیشه 'yearShort'
                - format: فرمت نمایش
                - value: مقدار سال
        """
        year_short_info = {
            'type': 'yearShort',
            'format': 'yy',
            'value': None
        }
        
        try:
            # استخراج خصوصیات از المان
            # در DOCX، yearShort معمولاً به صورت متن ساده است
            # اما ممکن است خصوصیات فرمت داشته باشد
            parent = year_short_elem.getparent()
            if parent is not None:
                # بررسی المان‌های مرتبط برای فرمت
                for sibling in parent:
                    if sibling.tag.endswith('fldChar'):
                        # اگر فیلد DATE باشد
                        fld_char_info = DocxUtils.extract_fld_char_info(sibling)
                        if fld_char_info.get('instrText') and 'DATE' in fld_char_info['instrText']:
                            # استخراج فرمت از دستور فیلد
                            instr_text = fld_char_info['instrText']
                            if '\\@' in instr_text:
                                # استخراج فرمت
                                format_part = instr_text.split('\\@')[1].strip().strip('"\'')
                                if 'yyyy' in format_part:
                                    year_short_info['format'] = 'yyyy'
                                elif 'yy' in format_part:
                                    year_short_info['format'] = 'yy'
                            break
            
            # مقدار سال (از متن المان)
            if year_short_elem.text:
                year_short_info['value'] = year_short_elem.text
                        
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات سال کوتاه: {str(e)}")
        
        return year_short_info
    
    @staticmethod
    def extract_month_short_info(month_short_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات ماه کوتاه (Month Short)
        
        Args:
            month_short_elem: المان w:monthShort
            
        Returns:
            Dict[str, Any]: اطلاعات ماه کوتاه شامل:
                - type: همیشه 'monthShort'
                - format: فرمت نمایش
                - value: مقدار ماه
        """
        month_short_info = {
            'type': 'monthShort',
            'format': 'M',
            'value': None
        }
        
        try:
            # استخراج خصوصیات از المان
            parent = month_short_elem.getparent()
            if parent is not None:
                # بررسی المان‌های مرتبط برای فرمت
                for sibling in parent:
                    if sibling.tag.endswith('fldChar'):
                        # اگر فیلد DATE باشد
                        fld_char_info = DocxUtils.extract_fld_char_info(sibling)
                        if fld_char_info.get('instrText') and 'DATE' in fld_char_info['instrText']:
                            # استخراج فرمت از دستور فیلد
                            instr_text = fld_char_info['instrText']
                            if '\\@' in instr_text:
                                # استخراج فرمت
                                format_part = instr_text.split('\\@')[1].strip().strip('"\'')
                                if 'MMMM' in format_part:
                                    month_short_info['format'] = 'MMMM'  # نام کامل ماه
                                elif 'MMM' in format_part:
                                    month_short_info['format'] = 'MMM'  # نام کوتاه ماه
                                elif 'MM' in format_part:
                                    month_short_info['format'] = 'MM'  # ماه دو رقمی
                                elif 'M' in format_part:
                                    month_short_info['format'] = 'M'  # ماه یک یا دو رقمی
                            break
            
            # مقدار ماه (از متن المان)
            if month_short_elem.text:
                month_short_info['value'] = month_short_elem.text
                        
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات ماه کوتاه: {str(e)}")
        
        return month_short_info
    
    @staticmethod
    def extract_day_short_info(day_short_elem: ET.Element) -> Dict[str, Any]:
        """
        استخراج اطلاعات روز کوتاه (Day Short)
        
        Args:
            day_short_elem: المان w:dayShort
            
        Returns:
            Dict[str, Any]: اطلاعات روز کوتاه شامل:
                - type: همیشه 'dayShort'
                - format: فرمت نمایش
                - value: مقدار روز
        """
        day_short_info = {
            'type': 'dayShort',
            'format': 'd',
            'value': None
        }
        
        try:
            # استخراج خصوصیات از المان
            parent = day_short_elem.getparent()
            if parent is not None:
                # بررسی المان‌های مرتبط برای فرمت
                for sibling in parent:
                    if sibling.tag.endswith('fldChar'):
                        # اگر فیلد DATE باشد
                        fld_char_info = DocxUtils.extract_fld_char_info(sibling)
                        if fld_char_info.get('instrText') and 'DATE' in fld_char_info['instrText']:
                            # استخراج فرمت از دستور فیلد
                            instr_text = fld_char_info['instrText']
                            if '\\@' in instr_text:
                                # استخراج فرمت
                                format_part = instr_text.split('\\@')[1].strip().strip('"\'')
                                if 'dddd' in format_part:
                                    day_short_info['format'] = 'dddd'  # نام کامل روز
                                elif 'ddd' in format_part:
                                    day_short_info['format'] = 'ddd'  # نام کوتاه روز
                                elif 'dd' in format_part:
                                    day_short_info['format'] = 'dd'  # روز دو رقمی
                                elif 'd' in format_part:
                                    day_short_info['format'] = 'd'  # روز یک یا دو رقمی
                            break
            
            # مقدار روز (از متن المان)
            if day_short_elem.text:
                day_short_info['value'] = day_short_elem.text
                        
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات روز کوتاه: {str(e)}")
        
        return day_short_info








# Add these to docx_utils.py (at the end of the DocxUtils class, before the final closing)

# Also add these module-level helper functions at the top after imports:

# Namespace dictionary for easy access
NS = OOXML_NAMESPACES


def safe_find(element: Optional[ET.Element], tag: str, namespaces: Optional[Dict[str, str]] = None) -> Optional[ET.Element]:
    """
    Safely find a single child element.
    
    Args:
        element: Parent element or None
        tag: Tag to search for (can include namespace prefix like 'w:p')
        namespaces: Optional namespace mapping dictionary
        
    Returns:
        Found element or None
    """
    if element is None:
        return None
    
    if namespaces:
        # Handle tag with namespace prefix
        if ':' in tag:
            prefix, local_name = tag.split(':', 1)
            ns_uri = namespaces.get(prefix, '')
            if ns_uri:
                tag = f'{{{ns_uri}}}{local_name}'
        
        return element.find(tag, namespaces)
    else:
        return element.find(tag)


def safe_findall(element: Optional[ET.Element], tag: str, namespaces: Optional[Dict[str, str]] = None) -> List[ET.Element]:
    """
    Safely find all child elements matching tag.
    
    Args:
        element: Parent element or None
        tag: Tag to search for (can include namespace prefix like 'w:p')
        namespaces: Optional namespace mapping dictionary
        
    Returns:
        List of found elements (empty list if none found or element is None)
    """
    if element is None:
        return []
    
    if namespaces:
        # Handle tag with namespace prefix
        if ':' in tag:
            prefix, local_name = tag.split(':', 1)
            ns_uri = namespaces.get(prefix, '')
            if ns_uri:
                tag = f'{{{ns_uri}}}{local_name}'
        
        return element.findall(tag, namespaces)
    else:
        return element.findall(tag)


def get_element_text(element: Optional[ET.Element], tag: Optional[str] = None, namespaces: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Get text content from an element or its child.
    
    Args:
        element: Parent element or None
        tag: Optional child tag to find first
        namespaces: Optional namespace mapping
        
    Returns:
        Text content or None
    """
    if element is None:
        return None
    
    target = element
    if tag:
        target = safe_find(element, tag, namespaces)
    
    if target is None:
        return None
    
    if target.text:
        return target.text.strip()
    
    return None


def xml_to_text(element: ET.Element, include_tail: bool = True) -> str:
    """
    Extract all text from an XML element recursively.
    
    Args:
        element: XML element
        include_tail: Whether to include tail text of children
        
    Returns:
        Concatenated text content
    """
    if element is None:
        return ""
    
    texts = []
    
    if element.text:
        texts.append(element.text)
    
    for child in element:
        texts.append(xml_to_text(child, include_tail))
        if include_tail and child.tail:
            texts.append(child.tail)
    
    if not include_tail and element.tail:
        texts.append(element.tail)
    
    return ''.join(texts)


def parse_dxa_to_points(value: Optional[Union[str, int, float]]) -> Optional[float]:
    """
    Convert DXA (twentieths of a point) to points.
    
    Args:
        value: DXA value as string, int, or float
        
    Returns:
        Value in points or None
    """
    if value is None:
        return None
    
    try:
        dxa = float(value) if isinstance(value, str) else float(value)
        return dxa / 20.0  # 1 DXA = 1/20 point
    except (ValueError, TypeError):
        return None


def parse_emu_to_pixels(value: Optional[Union[str, int, float]], dpi: int = 96) -> Optional[float]:
    """
    Convert EMU (English Metric Units) to pixels.
    
    Args:
        value: EMU value as string, int, or float
        dpi: Dots per inch (default 96)
        
    Returns:
        Value in pixels or None
    """
    if value is None:
        return None
    
    try:
        emu = float(value) if isinstance(value, str) else float(value)
        # 1 EMU = 1/914400 inch
        inches = emu / 914400.0
        return inches * dpi
    except (ValueError, TypeError):
        return None


def parse_border_element(border_elem: ET.Element) -> Dict[str, Any]:
    """
    Parse a Word border element (w:top, w:bottom, etc.).
    
    Args:
        border_elem: Border XML element
        
    Returns:
        Dictionary with border properties
    """
    border_info = {}
    
    if border_elem is None:
        return border_info
    
    # Border style
    val = border_elem.get(f'{{{NS["w"]}}}val')
    if val:
        border_info['style'] = val
    
    # Border color
    color = border_elem.get(f'{{{NS["w"]}}}color')
    if color:
        border_info['color'] = f"#{color}" if not color.startswith('#') else color
    
    # Border width (in eighths of a point)
    sz = border_elem.get(f'{{{NS["w"]}}}sz')
    if sz:
        try:
            border_info['width'] = float(sz) / 8.0  # Convert to points
        except ValueError:
            border_info['width'] = sz
    
    # Space between border and content
    space = border_elem.get(f'{{{NS["w"]}}}space')
    if space:
        try:
            border_info['space'] = float(space)
        except ValueError:
            border_info['space'] = space
    
    # Theme color
    theme_color = border_elem.get(f'{{{NS["w"]}}}themeColor')
    if theme_color:
        border_info['theme_color'] = theme_color
    
    # Theme tint/shade
    theme_tint = border_elem.get(f'{{{NS["w"]}}}themeTint')
    if theme_tint:
        border_info['theme_tint'] = theme_tint
    
    theme_shade = border_elem.get(f'{{{NS["w"]}}}themeShade')
    if theme_shade:
        border_info['theme_shade'] = theme_shade
    
    return border_info


def parse_shading_element(shading_elem: ET.Element) -> Dict[str, Any]:
    """
    Parse a Word shading element (w:shd).
    
    Args:
        shading_elem: Shading XML element
        
    Returns:
        Dictionary with shading properties
    """
    shading_info = {}
    
    if shading_elem is None:
        return shading_info
    
    # Fill color
    fill = shading_elem.get(f'{{{NS["w"]}}}fill')
    if fill:
        shading_info['fill'] = f"#{fill}" if not fill.startswith('#') else fill
    
    # Pattern type
    val = shading_elem.get(f'{{{NS["w"]}}}val')
    if val:
        shading_info['pattern'] = val
    
    # Pattern color
    color = shading_elem.get(f'{{{NS["w"]}}}color')
    if color:
        shading_info['color'] = f"#{color}" if not color.startswith('#') else color
    
    # Theme fill
    theme_fill = shading_elem.get(f'{{{NS["w"]}}}themeFill')
    if theme_fill:
        shading_info['theme_fill'] = theme_fill
    
    # Theme fill tint/shade
    theme_fill_tint = shading_elem.get(f'{{{NS["w"]}}}themeFillTint')
    if theme_fill_tint:
        shading_info['theme_fill_tint'] = theme_fill_tint
    
    theme_fill_shade = shading_elem.get(f'{{{NS["w"]}}}themeFillShade')
    if theme_fill_shade:
        shading_info['theme_fill_shade'] = theme_fill_shade
    
    # Theme color
    theme_color = shading_elem.get(f'{{{NS["w"]}}}themeColor')
    if theme_color:
        shading_info['theme_color'] = theme_color
    
    # Theme tint/shade
    theme_tint = shading_elem.get(f'{{{NS["w"]}}}themeTint')
    if theme_tint:
        shading_info['theme_tint'] = theme_tint
    
    theme_shade = shading_elem.get(f'{{{NS["w"]}}}themeShade')
    if theme_shade:
        shading_info['theme_shade'] = theme_shade
    
    return shading_info


def get_attribute(element: ET.Element, attr_name: str, namespace: str = 'w') -> Optional[str]:
    """
    Safely get an attribute value from an element with namespace.
    
    Args:
        element: XML element
        attr_name: Attribute name
        namespace: Namespace prefix (default 'w')
        
    Returns:
        Attribute value or None
    """
    if element is None:
        return None
    
    ns_uri = NS.get(namespace, '')
    if ns_uri:
        return element.get(f'{{{ns_uri}}}{attr_name}')
    else:
        return element.get(attr_name)


def extract_text_from_run(run_elem: ET.Element) -> str:
    """
    Extract text from a Word run element (w:r).
    
    Args:
        run_elem: Run XML element
        
    Returns:
        Extracted text
    """
    if run_elem is None:
        return ""
    
    texts = []
    
    for t_elem in safe_findall(run_elem, './/w:t'):
        if t_elem.text:
            texts.append(t_elem.text)
    
    # Handle special characters
    for cr_elem in safe_findall(run_elem, './/w:cr'):
        texts.append('\n')
    
    for br_elem in safe_findall(run_elem, './/w:br'):
        texts.append('\n')
    
    for tab_elem in safe_findall(run_elem, './/w:tab'):
        texts.append('\t')
    
    return ''.join(texts)