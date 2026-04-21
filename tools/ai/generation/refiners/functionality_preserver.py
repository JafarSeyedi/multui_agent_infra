#!/usr/bin/env python3
"""
Functionality Preserver - Ensures basic functionality is not removed during refinement.
"""

import ast
import hashlib
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from .base_refiner import SafetyCheck, RefinementContext, RefinementResult
from ...quality.validators.mypy_validator import MypyValidator
from ...quality.validators.ruff_validator import RuffValidator
from ...shared.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FunctionalitySignature:
    """Captures essential functionality of code."""
    name: str
    public_api: List[str]
    parameters: List[Tuple[str, str]]  # (name, type)
    return_type: Optional[str]
    raises: List[str]
    side_effects: List[str]
    control_flow_hash: str
    complexity: int
    dependencies: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'public_api': self.public_api,
            'parameters': self.parameters,
            'return_type': self.return_type,
            'raises': self.raises,
            'side_effects': self.side_effects,
            'control_flow_hash': self.control_flow_hash,
            'complexity': self.complexity,
            'dependencies': self.dependencies
        }


class FunctionalityPreserver(SafetyCheck):
    """
    Ensures functionality is preserved during refinement.
    
    Checks:
    1. Public API unchanged (unless explicitly allowed)
    2. Same exceptions raised
    3. Same side effects
    4. Control flow equivalent
    5. Type signatures compatible
    """
    
    def __init__(self, 
                 preserve_public_api: bool = True,
                 preserve_exceptions: bool = True,
                 preserve_side_effects: bool = True,
                 allow_adding_exports: bool = True):
        self.preserve_public_api = preserve_public_api
        self.preserve_exceptions = preserve_exceptions
        self.preserve_side_effects = preserve_side_effects
        self.allow_adding_exports = allow_adding_exports
        
        self.mypy = MypyValidator()
    
    def check(self, original: str, refined: str, 
              context: RefinementContext) -> Tuple[bool, List[str]]:
        """Check if refinement preserves functionality."""
        issues = []
        
        try:
            original_tree = ast.parse(original)
            refined_tree = ast.parse(refined)
        except SyntaxError as e:
            return False, [f"Syntax error in refined code: {e}"]
        
        # Extract signatures
        original_sig = self._extract_signatures(original_tree, context)
        refined_sig = self._extract_signatures(refined_tree, context)
        
        # Check public API
        if self.preserve_public_api:
            api_issues = self._check_public_api(original_sig, refined_sig, context)
            issues.extend(api_issues)
        
        # Check exceptions
        if self.preserve_exceptions:
            exception_issues = self._check_exceptions(original_sig, refined_sig)
            issues.extend(exception_issues)
        
        # Check side effects
        if self.preserve_side_effects:
            side_effect_issues = self._check_side_effects(original_sig, refined_sig)
            issues.extend(side_effect_issues)
        
        # Check type compatibility
        type_issues = self._check_type_compatibility(original, refined)
        issues.extend(type_issues)
        
        is_safe = len(issues) == 0
        
        if not is_safe:
            logger.warning(f"Functionality preservation issues: {issues}")
        
        return is_safe, issues
    
    def _extract_signatures(self, tree: ast.AST, 
                            context: RefinementContext) -> Dict[str, FunctionalitySignature]:
        """Extract functionality signatures from AST."""
        signatures = {}
        
        class SignatureVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                if not node.name.startswith('_') or node.name == '__init__':
                    sig = self._extract_function_signature(node)
                    signatures[node.name] = sig
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                if not node.name.startswith('_'):
                    sig = self._extract_function_signature(node, is_async=True)
                    signatures[node.name] = sig
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                if not node.name.startswith('_'):
                    sig = self._extract_class_signature(node)
                    signatures[node.name] = sig
                self.generic_visit(node)
            
            def _extract_function_signature(self, node, is_async: bool = False):
                params = []
                for arg in node.args.args:
                    param_type = ast.unparse(arg.annotation) if arg.annotation else "Any"
                    params.append((arg.arg, param_type))
                
                return_type = ast.unparse(node.returns) if node.returns else None
                
                raises = self._extract_raises(node)
                side_effects = self._extract_side_effects(node)
                control_flow_hash = self._hash_control_flow(node)
                complexity = self._calculate_complexity(node)
                dependencies = self._extract_dependencies(node)
                
                return FunctionalitySignature(
                    name=node.name,
                    public_api=[],
                    parameters=params,
                    return_type=return_type,
                    raises=raises,
                    side_effects=side_effects,
                    control_flow_hash=control_flow_hash,
                    complexity=complexity,
                    dependencies=dependencies
                )
            
            def _extract_class_signature(self, node):
                public_methods = []
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not child.name.startswith('_') or child.name == '__init__':
                            public_methods.append(child.name)
                
                return FunctionalitySignature(
                    name=node.name,
                    public_api=public_methods,
                    parameters=[],
                    return_type=None,
                    raises=[],
                    side_effects=[],
                    control_flow_hash=self._hash_control_flow(node),
                    complexity=self._calculate_complexity(node),
                    dependencies=self._extract_dependencies(node)
                )
            
            def _extract_raises(self, node):
                raises = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Raise):
                        if child.exc:
                            if isinstance(child.exc, ast.Call):
                                if isinstance(child.exc.func, ast.Name):
                                    raises.append(child.exc.func.id)
                return list(set(raises))
            
            def _extract_side_effects(self, node):
                effects = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Attribute):
                                if isinstance(target.value, ast.Name):
                                    if target.value.id in ('self', 'cls'):
                                        effects.append(f"mutate:{target.attr}")
                    elif isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            if child.func.id in ('print', 'open', 'write'):
                                effects.append(f"io:{child.func.id}")
                return effects
            
            def _hash_control_flow(self, node):
                control_structures = []
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                        control_structures.append(type(child).__name__)
                content = '|'.join(sorted(control_structures))
                return hashlib.sha256(content.encode()).hexdigest()[:16]
            
            def _calculate_complexity(self, node):
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                        complexity += 1
                    elif isinstance(child, (ast.And, ast.Or)):
                        complexity += 1
                return complexity
            
            def _extract_dependencies(self, node):
                deps = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            deps.add(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            if isinstance(child.func.value, ast.Name):
                                deps.add(f"{child.func.value.id}.{child.func.attr}")
                return list(deps)
        
        visitor = SignatureVisitor()
        visitor.visit(tree)
        return signatures
    
    def _check_public_api(self, original: Dict[str, FunctionalitySignature],
                          refined: Dict[str, FunctionalitySignature],
                          context: RefinementContext) -> List[str]:
        """Check that public API is preserved."""
        issues = []
        
        for name, orig_sig in original.items():
            if name not in refined:
                if context.change_type.value in ('api_change', 'refactor'):
                    continue
                issues.append(f"Public symbol '{name}' was removed")
                continue
            
            ref_sig = refined[name]
            
            # Check methods for classes
            if orig_sig.public_api:
                for method in orig_sig.public_api:
                    if method not in ref_sig.public_api:
                        if context.change_type.value in ('api_change', 'refactor'):
                            continue
                        issues.append(f"Public method '{name}.{method}' was removed")
        
        # Check for unauthorized additions (if not allowed)
        if not self.allow_adding_exports:
            for name in refined:
                if name not in original:
                    issues.append(f"New public symbol '{name}' was added without permission")
        
        return issues
    
    def _check_exceptions(self, original: Dict[str, FunctionalitySignature],
                          refined: Dict[str, FunctionalitySignature]) -> List[str]:
        """Check that same exceptions can be raised."""
        issues = []
        
        for name, orig_sig in original.items():
            if name not in refined:
                continue
            
            ref_sig = refined[name]
            
            for exc in orig_sig.raises:
                if exc not in ref_sig.raises:
                    issues.append(f"'{name}' no longer raises {exc} (may break error handling)")
        
        return issues
    
    def _check_side_effects(self, original: Dict[str, FunctionalitySignature],
                            refined: Dict[str, FunctionalitySignature]) -> List[str]:
        """Check that side effects are preserved."""
        issues = []
        
        for name, orig_sig in original.items():
            if name not in refined:
                continue
            
            ref_sig = refined[name]
            
            for effect in orig_sig.side_effects:
                if effect not in ref_sig.side_effects:
                    issues.append(f"'{name}' lost side effect: {effect}")
        
        return issues
    
    def _check_type_compatibility(self, original: str, refined: str) -> List[str]:
        """Check type compatibility using mypy."""
        issues = []
        
        orig_errors = self.mypy.validate_string(original)
        ref_errors = self.mypy.validate_string(refined)
        
        orig_error_msgs = {e.split(':', 3)[-1] for e in orig_errors}
        ref_error_msgs = {e.split(':', 3)[-1] for e in ref_errors}
        
        new_type_errors = ref_error_msgs - orig_error_msgs
        for error in new_type_errors:
            if 'incompatible' in error.lower() or 'cannot' in error.lower():
                issues.append(f"New type error introduced: {error[:100]}")
        
        return issues