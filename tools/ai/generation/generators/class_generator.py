#!/usr/bin/env python3
"""
Class Generator - AI Development Framework
Generates Python classes from specifications with full type hints and documentation.

Part of the Level 3 Generation tools (generators/class_generator.py)

This class_generator.py provides:

1. Specification-Based Generation - Generate classes from structured ClassSpec objects
2. Multiple Class Types - Dataclasses, enums, ABCs, Protocols, Pydantic, attrs, etc.
3. Full Type Hints - Complete type annotations for all fields and methods
4. Comprehensive Docstrings - Google, NumPy, or Sphinx style documentation
5. Iterative Refinement - Automatic validation and improvement cycle
6. LLM-Powered Description Parsing - Generate from natural language descriptions
7. Batch Generation - Generate multiple classes or entire modules
8. Quick Templates - Helper methods for common class patterns
9. Import Management - Automatic typing imports based on type hints
10. Validation Integration - mypy and ruff validation built-in
11. Spec Export/Import - JSON serialization for specifications
12. Special Method Generation - Auto-generate __init__, __repr__, __eq__ when appropriate

The class generator produces production-ready, type-safe Python classes with minimal effort.
"""

import json
import ast
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

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class ClassType(str, Enum):
    """Type of class to generate."""
    REGULAR = "regular"
    DATACLASS = "dataclass"
    ENUM = "enum"
    ABC = "abc"
    PROTOCOL = "protocol"
    EXCEPTION = "exception"
    PYDANTIC = "pydantic"
    ATTRS = "attrs"
    SINGLETON = "singleton"
    MIXIN = "mixin"
    SERVICE = "service"
    REPOSITORY = "repository"
    DTO = "dto"
    ENTITY = "entity"
    VALUE_OBJECT = "value_object"


class MethodType(str, Enum):
    """Type of method."""
    INSTANCE = "instance"
    CLASS = "classmethod"
    STATIC = "staticmethod"
    PROPERTY = "property"
    CACHED_PROPERTY = "cached_property"
    ABSTRACT = "abstractmethod"
    SETTER = "setter"
    DELETER = "deleter"


class Visibility(str, Enum):
    """Visibility level."""
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class FieldSpec:
    """Specification for a class field."""
    name: str
    type_hint: str
    default_value: Optional[str] = None
    default_factory: Optional[str] = None
    visibility: Visibility = Visibility.PUBLIC
    is_required: bool = True
    is_final: bool = False
    is_class_var: bool = False
    is_init_var: bool = False
    description: Optional[str] = None
    validator: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MethodSpec:
    """Specification for a method."""
    name: str
    method_type: MethodType = MethodType.INSTANCE
    visibility: Visibility = Visibility.PUBLIC
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: str = "None"
    body: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_abstract: bool = False
    is_final: bool = False
    is_overload: bool = False
    raises: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class PropertySpec:
    """Specification for a property."""
    name: str
    type_hint: str
    visibility: Visibility = Visibility.PUBLIC
    getter_body: Optional[str] = None
    setter_body: Optional[str] = None
    deleter_body: Optional[str] = None
    docstring: Optional[str] = None
    is_cached: bool = False
    is_abstract: bool = False


@dataclass
class ClassSpec:
    """Complete specification for a class."""
    name: str
    class_type: ClassType = ClassType.REGULAR
    module_path: str = ""
    description: str = ""
    docstring: Optional[str] = None
    bases: List[str] = field(default_factory=list)
    metaclass: Optional[str] = None
    fields: List[FieldSpec] = field(default_factory=list)
    methods: List[MethodSpec] = field(default_factory=list)
    properties: List[PropertySpec] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    type_vars: List[str] = field(default_factory=list)
    is_frozen: bool = False
    is_slotted: bool = True
    is_generic: bool = False
    order: bool = False
    eq: bool = True
    repr: bool = True
    hash: Optional[bool] = None
    init: bool = True
    match_args: bool = True
    imports: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedClass:
    """Result of class generation."""
    class_spec: ClassSpec
    code: str
    file_path: Optional[Path] = None
    validation_passed: bool = False
    mypy_errors: List[str] = field(default_factory=list)
    ruff_errors: List[str] = field(default_factory=list)
    iterations: int = 0
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ClassGeneratorConfig:
    """Configuration for class generator."""
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    max_iterations: int = 5
    validate_mypy: bool = True
    validate_ruff: bool = True
    add_timestamps: bool = True
    include_type_hints: bool = True
    use_future_annotations: bool = True
    docstring_style: str = "google"  # google, numpy, sphinx
    line_length: int = 88
    indent_size: int = 4


