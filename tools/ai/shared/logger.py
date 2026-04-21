#!/usr/bin/env python3
"""
Logger - Unified logging system for the AI development framework.

Part of the Shared module (shared/logger.py)

This logger.py provides:

Unified Logging System - Singleton manager for consistent logging
Multiple Formats - Console (colored), JSON, Detailed, Simple
File Rotation - Automatic log file rotation with size limits
Structured JSON Logging - Machine-readable JSON output
Sensitive Data Redaction - Automatic masking of passwords, tokens, keys
Context Management - Add request IDs, user info to log context
Buffered Logging - Performance optimization for high-volume logging
Log Decorators - @log_execution and @log_async for function logging
Configuration Integration - Uses shared Config system
Per-Module Log Levels - Fine-grained control over verbosity
Exception Tracking - Automatic traceback capture
CLI Interface - Command-line log configuration and testing

The logger provides a professional, feature-rich logging system that integrates seamlessly with the rest of the framework.
"""

import os
import sys
import json
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import contextmanager
import threading
import traceback

from .config import get_config, LogLevel


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class LogFormat(str, Enum):
    """Log output format."""
    CONSOLE = "console"
    JSON = "json"
    DETAILED = "detailed"
    SIMPLE = "simple"
    CUSTOM = "custom"


class LogDestination(str, Enum):
    """Log destination."""
    CONSOLE = "console"
    FILE = "file"
    BOTH = "both"
    SYSLOG = "syslog"
    HTTP = "http"


# ANSI color codes
COLORS = {
    'DEBUG': '\033[36m',      # Cyan
    'INFO': '\033[32m',       # Green
    'WARNING': '\033[33m',    # Yellow
    'ERROR': '\033[31m',      # Red
    'CRITICAL': '\033[35m',   # Magenta
    'RESET': '\033[0m'
}


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class LoggerConfig:
    """Logger configuration."""
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.CONSOLE
    destination: LogDestination = LogDestination.CONSOLE
    file_path: Optional[Path] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = False
    redact_sensitive: bool = True
    include_traceback: bool = True
    include_thread: bool = False
    include_process: bool = False
    custom_format: Optional[str] = None
    sensitive_patterns: List[str] = field(default_factory=lambda: [
        "password", "secret", "token", "key", "auth", "credential",
        "api_key", "apikey", "passwd", "pwd"
    ])
    json_indent: Optional[int] = None
    date_format: str = "%Y-%m-%d %H:%M:%S"
    module_filter: Optional[List[str]] = None
    enable_colors: bool = True
    buffered: bool = False
    buffer_size: int = 100


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: str
    module: str
    function: str
    line: int
    message: str
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[str] = None
    traceback: Optional[str] = None


# ============================================================
# CUSTOM FORMATTERS
# ============================================================

class ConsoleFormatter(logging.Formatter):
    """Colored console formatter."""
    
    def __init__(self, config: LoggerConfig):
        super().__init__()
        self.config = config
        self._fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        if self.config.enable_colors and record.levelname in COLORS:
            color = COLORS[record.levelname]
            reset = COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON log formatter."""
    
    def __init__(self, config: LoggerConfig):
        super().__init__()
        self.config = config
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created),
            level=record.levelname,
            module=record.name,
            function=record.funcName,
            line=record.lineno,
            message=record.getMessage(),
            thread_id=record.thread,
            process_id=record.process,
            extra=getattr(record, 'extra', {})
        )
        
        if record.exc_info:
            log_entry.exception = str(record.exc_info[1])
            if self.config.include_traceback:
                log_entry.traceback = ''.join(traceback.format_exception(*record.exc_info))
        
        result = {
            'timestamp': log_entry.timestamp.isoformat(),
            'level': log_entry.level,
            'module': log_entry.module,
            'function': log_entry.function,
            'line': log_entry.line,
            'message': log_entry.message,
        }
        
        if self.config.include_thread:
            result['thread_id'] = log_entry.thread_id
        if self.config.include_process:
            result['process_id'] = log_entry.process_id
        if log_entry.extra:
            result['extra'] = self._redact(log_entry.extra)
        if log_entry.exception:
            result['exception'] = log_entry.exception
        if log_entry.traceback:
            result['traceback'] = log_entry.traceback
        
        return json.dumps(result, indent=self.config.json_indent, default=str)
    
    def _redact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive information."""
        if not self.config.redact_sensitive:
            return data
        
        redacted = {}
        for key, value in data.items():
            if any(pattern in key.lower() for pattern in self.config.sensitive_patterns):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = self._redact(value)
            else:
                redacted[key] = value
        
        return redacted


