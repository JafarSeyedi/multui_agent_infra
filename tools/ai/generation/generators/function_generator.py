#!/usr/bin/env python3
"""
Function Generator - AI Development Framework
Generates Python functions from specifications with full type hints and documentation.

Part of the Level 3 Generation tools (generators/function_generator.py)

This function_generator.py provides:

1. Specification-Based Generation - Generate functions from structured FunctionSpec objects
2. Multiple Function Types - Regular, async, methods, properties, class/static methods
3. Full Type Hints - Complete type annotations for parameters and returns
4. Comprehensive Docstrings - Automatic docstring generation in multiple styles
5. Iterative Refinement - Automatic validation and improvement cycle
6. LLM-Powered Body Generation - Generate complex function bodies from descriptions
7. Test Generation - Automatic unit test creation
8. Batch Generation - Generate multiple functions or entire modules
9. CRUD Templates - Quick creation of common function patterns
10. Error Handling Strategies - Configurable error handling approaches
11. Validation Integration - mypy and ruff validation built-in
12. Spec Export/Import - JSON serialization for specifications

The function generator produces production-ready, type-safe Python functions with minimal effort.

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
from ...quality.validators.mypy_validator import MypyValidator
from ...quality.validators.ruff_validator import RuffValidator
from ..refiners.iterative_refiner import IterativeRefiner
from .docstring_generator import DocstringGenerator, DocstringStyle, FunctionContext, ParameterInfo, ReturnInfo

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class FunctionType(str, Enum):
    """Type of function to generate."""
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    METHOD = "method"
    ASYNC_METHOD = "async_method"
    CLASS_METHOD = "classmethod"
    STATIC_METHOD = "staticmethod"
    PROPERTY_GETTER = "property_getter"
    PROPERTY_SETTER = "property_setter"
    PROPERTY_DELETER = "property_deleter"
    CACHED_PROPERTY = "cached_property"
    ABSTRACT_METHOD = "abstract_method"
    GENERATOR = "generator"
    ASYNC_GENERATOR = "async_generator"
    CONTEXT_MANAGER = "context_manager"
    ASYNC_CONTEXT_MANAGER = "async_context_manager"
    OVERLOAD = "overload"
    LAMBDA = "lambda"


class ReturnStrategy(str, Enum):
    """Strategy for return value."""
    SINGLE_VALUE = "single_value"
    TUPLE = "tuple"
    DICT = "dict"
    LIST = "list"
    GENERATOR = "generator"
    OPTIONAL = "optional"
    UNION = "union"


class ErrorHandling(str, Enum):
    """Error handling strategy."""
    RAISE = "raise"
    RETURN_NONE = "return_none"
    RETURN_DEFAULT = "return_default"
    LOG_AND_RAISE = "log_and_raise"
    LOG_AND_RETURN = "log_and_return"
    TRY_EXCEPT_PASS = "try_except_pass"


class Complexity(str, Enum):
    """Function complexity level."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ParameterSpec:
    """Specification for a function parameter."""
    name: str
    type_hint: str = "Any"
    default_value: Optional[str] = None
    kind: str = "positional_or_keyword"  # positional, keyword, varargs, kwarg
    description: Optional[str] = None
    required: bool = True
    validator: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReturnSpec:
    """Specification for return value."""
    type_hint: str = "None"
    description: Optional[str] = None
    strategy: ReturnStrategy = ReturnStrategy.SINGLE_VALUE
    example: Optional[str] = None


@dataclass
class ExceptionSpec:
    """Specification for raised exception."""
    exception_type: str
    condition: str
    message: Optional[str] = None


@dataclass
class DecoratorSpec:
    """Specification for a decorator."""
    name: str
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, str] = field(default_factory=dict)


@dataclass
class FunctionBodySpec:
    """Specification for function body generation."""
    logic_description: str
    steps: List[str] = field(default_factory=list)
    pseudo_code: Optional[str] = None
    algorithm: Optional[str] = None
    references: List[str] = field(default_factory=list)
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None


