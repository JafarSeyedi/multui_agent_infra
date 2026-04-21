#!/usr/bin/env python3
"""
Contract Generator - Generates interface contracts, ABCs, and Protocols.

Part of the Generation tools (generation/planners/contract_generator.py)

This contract_generator.py provides:

1. Multiple Contract Types - ABC, Protocol, TypedDict, Dataclass, Pydantic, Service, Repository, Factory, Strategy, Observer
2. Full Type Hints - Complete type annotations for all methods and properties
3. Comprehensive Docstrings - Google, NumPy, or Sphinx style documentation
4. Design by Contract - Preconditions, postconditions, and invariants
5. Generic Type Support - TypeVar definitions for generic contracts
6. Property Support - Getters, setters, deleters with caching
7. Implementation Stubs - Optional concrete implementation generation
8. LLM-Powered Parsing - Generate from natural language descriptions
9. Quick Templates - Service and repository contract templates
10. Validation Integration - mypy and ruff validation
11. Spec Export/Import - JSON serialization for specifications
12. Deprecation Support - Mark contracts and methods as deprecated

The contract generator creates robust interface definitions that serve as the foundation for reliable, testable code with clear behavioral expectations.

"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ....shared.llm_client import LLMClient
from ....shared.state_manager import StateManager
from ....shared.logger import get_logger
from ...validators.mypy_validator import MypyValidator
from ...validators.ruff_validator import RuffValidator

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class ContractType(str, Enum):
    """Type of contract to generate."""
    ABC = "abc"                    # Abstract Base Class
    PROTOCOL = "protocol"          # Protocol (structural subtyping)
    INTERFACE = "interface"        # Pure interface (all abstract)
    TYPED_DICT = "typed_dict"     # TypedDict for structured data
    DATA_CLASS = "dataclass"       # Dataclass with validation
    PYDANTIC = "pydantic"          # Pydantic model
    SERVICE_CONTRACT = "service_contract"  # Service interface
    REPOSITORY_CONTRACT = "repository_contract"
    FACTORY_CONTRACT = "factory_contract"
    STRATEGY_CONTRACT = "strategy_contract"
    OBSERVER_CONTRACT = "observer_contract"
    CUSTOM = "custom"


class ParameterKind(str, Enum):
    """Kind of parameter."""
    POSITIONAL = "positional"
    POSITIONAL_ONLY = "positional_only"
    KEYWORD_ONLY = "keyword_only"
    VARARGS = "varargs"
    KWARGS = "kwargs"


class ContractVisibility(str, Enum):
    """Visibility of contract members."""
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"


class ErrorHandling(str, Enum):
    """Error handling strategy for contract methods."""
    RAISE = "raise"
    RETURN_NONE = "return_none"
    RETURN_DEFAULT = "return_default"
    LOG_AND_RAISE = "log_and_raise"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ParameterSpec:
    """Specification for a method parameter."""
    name: str
    type_hint: str
    kind: ParameterKind = ParameterKind.POSITIONAL
    default_value: Optional[str] = None
    description: Optional[str] = None
    is_optional: bool = False
    validator: Optional[str] = None


@dataclass
class ReturnSpec:
    """Specification for return value."""
    type_hint: str
    description: Optional[str] = None
    is_optional: bool = False
    is_generator: bool = False
    is_async_generator: bool = False


@dataclass
class ExceptionSpec:
    """Specification for raised exception."""
    exception_type: str
    condition: str
    description: Optional[str] = None


@dataclass
class MethodSpec:
    """Specification for a contract method."""
    name: str
    description: str
    parameters: List[ParameterSpec] = field(default_factory=list)
    return_spec: Optional[ReturnSpec] = None
    exceptions: List[ExceptionSpec] = field(default_factory=list)
    visibility: ContractVisibility = ContractVisibility.PUBLIC
    is_abstract: bool = True
    is_async: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False
    is_setter: bool = False
    is_deleter: bool = False
    is_cached: bool = False
    is_final: bool = False
    is_deprecated: bool = False
    deprecation_message: Optional[str] = None
    error_handling: ErrorHandling = ErrorHandling.RAISE
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)
    complexity_target: Optional[str] = None
    performance_notes: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PropertySpec:
    """Specification for a property."""
    name: str
    type_hint: str
    description: Optional[str] = None
    visibility: ContractVisibility = ContractVisibility.PUBLIC
    has_getter: bool = True
    has_setter: bool = False
    has_deleter: bool = False
    is_abstract: bool = True
    is_cached: bool = False
    default_value: Optional[str] = None
    validator: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldSpec:
    """Specification for a data field (for dataclasses/TypedDict)."""
    name: str
    type_hint: str
    description: Optional[str] = None
    default_value: Optional[str] = None
    default_factory: Optional[str] = None
    is_required: bool = True
    is_final: bool = False
    validator: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TypeVarSpec:
    """Specification for a generic type variable."""
    name: str
    bound: Optional[str] = None
    covariant: bool = False
    contravariant: bool = False
    constraints: List[str] = field(default_factory=list)


@dataclass
class ContractSpec:
    """Complete specification for a contract."""
    name: str
    contract_type: ContractType
    description: str
    module_path: str = ""
    
    # Inheritance
    bases: List[str] = field(default_factory=list)
    protocols: List[str] = field(default_factory=list)
    
    # Generics
    type_vars: List[TypeVarSpec] = field(default_factory=list)
    is_generic: bool = False
    
    # Members
    methods: List[MethodSpec] = field(default_factory=list)
    properties: List[PropertySpec] = field(default_factory=list)
    fields: List[FieldSpec] = field(default_factory=list)
    
    # Metadata
    version: str = "1.0.0"
    author: Optional[str] = None
    since: Optional[str] = None
    is_deprecated: bool = False
    deprecation_message: Optional[str] = None
    
    # Configuration
    is_frozen: bool = False
    is_slotted: bool = True
    total: bool = True  # For TypedDict
    
    # Imports
    imports: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedContract:
    """Result of contract generation."""
    contract_spec: ContractSpec
    code: str
    file_path: Optional[Path] = None
    validation_passed: bool = False
    mypy_errors: List[str] = field(default_factory=list)
    ruff_errors: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContractGeneratorConfig:
    """Configuration for contract generator."""
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    validate_mypy: bool = True
    validate_ruff: bool = True
    include_docstrings: bool = True
    docstring_style: str = "google"
    include_contract_assertions: bool = False
    generate_implementation_stub: bool = False
    use_future_annotations: bool = True
    line_length: int = 88
    indent_size: int = 4


# ============================================================
# CONTRACT CODE GENERATOR
# ============================================================

class ContractCodeGenerator:
    """Generate contract code from specifications."""
    
    def __init__(self, config: ContractGeneratorConfig):
        self.config = config
        self.indent = " " * config.indent_size
    
    def generate(self, spec: ContractSpec) -> str:
        """Generate complete contract code."""
        lines = []
        
        # Module docstring
        lines.extend(self._generate_module_docstring(spec))
        
        # Future imports
        if self.config.use_future_annotations:
            lines.append("from __future__ import annotations")
            lines.append("")
        
        # Imports
        lines.extend(self._generate_imports(spec))
        lines.append("")
        
        # Type variables
        if spec.type_vars:
            lines.extend(self._generate_type_vars(spec.type_vars))
            lines.append("")
        
        # Class definition and docstring
        lines.append(self._generate_class_definition(spec))
        lines.extend(self._generate_class_docstring(spec))
        
        # Class body
        class_body = self._generate_class_body(spec)
        lines.extend(class_body)
        
        return "\n".join(lines)
    
    def _generate_module_docstring(self, spec: ContractSpec) -> List[str]:
        """Generate module docstring."""
        lines = []
        lines.append('"""')
        lines.append(f"{spec.name} Contract")
        lines.append("")
        lines.append(f"Type: {spec.contract_type.value}")
        lines.append(f"Version: {spec.version}")
        if spec.author:
            lines.append(f"Author: {spec.author}")
        if spec.since:
            lines.append(f"Since: {spec.since}")
        lines.append("")
        lines.append(spec.description)
        lines.append("")
        lines.append("This is an auto-generated contract definition.")
        lines.append('"""')
        lines.append("")
        return lines
    
    def _generate_imports(self, spec: ContractSpec) -> List[str]:
        """Generate import statements."""
        imports = set(spec.imports)
        
        # Add required imports based on contract type
        if spec.contract_type == ContractType.ABC:
            imports.add("from abc import ABC, abstractmethod")
        elif spec.contract_type == ContractType.PROTOCOL:
            imports.add("from typing import Protocol")
            if any(m.is_async for m in spec.methods):
                imports.add("from typing import Awaitable")
        elif spec.contract_type == ContractType.TYPED_DICT:
            imports.add("from typing import TypedDict")
            if not spec.total:
                imports.add("from typing import Required, NotRequired")
        elif spec.contract_type == ContractType.DATA_CLASS:
            imports.add("from dataclasses import dataclass, field")
        elif spec.contract_type == ContractType.PYDANTIC:
            imports.add("from pydantic import BaseModel, Field")
        
        # Add typing imports
        typing_imports = self._collect_typing_imports(spec)
        if typing_imports:
            imports.add(f"from typing import {', '.join(sorted(typing_imports))}")
        
        if spec.is_generic and spec.type_vars:
            imports.add("from typing import Generic")
        
        if any(m.is_final for m in spec.methods):
            imports.add("from typing import final")
        
        if any(m.is_cached for m in spec.properties):
            imports.add("from functools import cached_property")
        
        if spec.is_deprecated:
            imports.add("from warnings import deprecated")
        
        lines = []
        for imp in sorted(imports):
            lines.append(imp)
        
        return lines
    
    def _collect_typing_imports(self, spec: ContractSpec) -> Set[str]:
        """Collect required typing imports."""
        typing_imports = set()
        
        patterns = ["Optional", "List", "Dict", "Set", "Tuple", "Union", "Any", 
                   "Callable", "Iterable", "Iterator", "Sequence", "Mapping",
                   "Awaitable", "AsyncIterator", "AsyncIterable", "ClassVar",
                   "TypeVar", "Generic", "Protocol", "runtime_checkable"]
        
        def check_type(type_str: str):
            if type_str:
                for pattern in patterns:
                    if pattern in type_str:
                        typing_imports.add(pattern)
        
        for method in spec.methods:
            for param in method.parameters:
                check_type(param.type_hint)
            if method.return_spec:
                check_type(method.return_spec.type_hint)
        
        for prop in spec.properties:
            check_type(prop.type_hint)
        
        for field in spec.fields:
            check_type(field.type_hint)
        
        return typing_imports
    
    def _generate_type_vars(self, type_vars: List[TypeVarSpec]) -> List[str]:
        """Generate type variable definitions."""
        lines = []
        for tv in type_vars:
            parts = [f"{tv.name} = TypeVar('{tv.name}'"]
            if tv.bound:
                parts.append(f", bound={tv.bound}")
            if tv.covariant:
                parts.append(", covariant=True")
            if tv.contravariant:
                parts.append(", contravariant=True")
            parts.append(")")
            lines.append("".join(parts))
        return lines
    
    def _generate_class_definition(self, spec: ContractSpec) -> str:
        """Generate class definition line."""
        parts = [f"class {spec.name}"]
        
        # Add type variables
        if spec.is_generic and spec.type_vars:
            type_var_names = [tv.name for tv in spec.type_vars]
            parts.append(f"Generic[{', '.join(type_var_names)}]")
        
        # Add bases
        bases = list(spec.bases)
        
        if spec.contract_type == ContractType.ABC:
            if "ABC" not in bases:
                bases.insert(0, "ABC")
        elif spec.contract_type == ContractType.PROTOCOL:
            if "Protocol" not in bases:
                bases.insert(0, "Protocol")
        elif spec.contract_type == ContractType.TYPED_DICT:
            if "TypedDict" not in bases:
                bases.insert(0, "TypedDict")
        elif spec.contract_type == ContractType.PYDANTIC:
            if "BaseModel" not in bases:
                bases.insert(0, "BaseModel")
        
        bases.extend(spec.protocols)
        
        if bases:
            parts.append(f"({', '.join(bases)})")
        
        parts.append(":")
        return "".join(parts)
    
    def _generate_class_docstring(self, spec: ContractSpec) -> List[str]:
        """Generate class docstring."""
        if not self.config.include_docstrings:
            return []
        
        lines = []
        lines.append(f'{self.indent}"""')
        lines.append(f"{self.indent}{spec.description}")
        lines.append("")
        
        if spec.contract_type == ContractType.ABC:
            lines.append(f"{self.indent}This is an Abstract Base Class defining the contract.")
        elif spec.contract_type == ContractType.PROTOCOL:
            lines.append(f"{self.indent}This is a Protocol defining structural subtyping.")
        elif spec.contract_type == ContractType.TYPED_DICT:
            lines.append(f"{self.indent}This is a TypedDict defining the data structure.")
        
        if spec.type_vars:
            lines.append("")
            lines.append(f"{self.indent}Type Parameters:")
            for tv in spec.type_vars:
                bound_str = f" (bound: {tv.bound})" if tv.bound else ""
                lines.append(f"{self.indent}    {tv.name}{bound_str}")
        
        if spec.version:
            lines.append("")
            lines.append(f"{self.indent}Version: {spec.version}")
        
        if spec.is_deprecated and spec.deprecation_message:
            lines.append("")
            lines.append(f"{self.indent}.. deprecated:: {spec.deprecation_message}")
        
        lines.append(f'{self.indent}"""')
        return lines
    
    def _generate_class_body(self, spec: ContractSpec) -> List[str]:
        """Generate class body."""
        lines = []
        
        # Add __slots__
        if spec.is_slotted and spec.contract_type not in (ContractType.TYPED_DICT, ContractType.PYDANTIC):
            if spec.methods or spec.properties:
                lines.append(f"{self.indent}__slots__ = ()")
                lines.append("")
        
        # Add deprecation warning
        if spec.is_deprecated:
            if spec.deprecation_message:
                lines.append(f'{self.indent}@deprecated("{spec.deprecation_message}")')
            else:
                lines.append(f"{self.indent}@deprecated")
        
        # Add runtime_checkable for protocols
        if spec.contract_type == ContractType.PROTOCOL:
            lines.append(f"{self.indent}@runtime_checkable")
            lines.append(f"{self.indent}class {spec.name}(Protocol):")
            lines.append("")
        
        # Add fields (for dataclasses/TypedDict/Pydantic)
        if spec.fields and spec.contract_type in (ContractType.DATA_CLASS, ContractType.TYPED_DICT, ContractType.PYDANTIC):
            for field in spec.fields:
                lines.append(self._generate_field(field))
            if spec.fields:
                lines.append("")
        
        # Add properties
        for prop in spec.properties:
            lines.extend(self._generate_property(prop))
            lines.append("")
        
        # Add methods
        for method in spec.methods:
            lines.extend(self._generate_method(method))
            lines.append("")
        
        # Add implementation stub if requested
        if self.config.generate_implementation_stub and spec.contract_type == ContractType.ABC:
            lines.extend(self._generate_implementation_stub(spec))
        
        return lines
    
    def _generate_field(self, field: FieldSpec) -> str:
        """Generate field definition."""
        if field.is_required:
            return f"{self.indent}{field.name}: {field.type_hint}"
        else:
            if field.default_factory:
                return f"{self.indent}{field.name}: {field.type_hint} = field(default_factory={field.default_factory})"
            elif field.default_value is not None:
                return f"{self.indent}{field.name}: {field.type_hint} = {field.default_value}"
            else:
                return f"{self.indent}{field.name}: Optional[{field.type_hint}] = None"
    
    def _generate_property(self, prop: PropertySpec) -> List[str]:
        """Generate property methods."""
        lines = []
        
        # Property docstring
        if self.config.include_docstrings and prop.description:
            lines.append(f'{self.indent}"""')
            lines.append(f"{self.indent}{prop.description}")
            lines.append("")
            lines.append(f"{self.indent}:type: {prop.type_hint}")
            lines.append(f'{self.indent}"""')
        
        # Getter
        if prop.has_getter:
            if prop.is_abstract:
                lines.append(f"{self.indent}@property")
                lines.append(f"{self.indent}@abstractmethod")
                lines.append(f"{self.indent}def {prop.name}(self) -> {prop.type_hint}:")
                lines.append(f"{self.indent}{self.indent}...")
            else:
                decorator = "@cached_property" if prop.is_cached else "@property"
                lines.append(f"{self.indent}{decorator}")
                lines.append(f"{self.indent}def {prop.name}(self) -> {prop.type_hint}:")
                if self.config.include_docstrings:
                    lines.append(f'{self.indent}{self.indent}"""Return the {prop.name} value."""')
                lines.append(f"{self.indent}{self.indent}...")
            lines.append("")
        
        # Setter
        if prop.has_setter:
            lines.append(f"{self.indent}@{prop.name}.setter")
            if prop.is_abstract:
                lines.append(f"{self.indent}@abstractmethod")
            lines.append(f"{self.indent}def {prop.name}(self, value: {prop.type_hint}) -> None:")
            if self.config.include_docstrings:
                lines.append(f'{self.indent}{self.indent}"""Set the {prop.name} value."""')
            lines.append(f"{self.indent}{self.indent}...")
            lines.append("")
        
        # Deleter
        if prop.has_deleter:
            lines.append(f"{self.indent}@{prop.name}.deleter")
            if prop.is_abstract:
                lines.append(f"{self.indent}@abstractmethod")
            lines.append(f"{self.indent}def {prop.name}(self) -> None:")
            if self.config.include_docstrings:
                lines.append(f'{self.indent}{self.indent}"""Delete the {prop.name} value."""')
            lines.append(f"{self.indent}{self.indent}...")
            lines.append("")
        
        return lines
    
    def _generate_method(self, method: MethodSpec) -> List[str]:
        """Generate a method."""
        lines = []
        
        # Add decorators
        if method.is_final:
            lines.append(f"{self.indent}@final")
        if method.is_classmethod:
            lines.append(f"{self.indent}@classmethod")
        if method.is_staticmethod:
            lines.append(f"{self.indent}@staticmethod")
        if method.is_property:
            lines.append(f"{self.indent}@property")
        if method.is_cached:
            lines.append(f"{self.indent}@cached_property")
        if method.is_abstract:
            lines.append(f"{self.indent}@abstractmethod")
        if method.is_deprecated:
            if method.deprecation_message:
                lines.append(f'{self.indent}@deprecated("{method.deprecation_message}")')
            else:
                lines.append(f"{self.indent}@deprecated")
        
        # Method signature
        async_prefix = "async " if method.is_async else ""
        visibility_prefix = ""
        if method.visibility == ContractVisibility.PROTECTED:
            visibility_prefix = "_"
        elif method.visibility == ContractVisibility.PRIVATE:
            visibility_prefix = "__"
        
        params = self._generate_parameters(method)
        return_type = f" -> {method.return_spec.type_hint}" if method.return_spec and method.return_spec.type_hint else ""
        
        lines.append(f"{self.indent}{async_prefix}def {visibility_prefix}{method.name}({', '.join(params)}){return_type}:")
        
        # Method docstring
        if self.config.include_docstrings:
            lines.extend(self._generate_method_docstring(method))
        
        # Method body
        if method.is_abstract:
            lines.append(f"{self.indent}{self.indent}...")
        elif self.config.generate_implementation_stub:
            lines.extend(self._generate_method_stub(method))
        else:
            lines.append(f"{self.indent}{self.indent}...")
        
        return lines
    
    def _generate_parameters(self, method: MethodSpec) -> List[str]:
        """Generate parameter strings."""
        params = []
        
        # Add self/cls
        if not method.is_staticmethod:
            if method.is_classmethod:
                params.append("cls")
            else:
                params.append("self")
        
        for param in method.parameters:
            param_str = param.name
            
            if param.kind == ParameterKind.POSITIONAL_ONLY:
                param_str = f"{param_str}"
            elif param.kind == ParameterKind.KEYWORD_ONLY:
                param_str = f"*, {param_str}"
            elif param.kind == ParameterKind.VARARGS:
                param_str = f"*{param_str}"
            elif param.kind == ParameterKind.KWARGS:
                param_str = f"**{param_str}"
            
            param_str += f": {param.type_hint}"
            
            if param.default_value is not None:
                param_str += f" = {param.default_value}"
            elif param.is_optional:
                param_str += " = None"
            
            params.append(param_str)
        
        return params
    
    def _generate_method_docstring(self, method: MethodSpec) -> List[str]:
        """Generate method docstring."""
        lines = []
        lines.append(f'{self.indent}{self.indent}"""')
        lines.append(f"{self.indent}{self.indent}{method.description}")
        lines.append("")
        
        if method.parameters:
            if self.config.docstring_style == "google":
                lines.append(f"{self.indent}{self.indent}Args:")
                for param in method.parameters:
                    type_str = param.type_hint
                    default_str = f", optional" if param.default_value or param.is_optional else ""
                    desc = param.description or f"The {param.name} parameter"
                    lines.append(f"{self.indent}{self.indent}    {param.name} ({type_str}){default_str}: {desc}")
                lines.append("")
        
        if method.return_spec:
            if self.config.docstring_style == "google":
                lines.append(f"{self.indent}{self.indent}Returns:")
                type_str = method.return_spec.type_hint
                desc = method.return_spec.description or "Return value"
                lines.append(f"{self.indent}{self.indent}    {type_str}: {desc}")
                lines.append("")
        
        if method.exceptions:
            if self.config.docstring_style == "google":
                lines.append(f"{self.indent}{self.indent}Raises:")
                for exc in method.exceptions:
                    desc = exc.description or f"If {exc.condition}"
                    lines.append(f"{self.indent}{self.indent}    {exc.exception_type}: {desc}")
                lines.append("")
        
        if method.preconditions:
            lines.append(f"{self.indent}{self.indent}Preconditions:")
            for pre in method.preconditions:
                lines.append(f"{self.indent}{self.indent}    - {pre}")
            lines.append("")
        
        if method.postconditions:
            lines.append(f"{self.indent}{self.indent}Postconditions:")
            for post in method.postconditions:
                lines.append(f"{self.indent}{self.indent}    - {post}")
            lines.append("")
        
        if method.examples:
            lines.append(f"{self.indent}{self.indent}Examples:")
            for example in method.examples:
                lines.append(f"{self.indent}{self.indent}    {example}")
            lines.append("")
        
        lines.append(f'{self.indent}{self.indent}"""')
        return lines
    
    def _generate_method_stub(self, method: MethodSpec) -> List[str]:
        """Generate method implementation stub."""
        lines = []
        
        # Add contract assertions if enabled
        if self.config.include_contract_assertions:
            for pre in method.preconditions:
                lines.append(f"{self.indent}{self.indent}assert {pre}, \"Precondition violated: {pre}\"")
        
        # Generate basic return
        if method.return_spec:
            return_type = method.return_spec.type_hint
            if return_type == "None":
                lines.append(f"{self.indent}{self.indent}return")
            elif return_type == "bool":
                lines.append(f"{self.indent}{self.indent}return False")
            elif return_type == "str":
                lines.append(f'{self.indent}{self.indent}return ""')
            elif return_type == "int":
                lines.append(f"{self.indent}{self.indent}return 0")
            elif return_type == "float":
                lines.append(f"{self.indent}{self.indent}return 0.0")
            elif "List" in return_type:
                lines.append(f"{self.indent}{self.indent}return []")
            elif "Dict" in return_type:
                lines.append(f"{self.indent}{self.indent}return {{}}")
            elif "Optional" in return_type:
                lines.append(f"{self.indent}{self.indent}return None")
            else:
                lines.append(f"{self.indent}{self.indent}raise NotImplementedError(\"{method.name} must be implemented\")")
        else:
            lines.append(f"{self.indent}{self.indent}pass")
        
        return lines
    
    def _generate_implementation_stub(self, spec: ContractSpec) -> List[str]:
        """Generate implementation stub class."""
        lines = []
        lines.append("")
        lines.append(f"{self.indent}# Implementation stub")
        lines.append(f"{self.indent}class {spec.name}Impl({spec.name}):")
        lines.append(f'{self.indent}{self.indent}"""Concrete implementation of {spec.name}."""')
        lines.append("")
        
        for method in spec.methods:
            if method.is_abstract:
                lines.extend(self._generate_method_implementation(method))
        
        return lines
    
    def _generate_method_implementation(self, method: MethodSpec) -> List[str]:
        """Generate method implementation."""
        lines = []
        visibility_prefix = ""
        if method.visibility == ContractVisibility.PROTECTED:
            visibility_prefix = "_"
        elif method.visibility == ContractVisibility.PRIVATE:
            visibility_prefix = "__"
        
        async_prefix = "async " if method.is_async else ""
        params = self._generate_parameters(method)
        return_type = f" -> {method.return_spec.type_hint}" if method.return_spec and method.return_spec.type_hint else ""
        
        lines.append(f"{self.indent}{self.indent}{async_prefix}def {visibility_prefix}{method.name}({', '.join(params)}){return_type}:")
        lines.append(f'{self.indent}{self.indent}{self.indent}"""Implement {method.name}."""')
        lines.append(f"{self.indent}{self.indent}{self.indent}# TODO: Implement")
        
        if method.return_spec:
            if method.return_spec.type_hint == "None":
                lines.append(f"{self.indent}{self.indent}{self.indent}pass")
            else:
                lines.append(f"{self.indent}{self.indent}{self.indent}raise NotImplementedError()")
        else:
            lines.append(f"{self.indent}{self.indent}{self.indent}pass")
        
        lines.append("")
        return lines


