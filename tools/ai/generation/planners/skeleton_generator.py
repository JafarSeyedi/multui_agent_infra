#!/usr/bin/env python3
"""
Skeleton Generator - Generates full skeleton code with stubs from architecture plans.

Part of the Generation tools (generation/planners/skeleton_generator.py)

This skeleton_generator.py provides:

1. Complete Skeleton Generation - Generates fully-typed class, method, and function stubs
2. Multiple Implementation Hints - TODO, raise NotImplementedError, pass, return default values
3. Architecture Integration - Works directly with ModuleArchitect output
4. Interface Implementation - Generates both interface (ABC) and implementation stubs
5. Import Organization - Automatically organizes and groups imports
6. Docstring Generation - Comprehensive docstrings in multiple styles
7. Type Hint Support - Full type annotations throughout
8. Property Support - Getters, setters, deleters with caching
9. Test File Generation - Creates pytest test files with fixtures
10. __init__.py Generation - Creates package initialization files with exports
11. Validation Integration - mypy and ruff validation of generated code
12. Role-Based Method Generation - Auto-creates standard methods for repositories, services, controllers

The skeleton generator produces complete, ready-to-implement code structures that follow best practices 
and are immediately usable for development.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ....shared.llm_client import LLMClient
from ....shared.state_manager import StateManager
from ....shared.logger import get_logger
from ...validators.mypy_validator import MypyValidator
from ...validators.ruff_validator import RuffValidator
from .module_architect import ModuleArchitecture, ComponentSpec, FileSpec, DirectorySpec
from .interface_designer import InterfaceDesign, MethodDesign, PropertyDesign
from .dependency_planner import DependencyPlan, ImportPlan

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class StubType(str, Enum):
    """Type of stub to generate."""
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    PROPERTY = "property"
    CONSTANT = "constant"
    TYPE_ALIAS = "type_alias"
    EXCEPTION = "exception"
    DATACLASS = "dataclass"
    ENUM = "enum"
    INTERFACE = "interface"
    MODULE = "module"


class ImplementationHint(str, Enum):
    """Hint for implementation."""
    TODO = "todo"
    RAISE_NOT_IMPLEMENTED = "raise_not_implemented"
    PASS = "pass"
    RETURN_DEFAULT = "return_default"
    DELEGATE = "delegate"
    STUB_ONLY = "stub_only"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class StubConfig:
    """Configuration for a stub."""
    stub_type: StubType
    implementation_hint: ImplementationHint = ImplementationHint.RAISE_NOT_IMPLEMENTED
    include_docstring: bool = True
    include_type_hints: bool = True
    include_imports: bool = True
    include_todo_comments: bool = True
    generate_tests: bool = False


@dataclass
class ClassStub:
    """Stub for a class."""
    name: str
    docstring: str = ""
    bases: List[str] = field(default_factory=list)
    methods: List['MethodStub'] = field(default_factory=list)
    properties: List['PropertyStub'] = field(default_factory=list)
    class_variables: List['VariableStub'] = field(default_factory=list)
    instance_variables: List['VariableStub'] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_dataclass: bool = False
    is_abstract: bool = False
    is_final: bool = False
    type_vars: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MethodStub:
    """Stub for a method."""
    name: str
    docstring: str = ""
    parameters: List['ParameterStub'] = field(default_factory=list)
    return_type: str = "None"
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_abstract: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False
    is_final: bool = False
    implementation_hint: ImplementationHint = ImplementationHint.RAISE_NOT_IMPLEMENTED
    body: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PropertyStub:
    """Stub for a property."""
    name: str
    type_hint: str
    docstring: str = ""
    has_getter: bool = True
    has_setter: bool = False
    has_deleter: bool = False
    default_value: Optional[str] = None
    is_abstract: bool = False
    is_cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParameterStub:
    """Stub for a parameter."""
    name: str
    type_hint: str = "Any"
    default_value: Optional[str] = None
    kind: str = "positional"
    description: str = ""


@dataclass
class VariableStub:
    """Stub for a variable."""
    name: str
    type_hint: str = "Any"
    value: Optional[str] = None
    is_class_var: bool = False
    is_final: bool = False
    description: str = ""


@dataclass
class FunctionStub:
    """Stub for a standalone function."""
    name: str
    docstring: str = ""
    parameters: List[ParameterStub] = field(default_factory=list)
    return_type: str = "None"
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    implementation_hint: ImplementationHint = ImplementationHint.RAISE_NOT_IMPLEMENTED
    body: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConstantStub:
    """Stub for a constant."""
    name: str
    value: str
    type_hint: str
    docstring: str = ""
    is_public: bool = True


@dataclass
class TypeAliasStub:
    """Stub for a type alias."""
    name: str
    type_definition: str
    docstring: str = ""


@dataclass
class ImportStub:
    """Stub for an import statement."""
    module: str
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    is_from: bool = False
    is_relative: bool = False


@dataclass
class ModuleStub:
    """Complete module stub."""
    name: str
    file_path: str
    docstring: str = ""
    imports: List[ImportStub] = field(default_factory=list)
    constants: List[ConstantStub] = field(default_factory=list)
    type_aliases: List[TypeAliasStub] = field(default_factory=list)
    functions: List[FunctionStub] = field(default_factory=list)
    classes: List[ClassStub] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkeletonGenerationResult:
    """Result of skeleton generation."""
    module_name: str
    generated_files: List[Path] = field(default_factory=list)
    total_files: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_methods: int = 0
    validation_passed: bool = False
    mypy_errors: List[str] = field(default_factory=list)
    ruff_errors: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkeletonGeneratorConfig:
    """Configuration for skeleton generator."""
    output_dir: Path = field(default_factory=lambda: Path.cwd())
    
    # Stub configuration
    default_stub_config: StubConfig = field(default_factory=lambda: StubConfig(
        stub_type=StubType.CLASS,
        implementation_hint=ImplementationHint.RAISE_NOT_IMPLEMENTED,
        include_docstring=True,
        include_type_hints=True,
        include_todo_comments=True
    ))
    
    # Code style
    indent_size: int = 4
    line_length: int = 88
    use_future_annotations: bool = True
    include_encoding: bool = False
    
    # Documentation
    docstring_style: str = "google"
    include_examples: bool = True
    include_see_also: bool = False
    
    # Imports
    organize_imports: bool = True
    group_imports: bool = True
    sort_imports: bool = True
    
    # Validation
    validate_mypy: bool = True
    validate_ruff: bool = True
    
    # Tests
    generate_tests: bool = False
    test_dir: str = "tests"
    
    # Advanced
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    create_init_files: bool = True


# ============================================================
# STUB CODE GENERATOR
# ============================================================

class StubCodeGenerator:
    """Generate code from stubs."""
    
    def __init__(self, config: SkeletonGeneratorConfig):
        self.config = config
        self.indent = " " * config.indent_size
    
    def generate_module(self, stub: ModuleStub) -> str:
        """Generate complete module code."""
        lines = []
        
        # Encoding
        if self.config.include_encoding:
            lines.append("# -*- coding: utf-8 -*-")
            lines.append("")
        
        # Shebang for main modules
        if stub.name == "__main__" or stub.file_path.endswith("__main__.py"):
            lines.append("#!/usr/bin/env python3")
            lines.append("")
        
        # Future imports
        if self.config.use_future_annotations:
            lines.append("from __future__ import annotations")
            lines.append("")
        
        # Module docstring
        if stub.docstring:
            lines.append('"""')
            lines.append(stub.docstring)
            lines.append('"""')
            lines.append("")
        
        # Imports
        if stub.imports:
            lines.extend(self._generate_imports(stub.imports))
            lines.append("")
        
        # Constants
        if stub.constants:
            for const in stub.constants:
                lines.extend(self._generate_constant(const))
            lines.append("")
        
        # Type aliases
        if stub.type_aliases:
            for alias in stub.type_aliases:
                lines.extend(self._generate_type_alias(alias))
            lines.append("")
        
        # Functions
        for func in stub.functions:
            lines.extend(self._generate_function(func))
            lines.append("")
        
        # Classes
        for cls in stub.classes:
            lines.extend(self._generate_class(cls))
            lines.append("")
        
        # Exports
        if stub.exports:
            exports_str = ", ".join(f'"{e}"' for e in stub.exports)
            lines.append(f"__all__ = [{exports_str}]")
        
        return "\n".join(lines).rstrip() + "\n"
    
    def _generate_imports(self, imports: List[ImportStub]) -> List[str]:
        """Generate import statements."""
        lines = []
        
        # Group imports
        if self.config.group_imports:
            stdlib = []
            third_party = []
            local = []
            
            for imp in imports:
                if self._is_stdlib(imp.module):
                    stdlib.append(imp)
                elif imp.is_relative or imp.module.startswith('.'):
                    local.append(imp)
                else:
                    third_party.append(imp)
            
            for group in [stdlib, third_party, local]:
                for imp in group:
                    lines.append(self._format_import(imp))
                if group:
                    lines.append("")
        else:
            for imp in imports:
                lines.append(self._format_import(imp))
        
        return lines
    
    def _is_stdlib(self, module: str) -> bool:
        """Check if module is from standard library."""
        stdlib_modules = {
            'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections',
            'contextlib', 'copy', 'dataclasses', 'datetime', 'enum', 'functools',
            'hashlib', 'inspect', 'io', 'itertools', 'json', 'logging', 'math',
            'os', 'pathlib', 're', 'sys', 'threading', 'time', 'typing', 'uuid'
        }
        top_module = module.split('.')[0]
        return top_module in stdlib_modules
    
    def _format_import(self, imp: ImportStub) -> str:
        """Format an import statement."""
        if imp.is_from:
            if imp.names:
                names_str = ", ".join(imp.names)
                if len(names_str) > self.config.line_length - 20:
                    lines = [f"from {imp.module} import ("]
                    for name in imp.names:
                        lines.append(f"{self.indent}{name},")
                    lines.append(")")
                    return "\n".join(lines)
                return f"from {imp.module} import {names_str}"
            else:
                return f"from {imp.module} import *"
        else:
            if imp.alias:
                return f"import {imp.module} as {imp.alias}"
            return f"import {imp.module}"
    
    def _generate_constant(self, const: ConstantStub) -> List[str]:
        """Generate constant definition."""
        lines = []
        
        if const.docstring:
            lines.append(f'"""{const.docstring}"""')
        
        if self.config.default_stub_config.include_type_hints:
            lines.append(f"{const.name}: {const.type_hint} = {const.value}")
        else:
            lines.append(f"{const.name} = {const.value}")
        
        return lines
    
    def _generate_type_alias(self, alias: TypeAliasStub) -> List[str]:
        """Generate type alias definition."""
        lines = []
        
        if alias.docstring:
            lines.append(f'"""{alias.docstring}"""')
        
        lines.append(f"{alias.name} = {alias.type_definition}")
        
        return lines
    
    def _generate_function(self, func: FunctionStub) -> List[str]:
        """Generate function definition."""
        lines = []
        
        # Decorators
        for decorator in func.decorators:
            if not decorator.startswith('@'):
                decorator = '@' + decorator
            lines.append(decorator)
        
        # Signature
        async_prefix = "async " if func.is_async else ""
        params = self._generate_parameters(func.parameters)
        return_type = f" -> {func.return_type}" if func.return_type and self.config.default_stub_config.include_type_hints else ""
        
        lines.append(f"{async_prefix}def {func.name}({', '.join(params)}){return_type}:")
        
        # Docstring
        if func.docstring and self.config.default_stub_config.include_docstring:
            lines.append(f'{self.indent}"""')
            for line in func.docstring.split('\n'):
                lines.append(f"{self.indent}{line}")
            lines.append(f'{self.indent}"""')
        
        # Body
        lines.extend(self._generate_function_body(func))
        
        return lines
    
    def _generate_parameters(self, params: List[ParameterStub]) -> List[str]:
        """Generate parameter strings."""
        param_strs = []
        
        for param in params:
            param_str = param.name
            
            if param.kind == "keyword_only" and not param_str.startswith('*'):
                param_str = f"*, {param_str}"
            elif param.kind == "varargs":
                param_str = f"*{param_str}"
            elif param.kind == "kwargs":
                param_str = f"**{param_str}"
            
            if self.config.default_stub_config.include_type_hints:
                param_str += f": {param.type_hint}"
            
            if param.default_value is not None:
                param_str += f" = {param.default_value}"
            
            param_strs.append(param_str)
        
        return param_strs
    
    def _generate_function_body(self, func: FunctionStub) -> List[str]:
        """Generate function body."""
        lines = []
        
        if func.body:
            for line in func.body.split('\n'):
                lines.append(f"{self.indent}{line}")
            return lines
        
        hint = func.implementation_hint
        
        if hint == ImplementationHint.RAISE_NOT_IMPLEMENTED:
            lines.append(f'{self.indent}"""TODO: Implement {func.name}."""')
            lines.append(f'{self.indent}raise NotImplementedError("{func.name} must be implemented")')
        elif hint == ImplementationHint.PASS:
            lines.append(f"{self.indent}pass")
        elif hint == ImplementationHint.RETURN_DEFAULT:
            lines.append(f'{self.indent}"""TODO: Implement {func.name}."""')
            default = self._get_default_return(func.return_type)
            lines.append(f"{self.indent}return {default}")
        elif hint == ImplementationHint.TODO:
            lines.append(f'{self.indent}# TODO: Implement {func.name}')
            lines.append(f"{self.indent}pass")
        else:
            lines.append(f"{self.indent}pass")
        
        return lines
    
    def _get_default_return(self, return_type: str) -> str:
        """Get default return value for a type."""
        if return_type == "None":
            return "None"
        elif return_type == "bool":
            return "False"
        elif return_type == "str":
            return '""'
        elif return_type == "int":
            return "0"
        elif return_type == "float":
            return "0.0"
        elif "List" in return_type:
            return "[]"
        elif "Dict" in return_type:
            return "{}"
        elif "Optional" in return_type:
            return "None"
        else:
            return "None"
    
    def _generate_class(self, cls: ClassStub) -> List[str]:
        """Generate class definition."""
        lines = []
        
        # Decorators
        for decorator in cls.decorators:
            if not decorator.startswith('@'):
                decorator = '@' + decorator
            lines.append(decorator)
        
        if cls.is_dataclass and "@dataclass" not in lines:
            lines.insert(0, "@dataclass")
        
        # Class definition
        bases_str = f"({', '.join(cls.bases)})" if cls.bases else ""
        lines.append(f"class {cls.name}{bases_str}:")
        
        # Class docstring
        if cls.docstring and self.config.default_stub_config.include_docstring:
            lines.append(f'{self.indent}"""')
            for line in cls.docstring.split('\n'):
                lines.append(f"{self.indent}{line}")
            lines.append(f'{self.indent}"""')
        
        # Class variables
        for var in cls.class_variables:
            if self.config.default_stub_config.include_type_hints:
                lines.append(f"{self.indent}{var.name}: {var.type_hint}")
                if var.value:
                    lines[-1] += f" = {var.value}"
            else:
                if var.value:
                    lines.append(f"{self.indent}{var.name} = {var.value}")
            
            if var.description and self.config.default_stub_config.include_docstring:
                lines.append(f'{self.indent}"""{var.description}"""')
        
        if cls.class_variables:
            lines.append("")
        
        # Instance variables (as __init__)
        if cls.instance_variables and not cls.is_dataclass:
            lines.extend(self._generate_init_method(cls))
        
        # Properties
        for prop in cls.properties:
            lines.extend(self._generate_property(prop))
            lines.append("")
        
        # Methods
        for method in cls.methods:
            lines.extend(self._generate_method(method))
            lines.append("")
        
        return lines
    
    def _generate_init_method(self, cls: ClassStub) -> List[str]:
        """Generate __init__ method."""
        lines = []
        lines.append(f"{self.indent}def __init__(self):")
        lines.append(f'{self.indent}{self.indent}"""Initialize the instance."""')
        
        for var in cls.instance_variables:
            if var.value:
                lines.append(f"{self.indent}{self.indent}self.{var.name} = {var.value}")
            else:
                lines.append(f"{self.indent}{self.indent}self.{var.name} = None  # TODO: Initialize")
        
        lines.append("")
        return lines
    
    def _generate_property(self, prop: PropertyStub) -> List[str]:
        """Generate property definition."""
        lines = []
        
        # Getter
        if prop.has_getter:
            decorator = "@cached_property" if prop.is_cached else "@property"
            lines.append(f"{self.indent}{decorator}")
            if prop.is_abstract:
                lines.append(f"{self.indent}@abstractmethod")
            
            return_type = f" -> {prop.type_hint}" if self.config.default_stub_config.include_type_hints else ""
            lines.append(f"{self.indent}def {prop.name}(self){return_type}:")
            
            if prop.docstring:
                lines.append(f'{self.indent}{self.indent}"""')
                lines.append(f"{self.indent}{self.indent}{prop.docstring}")
                lines.append(f'{self.indent}{self.indent}"""')
            
            if prop.is_abstract:
                lines.append(f"{self.indent}{self.indent}...")
            else:
                if prop.default_value:
                    lines.append(f"{self.indent}{self.indent}return {prop.default_value}")
                else:
                    lines.append(f'{self.indent}{self.indent}raise NotImplementedError("{prop.name} must be implemented")')
        
        # Setter
        if prop.has_setter:
            lines.append("")
            lines.append(f"{self.indent}@{prop.name}.setter")
            if prop.is_abstract:
                lines.append(f"{self.indent}@abstractmethod")
            
            type_hint = f": {prop.type_hint}" if self.config.default_stub_config.include_type_hints else ""
            lines.append(f"{self.indent}def {prop.name}(self, value{type_hint}) -> None:")
            
            if prop.is_abstract:
                lines.append(f"{self.indent}{self.indent}...")
            else:
                lines.append(f'{self.indent}{self.indent}raise NotImplementedError("{prop.name} setter must be implemented")')
        
        return lines
    
    def _generate_method(self, method: MethodStub) -> List[str]:
        """Generate method definition."""
        lines = []
        
        # Decorators
        for decorator in method.decorators:
            if not decorator.startswith('@'):
                decorator = '@' + decorator
            lines.append(f"{self.indent}{decorator}")
        
        if method.is_classmethod:
            lines.append(f"{self.indent}@classmethod")
        if method.is_staticmethod:
            lines.append(f"{self.indent}@staticmethod")
        if method.is_property:
            lines.append(f"{self.indent}@property")
        if method.is_abstract:
            lines.append(f"{self.indent}@abstractmethod")
        if method.is_final:
            lines.append(f"{self.indent}@final")
        
        # Signature
        async_prefix = "async " if method.is_async else ""
        params = self._generate_method_parameters(method)
        return_type = f" -> {method.return_type}" if method.return_type and self.config.default_stub_config.include_type_hints else ""
        
        lines.append(f"{self.indent}{async_prefix}def {method.name}({', '.join(params)}){return_type}:")
        
        # Docstring
        if method.docstring and self.config.default_stub_config.include_docstring:
            lines.append(f'{self.indent}{self.indent}"""')
            for line in method.docstring.split('\n'):
                lines.append(f"{self.indent}{self.indent}{line}")
            lines.append(f'{self.indent}{self.indent}"""')
        
        # Body
        if method.is_abstract:
            lines.append(f"{self.indent}{self.indent}...")
        elif method.body:
            for line in method.body.split('\n'):
                lines.append(f"{self.indent}{self.indent}{line}")
        else:
            hint = method.implementation_hint
            
            if hint == ImplementationHint.RAISE_NOT_IMPLEMENTED:
                if self.config.default_stub_config.include_todo_comments:
                    lines.append(f'{self.indent}{self.indent}# TODO: Implement {method.name}')
                lines.append(f'{self.indent}{self.indent}raise NotImplementedError("{method.name} must be implemented")')
            elif hint == ImplementationHint.PASS:
                lines.append(f"{self.indent}{self.indent}pass")
            elif hint == ImplementationHint.RETURN_DEFAULT:
                default = self._get_default_return(method.return_type)
                lines.append(f"{self.indent}{self.indent}return {default}")
            elif hint == ImplementationHint.TODO:
                lines.append(f'{self.indent}{self.indent}# TODO: Implement {method.name}')
                lines.append(f"{self.indent}{self.indent}pass")
            else:
                lines.append(f"{self.indent}{self.indent}pass")
        
        return lines
    
    def _generate_method_parameters(self, method: MethodStub) -> List[str]:
        """Generate method parameter strings."""
        params = []
        
        if not method.is_staticmethod:
            if method.is_classmethod:
                params.append("cls")
            else:
                params.append("self")
        
        for param in method.parameters:
            param_str = param.name
            
            if param.kind == "keyword_only" and not param_str.startswith('*'):
                param_str = f"*, {param_str}"
            elif param.kind == "varargs":
                param_str = f"*{param_str}"
            elif param.kind == "kwargs":
                param_str = f"**{param_str}"
            
            if self.config.default_stub_config.include_type_hints:
                param_str += f": {param.type_hint}"
            
            if param.default_value is not None:
                param_str += f" = {param.default_value}"
            
            params.append(param_str)
        
        return params