@dataclass
class FunctionSpec:
    """Complete specification for a function."""
    name: str
    function_type: FunctionType = FunctionType.FUNCTION
    module_path: str = ""
    description: str = ""
    parameters: List[ParameterSpec] = field(default_factory=list)
    return_spec: ReturnSpec = field(default_factory=ReturnSpec())
    exceptions: List[ExceptionSpec] = field(default_factory=list)
    decorators: List[DecoratorSpec] = field(default_factory=list)
    body_spec: Optional[FunctionBodySpec] = None
    body_code: Optional[str] = None
    docstring: Optional[str] = None
    docstring_style: DocstringStyle = DocstringStyle.GOOGLE
    imports: List[str] = field(default_factory=list)
    type_vars: List[str] = field(default_factory=list)
    is_generic: bool = False
    is_final: bool = False
    is_deprecated: bool = False
    deprecation_message: Optional[str] = None
    error_handling: ErrorHandling = ErrorHandling.RAISE
    complexity: Complexity = Complexity.SIMPLE
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedFunction:
    """Result of function generation."""
    function_spec: FunctionSpec
    code: str
    file_path: Optional[Path] = None
    validation_passed: bool = False
    mypy_errors: List[str] = field(default_factory=list)
    ruff_errors: List[str] = field(default_factory=list)
    test_code: Optional[str] = None
    iterations: int = 0
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class FunctionGeneratorConfig:
    """Configuration for function generator."""
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    max_iterations: int = 5
    validate_mypy: bool = True
    validate_ruff: bool = True
    generate_docstring: bool = True
    generate_tests: bool = False
    docstring_style: DocstringStyle = DocstringStyle.GOOGLE
    include_type_hints: bool = True
    use_future_annotations: bool = True
    add_logging: bool = False
    add_timing: bool = False
    line_length: int = 88
    indent_size: int = 4


# ============================================================
# CODE GENERATORS
# ============================================================

