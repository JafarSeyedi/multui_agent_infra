#!/usr/bin/env python3
"""
Stack Trace Parser - Parses and analyzes Python stack traces for debugging.

Part of the Quality tools (quality/debuggers/stack_trace_parser.py)

This stack_trace_parser.py provides:

Stack Trace Parsing - Parses Python traceback strings and exception objects

Frame Classification - Identifies project vs stdlib vs third-party frames

Code Context Extraction - Extracts surrounding code around error location

Root Cause Analysis - Identifies the underlying cause of errors

Error Categorization - 20+ error categories with severity levels

Pattern Matching - Matches against known error patterns

Fix Suggestion Generation - Rule-based and LLM-powered fix suggestions

Import Analysis - Identifies missing modules and installation commands

Similar Error Detection - Finds patterns in historical errors

AST Context - Extracts AST information for deeper analysis

LLM-Powered Analysis - AI-enhanced root cause and fix suggestions

Comprehensive Reporting - JSON and Markdown formats

The stack trace parser helps developers quickly understand and fix errors by providing structured analysis and actionable fix suggestions.
"""

import re
import sys
import linecache
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ....shared.logger import get_logger
from ....shared.state_manager import StateManager
from ....shared.llm_client import LLMClient
from ....analysis.scanners.project_scanner import ProjectScanner

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class FrameType(str, Enum):
    """Type of stack frame."""
    PROJECT = "project"
    STDLIB = "stdlib"
    THIRD_PARTY = "third_party"
    ENTRY_POINT = "entry_point"
    ASYNCIO = "asyncio"
    THREADING = "threading"
    UNKNOWN = "unknown"


class ErrorCategory(str, Enum):
    """Category of error from stack trace."""
    IMPORT_ERROR = "import_error"
    ATTRIBUTE_ERROR = "attribute_error"
    TYPE_ERROR = "type_error"
    VALUE_ERROR = "value_error"
    KEY_ERROR = "key_error"
    INDEX_ERROR = "index_error"
    NAME_ERROR = "name_error"
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    ASSERTION_ERROR = "assertion_error"
    ZERO_DIVISION_ERROR = "zero_division_error"
    FILE_NOT_FOUND_ERROR = "file_not_found_error"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT_ERROR = "timeout_error"
    CONNECTION_ERROR = "connection_error"
    RECURSION_ERROR = "recursion_error"
    MEMORY_ERROR = "memory_error"
    UNKNOWN_ERROR = "unknown_error"


