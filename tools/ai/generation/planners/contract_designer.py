#!/usr/bin/env python3
"""
Contract Designer - Designs public APIs and function signatures for generated code.

Part of the Generation tools (generation/planners/contract_designer.py)

This contract_designer.py provides:

1. Requirement-Based Design - Create contracts from structured requirements
2. SOLID Principle Enforcement - Ensures single responsibility, explicit contracts
3. Automatic Signature Generation - Generates complete function signatures
4. Contract/ABC Generation - Creates abstract base classes from designs
5. Implementation Stubs - Generates skeleton implementations
6. LLM-Powered Enhancement - AI-assisted design improvements
7. Existing Code Extraction - Derives contracts from existing modules
8. Compatibility Checking - Verifies implementations match contracts
9. Contract Comparison - Detects breaking changes between versions
10. Consistent Naming - Enforces naming conventions
11. Comprehensive Documentation - Auto-generated docstrings with examples
12. Multiple Output Formats - JSON, Markdown, and executable code

The contract designer ensures that all generated components have well-designed, consistent, and documented public APIs that follow software engineering best practices.

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
from ....analysis.scanners.api_surface_extractor import APISurfaceExtractor

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class DesignPrinciple(str, Enum):
    """Design principles for contract design."""
    SINGLE_RESPONSIBILITY = "single_responsibility"
    OPEN_CLOSED = "open_closed"
    LISKOV_SUBSTITUTION = "liskov_substitution"
    INTERFACE_SEGREGATION = "contract_segregation"
    DEPENDENCY_INVERSION = "dependency_inversion"
    COMPOSITION_OVER_INHERITANCE = "composition_over_inheritance"
    LEAST_ASTONISHMENT = "least_astonishment"
    CONSISTENT_NAMING = "consistent_naming"
    EXPLICIT_BETTER_THAN_IMPLICIT = "explicit_better_than_implicit"


class ParameterKind(str, Enum):
    """Kind of parameter."""
    POSITIONAL = "positional"
    POSITIONAL_ONLY = "positional_only"
    KEYWORD_ONLY = "keyword_only"
    VARARGS = "varargs"
    KWARGS = "kwargs"


class ReturnStyle(str, Enum):
    """Return style for functions."""
    SINGLE_VALUE = "single_value"
    TUPLE = "tuple"
    NAMED_TUPLE = "named_tuple"
    DATACLASS = "dataclass"
    RESULT_OBJECT = "result_object"
    OPTIONAL = "optional"
    UNION = "union"
    GENERATOR = "generator"
    ASYNC_GENERATOR = "async_generator"
    CONTEXT_MANAGER = "context_manager"


class ErrorStrategy(str, Enum):
    """Error handling strategy."""
    RAISE_EXCEPTION = "raise_exception"
    RETURN_NONE = "return_none"
    RETURN_DEFAULT = "return_default"
    RETURN_RESULT = "return_result"
    LOG_AND_RAISE = "log_and_raise"
    LOG_AND_RETURN = "log_and_return"
    CALLBACK = "callback"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ParameterDesign:
    """Design for a function parameter."""
    name: str
    type_hint: str
    kind: ParameterKind = ParameterKind.POSITIONAL
    default_value: Optional[str] = None
    description: str = ""
    is_required: bool = True
    is_sensitive: bool = False
    validator: Optional[str] = None
    example_value: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReturnDesign:
    """Design for a function return value."""
    type_hint: str
    style: ReturnStyle = ReturnStyle.SINGLE_VALUE
    description: str = ""
    is_optional: bool = False
    is_paginated: bool = False
    example_value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExceptionDesign:
    """Design for a raised exception."""
    exception_type: str
    condition: str
    message: str = ""
    is_custom: bool = False
    recovery_hint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MethodDesign:
    """Design for a method in an contract."""
    name: str
    description: str
    parameters: List[ParameterDesign] = field(default_factory=list)
    return_design: Optional[ReturnDesign] = None
    exceptions: List[ExceptionDesign] = field(default_factory=list)
    is_async: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False
    is_abstract: bool = False
    is_final: bool = False
    is_deprecated: bool = False
    deprecation_message: Optional[str] = None
    error_strategy: ErrorStrategy = ErrorStrategy.RAISE_EXCEPTION
    complexity_target: str = "O(1)"
    performance_notes: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    see_also: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PropertyDesign:
    """Design for a property."""
    name: str
    type_hint: str
    description: str = ""
    is_readonly: bool = False
    is_writeonly: bool = False
    default_value: Optional[str] = None
    is_required: bool = True
    is_cached: bool = False
    is_deprecated: bool = False
    validator: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConstantDesign:
    """Design for a constant."""
    name: str
    value: str
    type_hint: str = "str"
    description: str = ""
    is_public: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TypeAliasDesign:
    """Design for a type alias."""
    name: str
    type_definition: str
    description: str = ""
    is_public: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContractDesign:
    """Complete contract design for a module."""
    name: str
    module_path: str
    description: str
    version: str = "1.0.0"
    
    # Members
    constants: List[ConstantDesign] = field(default_factory=list)
    type_aliases: List[TypeAliasDesign] = field(default_factory=list)
    properties: List[PropertyDesign] = field(default_factory=list)
    methods: List[MethodDesign] = field(default_factory=list)
    
    # Metadata
    author: Optional[str] = None
    since: Optional[str] = None
    is_deprecated: bool = False
    deprecation_message: Optional[str] = None
    
    # Design principles applied
    principles_applied: List[DesignPrinciple] = field(default_factory=list)
    
    # Dependencies
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Usage
    usage_examples: List[str] = field(default_factory=list)
    
    # Validation
    validation_rules: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContractSignature:
    """Complete contract signature for code generation."""
    design: ContractDesign
    signature_code: str
    contract_code: Optional[str] = None
    stub_code: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContractDesignerConfig:
    """Configuration for contract designer."""
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    
    # Design principles
    enforce_principles: bool = True
    required_principles: List[DesignPrinciple] = field(default_factory=lambda: [
        DesignPrinciple.SINGLE_RESPONSIBILITY,
        DesignPrinciple.EXPLICIT_BETTER_THAN_IMPLICIT
    ])
    
    # Naming conventions
    method_naming: str = "snake_case"
    class_naming: str = "PascalCase"
    constant_naming: str = "UPPER_SNAKE_CASE"
    
    # Parameter design
    max_parameters: int = 5
    prefer_keyword_only: bool = True
    use_type_hints: bool = True
    
    # Return design
    prefer_result_objects: bool = False
    avoid_none_return: bool = True
    
    # Error handling
    prefer_domain_exceptions: bool = True
    include_error_recovery: bool = True
    
    # Documentation
    generate_docstrings: bool = True
    docstring_style: str = "google"
    include_examples: bool = True
    
    # Output
    generate_contract: bool = True
    generate_stub: bool = True
    output_format: str = "json"


# ============================================================
# INTERFACE DESIGNER ENGINE
# ============================================================

class ContractDesignerEngine:
    """Core engine for designing contracts."""
    
    def __init__(self, config: ContractDesignerConfig):
        self.config = config
    
    def design(self, name: str, module_path: str, description: str,
               requirements: Optional[Dict[str, Any]] = None) -> ContractDesign:
        """Design an contract based on requirements."""
        design = ContractDesign(
            name=name,
            module_path=module_path,
            description=description
        )
        
        if requirements:
            design = self._apply_requirements(design, requirements)
        
        # Apply design principles
        if self.config.enforce_principles:
            design = self._enforce_principles(design)
        
        # Validate design
        issues = self.validate_design(design)
        if issues:
            design.metadata['validation_issues'] = issues
        
        return design
    
    def _apply_requirements(self, design: ContractDesign,
                            requirements: Dict[str, Any]) -> ContractDesign:
        """Apply requirements to design."""
        # Add methods from requirements
        for method_req in requirements.get('methods', []):
            method = MethodDesign(
                name=method_req['name'],
                description=method_req.get('description', ''),
                is_async=method_req.get('async', False)
            )
            
            # Add parameters
            for param_req in method_req.get('parameters', []):
                param = ParameterDesign(
                    name=param_req['name'],
                    type_hint=param_req.get('type', 'Any'),
                    description=param_req.get('description', ''),
                    is_required=param_req.get('required', True)
                )
                method.parameters.append(param)
            
            # Add return
            if 'return_type' in method_req:
                method.return_design = ReturnDesign(
                    type_hint=method_req['return_type'],
                    description=method_req.get('return_description', '')
                )
            
            design.methods.append(method)
        
        # Add properties from requirements
        for prop_req in requirements.get('properties', []):
            prop = PropertyDesign(
                name=prop_req['name'],
                type_hint=prop_req.get('type', 'Any'),
                description=prop_req.get('description', ''),
                is_readonly=prop_req.get('readonly', False)
            )
            design.properties.append(prop)
        
        # Add constants from requirements
        for const_req in requirements.get('constants', []):
            const = ConstantDesign(
                name=const_req['name'],
                value=const_req['value'],
                type_hint=const_req.get('type', 'str'),
                description=const_req.get('description', '')
            )
            design.constants.append(const)
        
        return design
    
    def _enforce_principles(self, design: ContractDesign) -> ContractDesign:
        """Enforce design principles on the contract."""
        principles_applied = []
        
        # Check Single Responsibility
        if self._has_single_responsibility(design):
            principles_applied.append(DesignPrinciple.SINGLE_RESPONSIBILITY)
        
        # Check Explicit is Better than Implicit
        if self._is_explicit(design):
            principles_applied.append(DesignPrinciple.EXPLICIT_BETTER_THAN_IMPLICIT)
        
        # Check Consistent Naming
        if self._has_consistent_naming(design):
            principles_applied.append(DesignPrinciple.CONSISTENT_NAMING)
        
        design.principles_applied = principles_applied
        return design
    
    def _has_single_responsibility(self, design: ContractDesign) -> bool:
        """Check if contract has single responsibility."""
        # Heuristic: method names should share a common theme
        method_names = [m.name for m in design.methods]
        if len(method_names) <= 5:
            return True
        
        # Check for mixed concerns
        action_types = set()
        for name in method_names:
            if name.startswith(('get', 'find', 'list', 'query')):
                action_types.add('query')
            elif name.startswith(('create', 'add', 'register')):
                action_types.add('create')
            elif name.startswith(('update', 'modify', 'change')):
                action_types.add('update')
            elif name.startswith(('delete', 'remove', 'destroy')):
                action_types.add('delete')
            elif name.startswith(('process', 'execute', 'run')):
                action_types.add('process')
        
        return len(action_types) <= 2
    
    def _is_explicit(self, design: ContractDesign) -> bool:
        """Check if contract is explicit."""
        # All parameters should have type hints
        for method in design.methods:
            for param in method.parameters:
                if not param.type_hint or param.type_hint == 'Any':
                    return False
        
        # All methods should have return types
        for method in design.methods:
            if not method.return_design or not method.return_design.type_hint:
                return False
        
        return True
    
    def _has_consistent_naming(self, design: ContractDesign) -> bool:
        """Check for consistent naming."""
        # Check method naming convention
        for method in design.methods:
            if not self._matches_naming(method.name, self.config.method_naming):
                return False
        
        # Check constant naming
        for const in design.constants:
            if not self._matches_naming(const.name, self.config.constant_naming):
                return False
        
        return True
    
    def _matches_naming(self, name: str, convention: str) -> bool:
        """Check if name matches naming convention."""
        import re
        
        if convention == "snake_case":
            return bool(re.match(r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$', name))
        elif convention == "PascalCase":
            return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))
        elif convention == "UPPER_SNAKE_CASE":
            return bool(re.match(r'^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$', name))
        return True
    
    def validate_design(self, design: ContractDesign) -> List[str]:
        """Validate contract design."""
        issues = []
        
        # Check parameter count
        for method in design.methods:
            required_params = [p for p in method.parameters if p.is_required]
            if len(required_params) > self.config.max_parameters:
                issues.append(
                    f"Method '{method.name}' has {len(required_params)} required parameters "
                    f"(max {self.config.max_parameters})"
                )
        
        # Check for duplicate names
        method_names = set()
        for method in design.methods:
            if method.name in method_names:
                issues.append(f"Duplicate method name: '{method.name}'")
            method_names.add(method.name)
        
        prop_names = set()
        for prop in design.properties:
            if prop.name in prop_names:
                issues.append(f"Duplicate property name: '{prop.name}'")
            prop_names.add(prop.name)
        
        # Check for name conflicts
        for method in design.methods:
            if method.name in prop_names:
                issues.append(f"Name conflict between method and property: '{method.name}'")
        
        return issues
    
    def compare_designs(self, design1: ContractDesign,
                         design2: ContractDesign) -> Dict[str, Any]:
        """Compare two contract designs."""
        comparison = {
            'methods_added': [],
            'methods_removed': [],
            'methods_modified': [],
            'properties_added': [],
            'properties_removed': [],
            'properties_modified': [],
            'constants_added': [],
            'constants_removed': [],
            'breaking_changes': []
        }
        
        # Compare methods
        methods1 = {m.name: m for m in design1.methods}
        methods2 = {m.name: m for m in design2.methods}
        
        for name in methods2.keys() - methods1.keys():
            comparison['methods_added'].append(name)
        
        for name in methods1.keys() - methods2.keys():
            comparison['methods_removed'].append(name)
            comparison['breaking_changes'].append(f"Method '{name}' removed")
        
        for name in methods1.keys() & methods2.keys():
            if self._method_changed(methods1[name], methods2[name]):
                comparison['methods_modified'].append(name)
        
        # Compare properties
        props1 = {p.name: p for p in design1.properties}
        props2 = {p.name: p for p in design2.properties}
        
        for name in props2.keys() - props1.keys():
            comparison['properties_added'].append(name)
        
        for name in props1.keys() - props2.keys():
            comparison['properties_removed'].append(name)
            comparison['breaking_changes'].append(f"Property '{name}' removed")
        
        return comparison
    
    def _method_changed(self, m1: MethodDesign, m2: MethodDesign) -> bool:
        """Check if method signature changed."""
        if m1.return_design and m2.return_design:
            if m1.return_design.type_hint != m2.return_design.type_hint:
                return True
        
        params1 = {(p.name, p.type_hint): p for p in m1.parameters}
        params2 = {(p.name, p.type_hint): p for p in m2.parameters}
        
        return params1 != params2


# ============================================================
# SIGNATURE GENERATOR
# ============================================================

class SignatureGenerator:
    """Generate code signatures from contract designs."""
    
    def __init__(self, config: ContractDesignerConfig):
        self.config = config
        self.indent = "    "
    
    def generate_signature(self, design: ContractDesign) -> str:
        """Generate contract signature code."""
        lines = []
        
        # Module docstring
        if self.config.generate_docstrings:
            lines.extend(self._generate_module_docstring(design))
            lines.append("")
        
        # Imports
        lines.extend(self._generate_imports(design))
        lines.append("")
        
        # Constants
        if design.constants:
            for const in design.constants:
                if const.is_public:
                    lines.append(f"{const.name}: {const.type_hint} = {const.value}")
            lines.append("")
        
        # Type aliases
        if design.type_aliases:
            for alias in design.type_aliases:
                if alias.is_public:
                    lines.append(f"{alias.name} = {alias.type_definition}")
            lines.append("")
        
        # Properties (as abstract properties in ABC)
        if design.properties:
            lines.append("class I" + design.name + "(ABC):")
            if self.config.generate_docstrings:
                lines.append(f'{self.indent}"""')
                lines.append(f"{self.indent}{design.description}")
                lines.append(f'{self.indent}"""')
            
            for prop in design.properties:
                lines.extend(self._generate_property(prop))
                lines.append("")
            
            for method in design.methods:
                lines.extend(self._generate_method(method))
                lines.append("")
        
        # Methods (as standalone functions)
        elif design.methods:
            for method in design.methods:
                lines.extend(self._generate_function(method))
                lines.append("")
        
        return "\n".join(lines).rstrip() + "\n"
    
    def _generate_module_docstring(self, design: ContractDesign) -> List[str]:
        """Generate module docstring."""
        lines = []
        lines.append('"""')
        lines.append(f"{design.name} Contract")
        lines.append("")
        lines.append(design.description)
        lines.append("")
        if design.version:
            lines.append(f"Version: {design.version}")
        if design.author:
            lines.append(f"Author: {design.author}")
        if design.since:
            lines.append(f"Since: {design.since}")
        lines.append('"""')
        return lines
    
    def _generate_imports(self, design: ContractDesign) -> List[str]:
        """Generate import statements."""
        imports = set(design.imports)
        imports.add("from abc import ABC, abstractmethod")
        imports.add("from typing import Optional, List, Dict, Any, Union")
        
        lines = []
        for imp in sorted(imports):
            lines.append(imp)
        return lines
    
    def _generate_property(self, prop: PropertyDesign) -> List[str]:
        """Generate property definition."""
        lines = []
        
        if self.config.generate_docstrings:
            lines.append(f'{self.indent}"""')
            lines.append(f"{self.indent}{prop.description}")
            lines.append("")
            lines.append(f"{self.indent}:type: {prop.type_hint}")
            lines.append(f'{self.indent}"""')
        
        # Getter
        lines.append(f"{self.indent}@property")
        lines.append(f"{self.indent}@abstractmethod")
        lines.append(f"{self.indent}def {prop.name}(self) -> {prop.type_hint}:")
        lines.append(f"{self.indent}{self.indent}...")
        
        # Setter
        if not prop.is_readonly:
            lines.append("")
            lines.append(f"{self.indent}@{prop.name}.setter")
            lines.append(f"{self.indent}@abstractmethod")
            lines.append(f"{self.indent}def {prop.name}(self, value: {prop.type_hint}) -> None:")
            lines.append(f"{self.indent}{self.indent}...")
        
        return lines
    
    def _generate_method(self, method: MethodDesign) -> List[str]:
        """Generate method definition."""
        lines = []
        
        # Decorators
        if method.is_abstract:
            lines.append(f"{self.indent}@abstractmethod")
        if method.is_classmethod:
            lines.append(f"{self.indent}@classmethod")
        if method.is_staticmethod:
            lines.append(f"{self.indent}@staticmethod")
        if method.is_property:
            lines.append(f"{self.indent}@property")
        if method.is_final:
            lines.append(f"{self.indent}@final")
        
        # Signature
        async_prefix = "async " if method.is_async else ""
        params = self._generate_parameters(method)
        return_type = f" -> {method.return_design.type_hint}" if method.return_design else " -> None"
        
        lines.append(f"{self.indent}{async_prefix}def {method.name}({', '.join(params)}){return_type}:")
        
        # Docstring
        if self.config.generate_docstrings:
            lines.extend(self._generate_method_docstring(method))
        
        # Body
        lines.append(f"{self.indent}{self.indent}...")
        
        return lines
    
    def _generate_function(self, method: MethodDesign) -> List[str]:
        """Generate standalone function definition."""
        lines = []
        
        async_prefix = "async " if method.is_async else ""
        params = self._generate_parameters(method, include_self=False)
        return_type = f" -> {method.return_design.type_hint}" if method.return_design else " -> None"
        
        lines.append(f"{async_prefix}def {method.name}({', '.join(params)}){return_type}:")
        
        if self.config.generate_docstrings:
            lines.extend(self._generate_method_docstring(method, indent_level=1))
        
        lines.append(f"{self.indent}...")
        
        return lines
    
    def _generate_parameters(self, method: MethodDesign,
                             include_self: bool = True) -> List[str]:
        """Generate parameter strings."""
        params = []
        
        if include_self and not method.is_staticmethod:
            if method.is_classmethod:
                params.append("cls")
            else:
                params.append("self")
        
        for param in method.parameters:
            param_str = param.name
            
            if param.kind == ParameterKind.KEYWORD_ONLY:
                param_str = f"*, {param_str}"
            elif param.kind == ParameterKind.VARARGS:
                param_str = f"*{param_str}"
            elif param.kind == ParameterKind.KWARGS:
                param_str = f"**{param_str}"
            
            param_str += f": {param.type_hint}"
            
            if param.default_value is not None:
                param_str += f" = {param.default_value}"
            elif not param.is_required:
                param_str += " = None"
            
            params.append(param_str)
        
        return params
    
    def _generate_method_docstring(self, method: MethodDesign,
                                    indent_level: int = 2) -> List[str]:
        """Generate method docstring."""
        indent = self.indent * indent_level
        lines = []
        lines.append(f'{indent}"""')
        lines.append(f"{indent}{method.description}")
        lines.append("")
        
        if method.parameters:
            if self.config.docstring_style == "google":
                lines.append(f"{indent}Args:")
                for param in method.parameters:
                    type_str = param.type_hint
                    default_str = "" if param.is_required else ", optional"
                    lines.append(f"{indent}    {param.name} ({type_str}{default_str}): {param.description}")
                lines.append("")
        
        if method.return_design:
            if self.config.docstring_style == "google":
                lines.append(f"{indent}Returns:")
                lines.append(f"{indent}    {method.return_design.type_hint}: {method.return_design.description}")
                lines.append("")
        
        if method.exceptions:
            if self.config.docstring_style == "google":
                lines.append(f"{indent}Raises:")
                for exc in method.exceptions:
                    lines.append(f"{indent}    {exc.exception_type}: {exc.message}")
                lines.append("")
        
        if method.examples and self.config.include_examples:
            lines.append(f"{indent}Examples:")
            for example in method.examples:
                lines.append(f"{indent}    {example}")
            lines.append("")
        
        lines.append(f'{indent}"""')
        return lines