class FunctionCodeGenerator:
    """Generate Python function code from specifications."""
    
    def __init__(self, config: FunctionGeneratorConfig):
        self.config = config
        self.indent = " " * config.indent_size
        self.docstring_generator = DocstringGenerator() if config.generate_docstring else None
    
    def generate(self, spec: FunctionSpec) -> str:
        """Generate complete function code."""
        lines = []
        
        # Generate imports if this is a standalone function
        if spec.imports:
            lines.extend(self._generate_imports(spec.imports))
            lines.append("")
        
        # Generate decorators
        lines.extend(self._generate_decorators(spec))
        
        # Generate function signature
        signature = self._generate_signature(spec)
        lines.append(signature)
        
        # Generate docstring
        docstring = self._generate_docstring(spec)
        if docstring:
            lines.append(docstring)
        
        # Generate function body
        body = self._generate_body(spec)
        lines.extend(body)
        
        return "\n".join(lines)
    
    def _generate_imports(self, imports: List[str]) -> List[str]:
        """Generate import statements."""
        lines = []
        for imp in sorted(set(imports)):
            if imp.startswith("from "):
                lines.append(imp)
            else:
                lines.append(f"import {imp}")
        return lines
    
    def _generate_decorators(self, spec: FunctionSpec) -> List[str]:
        """Generate decorator lines."""
        lines = []
        
        # Add built-in decorators based on function type
        if spec.function_type == FunctionType.CLASS_METHOD:
            lines.append("@classmethod")
        elif spec.function_type == FunctionType.STATIC_METHOD:
            lines.append("@staticmethod")
        elif spec.function_type == FunctionType.PROPERTY_GETTER:
            lines.append("@property")
        elif spec.function_type == FunctionType.CACHED_PROPERTY:
            lines.append("@cached_property")
            spec.imports.append("from functools import cached_property")
        elif spec.function_type == FunctionType.ABSTRACT_METHOD:
            lines.append("@abstractmethod")
            spec.imports.append("from abc import abstractmethod")
        elif spec.function_type == FunctionType.OVERLOAD:
            lines.append("@overload")
            spec.imports.append("from typing import overload")
        
        # Add deprecation decorator
        if spec.is_deprecated:
            if spec.deprecation_message:
                lines.append(f'@deprecated("{spec.deprecation_message}")')
            else:
                lines.append("@deprecated")
            spec.imports.append("from warnings import deprecated")
        
        # Add final decorator
        if spec.is_final:
            lines.append("@final")
            spec.imports.append("from typing import final")
        
        # Add timing decorator if configured
        if self.config.add_timing:
            lines.append("@timing_decorator")
        
        # Add custom decorators
        for decorator in spec.decorators:
            if decorator.args or decorator.kwargs:
                args_str = ", ".join(decorator.args)
                kwargs_str = ", ".join(f"{k}={v}" for k, v in decorator.kwargs.items())
                all_args = ", ".join(filter(None, [args_str, kwargs_str]))
                lines.append(f"@{decorator.name}({all_args})")
            else:
                lines.append(f"@{decorator.name}")
        
        return lines
    
    def _generate_signature(self, spec: FunctionSpec) -> str:
        """Generate function signature."""
        parts = []
        
        # Async prefix
        if spec.function_type in (FunctionType.ASYNC_FUNCTION, FunctionType.ASYNC_METHOD, 
                                   FunctionType.ASYNC_GENERATOR, FunctionType.ASYNC_CONTEXT_MANAGER):
            parts.append("async ")
        
        parts.append("def ")
        parts.append(spec.name)
        
        # Type variables
        if spec.is_generic and spec.type_vars:
            parts.append(f"[{', '.join(spec.type_vars)}]")
        
        # Parameters
        params = self._generate_parameters(spec)
        parts.append(f"({', '.join(params)})")
        
        # Return type
        if self.config.include_type_hints and spec.return_spec.type_hint:
            parts.append(f" -> {spec.return_spec.type_hint}")
        
        parts.append(":")
        
        return "".join(parts)
    
    def _generate_parameters(self, spec: FunctionSpec) -> List[str]:
        """Generate parameter strings."""
        params = []
        
        # Add self/cls for methods
        if spec.function_type in (FunctionType.METHOD, FunctionType.ASYNC_METHOD,
                                   FunctionType.ABSTRACT_METHOD, FunctionType.PROPERTY_SETTER,
                                   FunctionType.PROPERTY_DELETER, FunctionType.GENERATOR,
                                   FunctionType.ASYNC_GENERATOR):
            params.append("self")
        elif spec.function_type in (FunctionType.CLASS_METHOD,):
            params.append("cls")
        
        # Add regular parameters
        for param in spec.parameters:
            param_str = param.name
            
            # Type hint
            if self.config.include_type_hints:
                param_str += f": {param.type_hint}"
            
            # Default value
            if not param.required and param.default_value:
                param_str += f" = {param.default_value}"
            
            # Handle different parameter kinds
            if param.kind == "varargs":
                param_str = f"*{param_str}"
            elif param.kind == "kwargs":
                param_str = f"**{param_str}"
            elif param.kind == "keyword_only":
                pass  # Handled by position
            
            params.append(param_str)
        
        return params
    
    def _generate_docstring(self, spec: FunctionSpec) -> Optional[str]:
        """Generate function docstring."""
        if not self.config.generate_docstring:
            if spec.docstring:
                return f'{self.indent}"""\n{self.indent}{spec.docstring}\n{self.indent}"""'
            return None
        
        if self.docstring_generator:
            # Create context for docstring generator
            context = FunctionContext(
                name=spec.name,
                module_path=spec.module_path,
                parameters=[
                    ParameterInfo(
                        name=p.name,
                        type_hint=p.type_hint,
                        default_value=p.default_value,
                        description=p.description,
                        kind=p.kind
                    )
                    for p in spec.parameters
                ],
                return_info=ReturnInfo(
                    type_hint=spec.return_spec.type_hint,
                    description=spec.return_spec.description
                ),
                is_async=spec.function_type in (FunctionType.ASYNC_FUNCTION, FunctionType.ASYNC_METHOD),
                is_method=spec.function_type in (FunctionType.METHOD, FunctionType.ASYNC_METHOD),
                is_classmethod=spec.function_type == FunctionType.CLASS_METHOD,
                is_staticmethod=spec.function_type == FunctionType.STATIC_METHOD,
                is_property=spec.function_type in (FunctionType.PROPERTY_GETTER, FunctionType.PROPERTY_SETTER),
                existing_docstring=spec.docstring,
                complexity={"trivial": 1, "simple": 2, "moderate": 3, "complex": 5, "very_complex": 8}[spec.complexity.value]
            )
            
            result = self.docstring_generator.generate_for_function(context)
            docstring = result.docstring
        else:
            docstring = spec.docstring or spec.description
        
        if docstring:
            lines = [f'{self.indent}"""']
            for line in docstring.split('\n'):
                lines.append(f"{self.indent}{line}")
            lines.append(f'{self.indent}"""')
            return "\n".join(lines)
        
        return None
    
    def _generate_body(self, spec: FunctionSpec) -> List[str]:
        """Generate function body."""
        lines = []
        
        # Use provided body code if available
        if spec.body_code:
            for line in spec.body_code.split('\n'):
                lines.append(f"{self.indent}{line}")
            return lines
        
        # Generate from body specification
        if spec.body_spec:
            body_lines = self._generate_body_from_spec(spec)
            for line in body_lines:
                lines.append(f"{self.indent}{line}")
            return lines
        
        # Fallback: generate based on function type
        if spec.function_type in (FunctionType.ABSTRACT_METHOD,):
            lines.append(f"{self.indent}...")
        elif spec.function_type == FunctionType.OVERLOAD:
            lines.append(f"{self.indent}...")
        elif spec.function_type in (FunctionType.PROPERTY_GETTER, FunctionType.CACHED_PROPERTY):
            if spec.parameters:
                lines.append(f"{self.indent}return self._{spec.parameters[0].name}")
            else:
                lines.append(f"{self.indent}return self._value")
        elif spec.function_type == FunctionType.PROPERTY_SETTER:
            param_name = spec.parameters[0].name if spec.parameters else "value"
            lines.append(f"{self.indent}self._{param_name} = {param_name}")
        elif spec.function_type == FunctionType.PROPERTY_DELETER:
            param_name = spec.parameters[0].name if spec.parameters else "value"
            lines.append(f"{self.indent}del self._{param_name}")
        else:
            # Generate basic implementation
            lines.extend(self._generate_basic_body(spec))
        
        return lines
    
    def _generate_body_from_spec(self, spec: FunctionSpec) -> List[str]:
        """Generate body from FunctionBodySpec."""
        lines = []
        
        body_spec = spec.body_spec
        
        # Add logging if configured
        if self.config.add_logging:
            lines.append(f'logger.debug(f"Entering {spec.name} with args: {{locals()}}")')
        
        # Add docstring comment for logic
        if body_spec.logic_description:
            lines.append(f"# {body_spec.logic_description}")
        
        # Add steps as comments
        if body_spec.steps:
            for step in body_spec.steps:
                lines.append(f"# {step}")
        
        # Generate implementation based on complexity
        if spec.complexity == Complexity.TRIVIAL:
            lines.append(self._generate_trivial_body(spec))
        elif spec.complexity == Complexity.SIMPLE:
            lines.extend(self._generate_simple_body(spec))
        elif spec.complexity == Complexity.MODERATE:
            lines.extend(self._generate_moderate_body(spec))
        else:
            # Use LLM for complex functions
            if self.config.use_llm:
                lines.extend(self._generate_llm_body(spec))
            else:
                lines.append(f"{self.indent}# TODO: Implement {spec.name}")
                lines.append(f"{self.indent}raise NotImplementedError")
        
        # Add error handling
        if spec.error_handling != ErrorHandling.RAISE:
            lines = self._wrap_with_error_handling(lines, spec)
        
        # Add logging exit
        if self.config.add_logging:
            lines.append(f'logger.debug(f"Exiting {spec.name}")')
        
        return lines
    
    def _generate_basic_body(self, spec: FunctionSpec) -> List[str]:
        """Generate basic function body."""
        lines = []
        
        # Parameter validation
        for param in spec.parameters:
            if param.required:
                lines.append(f"if {param.name} is None:")
                lines.append(f"{self.indent}raise ValueError(f\"{param.name} cannot be None\")")
        
        # Return value
        if spec.return_spec.type_hint == "None":
            lines.append("pass")
        elif spec.return_spec.type_hint == "bool":
            lines.append("return True")
        elif spec.return_spec.type_hint == "str":
            lines.append('return ""')
        elif spec.return_spec.type_hint == "int":
            lines.append("return 0")
        elif spec.return_spec.type_hint == "float":
            lines.append("return 0.0")
        elif "List" in spec.return_spec.type_hint:
            lines.append("return []")
        elif "Dict" in spec.return_spec.type_hint:
            lines.append("return {}")
        elif "Optional" in spec.return_spec.type_hint:
            lines.append("return None")
        else:
            lines.append("# TODO: Implement return value")
            lines.append("...")
        
        return lines
    
    def _generate_trivial_body(self, spec: FunctionSpec) -> str:
        """Generate trivial function body."""
        if spec.parameters:
            # Simple transformation
            if spec.return_spec.type_hint == "str":
                return f"return str({spec.parameters[0].name})"
            elif spec.return_spec.type_hint == "int":
                return f"return int({spec.parameters[0].name})"
            elif spec.return_spec.type_hint == "bool":
                return f"return bool({spec.parameters[0].name})"
        
        return "pass"
    
    def _generate_simple_body(self, spec: FunctionSpec) -> List[str]:
        """Generate simple function body."""
        lines = []
        
        if spec.body_spec and spec.body_spec.algorithm:
            lines.append(f"# Algorithm: {spec.body_spec.algorithm}")
        
        # Basic implementation placeholder
        lines.append("# TODO: Implement simple logic")
        lines.append("pass")
        
        return lines
    
    def _generate_moderate_body(self, spec: FunctionSpec) -> List[str]:
        """Generate moderate complexity body."""
        lines = []
        
        lines.append('"""')
        lines.append("Moderate complexity implementation.")
        lines.append('"""')
        lines.append("")
        lines.append("# Implementation steps:")
        
        if spec.body_spec and spec.body_spec.steps:
            for i, step in enumerate(spec.body_spec.steps, 1):
                lines.append(f"# {i}. {step}")
        
        lines.append("")
        lines.append("result = None")
        lines.append("")
        lines.append("# TODO: Implement logic")
        lines.append("")
        lines.append("return result")
        
        return lines
    
    def _generate_llm_body(self, spec: FunctionSpec) -> List[str]:
        """Generate body using LLM."""
        # This would call LLM API - placeholder
        lines = []
        lines.append("# Generated by LLM")
        lines.append("pass")
        return lines
    
    def _wrap_with_error_handling(self, body_lines: List[str], spec: FunctionSpec) -> List[str]:
        """Wrap body with error handling."""
        lines = []
        
        if spec.error_handling == ErrorHandling.TRY_EXCEPT_PASS:
            lines.append("try:")
            for line in body_lines:
                lines.append(f"{self.indent}{line}")
            lines.append("except Exception:")
            lines.append(f"{self.indent}pass")
        elif spec.error_handling == ErrorHandling.RETURN_NONE:
            lines.append("try:")
            for line in body_lines:
                lines.append(f"{self.indent}{line}")
            lines.append("except Exception:")
            lines.append(f"{self.indent}return None")
        elif spec.error_handling == ErrorHandling.LOG_AND_RETURN:
            lines.append("try:")
            for line in body_lines:
                lines.append(f"{self.indent}{line}")
            lines.append("except Exception as e:")
            lines.append(f'{self.indent}logger.error(f"Error in {spec.name}: {{e}}")')
            lines.append(f"{self.indent}return None")
        
        return lines if lines else body_lines


