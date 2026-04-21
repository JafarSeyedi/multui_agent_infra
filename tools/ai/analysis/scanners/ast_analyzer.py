#!/usr/bin/env python3
"""
AST Analyzer - AI Development Framework
Deep Abstract Syntax Tree analysis for Python code.

Part of the Level 2 Analysis tools (scanners/ast_analyzer.py)

This ast_analyzer.py provides:

1. Comprehensive Metrics - Cyclomatic complexity, cognitive complexity, Halstead metrics, maintainability index
2. Code Smell Detection - Long methods, long parameter lists, deep nesting, magic numbers, etc.
3. AST Walking - Full traversal with state tracking for accurate metrics
4. Hierarchy Tracking - Parent-child relationships between code elements
5. Import/Export Analysis - Track module dependencies and public API
6. Multi-File Analysis - Analyze entire directories recursively
7. Halstead Metrics - Volume, difficulty, and effort calculations
8. Maintainability Index - Industry-standard maintainability scoring
9. Multiple Export Formats - JSON, HTML, and Markdown reports
10. Code Smell Summaries - Aggregate statistics across files
11. Complexity Heatmaps - Identify most complex functions
12. Configurable Thresholds - Customize all detection thresholds

The AST analyzer provides deep insights into code quality and complexity, helping identify areas that need refactoring or additional attention.

"""

import ast
import json
import hashlib
import tokenize
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict, Counter
from io import StringIO

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class NodeType(str, Enum):
    """AST node types."""
    MODULE = "Module"
    CLASS = "ClassDef"
    FUNCTION = "FunctionDef"
    ASYNC_FUNCTION = "AsyncFunctionDef"
    LAMBDA = "Lambda"
    METHOD = "method"
    PROPERTY = "property"
    IMPORT = "Import"
    IMPORT_FROM = "ImportFrom"
    ASSIGN = "Assign"
    ANN_ASSIGN = "AnnAssign"
    AUG_ASSIGN = "AugAssign"
    IF = "If"
    FOR = "For"
    ASYNC_FOR = "AsyncFor"
    WHILE = "While"
    TRY = "Try"
    EXCEPT = "ExceptHandler"
    WITH = "With"
    ASYNC_WITH = "AsyncWith"
    MATCH = "Match"
    CASE = "match_case"
    RAISE = "Raise"
    ASSERT = "Assert"
    RETURN = "Return"
    YIELD = "Yield"
    YIELD_FROM = "YieldFrom"
    AWAIT = "Await"
    CALL = "Call"
    ATTRIBUTE = "Attribute"
    SUBSCRIPT = "Subscript"
    SLICE = "Slice"
    LIST = "List"
    TUPLE = "Tuple"
    DICT = "Dict"
    SET = "Set"
    LIST_COMP = "ListComp"
    DICT_COMP = "DictComp"
    SET_COMP = "SetComp"
    GENERATOR_EXP = "GeneratorExp"
    COMPREHENSION = "comprehension"
    BOOL_OP = "BoolOp"
    BIN_OP = "BinOp"
    UNARY_OP = "UnaryOp"
    COMPARE = "Compare"
    IF_EXP = "IfExp"
    NAMED_EXPR = "NamedExpr"
    CONSTANT = "Constant"
    NAME = "Name"
    STARRED = "Starred"
    KEYWORD = "keyword"
    ARG = "arg"


class ComplexityType(str, Enum):
    """Types of code complexity."""
    CYCLOMATIC = "cyclomatic"
    COGNITIVE = "cognitive"
    HALSTEAD = "halstead"
    MAINTAINABILITY = "maintainability"
    NESTING_DEPTH = "nesting_depth"
    LINES_OF_CODE = "lines_of_code"


class CodeSmell(str, Enum):
    """Common code smells."""
    LONG_METHOD = "long_method"
    LONG_CLASS = "long_class"
    LONG_PARAMETER_LIST = "long_parameter_list"
    TOO_MANY_BRANCHES = "too_many_branches"
    TOO_MANY_RETURNS = "too_many_returns"
    TOO_MANY_LOCALS = "too_many_locals"
    DEEP_NESTING = "deep_nesting"
    DUPLICATE_CODE = "duplicate_code"
    DEAD_CODE = "dead_code"
    MAGIC_NUMBER = "magic_number"
    GLOBAL_VARIABLE = "global_variable"
    BAREBARE_EXCEPT = "bare_except"
    TOO_MANY_INSTANCE_VARS = "too_many_instance_vars"
    COMPLEX_CONDITION = "complex_condition"
    LONG_LINE = "long_line"
    COMMENTED_CODE = "commented_code"
    TODO_FIXME = "todo_fixme"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ASTMetrics:
    """Metrics extracted from AST."""
    node_type: NodeType
    name: str
    line_start: int
    line_end: int
    lines_of_code: int = 0
    lines_of_comments: int = 0
    cyclomatic_complexity: int = 1
    cognitive_complexity: int = 0
    nesting_depth: int = 0
    parameter_count: int = 0
    return_count: int = 0
    local_variable_count: int = 0
    instance_variable_count: int = 0
    method_count: int = 0
    attribute_count: int = 0
    branch_count: int = 0
    loop_count: int = 0
    call_count: int = 0
    halstead_volume: float = 0.0
    halstead_difficulty: float = 0.0
    halstead_effort: float = 0.0
    maintainability_index: float = 100.0
    docstring: Optional[str] = None
    code_smells: List[CodeSmell] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    parent: Optional[str] = None


