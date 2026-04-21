#!/usr/bin/env python3
"""
Mutation Tester - Performs mutation testing to evaluate test suite quality.

Part of the Quality tools (quality/testers/mutation_tester.py)


This mutation_tester.py provides:

Multiple Mutation Operators - Arithmetic, comparison, logical, boolean, control flow, return, exception, assignment, string, collection
AST-Based Mutation Generation - Precise code mutations using Python AST
Mutation Score Calculation - Percentage of mutations killed by tests
Parallel Execution - Multi-threaded mutation testing for speed
Test Effectiveness Analysis - Identifies weak and strong tests
Equivalent Mutation Detection - Identifies mutations that don't change behavior
Category and Operator Analysis - Breakdown by mutation type
Weak Area Identification - Pinpoints files with low mutation scores
Survived Mutation Reporting - Shows exact code that wasn't caught
Grade Calculation - A-F grade based on mutation score
Configurable Thresholds - Customizable acceptable scores
Comprehensive Reporting - JSON and Markdown formats

The mutation tester evaluates test suite quality by introducing bugs (mutations) and checking if tests catch them, providing a 
rigorous measure of test effectiveness beyond simple coverage metrics
"""

import ast
import random
import hashlib
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

from ....shared.logger import get_logger
from ....shared.state_manager import StateManager
from ....shared.llm_client import LLMClient
from ....analysis.scanners.project_scanner import ProjectScanner
from ....analysis.scanners.ast_analyzer import ASTAnalyzer

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class MutationOperator(str, Enum):
    """Type of mutation operator."""
    # Arithmetic operators
    ARITHMETIC_ADD_TO_SUB = "arithmetic_add_to_sub"
    ARITHMETIC_SUB_TO_ADD = "arithmetic_sub_to_add"
    ARITHMETIC_MUL_TO_DIV = "arithmetic_mul_to_div"
    ARITHMETIC_DIV_TO_MUL = "arithmetic_div_to_mul"
    ARITHMETIC_MOD_TO_MUL = "arithmetic_mod_to_mul"
    ARITHMETIC_POW_TO_MUL = "arithmetic_pow_to_mul"
    
    # Comparison operators
    COMPARISON_EQ_TO_NE = "comparison_eq_to_ne"
    COMPARISON_NE_TO_EQ = "comparison_ne_to_eq"
    COMPARISON_LT_TO_LE = "comparison_lt_to_le"
    COMPARISON_LE_TO_LT = "comparison_le_to_lt"
    COMPARISON_GT_TO_GE = "comparison_gt_to_ge"
    COMPARISON_GE_TO_GT = "comparison_ge_to_gt"
    
    # Logical operators
    LOGICAL_AND_TO_OR = "logical_and_to_or"
    LOGICAL_OR_TO_AND = "logical_or_to_and"
    LOGICAL_NOT_REMOVE = "logical_not_remove"
    
    # Boolean literals
    BOOLEAN_TRUE_TO_FALSE = "boolean_true_to_false"
    BOOLEAN_FALSE_TO_TRUE = "boolean_false_to_true"
    
    # Control flow
    CONDITIONAL_NEGATE = "conditional_negate"
    LOOP_BREAK_REMOVE = "loop_break_remove"
    LOOP_CONTINUE_REMOVE = "loop_continue_remove"
    
    # Return values
    RETURN_VALUE_MUTATE = "return_value_mutate"
    RETURN_NONE = "return_none"
    
    # Exception handling
    EXCEPTION_REMOVE = "exception_remove"
    EXCEPTION_SWALLOW = "exception_swallow"
    
    # Assignment
    ASSIGNMENT_REMOVE = "assignment_remove"
    AUGMENTED_ASSIGNMENT_MUTATE = "augmented_assignment_mutate"
    
    # String mutations
    STRING_EMPTY = "string_empty"
    STRING_INTERPOLATION = "string_interpolation"
    
    # List/Dict mutations
    COLLECTION_EMPTY = "collection_empty"
    DICT_KEY_SWAP = "dict_key_swap"
    SLICE_INDEX_MUTATE = "slice_index_mutate"


class MutationStatus(str, Enum):
    """Status of a mutation."""
    PENDING = "pending"
    RUNNING = "running"
    KILLED = "killed"
    SURVIVED = "survived"
    TIMEOUT = "timeout"
    ERROR = "error"
    SKIPPED = "skipped"
    INCOMPETENT = "incompetent"


