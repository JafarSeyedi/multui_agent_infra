#!/usr/bin/env python3
"""
Import Graph Analyzer - AI Development Framework
Analyzes and visualizes Python import relationships and dependencies.

Part of the Level 2 Analysis tools (scanners/import_graph.py)

This import_graph.py provides:

1. Complete Import Graph - All import relationships between modules
2. Import Type Detection - Direct, from, relative, star, conditional, dynamic, type checking
3. Circular Dependency Detection - Finds and reports import cycles
4. Unused Import Detection - Identifies potentially unused imports
5. Dead Module Detection - Finds modules never imported
6. Layering Analysis - Assigns architectural layers based on dependencies
7. Fan-in/Fan-out Metrics - Measures coupling and cohesion
8. External Dependency Tracking - Tracks third-party package usage
9. Path Finding - Finds import paths between modules
10. Multiple Export Formats - JSON, DOT, Mermaid, GraphML, GEXF
11. Comprehensive Reporting - Markdown reports with insights
12. NetworkX Integration - Advanced graph algorithms

The import graph analyzer provides deep insights into your project's dependency structure, helping identify architectural issues and optimization opportunities.

"""

import ast
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict, deque

import networkx as nx

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager
from .project_scanner import ProjectScanner, ProjectGraph, ScanConfig, ScanLevel

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
    CONDITIONAL = "conditional" # import inside if/except
    DYNAMIC = "dynamic"         # __import__ or importlib
    TYPE_CHECKING = "type_checking"  # from typing import TYPE_CHECKING
    LAZY = "lazy"               # lazy import patterns


class DependencyType(str, Enum):
    """Type of dependency between modules."""
    DIRECT = "direct"
    TRANSITIVE = "transitive"
    CIRCULAR = "circular"
    OPTIONAL = "optional"
    DEV = "dev"
    EXTERNAL = "external"
    INTERNAL = "internal"
    UNUSED = "unused"


class GraphFormat(str, Enum):
    """Export format for graph."""
    JSON = "json"
    DOT = "dot"
    MERMAID = "mermaid"
    GRAPHML = "graphml"
    GEXF = "gexf"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ImportEdge:
    """Represents an import relationship."""
    source: str
    target: str
    import_type: ImportType
    line_number: Optional[int] = None
    alias: Optional[str] = None
    imported_names: List[str] = field(default_factory=list)
    is_conditional: bool = False
    is_dynamic: bool = False
    is_type_only: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def id(self) -> str:
        return f"{self.source}->{self.target}"


