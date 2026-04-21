#!/usr/bin/env python3
"""
Test Generator - AI Development Framework
Generates comprehensive unit tests for Python code using AI.

Part of the Level 3 Generation tools (generators/test_generator.py)
This test_generator.py provides:

AST-Based Analysis - Analyzes target code to generate appropriate tests
Multiple Frameworks - Supports pytest, unittest, and Hypothesis
Comprehensive Test Types - Unit, integration, property, parametrized, edge cases, error cases
Mock Generation - Automatic mock creation for dependencies
Fixture Generation - pytest fixture generation with various scopes
Parametrized Tests - Generate data-driven tests
Edge Case Detection - Automatically identify and test edge cases
Error Case Generation - Test exception handling and error conditions
LLM-Powered Generation - Generate tests from natural language descriptions
Coverage Estimation - Estimate test coverage based on generated tests
Batch Generation - Generate tests for entire directories
Validation Integration - mypy and ruff validation for generated tests

The test generator produces high-quality, comprehensive unit tests that help ensure code correctness and facilitate test-driven development.
"""

import ast
import json
import inspect
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ...shared.llm_client import LLMClient
from ...shared.state_manager import StateManager
from ...shared.logger import get_logger
from ...level_2_analysis.scanners.ast_analyzer import ASTAnalyzer, ASTMetrics, NodeType
from ...quality.validators.mypy_validator import MypyValidator
from ...quality.validators.ruff_validator import RuffValidator
from ..refiners.iterative_refiner import IterativeRefiner

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class TestFramework(str, Enum):
    """Testing framework to use."""
    PYTEST = "pytest"
    UNITTEST = "unittest"
    HYPOTHESIS = "hypothesis"
    DOCTEST = "doctest"


class TestType(str, Enum):
    """Type of test to generate."""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    PROPERTY = "property"
    PARAMETRIZED = "parametrized"
    FIXTURE = "fixture"
    MOCK = "mock"
    EDGE_CASE = "edge_case"
    ERROR_CASE = "error_case"
    PERFORMANCE = "performance"
    REGRESSION = "regression"
    SMOKE = "smoke"


class MockStrategy(str, Enum):
    """Strategy for mocking dependencies."""
    NONE = "none"
    UNITTEST_MOCK = "unittest_mock"
    PYTEST_MOCK = "pytest_mock"
    MONKEYPATCH = "monkeypatch"
    FAKE = "fake"


class AssertionStyle(str, Enum):
    """Style of assertions."""
    STANDARD = "standard"  # assert x == y
    PYTEST_RAISES = "pytest_raises"  # with pytest.raises
    UNITTEST_ASSERT = "unittest_assert"  # self.assertEqual


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class TestCase:
    """Specification for a single test case."""
    name: str
    description: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    expected_output: Optional[Any] = None
    expected_exception: Optional[str] = None
    expected_exception_message: Optional[str] = None
    setup_code: Optional[str] = None
    teardown_code: Optional[str] = None
    mocks: Dict[str, Any] = field(default_factory=dict)
    assertions: List[str] = field(default_factory=list)
    is_parametrized: bool = False
    parametrize_values: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    skip: bool = False
    skip_reason: Optional[str] = None
    xfail: bool = False
    xfail_reason: Optional[str] = None


@dataclass
class FixtureSpec:
    """Specification for a test fixture."""
    name: str
    scope: str = "function"  # function, class, module, package, session
    autouse: bool = False
    returns: str = "Any"
    setup_code: Optional[str] = None
    teardown_code: Optional[str] = None
    params: Optional[List[Any]] = None
    description: Optional[str] = None


@dataclass
class MockSpec:
    """Specification for a mock object."""
    target: str  # What to mock (module.Class.method)
    return_value: Optional[Any] = None
    side_effect: Optional[List[Any]] = None
    spec: Optional[str] = None
    autospec: bool = True
    calls: List[Tuple[Tuple, Dict]] = field(default_factory=list)


@dataclass
class TestClassSpec:
    """Specification for a test class."""
    name: str
    target_class: str  # Class being tested
    description: Optional[str] = None
    fixtures: List[str] = field(default_factory=list)
    setup_method: Optional[str] = None
    teardown_method: Optional[str] = None
    setup_class: Optional[str] = None
    teardown_class: Optional[str] = None
    test_cases: List[TestCase] = field(default_factory=list)
    mocks: List[MockSpec] = field(default_factory=list)