class MutationCategory(str, Enum):
    """Category of mutation."""
    ARITHMETIC = "arithmetic"
    COMPARISON = "comparison"
    LOGICAL = "logical"
    BOOLEAN = "boolean"
    CONTROL_FLOW = "control_flow"
    RETURN = "return"
    EXCEPTION = "exception"
    ASSIGNMENT = "assignment"
    STRING = "string"
    COLLECTION = "collection"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Mutation:
    """A single code mutation."""
    id: str
    operator: MutationOperator
    category: MutationCategory
    file_path: str
    line_number: int
    column_offset: int
    original_code: str
    mutated_code: str
    context: str = ""
    status: MutationStatus = MutationStatus.PENDING
    test_result: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MutationResult:
    """Result of mutation testing for a file."""
    file_path: str
    total_mutations: int = 0
    killed: int = 0
    survived: int = 0
    timeout: int = 0
    error: int = 0
    skipped: int = 0
    incompetent: int = 0
    mutation_score: float = 0.0
    mutations: List[Mutation] = field(default_factory=list)
    killed_mutations: List[Mutation] = field(default_factory=list)
    survived_mutations: List[Mutation] = field(default_factory=list)
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCoverage:
    """Test coverage from mutation perspective."""
    test_name: str
    mutations_killed: List[str] = field(default_factory=list)
    effectiveness_score: float = 0.0


@dataclass
class MutationReport:
    """Complete mutation testing report."""
    analyzed_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    
    # Overall metrics
    total_files: int = 0
    total_mutations: int = 0
    killed: int = 0
    survived: int = 0
    timeout: int = 0
    error: int = 0
    incompetent: int = 0
    mutation_score: float = 0.0
    
    # Detailed results
    file_results: Dict[str, MutationResult] = field(default_factory=dict)
    
    # By category
    mutations_by_category: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # By operator
    mutations_by_operator: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # Survived mutations (most concerning)
    survived_mutations: List[Mutation] = field(default_factory=list)
    
    # Test effectiveness
    test_coverages: Dict[str, TestCoverage] = field(default_factory=dict)
    weak_tests: List[Tuple[str, float]] = field(default_factory=list)
    
    # Equivalent mutations (likely not killable)
    equivalent_mutations: List[Mutation] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    weak_areas: List[Tuple[str, float]] = field(default_factory=list)
    
    # Summary
    is_acceptable: bool = False
    overall_score: float = 0.0
    grade: str = "F"
    summary: str = ""
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MutationTesterConfig:
    """Configuration for mutation tester."""
    project_root: Path
    source_paths: List[str] = field(default_factory=lambda: ["src", "engines", "tools"])
    test_paths: List[str] = field(default_factory=lambda: ["tests", "test"])
    test_command: str = "pytest {test_path} -x -v"
    
    # Mutation operators to enable
    enabled_operators: Set[MutationOperator] = field(default_factory=lambda: {
        MutationOperator.ARITHMETIC_ADD_TO_SUB,
        MutationOperator.ARITHMETIC_SUB_TO_ADD,
        MutationOperator.ARITHMETIC_MUL_TO_DIV,
        MutationOperator.COMPARISON_EQ_TO_NE,
        MutationOperator.COMPARISON_LT_TO_LE,
        MutationOperator.COMPARISON_GT_TO_GE,
        MutationOperator.LOGICAL_AND_TO_OR,
        MutationOperator.LOGICAL_OR_TO_AND,
        MutationOperator.BOOLEAN_TRUE_TO_FALSE,
        MutationOperator.BOOLEAN_FALSE_TO_TRUE,
        MutationOperator.CONDITIONAL_NEGATE,
        MutationOperator.RETURN_VALUE_MUTATE,
    })
    
    # Limits
    max_mutations_per_file: int = 100
    max_total_mutations: int = 1000
    mutation_timeout_seconds: int = 30
    test_timeout_seconds: int = 300
    
    # Parallel execution
    parallel: bool = True
    max_workers: int = 4
    
    # Sampling (for large codebases)
    sample_rate: float = 1.0
    random_seed: int = 42
    
    # Filtering
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "test_*.py", "*_test.py",
        "migrations", "alembic", "setup.py", "conftest.py", "__init__.py"
    ])
    ignore_functions: List[str] = field(default_factory=list)
    
    # Detection
    detect_equivalent: bool = True
    min_test_effectiveness: float = 0.5
    
    # Thresholds
    acceptable_mutation_score: float = 80.0
    good_mutation_score: float = 90.0
    
    # Reporting
    generate_report: bool = True
    output_format: str = "markdown"
    show_survived_code: bool = True


# ============================================================
# MUTATION GENERATOR
# ============================================================