# ============================================================
# CODE GENERATORS
# ============================================================

class ClassCodeGenerator:
    """Generate Python class code from specifications."""
    
    def __init__(self, config: ClassGeneratorConfig):
        self.config = config
        self.indent = " " * config.indent_size
    
    def generate(self, spec: ClassSpec) -> str:
        """Generate complete class code."""
        lines = []
        
        # Add imports
        if spec.imports:
            lines.extend(self._generate_imports(spec.imports))
            lines.append("")
        
        # Add module docstring if this is the main module
        if spec.module_path and not spec.module_path.startswith("_"):
            lines.append(f'"""')
            lines.append(f"{spec.name} - {spec.description or 'Auto-generated class'}")
            lines.append(f'"""')
            lines.append("")
        
        # Add future imports
        if self.config.use_future_annotations:
            lines.append("from __future__ import annotations")
            lines.append("")
        
        # Add typing imports
        lines.extend(self._generate_typing_imports(spec))
        lines.append("")
        
        # Add class decorators
        decorators = self._generate_decorators(spec)
        lines.extend(decorators)
        
        # Class definition
        class_def = self._generate_class_definition(spec)
        lines.append(class_def)
        
        # Class docstring
        docstring = self._generate_class_docstring(spec)
        if docstring:
            lines.append(docstring)
        
        # Class body
        class_body = self._generate_class_body(spec)
        lines.extend(class_body)
        
        # Close class
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_imports(self, imports: List[str]) -> List[str]:
        """Generate import statements."""
        lines = []
        for imp in imports:
            if imp.startswith("from "):
                lines.append(imp)
            else:
                lines.append(f"import {imp}")
        return lines
    
    def _generate_typing_imports(self, spec: ClassSpec) -> List[str]:
        """Generate necessary typing imports."""
        typing_imports = set()
        
        # Check for type hints
        for field in spec.fields:
            if "Optional" in field.type_hint or "List" in field.type_hint or "Dict" in field.type_hint:
                typing_imports.update(self._extract_typing_types(field.type_hint))
        
        for method in spec.methods:
            if method.return_type and method.return_type != "None":
                typing_imports.update(self._extract_typing_types(method.return_type))
            for param in method.parameters:
                if "type_hint" in param:
                    typing_imports.update(self._extract_typing_types(param["type_hint"]))
        
        if spec.is_generic and spec.type_vars:
            typing_imports.add("TypeVar")
            typing_imports.add("Generic")
        
        if spec.class_type == ClassType.PROTOCOL:
            typing_imports.add("Protocol")
        
        if spec.class_type == ClassType.ABC or any(m.is_abstract for m in spec.methods):
            typing_imports.add("ABC")
            typing_imports.add("abstractmethod")
        
        lines = []
        if typing_imports:
            imports_str = ", ".join(sorted(typing_imports))
            if len(imports_str) > 80:
                lines.append("from typing import (")
                for imp in sorted(typing_imports):
                    lines.append(f"    {imp},")
                lines.append(")")
            else:
                lines.append(f"from typing import {imports_str}")
        
        return lines
    
    def _extract_typing_types(self, type_str: str) -> Set[str]:
        """Extract typing types from type hint string."""
        types = set()
        typing_patterns = ["Optional", "List", "Dict", "Set", "Tuple", "Union", "Any", 
                          "Callable", "Iterable", "Iterator", "Sequence", "Mapping", "Type"]
        
        for pattern in typing_patterns:
            if pattern in type_str:
                types.add(pattern)
        
        return types
    
    def _generate_decorators(self, spec: ClassSpec) -> List[str]:
        """Generate class decorators."""
        lines = []
        
        if spec.class_type == ClassType.DATACLASS:
            decorator = "@dataclass"
            options = []
            if spec.init is not True:
                options.append(f"init={spec.init}")
            if spec.repr is not True:
                options.append(f"repr={spec.repr}")
            if spec.eq is not True:
                options.append(f"eq={spec.eq}")
            if spec.order:
                options.append(f"order={spec.order}")
            if spec.is_frozen:
                options.append(f"frozen={spec.is_frozen}")
            if spec.is_slotted is not True:
                options.append(f"slots={spec.is_slotted}")
            if spec.hash is not None:
                options.append(f"unsafe_hash={spec.hash}")
            if spec.match_args is not True:
                options.append(f"match_args={spec.match_args}")
            
            if options:
                decorator += f"({', '.join(options)})"
            lines.append(decorator)
        
        elif spec.class_type == ClassType.ENUM:
            lines.append("from enum import Enum")
            lines.append("")
        
        elif spec.class_type == ClassType.PYDANTIC:
            lines.append("from pydantic import BaseModel")
            lines.append("")
        
        elif spec.class_type == ClassType.ATTRS:
            lines.append("import attr")
            lines.append("@attr.s(auto_attribs=True)")
            if spec.is_frozen:
                lines.append("@attr.s(frozen=True)")
        
        # Custom decorators
        for decorator in spec.decorators:
            if not decorator.startswith('@'):
                decorator = '@' + decorator
            lines.append(decorator)
        
        return lines
    
    def _generate_class_definition(self, spec: ClassSpec) -> str:
        """Generate class definition line."""
        parts = [f"class {spec.name}"]
        
        # Add type variables
        if spec.is_generic and spec.type_vars:
            parts.append(f"Generic[{', '.join(spec.type_vars)}]")
        
        # Add bases
        bases = list(spec.bases)
        if spec.class_type == ClassType.ENUM:
            bases.insert(0, "Enum")
        elif spec.class_type == ClassType.PROTOCOL:
            bases.insert(0, "Protocol")
        elif spec.class_type == ClassType.ABC:
            bases.insert(0, "ABC")
        elif spec.class_type == ClassType.PYDANTIC:
            bases.insert(0, "BaseModel")
        elif spec.class_type == ClassType.EXCEPTION:
            bases.insert(0, "Exception")
        
        if bases:
            parts.append(f"({', '.join(bases)})")
        
        # Add metaclass
        if spec.metaclass:
            parts.append(f", metaclass={spec.metaclass}")
        
        parts.append(":")
        return "".join(parts)
    
    def _generate_class_docstring(self, spec: ClassSpec) -> Optional[str]:
        """Generate class docstring."""
        if not spec.docstring and not spec.description:
            return None
        
        lines = [f'{self.indent}"""']
        
        if spec.docstring:
            lines.append(f"{self.indent}{spec.docstring}")
        elif spec.description:
            lines.append(f"{self.indent}{spec.description}")
        
        lines.append("")
        
        # Add field documentation
        if spec.fields and self.config.docstring_style == "google":
            lines.append(f"{self.indent}Attributes:")
            for field in spec.fields:
                if field.visibility == Visibility.PUBLIC:
                    desc = field.description or ""
                    lines.append(f"{self.indent}    {field.name} ({field.type_hint}): {desc}")
        
        lines.append(f'{self.indent}"""')
        
        return "\n".join(lines)
    
    def _generate_class_body(self, spec: ClassSpec) -> List[str]:
        """Generate class body."""
        lines = []
        
        # Add __slots__
        if spec.is_slotted and spec.class_type != ClassType.DATACLASS:
            slot_names = [f.name for f in spec.fields if not f.is_class_var]
            if slot_names:
                slots_str = ", ".join(f'"{name}"' for name in slot_names)
                if len(slots_str) > 80:
                    lines.append(f"{self.indent}__slots__ = (")
                    for name in slot_names:
                        lines.append(f'{self.indent}{self.indent}"{name}",')
                    lines.append(f"{self.indent})")
                else:
                    lines.append(f"{self.indent}__slots__ = ({slots_str})")
                lines.append("")
        
        # Add class variables
        for field in spec.fields:
            if field.is_class_var:
                lines.append(self._generate_field(field))
        
        if any(not f.is_class_var for f in spec.fields):
            lines.append("")
        
        # Add __init__ if needed
        if spec.init and spec.class_type not in (ClassType.DATACLASS, ClassType.ATTRS, ClassType.PYDANTIC):
            init_method = self._generate_init_method(spec)
            if init_method:
                lines.extend(init_method)
                lines.append("")
        
        # Add properties
        for prop in spec.properties:
            lines.extend(self._generate_property(prop))
            lines.append("")
        
        # Add methods
        for method in spec.methods:
            lines.extend(self._generate_method(method))
            lines.append("")
        
        # Add special methods if needed
        if spec.class_type == ClassType.REGULAR and spec.fields:
            if spec.repr and not self._has_method(spec, "__repr__"):
                lines.extend(self._generate_repr_method(spec))
                lines.append("")
            if spec.eq and not self._has_method(spec, "__eq__"):
                lines.extend(self._generate_eq_method(spec))
                lines.append("")
        
        return lines
    
    def _generate_field(self, field: FieldSpec) -> str:
        """Generate field definition."""
        parts = []
        
        # Name with visibility
        name = field.name
        if field.visibility == Visibility.PROTECTED:
            name = f"_{name}"
        elif field.visibility == Visibility.PRIVATE:
            name = f"__{name}"
        
        parts.append(f"{self.indent}{name}")
        
        # Type annotation
        if self.config.include_type_hints:
            parts.append(f": {field.type_hint}")
        
        # Default value
        if not field.is_required:
            if field.default_factory:
                parts.append(f" = field(default_factory={field.default_factory})")
            elif field.default_value is not None:
                parts.append(f" = {field.default_value}")
        
        return "".join(parts)
    
    def _generate_init_method(self, spec: ClassSpec) -> List[str]:
        """Generate __init__ method."""
        lines = []
        fields = [f for f in spec.fields if not f.is_class_var and not f.is_init_var]
        
        if not fields:
            return lines
        
        # Method signature
        params = ["self"]
        for field in fields:
            param = field.name
            if self.config.include_type_hints:
                param += f": {field.type_hint}"
            if not field.is_required:
                if field.default_factory:
                    param += f" = None"
                elif field.default_value is not None:
                    param += f" = {field.default_value}"
            params.append(param)
        
        lines.append(f"{self.indent}def __init__({', '.join(params)}) -> None:")
        lines.append(f'{self.indent}{self.indent}"""Initialize the {spec.name}."""')
        
        # Body
        for field in fields:
            if field.default_factory:
                lines.append(f"{self.indent}{self.indent}self.{field.name} = {field.name} if {field.name} is not None else {field.default_factory}()")
            else:
                lines.append(f"{self.indent}{self.indent}self.{field.name} = {field.name}")
        
        return lines
    
    def _generate_property(self, prop: PropertySpec) -> List[str]:
        """Generate property methods."""
        lines = []
        internal_name = f"_{prop.name}"
        
        # Getter
        decorator = "@cached_property" if prop.is_cached else "@property"
        lines.append(f"{self.indent}{decorator}")
        lines.append(f"{self.indent}def {prop.name}(self) -> {prop.type_hint}:")
        
        if prop.docstring:
            lines.append(f'{self.indent}{self.indent}"""{prop.docstring}"""')
        
        if prop.getter_body:
            lines.extend(f"{self.indent}{self.indent}{line}" for line in prop.getter_body.split("\n"))
        else:
            lines.append(f"{self.indent}{self.indent}return self.{internal_name}")
        
        lines.append("")
        
        # Setter
        if prop.setter_body is not None:
            lines.append(f"{self.indent}@{prop.name}.setter")
            lines.append(f"{self.indent}def {prop.name}(self, value: {prop.type_hint}) -> None:")
            lines.extend(f"{self.indent}{self.indent}{line}" for line in prop.setter_body.split("\n"))
            lines.append("")
        
        return lines
    
    def _generate_method(self, method: MethodSpec) -> List[str]:
        """Generate a method."""
        lines = []
        
        # Add decorators
        for decorator in method.decorators:
            if not decorator.startswith('@'):
                decorator = '@' + decorator
            lines.append(f"{self.indent}{decorator}")
        
        if method.method_type == MethodType.CLASS:
            lines.append(f"{self.indent}@classmethod")
        elif method.method_type == MethodType.STATIC:
            lines.append(f"{self.indent}@staticmethod")
        elif method.method_type == MethodType.PROPERTY:
            lines.append(f"{self.indent}@property")
        elif method.method_type == MethodType.ABSTRACT:
            lines.append(f"{self.indent}@abstractmethod")
        
        # Method signature
        params = []
        if method.method_type != MethodType.STATIC:
            params.append("self")
        if method.method_type == MethodType.CLASS:
            params[0] = "cls"
        
        for param in method.parameters:
            param_str = param["name"]
            if self.config.include_type_hints and "type_hint" in param:
                param_str += f": {param['type_hint']}"
            if "default" in param:
                param_str += f" = {param['default']}"
            params.append(param_str)
        
        async_prefix = "async " if method.is_async else ""
        return_annotation = f" -> {method.return_type}" if self.config.include_type_hints else ""
        
        visibility_prefix = ""
        if method.visibility == Visibility.PROTECTED:
            visibility_prefix = "_"
        elif method.visibility == Visibility.PRIVATE:
            visibility_prefix = "__"
        
        lines.append(f"{self.indent}{async_prefix}def {visibility_prefix}{method.name}({', '.join(params)}){return_annotation}:")
        
        # Docstring
        if method.docstring:
            lines.append(f'{self.indent}{self.indent}"""{method.docstring}"""')
        else:
            lines.append(f'{self.indent}{self.indent}"""{"Async " if method.is_async else ""}{method.name} method."""')
        
        # Method body
        if method.body:
            lines.extend(f"{self.indent}{self.indent}{line}" for line in method.body.split("\n"))
        elif method.is_abstract:
            lines.append(f"{self.indent}{self.indent}...")
        else:
            lines.append(f"{self.indent}{self.indent}pass")
        
        return lines
    
    def _generate_repr_method(self, spec: ClassSpec) -> List[str]:
        """Generate __repr__ method."""
        lines = []
        fields = [f for f in spec.fields if not f.is_class_var]
        
        lines.append(f"{self.indent}def __repr__(self) -> str:")
        lines.append(f'{self.indent}{self.indent}"""Return string representation."""')
        
        attrs = ", ".join(f"{f.name}={{self.{f.name}!r}}" for f in fields)
        lines.append(f"{self.indent}{self.indent}return f\"{spec.name}({attrs})\"")
        
        return lines
    
    def _generate_eq_method(self, spec: ClassSpec) -> List[str]:
        """Generate __eq__ method."""
        lines = []
        fields = [f for f in spec.fields if not f.is_class_var]
        
        if not fields:
            return lines
        
        lines.append(f"{self.indent}def __eq__(self, other: object) -> bool:")
        lines.append(f'{self.indent}{self.indent}"""Check equality."""')
        lines.append(f"{self.indent}{self.indent}if not isinstance(other, {spec.name}):")
        lines.append(f"{self.indent}{self.indent}{self.indent}return NotImplemented")
        
        comparisons = " and ".join(f"self.{f.name} == other.{f.name}" for f in fields)
        lines.append(f"{self.indent}{self.indent}return {comparisons}")
        
        return lines
    
    def _has_method(self, spec: ClassSpec, method_name: str) -> bool:
        """Check if class already has a method."""
        return any(m.name == method_name for m in spec.methods)


