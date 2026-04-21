# engines/document/models/standards.py
"""
تعاریف استانداردها و مخفف‌های مورد استفاده در سیستم
"""

from enum import Enum
from typing import Dict, Any

class DocumentStandard(str, Enum):
    """استانداردهای سند مورد پشتیبانی"""
    
    # داده‌های ساختاریافته
    DSDM = "dsdm"  # Data Structured Document Model (Structured/hierarchical data)
    
    # اسناد متنی/صفحه‌ای
    USDM = "usdm"  # Unified/Universal Structured Document Model (HyperText/page-based docs)
    
    # داده‌های جدولی
    ESDM = "esdm"  # Excel/Spreadsheet Document Model
    
    # مدل‌های CAD/هندسی
    CSDM = "csdm"  # CAD/Geometric Structured Document Model

    GENERIC = "generic"

    UNKNOWN = "unknown"
    
    @property
    def full_name(self) -> str:
        """نام کامل استاندارد"""
        names = {
            "dsdm": "Data Structured Document Model",
            "usdm": "Unified Structured Document Model", 
            "esdm": "Excel/Spreadsheet Document Model",
            "csdm": "CAD/Geometric Structured Document Model",
            "generic": "Generic Text/Binary",
            "unknown": "Unknown",
        }
        return names.get(self.value, self.value)
    
    @property
    def description(self) -> str:
        """توضیحات استاندارد"""
        descriptions = {
            "dsdm": "مدل سند ساختاریافته داده‌ای برای فرمت‌های JSON، XML، YAML و...",
            "usdm": "مدل سند ساختاریافته یکپارچه برای اسناد متنی و صفحه‌ای",
            "esdm": "مدل سند ساختاریافته برای داده‌های جدولی و صفحه‌گسترده",
            "csdm": "مدل سند ساختاریافته برای مدل‌های CAD و داده‌های هندسی",
            "generic": "بدون رعایت یا کنترل ساختار خاص",
            "unknown": "نامشخص",
        }
        return descriptions.get(self.value, "")

class MediaCategory(str, Enum):
    """دسته‌بندی‌های اصلی رسانه‌ها"""
    
    STRUCTURED_DATA = "structured_data"      # داده ساختاریافته
    DOCUMENT = "document"                    # اسناد متنی
    SPREADSHEET = "spreadsheet"              # صفحات گسترده
    CAD_GEOMETRIC = "cad_geometric"          # CAD و هندسی
    IMAGE = "image"                          # تصاویر
    AUDIO = "audio"                          # صوت
    VIDEO = "video"                          # ویدئو
    ARCHIVE = "archive"                      # آرشیو
    EXECUTABLE = "executable"                # اجرایی
    DATABASE = "database"                    # پایگاه داده
    OTHER = "other"                          # سایر

# نگاشت استانداردها به دسته‌بندی‌ها
STANDARD_TO_CATEGORY: Dict[DocumentStandard, MediaCategory] = {
    DocumentStandard.DSDM: MediaCategory.STRUCTURED_DATA,
    DocumentStandard.USDM: MediaCategory.DOCUMENT,
    DocumentStandard.ESDM: MediaCategory.SPREADSHEET,
    DocumentStandard.CSDM: MediaCategory.CAD_GEOMETRIC
}

# تعاریف مخفف‌ها برای مستندات
ABBREVIATIONS: Dict[str, str] = {
    # استانداردها
    "DSDM": "Data Structured Document Model",
    "USDM": "Unified Structured Document Model",
    "ESDM": "Excel/Spreadsheet Document Model", 
    "CSDM": "CAD/Geometric Structured Document Model",
    
    # کامپوننت‌ها
    "MIME": "Multipurpose Internet Mail Extensions",
    "API": "Application Programming Interface",
    "JSON": "JavaScript Object Notation",
    "XML": "eXtensible Markup Language",
    "YAML": "YAML Ain't Markup Language",
    "CSV": "Comma-Separated Values",
    "PDF": "Portable Document Format",
    "HTML": "HyperText Markup Language",
    "DOCX": "Microsoft Word Document",
    "XLSX": "Microsoft Excel Spreadsheet",
    
    # مفاهیم
    "AST": "Abstract Syntax Tree",
    "DOM": "Document Object Model",
    "SAX": "Simple API for XML",
    "STAX": "Streaming API for XML",
}

def get_standard_info(standard: DocumentStandard) -> Dict[str, Any]:
    """دریافت اطلاعات کامل یک استاندارد"""
    return {
        "code": standard.value,
        "name": standard.full_name,
        "description": standard.description,
        "category": STANDARD_TO_CATEGORY.get(standard),
        "common_formats": get_common_formats(standard)
    }

def get_common_formats(standard: DocumentStandard) -> list[str]:
    """دریافت فرمت‌های رایج برای هر استاندارد"""
    formats = {
        DocumentStandard.DSDM: ["json", "xml", "yaml", "toml", "csv", "tsv"],
        DocumentStandard.USDM: ["pdf", "docx", "html", "md", "txt", "rtf"],
        DocumentStandard.ESDM: ["xlsx", "xls", "csv", "ods", "parquet"],
        DocumentStandard.CSDM: ["dxf", "dwg", "ifc", "stl", "step"]
    }
    return formats.get(standard, [])
