"""
Module for writing annotations in PDF
"""
import uuid
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Any


class AnnotationType(Enum):
    """Annotation types"""
    TEXT = "Text"              # Text note
    HIGHLIGHT = "Highlight"   # Highlight
    UNDERLINE = "Underline"   # Underline
    STRIKEOUT = "StrikeOut"   # Strikeout
    SQUIGGLY = "Squiggly"     # Squiggly underline
    SQUARE = "Square"         # Rectangle
    CIRCLE = "Circle"         # Circle
    LINE = "Line"             # Line
    ARROW = "Arrow"           # Arrow
    POLYGON = "Polygon"       # Polygon
    POLYLINE = "PolyLine"     # Polyline
    INK = "Ink"              # Handwriting
    STAMP = "Stamp"          # Stamp
    CARET = "Caret"          # Insertion mark
    FREETEXT = "FreeText"    # Free text
    FILEATTACHMENT = "FileAttachment"  # File attachment
    SOUND = "Sound"          # Sound
    MOVIE = "Movie"          # Movie
    WIDGET = "Widget"        # Widget (for forms)
    SCREEN = "Screen"        # Screen
    PRINTERMARK = "PrinterMark"  # Printer mark
    TRAPNET = "TrapNet"      # Trap net
    WATERMARK = "Watermark"  # Watermark
    _3D = "3D"              # Three-dimensional


class AnnotationBorderStyle(Enum):
    """Border style"""
    SOLID = "S"          # Solid
    DASHED = "D"        # Dashed
    BEVELED = "B"      # Beveled
    INSET = "I"         # Inset
    UNDERLINE = "U"  # Underline


class AnnotationFlag(Enum):
    """Annotation flags"""
    INVISIBLE = 1 << 0          # Invisible
    HIDDEN = 1 << 1           # Hidden
    PRINT = 1 << 2            # Printable
    NOZOOM = 1 << 3           # No zoom
    NOROTATE = 1 << 4         # No rotate
    NOVIEW = 1 << 5           # No view
    READONLY = 1 << 6         # Read only
    LOCKED = 1 << 7           # Locked
    TOGGLENOVIEW = 1 << 8     # Toggle no view
    LOCKEDCONTENTS = 1 << 9   # Locked contents


