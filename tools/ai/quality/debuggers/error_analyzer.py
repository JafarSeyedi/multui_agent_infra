#!/usr/bin/env python3
"""
Error Analyzer - Analyzes errors, exceptions, and stack traces for debugging.

Part of the Quality tools (quality/debuggers/error_analyzer.py)

This error_analyzer.py provides:

1. Exception Parsing - Parses Python exceptions and tracebacks
2. Error Categorization - Classifies errors into 20+ categories
3. Root Cause Analysis - Identifies underlying causes with confidence levels
4. Fix Suggestion Generation - Rule-based and LLM-powered fix suggestions
5. Context Extraction - Extracts code context around error location
6. Similar Error Detection - Finds patterns in historical errors
7. AST-Based Analysis - Uses AST to find undefined variables, missing imports
8. Auto-Fix Capability - Identifies auto-fixable issues
9. Resolution Time Estimation - Estimates time to fix based on severity
10. Multiple Input Sources - Exception objects, traceback strings, files, stdin
11. Comprehensive Reporting - JSON and Markdown formats
12. Error History Tracking - Maintains history for pattern detection

The error analyzer helps developers quickly understand and fix errors by providing actionable insights and specific fix suggestions.


"""

import ast
import re
import sys
import traceback
import linecache
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ....shared.llm_client import LLMClient
from ....shared.state_manager import StateManager
from ....shared.logger import get_logger
from ....analysis.scanners.ast_analyzer import ASTAnalyzer
from ....analysis.scanners.project_scanner import ProjectScanner

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class ErrorCategory(str, Enum):
    """Category of error."""
    SYNTAX_ERROR = "syntax_error"
    TYPE_ERROR = "type_error"
    NAME_ERROR = "name_error"
    ATTRIBUTE_ERROR = "attribute_error"
    IMPORT_ERROR = "import_error"
    INDEX_ERROR = "index_error"
    KEY_ERROR = "key_error"
    VALUE_ERROR = "value_error"
    ZERO_DIVISION_ERROR = "zero_division_error"
    FILE_NOT_FOUND_ERROR = "file_not_found_error"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT_ERROR = "timeout_error"
    CONNECTION_ERROR = "connection_error"
    ASSERTION_ERROR = "assertion_error"
    RUNTIME_ERROR = "runtime_error"
    MEMORY_ERROR = "memory_error"
    RECURSION_ERROR = "recursion_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(str, Enum):
    """Severity of error."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RootCauseType(str, Enum):
    """Type of root cause."""
    MISSING_IMPORT = "missing_import"
    UNDEFINED_VARIABLE = "undefined_variable"
    WRONG_TYPE = "wrong_type"
    NONE_ACCESS = "none_access"
    OUT_OF_BOUNDS = "out_of_bounds"
    MISSING_KEY = "missing_key"
    INVALID_VALUE = "invalid_value"
    DIVISION_BY_ZERO = "division_by_zero"
    FILE_MISSING = "file_missing"
    PERMISSION_DENIED = "permission_denied"
    NETWORK_ISSUE = "network_issue"
    ASSERTION_FAILED = "assertion_failed"
    INFINITE_RECURSION = "infinite_recursion"
    MEMORY_EXHAUSTED = "memory_exhausted"
    LOGIC_ERROR = "logic_error"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """Confidence level of analysis."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SPECULATIVE = "speculative"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class StackFrame:
    """Represents a single stack frame."""
    file_path: str
    line_number: int
    function_name: str
    code_line: str
    locals_summary: Dict[str, str] = field(default_factory=dict)
    is_project_code: bool = True
    is_entry_point: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorInfo:
    """Information about an error."""
    error_type: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    traceback: List[StackFrame] = field(default_factory=list)
    exception: Optional[Exception] = None
    context_code: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RootCause:
    """Root cause analysis result."""
    cause_type: RootCauseType
    description: str
    confidence: ConfidenceLevel
    evidence: List[str] = field(default_factory=list)
    fix_suggestion: Optional[str] = None
    code_fix: Optional[str] = None
    related_files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FixSuggestion:
    """A suggested fix for an error."""
    title: str
    description: str
    code_changes: List[Dict[str, Any]] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    auto_fixable: bool = False
    requires_import: bool = False
    estimated_effort: str = "low"  # low, medium, high
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorAnalysisReport:
    """Complete error analysis report."""
    analyzed_at: datetime = field(default_factory=datetime.now)
    error: ErrorInfo = field(default_factory=ErrorInfo)
    root_causes: List[RootCause] = field(default_factory=list)
    fix_suggestions: List[FixSuggestion] = field(default_factory=list)
    similar_errors: List[Dict[str, Any]] = field(default_factory=list)
    impacted_code: List[str] = field(default_factory=list)
    complexity_at_error: Optional[int] = None
    test_coverage_at_error: Optional[float] = None
    is_resolvable: bool = True
    resolution_time_estimate: str = "unknown"
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorAnalyzerConfig:
    """Configuration for error analyzer."""
    project_root: Path
    max_context_lines: int = 10
    max_traceback_depth: int = 20
    analyze_imports: bool = True
    analyze_dependencies: bool = True
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    find_similar_errors: bool = True
    suggest_fixes: bool = True
    auto_apply_safe_fixes: bool = False
    include_locals: bool = False
    redact_sensitive: bool = True
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", ".git", ".venv", "venv", "site-packages"
    ])
    sensitive_patterns: List[str] = field(default_factory=lambda: [
        "password", "secret", "token", "key", "auth", "credential"
    ])


# ============================================================
# ERROR PARSER
# ============================================================

