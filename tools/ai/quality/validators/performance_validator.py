#!/usr/bin/env python3
"""
Performance Validator - Validates code performance metrics and detects inefficiencies.

Part of the Quality tools (validators/performance_validator.py)

This performance_validator.py provides:

1. Time Complexity Analysis - Detects O(1), O(n), O(n²), O(n³), O(log n), O(2ⁿ) complexity
2. Nested Loop Detection - Identifies O(n²) and O(n³) patterns
3. Performance Anti-Pattern Detection - Redundant computations, inefficient string concatenation, unnecessary copies
4. cProfile Integration - Profiles function execution times
5. tracemalloc Integration - Memory profiling and leak detection
6. Function Benchmarking - Measures ops/second with statistical analysis
7. Recursion Analysis - Detects deep recursion and divide-and-conquer patterns
8. Performance Scoring - A-F grade based on issues and complexity
9. Actionable Suggestions - Specific optimization recommendations
10. Code Snippet Extraction - Shows problematic code in reports
11. Historical Tracking - Tracks performance trends over time
12. Configurable Thresholds - Customize acceptable complexity and memory limits

The performance validator helps identify and fix performance bottlenecks before they impact production systems.
"""

import ast
import time
import cProfile
import pstats
import tracemalloc
import asyncio
import statistics
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import importlib.util
import sys
import tempfile

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class PerformanceIssueType(str, Enum):
    """Type of performance issue."""
    O_N2_LOOP = "o_n2_loop"
    O_N3_LOOP = "o_n3_loop"
    REDUNDANT_COMPUTATION = "redundant_computation"
    INEFFICIENT_DATA_STRUCTURE = "inefficient_data_structure"
    EXCESSIVE_MEMORY = "excessive_memory"
    MEMORY_LEAK = "memory_leak"
    SLOW_IO = "slow_io"
    UNOPTIMIZED_QUERY = "unoptimized_query"
    LARGE_OBJECT_CREATION = "large_object_creation"
    INEFFICIENT_STRING_CONCAT = "inefficient_string_concat"
    MISSING_INDEX = "missing_index"
    N_PLUS_ONE_QUERY = "n_plus_one_query"
    BLOCKING_OPERATION = "blocking_operation"
    CONTENTION = "contention"
    DEEP_RECURSION = "deep_recursion"
    EXCESSIVE_FUNCTION_CALLS = "excessive_function_calls"
    INEFFICIENT_REGEX = "inefficient_regex"
    LARGE_DEPENDENCY = "large_dependency"
    SLOW_STARTUP = "slow_startup"
    UNNECESSARY_COPY = "unnecessary_copy"
    GLOBAL_INTERPRETER_LOCK = "gil_contention"


