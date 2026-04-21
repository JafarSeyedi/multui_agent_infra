#!/usr/bin/env python3
"""
Import Validator - Validates import statements for correctness, organization, and best practices.

Part of the Quality tools (validators/import_validator.py)


This import_validator.py provides:

1. Import Parsing - Direct, from, relative, star, conditional, dynamic imports
2. Import Order Validation - Enforces standard grouping (future, stdlib, third-party, first-party, local)
3. Unused Import Detection - Identifies imports that are never used
4. Star Import Detection - Flags wildcard imports
5. Relative Import Validation - Checks depth and configuration
6. Conditional Import Detection - Finds imports inside if/try blocks
7. Dynamic Import Detection - Identifies __import__ and importlib.import_module
8. TYPE_CHECKING Support - Recognizes typing-only imports
9. Alias Naming Enforcement - Validates standard aliases (np, pd, plt, etc.)
10. Forbidden Module Checking - Blocks specific modules
11. Circular Dependency Detection - Finds import cycles
12. Import Health Scoring - A-F grade based on import quality

The import validator ensures clean, organized, and maintainable import statements throughout your codebase.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class ImportType(str, Enum):
    """Type of import statement."""
    DIRECT = "direct"           # import module
    FROM = "from"               # from module import name
    RELATIVE = "relative"       # from .module import name
    STAR = "star"               # from module import *
    ALIAS = "alias"             # import module as alias
    CONDITIONAL = "conditional" # import inside if/try
    DYNAMIC = "dynamic"         # __import__ or importlib
    TYPE_CHECKING = "type_checking"


class Severity(str, Enum):
    """Severity of import issue."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ImportGroup(str, Enum):
    """Standard import grouping."""
    FUTURE = "future"
    STDLIB = "stdlib"
    THIRD_PARTY = "third_party"
    FIRST_PARTY = "first_party"
    LOCAL = "local"
    RELATIVE = "relative"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ImportStatement:
    """Represents a single import statement."""
    type: ImportType
    module: str
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    level: int = 0  # For relative imports
    line_number: int = 0
    is_conditional: bool = False
    is_dynamic: bool = False
    is_type_only: bool = False
    is_used: bool = True
    group: ImportGroup = ImportGroup.THIRD_PARTY
    raw_line: str = ""


@dataclass
class ImportIssue:
    """A single import issue."""
    issue_type: str
    severity: Severity
    file_path: str
    line_number: Optional[int] = None
    import_statement: Optional[str] = None
    description: str = ""
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleImports:
    """Import information for a single module."""
    file_path: str
    imports: List[ImportStatement] = field(default_factory=list)
    unused_imports: List[ImportStatement] = field(default_factory=list)
    missing_imports: List[str] = field(default_factory=list)
    circular_dependencies: List[List[str]] = field(default_factory=list)
    issues: List[ImportIssue] = field(default_factory=list)