class ErrorParser:
    """Parse errors and exceptions into structured data."""
    
    def __init__(self, config: ErrorAnalyzerConfig):
        self.config = config
    
    def parse_exception(self, exc: Exception, tb: Optional[Any] = None) -> ErrorInfo:
        """Parse an exception into ErrorInfo."""
        error_type = type(exc).__name__
        error_message = str(exc)
        category = self._categorize_error(error_type, error_message)
        severity = self._determine_severity(category, error_message)
        
        # Extract traceback
        if tb is None:
            tb = exc.__traceback__
        
        traceback_frames = []
        if tb:
            frames = traceback.extract_tb(tb, limit=self.config.max_traceback_depth)
            
            for frame in frames:
                is_project = self._is_project_file(frame.filename)
                
                # Skip frames from excluded paths
                if not is_project and not self._should_include_frame(frame):
                    continue
                
                code_line = frame.line or linecache.getline(frame.filename, frame.lineno).strip()
                
                traceback_frames.append(StackFrame(
                    file_path=frame.filename,
                    line_number=frame.lineno,
                    function_name=frame.name,
                    code_line=code_line,
                    is_project_code=is_project,
                    is_entry_point=frame.name == '<module>'
                ))
        
        # Get context code from the error location
        context_code = []
        if traceback_frames:
            last_frame = traceback_frames[-1]
            if last_frame.file_path and last_frame.line_number:
                context_code = self._extract_context(
                    last_frame.file_path, 
                    last_frame.line_number
                )
        
        return ErrorInfo(
            error_type=error_type,
            error_message=error_message,
            category=category,
            severity=severity,
            file_path=traceback_frames[-1].file_path if traceback_frames else None,
            line_number=traceback_frames[-1].line_number if traceback_frames else None,
            traceback=traceback_frames,
            exception=exc,
            context_code=context_code
        )
    
    def parse_traceback(self, tb_text: str) -> ErrorInfo:
        """Parse a traceback string into ErrorInfo."""
        lines = tb_text.strip().split('\n')
        
        # Extract error type and message (last line)
        error_line = lines[-1] if lines else ""
        error_match = re.match(r'^(\w+(?:\.\w+)*):\s*(.+)$', error_line)
        
        if error_match:
            error_type = error_match.group(1)
            error_message = error_match.group(2)
        else:
            error_type = "UnknownError"
            error_message = error_line
        
        category = self._categorize_error(error_type, error_message)
        severity = self._determine_severity(category, error_message)
        
        # Parse stack frames
        traceback_frames = []
        frame_pattern = re.compile(
            r'^\s*File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+(\w+)'
        )
        
        for line in lines[:-1]:
            match = frame_pattern.search(line)
            if match:
                file_path = match.group(1)
                line_number = int(match.group(2))
                function_name = match.group(3)
                
                is_project = self._is_project_file(file_path)
                
                if is_project or self._should_include_frame_by_path(file_path):
                    code_line = linecache.getline(file_path, line_number).strip()
                    
                    traceback_frames.append(StackFrame(
                        file_path=file_path,
                        line_number=line_number,
                        function_name=function_name,
                        code_line=code_line,
                        is_project_code=is_project,
                        is_entry_point=function_name == '<module>'
                    ))
        
        return ErrorInfo(
            error_type=error_type,
            error_message=error_message,
            category=category,
            severity=severity,
            file_path=traceback_frames[-1].file_path if traceback_frames else None,
            line_number=traceback_frames[-1].line_number if traceback_frames else None,
            traceback=traceback_frames
        )
    
    def parse_syntax_error(self, exc: SyntaxError) -> ErrorInfo:
        """Parse a syntax error."""
        error_message = str(exc)
        
        return ErrorInfo(
            error_type="SyntaxError",
            error_message=error_message,
            category=ErrorCategory.SYNTAX_ERROR,
            severity=ErrorSeverity.CRITICAL,
            file_path=exc.filename,
            line_number=exc.lineno,
            column_number=exc.offset,
            exception=exc
        )
    
    def _categorize_error(self, error_type: str, error_message: str) -> ErrorCategory:
        """Categorize error based on type and message."""
        error_lower = error_type.lower()
        msg_lower = error_message.lower()
        
        if 'syntax' in error_lower:
            return ErrorCategory.SYNTAX_ERROR
        elif 'type' in error_lower:
            return ErrorCategory.TYPE_ERROR
        elif 'name' in error_lower:
            return ErrorCategory.NAME_ERROR
        elif 'attribute' in error_lower:
            return ErrorCategory.ATTRIBUTE_ERROR
        elif 'import' in error_lower or 'modulenotfound' in error_lower:
            return ErrorCategory.IMPORT_ERROR
        elif 'index' in error_lower:
            return ErrorCategory.INDEX_ERROR
        elif 'key' in error_lower:
            return ErrorCategory.KEY_ERROR
        elif 'value' in error_lower:
            return ErrorCategory.VALUE_ERROR
        elif 'zerodivision' in error_lower:
            return ErrorCategory.ZERO_DIVISION_ERROR
        elif 'file' in error_lower and 'not found' in msg_lower:
            return ErrorCategory.FILE_NOT_FOUND_ERROR
        elif 'permission' in error_lower:
            return ErrorCategory.PERMISSION_ERROR
        elif 'timeout' in error_lower:
            return ErrorCategory.TIMEOUT_ERROR
        elif 'connection' in error_lower:
            return ErrorCategory.CONNECTION_ERROR
        elif 'assertion' in error_lower:
            return ErrorCategory.ASSERTION_ERROR
        elif 'memory' in error_lower:
            return ErrorCategory.MEMORY_ERROR
        elif 'recursion' in error_lower:
            return ErrorCategory.RECURSION_ERROR
        elif 'runtime' in error_lower:
            return ErrorCategory.RUNTIME_ERROR
        else:
            return ErrorCategory.UNKNOWN_ERROR
    
    def _determine_severity(self, category: ErrorCategory, message: str) -> ErrorSeverity:
        """Determine error severity."""
        if category in (ErrorCategory.SYNTAX_ERROR, ErrorCategory.IMPORT_ERROR,
                        ErrorCategory.MEMORY_ERROR, ErrorCategory.RECURSION_ERROR):
            return ErrorSeverity.CRITICAL
        
        if category in (ErrorCategory.TYPE_ERROR, ErrorCategory.ATTRIBUTE_ERROR,
                        ErrorCategory.NAME_ERROR):
            return ErrorSeverity.HIGH
        
        if category in (ErrorCategory.INDEX_ERROR, ErrorCategory.KEY_ERROR,
                        ErrorCategory.VALUE_ERROR, ErrorCategory.ZERO_DIVISION_ERROR):
            return ErrorSeverity.MEDIUM
        
        if 'deprecated' in message.lower():
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _is_project_file(self, file_path: str) -> bool:
        """Check if file is part of the project."""
        if not file_path or file_path == '<string>' or file_path == '<stdin>':
            return False
        
        # Check if under project root
        try:
            Path(file_path).relative_to(self.config.project_root)
            return True
        except ValueError:
            pass
        
        # Check ignore patterns
        for pattern in self.config.ignore_patterns:
            if pattern in file_path:
                return False
        
        return False
    
    def _should_include_frame(self, frame) -> bool:
        """Check if frame should be included despite not being project code."""
        # Include frames from standard library that might be relevant
        important_modules = {'asyncio', 'concurrent', 'threading', 'multiprocessing'}
        for mod in important_modules:
            if mod in frame.filename:
                return True
        return False
    
    def _should_include_frame_by_path(self, file_path: str) -> bool:
        """Check if frame should be included by path."""
        important_modules = {'asyncio', 'concurrent', 'threading', 'multiprocessing'}
        for mod in important_modules:
            if mod in file_path:
                return True
        return False
    
    def _extract_context(self, file_path: str, line_number: int) -> List[str]:
        """Extract context lines around error location."""
        context = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start = max(0, line_number - self.config.max_context_lines - 1)
            end = min(len(lines), line_number + self.config.max_context_lines)
            
            for i in range(start, end):
                line = lines[i].rstrip()
                marker = ">>> " if i == line_number - 1 else "    "
                context.append(f"{marker}{i + 1:4d}: {line}")
                
        except Exception:
            pass
        
        return context