@dataclass
class TestModuleSpec:
    """Complete specification for a test module."""
    name: str
    target_module: str  # Module being tested
    framework: TestFramework = TestFramework.PYTEST
    description: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    fixtures: List[FixtureSpec] = field(default_factory=list)
    test_classes: List[TestClassSpec] = field(default_factory=list)
    test_functions: List[TestCase] = field(default_factory=list)
    conftest_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedTest:
    """Result of test generation."""
    test_spec: TestModuleSpec
    code: str
    file_path: Optional[Path] = None
    validation_passed: bool = False
    mypy_errors: List[str] = field(default_factory=list)
    ruff_errors: List[str] = field(default_factory=list)
    coverage_estimate: float = 0.0
    test_count: int = 0
    iterations: int = 0
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TestGeneratorConfig:
    """Configuration for test generator."""
    framework: TestFramework = TestFramework.PYTEST
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    max_iterations: int = 3
    validate_mypy: bool = True
    validate_ruff: bool = True
    mock_strategy: MockStrategy = MockStrategy.PYTEST_MOCK
    assertion_style: AssertionStyle = AssertionStyle.STANDARD
    generate_fixtures: bool = True
    generate_parametrized: bool = True
    generate_edge_cases: bool = True
    generate_error_cases: bool = True
    generate_property_tests: bool = False
    coverage_target: float = 90.0
    include_docstrings: bool = True
    async_support: bool = True
    line_length: int = 88
    indent_size: int = 4


# ============================================================
# CODE ANALYZER FOR TEST GENERATION
# ============================================================

class TestTargetAnalyzer(ast.NodeVisitor):
    """Analyze target code for test generation."""
    
    def __init__(self, target_module: str):
        self.target_module = target_module
        self.functions: List[Dict[str, Any]] = []
        self.classes: List[Dict[str, Any]] = []
        self.imports: List[str] = []
        self.current_class: Optional[str] = None
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file for test generation."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            self.visit(tree)
            
            return {
                'functions': self.functions,
                'classes': self.classes,
                'imports': self.imports
            }
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return {'functions': [], 'classes': [], 'imports': []}
    
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(f"import {alias.name}")
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            names = ", ".join(alias.name for alias in node.names)
            self.imports.append(f"from {node.module} import {names}")
    
    def visit_ClassDef(self, node: ast.ClassDef):
        self.current_class = node.name
        
        methods = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not child.name.startswith('_') or child.name == '__init__':
                    method_info = self._extract_function_info(child, is_method=True)
                    methods.append(method_info)
        
        self.classes.append({
            'name': node.name,
            'bases': [ast.unparse(b) for b in node.bases],
            'methods': methods,
            'docstring': ast.get_docstring(node),
            'line_count': node.end_lineno - node.lineno + 1 if node.end_lineno else 1
        })
        
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        if not self.current_class:
            func_info = self._extract_function_info(node, is_method=False)
            self.functions.append(func_info)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        if not self.current_class:
            func_info = self._extract_function_info(node, is_method=False, is_async=True)
            self.functions.append(func_info)
        self.generic_visit(node)
    
    def _extract_function_info(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], 
                                is_method: bool = False, is_async: bool = False) -> Dict[str, Any]:
        """Extract function information."""
        params = []
        for arg in node.args.args:
            param_info = {
                'name': arg.arg,
                'type': ast.unparse(arg.annotation) if arg.annotation else None
            }
            
            # Check for default value
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            arg_index = node.args.args.index(arg)
            if arg_index >= defaults_offset:
                default_idx = arg_index - defaults_offset
                param_info['default'] = ast.unparse(node.args.defaults[default_idx])
            
            params.append(param_info)
        
        return {
            'name': node.name,
            'params': params,
            'return_type': ast.unparse(node.returns) if node.returns else None,
            'is_async': is_async or isinstance(node, ast.AsyncFunctionDef),
            'is_method': is_method,
            'docstring': ast.get_docstring(node),
            'decorators': [ast.unparse(d) for d in node.decorator_list],
            'line_count': node.end_lineno - node.lineno + 1 if node.end_lineno else 1
        }


# ============================================================
# TEST CODE GENERATOR
# ============================================================

