# engines/document/models/exceptions.py
from typing import Optional
"""
سیستم خطاهای سلسله‌مراتبی برای مدیریت اسناد
"""

class DocumentError(Exception):
    """خطای پایه برای تمام خطاهای مربوط به اسناد"""
    pass


class DocumentParseError(DocumentError):
    """خطا در هنگام پارس کردن سند"""
    pass


class DocumentWriteError(DocumentError):
    """خطا در هنگام نوشتن سند"""
    pass


class DocumentValidationError(DocumentError):
    """خطا در اعتبارسنجی سند"""
    pass


class UnsupportedFormatError(DocumentError):
    """فرمت سند پشتیبانی نمی‌شود"""
    def __init__(self, format_name: str, supported_formats: Optional[list[str]] = None):
        self.format_name = format_name
        self.supported_formats = supported_formats or []
        message = f"فرمت '{format_name}' پشتیبانی نمی‌شود"
        if supported_formats:
            message += f". فرمت‌های پشتیبانی شده: {', '.join(supported_formats)}"
        super().__init__(message)


class BinaryEncodingError(DocumentError):
    """خطا در کدگذاری/کدگشایی باینری"""
    pass


class StreamingError(DocumentError):
    """خطا در عملیات استریمینگ"""
    pass


class RegistryError(DocumentError):
    """خطا در سیستم رجیستری"""
    pass


class CompressionError(DocumentError):
    """خطا در فشرده‌سازی/رفع فشردگی"""
    pass


class SchemaValidationError(DocumentValidationError):
    """خطا در اعتبارسنجی schema"""
    pass


class ContentDetectionError(DocumentError):
    """خطا در تشخیص محتوا"""
    pass