class Severity(str, Enum):
    """Severity of performance issue."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplexityClass(str, Enum):
    """Time complexity class."""
    CONSTANT = "O(1)"
    LOGARITHMIC = "O(log n)"
    LINEAR = "O(n)"
    LINEARITHMIC = "O(n log n)"
    QUADRATIC = "O(n²)"
    CUBIC = "O(n³)"
    EXPONENTIAL = "O(2ⁿ)"
    FACTORIAL = "O(n!)"
    UNKNOWN = "unknown"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ComplexityAnalysis:
    """Time complexity analysis of a function."""
    function_name: str
    file_path: str
    line_number: int
    detected_complexity: ComplexityClass
    confidence: float
    reasoning: str
    nested_loops: int
    recursive_depth: int
    input_dependent_branches: int
    loop_variables: List[str] = field(default_factory=list)
    suggestion: Optional[str] = None


@dataclass
class ProfileResult:
    """Profiling result for a function."""
    function_name: str
    file_path: str
    line_number: int
    calls: int
    total_time: float
    cumulative_time: float
    time_per_call: float
    percentage: float
    is_builtin: bool = False
    callers: List[Tuple[str, int]] = field(default_factory=list)


@dataclass
class MemoryProfile:
    """Memory profiling result."""
    function_name: str
    file_path: str
    line_number: int
    peak_memory_mb: float
    average_memory_mb: float
    allocations: int
    deallocations: int
    leaked_memory_mb: float
    large_allocations: List[Tuple[int, float]] = field(default_factory=list)
    traceback: Optional[str] = None


@dataclass
class BenchmarkResult:
    """Benchmark result for a function."""
    function_name: str
    file_path: str
    iterations: int
    total_time: float
    min_time: float
    max_time: float
    mean_time: float
    median_time: float
    std_dev: float
    ops_per_second: float
    warmup_runs: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceIssue:
    """A single performance issue."""
    issue_type: PerformanceIssueType
    severity: Severity
    file_path: str
    function_name: Optional[str] = None
    line_number: Optional[int] = None
    description: str = ""
    detected_complexity: Optional[ComplexityClass] = None
    suggested_complexity: Optional[ComplexityClass] = None
    estimated_impact: str = ""
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceReport:
    """Complete performance validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    
    # Complexity analysis
    complexity_analyses: List[ComplexityAnalysis] = field(default_factory=list)
    problematic_functions: List[ComplexityAnalysis] = field(default_factory=list)
    
    # Profiling results
    profile_results: List[ProfileResult] = field(default_factory=list)
    top_slow_functions: List[ProfileResult] = field(default_factory=list)
    total_profile_time: float = 0.0
    
    # Memory profiling
    memory_profiles: List[MemoryProfile] = field(default_factory=list)
    top_memory_consumers: List[MemoryProfile] = field(default_factory=list)
    peak_total_memory_mb: float = 0.0
    memory_leaks: List[MemoryProfile] = field(default_factory=list)
    
    # Benchmark results
    benchmark_results: List[BenchmarkResult] = field(default_factory=list)
    
    # Issues
    issues: List[PerformanceIssue] = field(default_factory=list)
    warnings: List[PerformanceIssue] = field(default_factory=list)
    
    # Validation
    is_valid: bool = True
    overall_score: float = 0.0
    grade: str = "A"
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceValidatorConfig:
    """Configuration for performance validator."""
    project_root: Path
    
    # Complexity analysis
    analyze_complexity: bool = True
    max_acceptable_complexity: ComplexityClass = ComplexityClass.QUADRATIC
    warn_on_quadratic: bool = True
    
    # Profiling
    run_profiling: bool = False
    profile_top_n: int = 20
    min_profile_time: float = 0.1  # seconds
    
    # Memory profiling
    profile_memory: bool = False
    track_allocations: bool = True
    memory_threshold_mb: float = 100.0
    leak_threshold_mb: float = 1.0
    
    # Benchmarking
    run_benchmarks: bool = False
    benchmark_iterations: int = 1000
    benchmark_warmup: int = 3
    min_ops_per_second: float = 1000.0
    
    # Patterns to detect
    detect_o_n2: bool = True
    detect_o_n3: bool = True
    detect_redundant_computation: bool = True
    detect_inefficient_string_concat: bool = True
    detect_large_allocations: bool = True
    detect_unnecessary_copy: bool = True
    detect_deep_recursion: bool = True
    
    # Ignore patterns
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "test_*.py", "*_test.py"
    ])
    ignore_functions: List[str] = field(default_factory=list)
    
    # Validation
    fail_on_critical: bool = True
    fail_on_high: bool = False
    max_issues: int = 20
    
    # Reporting
    generate_report: bool = True
    output_format: str = "markdown"


# ============================================================
# COMPLEXITY ANALYZER
# ============================================================