@dataclass
class Annotation:
    """Annotation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: AnnotationType = AnnotationType.TEXT
    page_number: int = 1
    rect: tuple[float, float, float, float] = (0, 0, 100, 100)  # x1, y1, x2, y2
    contents: str = ""  # Annotation text
    author: str = ""    # Author
    subject: str = ""   # Subject
    creation_date: str = field(default_factory=lambda: AnnotationWriter._get_pdf_date())
    modification_date: str = field(default_factory=lambda: AnnotationWriter._get_pdf_date())
    color: tuple[float, float, float] = (1, 1, 0)  # Color (yellow default)
    opacity: float = 1.0  # Opacity (0-1)
    border_width: float = 1.0  # Border width
    border_style: AnnotationBorderStyle = AnnotationBorderStyle.SOLID
    border_color: tuple[float, float, float] | None = None  # Border color
    border_dash: list[float] | None = None  # Dash pattern
    rotation: float = 0  # Rotation (degrees)
    flags: int = 4  # PDF flags (4 = PRINT)
    custom_data: dict[str, Any] = field(default_factory=dict)  # Custom data

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
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
    """PDF annotation writer"""

    def __init__(self) -> None:
        self.annotations: list[Annotation] = []
        self.next_object_num = 1
        self.annotation_map: dict[str, int] = {}  # Mapping of annotation_id to object number

    @staticmethod
    def _get_pdf_date() -> str:
        """Get current date in PDF format"""
        now = datetime.now()
        return f"D:{now.strftime('%Y%m%d%H%M%S')}"

    def add_annotation(self, annotation: Annotation) -> str:
        """Add annotation"""
        self.annotations.append(annotation)
        return annotation.id

    def create_text_annotation(self, page_number: int, rect: tuple[float, float, float, float],
                              contents: str, **kwargs) -> Annotation:
        """Create text annotation"""
        annotation = Annotation(
            type=AnnotationType.TEXT,
            page_number=page_number,
            rect=rect,
            contents=contents,
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation

    def create_highlight_annotation(self, page_number: int, rect: tuple[float, float, float, float],
                                   contents: str = "", **kwargs) -> Annotation:
        """Create highlight annotation"""
        annotation = Annotation(
            type=AnnotationType.HIGHLIGHT,
            page_number=page_number,
            rect=rect,
            contents=contents,
            color=kwargs.pop('color', (1, 1, 0)),  # Yellow default
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation

    def create_line_annotation(self, page_number: int,
                             start_point: tuple[float, float],
                             end_point: tuple[float, float],
                             contents: str = "", **kwargs) -> Annotation:
        """Create line annotation"""
        # Calculate rect from points
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
                                 vertices: list[tuple[float, float]],
                                 contents: str = "", **kwargs) -> Annotation:
        """Create polygon annotation"""
        # Calculate rect from vertices
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
                                  points: list[tuple[float, float]],
                                  contents: str = "", **kwargs) -> Annotation:
        """Create polyline annotation"""
        # Calculate rect from points
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

    def create_square_annotation(self, page_number: int, rect: tuple[float, float, float, float],
                               contents: str = "", **kwargs) -> Annotation:
        """Create square annotation"""
        annotation = Annotation(
            type=AnnotationType.SQUARE,
            page_number=page_number,
            rect=rect,
            contents=contents,
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation

    def create_circle_annotation(self, page_number: int, center: tuple[float, float],
                               radius: float, contents: str = "", **kwargs) -> Annotation:
        """Create circle annotation"""
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

    def create_freetext_annotation(self, page_number: int, rect: tuple[float, float, float, float],
                                 text: str, font_size: float = 12, **kwargs) -> Annotation:
        """Create free text annotation"""
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

    def create_stamp_annotation(self, page_number: int, rect: tuple[float, float, float, float],
                               stamp_name: str, contents: str = "", **kwargs) -> Annotation:
        """Create stamp annotation"""
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
                                       rect: tuple[float, float, float, float],
                                       file_name: str, file_data: bytes,
                                       contents: str = "", **kwargs) -> Annotation:
        """Create file attachment annotation"""
        annotation = Annotation(
            type=AnnotationType.FILEATTACHMENT,
            page_number=page_number,
            rect=rect,
            contents=contents,
            custom_data={
                'file_name': file_name,
                'file_size': len(file_data),
                'file_data': file_data.hex()  # Store as hex
            },
            **kwargs
        )
        self.add_annotation(annotation)
        return annotation

    def create_ink_annotation(self, page_number: int,
                            strokes: list[list[tuple[float, float]]],
                            contents: str = "", **kwargs) -> Annotation:
        """Create ink annotation"""
        # Calculate rect from all points
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

    def generate_annotation_objects(self, page_refs: dict[int, str]) -> list[dict[str, Any]]:
        """Generate PDF annotation objects"""
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

    def _create_annotation_object(self, annotation: Annotation, page_ref: str) -> dict[str, Any] | None:
        """Create annotation object"""
        base_dict = {
            'Type': '/Annot',
            'Subtype': f'/{annotation.type.value}',
            'Rect': f'[{annotation.rect[0]:.2f} {annotation.rect[1]:.2f} {annotation.rect[2]:.2f} {annotation.rect[3]:.2f}]',
            'P': page_ref,
            'F': annotation.flags
        }

        # Add optional fields
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

        # Add color
        if annotation.color:
            r, g, b = annotation.color
            base_dict['C'] = f'[{r:.3f} {g:.3f} {b:.3f}]'

        # Add border
        border_dict = self._create_border_dict(annotation)
        if border_dict:
            base_dict['Border'] = border_dict

        # Add type-specific data
        type_specific = self._create_type_specific_dict(annotation)
        base_dict.update(type_specific)

        # Add custom data
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
        """Create border dictionary"""
        border_parts = []

        # border width
        border_parts.append(f'{annotation.border_width:.1f}')

        # border style
        if annotation.border_style == AnnotationBorderStyle.DASHED:
            border_parts.append(f'[{annotation.border_dash[0]:.1f} {annotation.border_dash[1]:.1f}]'
                              if annotation.border_dash else '[3 3]')
        else:
            border_parts.append(f'/{annotation.border_style.value}')

        # border color (if specified)
        if annotation.border_color:
            r, g, b = annotation.border_color
            border_parts.append(f'[{r:.3f} {g:.3f} {b:.3f}]')

        return f'[{" ".join(border_parts)}]'

    def _create_type_specific_dict(self, annotation: Annotation) -> dict[str, Any]:
        """Create annotation type-specific dictionary"""
        type_specific = {}

        if annotation.type == AnnotationType.LINE:
            if 'start_point' in annotation.custom_data and 'end_point' in annotation.custom_data:
                x1, y1 = annotation.custom_data['start_point']
                x2, y2 = annotation.custom_data['end_point']
                type_specific['L'] = f'[{x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f}]'

                # Add arrow heads if needed
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
                annotation.custom_data['radius']
                # For circle, use Cloudy border
                type_specific['BS'] = '<< /Type /Border /S /C /W 1 >>'

        elif annotation.type == AnnotationType.FREETEXT:
            if 'font_size' in annotation.custom_data:
                type_specific['DS'] = f'(font: {annotation.custom_data.get("font_name", "Helvetica")} {annotation.custom_data["font_size"]}pt)'
                type_specific['DA'] = f'({annotation.custom_data["font_size"]} Tf 0 g)'

                # Set alignment
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
        """Format custom value for PDF"""
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
        """Escape string for PDF"""
        # Replace special characters
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

    def get_annotations_by_page(self, page_number: int) -> list[Annotation]:
        """Get annotations for a page"""
        return [ann for ann in self.annotations if ann.page_number == page_number]

    def get_annotation_by_id(self, annotation_id: str) -> Annotation | None:
        """Get annotation by ID"""
        for ann in self.annotations:
            if ann.id == annotation_id:
                return ann
        return None

    def remove_annotation(self, annotation_id: str) -> bool:
        """Remove annotation"""
        for i, ann in enumerate(self.annotations):
            if ann.id == annotation_id:
                self.annotations.pop(i)
                if annotation_id in self.annotation_map:
                    del self.annotation_map[annotation_id]
                return True
        return False

    def clear_page_annotations(self, page_number: int) -> int:
        """Remove all annotations for a page"""
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
        """Clear all annotations"""
        self.annotations.clear()
        self.annotation_map.clear()

    def get_annotation_count(self) -> int:
        """Get annotation count"""
        return len(self.annotations)

    def get_annotation_statistics(self) -> dict[str, Any]:
        """Get annotation statistics"""
        # Use explicitly typed inner dictionaries to avoid type narrowing issues
        by_type: dict[str, int] = {}
        by_page: dict[int, int] = {}

        stats: dict[str, Any] = {
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