# ============================================================
# MAIN CLASS GENERATOR
# ============================================================

class ClassGenerator:
    """
    Generates Python classes from specifications.
    
    Features:
    - Generate from structured specifications
    - Support for dataclasses, enums, ABCs, Protocols
    - Full type hints and docstrings
    - Iterative refinement with validation
    - LLM-powered generation from natural language
    - Multiple output formats
    - Test generation
    - Integration with mypy and ruff
    """
    
    def __init__(self, config: Optional[ClassGeneratorConfig] = None):
        self.config = config or ClassGeneratorConfig()
        self.code_generator = ClassCodeGenerator(self.config)
        self.llm = LLMClient() if self.config.use_llm else None
        self.state = StateManager(Path(".ai_state") / "class_generator.json")
        
        self.mypy_validator = MypyValidator() if self.config.validate_mypy else None
        self.ruff_validator = RuffValidator() if self.config.validate_ruff else None
        self.refiner = IterativeRefiner(self.llm) if self.llm else None
        
        logger.info("ClassGenerator initialized")
    
    # ============================================================
    # GENERATION
    # ============================================================
    
    def generate(self, spec: ClassSpec, output_path: Optional[Path] = None) -> GeneratedClass:
        """
        Generate a class from specification.
        
        Args:
            spec: Class specification
            output_path: Optional output file path
        """
        logger.info(f"Generating class: {spec.name}")
        
        # Generate initial code
        code = self.code_generator.generate(spec)
        
        # Iterative refinement
        iteration = 0
        mypy_errors = []
        ruff_errors = []
        
        if self.refiner and self.config.max_iterations > 1:
            for iteration in range(1, self.config.max_iterations):
                # Validate
                if self.mypy_validator:
                    mypy_errors = self.mypy_validator.validate_string(code)
                if self.ruff_validator:
                    ruff_errors = self.ruff_validator.validate_string(code)
                
                if not mypy_errors and not ruff_errors:
                    logger.info(f"Validation passed at iteration {iteration}")
                    break
                
                logger.info(f"Iteration {iteration}: {len(mypy_errors)} mypy, {len(ruff_errors)} ruff errors")
                
                # Refine
                code = self.refiner.refine_class(
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
        
        # Write to file if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(code)
        
        result = GeneratedClass(
            class_spec=spec,
            code=code,
            file_path=output_path,
            validation_passed=not (mypy_errors or ruff_errors),
            mypy_errors=mypy_errors,
            ruff_errors=ruff_errors,
            iterations=iteration
        )
        
        self._save_result(result)
        
        logger.info(f"Generated class {spec.name} in {iteration} iterations")
        return result
    
    def generate_from_description(self, 
                                   description: str,
                                   class_name: str,
                                   output_path: Optional[Path] = None) -> GeneratedClass:
        """
        Generate a class from natural language description.
        
        Args:
            description: Natural language description
            class_name: Name of the class
            output_path: Optional output file path
        """
        if not self.llm:
            raise ValueError("LLM is required for description-based generation")
        
        logger.info(f"Generating class '{class_name}' from description")
        
        # Parse description into specification
        spec = self._parse_description(description, class_name)
        
        return self.generate(spec, output_path)
    
    def _parse_description(self, description: str, class_name: str) -> ClassSpec:
        """Parse natural language description into ClassSpec."""
        prompt = f"""
        Parse this class description into a structured specification:
        
        Class Name: {class_name}
        Description: {description}
        
        Return a JSON object with:
        - class_type: one of {[t.value for t in ClassType]}
        - description: brief description
        - docstring: detailed docstring
        - bases: list of base classes
        - fields: list of fields with name, type_hint, description
        - methods: list of methods with name, parameters, return_type, description
        - imports: list of required imports
        
        Output only valid JSON.
        """
        
        response = self.llm.complete_json(prompt)
        
        # Build ClassSpec
        spec = ClassSpec(
            name=class_name,
            class_type=ClassType(response.get('class_type', 'regular')),
            description=response.get('description', ''),
            docstring=response.get('docstring'),
            bases=response.get('bases', []),
            imports=response.get('imports', [])
        )
        
        # Parse fields
        for field_data in response.get('fields', []):
            field = FieldSpec(
                name=field_data['name'],
                type_hint=field_data['type_hint'],
                description=field_data.get('description'),
                is_required=field_data.get('required', True)
            )
            spec.fields.append(field)
        
        # Parse methods
        for method_data in response.get('methods', []):
            method = MethodSpec(
                name=method_data['name'],
                parameters=method_data.get('parameters', []),
                return_type=method_data.get('return_type', 'None'),
                docstring=method_data.get('description')
            )
            spec.methods.append(method)
        
        return spec
    
    # ============================================================
    # BATCH GENERATION
    # ============================================================
    
    def generate_multiple(self, 
                          specs: List[ClassSpec],
                          output_dir: Optional[Path] = None) -> List[GeneratedClass]:
        """Generate multiple classes."""
        results = []
        
        for spec in specs:
            output_path = None
            if output_dir:
                filename = f"{spec.name.lower()}.py"
                output_path = output_dir / filename
            
            result = self.generate(spec, output_path)
            results.append(result)
        
        logger.info(f"Generated {len(results)} classes")
        return results
    
    def generate_module(self,
                        specs: List[ClassSpec],
                        module_name: str,
                        output_path: Optional[Path] = None) -> str:
        """Generate a complete module with multiple classes."""
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
        lines.append("from typing import Optional, List, Dict, Any")
        lines.append("")
        
        # Generate each class
        for i, spec in enumerate(specs):
            code = self.code_generator.generate(spec)
            # Remove imports from individual class code
            code_lines = code.split("\n")
            class_start = 0
            for j, line in enumerate(code_lines):
                if line.startswith("class "):
                    class_start = j
                    break
            
            lines.extend(code_lines[class_start:])
            
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
    
    def create_dataclass_spec(self, 
                              name: str,
                              fields: List[Tuple[str, str, Optional[str]]],
                              description: str = "") -> ClassSpec:
        """Create a dataclass specification quickly."""
        spec = ClassSpec(
            name=name,
            class_type=ClassType.DATACLASS,
            description=description,
            imports=["from dataclasses import dataclass, field"]
        )
        
        for field_name, field_type, default in fields:
            field = FieldSpec(
                name=field_name,
                type_hint=field_type,
                is_required=default is None
            )
            if default:
                field.default_value = default
            spec.fields.append(field)
        
        return spec
    
    def create_enum_spec(self,
                         name: str,
                         values: List[Tuple[str, Any]],
                         description: str = "") -> ClassSpec:
        """Create an enum specification quickly."""
        spec = ClassSpec(
            name=name,
            class_type=ClassType.ENUM,
            description=description,
            imports=["from enum import Enum"]
        )
        
        for value_name, value in values:
            spec.fields.append(FieldSpec(
                name=value_name,
                type_hint="Any",
                default_value=repr(value)
            ))
        
        return spec
    
    def create_service_spec(self,
                            name: str,
                            methods: List[Tuple[str, List[str], str]],
                            description: str = "") -> ClassSpec:
        """Create a service class specification quickly."""
        spec = ClassSpec(
            name=name,
            class_type=ClassType.SERVICE,
            description=description
        )
        
        for method_name, params, return_type in methods:
            method = MethodSpec(
                name=method_name,
                parameters=[{"name": p, "type_hint": "Any"} for p in params],
                return_type=return_type
            )
            spec.methods.append(method)
        
        return spec
    
    # ============================================================
    # VALIDATION AND EXPORT
    # ============================================================
    
    def validate_spec(self, spec: ClassSpec) -> List[str]:
        """Validate a class specification."""
        errors = []
        
        if not spec.name:
            errors.append("Class name is required")
        elif not spec.name[0].isupper():
            errors.append("Class name should start with uppercase (PEP 8)")
        
        for field in spec.fields:
            if not field.name:
                errors.append("Field name is required")
            if not field.type_hint:
                errors.append(f"Type hint required for field '{field.name}'")
        
        for method in spec.methods:
            if not method.name:
                errors.append("Method name is required")
            if method.name.startswith('__') and method.name.endswith('__'):
                pass  # Special methods allowed
            elif method.name[0].isupper():
                errors.append(f"Method '{method.name}' should be lowercase (PEP 8)")
        
        return errors
    
    def _save_result(self, result: GeneratedClass):
        """Save generation result to state."""
        history = self.state.get('history', [])
        history.append({
            'class_name': result.class_spec.name,
            'file_path': str(result.file_path) if result.file_path else None,
            'validation_passed': result.validation_passed,
            'iterations': result.iterations,
            'generated_at': result.generated_at.isoformat(),
            'mypy_error_count': len(result.mypy_errors),
            'ruff_error_count': len(result.ruff_errors)
        })
        
        # Keep last 100 entries
        if len(history) > 100:
            history = history[-100:]
        
        self.state.set('history', history)
        self.state.save()
    
    def export_spec(self, spec: ClassSpec, output_path: Optional[Path] = None) -> str:
        """Export class specification as JSON."""
        data = {
            'name': spec.name,
            'class_type': spec.class_type.value,
            'description': spec.description,
            'docstring': spec.docstring,
            'bases': spec.bases,
            'fields': [
                {
                    'name': f.name,
                    'type_hint': f.type_hint,
                    'default_value': f.default_value,
                    'is_required': f.is_required,
                    'description': f.description
                }
                for f in spec.fields
            ],
            'methods': [
                {
                    'name': m.name,
                    'method_type': m.method_type.value,
                    'parameters': m.parameters,
                    'return_type': m.return_type,
                    'docstring': m.docstring,
                    'is_async': m.is_async
                }
                for m in spec.methods
            ],
            'imports': spec.imports
        }
        
        content = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def import_spec(self, input_path: Path) -> ClassSpec:
        """Import class specification from JSON."""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        spec = ClassSpec(
            name=data['name'],
            class_type=ClassType(data.get('class_type', 'regular')),
            description=data.get('description', ''),
            docstring=data.get('docstring'),
            bases=data.get('bases', []),
            imports=data.get('imports', [])
        )
        
        for field_data in data.get('fields', []):
            field = FieldSpec(
                name=field_data['name'],
                type_hint=field_data['type_hint'],
                default_value=field_data.get('default_value'),
                is_required=field_data.get('is_required', True),
                description=field_data.get('description')
            )
            spec.fields.append(field)
        
        for method_data in data.get('methods', []):
            method = MethodSpec(
                name=method_data['name'],
                method_type=MethodType(method_data.get('method_type', 'instance')),
                parameters=method_data.get('parameters', []),
                return_type=method_data.get('return_type', 'None'),
                docstring=method_data.get('docstring'),
                is_async=method_data.get('is_async', False)
            )
            spec.methods.append(method)
        
        return spec
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("ClassGenerator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for class generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Python classes from specifications")
    parser.add_argument("--name", type=str, required=True, help="Class name")
    parser.add_argument("--type", choices=[t.value for t in ClassType],
                       default=ClassType.REGULAR.value, help="Class type")
    parser.add_argument("--description", type=str, help="Class description")
    parser.add_argument("--spec", type=Path, help="Import specification from JSON")
    parser.add_argument("--output", "-o", type=Path, help="Output file path")
    parser.add_argument("--fields", nargs="*", help="Fields in format name:type")
    parser.add_argument("--bases", nargs="*", help="Base classes")
    parser.add_argument("--frozen", action="store_true", help="Make dataclass frozen")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    parser.add_argument("--export-spec", type=Path, help="Export specification to JSON")
    
    args = parser.parse_args()
    
    config = ClassGeneratorConfig(use_llm=not args.no_llm)
    generator = ClassGenerator(config)
    
    if args.spec:
        spec = generator.import_spec(args.spec)
        spec.name = args.name  # Override name
    else:
        spec = ClassSpec(
            name=args.name,
            class_type=ClassType(args.type),
            description=args.description or "",
            bases=args.bases or [],
            is_frozen=args.frozen
        )
        
        if args.fields:
            for field_str in args.fields:
                if ':' in field_str:
                    name, type_hint = field_str.split(':', 1)
                    spec.fields.append(FieldSpec(name=name.strip(), type_hint=type_hint.strip()))
    
    if args.export_spec:
        generator.export_spec(spec, args.export_spec)
        print(f"Specification exported to {args.export_spec}")
    
    result = generator.generate(spec, args.output)
    
    if args.output:
        print(f"Class generated at {args.output}")
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