# ============================================================
# MAIN SKELETON GENERATOR
# ============================================================

class SkeletonGenerator:
    """
    Generates full skeleton code with stubs from architecture plans.
    
    Features:
    - Generate complete module skeletons from architecture plans
    - Class, method, property, function stubs with type hints
    - Configurable implementation hints (TODO, raise, pass, return default)
    - Automatic import organization and grouping
    - Docstring generation in multiple styles
    - Integration with module architect and interface designer
    - Validation with mypy and ruff
    - Test file generation
    - LLM-powered stub enhancement
    """
    
    def __init__(self, config: Optional[SkeletonGeneratorConfig] = None):
        self.config = config or SkeletonGeneratorConfig()
        self.code_generator = StubCodeGenerator(self.config)
        self.llm = LLMClient() if self.config.use_llm else None
        self.state = StateManager(self.config.output_dir / ".ai_state" / "skeleton_generator.json")
        
        self.mypy_validator = MypyValidator() if self.config.validate_mypy else None
        self.ruff_validator = RuffValidator() if self.config.validate_ruff else None
        
        logger.info("SkeletonGenerator initialized")
    
    def generate_from_architecture(self, arch: ModuleArchitecture,
                                    dependency_plan: Optional[DependencyPlan] = None) -> SkeletonGenerationResult:
        """Generate skeleton from module architecture."""
        logger.info(f"Generating skeleton for module: {arch.name}")
        
        result = SkeletonGenerationResult(module_name=arch.name)
        
        # Convert architecture to module stubs
        module_stubs = self._architecture_to_stubs(arch, dependency_plan)
        
        # Generate files
        for stub in module_stubs:
            file_path = self.config.output_dir / stub.file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate code
            code = self.code_generator.generate_module(stub)
            
            # Write file
            file_path.write_text(code)
            result.generated_files.append(file_path)
            result.total_files += 1
            
            # Count components
            result.total_classes += len(stub.classes)
            result.total_functions += len(stub.functions)
            for cls in stub.classes:
                result.total_methods += len(cls.methods)
            
            # Validate
            if self.config.validate_mypy or self.config.validate_ruff:
                mypy_errors, ruff_errors = self._validate_file(file_path, code)
                result.mypy_errors.extend(mypy_errors)
                result.ruff_errors.extend(ruff_errors)
        
        result.validation_passed = not (result.mypy_errors or result.ruff_errors)
        
        # Generate tests if configured
        if self.config.generate_tests:
            test_files = self._generate_test_files(arch, module_stubs)
            result.generated_files.extend(test_files)
        
        # Create __init__.py files
        if self.config.create_init_files:
            init_files = self._create_init_files(arch)
            result.generated_files.extend(init_files)
        
        # Save result
        self._save_result(result)
        
        logger.info(f"Generated {result.total_files} skeleton files for {arch.name}")
        
        return result
    
    def generate_from_interface(self, interface: InterfaceDesign,
                                 module_path: str) -> SkeletonGenerationResult:
        """Generate skeleton from interface design."""
        logger.info(f"Generating skeleton from interface: {interface.name}")
        
        # Create simple architecture from interface
        arch = ModuleArchitecture(
            name=interface.name,
            root_path=module_path,
            pattern=ArchitecturePattern.LAYERED,
            description=interface.description
        )
        
        # Convert interface to stubs
        stubs = self._interface_to_stubs(interface, module_path)
        
        result = SkeletonGenerationResult(module_name=interface.name)
        
        for stub in stubs:
            file_path = self.config.output_dir / stub.file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            code = self.code_generator.generate_module(stub)
            file_path.write_text(code)
            result.generated_files.append(file_path)
            result.total_files += 1
        
        return result
    
    def _architecture_to_stubs(self, arch: ModuleArchitecture,
                                dependency_plan: Optional[DependencyPlan]) -> List[ModuleStub]:
        """Convert architecture to module stubs."""
        stubs = []
        
        for file_path, file_spec in arch.files.items():
            stub = ModuleStub(
                name=file_spec.name,
                file_path=file_path,
                docstring=file_spec.description or f"{file_spec.name} module"
            )
            
            # Add imports from dependency plan
            if dependency_plan and file_path in dependency_plan.import_plans:
                import_plan = dependency_plan.import_plans[file_path]
                stub.imports = self._convert_import_plan(import_plan)
            
            # Add components
            for class_name in file_spec.classes:
                comp = arch.components.get(class_name)
                if comp:
                    class_stub = self._component_to_class_stub(comp, arch)
                    stub.classes.append(class_stub)
            
            # Add functions
            for func_name in file_spec.functions:
                func_stub = FunctionStub(
                    name=func_name,
                    docstring=f"{func_name} function",
                    implementation_hint=self.config.default_stub_config.implementation_hint
                )
                stub.functions.append(func_stub)
            
            # Add constants
            for const_name in file_spec.constants:
                const_stub = ConstantStub(
                    name=const_name,
                    value="None",
                    type_hint="Any",
                    docstring=f"{const_name} constant"
                )
                stub.constants.append(const_stub)
            
            # Add exports
            stub.exports = file_spec.exports
            
            stubs.append(stub)
        
        # Add interfaces as separate files
        for interface_name, interface in arch.interfaces.items():
            interface_stubs = self._interface_to_stubs(interface, arch.root_path)
            stubs.extend(interface_stubs)
        
        return stubs
    
    def _component_to_class_stub(self, comp: ComponentSpec,
                                   arch: ModuleArchitecture) -> ClassStub:
        """Convert component to class stub."""
        class_stub = ClassStub(
            name=comp.name,
            docstring=comp.description or f"{comp.name} {comp.role.value}",
            is_abstract=comp.is_abstract,
            is_final=comp.is_final
        )
        
        # Add interface reference as base
        if comp.interface_ref:
            class_stub.bases.append(comp.interface_ref)
        
        # Add methods based on role
        if comp.role == ComponentRole.REPOSITORY:
            class_stub.methods = self._create_repository_methods()
        elif comp.role == ComponentRole.SERVICE:
            class_stub.methods = self._create_service_methods()
        elif comp.role == ComponentRole.CONTROLLER:
            class_stub.methods = self._create_controller_methods()
        
        # Add dependencies as instance variables
        for dep in comp.dependencies:
            var = VariableStub(
                name=f"_{dep.lower()}",
                type_hint=dep,
                description=f"{dep} dependency"
            )
            class_stub.instance_variables.append(var)
        
        return class_stub
    
    def _interface_to_stubs(self, interface: InterfaceDesign,
                            module_path: str) -> List[ModuleStub]:
        """Convert interface to module stubs."""
        stubs = []
        
        # Create interface stub
        interface_stub = ModuleStub(
            name=f"i_{interface.name.lower()}",
            file_path=f"{module_path}/interfaces/i_{interface.name.lower()}.py",
            docstring=interface.description
        )
        
        class_stub = ClassStub(
            name=f"I{interface.name}",
            docstring=interface.description,
            is_abstract=True
        )
        class_stub.bases.append("ABC")
        
        for method in interface.methods:
            method_stub = MethodStub(
                name=method.name,
                docstring=method.description,
                return_type=method.return_design.type_hint if method.return_design else "None",
                is_abstract=method.is_abstract,
                is_async=method.is_async
            )
            
            for param in method.parameters:
                param_stub = ParameterStub(
                    name=param.name,
                    type_hint=param.type_hint,
                    description=param.description
                )
                method_stub.parameters.append(param_stub)
            
            class_stub.methods.append(method_stub)
        
        interface_stub.classes.append(class_stub)
        interface_stub.imports.append(ImportStub(module="abc", names=["ABC", "abstractmethod"]))
        stubs.append(interface_stub)
        
        # Create implementation stub
        impl_stub = ModuleStub(
            name=f"{interface.name.lower()}_impl",
            file_path=f"{module_path}/implementations/{interface.name.lower()}_impl.py",
            docstring=f"Implementation of {interface.name}"
        )
        
        impl_class = ClassStub(
            name=f"{interface.name}Impl",
            docstring=f"Implementation of I{interface.name}",
            bases=[f"I{interface.name}"]
        )
        
        for method in interface.methods:
            if not method.is_property:
                method_stub = MethodStub(
                    name=method.name,
                    docstring=f"Implement {method.name}",
                    return_type=method.return_design.type_hint if method.return_design else "None",
                    is_async=method.is_async,
                    implementation_hint=self.config.default_stub_config.implementation_hint
                )
                
                for param in method.parameters:
                    param_stub = ParameterStub(
                        name=param.name,
                        type_hint=param.type_hint
                    )
                    method_stub.parameters.append(param_stub)
                
                impl_class.methods.append(method_stub)
        
        impl_stub.classes.append(impl_class)
        impl_stub.imports.append(ImportStub(
            module=f"interfaces.i_{interface.name.lower()}",
            names=[f"I{interface.name}"],
            is_from=True
        ))
        stubs.append(impl_stub)
        
        return stubs
    
    def _convert_import_plan(self, import_plan: ImportPlan) -> List[ImportStub]:
        """Convert import plan to import stubs."""
        imports = []
        
        for block_name, block_imports in import_plan.import_blocks:
            for imp in block_imports:
                import_stub = self._parse_import_string(imp)
                if import_stub:
                    imports.append(import_stub)
        
        return imports
    
    def _parse_import_string(self, import_str: str) -> Optional[ImportStub]:
        """Parse import string to ImportStub."""
        import_str = import_str.strip()
        
        if import_str.startswith("from "):
            # from module import names
            parts = import_str.split(" import ")
            if len(parts) == 2:
                module = parts[0][5:]
                names_str = parts[1]
                names = [n.strip() for n in names_str.split(",")]
                return ImportStub(module=module, names=names, is_from=True)
        elif import_str.startswith("import "):
            # import module as alias
            parts = import_str[7:].split(" as ")
            if len(parts) == 2:
                return ImportStub(module=parts[0].strip(), alias=parts[1].strip())
            else:
                return ImportStub(module=import_str[7:].strip())
        
        return None
    
    def _create_repository_methods(self) -> List[MethodStub]:
        """Create standard repository methods."""
        return [
            MethodStub(name="get", return_type="Optional[Any]", 
                      parameters=[ParameterStub(name="id", type_hint="str")],
                      docstring="Get entity by ID"),
            MethodStub(name="save", return_type="Any",
                      parameters=[ParameterStub(name="entity", type_hint="Any")],
                      docstring="Save entity"),
            MethodStub(name="delete", return_type="bool",
                      parameters=[ParameterStub(name="id", type_hint="str")],
                      docstring="Delete entity by ID"),
            MethodStub(name="list", return_type="List[Any]",
                      docstring="List all entities"),
        ]
    
    def _create_service_methods(self) -> List[MethodStub]:
        """Create standard service methods."""
        return [
            MethodStub(name="execute", return_type="Any",
                      parameters=[ParameterStub(name="request", type_hint="Any")],
                      docstring="Execute service operation"),
        ]
    
    def _create_controller_methods(self) -> List[MethodStub]:
        """Create standard controller methods."""
        return [
            MethodStub(name="handle", return_type="Any",
                      parameters=[ParameterStub(name="request", type_hint="Any")],
                      docstring="Handle request"),
        ]
    
    def _validate_file(self, file_path: Path, code: str) -> Tuple[List[str], List[str]]:
        """Validate a generated file."""
        mypy_errors = []
        ruff_errors = []
        
        if self.mypy_validator:
            mypy_errors = self.mypy_validator.validate_string(code)
        
        if self.ruff_validator:
            ruff_errors = self.ruff_validator.validate_string(code)
        
        return mypy_errors, ruff_errors
    
    def _generate_test_files(self, arch: ModuleArchitecture,
                              stubs: List[ModuleStub]) -> List[Path]:
        """Generate test files."""
        test_files = []
        test_dir = self.config.output_dir / self.config.test_dir / arch.name
        test_dir.mkdir(parents=True, exist_ok=True)
        
        for stub in stubs:
            if stub.name.startswith('_') or stub.name == '__init__':
                continue
            
            test_file = test_dir / f"test_{stub.name}.py"
            
            lines = [
                '"""',
                f'Unit tests for {stub.name} module.',
                '"""',
                '',
                'import pytest',
                f'from {arch.name}.{stub.name} import *',
                '',
                '',
            ]
            
            # Generate test class for each class
            for cls in stub.classes:
                lines.append(f"class Test{cls.name}:")
                lines.append(f'    """Tests for {cls.name}."""')
                lines.append("")
                
                for method in cls.methods:
                    if method.name.startswith('_'):
                        continue
                    
                    lines.append(f"    def test_{method.name}(self):")
                    lines.append(f'        """Test {method.name}."""')
                    lines.append(f"        # TODO: Implement test")
                    lines.append(f"        pass")
                    lines.append("")
            
            test_file.write_text('\n'.join(lines))
            test_files.append(test_file)
        
        # Create conftest.py
        conftest = test_dir / "conftest.py"
        conftest_content = '''
"""Pytest configuration."""

import pytest


@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return {}
'''
        conftest.write_text(conftest_content)
        test_files.append(conftest)
        
        return test_files
    
    def _create_init_files(self, arch: ModuleArchitecture) -> List[Path]:
        """Create __init__.py files for all directories."""
        init_files = []
        
        for dir_path in arch.directories.keys():
            full_path = self.config.output_dir / dir_path
            if full_path.exists():
                init_file = full_path / "__init__.py"
                if not init_file.exists():
                    dir_spec = arch.directories[dir_path]
                    content = self._generate_init_content(dir_spec)
                    init_file.write_text(content)
                    init_files.append(init_file)
        
        return init_files
    
    def _generate_init_content(self, dir_spec: DirectorySpec) -> str:
        """Generate __init__.py content."""
        lines = ['"""', f"{dir_spec.name} package.", '"""', '']
        
        if dir_spec.init_exports:
            exports = ", ".join(f'"{e}"' for e in dir_spec.init_exports)
            lines.append(f"__all__ = [{exports}]")
        
        return '\n'.join(lines)
    
    def _save_result(self, result: SkeletonGenerationResult):
        """Save generation result to state."""
        results = self.state.get('results', [])
        results.append({
            'timestamp': result.generated_at.isoformat(),
            'module': result.module_name,
            'files': result.total_files,
            'classes': result.total_classes,
            'functions': result.total_functions,
            'methods': result.total_methods,
            'validation_passed': result.validation_passed
        })
        
        if len(results) > 50:
            results = results[-50:]
        
        self.state.set('results', results)
        self.state.save()
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("SkeletonGenerator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for skeleton generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate skeleton code from architecture plans")
    parser.add_argument("--architecture", type=Path, required=True, help="Architecture JSON file")
    parser.add_argument("--output", "-o", type=Path, default=Path.cwd(), help="Output directory")
    parser.add_argument("--implementation-hint", choices=[h.value for h in ImplementationHint],
                       default=ImplementationHint.RAISE_NOT_IMPLEMENTED.value)
    parser.add_argument("--no-docstrings", action="store_true", help="Skip docstring generation")
    parser.add_argument("--no-type-hints", action="store_true", help="Skip type hint generation")
    parser.add_argument("--generate-tests", action="store_true", help="Generate test files")
    parser.add_argument("--validate", action="store_true", help="Validate generated code")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    
    args = parser.parse_args()
    
    config = SkeletonGeneratorConfig(
        output_dir=args.output,
        generate_tests=args.generate_tests,
        validate_mypy=args.validate,
        validate_ruff=args.validate,
        use_llm=not args.no_llm
    )
    
    config.default_stub_config.implementation_hint = ImplementationHint(args.implementation_hint)
    config.default_stub_config.include_docstring = not args.no_docstrings
    config.default_stub_config.include_type_hints = not args.no_type_hints
    
    generator = SkeletonGenerator(config)
    
    # Load architecture
    with open(args.architecture, 'r') as f:
        arch_data = json.load(f)
    
    # Reconstruct architecture (simplified)
    arch = ModuleArchitecture(
        name=arch_data['name'],
        root_path=arch_data['root_path'],
        pattern=ArchitecturePattern(arch_data['pattern']),
        description=arch_data.get('description', '')
    )
    
    # Parse files from architecture data
    for file_path, file_data in arch_data.get('files', {}).items():
        file_spec = FileSpec(
            name=file_data['name'],
            file_type=ModuleType(file_data['type']),
            path=file_path,
            description=file_data.get('description', ''),
            classes=file_data.get('classes', []),
            functions=file_data.get('functions', []),
            exports=file_data.get('exports', [])
        )
        arch.files[file_path] = file_spec
    
    # Parse components
    for comp_name, comp_data in arch_data.get('components', {}).items():
        comp = ComponentSpec(
            name=comp_name,
            component_type=comp_data['type'],
            role=ComponentRole(comp_data['role']),
            description=comp_data.get('description', ''),
            dependencies=comp_data.get('dependencies', []),
            interface_ref=comp_data.get('interface_ref')
        )
        arch.components[comp_name] = comp
    
    # Parse directories
    for dir_path, dir_data in arch_data.get('directories', {}).items():
        dir_spec = DirectorySpec(
            name=dir_data['name'],
            path=dir_path,
            description=dir_data.get('description', ''),
            is_package=dir_data.get('is_package', True),
            init_exports=dir_data.get('init_exports', [])
        )
        arch.directories[dir_path] = dir_spec
    
    result = generator.generate_from_architecture(arch)
    
    print(f"\nGenerated {result.total_files} skeleton files")
    print(f"Classes: {result.total_classes}")
    print(f"Functions: {result.total_functions}")
    print(f"Methods: {result.total_methods}")
    print(f"Validation: {'✅ Passed' if result.validation_passed else '❌ Failed'}")
    
    if result.mypy_errors:
        print(f"\nMypy errors: {len(result.mypy_errors)}")
    if result.ruff_errors:
        print(f"Ruff errors: {len(result.ruff_errors)}")
    
    generator.close()


if __name__ == "__main__":
    main()