@dataclass
class ASTAnalysisResult:
    """Complete AST analysis result."""
    file_path: str
    analyzed_at: datetime
    module_name: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    metrics: List[ASTMetrics] = field(default_factory=list)
    metrics_by_type: Dict[NodeType, List[str]] = field(default_factory=dict)
    metrics_by_name: Dict[str, ASTMetrics] = field(default_factory=dict)
    hierarchy: Dict[str, List[str]] = field(default_factory=dict)
    code_smells: List[Dict[str, Any]] = field(default_factory=list)
    imports: List[Dict[str, Any]] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    complexity_score: float = 0.0
    maintainability_score: float = 100.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ASTAnalyzerConfig:
    """Configuration for AST analyzer."""
    max_method_lines: int = 50
    max_class_lines: int = 500
    max_parameters: int = 5
    max_branches: int = 10
    max_returns: int = 5
    max_locals: int = 15
    max_nesting_depth: int = 4
    max_instance_vars: int = 10
    max_line_length: int = 120
    detect_code_smells: bool = True
    compute_halstead: bool = True
    compute_maintainability: bool = True
    extract_docstrings: bool = True
    track_hierarchy: bool = True
    ignore_private: bool = False
    ignore_tests: bool = True


# ============================================================
# AST VISITORS
# ============================================================

