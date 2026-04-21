"""
ماژول تحلیل لایه‌بندی PDF
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
import fitz  # PyMuPDF
import numpy as np
from sklearn.cluster import DBSCAN
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class LayoutBlock:
    """بلوک لایه‌بندی"""
    id: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    content_type: str  # 'text', 'image', 'table', 'header', 'footer', 'sidebar'
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List['LayoutBlock'] = field(default_factory=list)
    parent_id: Optional[str] = None


@dataclass
class PageLayout:
    """لایه‌بندی یک صفحه"""
    page_number: int
    width: float
    height: float
    blocks: List[LayoutBlock] = field(default_factory=list)
    columns: List[Tuple[float, float]] = field(default_factory=list)  # column boundaries
    regions: Dict[str, List[LayoutBlock]] = field(default_factory=dict)  # header, footer, main, etc.
    reading_order: List[str] = field(default_factory=list)  # block IDs in reading order


class LayoutAnalyzer:
    """تحلیلگر لایه‌بندی PDF"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        self.options = options or {}
        self.min_block_area = self.options.get('min_block_area', 10.0)
        self.column_threshold = self.options.get('column_threshold', 50.0)
        self.header_footer_threshold = self.options.get('header_footer_threshold', 0.1)
        
    def analyze_page(self, page: fitz.Page, page_num: int) -> PageLayout:
        """
        تحلیل لایه‌بندی یک صفحه PDF
        
        Args:
            page: صفحه PyMuPDF
            page_num: شماره صفحه
            
        Returns:
            PageLayout: ساختار لایه‌بندی صفحه
        """
        layout = PageLayout(
            page_number=page_num,
            width=page.rect.width,
            height=page.rect.height
        )
        
        # استخراج بلوک‌های اصلی
        blocks = self._extract_blocks(page)
        
        # طبقه‌بندی بلوک‌ها
        classified_blocks = self._classify_blocks(blocks, layout)
        
        # شناسایی ستون‌ها
        layout.columns = self._detect_columns(classified_blocks, layout.width)
        
        # شناسایی مناطق (هدر، فوتر، سایدبار)
        layout.regions = self._detect_regions(classified_blocks, layout)
        
        # تعیین ترتیب خواندن
        layout.reading_order = self._determine_reading_order(classified_blocks, layout)
        
        layout.blocks = classified_blocks
        return layout
    
    def _extract_blocks(self, page: fitz.Page) -> List[LayoutBlock]:
        """استخراج بلوک‌ها از صفحه"""
        blocks = []
        
        # استخراج بلوک‌های متن
        text_blocks = page.get_text("dict")["blocks"]
        for i, block in enumerate(text_blocks):
            if block["type"] == 0:  # متن
                bbox = tuple(block["bbox"])
                if self._calculate_area(bbox) > self.min_block_area:
                    layout_block = LayoutBlock(
                        id=f"text_{i}",
                        bbox=bbox,
                        content_type="text",
                        metadata={
                            "lines": len(block.get("lines", [])),
                            "spans": sum(len(line.get("spans", [])) for line in block.get("lines", [])),
                            "font_sizes": list(set(span.get("size", 0) for line in block.get("lines", []) 
                                                  for span in line.get("spans", [])))
                        }
                    )
                    blocks.append(layout_block)
        
        # استخراج تصاویر
        images = page.get_images()
        for i, img_info in enumerate(images):
            try:
                # پیدا کردن موقعیت تصویر
                for draw in page.get_drawings():
                    if draw.get("type") == "image":
                        bbox = (draw["rect"].x0, draw["rect"].y0, 
                               draw["rect"].x1, draw["rect"].y1)
                        layout_block = LayoutBlock(
                            id=f"image_{i}",
                            bbox=bbox,
                            content_type="image",
                            metadata={
                                "xref": img_info[0],
                                "width": img_info[2],
                                "height": img_info[3]
                            }
                        )
                        blocks.append(layout_block)
                        break
            except:
                pass
        
        # استخراج جداول (با استفاده از pdfplumber)
        try:
            import pdfplumber
            with pdfplumber.open(stream=page.parent.write()) as pdf:
                pdf_page = pdf.pages[page.number]
                tables = pdf_page.find_tables()
                
                for i, table in enumerate(tables):
                    bbox = (table.bbox[0], table.bbox[1], 
                           table.bbox[2], table.bbox[3])
                    layout_block = LayoutBlock(
                        id=f"table_{i}",
                        bbox=bbox,
                        content_type="table",
                        metadata={
                            "rows": table.rows,
                            "cols": table.cols,
                            "cells": len(table.cells)
                        }
                    )
                    blocks.append(layout_block)
        except:
            pass
        
        return blocks
    
    def _classify_blocks(self, blocks: List[LayoutBlock], layout: PageLayout) -> List[LayoutBlock]:
        """طبقه‌بندی بلوک‌ها"""
        classified_blocks = []
        page_height = layout.height
        
        for block in blocks:
            # تشخیص هدر/فوتر
            block_height = block.bbox[3] - block.bbox[1]
            header_threshold = page_height * self.header_footer_threshold
            footer_threshold = page_height * (1 - self.header_footer_threshold)
            
            if block.bbox[1] < header_threshold:
                block.content_type = "header"
            elif block.bbox[3] > footer_threshold:
                block.content_type = "footer"
            
            # تشخیص سایدبار
            block_width = block.bbox[2] - block.bbox[0]
            page_width = layout.width
            
            if block_width < page_width * 0.3:  # کمتر از 30% عرض صفحه
                if block.bbox[0] < page_width * 0.1:  # سمت چپ
                    block.content_type = "sidebar_left"
                elif block.bbox[2] > page_width * 0.9:  # سمت راست
                    block.content_type = "sidebar_right"
            
            classified_blocks.append(block)
        
        return classified_blocks
    
    def _detect_columns(self, blocks: List[LayoutBlock], page_width: float) -> List[Tuple[float, float]]:
        """شناسایی ستون‌ها"""
        if not blocks:
            return [(0.0, page_width)]  # یک ستون
        
        # جمع‌آوری موقعیت‌های عمودی بلوک‌های متن
        vertical_positions = []
        for block in blocks:
            if block.content_type == "text":
                vertical_positions.append((block.bbox[0] + block.bbox[2]) / 2)  # مرکز افقی
        
        if not vertical_positions:
            return [(0.0, page_width)]
        
        # خوشه‌بندی موقعیت‌ها برای شناسایی ستون‌ها
        positions_array = np.array(vertical_positions).reshape(-1, 1)
        
        # استفاده از DBSCAN برای خوشه‌بندی
        clustering = DBSCAN(eps=self.column_threshold, min_samples=2).fit(positions_array)
        
        columns = []
        unique_labels = set(clustering.labels_)
        
        for label in unique_labels:
            if label != -1:  # نادیده گرفتن نقاط پرت
                cluster_points = positions_array[clustering.labels_ == label]
                left = float(cluster_points.min())
                right = float(cluster_points.max())
                columns.append((left, right))
        
        # مرتب‌سازی ستون‌ها از چپ به راست
        columns.sort(key=lambda x: x[0])
        
        # اگر ستونی شناسایی نشد، کل صفحه را یک ستون در نظر بگیر
        if not columns:
            columns = [(0.0, page_width)]
        
        return columns
    
    def _detect_regions(self, blocks: List[LayoutBlock], layout: PageLayout) -> Dict[str, List[LayoutBlock]]:
        """شناسایی مناطق صفحه"""
        regions = {
            "header": [],
            "footer": [],
            "main": [],
            "sidebar_left": [],
            "sidebar_right": [],
            "marginalia": []
        }
        
        page_height = layout.height
        header_threshold = page_height * 0.15  # 15% بالای صفحه
        footer_threshold = page_height * 0.85  # 85% بالای صفحه
        
        for block in blocks:
            block_center_y = (block.bbox[1] + block.bbox[3]) / 2
            
            if block_center_y < header_threshold:
                regions["header"].append(block)
            elif block_center_y > footer_threshold:
                regions["footer"].append(block)
            elif block.content_type.startswith("sidebar"):
                region_type = block.content_type
                regions[region_type].append(block)
            else:
                regions["main"].append(block)
        
        return regions
    
    def _determine_reading_order(self, blocks: List[LayoutBlock], layout: PageLayout) -> List[str]:
        """تعیین ترتیب خواندن"""
        if not blocks:
            return []
        
        # گروه‌بندی بلوک‌ها بر اساس ستون
        column_blocks = defaultdict(list)
        
        for block in blocks:
            if block.content_type == "text":
                block_center_x = (block.bbox[0] + block.bbox[2]) / 2
                
                # پیدا کردن ستون مربوطه
                for i, (col_left, col_right) in enumerate(layout.columns):
                    if col_left <= block_center_x <= col_right:
                        column_blocks[i].append(block)
                        break
        
        # مرتب‌سازی بلوک‌ها در هر ستون (بالا به پایین)
        for col_idx in column_blocks:
            column_blocks[col_idx].sort(key=lambda b: b.bbox[1])
        
        # ایجاد ترتیب خواندن (ستون‌ها از چپ به راست)
        reading_order = []
        sorted_columns = sorted(column_blocks.items())
        
        for col_idx, col_blocks in sorted_columns:
            for block in col_blocks:
                reading_order.append(block.id)
        
        # اضافه کردن بلوک‌های غیرمتنی
        non_text_blocks = [b for b in blocks if b.content_type != "text"]
        non_text_blocks.sort(key=lambda b: b.bbox[1])  # مرتب‌سازی بر اساس موقعیت عمودی
        
        for block in non_text_blocks:
            reading_order.append(block.id)
        
        return reading_order
    
    def _calculate_area(self, bbox: Tuple[float, float, float, float]) -> float:
        """محاسبه مساحت بلوک"""
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width * height
    
    def visualize_layout(self, layout: PageLayout, output_path: Optional[str] = None):
        """نمایش بصری لایه‌بندی"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            
            fig, ax = plt.subplots(figsize=(layout.width/100, layout.height/100))
            ax.set_xlim(0, layout.width)
            ax.set_ylim(layout.height, 0)  # معکوس کردن محور Y
            
            # رنگ‌های مختلف برای انواع مختلف
            colors = {
                "text": "blue",
                "image": "green",
                "table": "red",
                "header": "orange",
                "footer": "purple",
                "sidebar_left": "yellow",
                "sidebar_right": "yellow",
                "main": "lightblue"
            }
            
            for block in layout.blocks:
                color = colors.get(block.content_type, "gray")
                rect = patches.Rectangle(
                    (block.bbox[0], block.bbox[1]),
                    block.bbox[2] - block.bbox[0],
                    block.bbox[3] - block.bbox[1],
                    linewidth=1,
                    edgecolor=color,
                    facecolor=color + "20",  # شفافیت
                    alpha=0.5
                )
                ax.add_patch(rect)
                
                # نمایش ID
                ax.text(
                    block.bbox[0], block.bbox[1],
                    block.id,
                    fontsize=8,
                    color=color
                )
            
            # نمایش ستون‌ها
            for i, (left, right) in enumerate(layout.columns):
                ax.axvline(x=left, color='red', linestyle='--', alpha=0.3)
                ax.axvline(x=right, color='red', linestyle='--', alpha=0.3)
                ax.text(left, 20, f"Col {i}", fontsize=10, color='red')
            
            ax.set_title(f"Page {layout.page_number} Layout")
            ax.set_xlabel("Width")
            ax.set_ylabel("Height")
            
            if output_path:
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close()
            else:
                plt.show()
                
        except ImportError:
            logger.warning("Matplotlib not installed. Visualization skipped.")
    
    def export_to_json(self, layout: PageLayout) -> Dict[str, Any]:
        """صادر کردن لایه‌بندی به JSON"""
        return {
            "page_number": layout.page_number,
            "dimensions": {
                "width": layout.width,
                "height": layout.height
            },
            "columns": [
                {"left": col[0], "right": col[1]} 
                for col in layout.columns
            ],
            "blocks": [
                {
                    "id": block.id,
                    "bbox": {
                        "x0": block.bbox[0],
                        "y0": block.bbox[1],
                        "x1": block.bbox[2],
                        "y1": block.bbox[3]
                    },
                    "content_type": block.content_type,
                    "confidence": block.confidence,
                    "metadata": block.metadata,
                    "parent_id": block.parent_id
                }
                for block in layout.blocks
            ],
            "regions": {
                region: [block.id for block in blocks]
                for region, blocks in layout.regions.items()
            },
            "reading_order": layout.reading_order
        }
