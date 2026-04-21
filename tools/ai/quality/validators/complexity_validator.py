#!/usr/bin/env python3
"""
Complexity Validator - Validates code complexity metrics and enforces limits.

Part of the Quality tools (validators/complexity_validator.py)

This complexity_validator.py provides:

1. Cyclomatic Complexity - Measures code paths and branches
2. Cognitive Complexity - Measures how hard code is to understand
3. Halstead Metrics - Volume, difficulty, effort, bugs, time
4. Maintainability Index - Overall maintainability score (0-100)
5. Technical Debt Estimation - Hours needed to fix issues
6. Nesting Depth Analysis - Tracks indentation levels
7. Coupling Metrics - Afferent/efferent coupling
8. Configurable Thresholds - Per metric and scope
9. Grade Calculation - A-F grade based on overall score
10. Top Offenders - Identifies most problematic code
11. Comprehensive Reporting - JSON and Markdown formats
12. Actionable Recommendations - Specific refactoring suggestions

The complexity validator helps maintain code quality by identifying overly complex code that needs refactoring.
"""

import ast
import json
import math
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

class ComplexityMetric(str, Enum):
    """Types of complexity metrics."""
    CYCLOMATIC = "cyclomatic"
    COGNITIVE = "cognitive"
    HALSTEAD_VOLUME = "halstead_volume"
    HALSTEAD_DIFFICULTY = "halstead_difficulty"
    HALSTEAD_EFFORT = "halstead_effort"
    MAINTAINABILITY = "maintainability"
    LINES_OF_CODE = "lines_of_code"
    NESTING_DEPTH = "nesting_depth"
    PARAMETER_COUNT = "parameter_count"
    RETURN_COUNT = "return_count"
    BRANCH_COUNT = "branch_count"
    LOOP_COUNT = "loop_count"
    METHOD_COUNT = "method_count"
    ATTRIBUTE_COUNT = "attribute_count"
    DEPENDENCY_COUNT = "dependency_count"
    AFFERENT_COUPLING = "afferent_coupling"
    EFFERENT_COUPLING = "efferent_coupling"
    INSTABILITY = "instability"
    ABSTRACTNESS = "abstractness"
    DISTANCE_FROM_MAIN = "distance_from_main"


