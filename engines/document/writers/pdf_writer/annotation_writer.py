"""
ماژول نوشتن حاشیه‌نویسی‌ها (Annotations) در PDF
"""

from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
from datetime import datetime


class AnnotationType(Enum):
    """انواع حاشیه‌نویسی"""
    TEXT = "Text"              # یادداشت متنی
    HIGHLIGHT = "Highlight"   # هایلایت
    UNDERLINE = "Underline"   # زیرخط
    STRIKEOUT = "StrikeOut"   # خط زدن
    SQUIGGLY = "Squiggly"     # خط مواج
    SQUARE = "Square"         # مستطیل
    CIRCLE = "Circle"         # دایره
    LINE = "Line"             # خط
    ARROW = "Arrow"           # پیکان
    POLYGON = "Polygon"       # چندضلعی
    POLYLINE = "PolyLine"     # خط چندگانه
    INK = "Ink"              # دستخط
    STAMP = "Stamp"          # مهر
    CARET = "Caret"          # علامت درج
    FREETEXT = "FreeText"    # متن آزاد
    FILEATTACHMENT = "FileAttachment"  # ضمیمه فایل
    SOUND = "Sound"          # صدا
    MOVIE = "Movie"          # فیلم
    WIDGET = "Widget"        # ویجت (برای فرم‌ها)
    SCREEN = "Screen"        # صفحه
    PRINTERMARK = "PrinterMark"  # علامت چاپ
    TRAPNET = "TrapNet"      # شبکه تله
    WATERMARK = "Watermark"  # واترمارک
    _3D = "3D"              # سه‌بعدی


class AnnotationBorderStyle(Enum):
    """سبک حاشیه"""
    SOLID = "S"          # پیوسته
    DASHED = "D"        # خط‌چین
    BEVELED = "B"      # مورب
    INSET = "I"         # فرورفته
    UNDERLINE = "U"  # زیرخطی


class AnnotationFlag(Enum):
    """پرچم‌های حاشیه‌نویسی"""
    INVISIBLE = 1 << 0          # نامرئی
    HIDDEN = 1 << 1           # مخفی
    PRINT = 1 << 2            # قابل چاپ
    NOZOOM = 1 << 3           # غیرقابل زوم
    NOROTATE = 1 << 4         # غیرقابل چرخش
    NOVIEW = 1 << 5           # غیرقابل مشاهده
    READONLY = 1 << 6         # فقط خواندنی
    LOCKED = 1 << 7           # قفل شده
    TOGGLENOVIEW = 1 << 8     # تغییر وضعیت مشاهده
    LOCKEDCONTENTS = 1 << 9   # محتوای قفل شده