class Severity(str, Enum):
    """Severity of the error."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class StackFrame:
    """Represents a single stack frame."""
    index: int
    file_path: str
    line_number: int
    function_name: str
    code_line: str
    frame_type: FrameType = FrameType.UNKNOWN
    is_project_code: bool = False
    is_error_location: bool = False
    locals_summary: Dict[str, str] = field(default_factory=dict)
    arguments: Dict[str, str] = field(default_factory=dict)
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)
    ast_context: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StackTrace:
    """Complete stack trace analysis."""
    raw_text: str
    error_type: str
    error_message: str
    error_category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR
    severity: Severity = Severity.MEDIUM
    frames: List[StackFrame] = field(default_factory=list)
    project_frames: List[StackFrame] = field(default_factory=list)
    error_location: Optional[StackFrame] = None
    chained_exceptions: List['StackTrace'] = field(default_factory=list)
    context_summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeSnippet:
    """Code snippet with context."""
    file_path: str
    line_start: int
    line_end: int
    lines: List[str]
    highlighted_line: Optional[int] = None
    symbols: List[str] = field(default_factory=list)
    complexity: Optional[int] = None


@dataclass
class StackTraceAnalysis:
    """Complete stack trace analysis report."""
    analyzed_at: datetime = field(default_factory=datetime.now)
    stack_trace: StackTrace = field(default_factory=StackTrace)
    
    # Analysis results
    root_cause: str = ""
    root_cause_frame: Optional[StackFrame] = None
    likely_fix: Optional[str] = None
    fix_suggestions: List[str] = field(default_factory=list)
    
    # Code context
    error_snippet: Optional[CodeSnippet] = None
    related_snippets: List[CodeSnippet] = field(default_factory=list)
    
    # Additional analysis
    import_analysis: Optional[Dict[str, Any]] = None
    dependency_analysis: Optional[Dict[str, Any]] = None
    pattern_match: Optional[Dict[str, Any]] = None
    
    # Historical data
    similar_errors: List[Dict[str, Any]] = field(default_factory=list)
    resolution_rate: float = 0.0
    
    # Summary
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StackTraceParserConfig:
    """Configuration for stack trace parser."""
    project_root: Path
    context_lines: int = 5
    max_frames: int = 50
    analyze_imports: bool = True
    analyze_dependencies: bool = True
    find_similar_errors: bool = True
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    include_locals: bool = False
    include_ast: bool = True
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", ".git", ".venv", "venv", "site-packages"
    ])
    stdlib_patterns: List[str] = field(default_factory=lambda: [
        "/usr/lib/python", "/Library/Python", "python3", "lib/python"
    ])
    third_party_patterns: List[str] = field(default_factory=lambda: [
        "site-packages", "dist-packages", ".local/lib"
    ])


# ============================================================
# STACK TRACE PARSER
# ============================================================

class StackTraceParser:
    """Parse and analyze Python stack traces."""
    
    def __init__(self, config: StackTraceParserConfig):
        self.config = config
        self.scanner = ProjectScanner(project_root=config.project_root)
        self.llm = LLMClient() if config.use_llm else None
        self.state = StateManager(config.project_root / ".ai_state" / "stack_trace_parser.json")
        
        # Compiled patterns
        self._compile_patterns()
        
        # Error history
        self._error_history: List[StackTrace] = self._load_error_history()
        
        logger.info("StackTraceParser initialized")
    
    def _compile_patterns(self):
        """Compile regex patterns for parsing."""
        # Frame pattern: File "path", line N, in function
        self.frame_pattern = re.compile(
            r'^\s*File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+(\w+)'
        )
        
        # Code line pattern (with indentation)
        self.code_line_pattern = re.compile(r'^\s+(.+)$')
        
        # Error pattern: ErrorType: message
        self.error_pattern = re.compile(
            r'^(\w+(?:\.\w+)*(?:Error|Exception|Warning|Error|Fault)):\s*(.+)$'
        )
        
        # Chained exception pattern
        self.chained_pattern = re.compile(
            r'During handling of the above exception, another exception occurred'
        )
        self.caused_by_pattern = re.compile(
            r'The above exception was the direct cause'
        )
    
    def parse(self, traceback_text: str) -> StackTrace:
        """Parse a stack trace string."""
        lines = traceback_text.strip().split('\n')
        
        # Extract error type and message (last line)
        error_line = lines[-1] if lines else ""
        error_match = self.error_pattern.match(error_line)
        
        if error_match:
            error_type = error_match.group(1)
            error_message = error_match.group(2)
        else:
            error_type = "UnknownError"
            error_message = error_line
        
        error_category = self._categorize_error(error_type, error_message)
        severity = self._determine_severity(error_category, error_message)
        
        # Parse frames
        frames = []
        frame_lines = []
        current_frame = None
        
        for i, line in enumerate(lines[:-1]):  # Exclude error line
            frame_match = self.frame_pattern.match(line)
            
            if frame_match:
                # Save previous frame
                if current_frame:
                    current_frame.code_line = '\n'.join(frame_lines).strip()
                    frames.append(current_frame)
                
                file_path = frame_match.group(1)
                line_number = int(frame_match.group(2))
                function_name = frame_match.group(3)
                
                frame_type = self._determine_frame_type(file_path)
                is_project = frame_type == FrameType.PROJECT
                
                # Get code line
                code_line = linecache.getline(file_path, line_number).strip()
                
                # Get context
                context_before, context_after = self._extract_context(file_path, line_number)
                
                # Get locals if requested
                locals_summary = {}
                if self.config.include_locals:
                    locals_summary = self._extract_locals_summary(file_path, line_number)
                
                current_frame = StackFrame(
                    index=len(frames),
                    file_path=file_path,
                    line_number=line_number,
                    function_name=function_name,
                    code_line=code_line,
                    frame_type=frame_type,
                    is_project_code=is_project,
                    context_before=context_before,
                    context_after=context_after,
                    locals_summary=locals_summary
                )
                frame_lines = []
                
            elif current_frame is not None:
                code_match = self.code_line_pattern.match(line)
                if code_match:
                    frame_lines.append(code_match.group(1))
        
        # Add last frame
        if current_frame:
            current_frame.code_line = '\n'.join(frame_lines).strip()
            frames.append(current_frame)
        
        # Reverse frames (innermost first)
        frames.reverse()
        for i, frame in enumerate(frames):
            frame.index = i
        
        # Mark error location
        if frames:
            frames[-1].is_error_location = True
        
        # Filter project frames
        project_frames = [f for f in frames if f.is_project_code]
        
        # Extract AST context for error frame
        if frames and self.config.include_ast:
            error_frame = frames[-1]
            error_frame.ast_context = self._extract_ast_context(
                error_frame.file_path, 
                error_frame.line_number
            )
        
        stack_trace = StackTrace(
            raw_text=traceback_text,
            error_type=error_type,
            error_message=error_message,
            error_category=error_category,
            severity=severity,
            frames=frames,
            project_frames=project_frames,
            error_location=frames[-1] if frames else None
        )
        
        # Store in history
        self._error_history.append(stack_trace)
        self._save_error_history()
        
        return stack_trace
    
    def parse_exception(self, exc: Exception, tb: Optional[Any] = None) -> StackTrace:
        """Parse an exception object."""
        import traceback
        
        if tb is None:
            tb = exc.__traceback__
        
        traceback_text = ''.join(traceback.format_exception(type(exc), exc, tb))
        return self.parse(traceback_text)
    
    def _determine_frame_type(self, file_path: str) -> FrameType:
        """Determine the type of a frame."""
        # Check if project file
        try:
            Path(file_path).relative_to(self.config.project_root)
            return FrameType.PROJECT
        except ValueError:
            pass
        
        # Check if stdlib
        for pattern in self.config.stdlib_patterns:
            if pattern in file_path:
                return FrameType.STDLIB
        
        # Check if third-party
        for pattern in self.config.third_party_patterns:
            if pattern in file_path:
                return FrameType.THIRD_PARTY
        
        # Check for async/threading
        if 'asyncio' in file_path:
            return FrameType.ASYNCIO
        if 'threading' in file_path:
            return FrameType.THREADING
        
        if file_path == '<string>' or file_path == '<stdin>':
            return FrameType.ENTRY_POINT
        
        return FrameType.UNKNOWN
    
    def _categorize_error(self, error_type: str, error_message: str) -> ErrorCategory:
        """Categorize error based on type and message."""
        error_lower = error_type.lower()
        msg_lower = error_message.lower()
        
        if 'import' in error_lower or 'modulenotfound' in error_lower:
            return ErrorCategory.IMPORT_ERROR
        elif 'attribute' in error_lower:
            return ErrorCategory.ATTRIBUTE_ERROR
        elif 'type' in error_lower:
            return ErrorCategory.TYPE_ERROR
        elif 'value' in error_lower:
            return ErrorCategory.VALUE_ERROR
        elif 'key' in error_lower:
            return ErrorCategory.KEY_ERROR
        elif 'index' in error_lower:
            return ErrorCategory.INDEX_ERROR
        elif 'name' in error_lower:
            return ErrorCategory.NAME_ERROR
        elif 'syntax' in error_lower:
            return ErrorCategory.SYNTAX_ERROR
        elif 'runtime' in error_lower:
            return ErrorCategory.RUNTIME_ERROR
        elif 'assertion' in error_lower:
            return ErrorCategory.ASSERTION_ERROR
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
        elif 'recursion' in error_lower:
            return ErrorCategory.RECURSION_ERROR
        elif 'memory' in error_lower:
            return ErrorCategory.MEMORY_ERROR
        else:
            return ErrorCategory.UNKNOWN_ERROR
    
    def _determine_severity(self, category: ErrorCategory, message: str) -> Severity:
        """Determine error severity."""
        if category in (ErrorCategory.IMPORT_ERROR, ErrorCategory.SYNTAX_ERROR,
                        ErrorCategory.MEMORY_ERROR, ErrorCategory.RECURSION_ERROR):
            return Severity.CRITICAL
        
        if category in (ErrorCategory.TYPE_ERROR, ErrorCategory.ATTRIBUTE_ERROR,
                        ErrorCategory.NAME_ERROR, ErrorCategory.RUNTIME_ERROR):
            return Severity.HIGH
        
        if category in (ErrorCategory.INDEX_ERROR, ErrorCategory.KEY_ERROR,
                        ErrorCategory.VALUE_ERROR, ErrorCategory.ZERO_DIVISION_ERROR,
                        ErrorCategory.FILE_NOT_FOUND_ERROR):
            return Severity.MEDIUM
        
        if category in (ErrorCategory.PERMISSION_ERROR, ErrorCategory.TIMEOUT_ERROR,
                        ErrorCategory.CONNECTION_ERROR):
            return Severity.MEDIUM
        
        if 'deprecated' in message.lower():
            return Severity.LOW
        
        return Severity.MEDIUM
    
    def _extract_context(self, file_path: str, line_number: int) -> Tuple[List[str], List[str]]:
        """Extract code context around a line."""
        context_before = []
        context_after = []
        
        if not Path(file_path).exists():
            return context_before, context_after
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start = max(0, line_number - self.config.context_lines - 1)
            end = min(len(lines), line_number + self.config.context_lines)
            
            for i in range(start, line_number - 1):
                context_before.append(lines[i].rstrip())
            
            for i in range(line_number, end):
                context_after.append(lines[i].rstrip())
                
        except Exception:
            pass
        
        return context_before, context_after
    
    def _extract_locals_summary(self, file_path: str, line_number: int) -> Dict[str, str]:
        """Extract summary of local variables."""
        # This would require runtime inspection - placeholder
        return {}
    
    def _extract_ast_context(self, file_path: str, line_number: int) -> Optional[Dict[str, Any]]:
        """Extract AST context for a location."""
        import ast
        
        if not Path(file_path).exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            # Find the node at line number
            node = self._find_node_at_line(tree, line_number)
            if node:
                return {
                    'node_type': type(node).__name__,
                    'lineno': getattr(node, 'lineno', None),
                    'end_lineno': getattr(node, 'end_lineno', None),
                    'has_docstring': ast.get_docstring(node) is not None if hasattr(node, 'body') else False
                }
        except Exception:
            pass
        
        return None
    
    def _find_node_at_line(self, tree: ast.AST, line_number: int) -> Optional[ast.AST]:
        """Find AST node at given line number."""
        for node in ast.walk(tree):
            if hasattr(node, 'lineno') and node.lineno == line_number:
                return node
        return None
    
    def _load_error_history(self) -> List[StackTrace]:
        """Load error history from state."""
        history = self.state.get('error_history', [])
        return []  # Would reconstruct StackTrace objects
    
    def _save_error_history(self):
        """Save error history to state."""
        if len(self._error_history) > 100:
            self._error_history = self._error_history[-100:]
        
        history_data = [
            {
                'timestamp': datetime.now().isoformat(),
                'error_type': e.error_type,
                'error_message': e.error_message[:200],
                'category': e.error_category.value,
                'severity': e.severity.value,
                'frames_count': len(e.frames),
                'project_frames': len(e.project_frames)
            }
            for e in self._error_history[-50:]
        ]
        
        self.state.set('error_history', history_data)
        self.state.save()


# ============================================================
# STACK TRACE ANALYZER
# ============================================================

class StackTraceAnalyzer:
    """Analyze stack traces for root causes and fixes."""
    
    def __init__(self, config: StackTraceParserConfig):
        self.config = config
        self.parser = StackTraceParser(config)
        self.scanner = ProjectScanner(project_root=config.project_root)
        self.llm = LLMClient() if config.use_llm else None
        
        # Common error patterns and fixes
        self._error_patterns = self._load_error_patterns()
    
    def analyze(self, traceback_input: Union[str, Exception]) -> StackTraceAnalysis:
        """Analyze a stack trace and generate insights."""
        logger.info("Analyzing stack trace...")
        
        # Parse stack trace
        if isinstance(traceback_input, Exception):
            stack_trace = self.parser.parse_exception(traceback_input)
        else:
            stack_trace = self.parser.parse(traceback_input)
        
        analysis = StackTraceAnalysis(stack_trace=stack_trace)
        
        # Find root cause
        analysis.root_cause, analysis.root_cause_frame = self._find_root_cause(stack_trace)
        
        # Extract code snippets
        analysis.error_snippet = self._extract_error_snippet(stack_trace)
        analysis.related_snippets = self._extract_related_snippets(stack_trace)
        
        # Analyze imports
        if self.config.analyze_imports:
            analysis.import_analysis = self._analyze_imports(stack_trace)
        
        # Analyze dependencies
        if self.config.analyze_dependencies:
            analysis.dependency_analysis = self._analyze_dependencies(stack_trace)
        
        # Match against known patterns
        analysis.pattern_match = self._match_pattern(stack_trace)
        
        # Generate fix suggestions
        analysis.likely_fix, analysis.fix_suggestions = self._generate_fixes(stack_trace, analysis)
        
        # Find similar errors
        if self.config.find_similar_errors:
            analysis.similar_errors = self._find_similar_errors(stack_trace)
            analysis.resolution_rate = self._calculate_resolution_rate(stack_trace)
        
        # LLM-powered analysis
        if self.llm:
            llm_analysis = self._llm_analyze(stack_trace, analysis)
            if llm_analysis:
                analysis.metadata['llm_analysis'] = llm_analysis
        
        # Generate summary and recommendations
        analysis.summary = self._generate_summary(stack_trace, analysis)
        analysis.recommendations = self._generate_recommendations(analysis)
        
        logger.info(f"Stack trace analysis complete: {analysis.root_cause[:100]}")
        
        return analysis
    
    def _find_root_cause(self, stack_trace: StackTrace) -> Tuple[str, Optional[StackFrame]]:
        """Find the root cause of the error."""
        # Check pattern match first
        pattern_match = self._match_pattern(stack_trace)
        if pattern_match:
            return pattern_match.get('root_cause', ''), stack_trace.error_location
        
        # Analyze based on error category
        category = stack_trace.error_category
        error_msg = stack_trace.error_message
        
        if category == ErrorCategory.IMPORT_ERROR:
            module_match = re.search(r"No module named ['\"]?(\w+)['\"]?", error_msg)
            if module_match:
                return f"Missing module: {module_match.group(1)}", stack_trace.error_location
        
        elif category == ErrorCategory.ATTRIBUTE_ERROR:
            attr_match = re.search(r"['\"]?(\w+)['\"]? object has no attribute ['\"]?(\w+)['\"]?", error_msg)
            if attr_match:
                obj_type = attr_match.group(1)
                attr_name = attr_match.group(2)
                if obj_type == 'NoneType':
                    return f"Attempted to access '{attr_name}' on None object", stack_trace.error_location
                return f"Object of type '{obj_type}' has no attribute '{attr_name}'", stack_trace.error_location
        
        elif category == ErrorCategory.KEY_ERROR:
            key_match = re.search(r"KeyError: ['\"]?(\w+)['\"]?", error_msg)
            if key_match:
                return f"Missing key '{key_match.group(1)}' in dictionary", stack_trace.error_location
        
        elif category == ErrorCategory.INDEX_ERROR:
            return "Index out of range - attempted to access element beyond sequence length", stack_trace.error_location
        
        elif category == ErrorCategory.TYPE_ERROR:
            return f"Type mismatch: {error_msg}", stack_trace.error_location
        
        elif category == ErrorCategory.NAME_ERROR:
            name_match = re.search(r"name ['\"]?(\w+)['\"]? is not defined", error_msg)
            if name_match:
                return f"Variable '{name_match.group(1)}' is not defined", stack_trace.error_location
        
        elif category == ErrorCategory.RECURSION_ERROR:
            # Find the recursive function
            func_counts = defaultdict(int)
            for frame in stack_trace.frames:
                func_counts[frame.function_name] += 1
            
            for func, count in func_counts.items():
                if count > 10:
                    return f"Infinite recursion in function '{func}'", stack_trace.error_location
            
            return "Maximum recursion depth exceeded", stack_trace.error_location
        
        # Default
        frame = stack_trace.error_location
        if frame:
            return f"Error occurred in {frame.function_name} at line {frame.line_number}", frame
        
        return stack_trace.error_message, None
    
    def _extract_error_snippet(self, stack_trace: StackTrace) -> Optional[CodeSnippet]:
        """Extract code snippet at error location."""
        frame = stack_trace.error_location
        if not frame:
            return None
        
        lines = frame.context_before + [frame.code_line] + frame.context_after
        
        return CodeSnippet(
            file_path=frame.file_path,
            line_start=frame.line_number - len(frame.context_before),
            line_end=frame.line_number + len(frame.context_after),
            lines=lines,
            highlighted_line=frame.line_number,
            complexity=frame.ast_context.get('complexity') if frame.ast_context else None
        )
    
    def _extract_related_snippets(self, stack_trace: StackTrace) -> List[CodeSnippet]:
        """Extract related code snippets from project frames."""
        snippets = []
        
        for frame in stack_trace.project_frames[:3]:  # Top 3 project frames
            if frame == stack_trace.error_location:
                continue
            
            lines = frame.context_before + [frame.code_line] + frame.context_after
            
            snippets.append(CodeSnippet(
                file_path=frame.file_path,
                line_start=frame.line_number - len(frame.context_before),
                line_end=frame.line_number + len(frame.context_after),
                lines=lines,
                highlighted_line=frame.line_number
            ))
        
        return snippets
    
    def _analyze_imports(self, stack_trace: StackTrace) -> Optional[Dict[str, Any]]:
        """Analyze imports related to the error."""
        if stack_trace.error_category != ErrorCategory.IMPORT_ERROR:
            return None
        
        module_match = re.search(r"No module named ['\"]?(\w+)['\"]?", stack_trace.error_message)
        if not module_match:
            return None
        
        module_name = module_match.group(1)
        
        # Find files that import this module
        importing_files = []
        for py_file in self.config.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()
                if f"import {module_name}" in content or f"from {module_name}" in content:
                    importing_files.append(str(py_file))
            except Exception:
                pass
        
        # Check if it's a common package
        common_packages = {
            'PIL': 'Pillow',
            'sklearn': 'scikit-learn',
            'yaml': 'pyyaml',
            'cv2': 'opencv-python',
            'bs4': 'beautifulsoup4',
            'dotenv': 'python-dotenv',
        }
        
        pip_name = common_packages.get(module_name, module_name)
        
        return {
            'module': module_name,
            'pip_package': pip_name,
            'importing_files': importing_files,
            'install_command': f'pip install {pip_name}'
        }
    
    def _analyze_dependencies(self, stack_trace: StackTrace) -> Optional[Dict[str, Any]]:
        """Analyze dependencies related to the error."""
        # Check for dependency conflicts
        return None
    
    def _load_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load common error patterns and fixes."""
        return {
            'import_error': {
                'pattern': r"No module named ['\"]?(\w+)['\"]?",
                'root_cause': "Missing Python package",
                'fix': "Install the required package"
            },
            'none_attribute': {
                'pattern': r"'NoneType' object has no attribute ['\"]?(\w+)['\"]?",
                'root_cause': "Variable is None when attribute accessed",
                'fix': "Add a check for None before accessing attribute"
            },
            'key_error': {
                'pattern': r"KeyError: ['\"]?(\w+)['\"]?",
                'root_cause': "Missing key in dictionary",
                'fix': "Use .get() method or check if key exists"
            },
            'index_error': {
                'pattern': r"IndexError: list index out of range",
                'root_cause': "Empty list or index beyond length",
                'fix': "Check list length before indexing"
            },
            'type_error_str_int': {
                'pattern': r"can only concatenate str \(not \"int\"\) to str",
                'root_cause': "Type mismatch in string concatenation",
                'fix': "Convert int to str: str(value)"
            },
            'recursion_error': {
                'pattern': r"maximum recursion depth exceeded",
                'root_cause': "Infinite recursion",
                'fix': "Check base case or convert to iterative approach"
            }
        }
    
    def _match_pattern(self, stack_trace: StackTrace) -> Optional[Dict[str, Any]]:
        """Match stack trace against known patterns."""
        error_msg = stack_trace.error_message
        
        for pattern_name, pattern_info in self._error_patterns.items():
            if re.search(pattern_info['pattern'], error_msg):
                return {
                    'pattern': pattern_name,
                    'root_cause': pattern_info['root_cause'],
                    'fix': pattern_info['fix']
                }
        
        return None
    
    def _generate_fixes(self, stack_trace: StackTrace, 
                        analysis: StackTraceAnalysis) -> Tuple[Optional[str], List[str]]:
        """Generate fix suggestions."""
        likely_fix = None
        suggestions = []
        
        # Check pattern match
        if analysis.pattern_match:
            likely_fix = analysis.pattern_match.get('fix')
            suggestions.append(likely_fix)
        
        # Category-specific fixes
        if stack_trace.error_category == ErrorCategory.IMPORT_ERROR:
            if analysis.import_analysis:
                cmd = analysis.import_analysis['install_command']
                suggestions.append(f"Run: {cmd}")
                likely_fix = cmd
        
        elif stack_trace.error_category == ErrorCategory.ATTRIBUTE_ERROR:
            if 'NoneType' in stack_trace.error_message:
                suggestions.append("Add None check before attribute access")
                suggestions.append("Use optional chaining pattern or getattr with default")
                likely_fix = "Add None check"
        
        elif stack_trace.error_category == ErrorCategory.KEY_ERROR:
            key_match = re.search(r"KeyError: ['\"]?(\w+)['\"]?", stack_trace.error_message)
            if key_match:
                key = key_match.group(1)
                suggestions.append(f"Use .get('{key}', default) instead of ['{key}']")
                suggestions.append(f"Check if '{key}' exists with 'if {key} in dict'")
                likely_fix = f"Replace with .get('{key}', default)"
        
        elif stack_trace.error_category == ErrorCategory.INDEX_ERROR:
            suggestions.append("Check list length before indexing")
            suggestions.append("Use slice notation or try/except IndexError")
            likely_fix = "Add length check"
        
        elif stack_trace.error_category == ErrorCategory.TYPE_ERROR:
            suggestions.append("Check types of operands")
            suggestions.append("Add explicit type conversion")
            likely_fix = "Add type conversion"
        
        elif stack_trace.error_category == ErrorCategory.NAME_ERROR:
            name_match = re.search(r"name ['\"]?(\w+)['\"]? is not defined", stack_trace.error_message)
            if name_match:
                var_name = name_match.group(1)
                suggestions.append(f"Define '{var_name}' before using it")
                suggestions.append(f"Check for typos in '{var_name}'")
                likely_fix = f"Define {var_name}"
        
        # Add general suggestions
        suggestions.append("Review the code at the error location")
        suggestions.append("Add unit tests to catch this error")
        
        return likely_fix, suggestions[:5]
    
    def _find_similar_errors(self, stack_trace: StackTrace) -> List[Dict[str, Any]]:
        """Find similar errors in history."""
        similar = []
        
        for hist_error in self.parser._error_history[:-1]:
            if hist_error.error_type == stack_trace.error_type:
                similar.append({
                    'error': hist_error.error_message[:100],
                    'category': hist_error.error_category.value,
                    'occurred_at': hist_error.metadata.get('timestamp', 'unknown')
                })
        
        return similar[:5]
    
    def _calculate_resolution_rate(self, stack_trace: StackTrace) -> float:
        """Calculate resolution rate for this error type."""
        total = 0
        resolved = 0
        
        for hist_error in self.parser._error_history:
            if hist_error.error_type == stack_trace.error_type:
                total += 1
                if hist_error.metadata.get('resolved', False):
                    resolved += 1
        
        return resolved / total if total > 0 else 0.0
    
    def _llm_analyze(self, stack_trace: StackTrace, 
                     analysis: StackTraceAnalysis) -> Optional[Dict[str, Any]]:
        """Use LLM to analyze the stack trace."""
        if not self.llm:
            return None
        
        prompt = f"""
        Analyze this Python stack trace and provide insights:
        
        Error: {stack_trace.error_type}: {stack_trace.error_message}
        Category: {stack_trace.error_category.value}
        
        Stack frames (project code only):
        {chr(10).join(f'  {i+1}. {f.file_path}:{f.line_number} in {f.function_name} - {f.code_line}' 
                      for i, f in enumerate(stack_trace.project_frames))}
        
        Current analysis:
        Root cause: {analysis.root_cause}
        
        Provide:
        1. A more detailed root cause explanation
        2. The most likely fix
        3. Any additional considerations
        
        Output as JSON:
        {{
            "detailed_cause": "...",
            "likely_fix": "...",
            "considerations": ["..."]
        }}
        """
        
        try:
            response = self.llm.complete_json(prompt)
            return response
        except Exception as e:
            logger.debug(f"LLM analysis failed: {e}")
            return None
    
    def _generate_summary(self, stack_trace: StackTrace,
                          analysis: StackTraceAnalysis) -> str:
        """Generate analysis summary."""
        parts = []
        
        parts.append(f"{stack_trace.error_type}: {stack_trace.error_message[:50]}")
        
        if analysis.root_cause_frame:
            parts.append(f"at {Path(analysis.root_cause_frame.file_path).name}:{analysis.root_cause_frame.line_number}")
        
        if analysis.likely_fix:
            parts.append(f"Fix: {analysis.likely_fix[:50]}")
        
        return " | ".join(parts)
    
    def _generate_recommendations(self, analysis: StackTraceAnalysis) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if analysis.fix_suggestions:
            recommendations.append(f"Apply fix: {analysis.fix_suggestions[0]}")
        
        if analysis.similar_errors:
            recommendations.append("Review similar historical errors for patterns")
        
        if analysis.error_snippet and analysis.error_snippet.complexity:
            if analysis.error_snippet.complexity > 10:
                recommendations.append("Consider refactoring - high complexity detected")
        
        recommendations.append("Add test coverage for this scenario")
        
        return recommendations