@dataclass
class ImportReport:
    """Complete import validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    
    # Statistics
    total_files: int = 0
    total_imports: int = 0
    unused_imports: int = 0
    star_imports: int = 0
    relative_imports: int = 0
    conditional_imports: int = 0
    dynamic_imports: int = 0
    
    # Group statistics
    imports_by_group: Dict[str, int] = field(default_factory=dict)
    
    # Module details
    module_imports: Dict[str, ModuleImports] = field(default_factory=dict)
    
    # Issues
    issues: List[ImportIssue] = field(default_factory=list)
    warnings: List[ImportIssue] = field(default_factory=list)
    
    # Circular dependencies
    circular_dependencies: List[List[str]] = field(default_factory=list)
    
    # Validation
    is_valid: bool = True
    overall_score: float = 0.0
    grade: str = "A"
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportValidatorConfig:
    """Configuration for import validator."""
    project_root: Path
    
    # Import organization
    enforce_import_order: bool = True
    import_groups: List[ImportGroup] = field(default_factory=lambda: [
        ImportGroup.FUTURE,
        ImportGroup.STDLIB,
        ImportGroup.THIRD_PARTY,
        ImportGroup.FIRST_PARTY,
        ImportGroup.LOCAL,
        ImportGroup.RELATIVE
    ])
    group_spacing: int = 1  # Blank lines between groups
    
    # Import rules
    forbid_star_imports: bool = True
    forbid_relative_imports: bool = False
    forbid_conditional_imports: bool = False
    forbid_dynamic_imports: bool = True
    forbid_unused_imports: bool = True
    forbid_wildcard_except_type_checking: bool = True
    allow_type_checking_imports: bool = True
    
    # Naming rules
    enforce_alias_naming: bool = False
    alias_patterns: Dict[str, str] = field(default_factory=lambda: {
        "numpy": "np",
        "pandas": "pd",
        "matplotlib.pyplot": "plt",
        "tensorflow": "tf",
        "torch": None  # No alias allowed
    })
    
    # Module rules
    first_party_modules: List[str] = field(default_factory=list)
    allowed_modules: List[str] = field(default_factory=list)
    forbidden_modules: List[str] = field(default_factory=list)
    
    # Ignore patterns
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "test_*.py", "*_test.py"
    ])
    
    # Validation
    fail_on_error: bool = True
    fail_on_warning: bool = False
    max_imports_per_file: int = 50
    max_relative_import_depth: int = 2
    
    # Reporting
    generate_report: bool = True
    output_format: str = "markdown"


# ============================================================
# IMPORT PARSER
# ============================================================

class ImportParser:
    """Parse and analyze import statements."""
    
    def __init__(self, config: ImportValidatorConfig):
        self.config = config
        self.stdlib_modules: Set[str] = self._get_stdlib_modules()
    
    def parse_file(self, file_path: Path) -> ModuleImports:
        """Parse imports from a file."""
        module_imports = ModuleImports(file_path=str(file_path))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            tree = ast.parse(content)
            
            visitor = ImportVisitor(file_path, self.config, self.stdlib_modules, lines)
            visitor.visit(tree)
            
            module_imports.imports = visitor.imports
            module_imports.unused_imports = [i for i in visitor.imports if not i.is_used]
            module_imports.issues = visitor.issues
            
        except SyntaxError as e:
            module_imports.issues.append(ImportIssue(
                issue_type="syntax_error",
                severity=Severity.ERROR,
                file_path=str(file_path),
                line_number=e.lineno,
                description=f"Syntax error: {e}"
            ))
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
        
        return module_imports
    
    def _get_stdlib_modules(self) -> Set[str]:
        """Get set of Python standard library modules."""
        stdlib = {
            'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
            'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
            'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
            'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
            'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
            'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib',
            'dis', 'distutils', 'doctest', 'email', 'encodings', 'enum', 'errno', 'faulthandler',
            'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'fractions', 'ftplib', 'functools',
            'gc', 'getopt', 'getpass', 'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib',
            'heapq', 'hmac', 'html', 'http', 'idlelib', 'imaplib', 'imghdr', 'imp', 'importlib',
            'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword', 'lib2to3', 'linecache',
            'locale', 'logging', 'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes',
            'mmap', 'modulefinder', 'msilib', 'msvcrt', 'multiprocessing', 'netrc', 'nis',
            'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'pathlib',
            'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib',
            'poplib', 'posix', 'pprint', 'profile', 'pstats', 'pty', 'pwd', 'py_compile',
            'pyclbr', 'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib',
            'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select', 'selectors',
            'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib', 'sndhdr',
            'socket', 'socketserver', 'spwd', 'sqlite3', 'ssl', 'stat', 'statistics', 'string',
            'stringprep', 'struct', 'subprocess', 'sunau', 'symtable', 'sys', 'sysconfig',
            'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
            'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize', 'tomllib', 'trace',
            'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing',
            'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave',
            'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml',
            'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib', 'zoneinfo'
        }
        return stdlib
    
    def classify_import(self, module_name: str) -> ImportGroup:
        """Classify an import into a group."""
        if module_name == '__future__':
            return ImportGroup.FUTURE
        
        top_module = module_name.split('.')[0]
        
        if top_module in self.stdlib_modules:
            return ImportGroup.STDLIB
        
        if top_module in self.config.first_party_modules:
            return ImportGroup.FIRST_PARTY
        
        if module_name.startswith('.'):
            return ImportGroup.RELATIVE
        
        return ImportGroup.THIRD_PARTY


class ImportVisitor(ast.NodeVisitor):
    """AST visitor for import validation."""
    
    def __init__(self, file_path: Path, config: ImportValidatorConfig,
                 stdlib_modules: Set[str], source_lines: List[str]):
        self.file_path = str(file_path)
        self.config = config
        self.stdlib_modules = stdlib_modules
        self.source_lines = source_lines
        self.imports: List[ImportStatement] = []
        self.issues: List[ImportIssue] = []
        self.used_names: Set[str] = set()
        self.current_import_group: Optional[ImportGroup] = None
        self.last_import_line: int = 0
        self.in_type_checking: bool = False
        self.in_conditional: bool = False
    
    def visit_Module(self, node: ast.Module):
        """Visit module."""
        # First pass: collect all used names
        self._collect_used_names(node)
        
        # Second pass: visit imports
        self.generic_visit(node)
        
        # Check import order
        if self.config.enforce_import_order:
            self._check_import_order()
    
    def _collect_used_names(self, node: ast.AST):
        """Collect all names used in the module."""
        class NameCollector(ast.NodeVisitor):
            def __init__(self):
                self.names = set()
            
            def visit_Name(self, node):
                if isinstance(node.ctx, (ast.Load, ast.Del)):
                    self.names.add(node.id)
            
            def visit_Attribute(self, node):
                if isinstance(node.value, ast.Name):
                    self.names.add(node.value.id)
        
        collector = NameCollector()
        collector.visit(node)
        self.used_names = collector.names
    
    def visit_Import(self, node: ast.Import):
        """Visit direct import."""
        for alias in node.names:
            module = alias.name
            import_stmt = ImportStatement(
                type=ImportType.DIRECT,
                module=module,
                names=[alias.name],
                alias=alias.asname,
                line_number=node.lineno,
                is_conditional=self.in_conditional,
                is_type_only=self.in_type_checking,
                raw_line=self.source_lines[node.lineno - 1].strip() if node.lineno else ""
            )
            
            # Check if used
            used_name = alias.asname or alias.name.split('.')[0]
            import_stmt.is_used = used_name in self.used_names
            
            # Classify
            import_stmt.group = self._classify_import(module)
            
            self.imports.append(import_stmt)
            self.last_import_line = max(self.last_import_line, node.lineno)
            
            # Validate
            self._validate_import(import_stmt)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from import."""
        module = node.module or ''
        level = node.level
        
        for alias in node.names:
            import_type = ImportType.RELATIVE if level > 0 else ImportType.FROM
            if alias.name == '*':
                import_type = ImportType.STAR
            
            import_stmt = ImportStatement(
                type=import_type,
                module=module,
                names=[alias.name],
                alias=alias.asname,
                level=level,
                line_number=node.lineno,
                is_conditional=self.in_conditional,
                is_type_only=self.in_type_checking,
                raw_line=self.source_lines[node.lineno - 1].strip() if node.lineno else ""
            )
            
            # Check if used
            used_name = alias.asname or alias.name
            import_stmt.is_used = used_name in self.used_names or alias.name == '*'
            
            # Classify
            if level > 0:
                import_stmt.group = ImportGroup.RELATIVE
            else:
                import_stmt.group = self._classify_import(module)
            
            self.imports.append(import_stmt)
            self.last_import_line = max(self.last_import_line, node.lineno)
            
            # Validate
            self._validate_import(import_stmt)
    
    def visit_If(self, node: ast.If):
        """Visit if statement (check for TYPE_CHECKING)."""
        is_type_checking_block = self._is_type_checking(node)
        
        if is_type_checking_block:
            self.in_type_checking = True
            self.generic_visit(node)
            self.in_type_checking = False
        else:
            prev_conditional = self.in_conditional
            self.in_conditional = True
            self.generic_visit(node)
            self.in_conditional = prev_conditional
    
    def visit_Try(self, node: ast.Try):
        """Visit try block."""
        prev_conditional = self.in_conditional
        self.in_conditional = True
        self.generic_visit(node)
        self.in_conditional = prev_conditional
    
    def visit_Call(self, node: ast.Call):
        """Visit function call (check for dynamic imports)."""
        # Check for __import__
        if isinstance(node.func, ast.Name) and node.func.id == '__import__':
            if node.args:
                module = self._get_string_value(node.args[0])
                if module:
                    import_stmt = ImportStatement(
                        type=ImportType.DYNAMIC,
                        module=module,
                        line_number=node.lineno,
                        is_dynamic=True,
                        raw_line=self.source_lines[node.lineno - 1].strip() if node.lineno else ""
                    )
                    import_stmt.group = self._classify_import(module)
                    self.imports.append(import_stmt)
                    self._validate_import(import_stmt)
        
        # Check for importlib.import_module
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'import_module':
                if isinstance(node.func.value, ast.Name) and node.func.value.id == 'importlib':
                    if node.args:
                        module = self._get_string_value(node.args[0])
                        if module:
                            import_stmt = ImportStatement(
                                type=ImportType.DYNAMIC,
                                module=module,
                                line_number=node.lineno,
                                is_dynamic=True,
                                raw_line=self.source_lines[node.lineno - 1].strip() if node.lineno else ""
                            )
                            import_stmt.group = self._classify_import(module)
                            self.imports.append(import_stmt)
                            self._validate_import(import_stmt)
        
        self.generic_visit(node)
    
    def _is_type_checking(self, node: ast.If) -> bool:
        """Check if this is a TYPE_CHECKING block."""
        if isinstance(node.test, ast.Name):
            return node.test.id == 'TYPE_CHECKING'
        if isinstance(node.test, ast.Attribute):
            return node.test.attr == 'TYPE_CHECKING'
        return False
    
    def _get_string_value(self, node: ast.AST) -> Optional[str]:
        """Get string value from AST node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Str):
            return node.s
        return None
    
    def _classify_import(self, module: str) -> ImportGroup:
        """Classify an import into a group."""
        if module == '__future__':
            return ImportGroup.FUTURE
        
        top_module = module.split('.')[0]
        
        if top_module in self.stdlib_modules:
            return ImportGroup.STDLIB
        
        if top_module in self.config.first_party_modules:
            return ImportGroup.FIRST_PARTY
        
        return ImportGroup.THIRD_PARTY
    
    def _validate_import(self, import_stmt: ImportStatement):
        """Validate an import statement."""
        # Check star imports
        if (self.config.forbid_star_imports and 
            import_stmt.type == ImportType.STAR and
            not (self.config.allow_type_checking_imports and import_stmt.is_type_only)):
            self.issues.append(ImportIssue(
                issue_type="star_import",
                severity=Severity.WARNING,
                file_path=self.file_path,
                line_number=import_stmt.line_number,
                import_statement=import_stmt.raw_line,
                description="Wildcard import (from module import *) is discouraged",
                suggestion="Import specific names instead"
            ))
        
        # Check relative imports
        if self.config.forbid_relative_imports and import_stmt.type == ImportType.RELATIVE:
            self.issues.append(ImportIssue(
                issue_type="relative_import",
                severity=Severity.WARNING,
                file_path=self.file_path,
                line_number=import_stmt.line_number,
                import_statement=import_stmt.raw_line,
                description="Relative imports are discouraged",
                suggestion="Use absolute imports instead"
            ))
        
        # Check relative import depth
        if import_stmt.level > self.config.max_relative_import_depth:
            self.issues.append(ImportIssue(
                issue_type="deep_relative_import",
                severity=Severity.WARNING,
                file_path=self.file_path,
                line_number=import_stmt.line_number,
                import_statement=import_stmt.raw_line,
                description=f"Relative import depth {import_stmt.level} exceeds maximum {self.config.max_relative_import_depth}",
                suggestion="Restructure modules or use absolute imports"
            ))
        
        # Check conditional imports
        if (self.config.forbid_conditional_imports and 
            import_stmt.is_conditional and
            not import_stmt.is_type_only):
            self.issues.append(ImportIssue(
                issue_type="conditional_import",
                severity=Severity.WARNING,
                file_path=self.file_path,
                line_number=import_stmt.line_number,
                import_statement=import_stmt.raw_line,
                description="Conditional imports can cause runtime errors",
                suggestion="Move import to top of file or use try/except ImportError"
            ))
        
        # Check dynamic imports
        if self.config.forbid_dynamic_imports and import_stmt.is_dynamic:
            self.issues.append(ImportIssue(
                issue_type="dynamic_import",
                severity=Severity.ERROR,
                file_path=self.file_path,
                line_number=import_stmt.line_number,
                import_statement=import_stmt.raw_line,
                description="Dynamic imports are discouraged",
                suggestion="Use static imports instead"
            ))
        
        # Check forbidden modules
        if import_stmt.module in self.config.forbidden_modules:
            self.issues.append(ImportIssue(
                issue_type="forbidden_module",
                severity=Severity.ERROR,
                file_path=self.file_path,
                line_number=import_stmt.line_number,
                import_statement=import_stmt.raw_line,
                description=f"Module '{import_stmt.module}' is forbidden",
                suggestion=f"Use an allowed alternative"
            ))
        
        # Check alias naming
        if (self.config.enforce_alias_naming and 
            import_stmt.alias and 
            import_stmt.module in self.config.alias_patterns):
            expected_alias = self.config.alias_patterns[import_stmt.module]
            if expected_alias is None:
                self.issues.append(ImportIssue(
                    issue_type="unwanted_alias",
                    severity=Severity.WARNING,
                    file_path=self.file_path,
                    line_number=import_stmt.line_number,
                    import_statement=import_stmt.raw_line,
                    description=f"Module '{import_stmt.module}' should not be aliased",
                    suggestion="Remove the alias"
                ))
            elif import_stmt.alias != expected_alias:
                self.issues.append(ImportIssue(
                    issue_type="incorrect_alias",
                    severity=Severity.WARNING,
                    file_path=self.file_path,
                    line_number=import_stmt.line_number,
                    import_statement=import_stmt.raw_line,
                    description=f"Module '{import_stmt.module}' should be aliased as '{expected_alias}', not '{import_stmt.alias}'",
                    suggestion=f"Use 'import {import_stmt.module} as {expected_alias}'"
                ))
    
    def _check_import_order(self):
        """Check that imports are properly ordered."""
        sorted_imports = sorted(self.imports, key=lambda x: x.line_number)
        last_group_idx = -1
        
        for imp in sorted_imports:
            if imp.is_conditional or imp.is_dynamic:
                continue
            
            group_idx = self.config.import_groups.index(imp.group) if imp.group in self.config.import_groups else 999
            
            if group_idx < last_group_idx:
                self.issues.append(ImportIssue(
                    issue_type="import_order",
                    severity=Severity.WARNING,
                    file_path=self.file_path,
                    line_number=imp.line_number,
                    import_statement=imp.raw_line,
                    description=f"Import from group '{imp.group.value}' appears after imports from higher-priority groups",
                    suggestion="Reorder imports according to standard grouping"
                ))
                break
            
            last_group_idx = group_idx


# ============================================================
# MAIN IMPORT VALIDATOR
# ============================================================

class ImportValidator:
    """
    Validates import statements for correctness, organization, and best practices.
    
    Features:
    - Parse and analyze all import statements
    - Check import order and grouping
    - Detect unused imports
    - Forbid problematic import patterns (star, relative, conditional, dynamic)
    - Validate alias naming conventions
    - Check for forbidden modules
    - Detect circular dependencies
    - Calculate import health score
    - Generate comprehensive reports
    """
    
    def __init__(self, config: ImportValidatorConfig):
        self.config = config
        self.parser = ImportParser(config)
        self.state = StateManager(config.project_root / ".ai_state" / "import_validator.json")
        
        logger.info("ImportValidator initialized")
    
    def validate(self) -> ImportReport:
        """Run complete import validation."""
        logger.info("Starting import validation...")
        
        report = ImportReport(
            project_name=self.config.project_root.name
        )
        
        # Find Python files
        python_files = list(self.config.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_ignore(file_path):
                continue
            
            try:
                module_imports = self.parser.parse_file(file_path)
                report.module_imports[str(file_path)] = module_imports
                report.total_files += 1
                
                # Aggregate statistics
                self._aggregate_statistics(report, module_imports)
                
                # Collect issues
                for issue in module_imports.issues:
                    if issue.severity == Severity.ERROR:
                        report.issues.append(issue)
                    else:
                        report.warnings.append(issue)
                
            except Exception as e:
                logger.warning(f"Failed to validate {file_path}: {e}")
        
        # Check for circular dependencies
        report.circular_dependencies = self._detect_circular_dependencies(report)
        
        # Calculate overall score and grade
        report.overall_score = self._calculate_overall_score(report)
        report.grade = self._calculate_grade(report.overall_score)
        
        # Determine validity
        report.is_valid = len(report.issues) == 0
        if self.config.fail_on_warning and report.warnings:
            report.is_valid = False
        
        # Generate summary and recommendations
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Import validation complete: {report.total_imports} imports across {report.total_files} files")
        
        return report
    
    def _aggregate_statistics(self, report: ImportReport, module_imports: ModuleImports):
        """Aggregate statistics from module imports."""
        for imp in module_imports.imports:
            report.total_imports += 1
            
            if not imp.is_used:
                report.unused_imports += 1
            
            if imp.type == ImportType.STAR:
                report.star_imports += 1
            elif imp.type == ImportType.RELATIVE:
                report.relative_imports += 1
            
            if imp.is_conditional:
                report.conditional_imports += 1
            if imp.is_dynamic:
                report.dynamic_imports += 1
            
            group_key = imp.group.value
            report.imports_by_group[group_key] = report.imports_by_group.get(group_key, 0) + 1
        
        # Check for unused imports
        if self.config.forbid_unused_imports:
            for imp in module_imports.unused_imports:
                if not imp.is_type_only:
                    issue = ImportIssue(
                        issue_type="unused_import",
                        severity=Severity.WARNING,
                        file_path=module_imports.file_path,
                        line_number=imp.line_number,
                        import_statement=imp.raw_line,
                        description=f"Import '{imp.module}' is unused",
                        suggestion="Remove unused import"
                    )
                    report.warnings.append(issue)
    
    def _detect_circular_dependencies(self, report: ImportReport) -> List[List[str]]:
        """Detect circular dependencies between modules."""
        # Build dependency graph
        graph = defaultdict(set)
        
        for file_path, module_imports in report.module_imports.items():
            module_name = Path(file_path).stem
            
            for imp in module_imports.imports:
                if imp.group == ImportGroup.FIRST_PARTY or imp.group == ImportGroup.LOCAL:
                    target_module = imp.module.split('.')[-1]
                    graph[module_name].add(target_module)
        
        # Find cycles
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    def _calculate_overall_score(self, report: ImportReport) -> float:
        """Calculate overall import health score."""
        score = 100.0
        
        # Deduct for star imports
        score -= report.star_imports * 5
        
        # Deduct for unused imports
        score -= report.unused_imports * 2
        
        # Deduct for conditional imports
        score -= report.conditional_imports * 3
        
        # Deduct for dynamic imports
        score -= report.dynamic_imports * 10
        
        # Deduct for circular dependencies
        score -= len(report.circular_dependencies) * 15
        
        # Deduct for issues
        score -= len(report.issues) * 5
        score -= len(report.warnings) * 1
        
        return max(0, min(100, score))
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        path_str = str(file_path)
        for pattern in self.config.ignore_patterns:
            if pattern.replace('*', '') in path_str:
                return True
        return False
    
    def _generate_summary(self, report: ImportReport) -> str:
        """Generate validation summary."""
        if report.is_valid:
            return f"✅ Import validation passed. Score: {report.overall_score:.1f} (Grade: {report.grade})"
        else:
            return f"❌ Import issues found: {len(report.issues)} issues, {len(report.warnings)} warnings"
    
    def _generate_recommendations(self, report: ImportReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if report.star_imports > 0:
            recommendations.append(f"Replace {report.star_imports} star imports with explicit imports")
        
        if report.unused_imports > 0:
            recommendations.append(f"Remove {report.unused_imports} unused imports")
        
        if report.dynamic_imports > 0:
            recommendations.append(f"Replace {report.dynamic_imports} dynamic imports with static imports")
        
        if report.circular_dependencies:
            recommendations.append(f"Resolve {len(report.circular_dependencies)} circular dependencies")
        
        if report.overall_score < 80:
            recommendations.append("Improve overall import health score")
        
        return recommendations[:5]
    
    def _save_report(self, report: ImportReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.validated_at.isoformat(),
            'project': report.project_name,
            'is_valid': report.is_valid,
            'score': report.overall_score,
            'grade': report.grade,
            'total_imports': report.total_imports,
            'unused_imports': report.unused_imports,
            'star_imports': report.star_imports,
            'issues': len(report.issues),
            'warnings': len(report.warnings)
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: ImportReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export import report."""
        
        if format == 'json':
            data = {
                'validated_at': report.validated_at.isoformat(),
                'project': report.project_name,
                'is_valid': report.is_valid,
                'score': report.overall_score,
                'grade': report.grade,
                'summary': report.summary,
                'statistics': {
                    'total_files': report.total_files,
                    'total_imports': report.total_imports,
                    'unused_imports': report.unused_imports,
                    'star_imports': report.star_imports,
                    'relative_imports': report.relative_imports,
                    'conditional_imports': report.conditional_imports,
                    'dynamic_imports': report.dynamic_imports,
                    'imports_by_group': report.imports_by_group
                },
                'circular_dependencies': report.circular_dependencies,
                'issues': [
                    {
                        'type': i.issue_type,
                        'severity': i.severity.value,
                        'file': i.file_path,
                        'line': i.line_number,
                        'description': i.description,
                        'suggestion': i.suggestion
                    }
                    for i in report.issues
                ],
                'recommendations': report.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Import Validation Report",
                "",
                f"**Project:** {report.project_name}",
                f"**Validated:** {report.validated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Score:** {report.overall_score:.1f} (Grade: {report.grade})",
                f"**Status:** {report.summary}",
                "",
                "## Summary",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Files Analyzed | {report.total_files} |",
                f"| Total Imports | {report.total_imports} |",
                f"| Unused Imports | {report.unused_imports} |",
                f"| Star Imports | {report.star_imports} |",
                f"| Relative Imports | {report.relative_imports} |",
                f"| Conditional Imports | {report.conditional_imports} |",
                f"| Dynamic Imports | {report.dynamic_imports} |",
                "",
                "## Imports by Group",
                "",
            ]
            
            for group, count in sorted(report.imports_by_group.items()):
                lines.append(f"| {group} | {count} |")
            
            lines.append("")
            
            if report.circular_dependencies:
                lines.extend([
                    "## 🔄 Circular Dependencies",
                    "",
                ])
                for cycle in report.circular_dependencies:
                    lines.append(f"- {' → '.join(cycle)}")
                lines.append("")
            
            if report.issues:
                lines.extend([
                    "## ❌ Issues",
                    "",
                    "| Type | Severity | File | Line | Description |",
                    "|------|----------|------|------|-------------|",
                ])
                for issue in report.issues[:20]:
                    lines.append(f"| {issue.issue_type} | {issue.severity.value} | {Path(issue.file_path).name} | {issue.line_number or 'N/A'} | {issue.description[:40]} |")
                lines.append("")
            
            if report.recommendations:
                lines.extend([
                    "## Recommendations",
                    "",
                ])
                for rec in report.recommendations:
                    lines.append(f"- {rec}")
                lines.append("")
            
            content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("ImportValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for import validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Python import statements")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--allow-star", action="store_true", help="Allow star imports")
    parser.add_argument("--allow-relative", action="store_true", help="Allow relative imports")
    parser.add_argument("--fail-on-warning", action="store_true")
    
    args = parser.parse_args()
    
    config = ImportValidatorConfig(
        project_root=args.project_root,
        forbid_star_imports=not args.allow_star,
        forbid_relative_imports=not args.allow_relative,
        fail_on_warning=args.fail_on_warning
    )
    
    validator = ImportValidator(config)
    
    report = validator.validate()
    
    output = validator.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    
    if config.fail_on_error and not report.is_valid:
        exit(1)
    
    validator.close()


if __name__ == "__main__":
    main()