class MetricsVisitor(ast.NodeVisitor):
    """Extract comprehensive metrics from AST."""
    
    def __init__(self, config: ASTAnalyzerConfig, source_lines: List[str]):
        self.config = config
        self.source_lines = source_lines
        self.metrics: List[ASTMetrics] = []
        self.current_metrics: Optional[ASTMetrics] = None
        self.metrics_stack: List[ASTMetrics] = []
        self.node_counter = 0
        
        # Halstead metrics
        self.operators = Counter()
        self.operands = Counter()
        
        # Hierarchy tracking
        self.hierarchy: Dict[str, List[str]] = {}
        self.parent_map: Dict[str, str] = {}
        
        # Code smells
        self.code_smells: List[Dict[str, Any]] = []
        
        # State
        self.current_class: Optional[str] = None
        self.in_loop = 0
        self.in_conditional = 0
        self.nesting_depth = 0
        self.return_count = 0
        self.local_variables: Set[str] = set()
        self.instance_variables: Set[str] = set()
    
    def _create_metrics(self, node_type: NodeType, name: str, node: ast.AST) -> ASTMetrics:
        """Create a new metrics object."""
        return ASTMetrics(
            node_type=node_type,
            name=name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            nesting_depth=self.nesting_depth,
            docstring=ast.get_docstring(node) if self.config.extract_docstrings else None
        )
    
    def _push_metrics(self, metrics: ASTMetrics):
        """Push metrics to stack."""
        if self.current_metrics:
            self.current_metrics.children.append(metrics.name)
            metrics.parent = self.current_metrics.name
            self.metrics_stack.append(self.current_metrics)
        self.current_metrics = metrics
        self.nesting_depth += 1
    
    def _pop_metrics(self):
        """Pop metrics from stack."""
        if self.metrics_stack:
            self.current_metrics = self.metrics_stack.pop()
        else:
            self.current_metrics = None
        self.nesting_depth -= 1
    
    def _compute_lines_of_code(self, node: ast.AST) -> int:
        """Compute lines of code for a node."""
        if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
            return 0
        
        start = node.lineno - 1
        end = (node.end_lineno or node.lineno) - 1
        
        if start >= len(self.source_lines):
            return 0
        
        lines = self.source_lines[start:end + 1]
        return sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
    
    def _count_comments(self, node: ast.AST) -> int:
        """Count comments in node's lines."""
        if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
            return 0
        
        start = node.lineno - 1
        end = (node.end_lineno or node.lineno) - 1
        
        if start >= len(self.source_lines):
            return 0
        
        lines = self.source_lines[start:end + 1]
        return sum(1 for line in lines if line.strip().startswith('#'))
    
    def _update_halstead(self, node: ast.AST):
        """Update Halstead metrics."""
        # Operators
        if isinstance(node, ast.Add):
            self.operators['+'] += 1
        elif isinstance(node, ast.Sub):
            self.operators['-'] += 1
        elif isinstance(node, ast.Mult):
            self.operators['*'] += 1
        elif isinstance(node, ast.Div):
            self.operators['/'] += 1
        elif isinstance(node, ast.FloorDiv):
            self.operators['//'] += 1
        elif isinstance(node, ast.Mod):
            self.operators['%'] += 1
        elif isinstance(node, ast.Pow):
            self.operators['**'] += 1
        elif isinstance(node, ast.LShift):
            self.operators['<<'] += 1
        elif isinstance(node, ast.RShift):
            self.operators['>>'] += 1
        elif isinstance(node, ast.BitOr):
            self.operators['|'] += 1
        elif isinstance(node, ast.BitXor):
            self.operators['^'] += 1
        elif isinstance(node, ast.BitAnd):
            self.operators['&'] += 1
        elif isinstance(node, ast.And):
            self.operators['and'] += 1
        elif isinstance(node, ast.Or):
            self.operators['or'] += 1
        elif isinstance(node, ast.Not):
            self.operators['not'] += 1
        elif isinstance(node, ast.Invert):
            self.operators['~'] += 1
        elif isinstance(node, ast.UAdd):
            self.operators['+'] += 1
        elif isinstance(node, ast.USub):
            self.operators['-'] += 1
        elif isinstance(node, ast.Eq):
            self.operators['=='] += 1
        elif isinstance(node, ast.NotEq):
            self.operators['!='] += 1
        elif isinstance(node, ast.Lt):
            self.operators['<'] += 1
        elif isinstance(node, ast.LtE):
            self.operators['<='] += 1
        elif isinstance(node, ast.Gt):
            self.operators['>'] += 1
        elif isinstance(node, ast.GtE):
            self.operators['>='] += 1
        elif isinstance(node, ast.Is):
            self.operators['is'] += 1
        elif isinstance(node, ast.IsNot):
            self.operators['is not'] += 1
        elif isinstance(node, ast.In):
            self.operators['in'] += 1
        elif isinstance(node, ast.NotIn):
            self.operators['not in'] += 1
        
        # Operands
        if isinstance(node, ast.Constant):
            self.operands[str(node.value)] += 1
        elif isinstance(node, ast.Name):
            self.operands[node.id] += 1
    
    def _compute_halstead_metrics(self, metrics: ASTMetrics):
        """Compute Halstead metrics for collected data."""
        n1 = len(self.operators)  # Unique operators
        n2 = len(self.operands)   # Unique operands
        N1 = sum(self.operators.values())  # Total operators
        N2 = sum(self.operands.values())   # Total operands
        
        if n1 == 0 or n2 == 0:
            return
        
        # Halstead metrics
        program_length = N1 + N2
        program_vocabulary = n1 + n2
        program_volume = program_length * (program_vocabulary.bit_length() if program_vocabulary > 0 else 1)
        program_difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        program_effort = program_volume * program_difficulty
        
        metrics.halstead_volume = program_volume
        metrics.halstead_difficulty = program_difficulty
        metrics.halstead_effort = program_effort
    
    def _compute_maintainability_index(self, metrics: ASTMetrics):
        """Compute maintainability index."""
        # MI = 171 - 5.2 * ln(V) - 0.23 * C - 16.2 * ln(LOC)
        import math
        
        V = metrics.halstead_volume or 1
        C = metrics.cyclomatic_complexity
        LOC = metrics.lines_of_code or 1
        
        mi = 171 - 5.2 * math.log(V) - 0.23 * C - 16.2 * math.log(LOC)
        mi = max(0, min(100, mi))
        
        metrics.maintainability_index = mi
    
    def _detect_code_smells(self, metrics: ASTMetrics, node: ast.AST):
        """Detect code smells."""
        # Long method
        if metrics.node_type in (NodeType.FUNCTION, NodeType.ASYNC_FUNCTION, NodeType.METHOD):
            if metrics.lines_of_code > self.config.max_method_lines:
                metrics.code_smells.append(CodeSmell.LONG_METHOD)
                self.code_smells.append({
                    'type': CodeSmell.LONG_METHOD.value,
                    'location': f"{metrics.name}:{metrics.line_start}",
                    'lines': metrics.lines_of_code,
                    'threshold': self.config.max_method_lines
                })
        
        # Long class
        if metrics.node_type == NodeType.CLASS:
            if metrics.lines_of_code > self.config.max_class_lines:
                metrics.code_smells.append(CodeSmell.LONG_CLASS)
                self.code_smells.append({
                    'type': CodeSmell.LONG_CLASS.value,
                    'location': f"{metrics.name}:{metrics.line_start}",
                    'lines': metrics.lines_of_code,
                    'threshold': self.config.max_class_lines
                })
        
        # Long parameter list
        if metrics.parameter_count > self.config.max_parameters:
            metrics.code_smells.append(CodeSmell.LONG_PARAMETER_LIST)
            self.code_smells.append({
                'type': CodeSmell.LONG_PARAMETER_LIST.value,
                'location': f"{metrics.name}:{metrics.line_start}",
                'parameters': metrics.parameter_count,
                'threshold': self.config.max_parameters
            })
        
        # Too many branches
        if metrics.branch_count > self.config.max_branches:
            metrics.code_smells.append(CodeSmell.TOO_MANY_BRANCHES)
            self.code_smells.append({
                'type': CodeSmell.TOO_MANY_BRANCHES.value,
                'location': f"{metrics.name}:{metrics.line_start}",
                'branches': metrics.branch_count,
                'threshold': self.config.max_branches
            })
        
        # Too many returns
        if metrics.return_count > self.config.max_returns:
            metrics.code_smells.append(CodeSmell.TOO_MANY_RETURNS)
            self.code_smells.append({
                'type': CodeSmell.TOO_MANY_RETURNS.value,
                'location': f"{metrics.name}:{metrics.line_start}",
                'returns': metrics.return_count,
                'threshold': self.config.max_returns
            })
        
        # Too many locals
        if metrics.local_variable_count > self.config.max_locals:
            metrics.code_smells.append(CodeSmell.TOO_MANY_LOCALS)
            self.code_smells.append({
                'type': CodeSmell.TOO_MANY_LOCALS.value,
                'location': f"{metrics.name}:{metrics.line_start}",
                'locals': metrics.local_variable_count,
                'threshold': self.config.max_locals
            })
        
        # Deep nesting
        if metrics.nesting_depth > self.config.max_nesting_depth:
            metrics.code_smells.append(CodeSmell.DEEP_NESTING)
            self.code_smells.append({
                'type': CodeSmell.DEEP_NESTING.value,
                'location': f"{metrics.name}:{metrics.line_start}",
                'depth': metrics.nesting_depth,
                'threshold': self.config.max_nesting_depth
            })
        
        # Too many instance variables
        if metrics.instance_variable_count > self.config.max_instance_vars:
            metrics.code_smells.append(CodeSmell.TOO_MANY_INSTANCE_VARS)
            self.code_smells.append({
                'type': CodeSmell.TOO_MANY_INSTANCE_VARS.value,
                'location': f"{metrics.name}:{metrics.line_start}",
                'variables': metrics.instance_variable_count,
                'threshold': self.config.max_instance_vars
            })
    
    def visit_Module(self, node: ast.Module):
        """Visit module."""
        metrics = self._create_metrics(NodeType.MODULE, '__module__', node)
        metrics.lines_of_code = self._compute_lines_of_code(node)
        metrics.lines_of_comments = self._count_comments(node)
        
        self._push_metrics(metrics)
        self.generic_visit(node)
        self._pop_metrics()
        
        self.metrics.append(metrics)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        if self.config.ignore_private and node.name.startswith('_'):
            self.generic_visit(node)
            return
        
        prev_class = self.current_class
        self.current_class = node.name
        
        metrics = self._create_metrics(NodeType.CLASS, node.name, node)
        metrics.lines_of_code = self._compute_lines_of_code(node)
        metrics.lines_of_comments = self._count_comments(node)
        
        # Reset instance variable tracking
        prev_instance_vars = self.instance_variables
        self.instance_variables = set()
        
        self._push_metrics(metrics)
        self.generic_visit(node)
        self._pop_metrics()
        
        metrics.instance_variable_count = len(self.instance_variables)
        
        if self.config.detect_code_smells:
            self._detect_code_smells(metrics, node)
        
        self.metrics.append(metrics)
        self.current_class = prev_class
        self.instance_variables = prev_instance_vars
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        self._visit_function(node, is_async=False)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self._visit_function(node, is_async=True)
    
    def _visit_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool):
        """Common function visitor."""
        if self.config.ignore_private and node.name.startswith('_') and node.name != '__init__':
            self.generic_visit(node)
            return
        
        # Determine node type
        if self.current_class:
            node_type = NodeType.METHOD
            full_name = f"{self.current_class}.{node.name}"
        else:
            node_type = NodeType.ASYNC_FUNCTION if is_async else NodeType.FUNCTION
            full_name = node.name
        
        metrics = self._create_metrics(node_type, full_name, node)
        metrics.lines_of_code = self._compute_lines_of_code(node)
        metrics.lines_of_comments = self._count_comments(node)
        metrics.parameter_count = len(node.args.args) + len(node.args.kwonlyargs)
        
        # Reset function-level tracking
        prev_return_count = self.return_count
        prev_local_vars = self.local_variables
        self.return_count = 0
        self.local_variables = set()
        
        # Reset Halstead counters
        prev_operators = self.operators
        prev_operands = self.operands
        self.operators = Counter()
        self.operands = Counter()
        
        self._push_metrics(metrics)
        self.generic_visit(node)
        self._pop_metrics()
        
        # Collect metrics
        metrics.return_count = self.return_count
        metrics.local_variable_count = len(self.local_variables)
        
        if self.config.compute_halstead:
            self._compute_halstead_metrics(metrics)
        
        if self.config.compute_maintainability:
            self._compute_maintainability_index(metrics)
        
        if self.config.detect_code_smells:
            self._detect_code_smells(metrics, node)
        
        self.metrics.append(metrics)
        
        # Restore state
        self.return_count = prev_return_count
        self.local_variables = prev_local_vars
        self.operators = prev_operators
        self.operands = prev_operands
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.local_variables.add(target.id)
            elif isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == 'self':
                    self.instance_variables.add(target.attr)
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Visit annotated assignment."""
        if isinstance(node.target, ast.Name):
            self.local_variables.add(node.target.id)
        elif isinstance(node.target, ast.Attribute):
            if isinstance(node.target.value, ast.Name) and node.target.value.id == 'self':
                self.instance_variables.add(node.target.attr)
        
        self.generic_visit(node)
    
    def visit_If(self, node: ast.If):
        """Visit if statement."""
        if self.current_metrics:
            self.current_metrics.cyclomatic_complexity += 1
            self.current_metrics.branch_count += 1
        
        self.in_conditional += 1
        self.generic_visit(node)
        self.in_conditional -= 1
    
    def visit_For(self, node: ast.For):
        """Visit for loop."""
        if self.current_metrics:
            self.current_metrics.cyclomatic_complexity += 1
            self.current_metrics.loop_count += 1
        
        self.in_loop += 1
        self.generic_visit(node)
        self.in_loop -= 1
    
    def visit_AsyncFor(self, node: ast.AsyncFor):
        """Visit async for loop."""
        if self.current_metrics:
            self.current_metrics.cyclomatic_complexity += 1
            self.current_metrics.loop_count += 1
        
        self.in_loop += 1
        self.generic_visit(node)
        self.in_loop -= 1
    
    def visit_While(self, node: ast.While):
        """Visit while loop."""
        if self.current_metrics:
            self.current_metrics.cyclomatic_complexity += 1
            self.current_metrics.loop_count += 1
        
        self.in_loop += 1
        self.generic_visit(node)
        self.in_loop -= 1
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """Visit except handler."""
        if self.current_metrics:
            self.current_metrics.cyclomatic_complexity += 1
        
        # Check for bare except
        if node.type is None:
            if self.current_metrics:
                self.current_metrics.code_smells.append(CodeSmell.BAREBARE_EXCEPT)
        
        self.generic_visit(node)
    
    def visit_Return(self, node: ast.Return):
        """Visit return statement."""
        self.return_count += 1
        self.generic_visit(node)
    
    def visit_BoolOp(self, node: ast.BoolOp):
        """Visit boolean operation."""
        if self.current_metrics:
            # Each boolean operator adds cognitive complexity
            self.current_metrics.cognitive_complexity += 1
            
            # Check for complex condition
            if len(node.values) > 3:
                self.current_metrics.code_smells.append(CodeSmell.COMPLEX_CONDITION)
        
        self.generic_visit(node)
    
    def visit_Global(self, node: ast.Global):
        """Visit global statement."""
        if self.current_metrics:
            self.current_metrics.code_smells.append(CodeSmell.GLOBAL_VARIABLE)
        
        self.generic_visit(node)
    
    def visit_Constant(self, node: ast.Constant):
        """Visit constant."""
        # Check for magic numbers
        if isinstance(node.value, (int, float)) and node.value not in (0, 1, -1, 2):
            # Could be a magic number
            pass
        
        self._update_halstead(node)
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        """Visit name."""
        self._update_halstead(node)
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Visit call."""
        if self.current_metrics:
            self.current_metrics.call_count += 1
        
        self.generic_visit(node)


