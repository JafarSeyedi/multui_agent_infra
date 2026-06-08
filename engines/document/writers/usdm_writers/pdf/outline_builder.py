"""
Module for building Table of Contents (Outline/Bookmarks) for PDF
"""
import uuid
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any


class OutlineStyle(Enum):
    """Table of contents styles"""
    DEFAULT = "default"      # Default
    BOLD = "bold"           # Bold
    ITALIC = "italic"       # Italic
    COLORED = "colored"     # Colored


@dataclass
class OutlineItem:
    """Table of contents item"""
    title: str                      # Title
    page_number: int                # Page number
    level: int = 0                  # Level (0 for root)
    children: list['OutlineItem'] = field(default_factory=list)  # Children
    style: OutlineStyle = OutlineStyle.DEFAULT  # Style
    color: tuple[float, float, float] | None = None  # Color (RGB)
    is_open: bool = True            # Whether open
    action: str | None = None    # Action (for specific links)
    object_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
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
    """PDF table of contents builder"""

    def __init__(self) -> None:
        self.items: list[OutlineItem] = []
        self.next_object_num = 1
        self.object_map: dict[str, int] = {}  # Map object_id to PDF object number

    def add_item(self, title: str, page_number: int, level: int = 0,
                parent: OutlineItem | None = None, **kwargs) -> OutlineItem:
        """Add item to table of contents"""
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

    def build_from_toc(self, toc_structure: list[dict[str, Any]]) -> None:
        """Build table of contents from TOC structure"""
        self._build_recursive(toc_structure, None, 0)

    def _build_recursive(self, items: list[dict[str, Any]],
                        parent: OutlineItem | None, level: int) -> None:
        """Build recursively"""
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

            # Process children
            children = item_data.get('children', [])
            if children:
                self._build_recursive(children, item, level + 1)

    def generate_outline_objects(self, page_refs: dict[int, str]) -> list[dict[str, Any]]:
        """Generate PDF table of contents objects"""
        objects: list[dict[str, Any]] = []

        if not self.items:
            return objects

        # Generate Outline objects
        outline_dict = self._create_outline_dict()
        objects.append(outline_dict)

        # Generate item objects
        for item in self._flatten_items():
            item_objects = self._create_outline_item_objects(item, page_refs)
            objects.extend(item_objects)

        return objects

    def _flatten_items(self) -> list[OutlineItem]:
        """Convert tree structure to flat list"""
        flattened = []

        def flatten_recursive(items: list[OutlineItem]):
            for item in items:
                flattened.append(item)
                flatten_recursive(item.children)

        flatten_recursive(self.items)
        return flattened

    def _create_outline_dict(self) -> dict[str, Any]:
        """Create Outline dictionary"""
        first_item_ref = None
        last_item_ref = None
        count = len(self._flatten_items())

        if self.items:
            first_item = self.items[0]
            last_item = self._get_last_item(self.items[-1])

            first_item_ref = f"{self.object_map.get(first_item.object_id, 0)} 0 R"
            last_item_ref = f"{self.object_map.get(last_item.object_id, 0)} 0 R"
        data: dict[str, Any]={
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
        """Get last item in subtree"""
        if not item.children:
            return item

        return self._get_last_item(item.children[-1])

    def _create_outline_item_objects(self, item: OutlineItem,
                                   page_refs: dict[int, str]) -> list[dict[str, Any]]:
        """Create outline item objects"""
        objects = []

        # Create main item object
        item_dict = self._create_item_dict(item, page_refs)
        objects.append(item_dict)

        # Register in object_map
        self.object_map[item.object_id] = item_dict['object_num']

        return objects

    def _create_item_dict(self, item: OutlineItem,
                         page_refs: dict[int, str]) -> dict[str, Any]:
        """Create item dictionary"""
        data: dict[str, Any] = {
                'Title': f'({self._escape_pdf_string(item.title)})',
                'Parent': '',  # Will be filled later
                'Dest': self._create_destination(item, page_refs)
            }
        item_dict = {
            'type': 'outline_item',
            'object_num': self.next_object_num,
            'data': data
        }

        # Set style
        if item.style == OutlineStyle.BOLD:
            data['F'] = 2  # Bold flag
        elif item.style == OutlineStyle.ITALIC:
            data['F'] = 1  # Italic flag

        # Set color
        if item.color:
            r, g, b = item.color
            data['C'] = f'[{r:.3f} {g:.3f} {b:.3f}]'

        # Set open/closed state
        if not item.is_open:
            data['Count'] = 0
        elif item.children:
            data['Count'] = len(self._flatten_items_from(item))

        # Set references to children and siblings
        if item.children:
            item.children[0]
            item.children[-1]

            data['First'] = f"{self.next_object_num + 1} 0 R"
            data['Last'] = f"{self.next_object_num + len(item.children)} 0 R"

        self.next_object_num += 1
        return item_dict

    def _flatten_items_from(self, item: OutlineItem) -> list[OutlineItem]:
        """Convert subtree to flat list"""
        flattened = []

        def flatten_recursive(current_item: OutlineItem):
            flattened.append(current_item)
            for child in current_item.children:
                flatten_recursive(child)

        flatten_recursive(item)
        return flattened

    def _create_destination(self, item: OutlineItem,
                          page_refs: dict[int, str]) -> str:
        """Create destination for item"""
        page_ref = page_refs.get(item.page_number, page_refs.get(1, ''))

        if item.action:
            # Custom action
            return f'/{item.action}'
        else:
            # Page destination
            return f'[{page_ref} /XYZ 0 0 null]'

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

    def get_outline_structure(self) -> list[dict[str, Any]]:
        """Get table of contents structure"""
        return [item.to_dict() for item in self.items]

    def clear(self):
        """Clear table of contents"""
        self.items.clear()
        self.object_map.clear()
        self.next_object_num = 1