class DetailedFormatter(logging.Formatter):
    """Detailed log formatter with all context."""
    
    def __init__(self, config: LoggerConfig):
        fmt = "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"
        super().__init__(fmt, datefmt=config.date_format)


# ============================================================
# BUFFERED HANDLER
# ============================================================

class BufferedHandler(logging.Handler):
    """Buffered log handler for batch processing."""
    
    def __init__(self, capacity: int = 100, target_handler: Optional[logging.Handler] = None):
        super().__init__()
        self.capacity = capacity
        self.buffer: List[logging.LogRecord] = []
        self.target_handler = target_handler
        self._lock = threading.Lock()
    
    def emit(self, record: logging.LogRecord):
        """Buffer the record."""
        with self._lock:
            self.buffer.append(record)
            if len(self.buffer) >= self.capacity:
                self.flush()
    
    def flush(self):
        """Flush buffered records to target handler."""
        with self._lock:
            if self.target_handler and self.buffer:
                for record in self.buffer:
                    self.target_handler.emit(record)
                self.buffer.clear()
    
    def close(self):
        """Close handler and flush."""
        self.flush()
        super().close()


# ============================================================
# LOGGER MANAGER
# ============================================================

class LoggerManager:
    """
    Unified logging system for the AI development framework.
    
    Features:
    - Multiple output formats (console, JSON, detailed)
    - File rotation with size limits
    - Colored console output
    - Structured JSON logging
    - Sensitive data redaction
    - Buffered logging for performance
    - Context managers for temporary logging
    - Per-module log levels
    - Thread-safe
    - Exception tracking with tracebacks
    """
    
    _instance: Optional['LoggerManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._loggers: Dict[str, logging.Logger] = {}
        self._config: Optional[LoggerConfig] = None
        self._handlers: List[logging.Handler] = []
        self._context_stack: List[Dict[str, Any]] = []
        self._buffered_handler: Optional[BufferedHandler] = None
        
        self._configure()
    
    def _configure(self):
        """Configure logging system."""
        # Get configuration
        try:
            app_config = get_config()
            self._config = LoggerConfig(
                level=app_config.logging.level,
                format=LogFormat(app_config.logging.format),
                destination=LogDestination.CONSOLE if app_config.logging.enable_console else LogDestination.FILE,
                file_path=app_config.logging.file,
                max_bytes=app_config.logging.max_bytes,
                backup_count=app_config.logging.backup_count,
                enable_console=app_config.logging.enable_console,
                enable_file=app_config.logging.enable_file,
                redact_sensitive=app_config.logging.redact_sensitive,
                sensitive_patterns=app_config.logging.sensitive_patterns
            )
        except Exception:
            # Use defaults if config not available
            self._config = LoggerConfig()
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self._get_logging_level(self._config.level))
        root_logger.handlers.clear()
        
        # Create handlers
        if self._config.enable_console:
            console_handler = self._create_console_handler()
            root_logger.addHandler(console_handler)
            self._handlers.append(console_handler)
        
        if self._config.enable_file and self._config.file_path:
            file_handler = self._create_file_handler()
            root_logger.addHandler(file_handler)
            self._handlers.append(file_handler)
        
        # Setup buffered handler if enabled
        if self._config.buffered:
            self._buffered_handler = BufferedHandler(
                capacity=self._config.buffer_size,
                target_handler=self._handlers[0] if self._handlers else None
            )
            root_logger.addHandler(self._buffered_handler)
        
        # Suppress noisy loggers
        self._suppress_noisy_loggers()
    
    def _get_logging_level(self, level: LogLevel) -> int:
        """Convert LogLevel to logging level."""
        return {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }.get(level, logging.INFO)
    
    def _create_console_handler(self) -> logging.Handler:
        """Create console handler."""
        handler = logging.StreamHandler(sys.stdout)
        
        if self._config.format == LogFormat.CONSOLE:
            formatter = ConsoleFormatter(self._config)
            handler.setFormatter(formatter)
        elif self._config.format == LogFormat.JSON:
            formatter = JSONFormatter(self._config)
            handler.setFormatter(formatter)
        elif self._config.format == LogFormat.DETAILED:
            formatter = DetailedFormatter(self._config)
            handler.setFormatter(formatter)
        elif self._config.format == LogFormat.SIMPLE:
            formatter = logging.Formatter("%(levelname)s: %(message)s")
            handler.setFormatter(formatter)
        elif self._config.custom_format:
            formatter = logging.Formatter(self._config.custom_format)
            handler.setFormatter(formatter)
        else:
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            handler.setFormatter(formatter)
        
        return handler
    
    def _create_file_handler(self) -> logging.Handler:
        """Create rotating file handler."""
        if not self._config.file_path:
            return None
        
        self._config.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            filename=str(self._config.file_path),
            maxBytes=self._config.max_bytes,
            backupCount=self._config.backup_count,
            encoding='utf-8'
        )
        
        if self._config.format == LogFormat.JSON:
            formatter = JSONFormatter(self._config)
        else:
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s",
                datefmt=self._config.date_format
            )
        
        handler.setFormatter(formatter)
        return handler
    
    def _suppress_noisy_loggers(self):
        """Suppress verbose third-party loggers."""
        noisy_loggers = [
            'urllib3', 'requests', 'charset_normalizer',
            'asyncio', 'aiohttp', 'websockets',
            'matplotlib', 'PIL', 'numexpr'
        ]
        
        for name in noisy_loggers:
            logging.getLogger(name).setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger."""
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        
        # Apply module filter if configured
        if self._config.module_filter:
            should_log = any(name.startswith(prefix) for prefix in self._config.module_filter)
            if not should_log:
                logger.setLevel(logging.WARNING)
        
        self._loggers[name] = logger
        return logger
    
    def set_level(self, level: Union[LogLevel, str], logger_name: Optional[str] = None):
        """Set log level for specific logger or root."""
        if isinstance(level, str):
            level = LogLevel(level.upper())
        
        log_level = self._get_logging_level(level)
        
        if logger_name:
            self.get_logger(logger_name).setLevel(log_level)
        else:
            logging.getLogger().setLevel(log_level)
            self._config.level = level
    
    def add_context(self, **kwargs) -> 'LogContext':
        """Add context to all subsequent log messages."""
        return LogContext(self, **kwargs)
    
    def _push_context(self, context: Dict[str, Any]):
        """Push context to stack."""
        self._context_stack.append(context)
    
    def _pop_context(self):
        """Pop context from stack."""
        if self._context_stack:
            self._context_stack.pop()
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context."""
        context = {}
        for ctx in self._context_stack:
            context.update(ctx)
        return context
    
    def flush(self):
        """Flush all handlers."""
        if self._buffered_handler:
            self._buffered_handler.flush()
        for handler in self._handlers:
            handler.flush()
    
    def close(self):
        """Close all handlers."""
        self.flush()
        for handler in self._handlers:
            handler.close()
    
    def reconfigure(self, config: Optional[LoggerConfig] = None):
        """Reconfigure logging system."""
        if config:
            self._config = config
        self._configure()