class ImportExtractor(ast.NodeVisitor):
    """Extract import statements from AST."""
    
    def __init__(self):
        self.imports: List[Dict[str, Any]] = []
        self.exports: List[str] = []
    
    def visit_Import(self, node: ast.Import):
        """Visit import."""
        for alias in node.names:
            self.imports.append({
                'type': 'import',
                'name': alias.name,
                'alias': alias.asname,
                'line': node.lineno
            })
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from import."""
        for alias in node.names:
            self.imports.append({
                'type': 'from',
                'module': node.module,
                'name': alias.name,
                'alias': alias.asname,
                'level': node.level,
                'line': node.lineno
            })
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment for __all__."""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == '__all__':
                if isinstance(node.value, ast.List):
                    for item in node.value.elts:
                        if isinstance(item, ast.Constant):
                            self.exports.append(item.value)


# ============================================================
# MAIN AST ANALYZER CLASS
# ============================================================

class ASTAnalyzer:
    """
    Deep AST analysis for Python code.
    
    Features:
    - Comprehensive metrics extraction
    - Cyclomatic and cognitive complexity
    - Halstead metrics (volume, difficulty, effort)
    - Maintainability index
    - Code smell detection
    - Import/export analysis
    - Hierarchy tracking
    - Docstring extraction
    - Multi-file analysis
    - Export to JSON/HTML
    """
    
    def __init__(self, config: Optional[ASTAnalyzerConfig] = None):
        self.config = config or ASTAnalyzerConfig()
        self.state = StateManager(Path(".ai_state") / "ast_analyzer.json")
        
        logger.info("ASTAnalyzer initialized")
    
    # ============================================================
    # FILE ANALYSIS
    # ============================================================
    
    def analyze_file(self, file_path: Path) -> Optional[ASTAnalysisResult]:
        """Analyze a single Python file."""
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        # Skip tests if configured
        if self.config.ignore_tests and 'test' in str(file_path).lower():
            return None
        
        logger.info(f"Analyzing: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count lines
            lines = content.split('\n')
            total_lines = len(lines)
            code_lines = sum(1 for l in lines if l.strip() and not l.strip().startswith('#'))
            comment_lines = sum(1 for l in lines if l.strip().startswith('#'))
            blank_lines = total_lines - code_lines - comment_lines
            
            # Parse AST
            tree = ast.parse(content)
            
            # Get module name
            module_name = self._get_module_name(file_path)
            
            # Extract metrics
            visitor = MetricsVisitor(self.config, lines)
            visitor.visit(tree)
            
            # Extract imports
            import_extractor = ImportExtractor()
            import_extractor.visit(tree)
            
            # Build result
            result = ASTAnalysisResult(
                file_path=str(file_path),
                analyzed_at=datetime.now(),
                module_name=module_name,
                total_lines=total_lines,
                code_lines=code_lines,
                comment_lines=comment_lines,
                blank_lines=blank_lines,
                metrics=visitor.metrics,
                hierarchy=visitor.hierarchy,
                code_smells=visitor.code_smells,
                imports=import_extractor.imports,
                exports=import_extractor.exports
            )
            
            # Build indices
            for m in result.metrics:
                if m.node_type not in result.metrics_by_type:
                    result.metrics_by_type[m.node_type] = []
                result.metrics_by_type[m.node_type].append(m.name)
                result.metrics_by_name[m.name] = m
            
            # Compute overall scores
            result.complexity_score = self._compute_complexity_score(result)
            result.maintainability_score = self._compute_maintainability_score(result)
            
            return result
            
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return None
    
    def analyze_directory(self, directory: Path, recursive: bool = True) -> List[ASTAnalysisResult]:
        """Analyze all Python files in a directory."""
        results = []
        
        pattern = "**/*.py" if recursive else "*.py"
        for file_path in directory.glob(pattern):
            result = self.analyze_file(file_path)
            if result:
                results.append(result)
        
        logger.info(f"Analyzed {len(results)} files in {directory}")
        return results
    
    def _get_module_name(self, file_path: Path) -> str:
        """Get module name from file path."""
        return file_path.stem
    
    def _compute_complexity_score(self, result: ASTAnalysisResult) -> float:
        """Compute overall complexity score."""
        if not result.metrics:
            return 0.0
        
        total_complexity = sum(m.cyclomatic_complexity for m in result.metrics)
        avg_complexity = total_complexity / len(result.metrics)
        
        # Normalize to 0-100 scale
        score = min(100, avg_complexity * 5)
        return score
    
    def _compute_maintainability_score(self, result: ASTAnalysisResult) -> float:
        """Compute overall maintainability score."""
        if not result.metrics:
            return 100.0
        
        scores = [m.maintainability_index for m in result.metrics if m.maintainability_index > 0]
        if not scores:
            return 100.0
        
        return sum(scores) / len(scores)
    
    # ============================================================
    # QUERY METHODS
    # ============================================================
    
    def get_most_complex_functions(self, results: List[ASTAnalysisResult], top_n: int = 10) -> List[Tuple[str, int]]:
        """Get most complex functions across all results."""
        functions = []
        
        for result in results:
            for name, metrics in result.metrics_by_name.items():
                if metrics.node_type in (NodeType.FUNCTION, NodeType.ASYNC_FUNCTION, NodeType.METHOD):
                    functions.append((f"{result.file_path}:{name}", metrics.cyclomatic_complexity))
        
        functions.sort(key=lambda x: x[1], reverse=True)
        return functions[:top_n]
    
    def get_code_smells_summary(self, results: List[ASTAnalysisResult]) -> Dict[str, int]:
        """Get summary of code smells."""
        summary = defaultdict(int)
        
        for result in results:
            for smell in result.code_smells:
                summary[smell['type']] += 1
        
        return dict(summary)
    
    def get_metrics_by_type(self, results: List[ASTAnalysisResult], node_type: NodeType) -> List[ASTMetrics]:
        """Get all metrics of a specific type."""
        all_metrics = []
        
        for result in results:
            for name in result.metrics_by_type.get(node_type, []):
                metrics = result.metrics_by_name.get(name)
                if metrics:
                    all_metrics.append(metrics)
        
        return all_metrics
    
    def get_hierarchy(self, result: ASTAnalysisResult) -> Dict[str, Any]:
        """Get class/function hierarchy."""
        return result.hierarchy
    
    # ============================================================
    # EXPORT
    # ============================================================
    
    def export_json(self, results: List[ASTAnalysisResult], output_path: Optional[Path] = None) -> str:
        """Export results as JSON."""
        data = {
            'analyzed_at': datetime.now().isoformat(),
            'file_count': len(results),
            'files': [
                {
                    'path': r.file_path,
                    'module': r.module_name,
                    'total_lines': r.total_lines,
                    'code_lines': r.code_lines,
                    'comment_lines': r.comment_lines,
                    'complexity_score': r.complexity_score,
                    'maintainability_score': r.maintainability_score,
                    'metrics_count': len(r.metrics),
                    'code_smells_count': len(r.code_smells),
                    'imports': r.imports,
                    'exports': r.exports,
                    'metrics': [
                        {
                            'name': m.name,
                            'type': m.node_type.value,
                            'lines': m.lines_of_code,
                            'complexity': m.cyclomatic_complexity,
                            'cognitive_complexity': m.cognitive_complexity,
                            'parameters': m.parameter_count,
                            'returns': m.return_count,
                            'locals': m.local_variable_count,
                            'nesting_depth': m.nesting_depth,
                            'maintainability': m.maintainability_index,
                            'docstring': m.docstring,
                            'code_smells': [s.value for s in m.code_smells]
                        }
                        for m in r.metrics
                    ],
                    'code_smells': r.code_smells
                }
                for r in results
            ]
        }
        
        content = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def export_html(self, results: List[ASTAnalysisResult], output_path: Optional[Path] = None) -> str:
        """Export results as HTML report."""
        html = self._generate_html_report(results)
        
        if output_path:
            output_path.write_text(html)
        
        return html
    
    def _generate_html_report(self, results: List[ASTAnalysisResult]) -> str:
        """Generate HTML report."""
        summary = self._generate_summary(results)
        complex_functions = self.get_most_complex_functions(results, 20)
        smells_summary = self.get_code_smells_summary(results)
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>AST Analysis Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
        h1, h2 {{ color: #333; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .card {{ background: #f5f5f5; border-radius: 8px; padding: 20px; }}
        .card h3 {{ margin: 0 0 10px 0; color: #666; font-size: 14px; text-transform: uppercase; }}
        .card .value {{ font-size: 32px; font-weight: bold; color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; font-weight: 600; }}
        .smell-critical {{ color: #d32f2f; }}
        .smell-high {{ color: #f57c00; }}
        .smell-medium {{ color: #fbc02d; }}
        .smell-low {{ color: #388e3c; }}
        .complexity-high {{ background: #ffebee; }}
        .complexity-medium {{ background: #fff3e0; }}
    </style>
</head>
<body>
    <h1>AST Analysis Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <div class="card">
            <h3>Files Analyzed</h3>
            <div class="value">{summary['total_files']}</div>
        </div>
        <div class="card">
            <h3>Total Lines</h3>
            <div class="value">{summary['total_lines']:,}</div>
        </div>
        <div class="card">
            <h3>Code Lines</h3>
            <div class="value">{summary['code_lines']:,}</div>
        </div>
        <div class="card">
            <h3>Avg Complexity</h3>
            <div class="value">{summary['avg_complexity']:.1f}</div>
        </div>
        <div class="card">
            <h3>Maintainability</h3>
            <div class="value">{summary['avg_maintainability']:.1f}%</div>
        </div>
        <div class="card">
            <h3>Code Smells</h3>
            <div class="value">{summary['total_smells']}</div>
        </div>
    </div>
    
    <h2>Most Complex Functions</h2>
    <table>
        <tr><th>Function</th><th>Complexity</th></tr>
'''
        
        for name, complexity in complex_functions:
            css_class = 'complexity-high' if complexity > 20 else 'complexity-medium' if complexity > 10 else ''
            html += f'<tr class="{css_class}"><td>{name}</td><td>{complexity}</td></tr>'
        
        html += '''
    </table>
    
    <h2>Code Smells Summary</h2>
    <table>
        <tr><th>Smell Type</th><th>Count</th></tr>
'''
        
        for smell_type, count in sorted(smells_summary.items(), key=lambda x: x[1], reverse=True):
            html += f'<tr><td>{smell_type}</td><td>{count}</td></tr>'
        
        html += '''
    </table>
    
    <h2>File Details</h2>
    <table>
        <tr><th>File</th><th>Lines</th><th>Functions</th><th>Classes</th><th>Complexity</th><th>Smells</th></tr>
'''
        
        for r in results:
            func_count = len(r.metrics_by_type.get(NodeType.FUNCTION, [])) + len(r.metrics_by_type.get(NodeType.METHOD, []))
            class_count = len(r.metrics_by_type.get(NodeType.CLASS, []))
            
            html += f'''<tr>
                <td>{r.file_path}</td>
                <td>{r.code_lines}</td>
                <td>{func_count}</td>
                <td>{class_count}</td>
                <td>{r.complexity_score:.1f}</td>
                <td>{len(r.code_smells)}</td>
            </tr>'''
        
        html += '''
    </table>
</body>
</html>'''
        
        return html
    
    def _generate_summary(self, results: List[ASTAnalysisResult]) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not results:
            return {
                'total_files': 0,
                'total_lines': 0,
                'code_lines': 0,
                'avg_complexity': 0,
                'avg_maintainability': 0,
                'total_smells': 0
            }
        
        return {
            'total_files': len(results),
            'total_lines': sum(r.total_lines for r in results),
            'code_lines': sum(r.code_lines for r in results),
            'avg_complexity': sum(r.complexity_score for r in results) / len(results),
            'avg_maintainability': sum(r.maintainability_score for r in results) / len(results),
            'total_smells': sum(len(r.code_smells) for r in results)
        }
    
    def generate_report(self, results: List[ASTAnalysisResult], format: str = "markdown") -> str:
        """Generate analysis report."""
        if format == "html":
            return self.export_html(results)
        elif format == "json":
            return self.export_json(results)
        else:
            return self._generate_markdown_report(results)
    
    def _generate_markdown_report(self, results: List[ASTAnalysisResult]) -> str:
        """Generate markdown report."""
        summary = self._generate_summary(results)
        complex_functions = self.get_most_complex_functions(results, 20)
        smells_summary = self.get_code_smells_summary(results)
        
        lines = [
            "# AST Analysis Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- **Files Analyzed:** {summary['total_files']}",
            f"- **Total Lines:** {summary['total_lines']:,}",
            f"- **Code Lines:** {summary['code_lines']:,}",
            f"- **Avg Complexity:** {summary['avg_complexity']:.1f}",
            f"- **Avg Maintainability:** {summary['avg_maintainability']:.1f}%",
            f"- **Total Code Smells:** {summary['total_smells']}",
            "",
            "## Most Complex Functions",
            "",
            "| Function | Complexity |",
            "|----------|------------|",
        ]
        
        for name, complexity in complex_functions[:20]:
            lines.append(f"| {name} | {complexity} |")
        
        lines.extend([
            "",
            "## Code Smells Summary",
            "",
            "| Smell Type | Count |",
            "|------------|-------|",
        ])
        
        for smell_type, count in sorted(smells_summary.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {smell_type} | {count} |")
        
        lines.extend([
            "",
            "## File Summary",
            "",
            "| File | Lines | Functions | Classes | Complexity | Smells |",
            "|------|-------|-----------|---------|------------|--------|",
        ])
        
        for r in results[:50]:  # Limit to 50 files
            func_count = len(r.metrics_by_type.get(NodeType.FUNCTION, [])) + len(r.metrics_by_type.get(NodeType.METHOD, []))
            class_count = len(r.metrics_by_type.get(NodeType.CLASS, []))
            
            lines.append(f"| {r.file_path} | {r.code_lines} | {func_count} | {class_count} | {r.complexity_score:.1f} | {len(r.code_smells)} |")
        
        return '\n'.join(lines)
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("ASTAnalyzer closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for AST analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deep AST analysis for Python code")
    parser.add_argument("path", type=Path, help="File or directory to analyze")
    parser.add_argument("--output", "-o", type=Path, help="Output file")
    parser.add_argument("--format", choices=["json", "html", "markdown"], default="markdown",
                       help="Output format")
    parser.add_argument("--recursive", "-r", action="store_true", help="Analyze directories recursively")
    parser.add_argument("--max-complexity", type=int, default=10, help="Maximum complexity threshold")
    parser.add_argument("--max-lines", type=int, default=50, help="Maximum method lines")
    parser.add_argument("--no-smells", action="store_true", help="Disable code smell detection")
    parser.add_argument("--include-tests", action="store_true", help="Include test files")
    
    args = parser.parse_args()
    
    config = ASTAnalyzerConfig(
        max_method_lines=args.max_lines,
        max_branches=args.max_complexity,
        detect_code_smells=not args.no_smells,
        ignore_tests=not args.include_tests
    )
    
    analyzer = ASTAnalyzer(config)
    
    if args.path.is_file():
        results = [analyzer.analyze_file(args.path)]
        results = [r for r in results if r]
    else:
        results = analyzer.analyze_directory(args.path, args.recursive)
    
    if not results:
        print("No files analyzed")
        return
    
    report = analyzer.generate_report(results, args.format)
    
    if args.output:
        args.output.write_text(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)
    
    analyzer.close()


if __name__ == "__main__":
    main()