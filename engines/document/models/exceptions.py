# engines/document/models/exceptions.py
"""
سیستم خطاهای سلسله‌مراتبی برای مدیریت اسناد
"""

class DocumentError(Exception):
    """خطای پایه برای تمام خطاهای مربوط به اسناد"""


class DocumentParseError(DocumentError):
    """خطا در هنگام پارس کردن سند"""


class DocumentWriteError(DocumentError):
    """خطا در هنگام نوشتن سند"""


class DocumentValidationError(DocumentError):
    """خطا در اعتبارسنجی سند"""


class UnsupportedFormatError(DocumentError):
    """فرمت سند پشتیبانی نمی‌شود"""
    def __init__(self, format_name: str, supported_formats: list[str] | None = None):
        self.format_name = format_name
        self.supported_formats = supported_formats or []
        message = f"فرمت '{format_name}' پشتیبانی نمی‌شود"
        if supported_formats:
            message += f". فرمت‌های پشتیبانی شده: {', '.join(supported_formats)}"
        super().__init__(message)


class BinaryEncodingError(DocumentError):
    """خطا در کدگذاری/کدگشایی باینری"""


class StreamingError(DocumentError):
    """خطا در عملیات استریمینگ"""


class RegistryError(DocumentError):
    """خطا در سیستم رجیستری"""


class CompressionError(DocumentError):
    """خطا در فشرده‌سازی/رفع فشردگی"""


class SchemaValidationError(DocumentValidationError):
    """خطا در اعتبارسنجی schema"""


class ContentDetectionError(DocumentError):
    """خطا در تشخیص محتوا"""