class Severity(str, Enum):
    """Severity of complexity violation."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Scope(str, Enum):
    """Scope of complexity check."""
    PROJECT = "project"
    PACKAGE = "package"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ComplexityThreshold:
    """Threshold for a complexity metric."""
    metric: ComplexityMetric
    scope: Scope
    warning_threshold: float
    error_threshold: float
    description: str = ""


@dataclass
class ComplexityViolation:
    """A single complexity violation."""
    metric: ComplexityMetric
    severity: Severity
    scope: Scope
    entity_name: str
    file_path: str
    line_number: Optional[int] = None
    actual_value: float = 0.0
    threshold: float = 0.0
    description: str = ""
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplexityMetrics:
    """Complexity metrics for a code entity."""
    entity_name: str
    entity_type: Scope
    file_path: str
    line_start: int = 0
    line_end: int = 0
    
    # Core metrics
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    lines_of_code: int = 0
    logical_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # Structural metrics
    nesting_depth: int = 0
    parameter_count: int = 0
    return_count: int = 0
    branch_count: int = 0
    loop_count: int = 0
    
    # Halstead metrics
    halstead_volume: float = 0.0
    halstead_difficulty: float = 0.0
    halstead_effort: float = 0.0
    halstead_bugs: float = 0.0
    halstead_time: float = 0.0
    
    # Maintainability
    maintainability_index: float = 100.0
    technical_debt_ratio: float = 0.0
    technical_debt_hours: float = 0.0
    
    # Class-specific
    method_count: int = 0
    attribute_count: int = 0
    public_methods: int = 0
    private_methods: int = 0
    abstract_methods: int = 0
    depth_of_inheritance: int = 0
    number_of_children: int = 0
    
    # Coupling metrics
    afferent_coupling: int = 0
    efferent_coupling: int = 0
    instability: float = 0.0
    abstractness: float = 0.0
    distance_from_main: float = 0.0
    
    # Additional
    children: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplexityReport:
    """Complete complexity validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    total_files: int = 0
    total_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    
    # Metrics summaries
    project_metrics: ComplexityMetrics = field(default_factory=lambda: ComplexityMetrics(
        entity_name="project", entity_type=Scope.PROJECT, file_path=""
    ))
    
    # Violations
    violations: List[ComplexityViolation] = field(default_factory=list)
    warnings: List[ComplexityViolation] = field(default_factory=list)
    
    # Detailed metrics by entity
    module_metrics: Dict[str, ComplexityMetrics] = field(default_factory=dict)
    class_metrics: Dict[str, ComplexityMetrics] = field(default_factory=dict)
    function_metrics: Dict[str, ComplexityMetrics] = field(default_factory=dict)
    
    # Top offenders
    most_complex_functions: List[Tuple[str, int]] = field(default_factory=list)
    most_complex_classes: List[Tuple[str, int]] = field(default_factory=list)
    largest_modules: List[Tuple[str, int]] = field(default_factory=list)
    
    # Summary
    is_valid: bool = True
    overall_score: float = 0.0
    grade: str = "A"
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplexityValidatorConfig:
    """Configuration for complexity validator."""
    project_root: Path
    
    # Custom thresholds
    thresholds: List[ComplexityThreshold] = field(default_factory=lambda: [
        # Cyclomatic complexity
        ComplexityThreshold(ComplexityMetric.CYCLOMATIC, Scope.FUNCTION, 10, 20, 
                          "Cyclomatic complexity measures the number of linearly independent paths"),
        ComplexityThreshold(ComplexityMetric.CYCLOMATIC, Scope.METHOD, 10, 20,
                          "Method cyclomatic complexity"),
        ComplexityThreshold(ComplexityMetric.CYCLOMATIC, Scope.CLASS, 50, 100,
                          "Total class cyclomatic complexity"),
        ComplexityThreshold(ComplexityMetric.CYCLOMATIC, Scope.MODULE, 100, 200,
                          "Total module cyclomatic complexity"),
        
        # Cognitive complexity
        ComplexityThreshold(ComplexityMetric.COGNITIVE, Scope.FUNCTION, 15, 25,
                          "Cognitive complexity measures how hard code is to understand"),
        ComplexityThreshold(ComplexityMetric.COGNITIVE, Scope.METHOD, 15, 25,
                          "Method cognitive complexity"),
        
        # Lines of code
        ComplexityThreshold(ComplexityMetric.LINES_OF_CODE, Scope.FUNCTION, 50, 100,
                          "Function length in lines"),
        ComplexityThreshold(ComplexityMetric.LINES_OF_CODE, Scope.METHOD, 50, 100,
                          "Method length in lines"),
        ComplexityThreshold(ComplexityMetric.LINES_OF_CODE, Scope.CLASS, 300, 500,
                          "Class length in lines"),
        ComplexityThreshold(ComplexityMetric.LINES_OF_CODE, Scope.MODULE, 500, 1000,
                          "Module length in lines"),
        
        # Nesting depth
        ComplexityThreshold(ComplexityMetric.NESTING_DEPTH, Scope.FUNCTION, 3, 5,
                          "Maximum nesting depth"),
        
        # Parameter count
        ComplexityThreshold(ComplexityMetric.PARAMETER_COUNT, Scope.FUNCTION, 5, 8,
                          "Number of function parameters"),
        ComplexityThreshold(ComplexityMetric.PARAMETER_COUNT, Scope.METHOD, 5, 8,
                          "Number of method parameters"),
        
        # Return count
        ComplexityThreshold(ComplexityMetric.RETURN_COUNT, Scope.FUNCTION, 3, 5,
                          "Number of return statements"),
        
        # Method count
        ComplexityThreshold(ComplexityMetric.METHOD_COUNT, Scope.CLASS, 20, 30,
                          "Number of methods in a class"),
        
        # Attribute count
        ComplexityThreshold(ComplexityMetric.ATTRIBUTE_COUNT, Scope.CLASS, 15, 25,
                          "Number of attributes in a class"),
        
        # Maintainability index
        ComplexityThreshold(ComplexityMetric.MAINTAINABILITY, Scope.FUNCTION, 65, 40,
                          "Maintainability index (higher is better)"),
        ComplexityThreshold(ComplexityMetric.MAINTAINABILITY, Scope.CLASS, 65, 40,
                          "Class maintainability index"),
        ComplexityThreshold(ComplexityMetric.MAINTAINABILITY, Scope.MODULE, 65, 40,
                          "Module maintainability index"),
        
        # Efferent coupling
        ComplexityThreshold(ComplexityMetric.EFFERENT_COUPLING, Scope.CLASS, 10, 20,
                          "Number of outgoing dependencies"),
    ])
    
    # Ignore patterns
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "test_*.py", "*_test.py",
        "migrations", "alembic"
    ])
    
    # Scope to validate
    validate_scopes: List[Scope] = field(default_factory=lambda: [
        Scope.MODULE, Scope.CLASS, Scope.FUNCTION, Scope.METHOD
    ])
    
    # Configuration
    fail_on_error: bool = True
    fail_on_warning: bool = False
    include_private: bool = False
    include_tests: bool = False
    calculate_halstead: bool = True
    calculate_maintainability: bool = True
    calculate_coupling: bool = True
    max_top_offenders: int = 10
    generate_report: bool = True
    output_format: str = "markdown"