# ============================================================
# ROOT CAUSE ANALYZER
# ============================================================

class RootCauseAnalyzer:
    """Analyze root causes of errors."""
    
    def __init__(self, config: ErrorAnalyzerConfig):
        self.config = config
        self.scanner = ProjectScanner(project_root=config.project_root)
        self.ast_analyzer = ASTAnalyzer()
    
    def analyze(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze root causes of an error."""
        causes = []
        
        # Analyze based on error category
        if error.category == ErrorCategory.IMPORT_ERROR:
            causes.extend(self._analyze_import_error(error))
        elif error.category == ErrorCategory.NAME_ERROR:
            causes.extend(self._analyze_name_error(error))
        elif error.category == ErrorCategory.ATTRIBUTE_ERROR:
            causes.extend(self._analyze_attribute_error(error))
        elif error.category == ErrorCategory.TYPE_ERROR:
            causes.extend(self._analyze_type_error(error))
        elif error.category == ErrorCategory.INDEX_ERROR:
            causes.extend(self._analyze_index_error(error))
        elif error.category == ErrorCategory.KEY_ERROR:
            causes.extend(self._analyze_key_error(error))
        elif error.category == ErrorCategory.VALUE_ERROR:
            causes.extend(self._analyze_value_error(error))
        elif error.category == ErrorCategory.ZERO_DIVISION_ERROR:
            causes.extend(self._analyze_zero_division_error(error))
        elif error.category == ErrorCategory.FILE_NOT_FOUND_ERROR:
            causes.extend(self._analyze_file_not_found_error(error))
        elif error.category == ErrorCategory.RECURSION_ERROR:
            causes.extend(self._analyze_recursion_error(error))
        elif error.category == ErrorCategory.SYNTAX_ERROR:
            causes.extend(self._analyze_syntax_error(error))
        else:
            causes.extend(self._analyze_generic_error(error))
        
        # Enhance with AST analysis if possible
        if error.file_path and error.line_number:
            ast_causes = self._analyze_with_ast(error)
            causes.extend(ast_causes)
        
        return causes
    
    def _analyze_import_error(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze import error."""
        causes = []
        
        # Extract module name from error message
        import_match = re.search(r"No module named ['\"]?(\w+)['\"]?", error.error_message)
        if import_match:
            module_name = import_match.group(1)
            
            causes.append(RootCause(
                cause_type=RootCauseType.MISSING_IMPORT,
                description=f"Module '{module_name}' is not installed or not in PYTHONPATH",
                confidence=ConfidenceLevel.HIGH,
                evidence=[f"ImportError: {error.error_message}"],
                fix_suggestion=f"Install the missing module: pip install {module_name}",
                code_fix=f"# Add to requirements.txt\n{module_name}",
                related_files=self._find_files_importing(module_name)
            ))
        
        # Check for relative import issues
        if 'relative import' in error.error_message.lower():
            causes.append(RootCause(
                cause_type=RootCauseType.CONFIGURATION_ERROR,
                description="Relative import used outside of package context",
                confidence=ConfidenceLevel.HIGH,
                evidence=[error.error_message],
                fix_suggestion="Use absolute imports or ensure the module is run as part of a package"
            ))
        
        return causes
    
    def _analyze_name_error(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze name error."""
        causes = []
        
        # Extract undefined name
        name_match = re.search(r"name ['\"]?(\w+)['\"]? is not defined", error.error_message)
        if name_match:
            var_name = name_match.group(1)
            
            # Check if it's a typo of a defined variable
            if error.file_path and error.line_number:
                defined_vars = self._get_defined_variables(error.file_path, error.line_number)
                similar = self._find_similar_names(var_name, defined_vars)
                
                if similar:
                    causes.append(RootCause(
                        cause_type=RootCauseType.UNDEFINED_VARIABLE,
                        description=f"Variable '{var_name}' not defined. Did you mean '{similar[0]}'?",
                        confidence=ConfidenceLevel.HIGH,
                        evidence=[f"Similar variables: {', '.join(similar)}"],
                        fix_suggestion=f"Rename '{var_name}' to '{similar[0]}'",
                        code_fix=f"# Replace '{var_name}' with '{similar[0]}'"
                    ))
                else:
                    causes.append(RootCause(
                        cause_type=RootCauseType.UNDEFINED_VARIABLE,
                        description=f"Variable '{var_name}' is not defined in this scope",
                        confidence=ConfidenceLevel.HIGH,
                        evidence=[error.error_message],
                        fix_suggestion=f"Define '{var_name}' before using it or import it if it's from another module"
                    ))
        
        return causes
    
    def _analyze_attribute_error(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze attribute error."""
        causes = []
        
        # Extract object and attribute
        attr_match = re.search(r"['\"]?(\w+)['\"]? object has no attribute ['\"]?(\w+)['\"]?", error.error_message)
        if attr_match:
            obj_type = attr_match.group(1)
            attr_name = attr_match.group(2)
            
            causes.append(RootCause(
                cause_type=RootCauseType.NONE_ACCESS if obj_type == 'NoneType' else RootCauseType.LOGIC_ERROR,
                description=f"'{obj_type}' object has no attribute '{attr_name}'",
                confidence=ConfidenceLevel.HIGH,
                evidence=[error.error_message],
                fix_suggestion=f"Check if the object is of the expected type. If it's None, handle the None case."
            ))
        
        # Check for None access
        if 'NoneType' in error.error_message:
            causes.append(RootCause(
                cause_type=RootCauseType.NONE_ACCESS,
                description="Attempted to access attribute on None object",
                confidence=ConfidenceLevel.HIGH,
                evidence=[error.error_message],
                fix_suggestion="Add a check for None before accessing the attribute"
            ))
        
        return causes
    
    def _analyze_type_error(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze type error."""
        causes = []
        
        causes.append(RootCause(
            cause_type=RootCauseType.WRONG_TYPE,
            description="Operation performed on incompatible types",
            confidence=ConfidenceLevel.MEDIUM,
            evidence=[error.error_message],
            fix_suggestion="Check the types of variables and ensure they match expected types"
        ))
        
        return causes
    
    def _analyze_index_error(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze index error."""
        causes = []
        
        causes.append(RootCause(
            cause_type=RootCauseType.OUT_OF_BOUNDS,
            description="Index out of range - attempted to access element beyond sequence length",
            confidence=ConfidenceLevel.HIGH,
            evidence=[error.error_message],
            fix_suggestion="Check the length of the sequence before accessing by index"
        ))
        
        return causes
    
    def _analyze_key_error(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze key error."""
        causes = []
        
        # Extract missing key
        key_match = re.search(r"KeyError: ['\"]?(\w+)['\"]?", error.error_message)
        if key_match:
            key_name = key_match.group(1)
            
            causes.append(RootCause(
                cause_type=RootCauseType.MISSING_KEY,
                description=f"Key '{key_name}' not found in dictionary",
                confidence=ConfidenceLevel.HIGH,
                evidence=[error.error_message],
                fix_suggestion=f"Use .get('{key_name}', default) or check if key exists before accessing"
            ))
        
        return causes
    
    def _analyze_value_error(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze value error."""
        causes = []
        
        causes.append(RootCause(
            cause_type=RootCauseType.INVALID_VALUE,
            description="Invalid value provided to operation",
            confidence=ConfidenceLevel.MEDIUM,
            evidence=[error.error_message],
            fix_suggestion="Check the input value and ensure it meets the expected format/constraints"
        ))
        
        return causes
    
    def _analyze_zero_division_error(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze zero division error."""
        causes = []
        
        causes.append(RootCause(
            cause_type=RootCauseType.DIVISION_BY_ZERO,
            description="Division by zero attempted",
            confidence=ConfidenceLevel.HIGH,
            evidence=[error.error_message],
            fix_suggestion="Check denominator before division, or use try/except ZeroDivisionError"
        ))
        
        return causes
    
    def _analyze_file_not_found_error(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze file not found error."""
        causes = []
        
        # Extract file path
        path_match = re.search(r"No such file or directory: ['\"]?([^'\"]+)['\"]?", error.error_message)
        if path_match:
            file_path = path_match.group(1)
            
            # Check if path exists with different case
            causes.append(RootCause(
                cause_type=RootCauseType.FILE_MISSING,
                description=f"File '{file_path}' not found",
                confidence=ConfidenceLevel.HIGH,
                evidence=[error.error_message],
                fix_suggestion="Check if the file exists and the path is correct"
            ))
        
        return causes
    
    def _analyze_recursion_error(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze recursion error."""
        causes = []
        
        # Find function causing recursion
        if error.traceback:
            func_names = [f.function_name for f in error.traceback]
            func_counts = defaultdict(int)
            for name in func_names:
                func_counts[name] += 1
            
            for name, count in func_counts.items():
                if count > 10:
                    causes.append(RootCause(
                        cause_type=RootCauseType.INFINITE_RECURSION,
                        description=f"Function '{name}' called recursively {count} times",
                        confidence=ConfidenceLevel.HIGH,
                        evidence=[f"Function '{name}' appears {count} times in traceback"],
                        fix_suggestion=f"Check the base case in '{name}' or convert to iterative approach"
                    ))
                    break
        
        if not causes:
            causes.append(RootCause(
                cause_type=RootCauseType.INFINITE_RECURSION,
                description="Maximum recursion depth exceeded",
                confidence=ConfidenceLevel.HIGH,
                evidence=[error.error_message],
                fix_suggestion="Check for missing base case or convert to iterative solution"
            ))
        
        return causes
    
    def _analyze_syntax_error(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze syntax error."""
        causes = []
        
        causes.append(RootCause(
            cause_type=RootCauseType.LOGIC_ERROR,
            description=f"Syntax error: {error.error_message}",
            confidence=ConfidenceLevel.HIGH,
            evidence=[error.error_message],
            fix_suggestion="Check the syntax at the indicated line"
        ))
        
        return causes
    
    def _analyze_generic_error(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze generic/unclassified error."""
        causes = []
        
        causes.append(RootCause(
            cause_type=RootCauseType.UNKNOWN,
            description=f"Unclassified error: {error.error_type}",
            confidence=ConfidenceLevel.LOW,
            evidence=[error.error_message],
            fix_suggestion="Review the error message and traceback for clues"
        ))
        
        return causes
    
    def _analyze_with_ast(self, error: ErrorInfo) -> List[RootCause]:
        """Analyze error using AST."""
        causes = []
        
        try:
            with open(error.file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            # Find the node at error location
            error_node = self._find_node_at_line(tree, error.line_number)
            if error_node:
                # Analyze the node for potential issues
                if isinstance(error_node, ast.Call):
                    # Check if function exists
                    if isinstance(error_node.func, ast.Name):
                        func_name = error_node.func.id
                        if not self._is_function_defined(func_name, tree):
                            causes.append(RootCause(
                                cause_type=RootCauseType.UNDEFINED_VARIABLE,
                                description=f"Function '{func_name}' is called but not defined",
                                confidence=ConfidenceLevel.HIGH,
                                fix_suggestion=f"Define '{func_name}' or import it"
                            ))
        
        except Exception:
            pass
        
        return causes
    
    def _find_node_at_line(self, tree: ast.AST, line_number: int) -> Optional[ast.AST]:
        """Find AST node at given line number."""
        for node in ast.walk(tree):
            if hasattr(node, 'lineno') and node.lineno == line_number:
                return node
        return None
    
    def _is_function_defined(self, name: str, tree: ast.AST) -> bool:
        """Check if function is defined in AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return True
        return False
    
    def _get_defined_variables(self, file_path: str, line_number: int) -> Set[str]:
        """Get variables defined before a line."""
        variables = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if hasattr(node, 'lineno') and node.lineno < line_number:
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                variables.add(target.id)
                    elif isinstance(node, ast.AnnAssign):
                        if isinstance(node.target, ast.Name):
                            variables.add(node.target.id)
                    elif isinstance(node, ast.FunctionDef):
                        variables.add(node.name)
                        for arg in node.args.args:
                            variables.add(arg.arg)
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            variables.add(alias.asname or alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            variables.add(alias.asname or alias.name)
        
        except Exception:
            pass
        
        return variables
    
    def _find_similar_names(self, target: str, candidates: Set[str], threshold: float = 0.7) -> List[str]:
        """Find similar names using Levenshtein distance."""
        import difflib
        
        similar = []
        for candidate in candidates:
            ratio = difflib.SequenceMatcher(None, target.lower(), candidate.lower()).ratio()
            if ratio >= threshold:
                similar.append((candidate, ratio))
        
        similar.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in similar[:3]]
    
    def _find_files_importing(self, module_name: str) -> List[str]:
        """Find files that import a module."""
        files = []
        
        for py_file in self.config.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()
                if f"import {module_name}" in content or f"from {module_name}" in content:
                    files.append(str(py_file))
            except Exception:
                pass
        
        return files


# ============================================================
# FIX SUGGESTION GENERATOR
# ============================================================

class FixSuggestionGenerator:
    """Generate fix suggestions for errors."""
    
    def __init__(self, config: ErrorAnalyzerConfig):
        self.config = config
        self.llm = LLMClient() if config.use_llm else None
    
    def generate(self, error: ErrorInfo, root_causes: List[RootCause]) -> List[FixSuggestion]:
        """Generate fix suggestions."""
        suggestions = []
        
        # Rule-based suggestions
        for cause in root_causes:
            if cause.fix_suggestion:
                suggestion = FixSuggestion(
                    title=f"Fix: {cause.cause_type.value}",
                    description=cause.fix_suggestion,
                    code_fix=cause.code_fix,
                    confidence=cause.confidence,
                    auto_fixable=self._is_auto_fixable(cause),
                    estimated_effort=self._estimate_effort(cause)
                )
                suggestions.append(suggestion)
        
        # Category-specific suggestions
        if error.category == ErrorCategory.IMPORT_ERROR:
            suggestions.extend(self._suggest_import_fixes(error))
        elif error.category == ErrorCategory.NAME_ERROR:
            suggestions.extend(self._suggest_name_fixes(error))
        elif error.category == ErrorCategory.ATTRIBUTE_ERROR:
            suggestions.extend(self._suggest_attribute_fixes(error))
        elif error.category == ErrorCategory.TYPE_ERROR:
            suggestions.extend(self._suggest_type_fixes(error))
        
        # LLM-powered suggestions
        if self.llm and len(suggestions) < 3:
            llm_suggestions = self._generate_llm_suggestions(error, root_causes)
            suggestions.extend(llm_suggestions)
        
        return suggestions
    
    def _is_auto_fixable(self, cause: RootCause) -> bool:
        """Check if cause can be auto-fixed."""
        auto_fixable_causes = {
            RootCauseType.MISSING_IMPORT,
            RootCauseType.UNDEFINED_VARIABLE,
            RootCauseType.MISSING_KEY
        }
        return cause.cause_type in auto_fixable_causes
    
    def _estimate_effort(self, cause: RootCause) -> str:
        """Estimate fix effort."""
        if cause.cause_type in (RootCauseType.MISSING_IMPORT, RootCauseType.MISSING_KEY):
            return "low"
        elif cause.cause_type in (RootCauseType.INFINITE_RECURSION, RootCauseType.MEMORY_EXHAUSTED):
            return "high"
        else:
            return "medium"
    
    def _suggest_import_fixes(self, error: ErrorInfo) -> List[FixSuggestion]:
        """Suggest fixes for import errors."""
        suggestions = []
        
        # Extract module name
        import_match = re.search(r"No module named ['\"]?(\w+)['\"]?", error.error_message)
        if import_match:
            module_name = import_match.group(1)
            
            # Common module mappings
            module_mappings = {
                'PIL': 'Pillow',
                'sklearn': 'scikit-learn',
                'yaml': 'pyyaml',
                'cv2': 'opencv-python',
                'bs4': 'beautifulsoup4',
                'dotenv': 'python-dotenv',
                'pytest': 'pytest',
                'requests': 'requests',
            }
            
            pip_name = module_mappings.get(module_name, module_name)
            
            suggestions.append(FixSuggestion(
                title=f"Install missing module: {module_name}",
                description=f"The module '{module_name}' is not installed.",
                code_changes=[{
                    'type': 'shell',
                    'command': f'pip install {pip_name}'
                }],
                confidence=ConfidenceLevel.HIGH,
                auto_fixable=True,
                requires_import=True
            ))
            
            # Suggest adding to requirements
            suggestions.append(FixSuggestion(
                title=f"Add {module_name} to requirements",
                description=f"Add the module to requirements.txt for future installations.",
                code_changes=[{
                    'type': 'file',
                    'file': 'requirements.txt',
                    'action': 'append',
                    'content': f'{pip_name}\n'
                }],
                confidence=ConfidenceLevel.HIGH,
                auto_fixable=True
            ))
        
        return suggestions
    
    def _suggest_name_fixes(self, error: ErrorInfo) -> List[FixSuggestion]:
        """Suggest fixes for name errors."""
        suggestions = []
        
        name_match = re.search(r"name ['\"]?(\w+)['\"]? is not defined", error.error_message)
        if name_match and error.file_path and error.line_number:
            var_name = name_match.group(1)
            
            suggestions.append(FixSuggestion(
                title=f"Define variable '{var_name}'",
                description=f"The variable '{var_name}' is used before being defined.",
                confidence=ConfidenceLevel.HIGH
            ))
        
        return suggestions
    
    def _suggest_attribute_fixes(self, error: ErrorInfo) -> List[FixSuggestion]:
        """Suggest fixes for attribute errors."""
        suggestions = []
        
        if 'NoneType' in error.error_message:
            suggestions.append(FixSuggestion(
                title="Add None check",
                description="The object is None when trying to access an attribute.",
                code_changes=[{
                    'type': 'code',
                    'pattern': 'obj.attr',
                    'replacement': 'if obj is not None:\n    obj.attr'
                }],
                confidence=ConfidenceLevel.HIGH
            ))
        
        return suggestions
    
    def _suggest_type_fixes(self, error: ErrorInfo) -> List[FixSuggestion]:
        """Suggest fixes for type errors."""
        suggestions = []
        
        suggestions.append(FixSuggestion(
            title="Add type conversion",
            description="Convert the value to the expected type.",
            confidence=ConfidenceLevel.MEDIUM
        ))
        
        return suggestions
    
    def _generate_llm_suggestions(self, error: ErrorInfo, 
                                   root_causes: List[RootCause]) -> List[FixSuggestion]:
        """Generate suggestions using LLM."""
        suggestions = []
        
        if not self.llm:
            return suggestions
        
        prompt = f"""
        Analyze this Python error and suggest fixes:
        
        Error Type: {error.error_type}
        Error Message: {error.error_message}
        Category: {error.category.value}
        File: {error.file_path}
        Line: {error.line_number}
        
        Root Causes:
        {chr(10).join(f'- {c.description}' for c in root_causes)}
        
        Context Code:
        {chr(10).join(error.context_code) if error.context_code else 'No context available'}
        
        Provide 1-3 specific fix suggestions in JSON format:
        [
            {{
                "title": "Fix title",
                "description": "Detailed description",
                "code_fix": "Specific code to fix the issue",
                "confidence": "high/medium/low"
            }}
        ]
        
        Output only valid JSON.
        """
        
        try:
            response = self.llm.complete_json(prompt)
            
            for item in response:
                suggestions.append(FixSuggestion(
                    title=item.get('title', 'AI Suggested Fix'),
                    description=item.get('description', ''),
                    code_changes=[{'type': 'code', 'content': item.get('code_fix', '')}],
                    confidence=ConfidenceLevel(item.get('confidence', 'medium').lower())
                ))
                
        except Exception as e:
            logger.debug(f"LLM suggestion generation failed: {e}")
        
        return suggestions


# ============================================================
# MAIN ERROR ANALYZER
# ============================================================

class ErrorAnalyzer:
    """
    Analyzes errors, exceptions, and stack traces for debugging.
    
    Features:
    - Parse exceptions and tracebacks
    - Categorize errors by type
    - Identify root causes
    - Generate fix suggestions
    - Find similar historical errors
    - Estimate resolution time
    - LLM-powered analysis
    - Context code extraction
    """
    
    def __init__(self, config: ErrorAnalyzerConfig):
        self.config = config
        self.parser = ErrorParser(config)
        self.root_cause_analyzer = RootCauseAnalyzer(config)
        self.fix_generator = FixSuggestionGenerator(config)
        self.state = StateManager(config.project_root / ".ai_state" / "error_analyzer.json")
        
        # Error history
        self._error_history: List[ErrorInfo] = self._load_error_history()
        
        logger.info("ErrorAnalyzer initialized")
    
    def analyze(self, error: Union[Exception, str, ErrorInfo]) -> ErrorAnalysisReport:
        """
        Analyze an error and generate a comprehensive report.
        
        Args:
            error: Exception object, traceback string, or ErrorInfo
            
        Returns:
            ErrorAnalysisReport with analysis results
        """
        logger.info(f"Analyzing error...")
        
        # Parse error
        if isinstance(error, Exception):
            error_info = self.parser.parse_exception(error)
        elif isinstance(error, str):
            error_info = self.parser.parse_traceback(error)
        else:
            error_info = error
        
        # Store in history
        self._error_history.append(error_info)
        self._save_error_history()
        
        # Analyze root causes
        root_causes = self.root_cause_analyzer.analyze(error_info)
        
        # Generate fix suggestions
        fix_suggestions = self.fix_generator.generate(error_info, root_causes)
        
        # Find similar errors
        similar_errors = []
        if self.config.find_similar_errors:
            similar_errors = self._find_similar_errors(error_info)
        
        # Build report
        report = ErrorAnalysisReport(
            error=error_info,
            root_causes=root_causes,
            fix_suggestions=fix_suggestions,
            similar_errors=similar_errors,
            impacted_code=self._find_impacted_code(error_info),
            is_resolvable=len(fix_suggestions) > 0,
            resolution_time_estimate=self._estimate_resolution_time(error_info, root_causes),
            summary=self._generate_summary(error_info, root_causes, fix_suggestions)
        )
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Error analysis complete: {len(root_causes)} causes, {len(fix_suggestions)} fixes")
        
        return report
    
    def analyze_current_exception(self) -> ErrorAnalysisReport:
        """Analyze the current exception from sys.exc_info()."""
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        if exc_value is None:
            raise ValueError("No current exception")
        
        return self.analyze(exc_value)
    
    def _load_error_history(self) -> List[ErrorInfo]:
        """Load error history from state."""
        history = self.state.get('error_history', [])
        return []  # Simplified - would reconstruct ErrorInfo objects
    
    def _save_error_history(self):
        """Save error history to state."""
        # Keep last 100 errors
        if len(self._error_history) > 100:
            self._error_history = self._error_history[-100:]
        
        history_data = [
            {
                'timestamp': datetime.now().isoformat(),
                'error_type': e.error_type,
                'error_message': e.error_message[:200],
                'category': e.category.value,
                'severity': e.severity.value,
                'file': e.file_path,
                'line': e.line_number
            }
            for e in self._error_history[-50:]
        ]
        
        self.state.set('error_history', history_data)
        self.state.save()
    
    def _find_similar_errors(self, error: ErrorInfo) -> List[Dict[str, Any]]:
        """Find similar errors in history."""
        similar = []
        
        for hist_error in reversed(self._error_history[:-1]):  # Exclude current
            if hist_error.error_type == error.error_type:
                similarity = self._calculate_similarity(error, hist_error)
                if similarity > 0.5:
                    similar.append({
                        'error': hist_error.error_message[:100],
                        'similarity': similarity,
                        'occurred_at': hist_error.metadata.get('timestamp', 'unknown')
                    })
        
        return sorted(similar, key=lambda x: x['similarity'], reverse=True)[:5]
    
    def _calculate_similarity(self, e1: ErrorInfo, e2: ErrorInfo) -> float:
        """Calculate similarity between two errors."""
        import difflib
        
        # Compare error messages
        msg_sim = difflib.SequenceMatcher(None, e1.error_message, e2.error_message).ratio()
        
        # Compare categories
        cat_sim = 1.0 if e1.category == e2.category else 0.0
        
        # Compare file paths
        file_sim = 0.0
        if e1.file_path and e2.file_path:
            file_sim = difflib.SequenceMatcher(None, e1.file_path, e2.file_path).ratio()
        
        return (msg_sim * 0.5) + (cat_sim * 0.3) + (file_sim * 0.2)
    
    def _find_impacted_code(self, error: ErrorInfo) -> List[str]:
        """Find code impacted by the error."""
        impacted = []
        
        if error.file_path:
            impacted.append(error.file_path)
        
        for frame in error.traceback:
            if frame.is_project_code and frame.file_path not in impacted:
                impacted.append(frame.file_path)
        
        return impacted
    
    def _estimate_resolution_time(self, error: ErrorInfo, 
                                   root_causes: List[RootCause]) -> str:
        """Estimate time to resolve the error."""
        if not root_causes:
            return "unknown"
        
        # Simple estimation based on severity and cause type
        if error.severity == ErrorSeverity.CRITICAL:
            return "1-4 hours"
        elif error.severity == ErrorSeverity.HIGH:
            return "30-60 minutes"
        elif error.severity == ErrorSeverity.MEDIUM:
            return "15-30 minutes"
        else:
            return "5-15 minutes"
    
    def _generate_summary(self, error: ErrorInfo, root_causes: List[RootCause],
                          fix_suggestions: List[FixSuggestion]) -> str:
        """Generate analysis summary."""
        parts = []
        
        parts.append(f"{error.error_type}: {error.error_message[:100]}")
        
        if root_causes:
            primary_cause = root_causes[0]
            parts.append(f"Root cause: {primary_cause.description}")
        
        if fix_suggestions:
            parts.append(f"{len(fix_suggestions)} fix suggestion(s) available")
        
        return " | ".join(parts)
    
    def _save_report(self, report: ErrorAnalysisReport):
        """Save analysis report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.analyzed_at.isoformat(),
            'error_type': report.error.error_type,
            'category': report.error.category.value,
            'severity': report.error.severity.value,
            'root_causes': len(report.root_causes),
            'fix_suggestions': len(report.fix_suggestions),
            'is_resolvable': report.is_resolvable,
            'resolution_estimate': report.resolution_time_estimate
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: ErrorAnalysisReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export error analysis report."""
        
        if format == 'json':
            import json
            data = {
                'analyzed_at': report.analyzed_at.isoformat(),
                'error': {
                    'type': report.error.error_type,
                    'message': report.error.error_message,
                    'category': report.error.category.value,
                    'severity': report.error.severity.value,
                    'file': report.error.file_path,
                    'line': report.error.line_number
                },
                'root_causes': [
                    {
                        'type': c.cause_type.value,
                        'description': c.description,
                        'confidence': c.confidence.value,
                        'fix_suggestion': c.fix_suggestion
                    }
                    for c in report.root_causes
                ],
                'fix_suggestions': [
                    {
                        'title': s.title,
                        'description': s.description,
                        'confidence': s.confidence.value,
                        'auto_fixable': s.auto_fixable
                    }
                    for s in report.fix_suggestions
                ],
                'traceback': [
                    {
                        'file': f.file_path,
                        'line': f.line_number,
                        'function': f.function_name,
                        'code': f.code_line
                    }
                    for f in report.error.traceback
                ],
                'context_code': report.error.context_code,
                'summary': report.summary,
                'is_resolvable': report.is_resolvable,
                'resolution_estimate': report.resolution_time_estimate
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Error Analysis Report",
                "",
                f"**Analyzed:** {report.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Resolvable:** {'✅ Yes' if report.is_resolvable else '❌ No'}",
                f"**Est. Resolution:** {report.resolution_time_estimate}",
                "",
                "## Error Details",
                "",
                f"**Type:** `{report.error.error_type}`",
                f"**Category:** {report.error.category.value}",
                f"**Severity:** {report.error.severity.value}",
                f"**Message:** {report.error.error_message}",
            ]
            
            if report.error.file_path:
                lines.append(f"**Location:** `{report.error.file_path}:{report.error.line_number}`")
            
            lines.append("")
            
            if report.error.context_code:
                lines.extend([
                    "## Context",
                    "",
                    "```python",
                    *report.error.context_code,
                    "```",
                    ""
                ])
            
            if report.error.traceback:
                lines.extend([
                    "## Traceback",
                    "",
                    "```",
                ])
                for frame in report.error.traceback:
                    lines.append(f'  File "{frame.file_path}", line {frame.line_number}, in {frame.function_name}')
                    if frame.code_line:
                        lines.append(f"    {frame.code_line}")
                lines.append(f"{report.error.error_type}: {report.error.error_message}")
                lines.append("```")
                lines.append("")
            
            if report.root_causes:
                lines.extend([
                    "## Root Causes",
                    "",
                ])
                for i, cause in enumerate(report.root_causes, 1):
                    lines.append(f"### {i}. {cause.cause_type.value}")
                    lines.append(f"**Confidence:** {cause.confidence.value}")
                    lines.append(f"**Description:** {cause.description}")
                    if cause.fix_suggestion:
                        lines.append(f"**Suggestion:** {cause.fix_suggestion}")
                    if cause.code_fix:
                        lines.append(f"**Code Fix:** `{cause.code_fix}`")
                    lines.append("")
            
            if report.fix_suggestions:
                lines.extend([
                    "## Fix Suggestions",
                    "",
                ])
                for i, fix in enumerate(report.fix_suggestions, 1):
                    auto_badge = " 🤖 Auto-fixable" if fix.auto_fixable else ""
                    lines.append(f"### {i}. {fix.title}{auto_badge}")
                    lines.append(f"**Confidence:** {fix.confidence.value}")
                    lines.append(f"**Effort:** {fix.estimated_effort}")
                    lines.append(f"**Description:** {fix.description}")
                    if fix.code_changes:
                        lines.append("**Changes:**")
                        for change in fix.code_changes:
                            if change.get('type') == 'code':
                                lines.append(f"```python\n{change.get('content', '')}\n```")
                    lines.append("")
            
            if report.similar_errors:
                lines.extend([
                    "## Similar Historical Errors",
                    "",
                ])
                for similar in report.similar_errors:
                    lines.append(f"- {similar['error']} (similarity: {similar['similarity']:.0%})")
                lines.append("")
            
            content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def close(self):
        """Clean up resources."""
        self._save_error_history()
        self.state.save()
        logger.info("ErrorAnalyzer closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for error analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze Python errors and exceptions")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--traceback", "-t", type=str, help="Traceback string to analyze")
    parser.add_argument("--file", "-f", type=Path, help="File containing traceback")
    parser.add_argument("--output", "-o", type=Path, help="Output report file")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--current", action="store_true", help="Analyze current exception")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    parser.add_argument("--auto-fix", action="store_true", help="Auto-apply safe fixes")
    
    args = parser.parse_args()
    
    config = ErrorAnalyzerConfig(
        project_root=args.project_root,
        use_llm=not args.no_llm,
        auto_apply_safe_fixes=args.auto_fix
    )
    
    analyzer = ErrorAnalyzer(config)
    
    if args.current:
        report = analyzer.analyze_current_exception()
    elif args.traceback:
        report = analyzer.analyze(args.traceback)
    elif args.file:
        traceback_text = args.file.read_text()
        report = analyzer.analyze(traceback_text)
    else:
        # Read from stdin
        import sys
        traceback_text = sys.stdin.read()
        if traceback_text:
            report = analyzer.analyze(traceback_text)
        else:
            print("No traceback provided. Use --traceback, --file, or pipe input.")
            sys.exit(1)
    
    output = analyzer.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    
    analyzer.close()


if __name__ == "__main__":
    main()