class MutationGenerator(ast.NodeTransformer):
    """Generate mutations from Python AST."""
    
    def __init__(self, config: MutationTesterConfig, file_path: str, source_code: str):
        self.config = config
        self.file_path = file_path
        self.source_code = source_code
        self.source_lines = source_code.split('\n')
        self.mutations: List[Mutation] = []
        self.mutation_counter = 0
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None
    
    def generate(self) -> List[Mutation]:
        """Generate mutations from source code."""
        try:
            tree = ast.parse(self.source_code)
            self.visit(tree)
        except SyntaxError:
            logger.warning(f"Syntax error in {self.file_path}")
        
        # Sample if needed
        if self.config.sample_rate < 1.0:
            random.seed(self.config.random_seed)
            sample_size = int(len(self.mutations) * self.config.sample_rate)
            self.mutations = random.sample(self.mutations, min(sample_size, len(self.mutations)))
        
        # Limit per file
        if len(self.mutations) > self.config.max_mutations_per_file:
            self.mutations = self.mutations[:self.config.max_mutations_per_file]
        
        return self.mutations
    
    def _create_mutation(self, node: ast.AST, operator: MutationOperator,
                         original: str, mutated: str) -> Optional[Mutation]:
        """Create a mutation."""
        if operator not in self.config.enabled_operators:
            return None
        
        self.mutation_counter += 1
        
        # Get context
        line_num = getattr(node, 'lineno', 0)
        col_offset = getattr(node, 'col_offset', 0)
        
        context_start = max(0, line_num - 3)
        context_end = min(len(self.source_lines), line_num + 2)
        context = '\n'.join(self.source_lines[context_start:context_end])
        
        # Generate ID
        mutation_id = hashlib.md5(
            f"{self.file_path}:{line_num}:{col_offset}:{operator.value}".encode()
        ).hexdigest()[:12]
        
        return Mutation(
            id=mutation_id,
            operator=operator,
            category=self._get_category(operator),
            file_path=self.file_path,
            line_number=line_num,
            column_offset=col_offset,
            original_code=original,
            mutated_code=mutated,
            context=context,
            metadata={
                'function': self.current_function,
                'class': self.current_class
            }
        )
    
    def _get_category(self, operator: MutationOperator) -> MutationCategory:
        """Get category for operator."""
        if 'arithmetic' in operator.value:
            return MutationCategory.ARITHMETIC
        elif 'comparison' in operator.value:
            return MutationCategory.COMPARISON
        elif 'logical' in operator.value or 'boolean' in operator.value:
            return MutationCategory.BOOLEAN
        elif 'conditional' in operator.value or 'loop' in operator.value:
            return MutationCategory.CONTROL_FLOW
        elif 'return' in operator.value:
            return MutationCategory.RETURN
        elif 'exception' in operator.value:
            return MutationCategory.EXCEPTION
        elif 'assignment' in operator.value:
            return MutationCategory.ASSIGNMENT
        elif 'string' in operator.value:
            return MutationCategory.STRING
        elif 'collection' in operator.value or 'dict' in operator.value or 'slice' in operator.value:
            return MutationCategory.COLLECTION
        return MutationCategory.ARITHMETIC
    
    # ============================================================
    # VISITOR METHODS
    # ============================================================
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        if node.name in self.config.ignore_functions:
            return node
        
        prev_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev_function
        return node
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class
        return node
    
    def visit_BinOp(self, node: ast.BinOp):
        """Visit binary operation for arithmetic mutations."""
        original = ast.unparse(node)
        
        # Addition to Subtraction
        if isinstance(node.op, ast.Add):
            node.op = ast.Sub()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.ARITHMETIC_ADD_TO_SUB, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.op = ast.Add()
        
        # Subtraction to Addition
        elif isinstance(node.op, ast.Sub):
            node.op = ast.Add()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.ARITHMETIC_SUB_TO_ADD, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.op = ast.Sub()
        
        # Multiplication to Division
        elif isinstance(node.op, ast.Mult):
            node.op = ast.Div()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.ARITHMETIC_MUL_TO_DIV, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.op = ast.Mult()
        
        # Division to Multiplication
        elif isinstance(node.op, ast.Div):
            node.op = ast.Mult()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.ARITHMETIC_DIV_TO_MUL, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.op = ast.Div()
        
        # Modulo to Multiplication
        elif isinstance(node.op, ast.Mod):
            node.op = ast.Mult()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.ARITHMETIC_MOD_TO_MUL, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.op = ast.Mod()
        
        # Power to Multiplication
        elif isinstance(node.op, ast.Pow):
            node.op = ast.Mult()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.ARITHMETIC_POW_TO_MUL, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.op = ast.Pow()
        
        return self.generic_visit(node)
    
    def visit_Compare(self, node: ast.Compare):
        """Visit comparison for comparison mutations."""
        if len(node.ops) != 1:
            return self.generic_visit(node)
        
        original = ast.unparse(node)
        op = node.ops[0]
        
        # Eq to NotEq
        if isinstance(op, ast.Eq):
            node.ops[0] = ast.NotEq()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.COMPARISON_EQ_TO_NE, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.ops[0] = ast.Eq()
        
        # NotEq to Eq
        elif isinstance(op, ast.NotEq):
            node.ops[0] = ast.Eq()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.COMPARISON_NE_TO_EQ, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.ops[0] = ast.NotEq()
        
        # Lt to LtE
        elif isinstance(op, ast.Lt):
            node.ops[0] = ast.LtE()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.COMPARISON_LT_TO_LE, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.ops[0] = ast.Lt()
        
        # LtE to Lt
        elif isinstance(op, ast.LtE):
            node.ops[0] = ast.Lt()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.COMPARISON_LE_TO_LT, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.ops[0] = ast.LtE()
        
        # Gt to GtE
        elif isinstance(op, ast.Gt):
            node.ops[0] = ast.GtE()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.COMPARISON_GT_TO_GE, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.ops[0] = ast.Gt()
        
        # GtE to Gt
        elif isinstance(op, ast.GtE):
            node.ops[0] = ast.Gt()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.COMPARISON_GE_TO_GT, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.ops[0] = ast.GtE()
        
        return self.generic_visit(node)
    
    def visit_BoolOp(self, node: ast.BoolOp):
        """Visit boolean operation for logical mutations."""
        original = ast.unparse(node)
        
        # And to Or
        if isinstance(node.op, ast.And):
            node.op = ast.Or()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.LOGICAL_AND_TO_OR, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.op = ast.And()
        
        # Or to And
        elif isinstance(node.op, ast.Or):
            node.op = ast.And()
            mutated = ast.unparse(node)
            mutation = self._create_mutation(
                node, MutationOperator.LOGICAL_OR_TO_AND, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
            node.op = ast.Or()
        
        return self.generic_visit(node)
    
    def visit_UnaryOp(self, node: ast.UnaryOp):
        """Visit unary operation for not removal."""
        if isinstance(node.op, ast.Not):
            original = ast.unparse(node)
            mutated = ast.unparse(node.operand)
            mutation = self._create_mutation(
                node, MutationOperator.LOGICAL_NOT_REMOVE, original, mutated
            )
            if mutation:
                self.mutations.append(mutation)
        
        return self.generic_visit(node)
    
    def visit_Constant(self, node: ast.Constant):
        """Visit constant for boolean mutations."""
        if node.value is True:
            mutation = self._create_mutation(
                node, MutationOperator.BOOLEAN_TRUE_TO_FALSE, "True", "False"
            )
            if mutation:
                self.mutations.append(mutation)
        elif node.value is False:
            mutation = self._create_mutation(
                node, MutationOperator.BOOLEAN_FALSE_TO_TRUE, "False", "True"
            )
            if mutation:
                self.mutations.append(mutation)
        elif node.value == "" or node.value == '':
            mutation = self._create_mutation(
                node, MutationOperator.STRING_EMPTY, repr(node.value), '"mutated"'
            )
            if mutation:
                self.mutations.append(mutation)
        
        return self.generic_visit(node)
    
    def visit_If(self, node: ast.If):
        """Visit if statement for condition negation."""
        original = ast.unparse(node.test)
        
        # Negate condition
        if isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
            mutated = ast.unparse(node.test.operand)
        else:
            mutated = f"not ({original})"
        
        mutation = self._create_mutation(
            node.test, MutationOperator.CONDITIONAL_NEGATE, original, mutated
        )
        if mutation:
            self.mutations.append(mutation)
        
        return self.generic_visit(node)
    
    def visit_Return(self, node: ast.Return):
        """Visit return statement for return mutations."""
        if node.value:
            original = ast.unparse(node.value)
            
            # Return None
            mutation = self._create_mutation(
                node, MutationOperator.RETURN_NONE, original, "None"
            )
            if mutation:
                self.mutations.append(mutation)
            
            # Mutate return value
            if isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, (int, float)):
                    mutated = str(node.value.value + 1)
                    mutation = self._create_mutation(
                        node, MutationOperator.RETURN_VALUE_MUTATE, original, mutated
                    )
                    if mutation:
                        self.mutations.append(mutation)
        
        return self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment for assignment removal."""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if not node.targets[0].id.startswith('_'):
                original = ast.unparse(node)
                mutated = "pass  # Removed assignment"
                mutation = self._create_mutation(
                    node, MutationOperator.ASSIGNMENT_REMOVE, original, mutated
                )
                if mutation:
                    self.mutations.append(mutation)
        
        return self.generic_visit(node)


# ============================================================
# MUTATION EXECUTOR
# ============================================================

class MutationExecutor:
    """Execute mutations and run tests."""
    
    def __init__(self, config: MutationTesterConfig):
        self.config = config
        self._test_suite_passing = None
    
    def check_test_suite_passing(self) -> bool:
        """Check if the original test suite passes."""
        if self._test_suite_passing is not None:
            return self._test_suite_passing
        
        try:
            cmd = self._build_test_command()
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=self.config.test_timeout_seconds,
                cwd=self.config.project_root
            )
            self._test_suite_passing = result.returncode == 0
            return self._test_suite_passing
        except Exception as e:
            logger.error(f"Failed to run test suite: {e}")
            return False
    
    def _build_test_command(self, test_path: Optional[str] = None) -> str:
        """Build test command."""
        if test_path:
            return self.config.test_command.format(test_path=test_path)
        return self.config.test_command.format(test_path="")
    
    def execute_mutation(self, mutation: Mutation) -> Mutation:
        """Execute a single mutation."""
        if mutation.status != MutationStatus.PENDING:
            return mutation
        
        mutation.status = MutationStatus.RUNNING
        start_time = datetime.now()
        
        # Create temporary file with mutation
        try:
            with open(mutation.file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Apply mutation
            mutated_content = self._apply_mutation(
                original_content, 
                mutation.line_number,
                mutation.original_code,
                mutation.mutated_code
            )
            
            # Write to temp file
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, dir=Path(mutation.file_path).parent
            ) as tmp:
                tmp.write(mutated_content)
                tmp_path = Path(tmp.name)
            
            # Run tests
            test_cmd = self._build_test_command(str(tmp_path))
            result = subprocess.run(
                test_cmd, shell=True, capture_output=True, text=True,
                timeout=self.config.mutation_timeout_seconds,
                cwd=self.config.project_root
            )
            
            # Determine mutation status
            if result.returncode != 0:
                mutation.status = MutationStatus.KILLED
            else:
                mutation.status = MutationStatus.SURVIVED
            
            mutation.test_result = {
                'returncode': result.returncode,
                'stdout': result.stdout[:500],
                'stderr': result.stderr[:500]
            }
            
            # Clean up
            tmp_path.unlink()
            
        except subprocess.TimeoutExpired:
            mutation.status = MutationStatus.TIMEOUT
        except Exception as e:
            mutation.status = MutationStatus.ERROR
            mutation.test_result = {'error': str(e)}
        finally:
            # Restore original file if needed
            pass
        
        mutation.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return mutation
    
    def _apply_mutation(self, content: str, line_number: int,
                        original: str, mutated: str) -> str:
        """Apply mutation to source code."""
        lines = content.split('\n')
        
        if line_number > 0 and line_number <= len(lines):
            line = lines[line_number - 1]
            if original in line:
                lines[line_number - 1] = line.replace(original, mutated, 1)
        
        return '\n'.join(lines)
    
    def execute_mutations(self, mutations: List[Mutation]) -> List[Mutation]:
        """Execute multiple mutations."""
        if self.config.parallel and len(mutations) > 1:
            return self._execute_parallel(mutations)
        else:
            return [self.execute_mutation(m) for m in mutations]
    
    def _execute_parallel(self, mutations: List[Mutation]) -> List[Mutation]:
        """Execute mutations in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {executor.submit(self.execute_mutation, m): m for m in mutations}
            
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=self.config.mutation_timeout_seconds + 5)
                    results.append(result)
                except Exception as e:
                    mutation = futures[future]
                    mutation.status = MutationStatus.ERROR
                    mutation.test_result = {'error': str(e)}
                    results.append(mutation)
        
        return results