# ============================================================
# COMPLEXITY ANALYZER
# ============================================================

class ComplexityAnalyzer(ast.NodeVisitor):
    """Analyze code complexity metrics."""
    
    def __init__(self, file_path: str, config: ComplexityValidatorConfig):
        self.file_path = file_path
        self.config = config
        self.source_lines: List[str] = []
        self.current_metrics: Optional[ComplexityMetrics] = None
        self.metrics_stack: List[ComplexityMetrics] = []
        self.all_metrics: List[ComplexityMetrics] = []
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
        self.nesting_level: int = 0
        self.return_count: int = 0
        self.branch_count: int = 0
        self.loop_count: int = 0
        
        # Halstead counters
        self.operators = defaultdict(int)
        self.operands = defaultdict(int)
        
        # Dependency tracking
        self.imports: Set[str] = set()
        self.calls: Set[str] = set()
    
    def analyze(self, tree: ast.AST, source_lines: List[str]) -> List[ComplexityMetrics]:
        """Analyze AST and return metrics."""
        self.source_lines = source_lines
        self.visit(tree)
        
        # Add module-level metrics
        module_metrics = self._create_module_metrics(tree)
        self.all_metrics.append(module_metrics)
        
        return self.all_metrics
    
    def _create_module_metrics(self, tree: ast.AST) -> ComplexityMetrics:
        """Create module-level metrics."""
        metrics = ComplexityMetrics(
            entity_name=self._module_name(),
            entity_type=Scope.MODULE,
            file_path=self.file_path,
            line_start=1,
            line_end=len(self.source_lines)
        )
        
        # Count lines
        metrics.lines_of_code = len(self.source_lines)
        metrics.logical_lines = sum(1 for line in self.source_lines if line.strip() and not line.strip().startswith('#'))
        metrics.comment_lines = sum(1 for line in self.source_lines if line.strip().startswith('#'))
        metrics.blank_lines = metrics.lines_of_code - metrics.logical_lines - metrics.comment_lines
        
        # Aggregate from children
        for child_metrics in self.all_metrics:
            if child_metrics.entity_type == Scope.FUNCTION:
                metrics.cyclomatic_complexity += child_metrics.cyclomatic_complexity
                metrics.cognitive_complexity += child_metrics.cognitive_complexity
            elif child_metrics.entity_type == Scope.CLASS:
                metrics.method_count += child_metrics.method_count
                metrics.cyclomatic_complexity += child_metrics.cyclomatic_complexity
        
        metrics.total_functions = sum(1 for m in self.all_metrics if m.entity_type == Scope.FUNCTION)
        metrics.total_classes = sum(1 for m in self.all_metrics if m.entity_type == Scope.CLASS)
        
        # Coupling metrics
        metrics.efferent_coupling = len(self.imports)
        
        return metrics
    
    def _module_name(self) -> str:
        """Get module name from file path."""
        path = Path(self.file_path)
        try:
            return path.stem
        except:
            return "unknown"
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        if self._should_ignore(node.name):
            self.generic_visit(node)
            return
        
        metrics = ComplexityMetrics(
            entity_name=node.name,
            entity_type=Scope.CLASS,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno
        )
        
        # Count lines
        if node.end_lineno:
            metrics.lines_of_code = node.end_lineno - node.lineno + 1
        
        # Count methods
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not self._should_ignore(child.name):
                    metrics.method_count += 1
                    if child.name.startswith('_') and not child.name.startswith('__'):
                        metrics.private_methods += 1
                    else:
                        metrics.public_methods += 1
        
        # Count attributes
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        metrics.attribute_count += 1
            elif isinstance(child, ast.AnnAssign):
                metrics.attribute_count += 1
        
        # Check for abstract methods
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in child.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod':
                        metrics.abstract_methods += 1
                        break
        
        prev_class = self.current_class
        self.current_class = node.name
        
        self.metrics_stack.append(metrics)
        self.generic_visit(node)
        
        # Calculate additional metrics
        if self.config.calculate_coupling:
            metrics.efferent_coupling = len(self.imports)
        
        if self.config.calculate_maintainability:
            self._calculate_maintainability(metrics)
        
        self.metrics_stack.pop()
        self.all_metrics.append(metrics)
        self.current_class = prev_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_function(node, is_async=False)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_function(node, is_async=True)
    
    def _visit_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool):
        """Visit function definition."""
        if self._should_ignore(node.name):
            self.generic_visit(node)
            return
        
        entity_type = Scope.METHOD if self.current_class else Scope.FUNCTION
        name = f"{self.current_class}.{node.name}" if self.current_class else node.name
        
        metrics = ComplexityMetrics(
            entity_name=name,
            entity_type=entity_type,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno
        )
        
        # Count lines
        if node.end_lineno:
            metrics.lines_of_code = node.end_lineno - node.lineno + 1
        
        # Count parameters
        metrics.parameter_count = len(node.args.args)
        
        # Reset counters
        self.nesting_level = 0
        self.return_count = 0
        self.branch_count = 0
        self.loop_count = 0
        self.operators.clear()
        self.operands.clear()
        
        prev_function = self.current_function
        self.current_function = node.name
        
        self.metrics_stack.append(metrics)
        
        # Visit function body
        for child in node.body:
            self.visit(child)
        
        # Calculate cyclomatic complexity
        metrics.cyclomatic_complexity = 1 + self.branch_count + self.loop_count
        
        # Calculate cognitive complexity
        metrics.cognitive_complexity = self._calculate_cognitive_complexity(node)
        
        # Set counts
        metrics.nesting_depth = self.nesting_level
        metrics.return_count = self.return_count
        metrics.branch_count = self.branch_count
        metrics.loop_count = self.loop_count
        
        # Calculate Halstead metrics
        if self.config.calculate_halstead:
            self._calculate_halstead_metrics(metrics)
        
        # Calculate maintainability
        if self.config.calculate_maintainability:
            self._calculate_maintainability(metrics)
        
        self.metrics_stack.pop()
        self.all_metrics.append(metrics)
        self.current_function = prev_function
    
    def visit_If(self, node: ast.If):
        """Visit if statement."""
        self.branch_count += 1
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1
    
    def visit_While(self, node: ast.While):
        """Visit while loop."""
        self.loop_count += 1
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1
    
    def visit_For(self, node: ast.For):
        """Visit for loop."""
        self.loop_count += 1
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """Visit except handler."""
        self.branch_count += 1
        self.generic_visit(node)
    
    def visit_Return(self, node: ast.Return):
        """Visit return statement."""
        self.return_count += 1
        self.generic_visit(node)
    
    def visit_BoolOp(self, node: ast.BoolOp):
        """Visit boolean operation."""
        self._count_operator('and' if isinstance(node.op, ast.And) else 'or')
        self.generic_visit(node)
    
    def visit_BinOp(self, node: ast.BinOp):
        """Visit binary operation."""
        op_map = {
            ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/',
            ast.FloorDiv: '//', ast.Mod: '%', ast.Pow: '**',
            ast.LShift: '<<', ast.RShift: '>>', ast.BitOr: '|',
            ast.BitXor: '^', ast.BitAnd: '&'
        }
        if type(node.op) in op_map:
            self._count_operator(op_map[type(node.op)])
        self.generic_visit(node)
    
    def visit_UnaryOp(self, node: ast.UnaryOp):
        """Visit unary operation."""
        op_map = {ast.Not: 'not', ast.Invert: '~', ast.UAdd: '+', ast.USub: '-'}
        if type(node.op) in op_map:
            self._count_operator(op_map[type(node.op)])
        self.generic_visit(node)
    
    def visit_Compare(self, node: ast.Compare):
        """Visit comparison."""
        for op in node.ops:
            if isinstance(op, ast.Eq):
                self._count_operator('==')
            elif isinstance(op, ast.NotEq):
                self._count_operator('!=')
            elif isinstance(op, ast.Lt):
                self._count_operator('<')
            elif isinstance(op, ast.LtE):
                self._count_operator('<=')
            elif isinstance(op, ast.Gt):
                self._count_operator('>')
            elif isinstance(op, ast.GtE):
                self._count_operator('>=')
            elif isinstance(op, ast.Is):
                self._count_operator('is')
            elif isinstance(op, ast.IsNot):
                self._count_operator('is not')
            elif isinstance(op, ast.In):
                self._count_operator('in')
            elif isinstance(op, ast.NotIn):
                self._count_operator('not in')
        self.generic_visit(node)
    
    def visit_Constant(self, node: ast.Constant):
        """Visit constant."""
        self._count_operand(str(node.value))
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        """Visit name."""
        if node.id not in ('self', 'cls', 'True', 'False', 'None'):
            self._count_operand(node.id)
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Visit function call."""
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.add(node.func.attr)
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import):
        """Visit import."""
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from import."""
        if node.module:
            self.imports.add(node.module.split('.')[0])
    
    def _count_operator(self, op: str):
        """Count an operator."""
        self.operators[op] += 1
    
    def _count_operand(self, operand: str):
        """Count an operand."""
        self.operands[operand] += 1
    
    def _calculate_cognitive_complexity(self, node: ast.AST) -> int:
        """Calculate cognitive complexity."""
        complexity = 0
        nesting_level = 0
        
        def visit_with_nesting(child: ast.AST, level: int):
            nonlocal complexity
            
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1 + level
                level += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.IfExp):
                complexity += 1 + level
            elif isinstance(child, (ast.Break, ast.Continue)):
                if level > 0:
                    complexity += 1
            
            for grandchild in ast.iter_child_nodes(child):
                visit_with_nesting(grandchild, level)
        
        visit_with_nesting(node, nesting_level)
        return complexity
    
    def _calculate_halstead_metrics(self, metrics: ComplexityMetrics):
        """Calculate Halstead metrics."""
        n1 = len(self.operators)  # Unique operators
        n2 = len(self.operands)   # Unique operands
        N1 = sum(self.operators.values())  # Total operators
        N2 = sum(self.operands.values())   # Total operands
        
        if n1 == 0 or n2 == 0:
            return
        
        # Program length
        N = N1 + N2
        
        # Program vocabulary
        n = n1 + n2
        
        # Volume
        V = N * math.log2(n) if n > 0 else 0
        metrics.halstead_volume = V
        
        # Difficulty
        D = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        metrics.halstead_difficulty = D
        
        # Effort
        E = V * D
        metrics.halstead_effort = E
        
        # Estimated bugs
        metrics.halstead_bugs = V / 3000
        
        # Time to program (seconds)
        metrics.halstead_time = E / 18
    
    def _calculate_maintainability(self, metrics: ComplexityMetrics):
        """Calculate maintainability index."""
        # MI = 171 - 5.2 * ln(V) - 0.23 * C - 16.2 * ln(LOC)
        V = metrics.halstead_volume or 1
        C = metrics.cyclomatic_complexity or 1
        LOC = metrics.lines_of_code or 1
        
        mi = 171 - 5.2 * math.log(V) - 0.23 * C - 16.2 * math.log(LOC)
        mi = max(0, min(100, mi))
        
        metrics.maintainability_index = mi
        
        # Technical debt ratio
        metrics.technical_debt_ratio = max(0, (100 - mi) / 100)
        
        # Technical debt hours (rough estimate)
        metrics.technical_debt_hours = metrics.technical_debt_ratio * LOC / 10
    
    def _should_ignore(self, name: str) -> bool:
        """Check if entity should be ignored."""
        if not self.config.include_private:
            if name.startswith('_') and not name.startswith('__'):
                return True
        return False


