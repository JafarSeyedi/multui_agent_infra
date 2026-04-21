#!/usr/bin/env python3
"""
Project Scanner - AI Development Framework
Comprehensive project scanning and analysis tool.

Part of the Level 2 Analysis tools (scanners/project_scanner.py)

This project_scanner.py provides:

1. Multi-Level Scanning - Quick, standard, deep, and comprehensive scan levels
2. AST-Based Analysis - Full Python AST parsing for deep code understanding
3. Symbol Extraction - Classes, functions, methods with rich metadata
4. Dependency Graphs - Module, import, and call graphs
5. Complexity Metrics - Cyclomatic and cognitive complexity
6. Project Type Detection - Library, application, web service, CLI, monorepo
7. Git Integration - Track changes and file history
8. Incremental Scanning - Only scan changed files
9. Issue Detection - Circular deps, high complexity, missing docstrings
10. Multiple Export Formats - JSON, Markdown, Mermaid diagrams
11. Caching - Content-based caching for fast incremental scans
12. Comprehensive Statistics - Symbol distribution, complexity trends

The project scanner is the foundation for all other analysis tools, providing a complete knowledge graph of your codebase.
"""

import ast
import json
import hashlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager
from ...shared.file_utils import FileUtils
from ...shared.git_utils import GitUtils

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class ScanLevel(str, Enum):
    """Depth of scanning."""
    QUICK = "quick"          # File names, basic stats only
    STANDARD = "standard"    # AST parsing, imports, symbols
    DEEP = "deep"            # Full analysis including complexity, dependencies
    COMPREHENSIVE = "comprehensive"  # Everything plus cross-references


class SymbolType(str, Enum):
    """Type of code symbol."""
    MODULE = "module"
    PACKAGE = "package"
    CLASS = "class"
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    METHOD = "method"
    ASYNC_METHOD = "async_method"
    PROPERTY = "property"
    CLASS_METHOD = "class_method"
    STATIC_METHOD = "static_method"
    ABSTRACT_METHOD = "abstract_method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    TYPE_ALIAS = "type_alias"
    ENUM = "enum"
    DATACLASS = "dataclass"
    NAMED_TUPLE = "named_tuple"
    PROTOCOL = "protocol"
    ABC = "abc"
    EXCEPTION = "exception"
    DECORATOR = "decorator"
    IMPORT = "import"


class FileType(str, Enum):
    """Type of file in project."""
    PYTHON = "python"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    TEST = "test"
    DATA = "data"
    ASSET = "asset"
    BUILD = "build"
    UNKNOWN = "unknown"