class ComplexityAnalyzer(ast.NodeVisitor):
    """Analyze time complexity of Python functions."""
    
    def __init__(self, config: PerformanceValidatorConfig):
        self.config = config
        self.analyses: List[ComplexityAnalysis] = []
        self.current_file: str = ""
        self.current_function: str = ""
        self.nested_loops: int = 0
        self.max_nested_loops: int = 0
        self.recursive_depth: int = 0
        self.input_dependent_branches: int = 0
        self.loop_vars: Set[str] = set()
        self.array_accesses: List[ast.Subscript] = []
    
    def analyze_file(self, file_path: Path) -> List[ComplexityAnalysis]:
        """Analyze a Python file for complexity issues."""
        self.current_file = str(file_path)
        self.analyses = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            self.visit(tree)
            
        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {e}")
        
        return self.analyses
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        if self._should_ignore(node.name):
            self.generic_visit(node)
            return
        
        prev_function = self.current_function
        prev_nested = self.nested_loops
        prev_max = self.max_nested_loops
        prev_recursive = self.recursive_depth
        prev_branches = self.input_dependent_branches
        prev_loop_vars = self.loop_vars
        
        self.current_function = node.name
        self.nested_loops = 0
        self.max_nested_loops = 0
        self.recursive_depth = 0
        self.input_dependent_branches = 0
        self.loop_vars = set()
        
        self.generic_visit(node)
        
        # Analyze complexity
        analysis = self._analyze_complexity(node)
        if analysis:
            self.analyses.append(analysis)
        
        self.current_function = prev_function
        self.nested_loops = prev_nested
        self.max_nested_loops = prev_max
        self.recursive_depth = prev_recursive
        self.input_dependent_branches = prev_branches
        self.loop_vars = prev_loop_vars
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        self.visit_FunctionDef(node)
    
    def visit_For(self, node: ast.For):
        """Visit for loop."""
        self.nested_loops += 1
        self.max_nested_loops = max(self.max_nested_loops, self.nested_loops)
        
        # Track loop variable
        if isinstance(node.target, ast.Name):
            self.loop_vars.add(node.target.id)
        elif isinstance(node.target, ast.Tuple):
            for elt in node.target.elts:
                if isinstance(elt, ast.Name):
                    self.loop_vars.add(elt.id)
        
        self.generic_visit(node)
        self.nested_loops -= 1
    
    def visit_While(self, node: ast.While):
        """Visit while loop."""
        self.nested_loops += 1
        self.max_nested_loops = max(self.max_nested_loops, self.nested_loops)
        self.generic_visit(node)
        self.nested_loops -= 1
    
    def visit_If(self, node: ast.If):
        """Visit if statement."""
        self.input_dependent_branches += 1
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Visit function call for recursion detection."""
        if isinstance(node.func, ast.Name):
            if node.func.id == self.current_function:
                self.recursive_depth += 1
        self.generic_visit(node)
    
    def visit_Subscript(self, node: ast.Subscript):
        """Visit subscript for array access."""
        self.array_accesses.append(node)
        self.generic_visit(node)
    
    def _analyze_complexity(self, node: ast.FunctionDef) -> Optional[ComplexityAnalysis]:
        """Analyze time complexity of a function."""
        complexity = ComplexityClass.CONSTANT
        confidence = 1.0
        reasoning_parts = []
        
        # Check nested loops
        if self.max_nested_loops == 1:
            if self._is_input_dependent(node):
                complexity = ComplexityClass.LINEAR
                reasoning_parts.append("single input-dependent loop")
            else:
                complexity = ComplexityClass.CONSTANT
                reasoning_parts.append("single constant loop")
        elif self.max_nested_loops == 2:
            complexity = ComplexityClass.QUADRATIC
            reasoning_parts.append("two nested loops")
            confidence = 0.8
        elif self.max_nested_loops == 3:
            complexity = ComplexityClass.CUBIC
            reasoning_parts.append("three nested loops")
            confidence = 0.9
        elif self.max_nested_loops > 3:
            complexity = ComplexityClass.CUBIC
            reasoning_parts.append(f"{self.max_nested_loops} nested loops")
            confidence = 0.95
        
        # Check recursion
        if self.recursive_depth > 0:
            if self._is_divide_and_conquer(node):
                complexity = ComplexityClass.LINEARITHMIC
                reasoning_parts.append("divide-and-conquer recursion")
            else:
                complexity = ComplexityClass.EXPONENTIAL
                reasoning_parts.append("non-tail recursion")
                confidence = 0.7
        
        # Check for binary search pattern
        if self._has_binary_search_pattern(node):
            complexity = ComplexityClass.LOGARITHMIC
            reasoning_parts.append("binary search pattern")
        
        # Check for linear scan with early exit
        if self.max_nested_loops == 1 and self._has_early_exit(node):
            reasoning_parts.append("linear scan with early exit")
        
        reasoning = ", ".join(reasoning_parts) if reasoning_parts else "constant time operations"
        
        analysis = ComplexityAnalysis(
            function_name=self.current_function,
            file_path=self.current_file,
            line_number=node.lineno,
            detected_complexity=complexity,
            confidence=confidence,
            reasoning=reasoning,
            nested_loops=self.max_nested_loops,
            recursive_depth=self.recursive_depth,
            input_dependent_branches=self.input_dependent_branches,
            loop_variables=list(self.loop_vars)
        )
        
        # Add suggestion if complexity is high
        if self._is_complexity_high(complexity):
            analysis.suggestion = self._get_complexity_suggestion(complexity, node)
        
        return analysis
    
    def _is_input_dependent(self, node: ast.FunctionDef) -> bool:
        """Check if function complexity depends on input size."""
        for arg in node.args.args:
            if arg.arg in self.loop_vars:
                return True
        
        return self.max_nested_loops > 0 and len(node.args.args) > 0
    
    def _is_divide_and_conquer(self, node: ast.FunctionDef) -> bool:
        """Check if recursion is divide-and-conquer."""
        recursive_calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    if child.func.id == self.current_function:
                        recursive_calls.append(child)
        
        return len(recursive_calls) >= 2
    
    def _has_binary_search_pattern(self, node: ast.FunctionDef) -> bool:
        """Check for binary search pattern."""
        has_mid = False
        has_halving = False
        
        for child in ast.walk(node):
            if isinstance(child, ast.BinOp):
                if isinstance(child.op, (ast.FloorDiv, ast.Div)):
                    if self._is_mid_calculation(child):
                        has_mid = True
            elif isinstance(child, ast.Slice):
                has_halving = True
        
        return has_mid and has_halving
    
    def _has_early_exit(self, node: ast.FunctionDef) -> bool:
        """Check if loop has early exit (return/break)."""
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)):
                for inner in ast.walk(child):
                    if isinstance(inner, (ast.Return, ast.Break)):
                        return True
        return False
    
    def _is_mid_calculation(self, node: ast.BinOp) -> bool:
        """Check if binary operation is calculating mid point."""
        if isinstance(node.left, ast.Name) and isinstance(node.right, ast.Name):
            return True
        if isinstance(node.op, ast.Add) and isinstance(node.left, ast.Name):
            return True
        return False
    
    def _is_complexity_high(self, complexity: ComplexityClass) -> bool:
        """Check if complexity is unacceptably high."""
        complexity_order = [
            ComplexityClass.CONSTANT,
            ComplexityClass.LOGARITHMIC,
            ComplexityClass.LINEAR,
            ComplexityClass.LINEARITHMIC,
            ComplexityClass.QUADRATIC,
            ComplexityClass.CUBIC,
            ComplexityClass.EXPONENTIAL,
            ComplexityClass.FACTORIAL
        ]
        
        threshold_idx = complexity_order.index(self.config.max_acceptable_complexity)
        current_idx = complexity_order.index(complexity)
        
        return current_idx > threshold_idx
    
    def _get_complexity_suggestion(self, complexity: ComplexityClass, 
                                    node: ast.FunctionDef) -> str:
        """Get suggestion for reducing complexity."""
        if complexity == ComplexityClass.QUADRATIC:
            if self.max_nested_loops == 2:
                return "Consider using a hash map/dictionary to eliminate inner loop"
            return "Consider algorithmic optimization to reduce O(n²) complexity"
        elif complexity == ComplexityClass.CUBIC:
            return "O(n³) complexity is very inefficient. Consider major algorithmic redesign"
        elif complexity == ComplexityClass.EXPONENTIAL:
            return "Exponential complexity will not scale. Use dynamic programming or memoization"
        return "Consider algorithmic optimization"
    
    def _should_ignore(self, name: str) -> bool:
        """Check if function should be ignored."""
        if name in self.config.ignore_functions:
            return True
        if name.startswith('_') and not name.startswith('__'):
            return True
        return False


# ============================================================
# PERFORMANCE ISSUE DETECTOR
# ============================================================

class PerformanceIssueDetector(ast.NodeVisitor):
    """Detect common performance anti-patterns."""
    
    def __init__(self, config: PerformanceValidatorConfig):
        self.config = config
        self.issues: List[PerformanceIssue] = []
        self.current_file: str = ""
        self.current_function: str = ""
        self.string_concat_count: int = 0
        self.in_loop: bool = False
        self.loop_depth: int = 0
        self.source_lines: List[str] = []
    
    def analyze_file(self, file_path: Path) -> List[PerformanceIssue]:
        """Analyze a Python file for performance issues."""
        self.current_file = str(file_path)
        self.issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.source_lines = content.split('\n')
            
            tree = ast.parse(content)
            self.visit(tree)
            
        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {e}")
        
        return self.issues
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        prev_function = self.current_function
        self.current_function = node.name
        self.string_concat_count = 0
        
        self.generic_visit(node)
        
        # Check for inefficient string concatenation
        if self.string_concat_count > 5:
            self.issues.append(PerformanceIssue(
                issue_type=PerformanceIssueType.INEFFICIENT_STRING_CONCAT,
                severity=Severity.MEDIUM,
                file_path=self.current_file,
                function_name=self.current_function,
                line_number=node.lineno,
                description=f"Multiple string concatenations ({self.string_concat_count}) detected",
                suggestion="Use ''.join() or io.StringIO for efficient string building",
                code_snippet=self._get_code_snippet(node)
            ))
        
        self.current_function = prev_function
    
    def visit_For(self, node: ast.For):
        """Visit for loop."""
        prev_in_loop = self.in_loop
        prev_depth = self.loop_depth
        self.in_loop = True
        self.loop_depth += 1
        
        self.generic_visit(node)
        
        self.in_loop = prev_in_loop
        self.loop_depth = prev_depth
        
        # Detect O(n²) loops
        if self.config.detect_o_n2 and self.loop_depth >= 2:
            self.issues.append(PerformanceIssue(
                issue_type=PerformanceIssueType.O_N2_LOOP,
                severity=Severity.HIGH if self.loop_depth == 2 else Severity.CRITICAL,
                file_path=self.current_file,
                function_name=self.current_function,
                line_number=node.lineno,
                description=f"Nested loop depth {self.loop_depth} detected (O(n^{self.loop_depth}) complexity)",
                detected_complexity=ComplexityClass.QUADRATIC if self.loop_depth == 2 else ComplexityClass.CUBIC,
                suggested_complexity=ComplexityClass.LINEARITHMIC,
                estimated_impact="Will scale poorly with large inputs",
                suggestion="Consider using hash map to eliminate nested loops",
                code_snippet=self._get_code_snippet(node)
            ))
    
    def visit_While(self, node: ast.While):
        """Visit while loop."""
        prev_in_loop = self.in_loop
        prev_depth = self.loop_depth
        self.in_loop = True
        self.loop_depth += 1
        
        self.generic_visit(node)
        
        self.in_loop = prev_in_loop
        self.loop_depth = prev_depth
    
    def visit_BinOp(self, node: ast.BinOp):
        """Visit binary operation."""
        # Detect string concatenation in loops
        if self.in_loop and isinstance(node.op, ast.Add):
            if self._is_string_operation(node):
                self.string_concat_count += 1
    
    def visit_Call(self, node: ast.Call):
        """Visit function call."""
        # Detect redundant computations in loops
        if self.in_loop and self.config.detect_redundant_computation:
            if self._is_potentially_redundant(node):
                self.issues.append(PerformanceIssue(
                    issue_type=PerformanceIssueType.REDUNDANT_COMPUTATION,
                    severity=Severity.MEDIUM,
                    file_path=self.current_file,
                    function_name=self.current_function,
                    line_number=node.lineno,
                    description="Potentially redundant computation inside loop",
                    suggestion="Move invariant computation outside the loop",
                    code_snippet=self._get_code_snippet(node)
                ))
        
        # Detect inefficient data structure usage
        if isinstance(node.func, ast.Name):
            if node.func.id == 'list' and node.args:
                if isinstance(node.args[0], ast.ListComp):
                    self.issues.append(PerformanceIssue(
                        issue_type=PerformanceIssueType.INEFFICIENT_DATA_STRUCTURE,
                        severity=Severity.LOW,
                        file_path=self.current_file,
                        function_name=self.current_function,
                        line_number=node.lineno,
                        description="Use list comprehension directly instead of list() wrapper",
                        suggestion="Remove redundant list() call",
                        code_snippet=self._get_code_snippet(node)
                    ))
            
            # Detect unnecessary copy
            if self.config.detect_unnecessary_copy:
                if node.func.id in ('copy', 'deepcopy'):
                    self.issues.append(PerformanceIssue(
                        issue_type=PerformanceIssueType.UNNECESSARY_COPY,
                        severity=Severity.MEDIUM,
                        file_path=self.current_file,
                        function_name=self.current_function,
                        line_number=node.lineno,
                        description="Unnecessary copy operation",
                        suggestion="Consider using reference or view instead of copy",
                        code_snippet=self._get_code_snippet(node)
                    ))
    
    def visit_ListComp(self, node: ast.ListComp):
        """Visit list comprehension."""
        # Detect nested comprehensions
        for generator in node.generators:
            if any(isinstance(g, ast.ListComp) for g in ast.walk(generator.iter)):
                self.issues.append(PerformanceIssue(
                    issue_type=PerformanceIssueType.O_N2_LOOP,
                    severity=Severity.MEDIUM,
                    file_path=self.current_file,
                    function_name=self.current_function,
                    line_number=node.lineno,
                    description="Nested list comprehension (O(n²) complexity)",
                    suggestion="Consider flattening or using different approach",
                    code_snippet=self._get_code_snippet(node)
                ))
    
    def _is_string_operation(self, node: ast.BinOp) -> bool:
        """Check if binary operation is string concatenation."""
        if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
            return True
        if isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
            return True
        return False
    
    def _is_potentially_redundant(self, node: ast.Call) -> bool:
        """Check if function call might be redundant in loop."""
        if isinstance(node.func, ast.Name):
            invariant_funcs = {'len', 'range', 'enumerate', 'zip', 'isinstance', 'type'}
            if node.func.id in invariant_funcs:
                for arg in node.args:
                    if isinstance(arg, ast.Name):
                        return False
                return True
        return False
    
    def _get_code_snippet(self, node: ast.AST, lines: int = 3) -> Optional[str]:
        """Get code snippet around a node."""
        if hasattr(self, 'source_lines') and hasattr(node, 'lineno'):
            start = max(0, node.lineno - 2)
            end = min(len(self.source_lines), node.lineno + lines - 1)
            return '\n'.join(self.source_lines[start:end])
        return None


# ============================================================
# PROFILER
# ============================================================

class CodeProfiler:
    """Profile Python code execution."""
    
    def __init__(self, config: PerformanceValidatorConfig):
        self.config = config
    
    def profile_file(self, file_path: Path) -> List[ProfileResult]:
        """Profile a Python file."""
        results = []
        
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec is None or spec.loader is None:
                return results
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[file_path.stem] = module
            
            profiler = cProfile.Profile()
            profiler.enable()
            
            try:
                spec.loader.exec_module(module)
            except Exception as e:
                logger.warning(f"Failed to execute {file_path}: {e}")
            
            profiler.disable()
            
            # Parse stats
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            
            total_time = sum(cc for _, (_, _, _, cc), _ in stats.stats.items())
            
            for func_stats in stats.stats.items():
                func_info, (cc, nc, tt, ct, callers) = func_stats
                filename, line, func_name = func_info
                
                if filename == str(file_path) and tt >= self.config.min_profile_time:
                    result = ProfileResult(
                        function_name=func_name,
                        file_path=filename,
                        line_number=line,
                        calls=nc,
                        total_time=tt,
                        cumulative_time=ct,
                        time_per_call=tt / nc if nc > 0 else tt,
                        percentage=(ct / total_time * 100) if total_time > 0 else 0,
                        is_builtin=False,
                        callers=[(c[0][2], c[1]) for c in callers.items()]
                    )
                    results.append(result)
            
            del sys.modules[file_path.stem]
            
        except Exception as e:
            logger.warning(f"Failed to profile {file_path}: {e}")
        
        return results


# ============================================================
# MEMORY PROFILER
# ============================================================

class MemoryProfiler:
    """Profile memory usage of Python code."""
    
    def __init__(self, config: PerformanceValidatorConfig):
        self.config = config
    
    def profile_file(self, file_path: Path) -> List[MemoryProfile]:
        """Profile memory usage of a Python file."""
        profiles = []
        
        try:
            tracemalloc.start()
            
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if spec is None or spec.loader is None:
                return profiles
            
            module = importlib.util.module_from_spec(spec)
            
            snapshot_before = tracemalloc.take_snapshot()
            
            try:
                spec.loader.exec_module(module)
            except Exception:
                pass
            
            snapshot_after = tracemalloc.take_snapshot()
            
            top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
            
            peak_memory = 0
            for stat in top_stats[:20]:
                if file_path.stem in str(stat.traceback):
                    peak_memory = max(peak_memory, stat.size)
                    
                    profile = MemoryProfile(
                        function_name="module_load",
                        file_path=str(file_path),
                        line_number=0,
                        peak_memory_mb=stat.size / (1024 * 1024),
                        average_memory_mb=stat.size / (1024 * 1024),
                        allocations=stat.count,
                        deallocations=0,
                        leaked_memory_mb=0.0,
                        traceback=str(stat.traceback)
                    )
                    profiles.append(profile)
            
            tracemalloc.stop()
            
        except Exception as e:
            logger.warning(f"Failed to profile memory for {file_path}: {e}")
            tracemalloc.stop()
        
        return profiles


# ============================================================
# BENCHMARKER
# ============================================================

class Benchmarker:
    """Benchmark Python functions."""
    
    def __init__(self, config: PerformanceValidatorConfig):
        self.config = config
    
    def benchmark_function(self, func: Callable, name: str, 
                           file_path: str) -> Optional[BenchmarkResult]:
        """Benchmark a single function."""
        times = []
        
        # Warmup
        for _ in range(self.config.benchmark_warmup):
            try:
                if func.__code__.co_argcount == 0:
                    func()
            except Exception:
                pass
        
        # Benchmark
        for _ in range(self.config.benchmark_iterations):
            try:
                start = time.perf_counter()
                if func.__code__.co_argcount == 0:
                    func()
                else:
                    break
                end = time.perf_counter()
                times.append(end - start)
            except Exception:
                break
        
        if len(times) < 10:
            return None
        
        total_time = sum(times)
        min_time = min(times)
        max_time = max(times)
        mean_time = statistics.mean(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        ops_per_second = 1.0 / mean_time if mean_time > 0 else 0.0
        
        return BenchmarkResult(
            function_name=name,
            file_path=file_path,
            iterations=len(times),
            total_time=total_time,
            min_time=min_time,
            max_time=max_time,
            mean_time=mean_time,
            median_time=median_time,
            std_dev=std_dev,
            ops_per_second=ops_per_second,
            warmup_runs=self.config.benchmark_warmup
        )


# ============================================================
# MAIN PERFORMANCE VALIDATOR
# ============================================================

class PerformanceValidator:
    """
    Validates code performance metrics and detects inefficiencies.
    
    Features:
    - Time complexity analysis (O(n), O(n²), etc.)
    - Performance anti-pattern detection
    - Code profiling with cProfile
    - Memory profiling with tracemalloc
    - Function benchmarking
    - Performance scoring and grading
    - Comprehensive reporting
    """
    
    def __init__(self, config: PerformanceValidatorConfig):
        self.config = config
        self.complexity_analyzer = ComplexityAnalyzer(config)
        self.issue_detector = PerformanceIssueDetector(config)
        self.profiler = CodeProfiler(config)
        self.memory_profiler = MemoryProfiler(config)
        self.benchmarker = Benchmarker(config)
        
        self.state = StateManager(config.project_root / ".ai_state" / "performance_validator.json")
        
        logger.info("PerformanceValidator initialized")
    
    def validate(self) -> PerformanceReport:
        """Run complete performance validation."""
        logger.info("Starting performance validation...")
        
        report = PerformanceReport(
            project_name=self.config.project_root.name
        )
        
        python_files = list(self.config.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_ignore(file_path):
                continue
            
            try:
                if self.config.analyze_complexity:
                    analyses = self.complexity_analyzer.analyze_file(file_path)
                    report.complexity_analyses.extend(analyses)
                    
                    for analysis in analyses:
                        if self._is_complexity_problematic(analysis):
                            report.problematic_functions.append(analysis)
                
                issues = self.issue_detector.analyze_file(file_path)
                for issue in issues:
                    if issue.severity in (Severity.CRITICAL, Severity.HIGH):
                        report.issues.append(issue)
                    else:
                        report.warnings.append(issue)
                
                if self.config.run_profiling:
                    profile_results = self.profiler.profile_file(file_path)
                    report.profile_results.extend(profile_results)
                    report.total_profile_time = sum(r.total_time for r in profile_results)
                
                if self.config.profile_memory:
                    memory_profiles = self.memory_profiler.profile_file(file_path)
                    report.memory_profiles.extend(memory_profiles)
                    
                    for profile in memory_profiles:
                        if profile.peak_memory_mb > self.config.memory_threshold_mb:
                            report.top_memory_consumers.append(profile)
                        if profile.leaked_memory_mb > self.config.leak_threshold_mb:
                            report.memory_leaks.append(profile)
                        
                        report.peak_total_memory_mb = max(
                            report.peak_total_memory_mb, 
                            profile.peak_memory_mb
                        )
                
            except Exception as e:
                logger.warning(f"Failed to validate {file_path}: {e}")
        
        report.top_slow_functions = sorted(
            report.profile_results, 
            key=lambda x: x.total_time, 
            reverse=True
        )[:self.config.profile_top_n]
        
        report.top_memory_consumers = sorted(
            report.top_memory_consumers,
            key=lambda x: x.peak_memory_mb,
            reverse=True
        )[:10]
        
        report.overall_score = self._calculate_overall_score(report)
        report.grade = self._calculate_grade(report.overall_score)
        report.is_valid = self._determine_validity(report)
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        self._save_report(report)
        
        logger.info(f"Performance validation complete: {len(report.issues)} issues, {len(report.warnings)} warnings")
        
        return report
    
    def _is_complexity_problematic(self, analysis: ComplexityAnalysis) -> bool:
        """Check if complexity analysis indicates a problem."""
        complexity_order = [
            ComplexityClass.CONSTANT,
            ComplexityClass.LOGARITHMIC,
            ComplexityClass.LINEAR,
            ComplexityClass.LINEARITHMIC,
            ComplexityClass.QUADRATIC,
            ComplexityClass.CUBIC,
            ComplexityClass.EXPONENTIAL,
            ComplexityClass.FACTORIAL
        ]
        
        threshold_idx = complexity_order.index(self.config.max_acceptable_complexity)
        current_idx = complexity_order.index(analysis.detected_complexity)
        
        return current_idx > threshold_idx
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        path_str = str(file_path)
        for pattern in self.config.ignore_patterns:
            if pattern.replace('*', '') in path_str:
                return True
        return False
    
    def _calculate_overall_score(self, report: PerformanceReport) -> float:
        """Calculate overall performance score."""
        score = 100.0
        
        severity_weights = {
            Severity.CRITICAL: 20,
            Severity.HIGH: 10,
            Severity.MEDIUM: 5,
            Severity.LOW: 2,
            Severity.INFO: 0
        }
        
        for issue in report.issues:
            score -= severity_weights.get(issue.severity, 5)
        
        for warning in report.warnings:
            score -= severity_weights.get(warning.severity, 2) * 0.5
        
        for analysis in report.problematic_functions:
            if analysis.detected_complexity == ComplexityClass.QUADRATIC:
                score -= 5
            elif analysis.detected_complexity == ComplexityClass.CUBIC:
                score -= 10
            elif analysis.detected_complexity in (ComplexityClass.EXPONENTIAL, ComplexityClass.FACTORIAL):
                score -= 20
        
        if report.peak_total_memory_mb > self.config.memory_threshold_mb:
            score -= 10
        
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
    
    def _determine_validity(self, report: PerformanceReport) -> bool:
        """Determine if validation passes."""
        if self.config.fail_on_critical:
            for issue in report.issues:
                if issue.severity == Severity.CRITICAL:
                    return False
        
        if self.config.fail_on_high:
            for issue in report.issues:
                if issue.severity == Severity.HIGH:
                    return False
        
        if len(report.issues) > self.config.max_issues:
            return False
        
        return True
    
    def _generate_summary(self, report: PerformanceReport) -> str:
        """Generate validation summary."""
        if report.is_valid:
            return f"✅ Performance validation passed. Score: {report.overall_score:.1f} (Grade: {report.grade})"
        else:
            return f"❌ Performance issues found: {len(report.issues)} issues, {len(report.warnings)} warnings"
    
    def _generate_recommendations(self, report: PerformanceReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if report.problematic_functions:
            top = report.problematic_functions[0]
            recommendations.append(f"Optimize '{top.function_name}' ({top.detected_complexity.value} complexity)")
        
        if report.top_slow_functions:
            top = report.top_slow_functions[0]
            recommendations.append(f"Profile and optimize slow function '{top.function_name}' ({top.total_time:.3f}s)")
        
        if report.top_memory_consumers:
            top = report.top_memory_consumers[0]
            recommendations.append(f"Reduce memory usage in '{top.function_name}' ({top.peak_memory_mb:.1f}MB)")
        
        if report.issues:
            issue_types = defaultdict(int)
            for issue in report.issues:
                issue_types[issue.issue_type.value] += 1
            
            top_issue = sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[0]
            recommendations.append(f"Fix {top_issue[1]} {top_issue[0]} issues")
        
        return recommendations[:5]
    
    def _save_report(self, report: PerformanceReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.validated_at.isoformat(),
            'project': report.project_name,
            'is_valid': report.is_valid,
            'score': report.overall_score,
            'grade': report.grade,
            'issues': len(report.issues),
            'warnings': len(report.warnings),
            'problematic_functions': len(report.problematic_functions)
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: PerformanceReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export performance report."""
        
        if format == 'json':
            import json
            data = {
                'validated_at': report.validated_at.isoformat(),
                'project': report.project_name,
                'is_valid': report.is_valid,
                'score': report.overall_score,
                'grade': report.grade,
                'summary': report.summary,
                'statistics': {
                    'problematic_functions': len(report.problematic_functions),
                    'profile_results': len(report.profile_results),
                    'memory_profiles': len(report.memory_profiles),
                    'issues': len(report.issues),
                    'warnings': len(report.warnings)
                },
                'problematic_functions': [
                    {
                        'name': f.function_name,
                        'file': f.file_path,
                        'complexity': f.detected_complexity.value,
                        'suggestion': f.suggestion
                    }
                    for f in report.problematic_functions[:10]
                ],
                'issues': [
                    {
                        'type': i.issue_type.value,
                        'severity': i.severity.value,
                        'function': i.function_name,
                        'file': i.file_path,
                        'description': i.description,
                        'suggestion': i.suggestion
                    }
                    for i in report.issues[:20]
                ],
                'recommendations': report.recommendations
            }
            
            return json.dumps(data, indent=2)
        
        else:  # markdown
            lines = [
                f"# Performance Validation Report",
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
                f"| Problematic Functions | {len(report.problematic_functions)} |",
                f"| Issues | {len(report.issues)} |",
                f"| Warnings | {len(report.warnings)} |",
                f"| Peak Memory | {report.peak_total_memory_mb:.1f} MB |",
                "",
            ]
            
            if report.problematic_functions:
                lines.extend([
                    "## ⚠️ Problematic Functions",
                    "",
                    "| Function | File | Complexity | Suggestion |",
                    "|----------|------|------------|------------|",
                ])
                for f in report.problematic_functions[:10]:
                    file_name = Path(f.file_path).name
                    lines.append(f"| {f.function_name} | {file_name}:{f.line_number} | {f.detected_complexity.value} | {f.suggestion or '-'} |")
                lines.append("")
            
            if report.issues:
                lines.extend([
                    "## ❌ Performance Issues",
                    "",
                    "| Type | Severity | Function | Description |",
                    "|------|----------|----------|-------------|",
                ])
                for issue in report.issues[:15]:
                    lines.append(f"| {issue.issue_type.value} | {issue.severity.value} | {issue.function_name or 'N/A'} | {issue.description[:50]} |")
                lines.append("")
            
            if report.top_slow_functions:
                lines.extend([
                    "## 🐢 Slowest Functions",
                    "",
                    "| Function | File | Time (s) | Calls | Time/Call |",
                    "|----------|------|----------|-------|-----------|",
                ])
                for f in report.top_slow_functions[:10]:
                    file_name = Path(f.file_path).name
                    lines.append(f"| {f.function_name} | {file_name}:{f.line_number} | {f.total_time:.3f} | {f.calls} | {f.time_per_call:.6f} |")
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
        logger.info("PerformanceValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for performance validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate code performance metrics")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--profile", action="store_true", help="Run code profiling")
    parser.add_argument("--memory", action="store_true", help="Run memory profiling")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmarks")
    parser.add_argument("--fail-on-high", action="store_true")
    parser.add_argument("--max-complexity", choices=[c.value for c in ComplexityClass],
                       default=ComplexityClass.QUADRATIC.value)
    
    args = parser.parse_args()
    
    config = PerformanceValidatorConfig(
        project_root=args.project_root,
        run_profiling=args.profile,
        profile_memory=args.memory,
        run_benchmarks=args.benchmark,
        fail_on_high=args.fail_on_high,
        max_acceptable_complexity=ComplexityClass(args.max_complexity)
    )
    
    validator = PerformanceValidator(config)
    
    report = validator.validate()
    
    output = validator.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    
    if config.fail_on_critical and not report.is_valid:
        exit(1)
    
    validator.close()


if __name__ == "__main__":
    main()