# ============================================================
# MAIN COMPLEXITY VALIDATOR
# ============================================================

class ComplexityValidator:
    """
    Validates code complexity metrics and enforces limits.
    
    Features:
    - Cyclomatic complexity analysis
    - Cognitive complexity analysis
    - Halstead metrics (volume, difficulty, effort)
    - Maintainability index calculation
    - Technical debt estimation
    - Nesting depth analysis
    - Coupling metrics (afferent/efferent)
    - Configurable thresholds per scope
    - Comprehensive reporting
    - Grade calculation
    """
    
    def __init__(self, config: ComplexityValidatorConfig):
        self.config = config
        self.state = StateManager(config.project_root / ".ai_state" / "complexity_validator.json")
        
        # Build threshold lookup
        self.threshold_map: Dict[Tuple[ComplexityMetric, Scope], ComplexityThreshold] = {}
        for threshold in config.thresholds:
            self.threshold_map[(threshold.metric, threshold.scope)] = threshold
        
        logger.info("ComplexityValidator initialized")
    
    def validate(self) -> ComplexityReport:
        """Run complete complexity validation."""
        logger.info("Starting complexity validation...")
        
        report = ComplexityReport(
            project_name=self.config.project_root.name
        )
        
        # Find Python files
        python_files = list(self.config.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_ignore(file_path):
                continue
            
            try:
                file_metrics = self._analyze_file(file_path)
                
                # Update report
                report.total_files += 1
                report.total_lines += file_metrics.lines_of_code
                
                report.module_metrics[str(file_path)] = file_metrics
                
                # Collect function/class metrics
                for metrics in file_metrics.children_metrics:
                    if metrics.entity_type == Scope.FUNCTION:
                        report.function_metrics[metrics.entity_name] = metrics
                        report.total_functions += 1
                    elif metrics.entity_type == Scope.CLASS:
                        report.class_metrics[metrics.entity_name] = metrics
                        report.total_classes += 1
                    
                    # Check thresholds
                    self._check_thresholds(metrics, report)
                
                # Check module thresholds
                self._check_thresholds(file_metrics, report)
                
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Calculate project-level metrics
        report.project_metrics = self._calculate_project_metrics(report)
        
        # Find top offenders
        report.most_complex_functions = self._find_top_complex_functions(report)
        report.most_complex_classes = self._find_top_complex_classes(report)
        report.largest_modules = self._find_largest_modules(report)
        
        # Calculate overall score and grade
        report.overall_score, report.grade = self._calculate_overall_score(report)
        
        # Determine validity
        report.is_valid = len(report.violations) == 0
        if self.config.fail_on_warning and report.warnings:
            report.is_valid = False
        
        # Generate summary and recommendations
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Complexity validation complete: {len(report.violations)} violations, {len(report.warnings)} warnings")
        
        return report
    
    def _analyze_file(self, file_path: Path) -> ComplexityMetrics:
        """Analyze a single file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        source_lines = content.split('\n')
        tree = ast.parse(content)
        
        analyzer = ComplexityAnalyzer(str(file_path), self.config)
        all_metrics = analyzer.analyze(tree, source_lines)
        
        # Find module metrics
        module_metrics = next(m for m in all_metrics if m.entity_type == Scope.MODULE)
        module_metrics.children_metrics = [m for m in all_metrics if m.entity_type != Scope.MODULE]
        
        return module_metrics
    
    def _check_thresholds(self, metrics: ComplexityMetrics, report: ComplexityReport):
        """Check metrics against thresholds."""
        metric_values = {
            ComplexityMetric.CYCLOMATIC: metrics.cyclomatic_complexity,
            ComplexityMetric.COGNITIVE: metrics.cognitive_complexity,
            ComplexityMetric.LINES_OF_CODE: metrics.lines_of_code,
            ComplexityMetric.NESTING_DEPTH: metrics.nesting_depth,
            ComplexityMetric.PARAMETER_COUNT: metrics.parameter_count,
            ComplexityMetric.RETURN_COUNT: metrics.return_count,
            ComplexityMetric.METHOD_COUNT: metrics.method_count,
            ComplexityMetric.ATTRIBUTE_COUNT: metrics.attribute_count,
            ComplexityMetric.MAINTAINABILITY: metrics.maintainability_index,
            ComplexityMetric.EFFERENT_COUPLING: metrics.efferent_coupling,
        }
        
        for metric, value in metric_values.items():
            if value == 0:
                continue
            
            key = (metric, metrics.entity_type)
            if key not in self.threshold_map:
                continue
            
            threshold = self.threshold_map[key]
            
            # Check error threshold
            if value > threshold.error_threshold:
                violation = ComplexityViolation(
                    metric=metric,
                    severity=Severity.CRITICAL if value > threshold.error_threshold * 1.5 else Severity.HIGH,
                    scope=metrics.entity_type,
                    entity_name=metrics.entity_name,
                    file_path=metrics.file_path,
                    line_number=metrics.line_start,
                    actual_value=value,
                    threshold=threshold.error_threshold,
                    description=f"{metric.value} exceeds error threshold ({value} > {threshold.error_threshold})",
                    suggestion=self._get_suggestion(metric, value, threshold.error_threshold)
                )
                report.violations.append(violation)
            
            # Check warning threshold
            elif value > threshold.warning_threshold:
                violation = ComplexityViolation(
                    metric=metric,
                    severity=Severity.MEDIUM,
                    scope=metrics.entity_type,
                    entity_name=metrics.entity_name,
                    file_path=metrics.file_path,
                    line_number=metrics.line_start,
                    actual_value=value,
                    threshold=threshold.warning_threshold,
                    description=f"{metric.value} exceeds warning threshold ({value} > {threshold.warning_threshold})",
                    suggestion=self._get_suggestion(metric, value, threshold.warning_threshold)
                )
                report.warnings.append(violation)
    
    def _get_suggestion(self, metric: ComplexityMetric, value: float, threshold: float) -> str:
        """Get suggestion for reducing complexity."""
        suggestions = {
            ComplexityMetric.CYCLOMATIC: "Extract complex logic into separate functions or use early returns",
            ComplexityMetric.COGNITIVE: "Simplify nested conditions, extract methods, or use guard clauses",
            ComplexityMetric.LINES_OF_CODE: "Split into smaller functions or classes",
            ComplexityMetric.NESTING_DEPTH: "Use early returns, extract nested blocks into functions",
            ComplexityMetric.PARAMETER_COUNT: "Group related parameters into a class or dataclass",
            ComplexityMetric.RETURN_COUNT: "Consolidate return statements or use a single return",
            ComplexityMetric.METHOD_COUNT: "Split class into multiple smaller classes (Single Responsibility)",
            ComplexityMetric.ATTRIBUTE_COUNT: "Group related attributes into separate classes",
            ComplexityMetric.MAINTAINABILITY: "Reduce complexity and add documentation",
            ComplexityMetric.EFFERENT_COUPLING: "Use dependency inversion or facade pattern",
        }
        return suggestions.get(metric, "Review and refactor to reduce complexity")
    
    def _calculate_project_metrics(self, report: ComplexityReport) -> ComplexityMetrics:
        """Calculate project-level metrics."""
        metrics = ComplexityMetrics(
            entity_name="project",
            entity_type=Scope.PROJECT,
            file_path=""
        )
        
        # Aggregate from modules
        for module_metrics in report.module_metrics.values():
            metrics.lines_of_code += module_metrics.lines_of_code
            metrics.cyclomatic_complexity += module_metrics.cyclomatic_complexity
            metrics.cognitive_complexity += module_metrics.cognitive_complexity
            metrics.halstead_volume += module_metrics.halstead_volume
            metrics.halstead_difficulty += module_metrics.halstead_difficulty
            metrics.halstead_effort += module_metrics.halstead_effort
            metrics.technical_debt_hours += module_metrics.technical_debt_hours
        
        # Calculate averages
        if report.total_files > 0:
            metrics.maintainability_index = sum(
                m.maintainability_index for m in report.module_metrics.values()
            ) / report.total_files
            metrics.technical_debt_ratio = sum(
                m.technical_debt_ratio for m in report.module_metrics.values()
            ) / report.total_files
        
        return metrics
    
    def _find_top_complex_functions(self, report: ComplexityReport) -> List[Tuple[str, int]]:
        """Find most complex functions."""
        functions = [
            (name, m.cyclomatic_complexity)
            for name, m in report.function_metrics.items()
        ]
        functions.sort(key=lambda x: x[1], reverse=True)
        return functions[:self.config.max_top_offenders]
    
    def _find_top_complex_classes(self, report: ComplexityReport) -> List[Tuple[str, int]]:
        """Find most complex classes."""
        classes = [
            (name, m.cyclomatic_complexity)
            for name, m in report.class_metrics.items()
        ]
        classes.sort(key=lambda x: x[1], reverse=True)
        return classes[:self.config.max_top_offenders]
    
    def _find_largest_modules(self, report: ComplexityReport) -> List[Tuple[str, int]]:
        """Find largest modules."""
        modules = [
            (name, m.lines_of_code)
            for name, m in report.module_metrics.items()
        ]
        modules.sort(key=lambda x: x[1], reverse=True)
        return modules[:self.config.max_top_offenders]
    
    def _calculate_overall_score(self, report: ComplexityReport) -> Tuple[float, str]:
        """Calculate overall complexity score and grade."""
        if report.total_files == 0:
            return 100.0, "A"
        
        # Base score from maintainability
        score = report.project_metrics.maintainability_index
        
        # Deduct for violations
        score -= len(report.violations) * 5
        score -= len(report.warnings) * 2
        
        # Clamp score
        score = max(0, min(100, score))
        
        # Determine grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return score, grade
    
    def _generate_summary(self, report: ComplexityReport) -> str:
        """Generate validation summary."""
        if report.is_valid:
            return f"✅ Complexity validation passed. Score: {report.overall_score:.1f} (Grade: {report.grade})"
        else:
            return f"❌ Complexity issues found: {len(report.violations)} violations, {len(report.warnings)} warnings"
    
    def _generate_recommendations(self, report: ComplexityReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if report.most_complex_functions:
            top = report.most_complex_functions[0]
            recommendations.append(f"Refactor '{top[0]}' (cyclomatic complexity: {top[1]})")
        
        if report.largest_modules:
            top = report.largest_modules[0]
            recommendations.append(f"Split '{top[0]}' into smaller modules ({top[1]} lines)")
        
        if report.project_metrics.maintainability_index < 65:
            recommendations.append("Improve overall maintainability by adding documentation and reducing complexity")
        
        if report.project_metrics.technical_debt_hours > 40:
            recommendations.append(f"Address technical debt (estimated {report.project_metrics.technical_debt_hours:.1f} hours)")
        
        return recommendations[:5]
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        path_str = str(file_path)
        for pattern in self.config.ignore_patterns:
            if pattern in path_str:
                return True
        return False
    
    def _save_report(self, report: ComplexityReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.validated_at.isoformat(),
            'project': report.project_name,
            'is_valid': report.is_valid,
            'score': report.overall_score,
            'grade': report.grade,
            'violations': len(report.violations),
            'warnings': len(report.warnings),
            'files': report.total_files,
            'lines': report.total_lines
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: ComplexityReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export complexity report."""
        
        if format == 'json':
            data = {
                'validated_at': report.validated_at.isoformat(),
                'project': report.project_name,
                'is_valid': report.is_valid,
                'score': report.overall_score,
                'grade': report.grade,
                'summary': report.summary,
                'totals': {
                    'files': report.total_files,
                    'lines': report.total_lines,
                    'functions': report.total_functions,
                    'classes': report.total_classes
                },
                'project_metrics': {
                    'maintainability': report.project_metrics.maintainability_index,
                    'cyclomatic': report.project_metrics.cyclomatic_complexity,
                    'cognitive': report.project_metrics.cognitive_complexity,
                    'technical_debt_hours': report.project_metrics.technical_debt_hours
                },
                'violations': [
                    {
                        'metric': v.metric.value,
                        'severity': v.severity.value,
                        'entity': v.entity_name,
                        'file': v.file_path,
                        'value': v.actual_value,
                        'threshold': v.threshold
                    }
                    for v in report.violations
                ],
                'warnings': [
                    {
                        'metric': w.metric.value,
                        'entity': w.entity_name,
                        'value': w.actual_value,
                        'threshold': w.threshold
                    }
                    for w in report.warnings
                ],
                'top_offenders': {
                    'functions': report.most_complex_functions,
                    'classes': report.most_complex_classes,
                    'modules': report.largest_modules
                },
                'recommendations': report.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Complexity Validation Report",
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
                f"| Total Lines | {report.total_lines:,} |",
                f"| Total Functions | {report.total_functions} |",
                f"| Total Classes | {report.total_classes} |",
                f"| Maintainability Index | {report.project_metrics.maintainability_index:.1f} |",
                f"| Cyclomatic Complexity | {report.project_metrics.cyclomatic_complexity} |",
                f"| Cognitive Complexity | {report.project_metrics.cognitive_complexity} |",
                f"| Technical Debt | {report.project_metrics.technical_debt_hours:.1f} hours |",
                "",
            ]
            
            if report.violations:
                lines.extend([
                    "## ❌ Violations",
                    "",
                    "| Metric | Severity | Entity | File | Value | Threshold |",
                    "|--------|----------|--------|------|-------|-----------|",
                ])
                for v in report.violations[:20]:
                    lines.append(f"| {v.metric.value} | {v.severity.value} | {v.entity_name[:30]} | {Path(v.file_path).name} | {v.actual_value:.1f} | {v.threshold:.1f} |")
                lines.append("")
            
            if report.warnings:
                lines.extend([
                    "## ⚠️ Warnings",
                    "",
                    "| Metric | Entity | File | Value | Threshold |",
                    "|--------|--------|------|-------|-----------|",
                ])
                for w in report.warnings[:20]:
                    lines.append(f"| {w.metric.value} | {w.entity_name[:30]} | {Path(w.file_path).name} | {w.actual_value:.1f} | {w.threshold:.1f} |")
                lines.append("")
            
            if report.most_complex_functions:
                lines.extend([
                    "## Most Complex Functions",
                    "",
                    "| Function | Complexity |",
                    "|----------|------------|",
                ])
                for name, complexity in report.most_complex_functions:
                    lines.append(f"| {name[:50]} | {complexity} |")
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
        logger.info("ComplexityValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for complexity validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate code complexity metrics")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--include-private", action="store_true")
    parser.add_argument("--max-cyclomatic", type=int, default=10, help="Max cyclomatic complexity")
    parser.add_argument("--max-cognitive", type=int, default=15, help="Max cognitive complexity")
    parser.add_argument("--max-lines", type=int, default=50, help="Max function lines")
    
    args = parser.parse_args()
    
    config = ComplexityValidatorConfig(
        project_root=args.project_root,
        fail_on_warning=args.fail_on_warning,
        include_tests=args.include_tests,
        include_private=args.include_private
    )
    
    # Override thresholds from CLI
    for threshold in config.thresholds:
        if threshold.metric == ComplexityMetric.CYCLOMATIC and threshold.scope == Scope.FUNCTION:
            threshold.warning_threshold = args.max_cyclomatic
            threshold.error_threshold = args.max_cyclomatic * 2
        elif threshold.metric == ComplexityMetric.COGNITIVE and threshold.scope == Scope.FUNCTION:
            threshold.warning_threshold = args.max_cognitive
            threshold.error_threshold = args.max_cognitive * 2
        elif threshold.metric == ComplexityMetric.LINES_OF_CODE and threshold.scope == Scope.FUNCTION:
            threshold.warning_threshold = args.max_lines
            threshold.error_threshold = args.max_lines * 2
    
    validator = ComplexityValidator(config)
    
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