# ============================================================
# MAIN CONTRACT GENERATOR
# ============================================================

class ContractGenerator:
    """
    Generates interface contracts, ABCs, and Protocols.
    
    Features:
    - Multiple contract types (ABC, Protocol, TypedDict, Dataclass, Pydantic)
    - Full type hints and docstrings
    - Pre/post condition support
    - Generic type support
    - Design by contract assertions
    - Implementation stub generation
    - Validation with mypy and ruff
    - LLM-powered generation from descriptions
    """
    
    def __init__(self, config: Optional[ContractGeneratorConfig] = None):
        self.config = config or ContractGeneratorConfig()
        self.code_generator = ContractCodeGenerator(self.config)
        self.llm = LLMClient() if self.config.use_llm else None
        self.state = StateManager(Path(".ai_state") / "contract_generator.json")
        
        self.mypy_validator = MypyValidator() if self.config.validate_mypy else None
        self.ruff_validator = RuffValidator() if self.config.validate_ruff else None
        
        logger.info("ContractGenerator initialized")
    
    def generate(self, spec: ContractSpec, output_path: Optional[Path] = None) -> GeneratedContract:
        """Generate a contract from specification."""
        logger.info(f"Generating contract: {spec.name}")
        
        # Generate code
        code = self.code_generator.generate(spec)
        
        # Validate
        mypy_errors = []
        ruff_errors = []
        
        if self.mypy_validator:
            mypy_errors = self.mypy_validator.validate_string(code)
        if self.ruff_validator:
            ruff_errors = self.ruff_validator.validate_string(code)
        
        # Write to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(code)
        
        result = GeneratedContract(
            contract_spec=spec,
            code=code,
            file_path=output_path,
            validation_passed=not (mypy_errors or ruff_errors),
            mypy_errors=mypy_errors,
            ruff_errors=ruff_errors
        )
        
        self._save_result(result)
        
        logger.info(f"Generated contract {spec.name}")
        return result
    
    def generate_from_description(self, description: str, name: str,
                                   contract_type: ContractType = ContractType.ABC,
                                   output_path: Optional[Path] = None) -> GeneratedContract:
        """Generate a contract from natural language description."""
        if not self.llm:
            raise ValueError("LLM is required for description-based generation")
        
        logger.info(f"Generating contract '{name}' from description")
        
        spec = self._parse_description(description, name, contract_type)
        return self.generate(spec, output_path)
    
    def _parse_description(self, description: str, name: str,
                           contract_type: ContractType) -> ContractSpec:
        """Parse natural language description into ContractSpec."""
        prompt = f"""
        Parse this contract description into a structured specification:
        
        Contract Name: {name}
        Contract Type: {contract_type.value}
        Description: {description}
        
        Return a JSON object with:
        - description: brief description
        - methods: list of methods with name, description, parameters, return_type
        - properties: list of properties with name, type_hint, description
        - fields: list of fields (for data contracts)
        - bases: list of base classes
        - imports: list of required imports
        
        Output only valid JSON.
        """
        
        response = self.llm.complete_json(prompt)
        
        spec = ContractSpec(
            name=name,
            contract_type=contract_type,
            description=response.get('description', description),
            bases=response.get('bases', []),
            imports=response.get('imports', [])
        )
        
        # Parse methods
        for method_data in response.get('methods', []):
            method = MethodSpec(
                name=method_data['name'],
                description=method_data.get('description', ''),
                return_spec=ReturnSpec(
                    type_hint=method_data.get('return_type', 'None')
                ) if method_data.get('return_type') else None,
                is_abstract=True
            )
            
            for param_data in method_data.get('parameters', []):
                param = ParameterSpec(
                    name=param_data['name'],
                    type_hint=param_data.get('type_hint', 'Any'),
                    description=param_data.get('description')
                )
                method.parameters.append(param)
            
            spec.methods.append(method)
        
        # Parse properties
        for prop_data in response.get('properties', []):
            prop = PropertySpec(
                name=prop_data['name'],
                type_hint=prop_data.get('type_hint', 'Any'),
                description=prop_data.get('description'),
                is_abstract=True
            )
            spec.properties.append(prop)
        
        # Parse fields
        for field_data in response.get('fields', []):
            field = FieldSpec(
                name=field_data['name'],
                type_hint=field_data.get('type_hint', 'Any'),
                description=field_data.get('description'),
                is_required=field_data.get('required', True)
            )
            spec.fields.append(field)
        
        return spec
    
    def create_service_contract(self, name: str, methods: List[Tuple[str, str, List[str]]],
                                 description: str = "") -> ContractSpec:
        """Quickly create a service contract."""
        spec = ContractSpec(
            name=name,
            contract_type=ContractType.SERVICE_CONTRACT,
            description=description or f"{name} service contract",
            bases=["ABC"]
        )
        
        for method_name, return_type, param_names in methods:
            method = MethodSpec(
                name=method_name,
                description=f"{method_name} operation",
                return_spec=ReturnSpec(type_hint=return_type),
                is_abstract=True
            )
            for param_name in param_names:
                method.parameters.append(ParameterSpec(
                    name=param_name,
                    type_hint="Any"
                ))
            spec.methods.append(method)
        
        return spec
    
    def create_repository_contract(self, entity_name: str) -> ContractSpec:
        """Create a standard repository contract."""
        spec = ContractSpec(
            name=f"{entity_name}Repository",
            contract_type=ContractType.REPOSITORY_CONTRACT,
            description=f"Repository contract for {entity_name}",
            bases=["ABC"],
            is_generic=True,
            type_vars=[TypeVarSpec(name="T", bound=entity_name)]
        )
        
        # Standard CRUD methods
        crud_methods = [
            ("get", "Optional[T]", ["id: str"]),
            ("get_all", "List[T]", []),
            ("save", "T", ["entity: T"]),
            ("delete", "bool", ["id: str"]),
            ("exists", "bool", ["id: str"]),
        ]
        
        for method_name, return_type, params in crud_methods:
            method = MethodSpec(
                name=method_name,
                description=f"{method_name} {entity_name}",
                return_spec=ReturnSpec(type_hint=return_type),
                is_abstract=True
            )
            for param_str in params:
                name, type_hint = param_str.split(": ")
                method.parameters.append(ParameterSpec(name=name, type_hint=type_hint))
            spec.methods.append(method)
        
        return spec
    
    def _save_result(self, result: GeneratedContract):
        """Save generation result to state."""
        history = self.state.get('history', [])
        history.append({
            'contract_name': result.contract_spec.name,
            'contract_type': result.contract_spec.contract_type.value,
            'file_path': str(result.file_path) if result.file_path else None,
            'validation_passed': result.validation_passed,
            'generated_at': result.generated_at.isoformat()
        })
        
        if len(history) > 100:
            history = history[-100:]
        
        self.state.set('history', history)
        self.state.save()
    
    def export_spec(self, spec: ContractSpec, output_path: Optional[Path] = None) -> str:
        """Export contract specification as JSON."""
        data = {
            'name': spec.name,
            'contract_type': spec.contract_type.value,
            'description': spec.description,
            'version': spec.version,
            'bases': spec.bases,
            'methods': [
                {
                    'name': m.name,
                    'description': m.description,
                    'parameters': [
                        {'name': p.name, 'type_hint': p.type_hint}
                        for p in m.parameters
                    ],
                    'return_type': m.return_spec.type_hint if m.return_spec else None,
                    'is_async': m.is_async
                }
                for m in spec.methods
            ],
            'properties': [
                {'name': p.name, 'type_hint': p.type_hint}
                for p in spec.properties
            ],
            'imports': spec.imports
        }
        
        content = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def import_spec(self, input_path: Path) -> ContractSpec:
        """Import contract specification from JSON."""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        spec = ContractSpec(
            name=data['name'],
            contract_type=ContractType(data['contract_type']),
            description=data['description'],
            version=data.get('version', '1.0.0'),
            bases=data.get('bases', []),
            imports=data.get('imports', [])
        )
        
        for method_data in data.get('methods', []):
            method = MethodSpec(
                name=method_data['name'],
                description=method_data['description'],
                return_spec=ReturnSpec(type_hint=method_data['return_type']) if method_data.get('return_type') else None,
                is_async=method_data.get('is_async', False),
                is_abstract=True
            )
            for param_data in method_data.get('parameters', []):
                method.parameters.append(ParameterSpec(
                    name=param_data['name'],
                    type_hint=param_data['type_hint']
                ))
            spec.methods.append(method)
        
        for prop_data in data.get('properties', []):
            spec.properties.append(PropertySpec(
                name=prop_data['name'],
                type_hint=prop_data['type_hint'],
                is_abstract=True
            ))
        
        return spec
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("ContractGenerator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for contract generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate interface contracts and ABCs")
    parser.add_argument("--name", type=str, required=True, help="Contract name")
    parser.add_argument("--type", choices=[t.value for t in ContractType],
                       default=ContractType.ABC.value, help="Contract type")
    parser.add_argument("--description", type=str, help="Contract description")
    parser.add_argument("--spec", type=Path, help="Import specification from JSON")
    parser.add_argument("--output", "-o", type=Path, help="Output file path")
    parser.add_argument("--export-spec", type=Path, help="Export specification to JSON")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    
    args = parser.parse_args()
    
    config = ContractGeneratorConfig(use_llm=not args.no_llm)
    generator = ContractGenerator(config)
    
    if args.spec:
        spec = generator.import_spec(args.spec)
        spec.name = args.name
    else:
        spec = ContractSpec(
            name=args.name,
            contract_type=ContractType(args.type),
            description=args.description or f"{args.name} contract"
        )
    
    if args.export_spec:
        generator.export_spec(spec, args.export_spec)
        print(f"Specification exported to {args.export_spec}")
    
    result = generator.generate(spec, args.output)
    
    if args.output:
        print(f"Contract generated at {args.output}")
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