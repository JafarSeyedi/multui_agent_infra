#!/usr/bin/env python3
"""
Dependency Analyzer - AI Development Framework
Analyzes module dependencies, detects issues, and suggests optimizations.

Part of the Level 1 Planning tools (dependency_analyzer.py)

This dependency_analyzer.py provides:

1. Complete Dependency Graph Building - From project scan or pre-scanned graph
2. Metrics Calculation - Fan-in, fan-out, instability, abstractness, distance from main sequence
3. Issue Detection - Circular dependencies, tight coupling, god modules, layer violations
4. Layering Analysis - Automatic layer assignment with refinement
5. Optimization Suggestions - Prioritized, actionable recommendations
6. Visualization - Mermaid diagrams and ASCII trees
7. Multiple Report Formats - Markdown, JSON, HTML
8. AI-Powered Analysis - Get LLM-generated optimization plans
9. Export/Persistence - Save graphs and reports for tracking

The tool integrates with ProjectScanner output and provides a foundation for architectural governance.
"""

import ast
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, DefaultDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import networkx as nx

from ..shared.llm_client import LLMClient
from ..shared.state_manager import StateManager
from ..shared.logger import get_logger

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class DependencyType(str, Enum):
    """Type of dependency between modules."""
    DIRECT_IMPORT = "direct_import"
    RELATIVE_IMPORT = "relative_import"
    TYPE_CHECKING = "type_checking"
    LAZY_IMPORT = "lazy_import"
    CIRCULAR = "circular"
    CONDITIONAL = "conditional"
    DYNAMIC = "dynamic"