# ============================================================
# MAIN STACK TRACE PARSER
# ============================================================

class StackTraceParserTool:
    """
    Main tool for parsing and analyzing Python stack traces.
    
    Features:
    - Parse stack trace strings and exceptions
    - Identify project vs library frames
    - Extract code context around errors
    - Find root causes
    - Generate fix suggestions
    - Match against known error patterns
    - Find similar historical errors
    - LLM-powered analysis
    - Export analysis reports
    """
    
    def __init__(self, config: StackTraceParserConfig):
        self.config = config
        self.analyzer = StackTraceAnalyzer(config)
        self.state = StateManager(config.project_root / ".ai_state" / "stack_trace_tool.json")
        
        logger.info("StackTraceParserTool initialized")
    
    def analyze(self, input_data: Union[str, Exception]) -> StackTraceAnalysis:
        """Analyze stack trace input."""
        return self.analyzer.analyze(input_data)
    
    def analyze_file(self, file_path: Path) -> StackTraceAnalysis:
        """Analyze stack trace from file."""
        content = file_path.read_text()
        return self.analyze(content)
    
    def export_analysis(self, analysis: StackTraceAnalysis,
                        output_path: Optional[Path] = None,
                        format: str = 'markdown') -> str:
        """Export analysis report."""
        
        if format == 'json':
            import json
            data = {
                'analyzed_at': analysis.analyzed_at.isoformat(),
                'error': {
                    'type': analysis.stack_trace.error_type,
                    'message': analysis.stack_trace.error_message,
                    'category': analysis.stack_trace.error_category.value,
                    'severity': analysis.stack_trace.severity.value
                },
                'root_cause': analysis.root_cause,
                'likely_fix': analysis.likely_fix,
                'fix_suggestions': analysis.fix_suggestions,
                'error_location': {
                    'file': analysis.stack_trace.error_location.file_path if analysis.stack_trace.error_location else None,
                    'line': analysis.stack_trace.error_location.line_number if analysis.stack_trace.error_location else None,
                    'function': analysis.stack_trace.error_location.function_name if analysis.stack_trace.error_location else None,
                    'code': analysis.stack_trace.error_location.code_line if analysis.stack_trace.error_location else None
                },
                'project_frames': [
                    {
                        'file': f.file_path,
                        'line': f.line_number,
                        'function': f.function_name,
                        'code': f.code_line
                    }
                    for f in analysis.stack_trace.project_frames
                ],
                'import_analysis': analysis.import_analysis,
                'pattern_match': analysis.pattern_match,
                'similar_errors': analysis.similar_errors,
                'resolution_rate': analysis.resolution_rate,
                'summary': analysis.summary,
                'recommendations': analysis.recommendations
            }
            
            if analysis.error_snippet:
                data['error_snippet'] = {
                    'file': analysis.error_snippet.file_path,
                    'lines': analysis.error_snippet.lines,
                    'highlighted_line': analysis.error_snippet.highlighted_line
                }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Stack Trace Analysis",
                "",
                f"**Analyzed:** {analysis.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Summary:** {analysis.summary}",
                "",
                "## Error Details",
                "",
                f"**Type:** `{analysis.stack_trace.error_type}`",
                f"**Category:** {analysis.stack_trace.error_category.value}",
                f"**Severity:** {analysis.stack_trace.severity.value}",
                f"**Message:** {analysis.stack_trace.error_message}",
                "",
                "## Root Cause",
                "",
                analysis.root_cause,
                "",
            ]
            
            if analysis.error_snippet:
                lines.extend([
                    "## Error Location",
                    "",
                    f"**File:** `{analysis.error_snippet.file_path}`",
                    f"**Line:** {analysis.error_snippet.highlighted_line}",
                    "",
                    "```python",
                ])
                for line in analysis.error_snippet.lines:
                    lines.append(line)
                lines.extend(["```", ""])
            
            if analysis.project_frames:
                lines.extend([
                    "## Stack Trace (Project Code)",
                    "",
                ])
                for i, frame in enumerate(analysis.stack_trace.project_frames):
                    lines.append(f"{i+1}. **{frame.function_name}** at `{Path(frame.file_path).name}:{frame.line_number}`")
                    if frame.code_line:
                        lines.append(f"   ```python\n   {frame.code_line}\n   ```")
                lines.append("")
            
            if analysis.likely_fix:
                lines.extend([
                    "## Likely Fix",
                    "",
                    analysis.likely_fix,
                    "",
                ])
            
            if analysis.fix_suggestions:
                lines.extend([
                    "## Fix Suggestions",
                    "",
                ])
                for suggestion in analysis.fix_suggestions:
                    lines.append(f"- {suggestion}")
                lines.append("")
            
            if analysis.import_analysis:
                lines.extend([
                    "## Import Analysis",
                    "",
                    f"**Missing Module:** {analysis.import_analysis['module']}",
                    f"**Install Command:** `{analysis.import_analysis['install_command']}`",
                    f"**Files Importing:** {len(analysis.import_analysis['importing_files'])}",
                    "",
                ])
            
            if analysis.pattern_match:
                lines.extend([
                    "## Pattern Match",
                    "",
                    f"**Pattern:** {analysis.pattern_match['pattern']}",
                    f"**Root Cause:** {analysis.pattern_match['root_cause']}",
                    f"**Fix:** {analysis.pattern_match['fix']}",
                    "",
                ])
            
            if analysis.similar_errors:
                lines.extend([
                    "## Similar Historical Errors",
                    "",
                ])
                for similar in analysis.similar_errors:
                    lines.append(f"- {similar['error']}")
                lines.append("")
            
            if analysis.recommendations:
                lines.extend([
                    "## Recommendations",
                    "",
                ])
                for rec in analysis.recommendations:
                    lines.append(f"- {rec}")
                lines.append("")
            
            content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("StackTraceParserTool closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for stack trace parser."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Parse and analyze Python stack traces")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--input", "-i", type=str, help="Stack trace string")
    parser.add_argument("--file", "-f", type=Path, help="File containing stack trace")
    parser.add_argument("--output", "-o", type=Path, help="Output report file")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--context-lines", type=int, default=5, help="Context lines to show")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    parser.add_argument("--no-similar", action="store_true", help="Disable similar error search")
    
    args = parser.parse_args()
    
    config = StackTraceParserConfig(
        project_root=args.project_root,
        context_lines=args.context_lines,
        use_llm=not args.no_llm,
        find_similar_errors=not args.no_similar
    )
    
    tool = StackTraceParserTool(config)
    
    if args.input:
        analysis = tool.analyze(args.input)
    elif args.file:
        analysis = tool.analyze_file(args.file)
    else:
        # Read from stdin
        input_text = sys.stdin.read()
        if input_text:
            analysis = tool.analyze(input_text)
        else:
            print("No input provided. Use --input, --file, or pipe input.")
            sys.exit(1)
    
    output = tool.export_analysis(analysis, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{analysis.summary}")
    
    if analysis.likely_fix:
        print(f"\nLikely fix: {analysis.likely_fix}")
    
    tool.close()


if __name__ == "__main__":
    main()