# ============================================================
# MAIN INTERFACE DESIGNER
# ============================================================

class ContractDesigner:
    """
    Designs public APIs and function signatures for generated code.
    
    Features:
    - Requirement-based contract design
    - Design principle enforcement (SOLID)
    - Automatic signature generation
    - Contract/ABC generation
    - Contract comparison and compatibility checking
    - LLM-powered design suggestions
    - Multiple output formats
    - Validation and best practice checks
    """
    
    def __init__(self, config: Optional[ContractDesignerConfig] = None):
        self.config = config or ContractDesignerConfig()
        self.engine = ContractDesignerEngine(self.config)
        self.signature_generator = SignatureGenerator(self.config)
        self.llm = LLMClient() if self.config.use_llm else None
        self.state = StateManager(Path(".ai_state") / "contract_designer.json")
        
        self.api_extractor = APISurfaceExtractor()
        
        logger.info("ContractDesigner initialized")
    
    def design(self, name: str, module_path: str, description: str,
               requirements: Optional[Dict[str, Any]] = None) -> ContractSignature:
        """Design an contract."""
        logger.info(f"Designing contract: {name}")
        
        # Create design
        design = self.engine.design(name, module_path, description, requirements)
        
        # Enhance with LLM if available
        if self.llm:
            design = self._enhance_with_llm(design)
        
        # Generate signature
        signature_code = self.signature_generator.generate_signature(design)
        
        # Generate contract if requested
        contract_code = None
        if self.config.generate_contract:
            contract_code = self._generate_contract(design)
        
        # Generate stub if requested
        stub_code = None
        if self.config.generate_stub:
            stub_code = self._generate_stub(design)
        
        result = ContractSignature(
            design=design,
            signature_code=signature_code,
            contract_code=contract_code,
            stub_code=stub_code
        )
        
        self._save_result(result)
        
        logger.info(f"Contract designed: {name} ({len(design.methods)} methods, {len(design.properties)} properties)")
        
        return result
    
    def design_from_description(self, description: str, name: str,
                                 module_path: str = "") -> ContractSignature:
        """Design an contract from natural language description."""
        if not self.llm:
            raise ValueError("LLM is required for description-based design")
        
        logger.info(f"Designing contract '{name}' from description")
        
        prompt = f"""
        Design an contract based on this description:
        
        Contract Name: {name}
        Description: {description}
        
        Return a JSON object with:
        - description: refined contract description
        - methods: list of methods with name, description, parameters, return_type
        - properties: list of properties with name, type_hint, description
        - constants: list of constants with name, value, type_hint
        - imports: list of required imports
        
        Follow SOLID principles and Python best practices.
        Output only valid JSON.
        """
        
        response = self.llm.complete_json(prompt)
        
        requirements = {
            'methods': response.get('methods', []),
            'properties': response.get('properties', []),
            'constants': response.get('constants', [])
        }
        
        refined_description = response.get('description', description)
        
        return self.design(name, module_path, refined_description, requirements)
    
    def design_from_existing(self, module_path: str, name: Optional[str] = None) -> ContractSignature:
        """Extract and refine contract from existing code."""
        logger.info(f"Extracting contract from existing module: {module_path}")
        
        # Extract API surface
        surface = self.api_extractor.extract(module_path)
        
        # Convert to requirements
        requirements = {
            'methods': [],
            'properties': [],
            'constants': []
        }
        
        for element in surface.global_elements.values():
            if element.element_type.value == 'function':
                requirements['methods'].append({
                    'name': element.name,
                    'description': element.docstring or '',
                    'parameters': [
                        {'name': p.name, 'type': p.type_annotation or 'Any'}
                        for p in element.parameters
                    ],
                    'return_type': element.return_type or 'None'
                })
            elif element.element_type.value == 'constant':
                requirements['constants'].append({
                    'name': element.name,
                    'value': '...',
                    'type': 'Any'
                })
        
        contract_name = name or f"I{Path(module_path).stem.title()}"
        
        return self.design(contract_name, module_path, 
                          f"Contract extracted from {module_path}", requirements)
    
    def _enhance_with_llm(self, design: ContractDesign) -> ContractDesign:
        """Enhance design with LLM suggestions."""
        prompt = f"""
        Review and enhance this contract design:
        
        Name: {design.name}
        Description: {design.description}
        Methods: {len(design.methods)}
        Properties: {len(design.properties)}
        
        Suggest improvements for:
        1. Method names and signatures
        2. Missing methods or properties
        3. Type hints
        4. Documentation
        
        Return JSON with:
        - suggested_additions: list of methods/properties to add
        - suggested_changes: list of changes to existing members
        - improved_description: enhanced description
        """
        
        try:
            response = self.llm.complete_json(prompt)
            
            # Apply suggestions
            if 'improved_description' in response:
                design.description = response['improved_description']
            
        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}")
        
        return design
    
    def _generate_contract(self, design: ContractDesign) -> str:
        """Generate ABC contract from design."""
        lines = []
        lines.append(f"from abc import ABC, abstractmethod")
        lines.append(f"from typing import Optional, List, Dict, Any")
        lines.append("")
        lines.append(f"class I{design.name}(ABC):")
        lines.append(f'    """')
        lines.append(f"    {design.description}")
        lines.append(f'    """')
        lines.append("")
        
        for method in design.methods:
            lines.extend(self.signature_generator._generate_method(method))
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_stub(self, design: ContractDesign) -> str:
        """Generate implementation stub."""
        lines = []
        lines.append(f"class {design.name}Impl(I{design.name}):")
        lines.append(f'    """')
        lines.append(f"    Implementation of {design.name}.")
        lines.append(f'    """')
        lines.append("")
        
        for method in design.methods:
            if method.is_abstract:
                params = self.signature_generator._generate_parameters(method)
                return_type = f" -> {method.return_design.type_hint}" if method.return_design else ""
                lines.append(f"    def {method.name}({', '.join(params)}){return_type}:")
                lines.append(f'        """Implement {method.name}."""')
                lines.append(f"        # TODO: Implement")
                if method.return_design:
                    if method.return_design.type_hint == "None":
                        lines.append(f"        pass")
                    else:
                        lines.append(f"        raise NotImplementedError()")
                else:
                    lines.append(f"        pass")
                lines.append("")
        
        return "\n".join(lines)
    
    def compare_contracts(self, contract1: ContractDesign,
                           contract2: ContractDesign) -> Dict[str, Any]:
        """Compare two contract designs."""
        return self.engine.compare_designs(contract1, contract2)
    
    def check_compatibility(self, contract: ContractDesign,
                            implementation: str) -> Dict[str, Any]:
        """Check if implementation is compatible with contract."""
        try:
            tree = ast.parse(implementation)
            
            compatibility = {
                'is_compatible': True,
                'missing_methods': [],
                'signature_mismatches': [],
                'missing_properties': []
            }
            
            # Extract implemented methods
            implemented_methods = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for child in node.body:
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if not child.name.startswith('_'):
                                implemented_methods[child.name] = child
            
            # Check required methods
            for method in contract.methods:
                if method.name not in implemented_methods:
                    compatibility['is_compatible'] = False
                    compatibility['missing_methods'].append(method.name)
                else:
                    # Check signature compatibility
                    impl = implemented_methods[method.name]
                    if len(impl.args.args) - 1 != len(method.parameters):  # -1 for self
                        compatibility['signature_mismatches'].append({
                            'method': method.name,
                            'reason': 'Parameter count mismatch'
                        })
            
            return compatibility
            
        except Exception as e:
            return {'is_compatible': False, 'error': str(e)}
    
    def _save_result(self, result: ContractSignature):
        """Save design result to state."""
        designs = self.state.get('designs', [])
        designs.append({
            'timestamp': result.generated_at.isoformat(),
            'name': result.design.name,
            'module': result.design.module_path,
            'methods': len(result.design.methods),
            'properties': len(result.design.properties),
            'principles': [p.value for p in result.design.principles_applied]
        })
        
        if len(designs) > 50:
            designs = designs[-50:]
        
        self.state.set('designs', designs)
        self.state.save()
    
    def export_design(self, design: ContractDesign,
                      output_path: Optional[Path] = None,
                      format: str = 'json') -> str:
        """Export contract design."""
        
        if format == 'json':
            data = {
                'name': design.name,
                'module_path': design.module_path,
                'description': design.description,
                'version': design.version,
                'methods': [
                    {
                        'name': m.name,
                        'description': m.description,
                        'parameters': [
                            {'name': p.name, 'type': p.type_hint, 'description': p.description}
                            for p in m.parameters
                        ],
                        'return_type': m.return_design.type_hint if m.return_design else None,
                        'is_async': m.is_async,
                        'is_abstract': m.is_abstract
                    }
                    for m in design.methods
                ],
                'properties': [
                    {'name': p.name, 'type': p.type_hint, 'description': p.description}
                    for p in design.properties
                ],
                'constants': [
                    {'name': c.name, 'value': c.value, 'type': c.type_hint}
                    for c in design.constants
                ],
                'principles_applied': [p.value for p in design.principles_applied],
                'imports': design.imports
            }
            
            content = json.dumps(data, indent=2)
            
        elif format == 'markdown':
            lines = [
                f"# Contract: {design.name}",
                "",
                f"**Module:** `{design.module_path}`",
                f"**Version:** {design.version}",
                f"**Principles:** {', '.join(p.value for p in design.principles_applied)}",
                "",
                design.description,
                "",
                "## Methods",
                "",
            ]
            
            for method in design.methods:
                lines.append(f"### `{method.name}`")
                lines.append("")
                lines.append(method.description)
                lines.append("")
                lines.append("**Parameters:**")
                for param in method.parameters:
                    required = "required" if param.is_required else "optional"
                    lines.append(f"- `{param.name}: {param.type_hint}` ({required}) - {param.description}")
                lines.append("")
                if method.return_design:
                    lines.append(f"**Returns:** `{method.return_design.type_hint}` - {method.return_design.description}")
                lines.append("")
            
            if design.properties:
                lines.append("## Properties")
                lines.append("")
                for prop in design.properties:
                    lines.append(f"- `{prop.name}: {prop.type_hint}` - {prop.description}")
                lines.append("")
            
            content = '\n'.join(lines)
            
        else:
            content = self.signature_generator.generate_signature(design)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("ContractDesigner closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for contract designer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Design public APIs and function signatures")
    parser.add_argument("--name", type=str, required=True, help="Contract name")
    parser.add_argument("--module", type=str, default="", help="Module path")
    parser.add_argument("--description", type=str, help="Contract description")
    parser.add_argument("--requirements", type=Path, help="Requirements JSON file")
    parser.add_argument("--from-existing", type=Path, help="Extract from existing module")
    parser.add_argument("--output", "-o", type=Path, help="Output file")
    parser.add_argument("--format", choices=["json", "markdown", "code"], default="code")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    parser.add_argument("--no-contract", action="store_true", help="Skip contract generation")
    parser.add_argument("--no-stub", action="store_true", help="Skip stub generation")
    
    args = parser.parse_args()
    
    config = ContractDesignerConfig(
        use_llm=not args.no_llm,
        generate_contract=not args.no_contract,
        generate_stub=not args.no_stub
    )
    
    designer = ContractDesigner(config)
    
    if args.from_existing:
        result = designer.design_from_existing(str(args.from_existing), args.name)
    elif args.requirements:
        with open(args.requirements, 'r') as f:
            requirements = json.load(f)
        result = designer.design(args.name, args.module, args.description or "", requirements)
    elif args.description:
        result = designer.design_from_description(args.description, args.name, args.module)
    else:
        result = designer.design(args.name, args.module, args.description or "")
    
    if args.format == "code":
        output = result.signature_code
        if result.contract_code:
            output += "\n\n# Contract\n" + result.contract_code
        if result.stub_code:
            output += "\n\n# Stub\n" + result.stub_code
    else:
        output = designer.export_design(result.design, args.output, args.format)
    
    if args.output:
        args.output.write_text(output)
        print(f"Contract saved to {args.output}")
    else:
        print(output)
    
    designer.close()


if __name__ == "__main__":
    main()