class TestCodeGenerator:
    """Generate test code from specifications."""
    
    def __init__(self, config: TestGeneratorConfig):
        self.config = config
        self.indent = " " * config.indent_size
    
    def generate(self, spec: TestModuleSpec) -> str:
        """Generate complete test module code."""
        lines = []
        
        # Module docstring
        lines.extend(self._generate_module_docstring(spec))
        
        # Imports
        lines.extend(self._generate_imports(spec))
        
        # Fixtures
        if spec.fixtures:
            lines.extend(self._generate_fixtures(spec.fixtures))
        
        # Test functions
        if spec.test_functions:
            for test_case in spec.test_functions:
                lines.extend(self._generate_test_function(test_case))
        
        # Test classes
        for test_class in spec.test_classes:
            lines.extend(self._generate_test_class(test_class))
        
        # Conftest content (if needed)
        if spec.conftest_content:
            lines.append("# conftest.py content would be generated separately")
        
        return "\n".join(lines)
    
    def _generate_module_docstring(self, spec: TestModuleSpec) -> List[str]:
        """Generate module docstring."""
        lines = []
        lines.append('"""')
        lines.append(f"Unit tests for {spec.target_module}.")
        lines.append("")
        if spec.description:
            lines.append(spec.description)
        lines.append('"""')
        lines.append("")
        return lines
    
    def _generate_imports(self, spec: TestModuleSpec) -> List[str]:
        """Generate import statements."""
        lines = []
        
        # Framework imports
        if spec.framework == TestFramework.PYTEST:
            lines.append("import pytest")
            if self.config.mock_strategy == MockStrategy.PYTEST_MOCK:
                lines.append("from pytest_mock import MockerFixture")
        elif spec.framework == TestFramework.UNITTEST:
            lines.append("import unittest")
            if self.config.mock_strategy == MockStrategy.UNITTEST_MOCK:
                lines.append("from unittest.mock import Mock, patch, MagicMock")
        
        # Hypothesis for property testing
        if self.config.generate_property_tests:
            lines.append("from hypothesis import given, strategies as st")
        
        # Target module imports
        lines.append(f"from {spec.target_module} import *")
        
        # Additional imports
        for imp in spec.imports:
            if imp not in lines:
                lines.append(imp)
        
        lines.append("")
        return lines
    
    def _generate_fixtures(self, fixtures: List[FixtureSpec]) -> List[str]:
        """Generate pytest fixtures."""
        lines = []
        
        for fixture in fixtures:
            # Fixture decorator
            decorator = f"@pytest.fixture"
            if fixture.scope != "function":
                decorator += f"(scope=\"{fixture.scope}\")"
            if fixture.autouse:
                if fixture.scope != "function":
                    decorator = decorator[:-1] + f", autouse=True)"
                else:
                    decorator = f"@pytest.fixture(autouse=True)"
            lines.append(decorator)
            
            # Fixture function
            lines.append(f"def {fixture.name}() -> {fixture.returns}:")
            
            if fixture.description and self.config.include_docstrings:
                lines.append(f'{self.indent}"""{fixture.description}"""')
            
            if fixture.setup_code:
                for code_line in fixture.setup_code.split('\n'):
                    lines.append(f"{self.indent}{code_line}")
            else:
                lines.append(f"{self.indent}# TODO: Implement fixture")
                lines.append(f"{self.indent}return {{}}")
            
            if fixture.teardown_code:
                lines.append(f"{self.indent}yield result")
                for code_line in fixture.teardown_code.split('\n'):
                    lines.append(f"{self.indent}{code_line}")
            else:
                lines.append(f"{self.indent}yield {{}}")
            
            lines.append("")
        
        return lines
    
    def _generate_test_class(self, spec: TestClassSpec) -> List[str]:
        """Generate a test class."""
        lines = []
        
        # Class definition
        bases = ""
        if self.config.framework == TestFramework.UNITTEST:
            bases = "(unittest.TestCase)"
        
        lines.append(f"class {spec.name}{bases}:")
        
        if spec.description and self.config.include_docstrings:
            lines.append(f'{self.indent}"""{spec.description}"""')
        
        # Fixture requests
        if spec.fixtures:
            fixture_params = ", ".join(spec.fixtures)
            if self.config.framework == TestFramework.UNITTEST:
                lines.append(f"{self.indent}@classmethod")
                lines.append(f"{self.indent}def setUpClass(cls):")
                for fixture in spec.fixtures:
                    lines.append(f"{self.indent}{self.indent}cls.{fixture} = {fixture}()")
                lines.append("")
        
        # Setup method
        if spec.setup_method:
            setup_name = "setUp" if self.config.framework == TestFramework.UNITTEST else "setup_method"
            lines.append(f"{self.indent}def {setup_name}(self):")
            for line in spec.setup_method.split('\n'):
                lines.append(f"{self.indent}{self.indent}{line}")
            lines.append("")
        
        # Teardown method
        if spec.teardown_method:
            teardown_name = "tearDown" if self.config.framework == TestFramework.UNITTEST else "teardown_method"
            lines.append(f"{self.indent}def {teardown_name}(self):")
            for line in spec.teardown_method.split('\n'):
                lines.append(f"{self.indent}{self.indent}{line}")
            lines.append("")
        
        # Test methods
        for test_case in spec.test_cases:
            lines.extend(self._generate_test_method(test_case))
        
        return lines
    
    def _generate_test_method(self, test_case: TestCase) -> List[str]:
        """Generate a test method."""
        lines = []
        
        # Skip/xfail decorators
        if test_case.skip:
            if self.config.framework == TestFramework.PYTEST:
                reason = test_case.skip_reason or "Skipped"
                lines.append(f'{self.indent}@pytest.mark.skip(reason="{reason}")')
        elif test_case.xfail:
            if self.config.framework == TestFramework.PYTEST:
                reason = test_case.xfail_reason or "Expected to fail"
                lines.append(f'{self.indent}@pytest.mark.xfail(reason="{reason}")')
        
        # Parametrize decorator
        if test_case.is_parametrized and test_case.parametrize_values:
            if self.config.framework == TestFramework.PYTEST:
                param_names = list(test_case.parametrize_values[0].keys())
                values = [[v[k] for k in param_names] for v in test_case.parametrize_values]
                lines.append(f'{self.indent}@pytest.mark.parametrize("{", ".join(param_names)}", {values})')
        
        # Test method
        method_name = f"test_{test_case.name.replace(' ', '_').lower()}"
        
        if self.config.framework == TestFramework.UNITTEST:
            lines.append(f"{self.indent}def {method_name}(self):")
        else:
            fixture_params = ""
            lines.append(f"{self.indent}def {method_name}({fixture_params}):")
        
        if test_case.description and self.config.include_docstrings:
            lines.append(f'{self.indent}{self.indent}"""{test_case.description}"""')
        
        # Setup code
        if test_case.setup_code:
            for line in test_case.setup_code.split('\n'):
                lines.append(f"{self.indent}{self.indent}{line}")
        
        # Test body
        lines.extend(self._generate_test_body(test_case))
        
        # Teardown code
        if test_case.teardown_code:
            for line in test_case.teardown_code.split('\n'):
                lines.append(f"{self.indent}{self.indent}{line}")
        
        lines.append("")
        return lines
    
    def _generate_test_function(self, test_case: TestCase) -> List[str]:
        """Generate a standalone test function."""
        lines = []
        
        # Skip/xfail decorators
        if test_case.skip:
            if self.config.framework == TestFramework.PYTEST:
                reason = test_case.skip_reason or "Skipped"
                lines.append(f'@pytest.mark.skip(reason="{reason}")')
        elif test_case.xfail:
            if self.config.framework == TestFramework.PYTEST:
                reason = test_case.xfail_reason or "Expected to fail"
                lines.append(f'@pytest.mark.xfail(reason="{reason}")')
        
        # Parametrize decorator
        if test_case.is_parametrized and test_case.parametrize_values:
            if self.config.framework == TestFramework.PYTEST:
                param_names = list(test_case.parametrize_values[0].keys())
                values = [[v[k] for k in param_names] for v in test_case.parametrize_values]
                lines.append(f'@pytest.mark.parametrize("{", ".join(param_names)}", {values})')
        
        # Test function
        func_name = f"test_{test_case.name.replace(' ', '_').lower()}"
        lines.append(f"def {func_name}():")
        
        if test_case.description and self.config.include_docstrings:
            lines.append(f'{self.indent}"""{test_case.description}"""')
        
        # Setup code
        if test_case.setup_code:
            for line in test_case.setup_code.split('\n'):
                lines.append(f"{self.indent}{line}")
        
        # Test body
        lines.extend(self._generate_test_body(test_case))
        
        # Teardown code
        if test_case.teardown_code:
            for line in test_case.teardown_code.split('\n'):
                lines.append(f"{self.indent}{line}")
        
        lines.append("")
        return lines
    
    def _generate_test_body(self, test_case: TestCase) -> List[str]:
        """Generate test body with assertions."""
        lines = []
        
        # Build function call
        if test_case.inputs:
            args = []
            for key, value in test_case.inputs.items():
                if isinstance(value, str):
                    args.append(f"{key}={repr(value)}")
                else:
                    args.append(f"{key}={value}")
            
            func_call = f"result = target_function({', '.join(args)})"
        else:
            func_call = "result = target_function()"
        
        lines.append(f"{self.indent}{self.indent}# Arrange")
        
        # Add mocks if needed
        if test_case.mocks:
            for mock_name, mock_config in test_case.mocks.items():
                lines.append(f"{self.indent}{self.indent}{mock_name} = Mock({mock_config})")
        
        lines.append(f"{self.indent}{self.indent}# Act")
        
        # Expected exception
        if test_case.expected_exception:
            if self.config.framework == TestFramework.PYTEST:
                lines.append(f"{self.indent}{self.indent}with pytest.raises({test_case.expected_exception})")
                if test_case.expected_exception_message:
                    lines.append(f"{self.indent}{self.indent}{self.indent}match=r\"{test_case.expected_exception_message}\"")
                lines.append(f"{self.indent}{self.indent}{self.indent}{func_call}")
            else:
                lines.append(f"{self.indent}{self.indent}with self.assertRaises({test_case.expected_exception}):")
                lines.append(f"{self.indent}{self.indent}{self.indent}{func_call}")
        else:
            lines.append(f"{self.indent}{self.indent}{func_call}")
        
        lines.append(f"{self.indent}{self.indent}# Assert")
        
        # Add assertions
        if test_case.assertions:
            for assertion in test_case.assertions:
                lines.append(f"{self.indent}{self.indent}{assertion}")
        elif test_case.expected_output is not None:
            if self.config.assertion_style == AssertionStyle.STANDARD:
                lines.append(f"{self.indent}{self.indent}assert result == {repr(test_case.expected_output)}")
            elif self.config.assertion_style == AssertionStyle.UNITTEST_ASSERT:
                lines.append(f"{self.indent}{self.indent}self.assertEqual(result, {repr(test_case.expected_output)})")
        else:
            lines.append(f"{self.indent}{self.indent}assert result is not None")
        
        return lines