@dataclass
class ModuleNode:
    """Represents a module in the import graph."""
    name: str
    path: str
    package: str
    is_package: bool = False
    is_external: bool = False
    is_stdlib: bool = False
    imports: List[ImportEdge] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)
    fan_in: int = 0
    fan_out: int = 0
    layer: int = 0
    is_circular: bool = False
    is_dead: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportGraphConfig:
    """Configuration for import graph analysis."""
    project_root: Path
    include_external: bool = True
    include_stdlib: bool = False
    include_tests: bool = True
    include_type_checking: bool = False
    resolve_aliases: bool = True
    detect_circular: bool = True
    detect_unused: bool = True
    detect_layering: bool = True
    compute_metrics: bool = True
    max_depth: int = 10
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__/*", "*.pyc", ".git/*", ".venv/*", "venv/*",
        "dist/*", "build/*", "*.egg-info/*", ".pytest_cache/*"
    ])


@dataclass
class ImportGraph:
    """Complete import graph analysis."""
    project_root: str
    analyzed_at: datetime
    nodes: Dict[str, ModuleNode] = field(default_factory=dict)
    edges: List[ImportEdge] = field(default_factory=list)
    packages: Dict[str, List[str]] = field(default_factory=dict)
    layers: Dict[int, List[str]] = field(default_factory=dict)
    circular_deps: List[List[str]] = field(default_factory=list)
    unused_imports: List[ImportEdge] = field(default_factory=list)
    dead_modules: List[str] = field(default_factory=list)
    external_deps: Dict[str, List[str]] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# AST IMPORT EXTRACTOR
# ============================================================

class ImportExtractor(ast.NodeVisitor):
    """Extract all import statements from Python AST."""
    
    def __init__(self, module_name: str, config: ImportGraphConfig):
        self.module_name = module_name
        self.config = config
        self.imports: List[ImportEdge] = []
        self.in_type_checking = False
        self.in_conditional = False
    
    def visit_Import(self, node: ast.Import):
        """Visit direct import."""
        for alias in node.names:
            edge = ImportEdge(
                source=self.module_name,
                target=alias.name,
                import_type=ImportType.DIRECT,
                line_number=node.lineno,
                alias=alias.asname,
                is_conditional=self.in_conditional
            )
            self.imports.append(edge)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from import."""
        if node.module is None:
            return
        
        # Handle relative imports
        if node.level > 0:
            import_type = ImportType.RELATIVE
            target = self._resolve_relative_import(node.module, node.level)
        else:
            import_type = ImportType.FROM
            target = node.module
        
        # Check for star import
        if any(alias.name == '*' for alias in node.names):
            import_type = ImportType.STAR
        
        edge = ImportEdge(
            source=self.module_name,
            target=target,
            import_type=import_type,
            line_number=node.lineno,
            imported_names=[alias.name for alias in node.names],
            is_conditional=self.in_conditional
        )
        
        # Check for type checking imports
        if self.in_type_checking:
            edge.is_type_only = True
            edge.metadata['type_checking'] = True
        
        self.imports.append(edge)
    
    def visit_If(self, node: ast.IF):
        """Track conditional imports."""
        # Check if this is a TYPE_CHECKING block
        if self._is_type_checking_block(node):
            self.in_type_checking = True
            self.generic_visit(node)
            self.in_type_checking = False
        else:
            prev_conditional = self.in_conditional
            self.in_conditional = True
            self.generic_visit(node)
            self.in_conditional = prev_conditional
    
    def visit_Try(self, node: ast.Try):
        """Track conditional imports in try blocks."""
        prev_conditional = self.in_conditional
        self.in_conditional = True
        self.generic_visit(node)
        self.in_conditional = prev_conditional
    
    def visit_Call(self, node: ast.Call):
        """Detect dynamic imports."""
        if isinstance(node.func, ast.Name) and node.func.id == '__import__':
            if node.args:
                target = self._get_string_value(node.args[0])
                if target:
                    edge = ImportEdge(
                        source=self.module_name,
                        target=target,
                        import_type=ImportType.DYNAMIC,
                        line_number=node.lineno,
                        is_dynamic=True
                    )
                    self.imports.append(edge)
        
        # Check for importlib.import_module
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'import_module':
                if node.args:
                    target = self._get_string_value(node.args[0])
                    if target:
                        edge = ImportEdge(
                            source=self.module_name,
                            target=target,
                            import_type=ImportType.DYNAMIC,
                            line_number=node.lineno,
                            is_dynamic=True
                        )
                        self.imports.append(edge)
        
        self.generic_visit(node)
    
    def _resolve_relative_import(self, module: str, level: int) -> str:
        """Resolve relative import to absolute module name."""
        parts = self.module_name.split('.')
        
        if level > len(parts):
            return module
        
        base_parts = parts[:-level] if level > 0 else parts
        if module:
            return '.'.join(base_parts + [module])
        return '.'.join(base_parts)
    
    def _is_type_checking_block(self, node: ast.If) -> bool:
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
        if isinstance(node, ast.Str):  # Python 3.7
            return node.s
        return None


# ============================================================
# MAIN IMPORT GRAPH ANALYZER
# ============================================================

class ImportGraphAnalyzer:
    """
    Analyzes Python import relationships and dependencies.
    
    Features:
    - Complete import graph construction
    - Circular dependency detection
    - Unused import identification
    - Layering analysis
    - Dead module detection
    - Fan-in/fan-out metrics
    - External dependency tracking
    - Multiple export formats (JSON, DOT, Mermaid, GraphML)
    - Visualization generation
    - Incremental updates
    """
    
    # Standard library modules (Python 3.11)
    STD_LIB_MODULES: Set[str] = {
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
    
    def __init__(self, config: ImportGraphConfig):
        self.config = config
        self.state = StateManager(config.project_root / ".ai_state" / "import_graph.json")
        
        # Graph data
        self.graph = ImportGraph(
            project_root=str(config.project_root),
            analyzed_at=datetime.now()
        )
        
        # NetworkX graph for advanced analysis
        self._nx_graph: Optional[nx.DiGraph] = None
        
        # Caches
        self._module_to_file: Dict[str, Path] = {}
        self._alias_map: Dict[str, str] = {}
        
        logger.info(f"ImportGraphAnalyzer initialized for {config.project_root}")
    
    # ============================================================
    # GRAPH CONSTRUCTION
    # ============================================================
    
    def analyze(self, project_graph: Optional[ProjectGraph] = None) -> ImportGraph:
        """
        Analyze import relationships.
        
        Args:
            project_graph: Optional pre-scanned project graph
        """
        start_time = datetime.now()
        logger.info("Starting import graph analysis")
        
        # Get modules to analyze
        if project_graph:
            modules = list(project_graph.modules.keys())
        else:
            modules = self._find_python_modules()
        
        logger.info(f"Analyzing {len(modules)} modules")
        
        # Build module nodes
        for module_name in modules:
            self._add_module_node(module_name)
        
        # Extract imports
        for module_name in modules:
            self._extract_module_imports(module_name)
        
        # Build package structure
        self._build_package_structure()
        
        # Compute metrics
        if self.config.compute_metrics:
            self._compute_metrics()
        
        # Detect issues
        if self.config.detect_circular:
            self._detect_circular_dependencies()
        
        if self.config.detect_unused:
            self._detect_unused_imports()
        
        if self.config.detect_layering:
            self._analyze_layering()
        
        self._detect_dead_modules()
        
        # Build NetworkX graph
        self._build_nx_graph()
        
        analysis_duration = (datetime.now() - start_time).total_seconds()
        self.graph.metadata['analysis_duration'] = analysis_duration
        
        logger.info(f"Analysis complete: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges in {analysis_duration:.1f}s")
        
        return self.graph
    
    def _find_python_modules(self) -> List[str]:
        """Find all Python modules in project."""
        modules = []
        
        for file_path in self.config.project_root.rglob("*.py"):
            if self._should_include_file(file_path):
                module_name = self._get_module_name(file_path)
                if module_name:
                    modules.append(module_name)
                    self._module_to_file[module_name] = file_path
        
        return modules
    
    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included."""
        import fnmatch
        
        rel_path = str(file_path.relative_to(self.config.project_root))
        
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return False
        
        # Skip tests if configured
        if not self.config.include_tests and 'test' in rel_path.lower():
            return False
        
        return True
    
    def _get_module_name(self, file_path: Path) -> Optional[str]:
        """Get Python module name from file path."""
        try:
            rel_path = file_path.relative_to(self.config.project_root)
        except ValueError:
            return None
        
        parts = list(rel_path.parts)
        
        if parts[-1] == '__init__.py':
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].replace('.py', '')
        
        if not parts:
            return None
        
        return '.'.join(parts)
    
    def _add_module_node(self, module_name: str):
        """Add a module node to the graph."""
        if module_name in self.graph.nodes:
            return
        
        # Check if external/stdlib
        root_pkg = module_name.split('.')[0]
        is_stdlib = root_pkg in self.STD_LIB_MODULES
        is_external = not is_stdlib and not self._is_internal_module(module_name)
        
        file_path = self._module_to_file.get(module_name)
        
        node = ModuleNode(
            name=module_name,
            path=str(file_path) if file_path else "",
            package='.'.join(module_name.split('.')[:-1]),
            is_package=file_path.name == '__init__.py' if file_path else False,
            is_external=is_external,
            is_stdlib=is_stdlib
        )
        
        self.graph.nodes[module_name] = node
    
    def _is_internal_module(self, module_name: str) -> bool:
        """Check if module is part of the project."""
        return module_name in self._module_to_file
    
    def _extract_module_imports(self, module_name: str):
        """Extract imports from a module."""
        file_path = self._module_to_file.get(module_name)
        if not file_path or not file_path.exists():
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            extractor = ImportExtractor(module_name, self.config)
            extractor.visit(tree)
            
            for edge in extractor.imports:
                self._add_import_edge(edge)
                
        except Exception as e:
            logger.warning(f"Failed to extract imports from {module_name}: {e}")
    
    def _add_import_edge(self, edge: ImportEdge):
        """Add an import edge to the graph."""
        # Resolve alias
        if self.config.resolve_aliases and edge.alias:
            self._alias_map[f"{edge.source}.{edge.alias}"] = edge.target
        
        # Check if target should be included
        if not self._should_include_target(edge.target):
            return
        
        # Add target node if needed
        if edge.target not in self.graph.nodes:
            self._add_module_node(edge.target)
        
        # Filter by type
        if not self.config.include_type_checking and edge.is_type_only:
            return
        
        if not self.config.include_external and self.graph.nodes[edge.target].is_external:
            return
        
        if not self.config.include_stdlib and self.graph.nodes[edge.target].is_stdlib:
            return
        
        # Add edge
        self.graph.edges.append(edge)
        
        # Update node relationships
        source_node = self.graph.nodes[edge.source]
        target_node = self.graph.nodes[edge.target]
        
        source_node.imports.append(edge)
        target_node.imported_by.append(edge.source)
        
        # Track external dependencies
        if target_node.is_external:
            root_pkg = edge.target.split('.')[0]
            if root_pkg not in self.graph.external_deps:
                self.graph.external_deps[root_pkg] = []
            if edge.source not in self.graph.external_deps[root_pkg]:
                self.graph.external_deps[root_pkg].append(edge.source)
    
    def _should_include_target(self, target: str) -> bool:
        """Check if import target should be included."""
        if not target:
            return False
        
        # Always include if configured
        return True
    
    def _build_package_structure(self):
        """Build package structure from modules."""
        for module_name in self.graph.nodes:
            parts = module_name.split('.')
            
            for i in range(1, len(parts)):
                pkg_name = '.'.join(parts[:i])
                if pkg_name not in self.graph.packages:
                    self.graph.packages[pkg_name] = []
                if module_name not in self.graph.packages[pkg_name]:
                    self.graph.packages[pkg_name].append(module_name)
    
    # ============================================================
    # METRICS AND ANALYSIS
    # ============================================================
    
    def _compute_metrics(self):
        """Compute graph metrics."""
        # Fan-in and fan-out
        for node in self.graph.nodes.values():
            node.fan_in = len(node.imported_by)
            node.fan_out = len(node.imports)
        
        # Overall metrics
        internal_nodes = [n for n in self.graph.nodes.values() if not n.is_external]
        
        if internal_nodes:
            avg_fan_in = sum(n.fan_in for n in internal_nodes) / len(internal_nodes)
            avg_fan_out = sum(n.fan_out for n in internal_nodes) / len(internal_nodes)
        else:
            avg_fan_in = avg_fan_out = 0
        
        # Most depended upon
        most_depended = sorted(
            [(n.name, n.fan_in) for n in internal_nodes],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Most dependencies
        most_dependencies = sorted(
            [(n.name, n.fan_out) for n in internal_nodes],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        self.graph.metrics = {
            'total_nodes': len(self.graph.nodes),
            'internal_nodes': len(internal_nodes),
            'external_nodes': sum(1 for n in self.graph.nodes.values() if n.is_external),
            'stdlib_nodes': sum(1 for n in self.graph.nodes.values() if n.is_stdlib),
            'total_edges': len(self.graph.edges),
            'avg_fan_in': round(avg_fan_in, 2),
            'avg_fan_out': round(avg_fan_out, 2),
            'most_depended_upon': most_depended,
            'most_dependencies': most_dependencies,
            'packages': len(self.graph.packages),
            'external_packages': len(self.graph.external_deps)
        }
    
    def _detect_circular_dependencies(self):
        """Detect circular import dependencies."""
        # Build adjacency list
        adj = defaultdict(list)
        for edge in self.graph.edges:
            if not self.graph.nodes[edge.target].is_external:
                adj[edge.source].append(edge.target)
        
        # Find cycles using DFS
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in adj[node]:
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in adj:
            if node not in visited:
                dfs(node, [])
        
        # Mark circular nodes
        for cycle in cycles:
            self.graph.circular_deps.append(cycle)
            for node_name in cycle[:-1]:  # Last is duplicate of first
                if node_name in self.graph.nodes:
                    self.graph.nodes[node_name].is_circular = True
        
        logger.info(f"Detected {len(cycles)} circular dependencies")
    
    def _detect_unused_imports(self):
        """Detect potentially unused imports."""
        # This requires more advanced analysis (variable usage)
        # Simple heuristic: imports that are never referenced by others
        for node in self.graph.nodes.values():
            if node.is_external or node.is_stdlib:
                continue
            
            if node.fan_in == 0 and node.name not in ['__main__']:
                # Check if it's a leaf with no incoming edges
                is_dead = True
                for edge in self.graph.edges:
                    if edge.target == node.name:
                        is_dead = False
                        break
                
                if is_dead:
                    for edge in node.imports:
                        self.graph.unused_imports.append(edge)
        
        logger.info(f"Detected {len(self.graph.unused_imports)} potentially unused imports")
    
    def _analyze_layering(self):
        """Analyze architectural layering."""
        # Assign layers based on dependencies
        # Layer 0: No dependencies on other internal modules
        # Layer N: Depends on modules from layer N-1
        
        # Build internal dependency graph
        internal_deps = defaultdict(set)
        for edge in self.graph.edges:
            source = edge.source
            target = edge.target
            
            if (source in self.graph.nodes and target in self.graph.nodes and
                not self.graph.nodes[target].is_external):
                internal_deps[source].add(target)
        
        # Topological layering
        layers: Dict[int, List[str]] = {}
        remaining = set(internal_deps.keys())
        
        layer_num = 0
        while remaining:
            # Find nodes with no remaining dependencies
            layer_nodes = {
                node for node in remaining
                if not (internal_deps[node] & remaining)
            }
            
            if not layer_nodes:
                # Circular dependency detected
                break
            
            layers[layer_num] = list(layer_nodes)
            for node in layer_nodes:
                if node in self.graph.nodes:
                    self.graph.nodes[node].layer = layer_num
            
            remaining -= layer_nodes
            layer_num += 1
        
        self.graph.layers = layers
        
        logger.info(f"Identified {len(layers)} architectural layers")
    
    def _detect_dead_modules(self):
        """Detect modules that are never imported."""
        for node in self.graph.nodes.values():
            if node.is_external or node.is_stdlib:
                continue
            
            if node.name == '__main__':
                continue
            
            if node.fan_in == 0 and node.name not in [e.source for e in self.graph.edges if e.target == '__main__']:
                node.is_dead = True
                self.graph.dead_modules.append(node.name)
        
        logger.info(f"Detected {len(self.graph.dead_modules)} potentially dead modules")
    
    def _build_nx_graph(self):
        """Build NetworkX graph for advanced analysis."""
        self._nx_graph = nx.DiGraph()
        
        for node_name, node in self.graph.nodes.items():
            if not node.is_external or self.config.include_external:
                self._nx_graph.add_node(
                    node_name,
                    is_external=node.is_external,
                    is_stdlib=node.is_stdlib,
                    layer=node.layer,
                    fan_in=node.fan_in,
                    fan_out=node.fan_out
                )
        
        for edge in self.graph.edges:
            if edge.source in self._nx_graph and edge.target in self._nx_graph:
                self._nx_graph.add_edge(
                    edge.source,
                    edge.target,
                    import_type=edge.import_type.value
                )
    
    # ============================================================
    # QUERY METHODS
    # ============================================================
    
    def get_dependencies(self, module_name: str, max_depth: int = 3) -> List[str]:
        """Get all dependencies of a module."""
        if module_name not in self.graph.nodes:
            return []
        
        deps = set()
        queue = deque([(module_name, 0)])
        visited = {module_name}
        
        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            
            node = self.graph.nodes.get(current)
            if node:
                for edge in node.imports:
                    if edge.target not in visited:
                        deps.add(edge.target)
                        visited.add(edge.target)
                        queue.append((edge.target, depth + 1))
        
        return list(deps)
    
    def get_dependents(self, module_name: str, max_depth: int = 3) -> List[str]:
        """Get all modules that depend on this module."""
        if module_name not in self.graph.nodes:
            return []
        
        deps = set()
        queue = deque([(module_name, 0)])
        visited = {module_name}
        
        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            
            node = self.graph.nodes.get(current)
            if node:
                for depender in node.imported_by:
                    if depender not in visited:
                        deps.add(depender)
                        visited.add(depender)
                        queue.append((depender, depth + 1))
        
        return list(deps)
    
    def find_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find import path between two modules."""
        if not self._nx_graph:
            self._build_nx_graph()
        
        if source not in self._nx_graph or target not in self._nx_graph:
            return None
        
        try:
            path = nx.shortest_path(self._nx_graph, source, target)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def get_import_chain(self, module_name: str) -> List[ImportEdge]:
        """Get the full import chain for a module."""
        return [e for e in self.graph.edges if e.source == module_name]
    
    def get_external_dependencies(self) -> Dict[str, int]:
        """Get external dependency counts."""
        return {
            pkg: len(modules)
            for pkg, modules in self.graph.external_deps.items()
        }
    
    def get_circular_dependencies(self) -> List[List[str]]:
        """Get all circular dependencies."""
        return self.graph.circular_deps
    
    def get_unused_imports(self) -> List[ImportEdge]:
        """Get potentially unused imports."""
        return self.graph.unused_imports
    
    def get_dead_modules(self) -> List[str]:
        """Get potentially dead modules."""
        return self.graph.dead_modules
    
    def get_module_info(self, module_name: str) -> Optional[ModuleNode]:
        """Get detailed module information."""
        return self.graph.nodes.get(module_name)
    
    # ============================================================
    # EXPORT AND VISUALIZATION
    # ============================================================
    
    def export(self, format: GraphFormat = GraphFormat.JSON, output_path: Optional[Path] = None) -> Union[str, Path]:
        """Export graph in various formats."""
        if format == GraphFormat.JSON:
            return self._export_json(output_path)
        elif format == GraphFormat.DOT:
            return self._export_dot(output_path)
        elif format == GraphFormat.MERMAID:
            return self._export_mermaid(output_path)
        elif format == GraphFormat.GRAPHML:
            return self._export_graphml(output_path)
        elif format == GraphFormat.GEXF:
            return self._export_gexf(output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self, output_path: Optional[Path] = None) -> Union[str, Path]:
        """Export as JSON."""
        data = {
            'project_root': self.graph.project_root,
            'analyzed_at': self.graph.analyzed_at.isoformat(),
            'metrics': self.graph.metrics,
            'nodes': {
                name: {
                    'path': node.path,
                    'package': node.package,
                    'is_package': node.is_package,
                    'is_external': node.is_external,
                    'is_stdlib': node.is_stdlib,
                    'fan_in': node.fan_in,
                    'fan_out': node.fan_out,
                    'layer': node.layer,
                    'is_circular': node.is_circular,
                    'is_dead': node.is_dead
                }
                for name, node in self.graph.nodes.items()
                if not node.is_external or self.config.include_external
            },
            'edges': [
                {
                    'source': e.source,
                    'target': e.target,
                    'type': e.import_type.value,
                    'line': e.line_number,
                    'is_conditional': e.is_conditional,
                    'is_type_only': e.is_type_only
                }
                for e in self.graph.edges
            ],
            'circular_deps': self.graph.circular_deps,
            'external_deps': self.graph.external_deps,
            'layers': self.graph.layers
        }
        
        content = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(content)
            return output_path
        return content
    
    def _export_dot(self, output_path: Optional[Path] = None) -> Union[str, Path]:
        """Export as Graphviz DOT format."""
        lines = ['digraph ImportGraph {']
        lines.append('    rankdir=TB;')
        lines.append('    node [shape=box, style=filled];')
        
        # Add nodes
        for name, node in self.graph.nodes.items():
            if node.is_external and not self.config.include_external:
                continue
            
            if node.is_stdlib:
                color = 'lightblue'
            elif node.is_external:
                color = 'lightcoral'
            elif node.is_circular:
                color = 'orange'
            elif node.is_dead:
                color = 'gray'
            else:
                color = 'lightgreen'
            
            label = name.split('.')[-1]
            lines.append(f'    "{name}" [label="{label}", fillcolor={color}];')
        
        # Add edges
        for edge in self.graph.edges:
            if edge.source in self.graph.nodes and edge.target in self.graph.nodes:
                style = 'dashed' if edge.is_conditional else 'solid'
                color = 'blue' if edge.is_type_only else 'black'
                lines.append(f'    "{edge.source}" -> "{edge.target}" [style={style}, color={color}];')
        
        lines.append('}')
        content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
            return output_path
        return content
    
    def _export_mermaid(self, output_path: Optional[Path] = None, max_nodes: int = 50) -> Union[str, Path]:
        """Export as Mermaid diagram."""
        lines = ['```mermaid', 'graph TD']
        
        # Select top nodes by importance
        node_scores = {
            name: node.fan_in + node.fan_out
            for name, node in self.graph.nodes.items()
            if not node.is_external
        }
        top_nodes = sorted(node_scores, key=node_scores.get, reverse=True)[:max_nodes]
        
        # Add nodes
        for name in top_nodes:
            short_name = name.split('.')[-1]
            lines.append(f'    {self._sanitize_mermaid(name)}["{short_name}"]')
        
        # Add edges
        for edge in self.graph.edges:
            if edge.source in top_nodes and edge.target in top_nodes:
                lines.append(f'    {self._sanitize_mermaid(edge.source)} --> {self._sanitize_mermaid(edge.target)}')
        
        lines.append('```')
        content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
            return output_path
        return content
    
    def _sanitize_mermaid(self, name: str) -> str:
        """Sanitize name for Mermaid."""
        return name.replace('.', '_').replace('-', '_')
    
    def _export_graphml(self, output_path: Path) -> Path:
        """Export as GraphML."""
        if not self._nx_graph:
            self._build_nx_graph()
        
        nx.write_graphml(self._nx_graph, str(output_path))
        return output_path
    
    def _export_gexf(self, output_path: Path) -> Path:
        """Export as GEXF."""
        if not self._nx_graph:
            self._build_nx_graph()
        
        nx.write_gexf(self._nx_graph, str(output_path))
        return output_path
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report."""
        lines = [
            "# Import Graph Analysis Report",
            "",
            f"**Project:** {self.graph.project_root}",
            f"**Analyzed:** {self.graph.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- **Total Modules:** {self.graph.metrics.get('total_nodes', 0)}",
            f"- **Internal Modules:** {self.graph.metrics.get('internal_nodes', 0)}",
            f"- **External Dependencies:** {self.graph.metrics.get('external_nodes', 0)}",
            f"- **Total Imports:** {self.graph.metrics.get('total_edges', 0)}",
            f"- **Average Fan-In:** {self.graph.metrics.get('avg_fan_in', 0)}",
            f"- **Average Fan-Out:** {self.graph.metrics.get('avg_fan_out', 0)}",
            f"- **Circular Dependencies:** {len(self.graph.circular_deps)}",
            f"- **Dead Modules:** {len(self.graph.dead_modules)}",
            "",
            "## Most Depended Upon Modules",
            "",
            "| Module | Fan-In |",
            "|--------|--------|",
        ]
        
        for name, count in self.graph.metrics.get('most_depended_upon', [])[:10]:
            lines.append(f"| {name} | {count} |")
        
        lines.extend([
            "",
            "## Modules with Most Dependencies",
            "",
            "| Module | Fan-Out |",
            "|--------|---------|",
        ])
        
        for name, count in self.graph.metrics.get('most_dependencies', [])[:10]:
            lines.append(f"| {name} | {count} |")
        
        if self.graph.circular_deps:
            lines.extend([
                "",
                "## Circular Dependencies",
                "",
            ])
            for i, cycle in enumerate(self.graph.circular_deps[:5], 1):
                lines.append(f"{i}. {' -> '.join(cycle)}")
        
        if self.graph.external_deps:
            lines.extend([
                "",
                "## External Dependencies",
                "",
                "| Package | Used By |",
                "|---------|---------|",
            ])
            
            sorted_deps = sorted(
                self.graph.external_deps.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            for pkg, modules in sorted_deps[:20]:
                lines.append(f"| {pkg} | {len(modules)} |")
        
        return '\n'.join(lines)
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("ImportGraphAnalyzer closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for import graph analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze Python import relationships")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    parser.add_argument("--output", "-o", type=Path, help="Output file")
    parser.add_argument("--format", choices=[f.value for f in GraphFormat],
                       default=GraphFormat.JSON.value, help="Output format")
    parser.add_argument("--include-external", action="store_true",
                       help="Include external dependencies")
    parser.add_argument("--include-stdlib", action="store_true",
                       help="Include standard library")
    parser.add_argument("--no-tests", action="store_true",
                       help="Exclude test files")
    parser.add_argument("--report", action="store_true",
                       help="Generate markdown report")
    parser.add_argument("--circular", action="store_true",
                       help="Show circular dependencies only")
    parser.add_argument("--unused", action="store_true",
                       help="Show unused imports only")
    parser.add_argument("--dead", action="store_true",
                       help="Show dead modules only")
    parser.add_argument("--deps", type=str, help="Show dependencies for module")
    parser.add_argument("--dependents", type=str, help="Show dependents for module")
    parser.add_argument("--path", nargs=2, metavar=('SOURCE', 'TARGET'),
                       help="Find path between two modules")
    parser.add_argument("--max-depth", type=int, default=3,
                       help="Maximum depth for dependency traversal")
    
    args = parser.parse_args()
    
    config = ImportGraphConfig(
        project_root=args.project_root,
        include_external=args.include_external,
        include_stdlib=args.include_stdlib,
        include_tests=not args.no_tests
    )
    
    analyzer = ImportGraphAnalyzer(config)
    graph = analyzer.analyze()
    
    if args.report:
        print(analyzer.generate_report())
        return
    
    if args.circular:
        cycles = analyzer.get_circular_dependencies()
        if cycles:
            print(f"\nCircular Dependencies ({len(cycles)}):\n")
            for i, cycle in enumerate(cycles, 1):
                print(f"{i}. {' -> '.join(cycle)}")
        else:
            print("No circular dependencies found")
        return
    
    if args.unused:
        unused = analyzer.get_unused_imports()
        if unused:
            print(f"\nPotentially Unused Imports ({len(unused)}):\n")
            for edge in unused[:20]:
                print(f"  {edge.source} imports {edge.target} (line {edge.line_number})")
        else:
            print("No unused imports found")
        return
    
    if args.dead:
        dead = analyzer.get_dead_modules()
        if dead:
            print(f"\nPotentially Dead Modules ({len(dead)}):\n")
            for module in dead:
                print(f"  {module}")
        else:
            print("No dead modules found")
        return
    
    if args.deps:
        deps = analyzer.get_dependencies(args.deps, args.max_depth)
        print(f"\nDependencies of '{args.deps}' (max depth {args.max_depth}):\n")
        for dep in sorted(deps):
            node = analyzer.get_module_info(dep)
            if node:
                tag = "[ext]" if node.is_external else "[stdlib]" if node.is_stdlib else ""
                print(f"  {dep} {tag}")
        return
    
    if args.dependents:
        deps = analyzer.get_dependents(args.dependents, args.max_depth)
        print(f"\nModules depending on '{args.dependents}' (max depth {args.max_depth}):\n")
        for dep in sorted(deps):
            print(f"  {dep}")
        return
    
    if args.path:
        path = analyzer.find_path(args.path[0], args.path[1])
        if path:
            print(f"\nPath from '{args.path[0]}' to '{args.path[1]}':")
            print("  " + " -> ".join(path))
        else:
            print(f"No path found from '{args.path[0]}' to '{args.path[1]}'")
        return
    
    # Default: export graph
    output = analyzer.export(GraphFormat(args.format), args.output)
    
    if args.output:
        print(f"Graph exported to {args.output}")
    else:
        print(output)
    
    analyzer.close()


if __name__ == "__main__":
    main()