#!/usr/bin/env python3
"""
Scope Manager - Manages module/class/function boundaries and prevents overlap.
"""

import ast
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field

from .base_refiner import SafetyCheck, RefinementContext, RefinementScope
from ...shared.logger import get_logger
from ...analysis.scanners.project_scanner import ProjectScanner, ProjectGraph

logger = get_logger(__name__)


@dataclass
class ScopeBoundary:
    """Defines a scope boundary."""
    name: str
    scope_type: RefinementScope
    exports: Set[str] = field(default_factory=set)
    imports: Set[str] = field(default_factory=set)
    internal_symbols: Set[str] = field(default_factory=set)
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)


class ScopeManager(SafetyCheck):
    """
    Manages scope boundaries and prevents overlap between components.
    
    Ensures:
    1. No symbol conflicts across modules
    2. Proper encapsulation (private symbols stay private)
    3. Import cycles not introduced
    4. Dependencies respect architectural layers
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.scanner = ProjectScanner(project_root)
        self.boundaries: Dict[str, ScopeBoundary] = {}
        self._load_project_boundaries()
    
    def _load_project_boundaries(self):
        """Load existing scope boundaries from project."""
        graph = self.scanner.scan()
        
        for module_name, module_info in graph.modules.items():
            boundary = ScopeBoundary(
                name=module_name,
                scope_type=RefinementScope.MODULE,
                exports=set(module_info.exports),
                imports=set(module_info.imports)
            )
            self.boundaries[module_name] = boundary
    
    def check(self, original: str, refined: str,
              context: RefinementContext) -> Tuple[bool, List[str]]:
        """Check that scope boundaries are respected."""
        issues = []
        
        try:
            original_tree = ast.parse(original)
            refined_tree = ast.parse(refined)
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]
        
        # Extract symbols from both versions
        original_symbols = self._extract_symbols(original_tree)
        refined_symbols = self._extract_symbols(refined_tree)
        
        # Check for symbol conflicts
        conflict_issues = self._check_conflicts(refined_symbols, context)
        issues.extend(conflict_issues)
        
        # Check encapsulation
        encapsulation_issues = self._check_encapsulation(original_symbols, refined_symbols)
        issues.extend(encapsulation_issues)
        
        # Check import cycles
        cycle_issues = self._check_import_cycles(refined_tree, context)
        issues.extend(cycle_issues)
        
        # Check layer violations
        layer_issues = self._check_layer_violations(refined_tree, context)
        issues.extend(layer_issues)
        
        return len(issues) == 0, issues
    
    def _extract_symbols(self, tree: ast.AST) -> Dict[str, Set[str]]:
        """Extract symbols by visibility."""
        symbols = {
            'public': set(),
            'protected': set(),
            'private': set(),
            'exported': set()
        }
        
        class SymbolVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_class = None
            
            def visit_ClassDef(self, node):
                if node.name.startswith('__'):
                    symbols['private'].add(node.name)
                elif node.name.startswith('_'):
                    symbols['protected'].add(node.name)
                else:
                    symbols['public'].add(node.name)
                
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = None
            
            def visit_FunctionDef(self, node):
                name = f"{self.current_class}.{node.name}" if self.current_class else node.name
                
                if node.name.startswith('__'):
                    symbols['private'].add(name)
                elif node.name.startswith('_'):
                    symbols['protected'].add(name)
                else:
                    symbols['public'].add(name)
                
                self.generic_visit(node)
            
            def visit_Assign(self, node):
                if isinstance(node.targets[0], ast.Name):
                    name = node.targets[0].id
                    if name == '__all__':
                        if isinstance(node.value, ast.List):
                            for item in node.value.elts:
                                if isinstance(item, ast.Constant):
                                    symbols['exported'].add(item.value)
        
        visitor = SymbolVisitor()
        visitor.visit(tree)
        
        return symbols
    
    def _check_conflicts(self, symbols: Dict[str, Set[str]], 
                         context: RefinementContext) -> List[str]:
        """Check for symbol conflicts with other modules."""
        issues = []
        target_module = context.target_file.stem
        
        for other_module, boundary in self.boundaries.items():
            if other_module == target_module:
                continue
            
            # Check if we're adding a symbol that already exists elsewhere
            for visibility in ['public', 'exported']:
                for symbol in symbols[visibility]:
                    if symbol in boundary.exports:
                        issues.append(
                            f"Symbol '{symbol}' already exported by '{other_module}'. "
                            f"Consider using a different name or importing."
                        )
        
        return issues
    
    def _check_encapsulation(self, original: Dict[str, Set[str]],
                             refined: Dict[str, Set[str]]) -> List[str]:
        """Check that encapsulation isn't broken."""
        issues = []
        
        # Check if any private symbols became public
        for symbol in original['private']:
            if symbol in refined['public'] or symbol in refined['exported']:
                issues.append(f"Private symbol '{symbol}' was made public (breaks encapsulation)")
        
        for symbol in original['protected']:
            if symbol in refined['exported']:
                issues.append(f"Protected symbol '{symbol}' was exported (breaks encapsulation)")
        
        return issues
    
    def _check_import_cycles(self, tree: ast.AST,
                             context: RefinementContext) -> List[str]:
        """Check for new import cycles."""
        issues = []
        
        imports = self._extract_imports(tree)
        target_module = context.target_file.stem
        
        # Build dependency graph including new imports
        graph = self.boundaries.copy()
        
        # Check for cycles
        def has_cycle(module, visited=None, path=None):
            if visited is None:
                visited = set()
            if path is None:
                path = []
            
            if module in path:
                cycle = path[path.index(module):] + [module]
                return cycle
            
            if module in visited:
                return None
            
            visited.add(module)
            path.append(module)
            
            boundary = graph.get(module)
            if boundary:
                for imp in boundary.imports:
                    if imp in graph:
                        cycle = has_cycle(imp, visited, path)
                        if cycle:
                            return cycle
            
            path.pop()
            return None
        
        cycle = has_cycle(target_module)
        if cycle:
            issues.append(f"Import cycle detected: {' -> '.join(cycle)}")
        
        return issues
    
    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract all imports from AST."""
        imports = set()
        
        class ImportVisitor(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    imports.add(alias.name)
            
            def visit_ImportFrom(self, node):
                if node.module:
                    imports.add(node.module)
        
        visitor = ImportVisitor()
        visitor.visit(tree)
        
        return imports
    
    def _check_layer_violations(self, tree: ast.AST,
                                context: RefinementContext) -> List[str]:
        """Check for architectural layer violations."""
        issues = []
        
        # This would use project-specific layer definitions
        # For now, check for circular dependencies between packages
        
        imports = self._extract_imports(tree)
        target_module = context.target_file.stem
        target_package = target_module.split('.')[0] if '.' in target_module else ''
        
        for imp in imports:
            if imp.startswith('..'):  # Relative import going up too many levels
                issues.append(f"Deep relative import '{imp}' may indicate layer violation")
        
        return issues
    
    def suggest_scope(self, code: str, context: RefinementContext) -> List[str]:
        """Suggest appropriate scope for new symbols."""
        suggestions = []
        
        try:
            tree = ast.parse(code)
            symbols = self._extract_symbols(tree)
            
            for symbol in symbols['public']:
                # Check if similar symbols exist
                similar = self._find_similar_symbols(symbol)
                if similar:
                    suggestions.append(
                        f"Symbol '{symbol}' is similar to existing: {', '.join(similar)}. "
                        f"Consider namespacing or using a more specific name."
                    )
            
            # Suggest module organization
            if len(symbols['public']) > 20:
                suggestions.append(
                    f"Module has {len(symbols['public'])} public symbols. "
                    f"Consider splitting into submodules."
                )
            
        except SyntaxError:
            pass
        
        return suggestions
    
    def _find_similar_symbols(self, symbol: str, threshold: float = 0.8) -> List[str]:
        """Find similar symbols in other modules."""
        import difflib
        
        similar = []
        for boundary in self.boundaries.values():
            for exported in boundary.exports:
                ratio = difflib.SequenceMatcher(None, symbol, exported).ratio()
                if ratio >= threshold:
                    similar.append(f"{boundary.name}.{exported}")
        
        return similar