class Severity(str, Enum):
    """Severity of dependency issue."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(str, Enum):
    """Type of dependency issue."""
    CIRCULAR_DEPENDENCY = "circular_dependency"
    TIGHT_COUPLING = "tight_coupling"
    UNUSED_IMPORT = "unused_import"
    WILDCARD_IMPORT = "wildcard_import"
    DEEP_IMPORT_CHAIN = "deep_import_chain"
    GOD_MODULE = "god_module"
    IMPROPER_LAYERING = "improper_layering"
    MISSING_ABSTRACTION = "missing_abstraction"
    TRANSITIVE_DEPENDENCY = "transitive_dependency"
    CYCLE_WITH_EXCEPTION = "cycle_with_exception"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class DependencyEdge:
    """Represents a dependency between two modules."""
    source: str
    target: str
    dep_type: DependencyType
    line_number: Optional[int] = None
    import_statement: Optional[str] = None
    is_type_only: bool = False
    is_lazy: bool = False
    is_conditional: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModuleMetrics:
    """Metrics for a single module."""
    name: str
    lines_of_code: int = 0
    number_of_classes: int = 0
    number_of_functions: int = 0
    number_of_imports: int = 0
    fan_in: int = 0  # Number of modules that depend on this
    fan_out: int = 0  # Number of modules this depends on
    instability: float = 0.0  # I = fan_out / (fan_in + fan_out)
    abstractness: float = 0.0  # A = abstract_classes / total_classes
    distance_from_main_sequence: float = 0.0  # D = |A + I - 1|
    dependencies: List[DependencyEdge] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)


@dataclass
class DependencyIssue:
    """Represents a dependency-related issue."""
    issue_type: IssueType
    severity: Severity
    description: str
    affected_modules: List[str]
    suggestion: str
    auto_fixable: bool = False
    fix_description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyGraph:
    """Complete dependency graph for the project."""
    modules: Dict[str, ModuleMetrics] = field(default_factory=dict)
    edges: List[DependencyEdge] = field(default_factory=list)
    packages: Dict[str, List[str]] = field(default_factory=dict)
    layers: Dict[str, int] = field(default_factory=dict)  # module -> layer index
    issues: List[DependencyIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationSuggestion:
    """Suggestion for dependency optimization."""
    title: str
    description: str
    impact: Severity
    effort: str  # 'low', 'medium', 'high'
    steps: List[str]
    affected_modules: List[str]
    estimated_time_saved: Optional[str] = None


# ============================================================
# MAIN ANALYZER CLASS
# ============================================================

class DependencyAnalyzer:
    """
    Comprehensive dependency analysis and optimization tool.
    
    Features:
    - Build complete dependency graph from project
    - Detect circular dependencies
    - Calculate instability and abstractness metrics
    - Identify architectural violations (layering)
    - Suggest dependency optimizations
    - Generate refactoring plans
    - Visualize dependency graphs
    - Track changes over time
    """
    
    # Known standard library modules
    STD_LIB_MODULES = {
        'os', 'sys', 'json', 're', 'pathlib', 'typing', 'datetime',
        'collections', 'itertools', 'functools', 'hashlib', 'uuid',
        'logging', 'subprocess', 'tempfile', 'shutil', 'glob', 'fnmatch',
        'math', 'random', 'statistics', 'decimal', 'fractions',
        'threading', 'multiprocessing', 'concurrent', 'asyncio',
        'socket', 'http', 'urllib', 'email', 'xml', 'html',
        'unittest', 'pytest', 'mock', 'dataclasses', 'enum', 'abc',
        'io', 'csv', 'configparser', 'argparse', 'getopt',
        'ast', 'tokenize', 'inspect', 'traceback', 'warnings',
        'typing_extensions', 'contextlib', 'time', 'signal',
        'copy', 'pickle', 'sqlite3', 'struct', 'array', 'queue',
    }
    
    # Common third-party modules
    COMMON_THIRD_PARTY = {
        'numpy', 'pandas', 'requests', 'pydantic', 'fastapi', 'flask',
        'django', 'sqlalchemy', 'alembic', 'celery', 'redis', 'pymongo',
        'pillow', 'opencv', 'tensorflow', 'torch', 'sklearn', 'matplotlib',
        'plotly', 'boto3', 'google.cloud', 'azure', 'kubernetes', 'docker',
        'lxml', 'beautifulsoup4', 'scrapy', 'aiohttp', 'websockets',
        'click', 'rich', 'tqdm', 'pyyaml', 'toml', 'marshmallow',
    }
    
    def __init__(self, project_root: Path, project_graph: Optional[Dict[str, Any]] = None):
        self.project_root = project_root
        self.project_graph = project_graph or {}
        self.llm = LLMClient()
        self.state = StateManager(project_root / ".ai_state" / "dependency_analyzer.json")
        
        self.graph = DependencyGraph()
        self._networkx_graph: Optional[nx.DiGraph] = None
        
        # Configuration
        self.max_circular_chain_display = 5
        self.instability_threshold = 0.7
        self.coupling_threshold = 10
    
    # ============================================================
    # GRAPH BUILDING
    # ============================================================
    
    def analyze(self, use_project_graph: bool = True) -> DependencyGraph:
        """
        Perform complete dependency analysis.
        
        Args:
            use_project_graph: Whether to use pre-scanned project graph
            
        Returns:
            Complete DependencyGraph with metrics and issues
        """
        logger.info("Starting dependency analysis...")
        
        if use_project_graph and self.project_graph:
            self._build_from_project_graph()
        else:
            self._scan_and_build()
        
        # Calculate metrics
        self._calculate_module_metrics()
        
        # Detect issues
        self._detect_circular_dependencies()
        self._detect_architectural_violations()
        self._detect_tight_coupling()
        self._detect_unused_imports()
        self._analyze_layering()
        
        # Calculate overall metrics
        self._calculate_overall_metrics()
        
        logger.info(f"Analysis complete: {len(self.graph.modules)} modules, {len(self.graph.edges)} dependencies, {len(self.graph.issues)} issues")
        
        return self.graph
    
    def _build_from_project_graph(self):
        """Build dependency graph from pre-scanned project graph."""
        modules_data = self.project_graph.get('modules', {})
        import_graph = self.project_graph.get('import_graph', {})
        
        for module_name, module_info in modules_data.items():
            metrics = ModuleMetrics(
                name=module_name,
                lines_of_code=module_info.get('lines_of_code', 0),
                number_of_classes=module_info.get('class_count', 0),
                number_of_functions=module_info.get('function_count', 0),
                number_of_imports=len(module_info.get('imports', []))
            )
            self.graph.modules[module_name] = metrics
            
            # Add to package grouping
            package = module_info.get('package', '')
            if package not in self.graph.packages:
                self.graph.packages[package] = []
            self.graph.packages[package].append(module_name)
        
        # Build edges from import graph
        for source, targets in import_graph.items():
            if source in self.graph.modules:
                for target in targets:
                    if target in self.graph.modules:
                        edge = DependencyEdge(
                            source=source,
                            target=target,
                            dep_type=DependencyType.DIRECT_IMPORT
                        )
                        self.graph.edges.append(edge)
                        self.graph.modules[source].dependencies.append(edge)
                        self.graph.modules[target].dependents.append(source)
    
    def _scan_and_build(self):
        """Scan project files and build dependency graph."""
        python_files = list(self.project_root.rglob("*.py"))
        
        # First pass: collect module info
        for file_path in python_files:
            if self._should_skip(file_path):
                continue
            
            module_name = self._get_module_name(file_path)
            if not module_name:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Extract metrics
                metrics = ModuleMetrics(
                    name=module_name,
                    lines_of_code=len([l for l in content.split('\n') if l.strip()]),
                    number_of_classes=len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                    number_of_functions=len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
                )
                self.graph.modules[module_name] = metrics
                
                # Extract package
                package = '.'.join(module_name.split('.')[:-1])
                if package not in self.graph.packages:
                    self.graph.packages[package] = []
                self.graph.packages[package].append(module_name)
                
                # Extract imports
                self._extract_imports(module_name, tree, file_path)
                
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Second pass: resolve dependencies
        self._resolve_dependencies()
    
    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            '__pycache__', '.git', '.venv', 'venv', 'env',
            'node_modules', 'dist', 'build', '.pytest_cache',
            '.mypy_cache', '.ruff_cache', '.ai_state'
        ]
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
    
    def _get_module_name(self, file_path: Path) -> Optional[str]:
        """Get fully qualified module name from file path."""
        try:
            rel_path = file_path.relative_to(self.project_root)
            parts = list(rel_path.parts)
            if parts[-1] == '__init__.py':
                parts = parts[:-1]
            else:
                parts[-1] = parts[-1].replace('.py', '')
            return '.'.join(parts)
        except ValueError:
            return None
    
    def _extract_imports(self, module_name: str, tree: ast.AST, file_path: Path):
        """Extract all imports from AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'name': alias.name,
                        'line': node.lineno,
                        'type': 'direct',
                        'asname': alias.asname
                    })
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append({
                        'name': node.module,
                        'line': node.lineno,
                        'type': 'from',
                        'level': node.level,
                        'names': [n.name for n in node.names]
                    })
        
        # Count imports
        self.graph.modules[module_name].number_of_imports = len(imports)
        
        # Store for later resolution
        self.graph.modules[module_name].metadata['raw_imports'] = imports
    
    def _resolve_dependencies(self):
        """Resolve module names to actual modules in project."""
        for module_name, metrics in self.graph.modules.items():
            raw_imports = metrics.metadata.get('raw_imports', [])
            
            for imp in raw_imports:
                target = self._resolve_import_target(module_name, imp)
                
                if target and target in self.graph.modules:
                    # Determine dependency type
                    dep_type = DependencyType.DIRECT_IMPORT
                    if imp.get('level', 0) > 0:
                        dep_type = DependencyType.RELATIVE_IMPORT
                    
                    edge = DependencyEdge(
                        source=module_name,
                        target=target,
                        dep_type=dep_type,
                        line_number=imp.get('line'),
                        import_statement=self._format_import_statement(imp)
                    )
                    
                    self.graph.edges.append(edge)
                    self.graph.modules[module_name].dependencies.append(edge)
                    self.graph.modules[target].dependents.append(module_name)
    
    def _resolve_import_target(self, source_module: str, imp: Dict[str, Any]) -> Optional[str]:
        """Resolve import to actual module name."""
        imp_name = imp['name']
        
        # Check if it's a standard library or third-party
        root_pkg = imp_name.split('.')[0]
        if root_pkg in self.STD_LIB_MODULES or root_pkg in self.COMMON_THIRD_PARTY:
            return None
        
        # Direct match
        if imp_name in self.graph.modules:
            return imp_name
        
        # Handle relative imports
        if imp.get('level', 0) > 0:
            source_parts = source_module.split('.')
            level = imp['level']
            
            if level <= len(source_parts):
                base_parts = source_parts[:-level] if level > 0 else source_parts
                if imp_name:
                    target = '.'.join(base_parts + [imp_name])
                else:
                    target = '.'.join(base_parts)
                
                if target in self.graph.modules:
                    return target
        
        # Try matching as submodule
        for module in self.graph.modules:
            if module.startswith(imp_name + '.'):
                return module
        
        # Try package-level import
        if imp_name in self.graph.packages:
            return imp_name
        
        return None
    
    def _format_import_statement(self, imp: Dict[str, Any]) -> str:
        """Format import dict as Python statement."""
        if imp['type'] == 'direct':
            if imp.get('asname'):
                return f"import {imp['name']} as {imp['asname']}"
            return f"import {imp['name']}"
        else:
            level = '.' * imp.get('level', 0)
            names = imp.get('names', [])
            if names:
                return f"from {level}{imp['name']} import {', '.join(names)}"
            return f"from {level}{imp['name']} import *"
    
    # ============================================================
    # METRICS CALCULATION
    # ============================================================
    
    def _calculate_module_metrics(self):
        """Calculate metrics for each module."""
        for module_name, metrics in self.graph.modules.items():
            # Fan-in and fan-out
            metrics.fan_in = len(metrics.dependents)
            metrics.fan_out = len(metrics.dependencies)
            
            # Instability (I = fan_out / (fan_in + fan_out))
            total = metrics.fan_in + metrics.fan_out
            metrics.instability = metrics.fan_out / total if total > 0 else 0.0
            
            # Abstractness (A = abstract_classes / total_classes)
            # Note: This requires deeper analysis - simplified here
            abstract_count = 0
            total_classes = metrics.number_of_classes
            if total_classes > 0:
                metrics.abstractness = abstract_count / total_classes
            
            # Distance from main sequence (D = |A + I - 1|)
            metrics.distance_from_main_sequence = abs(metrics.abstractness + metrics.instability - 1.0)
    
    def _calculate_overall_metrics(self):
        """Calculate overall project metrics."""
        total_modules = len(self.graph.modules)
        total_edges = len(self.graph.edges)
        
        # Average metrics
        avg_fan_in = sum(m.fan_in for m in self.graph.modules.values()) / max(total_modules, 1)
        avg_fan_out = sum(m.fan_out for m in self.graph.modules.values()) / max(total_modules, 1)
        avg_instability = sum(m.instability for m in self.graph.modules.values()) / max(total_modules, 1)
        
        # Identify most depended-on modules
        most_depended = sorted(
            self.graph.modules.items(),
            key=lambda x: x[1].fan_in,
            reverse=True
        )[:10]
        
        # Identify modules with most dependencies
        most_dependent = sorted(
            self.graph.modules.items(),
            key=lambda x: x[1].fan_out,
            reverse=True
        )[:10]
        
        self.graph.metrics = {
            'total_modules': total_modules,
            'total_edges': total_edges,
            'total_packages': len(self.graph.packages),
            'avg_fan_in': avg_fan_in,
            'avg_fan_out': avg_fan_out,
            'avg_instability': avg_instability,
            'most_depended_on': [{'name': n, 'fan_in': m.fan_in} for n, m in most_depended],
            'most_dependencies': [{'name': n, 'fan_out': m.fan_out} for n, m in most_dependent],
            'density': total_edges / (total_modules * (total_modules - 1)) if total_modules > 1 else 0
        }
    
    # ============================================================
    # ISSUE DETECTION
    # ============================================================
    
    def _detect_circular_dependencies(self):
        """Detect circular dependencies in the graph."""
        # Build NetworkX graph for cycle detection
        G = nx.DiGraph()
        for edge in self.graph.edges:
            G.add_edge(edge.source, edge.target)
        
        self._networkx_graph = G
        
        # Find all cycles
        try:
            cycles = list(nx.simple_cycles(G))
        except Exception:
            cycles = []
        
        for cycle in cycles:
            if len(cycle) > 1:  # Ignore self-loops
                issue = DependencyIssue(
                    issue_type=IssueType.CIRCULAR_DEPENDENCY,
                    severity=Severity.HIGH if len(cycle) <= 3 else Severity.CRITICAL,
                    description=f"Circular dependency detected: {' -> '.join(cycle)} -> {cycle[0]}",
                    affected_modules=cycle,
                    suggestion=self._get_circular_fix_suggestion(cycle),
                    auto_fixable=False,
                    metadata={'cycle_length': len(cycle), 'cycle': cycle}
                )
                self.graph.issues.append(issue)
    
    def _get_circular_fix_suggestion(self, cycle: List[str]) -> str:
        """Generate fix suggestion for circular dependency."""
        cycle_str = ' -> '.join(cycle)
        
        suggestions = [
            "Extract shared interfaces to a separate module",
            "Use dependency inversion (depend on abstractions, not concretions)",
            "Move shared functionality to a common utility module",
            "Use events or callbacks to break the cycle",
            "Consider merging modules if they're tightly coupled"
        ]
        
        if len(cycle) == 2:
            return f"Two-module cycle ({cycle_str}). {suggestions[0]} or {suggestions[1]}."
        else:
            return f"Multi-module cycle ({cycle_str}). Consider creating a shared base module."
    
    def _detect_architectural_violations(self):
        """Detect violations of architectural layering."""
        if not self.graph.layers:
            self._analyze_layering()
        
        # Check for improper dependencies (lower layer depending on higher layer)
        for edge in self.graph.edges:
            source_layer = self.graph.layers.get(edge.source, 0)
            target_layer = self.graph.layers.get(edge.target, 0)
            
            if source_layer < target_layer:
                issue = DependencyIssue(
                    issue_type=IssueType.IMPROPER_LAYERING,
                    severity=Severity.MEDIUM,
                    description=f"Layer violation: {edge.source} (layer {source_layer}) depends on {edge.target} (layer {target_layer})",
                    affected_modules=[edge.source, edge.target],
                    suggestion="Dependencies should flow from higher to lower layers. Consider using dependency inversion.",
                    auto_fixable=False,
                    metadata={'source_layer': source_layer, 'target_layer': target_layer}
                )
                self.graph.issues.append(issue)
    
    def _detect_tight_coupling(self):
        """Detect modules with too many dependencies."""
        for module_name, metrics in self.graph.modules.items():
            if metrics.fan_out > self.coupling_threshold:
                issue = DependencyIssue(
                    issue_type=IssueType.TIGHT_COUPLING,
                    severity=Severity.MEDIUM if metrics.fan_out < 20 else Severity.HIGH,
                    description=f"Module '{module_name}' has {metrics.fan_out} dependencies (tight coupling)",
                    affected_modules=[module_name],
                    suggestion="Consider splitting this module or using facade pattern to reduce dependencies.",
                    auto_fixable=False,
                    metadata={'dependency_count': metrics.fan_out, 'dependencies': [e.target for e in metrics.dependencies]}
                )
                self.graph.issues.append(issue)
            
            # God module detection
            if metrics.number_of_classes > 20 or metrics.lines_of_code > 1000:
                issue = DependencyIssue(
                    issue_type=IssueType.GOD_MODULE,
                    severity=Severity.HIGH,
                    description=f"Module '{module_name}' may be a God module ({metrics.lines_of_code} LOC, {metrics.number_of_classes} classes)",
                    affected_modules=[module_name],
                    suggestion="Split this module into smaller, focused modules with single responsibilities.",
                    auto_fixable=False,
                    metadata={'loc': metrics.lines_of_code, 'classes': metrics.number_of_classes}
                )
                self.graph.issues.append(issue)
    
    def _detect_unused_imports(self):
        """Detect potentially unused imports."""
        # This requires deeper analysis - placeholder
        pass
    
    def _analyze_layering(self):
        """
        Analyze and assign layer indices to modules.
        
        Layer definitions:
        0: Domain/Models (core business logic, no external deps)
        1: Services/Use Cases (depends on domain)
        2: Interfaces/Controllers (depends on services)
        3: Infrastructure/Adapters (depends on interfaces)
        4: Application/Entry Points (depends on infrastructure)
        """
        # Build reverse dependency graph
        G = nx.DiGraph()
        for edge in self.graph.edges:
            G.add_edge(edge.source, edge.target)
        
        # Heuristic: classify by name patterns
        for module_name in self.graph.modules:
            name_lower = module_name.lower()
            
            if any(x in name_lower for x in ['model', 'domain', 'entity', 'schema', 'types']):
                self.graph.layers[module_name] = 0
            elif any(x in name_lower for x in ['service', 'usecase', 'use_case', 'interactor']):
                self.graph.layers[module_name] = 1
            elif any(x in name_lower for x in ['controller', 'api', 'router', 'handler', 'interface']):
                self.graph.layers[module_name] = 2
            elif any(x in name_lower for x in ['repository', 'client', 'adapter', 'gateway', 'infra']):
                self.graph.layers[module_name] = 3
            elif any(x in name_lower for x in ['main', 'app', 'cli', 'run', 'server']):
                self.graph.layers[module_name] = 4
            else:
                # Default to service layer
                self.graph.layers[module_name] = 1
        
        # Refine based on dependencies
        changed = True
        max_iterations = 10
        iteration = 0
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            for module_name in self.graph.modules:
                current_layer = self.graph.layers.get(module_name, 1)
                
                # Module should be at least one layer above its dependencies
                deps = self.graph.modules[module_name].dependencies
                for edge in deps:
                    dep_layer = self.graph.layers.get(edge.target, 1)
                    if current_layer <= dep_layer:
                        self.graph.layers[module_name] = dep_layer + 1
                        changed = True
                
                # Module should be at least one layer below its dependents
                dependents = self.graph.modules[module_name].dependents
                for dep in dependents:
                    dep_layer = self.graph.layers.get(dep, 1)
                    if current_layer >= dep_layer:
                        self.graph.layers[dep] = current_layer + 1
                        changed = True
        
        # Clamp to valid range
        for module_name in self.graph.layers:
            self.graph.layers[module_name] = min(4, max(0, self.graph.layers[module_name]))
    
    # ============================================================
    # OPTIMIZATION SUGGESTIONS
    # ============================================================
    
    def generate_optimization_suggestions(self) -> List[OptimizationSuggestion]:
        """Generate prioritized optimization suggestions."""
        suggestions = []
        
        # 1. Fix circular dependencies first
        circular_issues = [i for i in self.graph.issues if i.issue_type == IssueType.CIRCULAR_DEPENDENCY]
        if circular_issues:
            suggestions.append(OptimizationSuggestion(
                title="Fix Circular Dependencies",
                description=f"Found {len(circular_issues)} circular dependencies. These make code hard to test and maintain.",
                impact=Severity.CRITICAL,
                effort="medium",
                steps=[
                    "Identify the shared functionality causing the cycle",
                    "Extract interfaces to a separate module",
                    "Use dependency inversion principle",
                    "Consider merging tightly coupled modules"
                ],
                affected_modules=list(set(m for i in circular_issues for m in i.affected_modules))
            ))
        
        # 2. Reduce tight coupling
        tightly_coupled = [
            (name, metrics) for name, metrics in self.graph.modules.items()
            if metrics.fan_out > self.coupling_threshold
        ]
        if tightly_coupled:
            top_offenders = sorted(tightly_coupled, key=lambda x: x[1].fan_out, reverse=True)[:3]
            suggestions.append(OptimizationSuggestion(
                title="Reduce Tight Coupling",
                description=f"Modules with high fan-out: {', '.join(n for n, _ in top_offenders)}",
                impact=Severity.HIGH,
                effort="medium",
                steps=[
                    "Apply facade pattern to simplify interfaces",
                    "Use dependency injection",
                    "Split large modules into smaller, focused ones",
                    "Introduce abstraction layers"
                ],
                affected_modules=[n for n, _ in top_offenders]
            ))
        
        # 3. Fix layer violations
        layer_violations = [i for i in self.graph.issues if i.issue_type == IssueType.IMPROPER_LAYERING]
        if layer_violations:
            suggestions.append(OptimizationSuggestion(
                title="Fix Architectural Layer Violations",
                description=f"Found {len(layer_violations)} layer violations. Dependencies should flow downward.",
                impact=Severity.MEDIUM,
                effort="medium",
                steps=[
                    "Review dependencies that go against layer direction",
                    "Use dependency inversion (interfaces) for upward communication",
                    "Consider event-driven patterns for cross-layer communication"
                ],
                affected_modules=list(set(m for i in layer_violations for m in i.affected_modules))
            ))
        
        # 4. Split God modules
        god_modules = [i for i in self.graph.issues if i.issue_type == IssueType.GOD_MODULE]
        if god_modules:
            suggestions.append(OptimizationSuggestion(
                title="Split Large Modules",
                description=f"Found {len(god_modules)} modules that are too large.",
                impact=Severity.MEDIUM,
                effort="high",
                steps=[
                    "Identify distinct responsibilities within the module",
                    "Extract cohesive groups into separate modules",
                    "Create clear interfaces between new modules",
                    "Update imports and dependencies"
                ],
                affected_modules=list(set(m for i in god_modules for m in i.affected_modules))
            ))
        
        return suggestions
    
    def get_ai_optimization_plan(self) -> str:
        """Get AI-generated optimization plan."""
        prompt = f"""
        Analyze this Python project's dependency structure and create an optimization plan.
        
        Project Metrics:
        - Total modules: {self.graph.metrics.get('total_modules', 0)}
        - Total dependencies: {self.graph.metrics.get('total_edges', 0)}
        - Average fan-out: {self.graph.metrics.get('avg_fan_out', 0):.2f}
        - Density: {self.graph.metrics.get('density', 0):.3f}
        
        Issues Found:
        {json.dumps([{
            'type': i.issue_type.value,
            'severity': i.severity.value,
            'description': i.description,
            'modules': i.affected_modules
        } for i in self.graph.issues], indent=2)}
        
        Top Dependencies (by fan-out):
        {json.dumps(self.graph.metrics.get('most_dependencies', []), indent=2)}
        
        Most Depended On:
        {json.dumps(self.graph.metrics.get('most_depended_on', []), indent=2)}
        
        Create a prioritized optimization plan with:
        1. Immediate actions (1-2 days)
        2. Short-term improvements (1 week)
        3. Long-term architectural changes (1 month)
        
        For each action, provide:
        - Clear description
        - Expected benefit
        - Potential risks
        - Effort estimate
        """
        
        return self.llm.complete(prompt)
    
    # ============================================================
    # VISUALIZATION
    # ============================================================
    
    def generate_mermaid_diagram(self, max_modules: int = 30) -> str:
        """Generate Mermaid diagram of dependency graph."""
        lines = ["```mermaid", "graph TD"]
        
        # Select top modules by dependency count
        module_scores = {
            name: metrics.fan_in + metrics.fan_out
            for name, metrics in self.graph.modules.items()
        }
        top_modules = sorted(module_scores, key=module_scores.get, reverse=True)[:max_modules]
        
        # Generate nodes with layer coloring
        layer_colors = {
            0: "#e1f5fe",  # Light blue - Domain
            1: "#c8e6c9",  # Light green - Services
            2: "#fff9c4",  # Light yellow - Controllers
            3: "#ffccbc",  # Light orange - Infrastructure
            4: "#f8bbd0",  # Light pink - Application
        }
        
        for module in top_modules:
            layer = self.graph.layers.get(module, 1)
            color = layer_colors.get(layer, "#ffffff")
            short_name = module.split('.')[-1]
            lines.append(f"    {self._sanitize_node(module)}[\"{short_name}\"]")
        
        # Generate edges
        for edge in self.graph.edges:
            if edge.source in top_modules and edge.target in top_modules:
                style = ""
                if edge.dep_type == DependencyType.CIRCULAR:
                    style = " ==> "
                elif self.graph.layers.get(edge.source, 0) < self.graph.layers.get(edge.target, 0):
                    style = " -.->|violation| "
                else:
                    style = " --> "
                
                lines.append(f"    {self._sanitize_node(edge.source)}{style}{self._sanitize_node(edge.target)}")
        
        lines.append("```")
        return "\n".join(lines)
    
    def _sanitize_node(self, name: str) -> str:
        """Sanitize module name for Mermaid."""
        return name.replace('.', '_').replace('-', '_')
    
    def generate_ascii_tree(self, package: Optional[str] = None) -> str:
        """Generate ASCII tree of module dependencies."""
        lines = []
        
        if package:
            modules = self.graph.packages.get(package, [])
        else:
            modules = list(self.graph.modules.keys())
        
        # Build tree structure
        tree = self._build_dependency_tree(modules)
        
        def _format_tree(node: Dict, indent: str = "", is_last: bool = True) -> List[str]:
            result = []
            prefix = "└── " if is_last else "├── "
            result.append(f"{indent}{prefix}{node['name']} ({node['metrics'].fan_out} deps)")
            
            children = node.get('children', [])
            for i, child in enumerate(children):
                child_indent = indent + ("    " if is_last else "│   ")
                result.extend(_format_tree(child, child_indent, i == len(children) - 1))
            
            return result
        
        for root in tree:
            lines.extend(_format_tree(root))
        
        return "\n".join(lines)
    
    def _build_dependency_tree(self, modules: List[str]) -> List[Dict]:
        """Build tree structure for visualization."""
        trees = []
        visited = set()
        
        def _build_node(module_name: str) -> Dict:
            if module_name in visited:
                return {'name': module_name, 'metrics': self.graph.modules.get(module_name), 'children': []}
            
            visited.add(module_name)
            metrics = self.graph.modules.get(module_name, ModuleMetrics(name=module_name))
            
            children = []
            for edge in metrics.dependencies[:5]:  # Limit to first 5 for readability
                child = _build_node(edge.target)
                children.append(child)
            
            return {'name': module_name, 'metrics': metrics, 'children': children}
        
        for module in modules[:10]:  # Limit roots
            if module not in visited:
                trees.append(_build_node(module))
        
        return trees
    
    # ============================================================
    # REPORTING
    # ============================================================
    
    def generate_report(self, output_format: str = "markdown") -> str:
        """Generate comprehensive dependency analysis report."""
        if output_format == "markdown":
            return self._generate_markdown_report()
        elif output_format == "json":
            return json.dumps(self._generate_json_report(), indent=2)
        elif output_format == "html":
            return self._generate_html_report()
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def _generate_markdown_report(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# Dependency Analysis Report",
            f"",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Modules | {self.graph.metrics.get('total_modules', 0)} |",
            f"| Total Dependencies | {self.graph.metrics.get('total_edges', 0)} |",
            f"| Total Packages | {self.graph.metrics.get('total_packages', 0)} |",
            f"| Average Fan-In | {self.graph.metrics.get('avg_fan_in', 0):.2f} |",
            f"| Average Fan-Out | {self.graph.metrics.get('avg_fan_out', 0):.2f} |",
            f"| Graph Density | {self.graph.metrics.get('density', 0):.3f} |",
            f"",
            f"## Issues Found",
            f"",
        ]
        
        # Group issues by severity
        issues_by_severity = defaultdict(list)
        for issue in self.graph.issues:
            issues_by_severity[issue.severity].append(issue)
        
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            issues = issues_by_severity.get(severity, [])
            if issues:
                lines.append(f"### {severity.value.upper()} ({len(issues)})")
                lines.append("")
                for issue in issues:
                    lines.append(f"**{issue.issue_type.value}**")
                    lines.append(f"- {issue.description}")
                    lines.append(f"- Affected: {', '.join(issue.affected_modules[:5])}")
                    if len(issue.affected_modules) > 5:
                        lines.append(f"  *(and {len(issue.affected_modules) - 5} more)*")
                    lines.append(f"- Suggestion: {issue.suggestion}")
                    lines.append("")
        
        # Top modules
        lines.extend([
            f"## Most Depended-On Modules",
            f"",
            f"| Module | Fan-In |",
            f"|--------|--------|",
        ])
        for item in self.graph.metrics.get('most_depended_on', [])[:10]:
            lines.append(f"| {item['name']} | {item['fan_in']} |")
        
        lines.extend([
            f"",
            f"## Modules with Most Dependencies",
            f"",
            f"| Module | Fan-Out |",
            f"|--------|---------|",
        ])
        for item in self.graph.metrics.get('most_dependencies', [])[:10]:
            lines.append(f"| {item['name']} | {item['fan_out']} |")
        
        # Optimization suggestions
        suggestions = self.generate_optimization_suggestions()
        if suggestions:
            lines.extend([
                f"",
                f"## Optimization Suggestions",
                f"",
            ])
            for i, sugg in enumerate(suggestions, 1):
                lines.extend([
                    f"### {i}. {sugg.title}",
                    f"",
                    f"**Impact:** {sugg.impact.value} | **Effort:** {sugg.effort}",
                    f"",
                    f"{sugg.description}",
                    f"",
                    f"**Steps:**",
                ])
                for step in sugg.steps:
                    lines.append(f"- {step}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_json_report(self) -> Dict[str, Any]:
        """Generate JSON report."""
        return {
            'analyzed_at': self.graph.analyzed_at.isoformat(),
            'metrics': self.graph.metrics,
            'issues': [
                {
                    'type': i.issue_type.value,
                    'severity': i.severity.value,
                    'description': i.description,
                    'affected_modules': i.affected_modules,
                    'suggestion': i.suggestion,
                    'auto_fixable': i.auto_fixable
                }
                for i in self.graph.issues
            ],
            'module_metrics': {
                name: {
                    'fan_in': m.fan_in,
                    'fan_out': m.fan_out,
                    'instability': m.instability,
                    'abstractness': m.abstractness,
                    'distance': m.distance_from_main_sequence,
                    'layer': self.graph.layers.get(name, 1)
                }
                for name, m in self.graph.modules.items()
            },
            'optimization_suggestions': [
                {
                    'title': s.title,
                    'description': s.description,
                    'impact': s.impact.value,
                    'effort': s.effort,
                    'steps': s.steps
                }
                for s in self.generate_optimization_suggestions()
            ]
        }
    
    def _generate_html_report(self) -> str:
        """Generate HTML report."""
        json_data = json.dumps(self._generate_json_report())
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Dependency Analysis Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .critical {{ color: #d32f2f; }}
        .high {{ color: #f57c00; }}
        .medium {{ color: #fbc02d; }}
        .low {{ color: #388e3c; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <h1>Dependency Analysis Report</h1>
    <p>Generated: {self.graph.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <div id="report"></div>
    <script>
        const data = {json_data};
        // Render report using JavaScript
        document.getElementById('report').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    </script>
</body>
</html>"""
    
    # ============================================================
    # EXPORT AND PERSISTENCE
    # ============================================================
    
    def export_graph(self, output_path: Optional[Path] = None) -> Path:
        """Export dependency graph to file."""
        if output_path is None:
            output_path = self.project_root / "project_doc" / "dependency_graph.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'analyzed_at': self.graph.analyzed_at.isoformat(),
            'modules': list(self.graph.modules.keys()),
            'edges': [
                {'source': e.source, 'target': e.target, 'type': e.dep_type.value}
                for e in self.graph.edges
            ],
            'layers': self.graph.layers,
            'metrics': self.graph.metrics
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported dependency graph to {output_path}")
        return output_path
    
    def save_report(self, output_path: Optional[Path] = None) -> Path:
        """Save analysis report to file."""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.project_root / "project_doc" / f"dependency_report_{timestamp}.md"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_report("markdown")
        output_path.write_text(report)
        
        logger.info(f"Saved dependency report to {output_path}")
        return output_path


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for dependency analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze project dependencies")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    parser.add_argument("--output", "-o", type=Path,
                       help="Output report path")
    parser.add_argument("--format", choices=["markdown", "json", "html"],
                       default="markdown", help="Report format")
    parser.add_argument("--mermaid", action="store_true",
                       help="Generate Mermaid diagram")
    parser.add_argument("--suggestions", action="store_true",
                       help="Show optimization suggestions only")
    parser.add_argument("--ai-plan", action="store_true",
                       help="Generate AI optimization plan")
    
    args = parser.parse_args()
    
    analyzer = DependencyAnalyzer(args.project_root)
    graph = analyzer.analyze()
    
    if args.suggestions:
        suggestions = analyzer.generate_optimization_suggestions()
        for s in suggestions:
            print(f"\n## {s.title}")
            print(f"Impact: {s.impact.value} | Effort: {s.effort}")
            print(f"{s.description}")
            print("\nSteps:")
            for step in s.steps:
                print(f"  - {step}")
    elif args.ai_plan:
        plan = analyzer.get_ai_optimization_plan()
        print(plan)
    elif args.mermaid:
        print(analyzer.generate_mermaid_diagram())
    else:
        report = analyzer.generate_report(args.format)
        if args.output:
            args.output.write_text(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)


if __name__ == "__main__":
    main()