class LogContext:
    """Context manager for temporary logging context."""
    
    def __init__(self, manager: LoggerManager, **kwargs):
        self.manager = manager
        self.context = kwargs
    
    def __enter__(self):
        self.manager._push_context(self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager._pop_context()
    
    def add(self, **kwargs):
        """Add more context."""
        self.context.update(kwargs)


# ============================================================
# CONTEXT FILTER
# ============================================================

class ContextFilter(logging.Filter):
    """Filter to add context to log records."""
    
    def __init__(self, manager: LoggerManager):
        super().__init__()
        self.manager = manager
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to record."""
        context = self.manager.get_context()
        if context:
            record.extra = getattr(record, 'extra', {})
            record.extra.update(context)
        return True


# ============================================================
# PUBLIC API
# ============================================================

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    manager = LoggerManager()
    logger = manager.get_logger(name)
    
    # Add context filter
    context_filter = ContextFilter(manager)
    if context_filter not in logger.filters:
        logger.addFilter(context_filter)
    
    return logger


def set_log_level(level: Union[LogLevel, str], logger_name: Optional[str] = None):
    """Set log level."""
    LoggerManager().set_level(level, logger_name)


def add_log_context(**kwargs) -> LogContext:
    """Add context to logs."""
    return LoggerManager().add_context(**kwargs)


def flush_logs():
    """Flush all log handlers."""
    LoggerManager().flush()


def reconfigure_logging(config: Optional[LoggerConfig] = None):
    """Reconfigure logging system."""
    LoggerManager().reconfigure(config)


# ============================================================
# DECORATORS
# ============================================================

def log_execution(level: LogLevel = LogLevel.DEBUG, log_args: bool = True, log_result: bool = False):
    """Decorator to log function execution."""
    def decorator(func):
        logger = get_logger(func.__module__)
        
        def wrapper(*args, **kwargs):
            if log_args:
                args_str = ', '.join(repr(a) for a in args)
                kwargs_str = ', '.join(f"{k}={repr(v)}" for k, v in kwargs.items())
                params = args_str + (', ' if args_str and kwargs_str else '') + kwargs_str
                logger.log(level, f"Calling {func.__name__}({params})")
            else:
                logger.log(level, f"Calling {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                if log_result:
                    logger.log(level, f"{func.__name__} returned: {repr(result)}")
                else:
                    logger.log(level, f"{func.__name__} completed")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} failed: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator


def log_async(level: LogLevel = LogLevel.DEBUG):
    """Decorator for async function logging."""
    def decorator(func):
        logger = get_logger(func.__module__)
        
        async def wrapper(*args, **kwargs):
            logger.log(level, f"Async call: {func.__name__}")
            try:
                result = await func(*args, **kwargs)
                logger.log(level, f"Async completed: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Async failed: {func.__name__}: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for logger configuration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Configure logging")
    parser.add_argument("--level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       default="INFO", help="Log level")
    parser.add_argument("--format", choices=["console", "json", "detailed", "simple"],
                       default="console", help="Log format")
    parser.add_argument("--file", type=Path, help="Log file path")
    parser.add_argument("--no-console", action="store_true", help="Disable console output")
    parser.add_argument("--no-colors", action="store_true", help="Disable colored output")
    parser.add_argument("--test", action="store_true", help="Test logging")
    
    args = parser.parse_args()
    
    if args.test:
        # Test logging
        logger = get_logger("test")
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        logger.critical("This is a critical message")
        
        with add_log_context(request_id="123", user="test"):
            logger.info("This message has context")
        
        return
    
    # Reconfigure logging
    config = LoggerConfig(
        level=LogLevel(args.level),
        format=LogFormat(args.format),
        file_path=args.file,
        enable_console=not args.no_console,
        enable_colors=not args.no_colors,
        enable_file=args.file is not None
    )
    
    reconfigure_logging(config)
    logger = get_logger(__name__)
    logger.info("Logging reconfigured")


if __name__ == "__main__":
    main()