"""
ماژول ساخت فهرست مطالب (Outline/Bookmarks) برای PDF
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid


class OutlineStyle(Enum):
    """سبک‌های فهرست مطالب"""
    DEFAULT = "default"      # پیش‌فرض
    BOLD = "bold"           # پررنگ
    ITALIC = "italic"       # ایتالیک
    COLORED = "colored"     # رنگی


@dataclass
class OutlineItem:
    """آیتم فهرست مطالب"""
    title: str                      # عنوان
    page_number: int                # شماره صفحه
    level: int = 0                  # سطح (0 برای ریشه)
    children: List['OutlineItem'] = field(default_factory=list)  # زیرمجموعه‌ها
    style: OutlineStyle = OutlineStyle.DEFAULT  # سبک
    color: Optional[Tuple[float, float, float]] = None  # رنگ (RGB)
    is_open: bool = True            # آیا باز باشد؟
    action: Optional[str] = None    # اکشن (برای لینک‌های خاص)
    object_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # شناسه یکتا
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            'title': self.title,
            'page_number': self.page_number,
            'level': self.level,
            'children': [child.to_dict() for child in self.children],
            'style': self.style.value,
            'color': self.color,
            'is_open': self.is_open,
            'action': self.action,
            'object_id': self.object_id
        }


class OutlineBuilder:
    """سازنده فهرست مطالب PDF"""
    
    def __init__(self) -> None:
        self.items: List[OutlineItem] = []
        self.next_object_num = 1
        self.object_map: Dict[str, int] = {}  # نگاشت object_id به شماره آبجکت PDF
    
    def add_item(self, title: str, page_number: int, level: int = 0, 
                parent: Optional[OutlineItem] = None, **kwargs) -> OutlineItem:
        """افزودن آیتم به فهرست مطالب"""
        item = OutlineItem(
            title=title,
            page_number=page_number,
            level=level,
            **kwargs
        )
        
        if parent:
            parent.children.append(item)
        else:
            self.items.append(item)
        
        return item
    
    def build_from_toc(self, toc_structure: List[Dict[str, Any]]) -> None:
        """ساخت فهرست از ساختار TOC"""
        self._build_recursive(toc_structure, None, 0)
    
    def _build_recursive(self, items: List[Dict[str, Any]], 
                        parent: Optional[OutlineItem], level: int) -> None:
        """ساخت بازگشتی"""
        for item_data in items:
            item = OutlineItem(
                title=item_data.get('title', ''),
                page_number=item_data.get('page_number', 1),
                level=level,
                style=OutlineStyle(item_data.get('style', 'default')),
                color=item_data.get('color'),
                is_open=item_data.get('is_open', True),
                action=item_data.get('action')
            )
            
            if parent:
                parent.children.append(item)
            else:
                self.items.append(item)
            
            # پردازش فرزندان
            children = item_data.get('children', [])
            if children:
                self._build_recursive(children, item, level + 1)
    
    def generate_outline_objects(self, page_refs: Dict[int, str]) -> List[Dict[str, Any]]:
        """تولید آبجکت‌های فهرست مطالب PDF"""
        objects: List[Dict[str, Any]] = []
        
        if not self.items:
            return objects
        
        # تولید آبجکت‌های Outline
        outline_dict = self._create_outline_dict()
        objects.append(outline_dict)
        
        # تولید آبجکت‌های آیتم‌ها
        for item in self._flatten_items():
            item_objects = self._create_outline_item_objects(item, page_refs)
            objects.extend(item_objects)
        
        return objects
    
    def _flatten_items(self) -> List[OutlineItem]:
        """تبدیل ساختار درختی به لیست تخت"""
        flattened = []
        
        def flatten_recursive(items: List[OutlineItem]):
            for item in items:
                flattened.append(item)
                flatten_recursive(item.children)
        
        flatten_recursive(self.items)
        return flattened
    
    def _create_outline_dict(self) -> Dict[str, Any]:
        """ایجاد دیکشنری Outline"""
        first_item_ref = None
        last_item_ref = None
        count = len(self._flatten_items())
        
        if self.items:
            first_item = self.items[0]
            last_item = self._get_last_item(self.items[-1])
            
            first_item_ref = f"{self.object_map.get(first_item.object_id, 0)} 0 R"
            last_item_ref = f"{self.object_map.get(last_item.object_id, 0)} 0 R"
        data: Dict[str, Any]={
                'Type': '/Outlines',
                'Count': count
            }
        outline_dict = {
            'type': 'outline',
            'object_num': self.next_object_num,
            'data': data
        }
        
        if first_item_ref:
            data['First'] = first_item_ref
        if last_item_ref:
            data['Last'] = last_item_ref
        
        self.next_object_num += 1
        return outline_dict
    
    def _get_last_item(self, item: OutlineItem) -> OutlineItem:
        """دریافت آخرین آیتم در زیردرخت"""
        if not item.children:
            return item
        
        return self._get_last_item(item.children[-1])
    
    def _create_outline_item_objects(self, item: OutlineItem, 
                                   page_refs: Dict[int, str]) -> List[Dict[str, Any]]:
        """ایجاد آبجکت‌های آیتم فهرست"""
        objects = []
        
        # ایجاد آبجکت اصلی آیتم
        item_dict = self._create_item_dict(item, page_refs)
        objects.append(item_dict)
        
        # ثبت در object_map
        self.object_map[item.object_id] = item_dict['object_num']
        
        return objects
    
    def _create_item_dict(self, item: OutlineItem, 
                         page_refs: Dict[int, str]) -> Dict[str, Any]:
        """ایجاد دیکشنری آیتم"""
        data: Dict[str, Any] = {
                'Title': f'({self._escape_pdf_string(item.title)})',
                'Parent': '',  # بعداً پر می‌شود
                'Dest': self._create_destination(item, page_refs)
            }
        item_dict = {
            'type': 'outline_item',
            'object_num': self.next_object_num,
            'data': data
        }
        
        # تنظیم سبک
        if item.style == OutlineStyle.BOLD:
            data['F'] = 2  # Bold flag
        elif item.style == OutlineStyle.ITALIC:
            data['F'] = 1  # Italic flag
        
        # تنظیم رنگ
        if item.color:
            r, g, b = item.color
            data['C'] = f'[{r:.3f} {g:.3f} {b:.3f}]'
        
        # تنظیم وضعیت باز/بسته بودن
        if not item.is_open:
            data['Count'] = 0
        elif item.children:
            data['Count'] = len(self._flatten_items_from(item))
        
        # تنظیم ارجاعات به فرزندان و همسایه‌ها
        if item.children:
            first_child = item.children[0]
            last_child = item.children[-1]
            
            data['First'] = f"{self.next_object_num + 1} 0 R"
            data['Last'] = f"{self.next_object_num + len(item.children)} 0 R"
        
        self.next_object_num += 1
        return item_dict
    
    def _flatten_items_from(self, item: OutlineItem) -> List[OutlineItem]:
        """تبدیل زیردرخت به لیست تخت"""
        flattened = []
        
        def flatten_recursive(current_item: OutlineItem):
            flattened.append(current_item)
            for child in current_item.children:
                flatten_recursive(child)
        
        flatten_recursive(item)
        return flattened
    
    def _create_destination(self, item: OutlineItem, 
                          page_refs: Dict[int, str]) -> str:
        """ایجاد مقصد برای آیتم"""
        page_ref = page_refs.get(item.page_number, page_refs.get(1, ''))
        
        if item.action:
            # اکشن سفارشی
            return f'/{item.action}'
        else:
            # مقصد صفحه
            return f'[{page_ref} /XYZ 0 0 null]'
    
    def _escape_pdf_string(self, text: str) -> str:
        """فرار کردن رشته برای PDF"""
        # جایگزینی کاراکترهای خاص
        replacements = {
            '(': '\\(',
            ')': '\\)',
            '\\': '\\\\',
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
            '\b': '\\b',
            '\f': '\\f'
        }
        
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        return result
    
    def get_outline_structure(self) -> List[Dict[str, Any]]:
        """دریافت ساختار فهرست مطالب"""
        return [item.to_dict() for item in self.items]
    
    def clear(self):
        """پاک کردن فهرست"""
        self.items.clear()
        self.object_map.clear()
        self.next_object_num = 1