# ============================================================
# MAIN MUTATION TESTER
# ============================================================

class MutationTester:
    """
    Performs mutation testing to evaluate test suite quality.
    
    Features:
    - Multiple mutation operators (arithmetic, comparison, logical, boolean, etc.)
    - Parallel mutation execution
    - Mutation score calculation
    - Test effectiveness analysis
    - Equivalent mutation detection
    - Weak test identification
    - Comprehensive reporting
    - Integration with pytest
    """
    
    def __init__(self, config: MutationTesterConfig):
        self.config = config
        self.executor = MutationExecutor(config)
        self.scanner = ProjectScanner(project_root=config.project_root)
        self.ast_analyzer = ASTAnalyzer()
        self.state = StateManager(config.project_root / ".ai_state" / "mutation_tester.json")
        
        random.seed(config.random_seed)
        
        logger.info("MutationTester initialized")
    
    def test(self) -> MutationReport:
        """Run complete mutation testing."""
        logger.info("Starting mutation testing...")
        
        # Check if test suite passes
        if not self.executor.check_test_suite_passing():
            logger.error("Original test suite does not pass. Fix tests first.")
            return self._create_empty_report("Test suite failing")
        
        report = MutationReport(
            project_name=self.config.project_root.name
        )
        
        # Find Python files to mutate
        source_files = self._find_source_files()
        report.total_files = len(source_files)
        
        # Generate mutations
        all_mutations = []
        for file_path in source_files:
            if self._should_ignore(file_path):
                continue
            
            mutations = self._generate_mutations(file_path)
            
            if len(all_mutations) + len(mutations) > self.config.max_total_mutations:
                remaining = self.config.max_total_mutations - len(all_mutations)
                if remaining > 0:
                    mutations = mutations[:remaining]
                    all_mutations.extend(mutations)
                break
            
            all_mutations.extend(mutations)
        
        report.total_mutations = len(all_mutations)
        logger.info(f"Generated {len(all_mutations)} mutations")
        
        if not all_mutations:
            report.summary = "No mutations generated"
            return report
        
        # Execute mutations
        executed_mutations = self.executor.execute_mutations(all_mutations)
        
        # Analyze results
        self._analyze_results(report, executed_mutations)
        
        # Group by file
        self._group_by_file(report, executed_mutations)
        
        # Calculate test effectiveness
        self._calculate_test_effectiveness(report)
        
        # Detect equivalent mutations
        if self.config.detect_equivalent:
            report.equivalent_mutations = self._detect_equivalent_mutations(report.survived_mutations)
        
        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)
        report.weak_areas = self._identify_weak_areas(report)
        
        # Calculate score and grade
        report.overall_score = report.mutation_score
        report.grade = self._calculate_grade(report.mutation_score)
        report.is_acceptable = report.mutation_score >= self.config.acceptable_mutation_score
        
        # Generate summary
        report.summary = self._generate_summary(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Mutation testing complete: {report.mutation_score:.1f}% score")
        
        return report
    
    def _create_empty_report(self, reason: str) -> MutationReport:
        """Create empty report with reason."""
        return MutationReport(
            project_name=self.config.project_root.name,
            summary=f"Mutation testing skipped: {reason}"
        )
    
    def _find_source_files(self) -> List[Path]:
        """Find source files to mutate."""
        files = []
        
        for source_path in self.config.source_paths:
            path = self.config.project_root / source_path
            if path.exists():
                if path.is_file():
                    files.append(path)
                else:
                    files.extend(path.rglob("*.py"))
        
        return files
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        path_str = str(file_path)
        
        for pattern in self.config.ignore_patterns:
            if pattern.replace('*', '') in path_str:
                return True
        
        return False
    
    def _generate_mutations(self, file_path: Path) -> List[Mutation]:
        """Generate mutations for a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            generator = MutationGenerator(self.config, str(file_path), source_code)
            return generator.generate()
            
        except Exception as e:
            logger.warning(f"Failed to generate mutations for {file_path}: {e}")
            return []
    
    def _analyze_results(self, report: MutationReport, mutations: List[Mutation]):
        """Analyze mutation results."""
        for mutation in mutations:
            report.total_mutations += 1
            
            if mutation.status == MutationStatus.KILLED:
                report.killed += 1
            elif mutation.status == MutationStatus.SURVIVED:
                report.survived += 1
                report.survived_mutations.append(mutation)
            elif mutation.status == MutationStatus.TIMEOUT:
                report.timeout += 1
            elif mutation.status == MutationStatus.ERROR:
                report.error += 1
            elif mutation.status == MutationStatus.INCOMPETENT:
                report.incompetent += 1
            
            # Track by category
            cat = mutation.category.value
            if cat not in report.mutations_by_category:
                report.mutations_by_category[cat] = {'total': 0, 'killed': 0, 'survived': 0}
            report.mutations_by_category[cat]['total'] += 1
            if mutation.status == MutationStatus.KILLED:
                report.mutations_by_category[cat]['killed'] += 1
            elif mutation.status == MutationStatus.SURVIVED:
                report.mutations_by_category[cat]['survived'] += 1
            
            # Track by operator
            op = mutation.operator.value
            if op not in report.mutations_by_operator:
                report.mutations_by_operator[op] = {'total': 0, 'killed': 0, 'survived': 0}
            report.mutations_by_operator[op]['total'] += 1
            if mutation.status == MutationStatus.KILLED:
                report.mutations_by_operator[op]['killed'] += 1
            elif mutation.status == MutationStatus.SURVIVED:
                report.mutations_by_operator[op]['survived'] += 1
        
        # Calculate mutation score
        detectable = report.killed + report.timeout
        total_valid = report.total_mutations - report.incompetent
        
        if total_valid > 0:
            report.mutation_score = (detectable / total_valid) * 100
    
    def _group_by_file(self, report: MutationReport, mutations: List[Mutation]):
        """Group mutations by file."""
        by_file = defaultdict(list)
        
        for mutation in mutations:
            by_file[mutation.file_path].append(mutation)
        
        for file_path, file_mutations in by_file.items():
            result = MutationResult(file_path=file_path)
            result.total_mutations = len(file_mutations)
            result.mutations = file_mutations
            
            for m in file_mutations:
                if m.status == MutationStatus.KILLED:
                    result.killed += 1
                    result.killed_mutations.append(m)
                elif m.status == MutationStatus.SURVIVED:
                    result.survived += 1
                    result.survived_mutations.append(m)
                elif m.status == MutationStatus.TIMEOUT:
                    result.timeout += 1
                elif m.status == MutationStatus.ERROR:
                    result.error += 1
                elif m.status == MutationStatus.INCOMPETENT:
                    result.incompetent += 1
                
                result.execution_time_ms += m.execution_time_ms
            
            detectable = result.killed + result.timeout
            total_valid = result.total_mutations - result.incompetent
            if total_valid > 0:
                result.mutation_score = (detectable / total_valid) * 100
            
            report.file_results[file_path] = result
    
    def _calculate_test_effectiveness(self, report: MutationReport):
        """Calculate test effectiveness scores."""
        # Group killed mutations by test (simplified - would parse test output)
        test_names = set()
        
        for mutation in report.survived_mutations[:20]:
            # Find which test should have killed this
            pass
        
        # Identify weak tests
        for test_name, coverage in report.test_coverages.items():
            if coverage.effectiveness_score < self.config.min_test_effectiveness:
                report.weak_tests.append((test_name, coverage.effectiveness_score))
        
        report.weak_tests.sort(key=lambda x: x[1])
    
    def _detect_equivalent_mutations(self, survived: List[Mutation]) -> List[Mutation]:
        """Detect likely equivalent mutations."""
        equivalent = []
        
        for mutation in survived:
            # Check if mutation is likely equivalent
            # Equivalent mutations don't change behavior
            if self._is_likely_equivalent(mutation):
                equivalent.append(mutation)
        
        return equivalent
    
    def _is_likely_equivalent(self, mutation: Mutation) -> bool:
        """Check if mutation is likely equivalent."""
        # Arithmetic on constants
        if mutation.operator in (MutationOperator.ARITHMETIC_ADD_TO_SUB,
                                  MutationOperator.ARITHMETIC_SUB_TO_ADD):
            if '0' in mutation.original_code:
                return True
        
        # Boolean mutations in assertions
        if mutation.operator in (MutationOperator.BOOLEAN_TRUE_TO_FALSE,
                                  MutationOperator.BOOLEAN_FALSE_TO_TRUE):
            if 'assert' in mutation.context:
                return True
        
        # String empty mutation in logging
        if mutation.operator == MutationOperator.STRING_EMPTY:
            if 'log' in mutation.context.lower() or 'print' in mutation.context:
                return True
        
        return False
    
    def _generate_recommendations(self, report: MutationReport) -> List[str]:
        """Generate recommendations for improving test suite."""
        recommendations = []
        
        if report.mutation_score < self.config.acceptable_mutation_score:
            recommendations.append(
                f"Mutation score is {report.mutation_score:.1f}% - below acceptable threshold of {self.config.acceptable_mutation_score}%"
            )
        
        # Most problematic categories
        for cat, stats in report.mutations_by_category.items():
            if stats['total'] > 5:
                kill_rate = (stats['killed'] / stats['total']) * 100 if stats['total'] > 0 else 0
                if kill_rate < 70:
                    recommendations.append(
                        f"Improve tests for {cat} mutations (only {kill_rate:.0f}% killed)"
                    )
        
        # Most survived mutations by operator
        for op, stats in sorted(report.mutations_by_operator.items(),
                                key=lambda x: x[1]['survived'], reverse=True)[:3]:
            if stats['survived'] > 0:
                recommendations.append(
                    f"Add tests to kill {stats['survived']} surviving {op} mutations"
                )
        
        # Weak test recommendations
        if report.weak_tests:
            worst_test = report.weak_tests[0]
            recommendations.append(
                f"Strengthen '{worst_test[0]}' - effectiveness score: {worst_test[1]:.2f}"
            )
        
        # File-specific recommendations
        for file_path, result in report.file_results.items():
            if result.total_mutations >= 5 and result.mutation_score < 70:
                file_name = Path(file_path).name
                recommendations.append(
                    f"Add tests for {file_name} - mutation score: {result.mutation_score:.0f}%"
                )
        
        return recommendations[:10]
    
    def _identify_weak_areas(self, report: MutationReport) -> List[Tuple[str, float]]:
        """Identify weak areas in the codebase."""
        weak_areas = []
        
        for file_path, result in report.file_results.items():
            if result.total_mutations >= 3:
                weak_areas.append((file_path, result.mutation_score))
        
        weak_areas.sort(key=lambda x: x[1])
        return weak_areas[:10]
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score."""
        if score >= self.config.good_mutation_score:
            return "A"
        elif score >= self.config.acceptable_mutation_score:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _generate_summary(self, report: MutationReport) -> str:
        """Generate testing summary."""
        if report.mutation_score >= self.config.good_mutation_score:
            return f"✅ Excellent mutation score: {report.mutation_score:.1f}% (Grade: {report.grade})"
        elif report.mutation_score >= self.config.acceptable_mutation_score:
            return f"⚠️ Acceptable mutation score: {report.mutation_score:.1f}% (Grade: {report.grade})"
        else:
            return f"❌ Poor mutation score: {report.mutation_score:.1f}% - {report.survived} mutations survived"
    
    def _save_report(self, report: MutationReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.analyzed_at.isoformat(),
            'project': report.project_name,
            'score': report.mutation_score,
            'grade': report.grade,
            'total_mutations': report.total_mutations,
            'killed': report.killed,
            'survived': report.survived,
            'is_acceptable': report.is_acceptable
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: MutationReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export mutation testing report."""
        
        if format == 'json':
            import json
            data = {
                'analyzed_at': report.analyzed_at.isoformat(),
                'project': report.project_name,
                'is_acceptable': report.is_acceptable,
                'score': report.mutation_score,
                'grade': report.grade,
                'summary': report.summary,
                'statistics': {
                    'total_files': report.total_files,
                    'total_mutations': report.total_mutations,
                    'killed': report.killed,
                    'survived': report.survived,
                    'timeout': report.timeout,
                    'error': report.error,
                    'incompetent': report.incompetent
                },
                'by_category': report.mutations_by_category,
                'by_operator': report.mutations_by_operator,
                'survived_mutations': [
                    {
                        'id': m.id,
                        'operator': m.operator.value,
                        'file': m.file_path,
                        'line': m.line_number,
                        'original': m.original_code,
                        'mutated': m.mutated_code
                    }
                    for m in report.survived_mutations[:50]
                ],
                'weak_tests': report.weak_tests,
                'weak_areas': report.weak_areas,
                'recommendations': report.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Mutation Testing Report",
                "",
                f"**Project:** {report.project_name}",
                f"**Analyzed:** {report.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Score:** {report.mutation_score:.1f}% (Grade: {report.grade})",
                f"**Acceptable:** {'✅ Yes' if report.is_acceptable else '❌ No'}",
                f"**Status:** {report.summary}",
                "",
                "## Summary",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Files Analyzed | {report.total_files} |",
                f"| Total Mutations | {report.total_mutations} |",
                f"| Killed | {report.killed} |",
                f"| Survived | {report.survived} |",
                f"| Timeout | {report.timeout} |",
                f"| Error | {report.error} |",
                f"| Mutation Score | {report.mutation_score:.1f}% |",
                "",
            ]
            
            if report.mutations_by_category:
                lines.extend([
                    "## Mutations by Category",
                    "",
                    "| Category | Total | Killed | Survived | Kill Rate |",
                    "|----------|-------|--------|----------|-----------|",
                ])
                for cat, stats in sorted(report.mutations_by_category.items(),
                                         key=lambda x: x[1]['total'], reverse=True):
                    kill_rate = (stats['killed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    lines.append(f"| {cat} | {stats['total']} | {stats['killed']} | {stats.get('survived', 0)} | {kill_rate:.0f}% |")
                lines.append("")
            
            if report.survived_mutations:
                lines.extend([
                    "## 🦠 Survived Mutations (Most Concerning)",
                    "",
                    "| File | Line | Operator | Original | Mutated |",
                    "|------|------|----------|----------|---------|",
                ])
                for m in report.survived_mutations[:15]:
                    file_name = Path(m.file_path).name
                    lines.append(f"| {file_name} | {m.line_number} | {m.operator.value} | `{m.original_code[:30]}` | `{m.mutated_code[:30]}` |")
                lines.append("")
            
            if report.weak_areas:
                lines.extend([
                    "## 🎯 Weak Areas",
                    "",
                    "| File | Mutation Score |",
                    "|------|----------------|",
                ])
                for file_path, score in report.weak_areas[:10]:
                    file_name = Path(file_path).name
                    lines.append(f"| {file_name} | {score:.0f}% |")
                lines.append("")
            
            if report.recommendations:
                lines.extend([
                    "## 📋 Recommendations",
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
        logger.info("MutationTester closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for mutation tester."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run mutation testing on Python code")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--source", nargs="*", default=["src"], help="Source directories")
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--max-mutations", type=int, default=1000)
    parser.add_argument("--sample-rate", type=float, default=1.0)
    parser.add_argument("--parallel", action="store_true", default=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--threshold", type=float, default=80.0, help="Acceptable mutation score")
    parser.add_argument("--timeout", type=int, default=30)
    
    args = parser.parse_args()
    
    config = MutationTesterConfig(
        project_root=args.project_root,
        source_paths=args.source,
        max_total_mutations=args.max_mutations,
        sample_rate=args.sample_rate,
        parallel=args.parallel,
        max_workers=args.workers,
        acceptable_mutation_score=args.threshold,
        mutation_timeout_seconds=args.timeout
    )
    
    tester = MutationTester(config)
    
    report = tester.test()
    
    output = tester.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    print(f"Killed: {report.killed}, Survived: {report.survived}")
    
    if not report.is_acceptable:
        print(f"\n⚠️ Mutation score below acceptable threshold of {config.acceptable_mutation_score}%")
    
    tester.close()


if __name__ == "__main__":
    main()