@dataclass
class Annotation:
    """حاشیه‌نویسی"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: AnnotationType = AnnotationType.TEXT
    page_number: int = 1
    rect: Tuple[float, float, float, float] = (0, 0, 100, 100)  # x1, y1, x2, y2
    contents: str = ""  # متن حاشیه‌نویسی
    author: str = ""    # نویسنده
    subject: str = ""   # موضوع
    creation_date: str = field(default_factory=lambda: AnnotationWriter._get_pdf_date())
    modification_date: str = field(default_factory=lambda: AnnotationWriter._get_pdf_date())
    color: Tuple[float, float, float] = (1, 1, 0)  # رنگ (زرد پیش‌فرض)
    opacity: float = 1.0  # شفافیت (0-1)
    border_width: float = 1.0  # ضخامت حاشیه
    border_style: AnnotationBorderStyle = AnnotationBorderStyle.SOLID
    border_color: Optional[Tuple[float, float, float]] = None  # رنگ حاشیه
    border_dash: Optional[List[float]] = None  # الگوی خط‌چین
    rotation: float = 0  # چرخش (درجه)
    flags: int = 4  # پرچم‌های PDF (4 = PRINT)
    custom_data: Dict[str, Any] = field(default_factory=dict)  # داده‌های سفارشی
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            'id': self.id,
            'type': self.type.value,
            'page_number': self.page_number,
            'rect': list(self.rect),
            'contents': self.contents,
            'author': self.author,
            'subject': self.subject,
            'creation_date': self.creation_date,
            'modification_date': self.modification_date,
            'color': list(self.color) if self.color else None,
            'opacity': self.opacity,
            'border_width': self.border_width,
            'border_style': self.border_style.value,
            'border_color': list(self.border_color) if self.border_color else None,
            'border_dash': self.border_dash,
            'rotation': self.rotation,
            'flags': self.flags,
            'custom_data': self.custom_data
        }


class AnnotationWriter:
    """نویسنده حاشیه‌نویسی‌های PDF"""
    
    def __init__(self) -> None:
        self.annotations: List[Annotation] = []
        self.next_object_num = 1
        self.annotation_map: Dict[str, int] = {}  # نگاشت annotation_id به شماره آبجکت
    
    @staticmethod
    def _get_pdf_date() -> str:
        """دریافت تاریخ فعلی به فرمت PDF"""
        now = datetime.now()
        return f"D:{now.strftime('%Y%m%d%H%M%S')}"
    
    def add_annotation(self, annotation: Annotation) -> str:
        """افزودن حاشیه‌نویسی"""
        self.annotations.append(annotation)
        return annotation.id
    
    def create_text_annotation(self, page_number: int, rect: Tuple[float, float, float, float],
                              contents: str, **kwargs) -> Annotation:
        """ایجاد حاشیه‌نویسی متنی"""
        annotation = Annotation(
            type=AnnotationType.TEXT,
            page_number=page_number,
            rect=rect,
            contents=contents,
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation
    
    def create_highlight_annotation(self, page_number: int, rect: Tuple[float, float, float, float],
                                   contents: str = "", **kwargs) -> Annotation:
        """ایجاد حاشیه‌نویسی هایلایت"""
        annotation = Annotation(
            type=AnnotationType.HIGHLIGHT,
            page_number=page_number,
            rect=rect,
            contents=contents,
            color=kwargs.pop('color', (1, 1, 0)),  # زرد پیش‌فرض
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation
    
    def create_line_annotation(self, page_number: int, 
                             start_point: Tuple[float, float],
                             end_point: Tuple[float, float],
                             contents: str = "", **kwargs) -> Annotation:
        """ایجاد حاشیه‌نویسی خط"""
        # محاسبه rect از نقاط
        x1, y1 = start_point
        x2, y2 = end_point
        rect = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        
        annotation = Annotation(
            type=AnnotationType.LINE,
            page_number=page_number,
            rect=rect,
            contents=contents,
            custom_data={
                'start_point': start_point,
                'end_point': end_point,
                'line_type': kwargs.pop('line_type', 'line')
            },
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation
    
    def create_polygon_annotation(self, page_number: int, 
                                 vertices: List[Tuple[float, float]],
                                 contents: str = "", **kwargs) -> Annotation:
        """ایجاد حاشیه‌نویسی چندضلعی"""
        # محاسبه rect از رئوس
        x_coords = [v[0] for v in vertices]
        y_coords = [v[1] for v in vertices]
        rect = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
        
        annotation = Annotation(
            type=AnnotationType.POLYGON,
            page_number=page_number,
            rect=rect,
            contents=contents,
            custom_data={'vertices': vertices},
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation
    
    def create_polyline_annotation(self, page_number: int,
                                  points: List[Tuple[float, float]],
                                  contents: str = "", **kwargs) -> Annotation:
        """ایجاد حاشیه‌نویسی خط چندگانه"""
        # محاسبه rect از نقاط
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        rect = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
        
        annotation = Annotation(
            type=AnnotationType.POLYLINE,
            page_number=page_number,
            rect=rect,
            contents=contents,
            custom_data={'points': points},
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation
    
    def create_square_annotation(self, page_number: int, rect: Tuple[float, float, float, float],
                               contents: str = "", **kwargs) -> Annotation:
        """ایجاد حاشیه‌نویسی مستطیل"""
        annotation = Annotation(
            type=AnnotationType.SQUARE,
            page_number=page_number,
            rect=rect,
            contents=contents,
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation
    
    def create_circle_annotation(self, page_number: int, center: Tuple[float, float],
                               radius: float, contents: str = "", **kwargs) -> Annotation:
        """ایجاد حاشیه‌نویسی دایره"""
        x, y = center
        rect = (x - radius, y - radius, x + radius, y + radius)
        
        annotation = Annotation(
            type=AnnotationType.CIRCLE,
            page_number=page_number,
            rect=rect,
            contents=contents,
            custom_data={'center': center, 'radius': radius},
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation
    
    def create_freetext_annotation(self, page_number: int, rect: Tuple[float, float, float, float],
                                 text: str, font_size: float = 12, **kwargs) -> Annotation:
        """ایجاد حاشیه‌نویسی متن آزاد"""
        annotation = Annotation(
            type=AnnotationType.FREETEXT,
            page_number=page_number,
            rect=rect,
            contents=text,
            custom_data={
                'font_size': font_size,
                'font_name': kwargs.pop('font_name', 'Helvetica'),
                'alignment': kwargs.pop('alignment', 'left')
            },
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation
    
    def create_stamp_annotation(self, page_number: int, rect: Tuple[float, float, float, float],
                               stamp_name: str, contents: str = "", **kwargs) -> Annotation:
        """ایجاد حاشیه‌نویسی مهر"""
        annotation = Annotation(
            type=AnnotationType.STAMP,
            page_number=page_number,
            rect=rect,
            contents=contents,
            custom_data={'stamp_name': stamp_name},
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation
    
    def create_fileattachment_annotation(self, page_number: int, 
                                       rect: Tuple[float, float, float, float],
                                       file_name: str, file_data: bytes,
                                       contents: str = "", **kwargs) -> Annotation:
        """ایجاد حاشیه‌نویسی ضمیمه فایل"""
        annotation = Annotation(
            type=AnnotationType.FILEATTACHMENT,
            page_number=page_number,
            rect=rect,
            contents=contents,
            custom_data={
                'file_name': file_name,
                'file_size': len(file_data),
                'file_data': file_data.hex()  # ذخیره به صورت hex
            },
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation
    
    def create_ink_annotation(self, page_number: int, 
                            strokes: List[List[Tuple[float, float]]],
                            contents: str = "", **kwargs) -> Annotation:
        """ایجاد حاشیه‌نویسی دستخط"""
        # محاسبه rect از تمام نقاط
        all_points = [point for stroke in strokes for point in stroke]
        x_coords = [p[0] for p in all_points]
        y_coords = [p[1] for p in all_points]
        rect = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
        
        annotation = Annotation(
            type=AnnotationType.INK,
            page_number=page_number,
            rect=rect,
            contents=contents,
            custom_data={'strokes': strokes},
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation
    
    def generate_annotation_objects(self, page_refs: Dict[int, str]) -> List[Dict[str, Any]]:
        """تولید آبجکت‌های حاشیه‌نویسی PDF"""
        objects = []
        
        for annotation in self.annotations:
            page_ref = page_refs.get(annotation.page_number)
            if not page_ref:
                continue
            
            annotation_object = self._create_annotation_object(annotation, page_ref)
            if annotation_object:
                objects.append(annotation_object)
                self.annotation_map[annotation.id] = annotation_object['object_num']
        
        return objects
    
    def _create_annotation_object(self, annotation: Annotation, page_ref: str) -> Optional[Dict[str, Any]]:
        """ایجاد آبجکت حاشیه‌نویسی"""
        base_dict = {
            'Type': '/Annot',
            'Subtype': f'/{annotation.type.value}',
            'Rect': f'[{annotation.rect[0]:.2f} {annotation.rect[1]:.2f} {annotation.rect[2]:.2f} {annotation.rect[3]:.2f}]',
            'P': page_ref,
            'F': annotation.flags
        }
        
        # اضافه کردن فیلدهای اختیاری
        if annotation.contents:
            base_dict['Contents'] = f'({self._escape_pdf_string(annotation.contents)})'
        
        if annotation.author:
            base_dict['T'] = f'({self._escape_pdf_string(annotation.author)})'
        
        if annotation.subject:
            base_dict['Subj'] = f'({self._escape_pdf_string(annotation.subject)})'
        
        if annotation.creation_date:
            base_dict['CreationDate'] = f'({annotation.creation_date})'
        
        if annotation.modification_date:
            base_dict['M'] = f'({annotation.modification_date})'
        
        # اضافه کردن رنگ
        if annotation.color:
            r, g, b = annotation.color
            base_dict['C'] = f'[{r:.3f} {g:.3f} {b:.3f}]'
        
        # اضافه کردن border
        border_dict = self._create_border_dict(annotation)
        if border_dict:
            base_dict['Border'] = border_dict
        
        # اضافه کردن داده‌های خاص بر اساس نوع
        type_specific = self._create_type_specific_dict(annotation)
        base_dict.update(type_specific)
        
        # اضافه کردن داده‌های سفارشی
        if annotation.custom_data:
            for key, value in annotation.custom_data.items():
                if key not in base_dict:
                    base_dict[key] = self._format_custom_value(value)
        
        return {
            'type': 'annotation',
            'object_num': self.next_object_num,
            'data': base_dict
        }
    
    def _create_border_dict(self, annotation: Annotation) -> str:
        """ایجاد دیکشنری border"""
        border_parts = []
        
        # border width
        border_parts.append(f'{annotation.border_width:.1f}')
        
        # border style
        if annotation.border_style == AnnotationBorderStyle.DASHED:
            border_parts.append(f'[{annotation.border_dash[0]:.1f} {annotation.border_dash[1]:.1f}]' 
                              if annotation.border_dash else '[3 3]')
        else:
            border_parts.append(f'/{annotation.border_style.value}')
        
        # border color (اگر مشخص شده)
        if annotation.border_color:
            r, g, b = annotation.border_color
            border_parts.append(f'[{r:.3f} {g:.3f} {b:.3f}]')
        
        return f'[{" ".join(border_parts)}]'
    
    def _create_type_specific_dict(self, annotation: Annotation) -> Dict[str, Any]:
        """ایجاد دیکشنری مخصوص نوع حاشیه‌نویسی"""
        type_specific = {}
        
        if annotation.type == AnnotationType.LINE:
            if 'start_point' in annotation.custom_data and 'end_point' in annotation.custom_data:
                x1, y1 = annotation.custom_data['start_point']
                x2, y2 = annotation.custom_data['end_point']
                type_specific['L'] = f'[{x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f}]'
                
                # اضافه کردن arrow heads اگر لازم باشد
                if annotation.custom_data.get('line_type') == 'arrow':
                    type_specific['LE'] = '[/None /OpenArrow]'
        
        elif annotation.type == AnnotationType.POLYGON:
            if 'vertices' in annotation.custom_data:
                vertices = annotation.custom_data['vertices']
                vertices_str = ' '.join([f'{x:.2f} {y:.2f}' for x, y in vertices])
                type_specific['Vertices'] = f'[{vertices_str}]'
        
        elif annotation.type == AnnotationType.POLYLINE:
            if 'points' in annotation.custom_data:
                points = annotation.custom_data['points']
                points_str = ' '.join([f'{x:.2f} {y:.2f}' for x, y in points])
                type_specific['Vertices'] = f'[{points_str}]'
        
        elif annotation.type == AnnotationType.CIRCLE:
            if 'center' in annotation.custom_data and 'radius' in annotation.custom_data:
                x, y = annotation.custom_data['center']
                r = annotation.custom_data['radius']
                # برای دایره، از Cloudy border استفاده می‌کنیم
                type_specific['BS'] = '<< /Type /Border /S /C /W 1 >>'
        
        elif annotation.type == AnnotationType.FREETEXT:
            if 'font_size' in annotation.custom_data:
                type_specific['DS'] = f'(font: {annotation.custom_data.get("font_name", "Helvetica")} {annotation.custom_data["font_size"]}pt)'
                type_specific['DA'] = f'({annotation.custom_data["font_size"]} Tf 0 g)'
                
                # تنظیم alignment
                alignment = annotation.custom_data.get('alignment', 'left')
                if alignment == 'center':
                    type_specific['Q'] = '1'
                elif alignment == 'right':
                    type_specific['Q'] = '2'
                else:
                    type_specific['Q'] = '0'
        
        elif annotation.type == AnnotationType.STAMP:
            if 'stamp_name' in annotation.custom_data:
                type_specific['Name'] = f'/{annotation.custom_data["stamp_name"]}'
        
        elif annotation.type == AnnotationType.FILEATTACHMENT:
            if 'file_name' in annotation.custom_data:
                type_specific['FS'] = f'<< /Type /Filespec /F ({annotation.custom_data["file_name"]}) >>'
        
        elif annotation.type == AnnotationType.INK:
            if 'strokes' in annotation.custom_data:
                strokes = annotation.custom_data['strokes']
                ink_list = []
                for stroke in strokes:
                    stroke_points = ' '.join([f'{x:.2f} {y:.2f}' for x, y in stroke])
                    ink_list.append(f'[{stroke_points}]')
                type_specific['InkList'] = f'[{" ".join(ink_list)}]'
        
        return type_specific
    
    def _format_custom_value(self, value: Any) -> str:
        """فرمت‌دهی مقدار سفارشی برای PDF"""
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return f'({self._escape_pdf_string(value)})'
        elif isinstance(value, list):
            items = [self._format_custom_value(item) for item in value]
            return f'[{" ".join(items)}]'
        elif isinstance(value, dict):
            items = []
            for k, v in value.items():
                items.append(f'/{k} {self._format_custom_value(v)}')
            return f'<< {" ".join(items)} >>'
        else:
            return f'({str(value)})'
    
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
    
    def get_annotations_by_page(self, page_number: int) -> List[Annotation]:
        """دریافت حاشیه‌نویسی‌های یک صفحه"""
        return [ann for ann in self.annotations if ann.page_number == page_number]
    
    def get_annotation_by_id(self, annotation_id: str) -> Optional[Annotation]:
        """دریافت حاشیه‌نویسی بر اساس شناسه"""
        for ann in self.annotations:
            if ann.id == annotation_id:
                return ann
        return None
    
    def remove_annotation(self, annotation_id: str) -> bool:
        """حذف حاشیه‌نویسی"""
        for i, ann in enumerate(self.annotations):
            if ann.id == annotation_id:
                self.annotations.pop(i)
                if annotation_id in self.annotation_map:
                    del self.annotation_map[annotation_id]
                return True
        return False
    
    def clear_page_annotations(self, page_number: int) -> int:
        """حذف تمام حاشیه‌نویسی‌های یک صفحه"""
        count = 0
        annotations_to_remove = []
        
        for ann in self.annotations:
            if ann.page_number == page_number:
                annotations_to_remove.append(ann.id)
                count += 1
        
        for ann_id in annotations_to_remove:
            self.remove_annotation(ann_id)
        
        return count
    
    def clear_all_annotations(self):
        """حذف تمام حاشیه‌نویسی‌ها"""
        self.annotations.clear()
        self.annotation_map.clear()
    
    def get_annotation_count(self) -> int:
        """دریافت تعداد حاشیه‌نویسی‌ها"""
        return len(self.annotations)

    def get_annotation_statistics(self) -> Dict[str, Any]:
        """دریافت آمار حاشیه‌نویسی‌ها"""
        # Use explicitly typed inner dictionaries to avoid type narrowing issues
        by_type: Dict[str, int] = {}
        by_page: Dict[int, int] = {}

        stats: Dict[str, Any] = {
            'total': len(self.annotations),
            'by_type': by_type,
            'by_page': by_page
        }

        for ann in self.annotations:
            ann_type = ann.type.value
            by_type[ann_type] = by_type.get(ann_type, 0) + 1

            page_num = ann.page_number
            by_page[page_num] = by_page.get(page_num, 0) + 1

        return stats    