# ============================================================
# MAIN TEST GENERATOR
# ============================================================

class TestGenerator:
    """
    Generates comprehensive unit tests for Python code.
    
    Features:
    - Generate tests from source code analysis
    - Multiple testing frameworks (pytest, unittest)
    - Property-based testing with Hypothesis
    - Mock generation for dependencies
    - Fixture generation
    - Parametrized test generation
    - Edge case and error case generation
    - LLM-powered test generation
    - Coverage estimation
    - Iterative refinement
    """
    
    def __init__(self, config: Optional[TestGeneratorConfig] = None):
        self.config = config or TestGeneratorConfig()
        self.code_generator = TestCodeGenerator(self.config)
        self.analyzer = TestTargetAnalyzer("")
        self.llm = LLMClient() if self.config.use_llm else None
        self.state = StateManager(Path(".ai_state") / "test_generator.json")
        
        self.mypy_validator = MypyValidator() if self.config.validate_mypy else None
        self.ruff_validator = RuffValidator() if self.config.validate_ruff else None
        self.refiner = IterativeRefiner(self.llm) if self.llm else None
        
        logger.info("TestGenerator initialized")
    
    # ============================================================
    # GENERATION
    # ============================================================
    
    def generate(self, spec: TestModuleSpec, output_path: Optional[Path] = None) -> GeneratedTest:
        """
        Generate a test module from specification.
        
        Args:
            spec: Test module specification
            output_path: Optional output file path
        """
        logger.info(f"Generating tests for: {spec.target_module}")
        
        # Generate initial code
        code = self.code_generator.generate(spec)
        
        # Count test cases
        test_count = len(spec.test_functions)
        for cls in spec.test_classes:
            test_count += len(cls.test_cases)
        
        # Iterative refinement
        iteration = 0
        mypy_errors = []
        ruff_errors = []
        
        if self.refiner and self.config.max_iterations > 1:
            for iteration in range(1, self.config.max_iterations):
                if self.mypy_validator:
                    mypy_errors = self.mypy_validator.validate_string(code)
                if self.ruff_validator:
                    ruff_errors = self.ruff_validator.validate_string(code)
                
                if not mypy_errors and not ruff_errors:
                    logger.info(f"Validation passed at iteration {iteration}")
                    break
                
                logger.info(f"Iteration {iteration}: {len(mypy_errors)} mypy, {len(ruff_errors)} ruff errors")
                
                code = self.refiner.refine_test(
                    code=code,
                    spec=spec,
                    mypy_errors=mypy_errors,
                    ruff_errors=ruff_errors
                )
        
        # Final validation
        if self.mypy_validator:
            mypy_errors = self.mypy_validator.validate_string(code)
        if self.ruff_validator:
            ruff_errors = self.ruff_validator.validate_string(code)
        
        # Estimate coverage
        coverage_estimate = self._estimate_coverage(spec)
        
        # Write to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(code)
            
            # Generate conftest if needed
            if spec.conftest_content:
                conftest_path = output_path.parent / "conftest.py"
                if not conftest_path.exists():
                    conftest_path.write_text(spec.conftest_content)
        
        result = GeneratedTest(
            test_spec=spec,
            code=code,
            file_path=output_path,
            validation_passed=not (mypy_errors or ruff_errors),
            mypy_errors=mypy_errors,
            ruff_errors=ruff_errors,
            coverage_estimate=coverage_estimate,
            test_count=test_count,
            iterations=iteration
        )
        
        self._save_result(result)
        
        logger.info(f"Generated {test_count} tests for {spec.target_module}")
        return result
    
    def generate_from_file(self, 
                            file_path: Path,
                            output_path: Optional[Path] = None) -> GeneratedTest:
        """
        Generate tests by analyzing a Python file.
        
        Args:
            file_path: Path to Python file to test
            output_path: Optional output file path
        """
        logger.info(f"Generating tests from file: {file_path}")
        
        # Analyze target file
        analysis = self.analyzer.analyze_file(file_path)
        
        # Build test specification
        spec = self._build_spec_from_analysis(file_path, analysis)
        
        # Set output path if not provided
        if not output_path:
            output_path = file_path.parent / "tests" / f"test_{file_path.stem}.py"
        
        return self.generate(spec, output_path)
    
    def generate_from_description(self,
                                   description: str,
                                   target_module: str,
                                   output_path: Optional[Path] = None) -> GeneratedTest:
        """
        Generate tests from natural language description.
        
        Args:
            description: Natural language description of what to test
            target_module: Name of the module being tested
            output_path: Optional output file path
        """
        if not self.llm:
            raise ValueError("LLM is required for description-based generation")
        
        logger.info(f"Generating tests for '{target_module}' from description")
        
        spec = self._parse_description(description, target_module)
        
        return self.generate(spec, output_path)
    
    def _build_spec_from_analysis(self, file_path: Path, analysis: Dict[str, Any]) -> TestModuleSpec:
        """Build test specification from code analysis."""
        module_name = file_path.stem
        
        spec = TestModuleSpec(
            name=f"test_{module_name}",
            target_module=module_name,
            framework=self.config.framework,
            imports=analysis['imports']
        )
        
        # Generate test cases for functions
        for func in analysis['functions']:
            test_cases = self._generate_test_cases_for_function(func)
            spec.test_functions.extend(test_cases)
        
        # Generate test classes for classes
        for cls in analysis['classes']:
            test_class = TestClassSpec(
                name=f"Test{cls['name']}",
                target_class=cls['name']
            )
            
            for method in cls['methods']:
                if method['name'] != '__init__':
                    test_cases = self._generate_test_cases_for_function(method, class_name=cls['name'])
                    test_class.test_cases.extend(test_cases)
            
            if test_class.test_cases:
                spec.test_classes.append(test_class)
        
        return spec
    
    def _generate_test_cases_for_function(self, func: Dict[str, Any], 
                                           class_name: Optional[str] = None) -> List[TestCase]:
        """Generate test cases for a function."""
        test_cases = []
        func_name = func['name']
        full_name = f"{class_name}.{func_name}" if class_name else func_name
        
        # Basic success case
        success_case = TestCase(
            name=f"test_{full_name}_success",
            description=f"Test successful {func_name} execution.",
            inputs=self._generate_sample_inputs(func['params']),
            expected_output=self._generate_expected_output(func['return_type']),
            tags=["smoke", "unit"]
        )
        test_cases.append(success_case)
        
        # Edge cases if configured
        if self.config.generate_edge_cases:
            edge_cases = self._generate_edge_cases(func)
            test_cases.extend(edge_cases)
        
        # Error cases if configured
        if self.config.generate_error_cases:
            error_cases = self._generate_error_cases(func)
            test_cases.extend(error_cases)
        
        return test_cases
    
    def _generate_sample_inputs(self, params: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate sample inputs for parameters."""
        inputs = {}
        
        for param in params:
            param_type = param.get('type', 'Any')
            
            if param_type == 'str':
                inputs[param['name']] = f"test_{param['name']}"
            elif param_type == 'int':
                inputs[param['name']] = 42
            elif param_type == 'float':
                inputs[param['name']] = 3.14
            elif param_type == 'bool':
                inputs[param['name']] = True
            elif 'List' in param_type:
                inputs[param['name']] = []
            elif 'Dict' in param_type:
                inputs[param['name']] = {}
            elif 'Optional' in param_type:
                inputs[param['name']] = None
            else:
                inputs[param['name']] = None
        
        return inputs
    
    def _generate_expected_output(self, return_type: Optional[str]) -> Any:
        """Generate expected output based on return type."""
        if not return_type or return_type == 'None':
            return None
        elif return_type == 'str':
            return "expected_result"
        elif return_type == 'int':
            return 42
        elif return_type == 'float':
            return 3.14
        elif return_type == 'bool':
            return True
        elif 'List' in return_type:
            return []
        elif 'Dict' in return_type:
            return {}
        return "expected_result"
    
    def _generate_edge_cases(self, func: Dict[str, Any]) -> List[TestCase]:
        """Generate edge case tests."""
        edge_cases = []
        func_name = func['name']
        
        # Empty inputs
        if func['params']:
            empty_case = TestCase(
                name=f"test_{func_name}_empty_inputs",
                description=f"Test {func_name} with empty/default inputs.",
                inputs={p['name']: self._get_empty_value(p.get('type')) for p in func['params']},
                tags=["edge_case"]
            )
            edge_cases.append(empty_case)
        
        # Boundary values for numeric types
        for param in func['params']:
            param_type = param.get('type', '')
            if 'int' in param_type:
                boundary_case = TestCase(
                    name=f"test_{func_name}_{param['name']}_boundary",
                    description=f"Test {func_name} with boundary values for {param['name']}.",
                    inputs={**{p['name']: 0 for p in func['params']}, param['name']: 0},
                    tags=["edge_case", "boundary"]
                )
                edge_cases.append(boundary_case)
                break
        
        return edge_cases
    
    def _generate_error_cases(self, func: Dict[str, Any]) -> List[TestCase]:
        """Generate error case tests."""
        error_cases = []
        func_name = func['name']
        
        # Invalid type case
        for param in func['params']:
            if param.get('type') == 'int':
                invalid_case = TestCase(
                    name=f"test_{func_name}_{param['name']}_invalid_type",
                    description=f"Test {func_name} with invalid type for {param['name']}.",
                    inputs={**{p['name']: 0 for p in func['params']}, param['name']: "not_an_int"},
                    expected_exception="TypeError" if not func.get('is_async') else None,
                    tags=["error_case"]
                )
                error_cases.append(invalid_case)
                break
        
        return error_cases
    
    def _get_empty_value(self, type_hint: Optional[str]) -> Any:
        """Get empty value for a type."""
        if not type_hint:
            return None
        elif type_hint == 'str':
            return ""
        elif type_hint == 'int':
            return 0
        elif type_hint == 'float':
            return 0.0
        elif type_hint == 'bool':
            return False
        elif 'List' in type_hint:
            return []
        elif 'Dict' in type_hint:
            return {}
        return None
    
    def _parse_description(self, description: str, target_module: str) -> TestModuleSpec:
        """Parse natural language description into TestModuleSpec."""
        prompt = f"""
        Parse this test description into a structured test specification:
        
        Target Module: {target_module}
        Description: {description}
        
        Return a JSON object with:
        - test_cases: list of test cases with name, description, inputs, expected_output
        - fixtures: list of required fixtures
        - edge_cases: list of edge case tests
        - error_cases: list of error case tests
        
        Output only valid JSON.
        """
        
        response = self.llm.complete_json(prompt)
        
        spec = TestModuleSpec(
            name=f"test_{target_module}",
            target_module=target_module,
            framework=self.config.framework
        )
        
        # Parse test cases
        for case_data in response.get('test_cases', []):
            test_case = TestCase(
                name=case_data['name'],
                description=case_data.get('description', ''),
                inputs=case_data.get('inputs', {}),
                expected_output=case_data.get('expected_output')
            )
            spec.test_functions.append(test_case)
        
        return spec
    
    def _estimate_coverage(self, spec: TestModuleSpec) -> float:
        """Estimate test coverage based on specification."""
        # Simple estimation based on test cases
        total_elements = len(spec.test_functions) + sum(len(c.test_cases) for c in spec.test_classes)
        
        if total_elements == 0:
            return 0.0
        
        # Assume each test covers about 5-10% of the target
        estimated = min(total_elements * 7.5, 95.0)
        return estimated
    
    # ============================================================
    # BATCH GENERATION
    # ============================================================
    
    def generate_for_directory(self,
                                directory: Path,
                                recursive: bool = True,
                                output_dir: Optional[Path] = None) -> List[GeneratedTest]:
        """Generate tests for all Python files in a directory."""
        results = []
        
        pattern = "**/*.py" if recursive else "*.py"
        for file_path in directory.glob(pattern):
            if file_path.name.startswith('test_') or file_path.name == '__init__.py':
                continue
            
            if output_dir:
                rel_path = file_path.relative_to(directory)
                test_path = output_dir / "tests" / f"test_{rel_path}"
            else:
                test_path = file_path.parent / "tests" / f"test_{file_path.name}"
            
            result = self.generate_from_file(file_path, test_path)
            results.append(result)
        
        logger.info(f"Generated tests for {len(results)} files")
        return results
    
    # ============================================================
    # VALIDATION AND EXPORT
    # ============================================================
    
    def _save_result(self, result: GeneratedTest):
        """Save generation result to state."""
        history = self.state.get('history', [])
        history.append({
            'target_module': result.test_spec.target_module,
            'file_path': str(result.file_path) if result.file_path else None,
            'validation_passed': result.validation_passed,
            'test_count': result.test_count,
            'coverage_estimate': result.coverage_estimate,
            'iterations': result.iterations,
            'generated_at': result.generated_at.isoformat()
        })
        
        if len(history) > 100:
            history = history[-100:]
        
        self.state.set('history', history)
        self.state.save()
    
    def export_spec(self, spec: TestModuleSpec, output_path: Optional[Path] = None) -> str:
        """Export test specification as JSON."""
        data = {
            'name': spec.name,
            'target_module': spec.target_module,
            'framework': spec.framework.value,
            'test_functions_count': len(spec.test_functions),
            'test_classes_count': len(spec.test_classes)
        }
        
        content = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("TestGenerator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for test generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate unit tests for Python code")
    parser.add_argument("target", type=Path, help="Python file or directory to generate tests for")
    parser.add_argument("--output", "-o", type=Path, help="Output file or directory")
    parser.add_argument("--framework", choices=[f.value for f in TestFramework],
                       default=TestFramework.PYTEST.value, help="Testing framework")
    parser.add_argument("--recursive", "-r", action="store_true", help="Process directories recursively")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    parser.add_argument("--edge-cases", action="store_true", help="Generate edge case tests")
    parser.add_argument("--error-cases", action="store_true", help="Generate error case tests")
    parser.add_argument("--property-tests", action="store_true", help="Generate property-based tests")
    
    args = parser.parse_args()
    
    config = TestGeneratorConfig(
        framework=TestFramework(args.framework),
        use_llm=not args.no_llm,
        generate_edge_cases=args.edge_cases,
        generate_error_cases=args.error_cases,
        generate_property_tests=args.property_tests
    )
    
    generator = TestGenerator(config)
    
    if args.target.is_file():
        result = generator.generate_from_file(args.target, args.output)
        print(f"Generated {result.test_count} tests for {args.target}")
        if args.output:
            print(f"Tests written to {args.output}")
    else:
        results = generator.generate_for_directory(args.target, args.recursive, args.output)
        total_tests = sum(r.test_count for r in results)
        print(f"Generated {total_tests} tests across {len(results)} files")
    
    generator.close()


if __name__ == "__main__":
    main()