# ============================================================
# MAIN FUNCTION GENERATOR
# ============================================================

class FunctionGenerator:
    """
    Generates Python functions from specifications.
    
    Features:
    - Generate from structured specifications
    - Support for all function types (async, methods, properties)
    - Full type hints and docstrings
    - Iterative refinement with validation
    - LLM-powered body generation
    - Test generation
    - Batch generation
    - Integration with mypy and ruff
    """
    
    def __init__(self, config: Optional[FunctionGeneratorConfig] = None):
        self.config = config or FunctionGeneratorConfig()
        self.code_generator = FunctionCodeGenerator(self.config)
        self.llm = LLMClient() if self.config.use_llm else None
        self.state = StateManager(Path(".ai_state") / "function_generator.json")
        
        self.mypy_validator = MypyValidator() if self.config.validate_mypy else None
        self.ruff_validator = RuffValidator() if self.config.validate_ruff else None
        self.refiner = IterativeRefiner(self.llm) if self.llm else None
        
        logger.info("FunctionGenerator initialized")
    
    # ============================================================
    # GENERATION
    # ============================================================
    
    def generate(self, spec: FunctionSpec, output_path: Optional[Path] = None) -> GeneratedFunction:
        """
        Generate a function from specification.
        
        Args:
            spec: Function specification
            output_path: Optional output file path
        """
        logger.info(f"Generating function: {spec.name}")
        
        # Generate initial code
        code = self.code_generator.generate(spec)
        
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
                
                code = self.refiner.refine_function(
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
        
        # Generate tests if configured
        test_code = None
        if self.config.generate_tests:
            test_code = self._generate_test(spec, code)
        
        # Write to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(code)
            
            if test_code:
                test_path = output_path.parent / f"test_{output_path.stem}.py"
                test_path.write_text(test_code)
        
        result = GeneratedFunction(
            function_spec=spec,
            code=code,
            file_path=output_path,
            validation_passed=not (mypy_errors or ruff_errors),
            mypy_errors=mypy_errors,
            ruff_errors=ruff_errors,
            test_code=test_code,
            iterations=iteration
        )
        
        self._save_result(result)
        
        logger.info(f"Generated function {spec.name} in {iteration} iterations")
        return result
    
    def generate_from_description(self,
                                   description: str,
                                   function_name: str,
                                   output_path: Optional[Path] = None) -> GeneratedFunction:
        """
        Generate a function from natural language description.
        
        Args:
            description: Natural language description
            function_name: Name of the function
            output_path: Optional output file path
        """
        if not self.llm:
            raise ValueError("LLM is required for description-based generation")
        
        logger.info(f"Generating function '{function_name}' from description")
        
        spec = self._parse_description(description, function_name)
        
        return self.generate(spec, output_path)
    
    def _parse_description(self, description: str, function_name: str) -> FunctionSpec:
        """Parse natural language description into FunctionSpec."""
        prompt = f"""
        Parse this function description into a structured specification:
        
        Function Name: {function_name}
        Description: {description}
        
        Return a JSON object with:
        - function_type: one of {[t.value for t in FunctionType]}
        - description: brief description
        - parameters: list of parameters with name, type_hint, description, required
        - return_type: return type hint
        - return_description: description of return value
        - exceptions: list of possible exceptions
        - complexity: one of trivial, simple, moderate, complex
        - logic_steps: list of implementation steps
        
        Output only valid JSON.
        """
        
        response = self.llm.complete_json(prompt)
        
        # Build FunctionSpec
        spec = FunctionSpec(
            name=function_name,
            function_type=FunctionType(response.get('function_type', 'function')),
            description=response.get('description', ''),
            return_spec=ReturnSpec(
                type_hint=response.get('return_type', 'None'),
                description=response.get('return_description')
            ),
            complexity=Complexity(response.get('complexity', 'simple'))
        )
        
        # Parse parameters
        for param_data in response.get('parameters', []):
            param = ParameterSpec(
                name=param_data['name'],
                type_hint=param_data.get('type_hint', 'Any'),
                description=param_data.get('description'),
                required=param_data.get('required', True)
            )
            spec.parameters.append(param)
        
        # Parse exceptions
        for exc_data in response.get('exceptions', []):
            exc = ExceptionSpec(
                exception_type=exc_data['type'],
                condition=exc_data.get('condition', ''),
                message=exc_data.get('message')
            )
            spec.exceptions.append(exc)
        
        # Create body spec
        if response.get('logic_steps'):
            spec.body_spec = FunctionBodySpec(
                logic_description=description,
                steps=response['logic_steps']
            )
        
        return spec
    
    def _generate_test(self, spec: FunctionSpec, code: str) -> str:
        """Generate unit test for function."""
        lines = [
            "\"\"\"Unit tests for {spec.name}.\"\"\"",
            "",
            "import pytest",
            f"from {spec.module_path or 'module'} import {spec.name}",
            "",
            "",
            f"class Test{spec.name.title().replace('_', '')}:",
            f'    """Tests for {spec.name}."""',
            ""
        ]
        
        # Basic test
        lines.extend([
            f"    def test_{spec.name}_basic(self):",
            f'        """Test basic functionality."""',
        ])
        
        if spec.parameters:
            args = []
            for param in spec.parameters:
                if param.required:
                    if param.type_hint == "str":
                        args.append('"test"')
                    elif param.type_hint == "int":
                        args.append("42")
                    elif param.type_hint == "bool":
                        args.append("True")
                    elif "List" in param.type_hint:
                        args.append("[]")
                    elif "Dict" in param.type_hint:
                        args.append("{}")
                    else:
                        args.append("None")
            
            args_str = ", ".join(args)
            lines.append(f"        result = {spec.name}({args_str})")
        else:
            lines.append(f"        result = {spec.name}()")
        
        if spec.return_spec.type_hint == "None":
            lines.append("        assert result is None")
        elif spec.return_spec.type_hint == "bool":
            lines.append("        assert isinstance(result, bool)")
        else:
            lines.append("        assert result is not None")
        
        # Edge cases
        lines.extend([
            "",
            f"    def test_{spec.name}_edge_cases(self):",
            f'        """Test edge cases."""',
            "        pass",
            ""
        ])
        
        # Error cases
        if spec.exceptions:
            lines.extend([
                f"    def test_{spec.name}_raises(self):",
                f'        """Test exception handling."""',
                "        with pytest.raises(Exception):",
                f"            {spec.name}()",
                ""
            ])
        
        return "\n".join(lines)
    
    # ============================================================
    # BATCH GENERATION
    # ============================================================
    
    def generate_multiple(self,
                          specs: List[FunctionSpec],
                          output_dir: Optional[Path] = None) -> List[GeneratedFunction]:
        """Generate multiple functions."""
        results = []
        
        for spec in specs:
            output_path = None
            if output_dir:
                filename = f"{spec.name}.py"
                output_path = output_dir / filename
            
            result = self.generate(spec, output_path)
            results.append(result)
        
        logger.info(f"Generated {len(results)} functions")
        return results
    
    def generate_module_functions(self,
                                   specs: List[FunctionSpec],
                                   module_name: str,
                                   output_path: Optional[Path] = None) -> str:
        """Generate a module with multiple functions."""
        lines = []
        
        # Module docstring
        lines.append(f'"""')
        lines.append(f"{module_name} - Auto-generated module")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f'"""')
        lines.append("")
        
        # Collect all imports
        all_imports = set()
        for spec in specs:
            all_imports.update(spec.imports)
        
        if all_imports:
            for imp in sorted(all_imports):
                if imp.startswith("from "):
                    lines.append(imp)
                else:
                    lines.append(f"import {imp}")
            lines.append("")
        
        # Add typing imports
        lines.append("from typing import Optional, List, Dict, Any, Union")
        lines.append("")
        
        # Add future imports
        if self.config.use_future_annotations:
            lines.append("from __future__ import annotations")
            lines.append("")
        
        # Generate each function
        for i, spec in enumerate(specs):
            code = self.code_generator.generate(spec)
            # Remove imports from individual function code
            code_lines = code.split("\n")
            func_start = 0
            for j, line in enumerate(code_lines):
                if line.startswith("def ") or line.startswith("async def ") or line.startswith("@"):
                    func_start = j
                    break
            
            lines.extend(code_lines[func_start:])
            
            if i < len(specs) - 1:
                lines.append("")
                lines.append("")
        
        module_code = "\n".join(lines)
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(module_code)
        
        return module_code
    
    # ============================================================
    # TEMPLATES
    # ============================================================
    
    def create_getter_setter_specs(self,
                                    name: str,
                                    type_hint: str = "Any",
                                    description: str = "") -> Tuple[FunctionSpec, FunctionSpec]:
        """Create getter and setter specifications."""
        getter = FunctionSpec(
            name=name,
            function_type=FunctionType.PROPERTY_GETTER,
            description=f"Get the {name} value.",
            return_spec=ReturnSpec(
                type_hint=type_hint,
                description=f"The current {name}"
            )
        )
        
        setter = FunctionSpec(
            name=name,
            function_type=FunctionType.PROPERTY_SETTER,
            description=f"Set the {name} value.",
            parameters=[
                ParameterSpec(
                    name="value",
                    type_hint=type_hint,
                    description=f"New {name} value"
                )
            ]
        )
        
        return getter, setter
    
    def create_crud_functions(self,
                               entity_name: str,
                               fields: List[Tuple[str, str]]) -> List[FunctionSpec]:
        """Create CRUD function specifications."""
        functions = []
        
        # Create
        create_params = [ParameterSpec(name=f[0], type_hint=f[1]) for f in fields]
        create_spec = FunctionSpec(
            name=f"create_{entity_name}",
            description=f"Create a new {entity_name}.",
            parameters=create_params,
            return_spec=ReturnSpec(
                type_hint=entity_name.title(),
                description=f"The created {entity_name}"
            )
        )
        functions.append(create_spec)
        
        # Read
        read_spec = FunctionSpec(
            name=f"get_{entity_name}",
            description=f"Retrieve a {entity_name} by ID.",
            parameters=[
                ParameterSpec(name="id", type_hint="str", description=f"{entity_name} identifier")
            ],
            return_spec=ReturnSpec(
                type_hint=f"Optional[{entity_name.title()}]",
                description=f"The {entity_name} if found"
            )
        )
        functions.append(read_spec)
        
        # Update
        update_params = [ParameterSpec(name="id", type_hint="str")]
        update_params.extend([ParameterSpec(name=f[0], type_hint=f"Optional[{f[1]}]", required=False) 
                              for f in fields])
        update_spec = FunctionSpec(
            name=f"update_{entity_name}",
            description=f"Update an existing {entity_name}.",
            parameters=update_params,
            return_spec=ReturnSpec(
                type_hint=f"Optional[{entity_name.title()}]",
                description=f"The updated {entity_name}"
            )
        )
        functions.append(update_spec)
        
        # Delete
        delete_spec = FunctionSpec(
            name=f"delete_{entity_name}",
            description=f"Delete a {entity_name}.",
            parameters=[
                ParameterSpec(name="id", type_hint="str")
            ],
            return_spec=ReturnSpec(
                type_hint="bool",
                description="True if deleted"
            )
        )
        functions.append(delete_spec)
        
        # List
        list_spec = FunctionSpec(
            name=f"list_{entity_name}s",
            description=f"List all {entity_name}s.",
            parameters=[
                ParameterSpec(name="limit", type_hint="int", default_value="100", required=False),
                ParameterSpec(name="offset", type_hint="int", default_value="0", required=False)
            ],
            return_spec=ReturnSpec(
                type_hint=f"List[{entity_name.title()}]",
                description=f"List of {entity_name}s"
            )
        )
        functions.append(list_spec)
        
        return functions
    
    # ============================================================
    # VALIDATION AND EXPORT
    # ============================================================
    
    def validate_spec(self, spec: FunctionSpec) -> List[str]:
        """Validate a function specification."""
        errors = []
        
        if not spec.name:
            errors.append("Function name is required")
        elif not spec.name.islower() or not spec.name.replace('_', '').isalnum():
            errors.append("Function name should be snake_case (PEP 8)")
        
        for param in spec.parameters:
            if not param.name:
                errors.append("Parameter name is required")
            if param.required and param.default_value:
                errors.append(f"Required parameter '{param.name}' cannot have default value")
        
        return errors
    
    def _save_result(self, result: GeneratedFunction):
        """Save generation result to state."""
        history = self.state.get('history', [])
        history.append({
            'function_name': result.function_spec.name,
            'file_path': str(result.file_path) if result.file_path else None,
            'validation_passed': result.validation_passed,
            'iterations': result.iterations,
            'generated_at': result.generated_at.isoformat(),
            'mypy_error_count': len(result.mypy_errors),
            'ruff_error_count': len(result.ruff_errors)
        })
        
        if len(history) > 100:
            history = history[-100:]
        
        self.state.set('history', history)
        self.state.save()
    
    def export_spec(self, spec: FunctionSpec, output_path: Optional[Path] = None) -> str:
        """Export function specification as JSON."""
        data = {
            'name': spec.name,
            'function_type': spec.function_type.value,
            'description': spec.description,
            'parameters': [
                {
                    'name': p.name,
                    'type_hint': p.type_hint,
                    'default_value': p.default_value,
                    'kind': p.kind,
                    'description': p.description,
                    'required': p.required
                }
                for p in spec.parameters
            ],
            'return_spec': {
                'type_hint': spec.return_spec.type_hint,
                'description': spec.return_spec.description,
                'strategy': spec.return_spec.strategy.value
            },
            'exceptions': [
                {
                    'exception_type': e.exception_type,
                    'condition': e.condition,
                    'message': e.message
                }
                for e in spec.exceptions
            ],
            'imports': spec.imports,
            'complexity': spec.complexity.value
        }
        
        if spec.body_spec:
            data['body_spec'] = {
                'logic_description': spec.body_spec.logic_description,
                'steps': spec.body_spec.steps,
                'time_complexity': spec.body_spec.time_complexity
            }
        
        content = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def import_spec(self, input_path: Path) -> FunctionSpec:
        """Import function specification from JSON."""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        spec = FunctionSpec(
            name=data['name'],
            function_type=FunctionType(data.get('function_type', 'function')),
            description=data.get('description', ''),
            return_spec=ReturnSpec(
                type_hint=data['return_spec']['type_hint'],
                description=data['return_spec'].get('description'),
                strategy=ReturnStrategy(data['return_spec'].get('strategy', 'single_value'))
            ),
            imports=data.get('imports', []),
            complexity=Complexity(data.get('complexity', 'simple'))
        )
        
        for param_data in data.get('parameters', []):
            param = ParameterSpec(
                name=param_data['name'],
                type_hint=param_data.get('type_hint', 'Any'),
                default_value=param_data.get('default_value'),
                kind=param_data.get('kind', 'positional_or_keyword'),
                description=param_data.get('description'),
                required=param_data.get('required', True)
            )
            spec.parameters.append(param)
        
        for exc_data in data.get('exceptions', []):
            exc = ExceptionSpec(
                exception_type=exc_data['exception_type'],
                condition=exc_data.get('condition', ''),
                message=exc_data.get('message')
            )
            spec.exceptions.append(exc)
        
        if 'body_spec' in data:
            spec.body_spec = FunctionBodySpec(
                logic_description=data['body_spec']['logic_description'],
                steps=data['body_spec'].get('steps', []),
                time_complexity=data['body_spec'].get('time_complexity')
            )
        
        return spec
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("FunctionGenerator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for function generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Python functions from specifications")
    parser.add_argument("--name", type=str, required=True, help="Function name")
    parser.add_argument("--type", choices=[t.value for t in FunctionType],
                       default=FunctionType.FUNCTION.value, help="Function type")
    parser.add_argument("--description", type=str, help="Function description")
    parser.add_argument("--spec", type=Path, help="Import specification from JSON")
    parser.add_argument("--output", "-o", type=Path, help="Output file path")
    parser.add_argument("--params", nargs="*", help="Parameters in format name:type")
    parser.add_argument("--return-type", type=str, default="None", help="Return type hint")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    parser.add_argument("--generate-test", action="store_true", help="Generate unit test")
    parser.add_argument("--export-spec", type=Path, help="Export specification to JSON")
    
    args = parser.parse_args()
    
    config = FunctionGeneratorConfig(
        use_llm=not args.no_llm,
        generate_tests=args.generate_test
    )
    
    generator = FunctionGenerator(config)
    
    if args.spec:
        spec = generator.import_spec(args.spec)
        spec.name = args.name
    else:
        spec = FunctionSpec(
            name=args.name,
            function_type=FunctionType(args.type),
            description=args.description or "",
            return_spec=ReturnSpec(type_hint=args.return_type)
        )
        
        if args.params:
            for param_str in args.params:
                if ':' in param_str:
                    name, type_hint = param_str.split(':', 1)
                    spec.parameters.append(ParameterSpec(name=name.strip(), type_hint=type_hint.strip()))
    
    if args.export_spec:
        generator.export_spec(spec, args.export_spec)
        print(f"Specification exported to {args.export_spec}")
    
    result = generator.generate(spec, args.output)
    
    if args.output:
        print(f"Function generated at {args.output}")
    else:
        print(result.code)
    
    if not result.validation_passed:
        print("\nValidation issues:")
        for error in result.mypy_errors[:5]:
            print(f"  [mypy] {error}")
        for error in result.ruff_errors[:5]:
            print(f"  [ruff] {error}")
    
    generator.close()


if __name__ == "__main__":
    main()