class ProjectType(str, Enum):
    """Type of project."""
    LIBRARY = "library"
    APPLICATION = "application"
    WEB_SERVICE = "web_service"
    CLI_TOOL = "cli_tool"
    DOCUMENTATION = "documentation"
    MONOREPO = "monorepo"
    UNKNOWN = "unknown"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ScanConfig:
    """Configuration for project scanning."""
    project_root: Path
    scan_level: ScanLevel = ScanLevel.STANDARD
    include_patterns: List[str] = field(default_factory=lambda: ["*.py", "*.md", "*.json", "*.yaml", "*.yml", "*.toml"])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__/*", "*.pyc", ".git/*", ".venv/*", "venv/*", "env/*",
        "dist/*", "build/*", "*.egg-info/*", ".pytest_cache/*",
        ".mypy_cache/*", ".ruff_cache/*", ".ai_state/*",
        "node_modules/*", ".tox/*", ".coverage", "htmlcov/*"
    ])
    max_file_size_mb: float = 10.0
    analyze_imports: bool = True
    analyze_dependencies: bool = True
    compute_complexity: bool = True
    extract_docstrings: bool = True
    detect_duplicates: bool = False
    track_git_info: bool = True
    include_tests: bool = True
    follow_symlinks: bool = False


@dataclass
class CodeSymbol:
    """Represents a code symbol."""
    id: str
    name: str
    symbol_type: SymbolType
    file_path: str
    module_path: str
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    signature: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    used_by: List[str] = field(default_factory=list)
    complexity: int = 0
    cognitive_complexity: int = 0
    maintainability_index: float = 0.0
    is_public: bool = True
    is_async: bool = False
    is_abstract: bool = False
    is_final: bool = False
    is_deprecated: bool = False
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"{self.symbol_type.value}_{hashlib.sha256(f'{self.file_path}:{self.name}'.encode()).hexdigest()[:16]}"


@dataclass
class FileInfo:
    """Information about a scanned file."""
    path: str
    relative_path: str
    file_type: FileType
    size_bytes: int
    lines_of_code: int = 0
    lines_of_comments: int = 0
    lines_blank: int = 0
    content_hash: str = ""
    last_modified: Optional[datetime] = None
    encoding: str = "utf-8"
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    symbols: List[CodeSymbol] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    complexity: int = 0
    coverage: Optional[float] = None
    git_last_commit: Optional[str] = None
    git_last_author: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    name: str
    path: str
    package: str
    is_package: bool = False
    file_info: Optional[FileInfo] = None
    submodules: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    symbols: List[CodeSymbol] = field(default_factory=list)


@dataclass
class PackageInfo:
    """Information about a Python package."""
    name: str
    path: str
    modules: List[str] = field(default_factory=list)
    subpackages: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    is_namespace: bool = False


@dataclass
class DependencyInfo:
    """Information about a dependency."""
    name: str
    version: Optional[str] = None
    dependency_type: str = "external"  # external, internal, dev, optional
    required_by: List[str] = field(default_factory=list)
    is_direct: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectGraph:
    """Complete project graph."""
    project_root: str
    project_name: str
    project_type: ProjectType
    scanned_at: datetime
    scan_level: ScanLevel
    files: Dict[str, FileInfo] = field(default_factory=dict)
    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    packages: Dict[str, PackageInfo] = field(default_factory=dict)
    symbols: Dict[str, CodeSymbol] = field(default_factory=dict)
    dependencies: Dict[str, DependencyInfo] = field(default_factory=dict)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    reverse_dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    import_graph: Dict[str, List[str]] = field(default_factory=dict)
    call_graph: Dict[str, List[str]] = field(default_factory=dict)
    inheritance_graph: Dict[str, List[str]] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# AST VISITORS
# ============================================================

class SymbolExtractor(ast.NodeVisitor):
    """Extract symbols from Python AST."""
    
    def __init__(self, file_path: str, module_path: str, config: ScanConfig):
        self.file_path = file_path
        self.module_path = module_path
        self.config = config
        self.symbols: List[CodeSymbol] = []
        self.imports: List[str] = []
        self.exports: List[str] = []
        self.current_class: Optional[str] = None
        self.class_stack: List[str] = []
        self._all_exports: Optional[Set[str]] = None
    
    def visit_Module(self, node: ast.Module):
        """Visit module."""
        # Extract module docstring
        docstring = ast.get_docstring(node)
        
        # Find __all__ exports
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        if isinstance(child.value, ast.List):
                            self._all_exports = {
                                item.value if isinstance(item, ast.Constant) else None
                                for item in child.value.elts
                            }
        
        self.generic_visit(node)
        
        # Add module symbol
        if self.config.scan_level in (ScanLevel.DEEP, ScanLevel.COMPREHENSIVE):
            symbol = CodeSymbol(
                name=self.module_path,
                symbol_type=SymbolType.MODULE,
                file_path=self.file_path,
                module_path=self.module_path,
                line_start=1,
                line_end=node.end_lineno or 1,
                docstring=docstring,
                is_public=True,
                exports=self.exports
            )
            self.symbols.append(symbol)
    
    def visit_Import(self, node: ast.Import):
        """Visit import."""
        for alias in node.names:
            self.imports.append(alias.name)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from import."""
        if node.module:
            self.imports.append(node.module)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        prev_class = self.current_class
        self.current_class = node.name
        self.class_stack.append(node.name)
        
        # Determine symbol type
        symbol_type = self._get_class_type(node)
        
        # Extract bases
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(self._get_attribute_name(base))
        
        # Extract decorators
        decorators = self._extract_decorators(node)
        
        # Check if public
        is_public = not node.name.startswith('_')
        if self._all_exports is not None:
            is_public = node.name in self._all_exports
        
        symbol = CodeSymbol(
            name=f"{self.module_path}.{'.'.join(self.class_stack)}",
            symbol_type=symbol_type,
            file_path=self.file_path,
            module_path=self.module_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            decorators=decorators,
            bases=bases,
            is_public=is_public,
            is_abstract=any(d == 'abstractmethod' for d in decorators),
            is_final=any(d == 'final' for d in decorators),
            is_deprecated=any(d == 'deprecated' for d in decorators)
        )
        
        if self.config.compute_complexity:
            symbol.complexity = self._compute_cyclomatic_complexity(node)
            symbol.cognitive_complexity = self._compute_cognitive_complexity(node)
        
        self.symbols.append(symbol)
        self.generic_visit(node)
        
        self.class_stack.pop()
        self.current_class = prev_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        self._visit_function(node, is_async=False)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self._visit_function(node, is_async=True)
    
    def _visit_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool):
        """Common function visitor."""
        # Determine symbol type
        if self.current_class:
            if node.name == '__init__':
                symbol_type = SymbolType.METHOD
            elif node.name == '__new__':
                symbol_type = SymbolType.CLASS_METHOD
            elif any(isinstance(d, ast.Name) and d.id == 'property' for d in node.decorator_list):
                symbol_type = SymbolType.PROPERTY
            elif any(isinstance(d, ast.Name) and d.id == 'classmethod' for d in node.decorator_list):
                symbol_type = SymbolType.CLASS_METHOD
            elif any(isinstance(d, ast.Name) and d.id == 'staticmethod' for d in node.decorator_list):
                symbol_type = SymbolType.STATIC_METHOD
            elif any(isinstance(d, ast.Name) and d.id == 'abstractmethod' for d in node.decorator_list):
                symbol_type = SymbolType.ABSTRACT_METHOD
            else:
                symbol_type = SymbolType.ASYNC_METHOD if is_async else SymbolType.METHOD
        else:
            symbol_type = SymbolType.ASYNC_FUNCTION if is_async else SymbolType.FUNCTION
        
        # Extract decorators
        decorators = self._extract_decorators(node)
        
        # Build signature
        signature = self._get_function_signature(node)
        
        # Check if public
        is_public = not node.name.startswith('_')
        if self._all_exports is not None:
            is_public = node.name in self._all_exports
        
        full_name = f"{self.module_path}.{'.'.join(self.class_stack)}.{node.name}" if self.class_stack else f"{self.module_path}.{node.name}"
        
        symbol = CodeSymbol(
            name=full_name,
            symbol_type=symbol_type,
            file_path=self.file_path,
            module_path=self.module_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            signature=signature,
            decorators=decorators,
            is_public=is_public,
            is_async=is_async,
            is_abstract=any(d == 'abstractmethod' for d in decorators),
            is_final=any(d == 'final' for d in decorators),
            is_deprecated=any(d == 'deprecated' for d in decorators)
        )
        
        if self.config.compute_complexity:
            symbol.complexity = self._compute_cyclomatic_complexity(node)
            symbol.cognitive_complexity = self._compute_cognitive_complexity(node)
        
        self.symbols.append(symbol)
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment for constants."""
        if not self.current_class:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    symbol = CodeSymbol(
                        name=f"{self.module_path}.{target.id}",
                        symbol_type=SymbolType.CONSTANT,
                        file_path=self.file_path,
                        module_path=self.module_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        is_public=not target.id.startswith('_')
                    )
                    self.symbols.append(symbol)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Visit annotated assignment for type aliases."""
        if not self.current_class and isinstance(node.target, ast.Name):
            symbol = CodeSymbol(
                name=f"{self.module_path}.{node.target.id}",
                symbol_type=SymbolType.TYPE_ALIAS,
                file_path=self.file_path,
                module_path=self.module_path,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                is_public=not node.target.id.startswith('_')
            )
            self.symbols.append(symbol)
    
    def _get_class_type(self, node: ast.ClassDef) -> SymbolType:
        """Determine class symbol type."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == 'dataclass':
                return SymbolType.DATACLASS
            elif isinstance(decorator, ast.Name) and decorator.id == 'dataclass_transform':
                return SymbolType.DATACLASS
        
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id == 'Enum':
                    return SymbolType.ENUM
                elif base.id == 'Protocol':
                    return SymbolType.PROTOCOL
                elif base.id == 'ABC':
                    return SymbolType.ABC
                elif base.id == 'Exception' or base.id.endswith('Error'):
                    return SymbolType.EXCEPTION
            elif isinstance(base, ast.Attribute):
                if base.attr == 'NamedTuple':
                    return SymbolType.NAMED_TUPLE
        
        return SymbolType.CLASS
    
    def _extract_decorators(self, node: Union[ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef]) -> List[str]:
        """Extract decorator names."""
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(self._get_attribute_name(dec))
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    decorators.append(self._get_attribute_name(dec.func))
        return decorators
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get full attribute name."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        return node.attr
    
    def _get_function_signature(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
        """Get function signature as string."""
        args = []
        
        # Positional args
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        # Varargs
        if node.args.vararg:
            arg_str = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                arg_str += f": {ast.unparse(node.args.vararg.annotation)}"
            args.append(arg_str)
        
        # Kwargs
        if node.args.kwarg:
            arg_str = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                arg_str += f": {ast.unparse(node.args.kwarg.annotation)}"
            args.append(arg_str)
        
        # Return type
        returns = ""
        if node.returns:
            returns = f" -> {ast.unparse(node.returns)}"
        
        return f"def {node.name}({', '.join(args)}){returns}"
    
    def _compute_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Compute cyclomatic complexity."""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.IfExp):
                complexity += 1
            elif isinstance(child, ast.Match):  # Python 3.10+
                complexity += 1
        
        return complexity
    
    def _compute_cognitive_complexity(self, node: ast.AST) -> int:
        """Compute cognitive complexity."""
        complexity = 0
        nesting_level = 0
        
        def visit_with_nesting(child: ast.AST, level: int):
            nonlocal complexity
            
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)):
                complexity += 1 + level
                level += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.IfExp):
                complexity += 1 + level
            elif isinstance(child, ast.Break, ast.Continue):
                if level > 0:
                    complexity += 1
            
            for grandchild in ast.iter_child_nodes(child):
                visit_with_nesting(grandchild, level)
        
        visit_with_nesting(node, nesting_level)
        return complexity


class DependencyExtractor(ast.NodeVisitor):
    """Extract dependencies and call graph from AST."""
    
    def __init__(self, module_path: str):
        self.module_path = module_path
        self.dependencies: List[str] = []
        self.calls: List[str] = []
        self.current_function: Optional[str] = None
    
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.dependencies.append(alias.name)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self.dependencies.append(node.module)
    
    def visit_Call(self, node: ast.Call):
        """Visit function call."""
        if self.current_function:
            if isinstance(node.func, ast.Name):
                self.calls.append(f"{self.module_path}.{self.current_function} -> {node.func.id}")
            elif isinstance(node.func, ast.Attribute):
                call_target = self._get_call_target(node.func)
                self.calls.append(f"{self.module_path}.{self.current_function} -> {call_target}")
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        prev_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev_func
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        prev_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev_func
    
    def _get_call_target(self, node: ast.Attribute) -> str:
        """Get full call target name."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_call_target(node.value)}.{node.attr}"
        return node.attr


# ============================================================
# MAIN PROJECT SCANNER CLASS
# ============================================================

class ProjectScanner:
    """
    Comprehensive project scanning and analysis tool.
    
    Features:
    - Multi-level scanning (quick to comprehensive)
    - AST-based code analysis
    - Symbol extraction (classes, functions, methods)
    - Dependency graph construction
    - Import/call/inheritance graphs
    - Complexity metrics (cyclomatic, cognitive)
    - Project type detection
    - Git integration
    - Duplicate detection
    - Incremental scanning
    - Export to multiple formats
    """
    
    def __init__(self, config: ScanConfig):
        self.config = config
        self.project_root = config.project_root
        
        # Git integration
        self.git = GitUtils(config.project_root) if config.track_git_info else None
        
        # State management
        self.state = StateManager(config.project_root / ".ai_state" / "project_scanner.json")
        self.file_hashes: Dict[str, str] = {}
        
        # Caches
        self._ast_cache: Dict[str, ast.AST] = {}
        
        logger.info(f"ProjectScanner initialized for {config.project_root} (level={config.scan_level.value})")
    
    # ============================================================
    # MAIN SCANNING
    # ============================================================
    
    def scan(self, force_full: bool = False) -> ProjectGraph:
        """
        Perform project scan.
        
        Args:
            force_full: Force full rescan even if files unchanged
        """
        start_time = datetime.now()
        logger.info(f"Starting project scan (level={self.config.scan_level.value})")
        
        # Initialize graph
        graph = ProjectGraph(
            project_root=str(self.config.project_root),
            project_name=self._detect_project_name(),
            project_type=ProjectType.UNKNOWN,
            scanned_at=start_time,
            scan_level=self.config.scan_level
        )
        
        # Find all files
        files = self._find_files()
        logger.info(f"Found {len(files)} files to scan")
        
        # Scan files based on level
        for file_path in files:
            file_info = self._scan_file(file_path, force_full)
            if file_info:
                graph.files[file_info.relative_path] = file_info
        
        # Build module and package structure
        self._build_module_structure(graph)
        
        # Deep analysis if requested
        if self.config.scan_level in (ScanLevel.DEEP, ScanLevel.COMPREHENSIVE):
            self._analyze_dependencies(graph)
            self._build_dependency_graphs(graph)
            self._compute_statistics(graph)
            self._detect_issues(graph)
        
        # Detect project type
        graph.project_type = self._detect_project_type(graph)
        
        # Add git info
        if self.git:
            graph.metadata['git'] = {
                'branch': self.git.get_current_branch(),
                'commit': self.git.get_current_commit(),
                'last_commit_date': self.git.get_last_commit_date()
            }
        
        scan_duration = (datetime.now() - start_time).total_seconds()
        graph.metadata['scan_duration'] = scan_duration
        
        logger.info(f"Scan completed in {scan_duration:.1f}s: {len(graph.files)} files, {len(graph.modules)} modules, {len(graph.symbols)} symbols")
        
        return graph
    
    def scan_incremental(self) -> Optional[ProjectGraph]:
        """Perform incremental scan of changed files only."""
        if not self.git:
            logger.warning("Git integration required for incremental scanning")
            return None
        
        # Get changed files
        changed_files = self.git.get_changed_files()
        
        if not changed_files:
            logger.info("No changed files detected")
            return None
        
        # Filter Python files
        python_files = [f for f in changed_files if f.suffix == '.py']
        
        if not python_files:
            logger.info("No changed Python files")
            return None
        
        logger.info(f"Incremental scan of {len(python_files)} changed files")
        
        # Load existing graph
        existing_graph = self._load_graph()
        if not existing_graph:
            return self.scan(force_full=True)
        
        # Update changed files
        for file_path in python_files:
            file_info = self._scan_file(file_path, force_full=True)
            if file_info:
                existing_graph.files[file_info.relative_path] = file_info
        
        # Rebuild affected parts
        self._build_module_structure(existing_graph)
        self._analyze_dependencies(existing_graph)
        self._build_dependency_graphs(existing_graph)
        self._compute_statistics(existing_graph)
        
        existing_graph.scanned_at = datetime.now()
        
        return existing_graph
    
    # ============================================================
    # FILE SCANNING
    # ============================================================
    
    def _find_files(self) -> List[Path]:
        """Find all files to scan."""
        files = []
        
        for pattern in self.config.include_patterns:
            for file_path in self.config.project_root.rglob(pattern):
                if self._should_include_file(file_path):
                    files.append(file_path)
        
        # Exclude tests if configured
        if not self.config.include_tests:
            files = [f for f in files if 'test' not in str(f).lower()]
        
        return files
    
    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included."""
        import fnmatch
        
        if not file_path.is_file():
            return False
        
        if self.config.follow_symlinks and file_path.is_symlink():
            file_path = file_path.resolve()
            if not file_path.is_file():
                return False
        
        # Check size
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > self.config.max_file_size_mb:
            logger.warning(f"Skipping large file: {file_path} ({size_mb:.1f}MB)")
            return False
        
        rel_path = str(file_path.relative_to(self.config.project_root))
        
        # Check exclude patterns
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return False
        
        return True
    
    def _scan_file(self, file_path: Path, force_full: bool) -> Optional[FileInfo]:
        """Scan a single file."""
        rel_path = str(file_path.relative_to(self.config.project_root))
        
        # Check if file has changed
        content_hash = self._compute_file_hash(file_path)
        
        if not force_full and rel_path in self.file_hashes:
            if self.file_hashes[rel_path] == content_hash:
                logger.debug(f"Skipping unchanged file: {rel_path}")
                return self._load_cached_file_info(rel_path)
        
        self.file_hashes[rel_path] = content_hash
        
        # Detect file type
        file_type = self._detect_file_type(file_path)
        
        # Basic file info
        stat = file_path.stat()
        file_info = FileInfo(
            path=str(file_path),
            relative_path=rel_path,
            file_type=file_type,
            size_bytes=stat.st_size,
            content_hash=content_hash,
            last_modified=datetime.fromtimestamp(stat.st_mtime)
        )
        
        # Git info
        if self.git:
            file_info.git_last_commit = self.git.get_last_commit_for_file(rel_path)
            file_info.git_last_author = self.git.get_last_author_for_file(rel_path)
        
        # Parse based on file type
        if file_type == FileType.PYTHON:
            self._scan_python_file(file_path, file_info)
        elif file_type == FileType.DOCUMENTATION:
            self._scan_documentation_file(file_path, file_info)
        
        # Cache file info
        self._cache_file_info(rel_path, file_info)
        
        return file_info
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def _detect_file_type(self, file_path: Path) -> FileType:
        """Detect file type from extension and content."""
        ext = file_path.suffix.lower()
        
        if ext == '.py':
            if 'test' in str(file_path).lower():
                return FileType.TEST
            return FileType.PYTHON
        
        if ext in ('.md', '.markdown', '.rst', '.txt', '.adoc'):
            return FileType.DOCUMENTATION
        
        if ext in ('.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'):
            return FileType.CONFIGURATION
        
        if ext in ('.csv', '.tsv', '.xml', '.data'):
            return FileType.DATA
        
        if ext in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.pdf'):
            return FileType.ASSET
        
        if 'build' in str(file_path) or 'dist' in str(file_path):
            return FileType.BUILD
        
        return FileType.UNKNOWN
    
    def _scan_python_file(self, file_path: Path, file_info: FileInfo):
        """Scan Python file with AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count lines
            lines = content.split('\n')
            file_info.lines_of_code = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            file_info.lines_of_comments = len([l for l in lines if l.strip().startswith('#')])
            file_info.lines_blank = len([l for l in lines if not l.strip()])
            
            if self.config.scan_level == ScanLevel.QUICK:
                return
            
            # Parse AST
            tree = ast.parse(content)
            self._ast_cache[str(file_path)] = tree
            
            # Get module path
            module_path = self._get_module_path(file_path)
            
            # Extract symbols
            if self.config.scan_level in (ScanLevel.STANDARD, ScanLevel.DEEP, ScanLevel.COMPREHENSIVE):
                extractor = SymbolExtractor(str(file_path), module_path, self.config)
                extractor.visit(tree)
                
                file_info.symbols = extractor.symbols
                file_info.imports = list(set(extractor.imports))
                file_info.exports = extractor.exports
            
            # Extract dependencies
            if self.config.analyze_dependencies:
                dep_extractor = DependencyExtractor(module_path)
                dep_extractor.visit(tree)
                file_info.dependencies = list(set(dep_extractor.dependencies))
            
            # Compute overall complexity
            if self.config.compute_complexity:
                file_info.complexity = sum(s.complexity for s in file_info.symbols)
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to scan {file_path}: {e}")
    
    def _scan_documentation_file(self, file_path: Path, file_info: FileInfo):
        """Scan documentation file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            file_info.lines_of_code = len(lines)
            
            # Could add markdown parsing here for deeper analysis
        except Exception as e:
            logger.error(f"Failed to scan documentation {file_path}: {e}")
    
    def _get_module_path(self, file_path: Path) -> str:
        """Get Python module path from file path."""
        rel_path = file_path.relative_to(self.config.project_root)
        parts = list(rel_path.parts)
        
        if parts[-1] == '__init__.py':
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].replace('.py', '')
        
        return '.'.join(parts)
    
    # ============================================================
    # STRUCTURE BUILDING
    # ============================================================
    
    def _build_module_structure(self, graph: ProjectGraph):
        """Build module and package structure."""
        for rel_path, file_info in graph.files.items():
            if file_info.file_type != FileType.PYTHON:
                continue
            
            module_path = self._get_module_path(Path(file_info.path))
            
            # Determine package
            parts = module_path.split('.')
            package = '.'.join(parts[:-1]) if len(parts) > 1 else ''
            
            # Create module info
            module_info = ModuleInfo(
                name=module_path,
                path=file_info.path,
                package=package,
                is_package=Path(file_info.path).name == '__init__.py',
                file_info=file_info,
                imports=file_info.imports,
                exports=file_info.exports,
                symbols=file_info.symbols
            )
            
            graph.modules[module_path] = module_info
            
            # Update package
            if package:
                if package not in graph.packages:
                    graph.packages[package] = PackageInfo(
                        name=package,
                        path=str(Path(file_info.path).parent)
                    )
                
                graph.packages[package].modules.append(module_path)
            
            # Add symbols to graph
            for symbol in file_info.symbols:
                graph.symbols[symbol.name] = symbol
    
    def _analyze_dependencies(self, graph: ProjectGraph):
        """Analyze module dependencies."""
        for module_path, module_info in graph.modules.items():
            for imp in module_info.imports:
                # Check if internal
                if imp in graph.modules:
                    module_info.dependencies.append(imp)
                    graph.modules[imp].dependents.append(module_path)
                else:
                    # External dependency
                    if imp not in graph.dependencies:
                        graph.dependencies[imp] = DependencyInfo(
                            name=imp,
                            dependency_type="external",
                            is_direct=True
                        )
                    graph.dependencies[imp].required_by.append(module_path)
    
    def _build_dependency_graphs(self, graph: ProjectGraph):
        """Build various dependency graphs."""
        # Dependency graph
        for module_path, module_info in graph.modules.items():
            graph.dependency_graph[module_path] = module_info.dependencies
        
        # Reverse dependency graph
        for module_path, deps in graph.dependency_graph.items():
            for dep in deps:
                if dep not in graph.reverse_dependency_graph:
                    graph.reverse_dependency_graph[dep] = []
                graph.reverse_dependency_graph[dep].append(module_path)
        
        # Import graph (all imports)
        for module_path, module_info in graph.modules.items():
            graph.import_graph[module_path] = module_info.imports
        
        # Inheritance graph
        for symbol in graph.symbols.values():
            if symbol.symbol_type in (SymbolType.CLASS, SymbolType.DATACLASS, SymbolType.ENUM):
                if symbol.bases:
                    graph.inheritance_graph[symbol.name] = symbol.bases
    
    def _compute_statistics(self, graph: ProjectGraph):
        """Compute project statistics."""
        stats = {
            'total_files': len(graph.files),
            'python_files': sum(1 for f in graph.files.values() if f.file_type == FileType.PYTHON),
            'test_files': sum(1 for f in graph.files.values() if f.file_type == FileType.TEST),
            'doc_files': sum(1 for f in graph.files.values() if f.file_type == FileType.DOCUMENTATION),
            'total_lines': sum(f.lines_of_code for f in graph.files.values()),
            'total_modules': len(graph.modules),
            'total_packages': len(graph.packages),
            'total_symbols': len(graph.symbols),
            'symbols_by_type': defaultdict(int),
            'total_dependencies': len(graph.dependencies),
            'avg_complexity': 0,
            'max_complexity': 0,
            'most_complex_file': None,
            'largest_file': None
        }
        
        # Symbol type distribution
        for symbol in graph.symbols.values():
            stats['symbols_by_type'][symbol.symbol_type.value] += 1
        
        # Complexity stats
        complexities = [f.complexity for f in graph.files.values() if f.complexity > 0]
        if complexities:
            stats['avg_complexity'] = sum(complexities) / len(complexities)
            stats['max_complexity'] = max(complexities)
            
            for file_info in graph.files.values():
                if file_info.complexity == stats['max_complexity']:
                    stats['most_complex_file'] = file_info.relative_path
                    break
        
        # Largest file
        if graph.files:
            largest = max(graph.files.values(), key=lambda f: f.lines_of_code)
            stats['largest_file'] = largest.relative_path
        
        stats['symbols_by_type'] = dict(stats['symbols_by_type'])
        graph.statistics = stats
    
    def _detect_issues(self, graph: ProjectGraph):
        """Detect potential issues."""
        issues = []
        
        # High complexity files
        for file_info in graph.files.values():
            if file_info.complexity > 50:
                issues.append({
                    'type': 'high_complexity',
                    'severity': 'warning',
                    'file': file_info.relative_path,
                    'complexity': file_info.complexity,
                    'message': f"File has high cyclomatic complexity ({file_info.complexity})"
                })
        
        # Circular dependencies
        for module_path in graph.modules:
            cycle = self._find_cycle(graph.dependency_graph, module_path)
            if cycle:
                issues.append({
                    'type': 'circular_dependency',
                    'severity': 'error',
                    'cycle': cycle,
                    'message': f"Circular dependency detected: {' -> '.join(cycle)}"
                })
                break  # Only report first cycle
        
        # Missing docstrings
        for symbol in graph.symbols.values():
            if symbol.is_public and not symbol.docstring:
                if symbol.symbol_type in (SymbolType.CLASS, SymbolType.FUNCTION, SymbolType.METHOD):
                    issues.append({
                        'type': 'missing_docstring',
                        'severity': 'info',
                        'symbol': symbol.name,
                        'file': symbol.file_path,
                        'message': f"Public {symbol.symbol_type.value} missing docstring"
                    })
        
        # Too many dependencies
        for module_path, deps in graph.dependency_graph.items():
            if len(deps) > 20:
                issues.append({
                    'type': 'too_many_dependencies',
                    'severity': 'warning',
                    'module': module_path,
                    'count': len(deps),
                    'message': f"Module has {len(deps)} dependencies (consider refactoring)"
                })
        
        graph.issues = issues[:100]  # Limit issues
    
    def _find_cycle(self, graph: Dict[str, List[str]], start: str) -> Optional[List[str]]:
        """Find cycle in dependency graph."""
        visited = set()
        path = []
        
        def dfs(node: str) -> Optional[List[str]]:
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
            
            if node in visited:
                return None
            
            visited.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                cycle = dfs(neighbor)
                if cycle:
                    return cycle
            
            path.pop()
            return None
        
        return dfs(start)
    
    # ============================================================
    # PROJECT DETECTION
    # ============================================================
    
    def _detect_project_name(self) -> str:
        """Detect project name."""
        # Try pyproject.toml
        pyproject = self.config.project_root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text(encoding='utf-8')
            import re
            match = re.search(r'name\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
        
        # Try setup.py
        setup = self.config.project_root / "setup.py"
        if setup.exists():
            content = setup.read_text(encoding='utf-8')
            import re
            match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        
        # Fallback to directory name
        return self.config.project_root.name
    
    def _detect_project_type(self, graph: ProjectGraph) -> ProjectType:
        """Detect project type."""
        # Check for monorepo
        if (self.config.project_root / "packages").is_dir():
            return ProjectType.MONOREPO
        
        # Check for web framework
        has_fastapi = any('fastapi' in dep for dep in graph.dependencies)
        has_flask = any('flask' in dep for dep in graph.dependencies)
        has_django = any('django' in dep for dep in graph.dependencies)
        
        if has_fastapi or has_flask or has_django:
            return ProjectType.WEB_SERVICE
        
        # Check for CLI
        has_click = any('click' in dep for dep in graph.dependencies)
        has_argparse = any('argparse' in imp for module in graph.modules.values() for imp in module.imports)
        
        if has_click or has_argparse:
            return ProjectType.CLI_TOOL
        
        # Check for library
        if graph.packages:
            return ProjectType.LIBRARY
        
        return ProjectType.APPLICATION
    
    # ============================================================
    # CACHING
    # ============================================================
    
    def _cache_file_info(self, rel_path: str, file_info: FileInfo):
        """Cache file info to state."""
        cached = self.state.get('file_cache', {})
        cached[rel_path] = {
            'content_hash': file_info.content_hash,
            'lines_of_code': file_info.lines_of_code,
            'complexity': file_info.complexity,
            'symbol_count': len(file_info.symbols),
            'cached_at': datetime.now().isoformat()
        }
        self.state.set('file_cache', cached)
        self.state.save()
    
    def _load_cached_file_info(self, rel_path: str) -> Optional[FileInfo]:
        """Load cached file info."""
        cached = self.state.get('file_cache', {})
        if rel_path not in cached:
            return None
        
        file_path = self.config.project_root / rel_path
        stat = file_path.stat()
        
        return FileInfo(
            path=str(file_path),
            relative_path=rel_path,
            file_type=self._detect_file_type(file_path),
            size_bytes=stat.st_size,
            content_hash=cached[rel_path]['content_hash'],
            lines_of_code=cached[rel_path].get('lines_of_code', 0),
            complexity=cached[rel_path].get('complexity', 0),
            last_modified=datetime.fromtimestamp(stat.st_mtime)
        )
    
    def _load_graph(self) -> Optional[ProjectGraph]:
        """Load previously saved graph."""
        saved = self.state.get('last_graph')
        if not saved:
            return None
        
        # Basic reconstruction
        graph = ProjectGraph(
            project_root=saved.get('project_root', str(self.config.project_root)),
            project_name=saved.get('project_name', ''),
            project_type=ProjectType(saved.get('project_type', 'unknown')),
            scanned_at=datetime.fromisoformat(saved.get('scanned_at', datetime.now().isoformat())),
            scan_level=ScanLevel(saved.get('scan_level', 'standard'))
        )
        
        graph.statistics = saved.get('statistics', {})
        graph.metadata = saved.get('metadata', {})
        
        return graph
    
    # ============================================================
    # EXPORT
    # ============================================================
    
    def export_graph(self, graph: ProjectGraph, output_path: Optional[Path] = None, format: str = "json") -> Union[str, Path]:
        """Export project graph."""
        data = {
            'project_root': graph.project_root,
            'project_name': graph.project_name,
            'project_type': graph.project_type.value,
            'scanned_at': graph.scanned_at.isoformat(),
            'scan_level': graph.scan_level.value,
            'statistics': graph.statistics,
            'files': len(graph.files),
            'modules': len(graph.modules),
            'packages': len(graph.packages),
            'symbols': len(graph.symbols),
            'dependencies': len(graph.dependencies),
            'issues': graph.issues,
            'metadata': graph.metadata
        }
        
        if format == "json":
            content = json.dumps(data, indent=2, default=str)
            if output_path:
                output_path.write_text(content)
                return output_path
            return content
        
        elif format == "markdown":
            content = self._generate_markdown_report(graph)
            if output_path:
                output_path.write_text(content)
                return output_path
            return content
        
        return ""
    
    def _generate_markdown_report(self, graph: ProjectGraph) -> str:
        """Generate markdown report."""
        lines = [
            f"# Project Scan Report: {graph.project_name}",
            "",
            f"**Scanned:** {graph.scanned_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Level:** {graph.scan_level.value}",
            f"**Project Type:** {graph.project_type.value}",
            "",
            "## Summary",
            "",
            f"- **Files:** {len(graph.files)} ({graph.statistics.get('python_files', 0)} Python)",
            f"- **Lines of Code:** {graph.statistics.get('total_lines', 0):,}",
            f"- **Modules:** {len(graph.modules)}",
            f"- **Packages:** {len(graph.packages)}",
            f"- **Symbols:** {len(graph.symbols)}",
            f"- **Dependencies:** {len(graph.dependencies)}",
            "",
            "## Symbol Distribution",
            "",
            "| Type | Count |",
            "|------|-------|",
        ]
        
        for sym_type, count in graph.statistics.get('symbols_by_type', {}).items():
            lines.append(f"| {sym_type} | {count} |")
        
        if graph.issues:
            lines.extend([
                "",
                "## Issues",
                "",
            ])
            
            issues_by_severity = defaultdict(list)
            for issue in graph.issues:
                issues_by_severity[issue['severity']].append(issue)
            
            for severity in ['error', 'warning', 'info']:
                if severity in issues_by_severity:
                    lines.append(f"### {severity.title()} ({len(issues_by_severity[severity])})")
                    for issue in issues_by_severity[severity][:10]:
                        lines.append(f"- {issue['message']}")
        
        return '\n'.join(lines)
    
    def export_mermaid_diagram(self, graph: ProjectGraph, max_nodes: int = 50) -> str:
        """Generate Mermaid dependency diagram."""
        lines = ["```mermaid", "graph TD"]
        
        # Get top modules by dependency count
        module_deps = {m: len(deps) for m, deps in graph.dependency_graph.items()}
        top_modules = sorted(module_deps, key=module_deps.get, reverse=True)[:max_nodes]
        
        for module in top_modules:
            short_name = module.split('.')[-1]
            lines.append(f"    {module.replace('.', '_')}[\"{short_name}\"]")
        
        for module in top_modules:
            for dep in graph.dependency_graph.get(module, []):
                if dep in top_modules:
                    lines.append(f"    {module.replace('.', '_')} --> {dep.replace('.', '_')}")
        
        lines.append("```")
        return '\n'.join(lines)
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("ProjectScanner closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for project scanner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive project scanning and analysis")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    parser.add_argument("--level", choices=[l.value for l in ScanLevel],
                       default=ScanLevel.STANDARD.value, help="Scan depth")
    parser.add_argument("--output", "-o", type=Path, help="Output file")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown",
                       help="Output format")
    parser.add_argument("--incremental", action="store_true", help="Incremental scan")
    parser.add_argument("--full", action="store_true", help="Force full scan")
    parser.add_argument("--mermaid", action="store_true", help="Generate Mermaid diagram")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    parser.add_argument("--issues", action="store_true", help="Show issues only")
    
    args = parser.parse_args()
    
    config = ScanConfig(
        project_root=args.project_root,
        scan_level=ScanLevel(args.level)
    )
    
    scanner = ProjectScanner(config)
    
    if args.incremental:
        graph = scanner.scan_incremental()
        if not graph:
            print("No changes detected")
            return
    else:
        graph = scanner.scan(force_full=args.full)
    
    if args.mermaid:
        print(scanner.export_mermaid_diagram(graph))
        return
    
    if args.stats:
        print(json.dumps(graph.statistics, indent=2))
        return
    
    if args.issues:
        print(json.dumps(graph.issues, indent=2))
        return
    
    output = scanner.export_graph(graph, args.output, args.format)
    
    if args.output:
        print(f"Report saved to {args.output}")
    else:
        print(output)
    
    scanner.close()


if __name__ == "__main__":
    main()