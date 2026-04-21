#!/usr/bin/env python3
"""
Impact Analyzer - AI Development Framework
Analyzes the impact of code changes across the entire project.

Part of the Level 3 Generation tools (refiners/impact_analyzer.py)

This impact_analyzer.py provides:

1. Change Detection - Compares ASTs and git diffs to identify all changes
2. Direct Impact Analysis - Finds modules directly dependent on changed code
3. Transitive Impact Analysis - Traces impact through dependency chains
4. Breaking Change Detection - Identifies API-breaking changes
5. Test Impact Analysis - Finds tests that need to be updated/run
6. Documentation Impact - Identifies outdated documentation
7. Severity Classification - Critical, High, Medium, Low impact levels
8. Risk Score Calculation - Quantifies overall change risk (0.0 to 1.0)
9. Fix Hour Estimation - Estimates time needed to address impact
10. Migration Guide Generation - Creates guides for breaking changes
11. Git Integration - Analyzes changes from git history
12. Multiple Report Formats - Markdown and JSON reports

The impact analyzer is essential for understanding the ripple effects of code changes and ensuring safe refactoring.
"""

import ast
import json
import difflib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager
from ...shared.git_utils import GitUtils
from ...analysis.scanners.project_scanner import ProjectScanner, ProjectGraph, CodeSymbol
from ...analysis.scanners.import_graph import ImportGraphAnalyzer, ImportGraph
from ...analysis.scanners.api_surface_extractor import APISurfaceExtractor, APIElement

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class ImpactSeverity(str, Enum):
    """Severity of change impact."""
    CRITICAL = "critical"      # Breaking API change, widespread impact
    HIGH = "high"              # Breaking change, moderate impact
    MEDIUM = "medium"          # Non-breaking change, some impact
    LOW = "low"                # Minor change, limited impact
    NONE = "none"              # No impact


class ImpactType(str, Enum):
    """Type of impact."""
    DIRECT_DEPENDENCY = "direct_dependency"
    TRANSITIVE_DEPENDENCY = "transitive_dependency"
    API_BREAKING = "api_breaking"
    API_ADDITION = "api_addition"
    API_DEPRECATION = "api_deprecation"
    IMPORT_CHANGE = "import_change"
    SIGNATURE_CHANGE = "signature_change"
    TYPE_CHANGE = "type_change"
    EXCEPTION_CHANGE = "exception_change"
    BEHAVIOR_CHANGE = "behavior_change"
    TEST_FAILURE = "test_failure"
    DOC_OUTDATED = "doc_outdated"


class ChangeCategory(str, Enum):
    """Category of code change."""
    ADDITION = "addition"
    DELETION = "deletion"
    MODIFICATION = "modification"
    RENAME = "rename"
    MOVE = "move"
    REFACTOR = "refactor"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ChangeInfo:
    """Information about a specific change."""
    category: ChangeCategory
    file_path: str
    symbol_name: Optional[str] = None
    symbol_type: Optional[str] = None
    old_signature: Optional[str] = None
    new_signature: Optional[str] = None
    old_return_type: Optional[str] = None
    new_return_type: Optional[str] = None
    old_exceptions: List[str] = field(default_factory=list)
    new_exceptions: List[str] = field(default_factory=list)
    added_parameters: List[str] = field(default_factory=list)
    removed_parameters: List[str] = field(default_factory=list)
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    diff: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImpactedArtifact:
    """An artifact impacted by changes."""
    artifact_type: str  # 'module', 'class', 'function', 'test', 'doc', 'config'
    file_path: str
    symbol_name: Optional[str] = None
    impact_type: ImpactType
    severity: ImpactSeverity
    reason: str
    distance: int = 1  # Distance in dependency graph
    dependency_chain: List[str] = field(default_factory=list)
    suggested_action: Optional[str] = None
    estimated_fix_hours: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BreakingChange:
    """A breaking change that requires attention."""
    change: ChangeInfo
    impacted_artifacts: List[ImpactedArtifact] = field(default_factory=list)
    migration_guide: Optional[str] = None
    deprecation_message: Optional[str] = None
    severity: ImpactSeverity = ImpactSeverity.MEDIUM


@dataclass
class ImpactAnalysisResult:
    """Complete impact analysis result."""
    changes: List[ChangeInfo] = field(default_factory=list)
    impacted_modules: List[ImpactedArtifact] = field(default_factory=list)
    impacted_tests: List[ImpactedArtifact] = field(default_factory=list)
    impacted_docs: List[ImpactedArtifact] = field(default_factory=list)
    breaking_changes: List[BreakingChange] = field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    reverse_dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    affected_files: List[str] = field(default_factory=list)
    estimated_total_impact_hours: float = 0.0
    risk_score: float = 0.0  # 0.0 to 1.0
    analyzed_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImpactAnalyzerConfig:
    """Configuration for impact analyzer."""
    project_root: Path
    include_transitive_deps: bool = True
    max_dependency_depth: int = 5
    include_tests: bool = True
    include_docs: bool = True
    detect_breaking_changes: bool = True
    calculate_risk: bool = True
    generate_migration_guide: bool = True
    use_git_diff: bool = True
    compare_with: Optional[str] = None  # 'HEAD~1', 'main', etc.
    severity_threshold: ImpactSeverity = ImpactSeverity.LOW


# ============================================================
# CHANGE DETECTOR
# ============================================================

class ChangeDetector:
    """Detects changes between code versions."""
    
    def __init__(self, config: ImpactAnalyzerConfig):
        self.config = config
        self.git = GitUtils(config.project_root) if config.use_git_diff else None
    
    def detect_changes(self, 
                       original_code: Optional[str] = None,
                       refined_code: Optional[str] = None,
                       file_path: Optional[Path] = None) -> List[ChangeInfo]:
        """
        Detect changes between original and refined code.
        
        If original_code/refined_code not provided, uses git diff.
        """
        changes = []
        
        if original_code and refined_code:
            changes = self._detect_code_changes(original_code, refined_code, file_path)
        elif self.git:
            changes = self._detect_git_changes()
        
        return changes
    
    def _detect_code_changes(self, original: str, refined: str,
                              file_path: Optional[Path] = None) -> List[ChangeInfo]:
        """Detect changes by comparing ASTs."""
        changes = []
        file_path_str = str(file_path) if file_path else "unknown"
        
        try:
            original_tree = ast.parse(original)
            refined_tree = ast.parse(refined)
        except SyntaxError:
            # Fallback to line-based diff
            return self._detect_line_changes(original, refined, file_path_str)
        
        # Extract symbols from both versions
        original_symbols = self._extract_symbols(original_tree)
        refined_symbols = self._extract_symbols(refined_tree)
        
        # Find added symbols
        for name, info in refined_symbols.items():
            if name not in original_symbols:
                changes.append(ChangeInfo(
                    category=ChangeCategory.ADDITION,
                    file_path=file_path_str,
                    symbol_name=name,
                    symbol_type=info['type'],
                    new_signature=info.get('signature'),
                    new_return_type=info.get('return_type'),
                    line_start=info.get('line_start'),
                    line_end=info.get('line_end'),
                    diff=self._generate_diff(original, refined)
                ))
        
        # Find removed symbols
        for name, info in original_symbols.items():
            if name not in refined_symbols:
                changes.append(ChangeInfo(
                    category=ChangeCategory.DELETION,
                    file_path=file_path_str,
                    symbol_name=name,
                    symbol_type=info['type'],
                    old_signature=info.get('signature'),
                    old_return_type=info.get('return_type'),
                    line_start=info.get('line_start'),
                    line_end=info.get('line_end'),
                    diff=self._generate_diff(original, refined)
                ))
        
        # Find modified symbols
        for name in set(original_symbols) & set(refined_symbols):
            orig_info = original_symbols[name]
            ref_info = refined_symbols[name]
            
            if self._has_signature_changed(orig_info, ref_info):
                changes.append(ChangeInfo(
                    category=ChangeCategory.MODIFICATION,
                    file_path=file_path_str,
                    symbol_name=name,
                    symbol_type=orig_info['type'],
                    old_signature=orig_info.get('signature'),
                    new_signature=ref_info.get('signature'),
                    old_return_type=orig_info.get('return_type'),
                    new_return_type=ref_info.get('return_type'),
                    old_exceptions=orig_info.get('exceptions', []),
                    new_exceptions=ref_info.get('exceptions', []),
                    added_parameters=self._find_added_params(orig_info, ref_info),
                    removed_parameters=self._find_removed_params(orig_info, ref_info),
                    line_start=ref_info.get('line_start'),
                    line_end=ref_info.get('line_end'),
                    diff=self._generate_diff(original, refined)
                ))
        
        return changes
    
    def _detect_line_changes(self, original: str, refined: str,
                              file_path: str) -> List[ChangeInfo]:
        """Fallback line-based change detection."""
        changes = []
        
        diff = self._generate_diff(original, refined)
        
        # Count added/removed lines
        added_lines = sum(1 for line in diff.split('\n') if line.startswith('+') and not line.startswith('+++'))
        removed_lines = sum(1 for line in diff.split('\n') if line.startswith('-') and not line.startswith('---'))
        
        if added_lines > 0 or removed_lines > 0:
            changes.append(ChangeInfo(
                category=ChangeCategory.MODIFICATION,
                file_path=file_path,
                diff=diff,
                metadata={
                    'added_lines': added_lines,
                    'removed_lines': removed_lines
                }
            ))
        
        return changes
    
    def _detect_git_changes(self) -> List[ChangeInfo]:
        """Detect changes from git."""
        changes = []
        
        compare_with = self.config.compare_with or 'HEAD~1'
        changed_files = self.git.get_changed_files(compare_with)
        
        for file_path in changed_files:
            if file_path.suffix == '.py':
                try:
                    original = self.git.get_file_content(file_path, compare_with)
                    refined = file_path.read_text()
                    
                    file_changes = self._detect_code_changes(original, refined, file_path)
                    changes.extend(file_changes)
                except Exception as e:
                    logger.warning(f"Failed to analyze changes in {file_path}: {e}")
        
        return changes
    
    def _extract_symbols(self, tree: ast.AST) -> Dict[str, Dict[str, Any]]:
        """Extract symbols from AST."""
        symbols = {}
        
        class SymbolVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_class = None
            
            def visit_ClassDef(self, node):
                name = f"{self.current_class}.{node.name}" if self.current_class else node.name
                symbols[name] = {
                    'type': 'class',
                    'line_start': node.lineno,
                    'line_end': node.end_lineno or node.lineno,
                    'bases': [ast.unparse(b) for b in node.bases]
                }
                
                prev_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = prev_class
            
            def visit_FunctionDef(self, node):
                name = f"{self.current_class}.{node.name}" if self.current_class else node.name
                symbols[name] = self._extract_function_info(node, name)
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                name = f"{self.current_class}.{node.name}" if self.current_class else node.name
                info = self._extract_function_info(node, name)
                info['is_async'] = True
                symbols[name] = info
                self.generic_visit(node)
            
            def _extract_function_info(self, node, name):
                params = []
                for arg in node.args.args:
                    param_type = ast.unparse(arg.annotation) if arg.annotation else "Any"
                    params.append(f"{arg.arg}: {param_type}")
                
                return_type = ast.unparse(node.returns) if node.returns else "Any"
                signature = f"def {name.split('.')[-1]}({', '.join(params)}) -> {return_type}"
                
                exceptions = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Raise):
                        if child.exc and isinstance(child.exc, ast.Call):
                            if isinstance(child.exc.func, ast.Name):
                                exceptions.append(child.exc.func.id)
                
                return {
                    'type': 'function',
                    'line_start': node.lineno,
                    'line_end': node.end_lineno or node.lineno,
                    'signature': signature,
                    'return_type': return_type,
                    'exceptions': list(set(exceptions))
                }
        
        visitor = SymbolVisitor()
        visitor.visit(tree)
        
        return symbols
    
    def _has_signature_changed(self, orig: Dict, ref: Dict) -> bool:
        """Check if function signature has changed."""
        return (orig.get('signature') != ref.get('signature') or
                orig.get('return_type') != ref.get('return_type') or
                set(orig.get('exceptions', [])) != set(ref.get('exceptions', [])))
    
    def _find_added_params(self, orig: Dict, ref: Dict) -> List[str]:
        """Find parameters added to function."""
        # Simple heuristic - compare signatures
        orig_sig = orig.get('signature', '')
        ref_sig = ref.get('signature', '')
        
        orig_params = self._extract_param_names(orig_sig)
        ref_params = self._extract_param_names(ref_sig)
        
        return list(ref_params - orig_params)
    
    def _find_removed_params(self, orig: Dict, ref: Dict) -> List[str]:
        """Find parameters removed from function."""
        orig_sig = orig.get('signature', '')
        ref_sig = ref.get('signature', '')
        
        orig_params = self._extract_param_names(orig_sig)
        ref_params = self._extract_param_names(ref_sig)
        
        return list(orig_params - ref_params)
    
    def _extract_param_names(self, signature: str) -> Set[str]:
        """Extract parameter names from signature."""
        import re
        params = set()
        
        match = re.search(r'\((.*?)\)', signature)
        if match:
            param_str = match.group(1)
            for param in param_str.split(','):
                param = param.strip()
                if ':' in param:
                    name = param.split(':', 1)[0].strip()
                    params.add(name)
        
        return params
    
    def _generate_diff(self, original: str, refined: str) -> str:
        """Generate unified diff."""
        original_lines = original.splitlines(keepends=True)
        refined_lines = refined.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines, refined_lines,
            fromfile='original', tofile='refined'
        )
        
        return ''.join(diff)


# ============================================================
# IMPACT CALCULATOR
# ============================================================

class ImpactCalculator:
    """Calculates impact of changes across the project."""
    
    def __init__(self, config: ImpactAnalyzerConfig,
                 project_graph: Optional[ProjectGraph] = None,
                 import_graph: Optional[ImportGraph] = None):
        self.config = config
        
        self.scanner = ProjectScanner(project_root=config.project_root)
        self.import_analyzer = ImportGraphAnalyzer(config.project_root)
        
        self.project_graph = project_graph or self.scanner.scan()
        self.import_graph = import_graph or self.import_analyzer.analyze()
    
    def calculate_impact(self, changes: List[ChangeInfo]) -> ImpactAnalysisResult:
        """Calculate impact of all changes."""
        result = ImpactAnalysisResult(changes=changes)
        
        # Build dependency graphs
        result.dependency_graph = self.import_graph.dependency_graph
        result.reverse_dependency_graph = self._build_reverse_dependency_graph()
        
        # Calculate impact for each change
        for change in changes:
            impacted = self._calculate_change_impact(change, result)
            result.impacted_modules.extend(impacted)
            
            # Check for breaking changes
            if self.config.detect_breaking_changes:
                breaking = self._detect_breaking_change(change, impacted)
                if breaking:
                    result.breaking_changes.append(breaking)
        
        # Deduplicate impacted modules
        result.impacted_modules = self._deduplicate_impacts(result.impacted_modules)
        
        # Find impacted tests
        if self.config.include_tests:
            result.impacted_tests = self._find_impacted_tests(result.impacted_modules)
        
        # Find impacted docs
        if self.config.include_docs:
            result.impacted_docs = self._find_impacted_docs(result.impacted_modules)
        
        # Collect all affected files
        result.affected_files = self._collect_affected_files(result)
        
        # Calculate total impact hours
        result.estimated_total_impact_hours = self._estimate_total_hours(result)
        
        # Calculate risk score
        if self.config.calculate_risk:
            result.risk_score = self._calculate_risk_score(result)
        
        return result
    
    def _build_reverse_dependency_graph(self) -> Dict[str, List[str]]:
        """Build reverse dependency graph."""
        reverse = defaultdict(list)
        for source, targets in self.import_graph.dependency_graph.items():
            for target in targets:
                reverse[target].append(source)
        return dict(reverse)
    
    def _calculate_change_impact(self, change: ChangeInfo,
                                  result: ImpactAnalysisResult) -> List[ImpactedArtifact]:
        """Calculate impact of a single change."""
        impacts = []
        
        if not change.symbol_name:
            # File-level change - impact all dependents
            module_name = self._file_to_module(change.file_path)
            impacts.extend(self._find_module_dependents(module_name))
            return impacts
        
        # Symbol-level change
        module_name = self._file_to_module(change.file_path)
        full_symbol = f"{module_name}.{change.symbol_name}" if module_name else change.symbol_name
        
        # Find direct dependents
        dependents = self._find_symbol_dependents(full_symbol)
        
        for dependent in dependents:
            severity = self._determine_severity(change, dependent)
            impact_type = self._determine_impact_type(change)
            
            impacts.append(ImpactedArtifact(
                artifact_type='module',
                file_path=self._module_to_file(dependent),
                symbol_name=dependent,
                impact_type=impact_type,
                severity=severity,
                reason=self._generate_impact_reason(change, dependent),
                distance=1,
                dependency_chain=[full_symbol, dependent]
            ))
        
        # Find transitive dependents if configured
        if self.config.include_transitive_deps:
            transitive = self._find_transitive_dependents(full_symbol, max_depth=self.config.max_dependency_depth)
            for dep, distance in transitive:
                severity = self._downgrade_severity_for_distance(severity, distance)
                
                impacts.append(ImpactedArtifact(
                    artifact_type='module',
                    file_path=self._module_to_file(dep),
                    symbol_name=dep,
                    impact_type=ImpactType.TRANSITIVE_DEPENDENCY,
                    severity=severity,
                    reason=f"Transitive dependency (distance {distance})",
                    distance=distance,
                    dependency_chain=self._get_dependency_chain(full_symbol, dep)
                ))
        
        return impacts
    
    def _file_to_module(self, file_path: str) -> str:
        """Convert file path to module name."""
        path = Path(file_path)
        try:
            rel_path = path.relative_to(self.config.project_root)
            parts = list(rel_path.parts)
            if parts[-1] == '__init__.py':
                parts = parts[:-1]
            else:
                parts[-1] = parts[-1].replace('.py', '')
            return '.'.join(parts)
        except ValueError:
            return path.stem
    
    def _module_to_file(self, module_name: str) -> str:
        """Convert module name to file path."""
        parts = module_name.split('.')
        path = self.config.project_root / '/'.join(parts)
        
        if (path / '__init__.py').exists():
            return str(path / '__init__.py')
        return str(path) + '.py'
    
    def _find_module_dependents(self, module_name: str) -> List[ImpactedArtifact]:
        """Find all modules that depend on this module."""
        impacts = []
        
        dependents = self.import_graph.reverse_dependency_graph.get(module_name, [])
        
        for dependent in dependents:
            impacts.append(ImpactedArtifact(
                artifact_type='module',
                file_path=self._module_to_file(dependent),
                symbol_name=dependent,
                impact_type=ImpactType.DIRECT_DEPENDENCY,
                severity=ImpactSeverity.MEDIUM,
                reason=f"Depends on changed module {module_name}",
                distance=1
            ))
        
        return impacts
    
    def _find_symbol_dependents(self, full_symbol: str) -> List[str]:
        """Find modules that depend on a specific symbol."""
        # This requires deeper analysis - for now, return module dependents
        module_name = full_symbol.split('.')[0] if '.' in full_symbol else full_symbol
        return self.import_graph.reverse_dependency_graph.get(module_name, [])
    
    def _find_transitive_dependents(self, symbol: str,
                                     max_depth: int) -> List[Tuple[str, int]]:
        """Find transitive dependents up to max_depth."""
        visited = set()
        result = []
        
        def dfs(current: str, depth: int):
            if depth > max_depth:
                return
            
            module = current.split('.')[0] if '.' in current else current
            for dependent in self.import_graph.reverse_dependency_graph.get(module, []):
                if dependent not in visited:
                    visited.add(dependent)
                    result.append((dependent, depth))
                    dfs(dependent, depth + 1)
        
        dfs(symbol, 2)
        return result
    
    def _determine_severity(self, change: ChangeInfo,
                            dependent: str) -> ImpactSeverity:
        """Determine severity of impact."""
        if change.category == ChangeCategory.DELETION:
            return ImpactSeverity.CRITICAL
        
        if change.category == ChangeCategory.MODIFICATION:
            if change.removed_parameters:
                return ImpactSeverity.HIGH
            if change.old_return_type != change.new_return_type:
                return ImpactSeverity.HIGH
            if set(change.old_exceptions) != set(change.new_exceptions):
                return ImpactSeverity.MEDIUM
            return ImpactSeverity.MEDIUM
        
        if change.category == ChangeCategory.ADDITION:
            return ImpactSeverity.LOW
        
        return ImpactSeverity.MEDIUM
    
    def _downgrade_severity_for_distance(self, severity: ImpactSeverity,
                                          distance: int) -> ImpactSeverity:
        """Downgrade severity based on distance."""
        severity_order = [
            ImpactSeverity.CRITICAL,
            ImpactSeverity.HIGH,
            ImpactSeverity.MEDIUM,
            ImpactSeverity.LOW,
            ImpactSeverity.NONE
        ]
        
        idx = severity_order.index(severity)
        downgraded_idx = min(len(severity_order) - 1, idx + distance - 1)
        return severity_order[downgraded_idx]
    
    def _determine_impact_type(self, change: ChangeInfo) -> ImpactType:
        """Determine type of impact."""
        if change.category == ChangeCategory.DELETION:
            return ImpactType.API_BREAKING
        elif change.removed_parameters:
            return ImpactType.SIGNATURE_CHANGE
        elif change.old_return_type != change.new_return_type:
            return ImpactType.TYPE_CHANGE
        elif set(change.old_exceptions) != set(change.new_exceptions):
            return ImpactType.EXCEPTION_CHANGE
        elif change.category == ChangeCategory.ADDITION:
            return ImpactType.API_ADDITION
        return ImpactType.BEHAVIOR_CHANGE
    
    def _generate_impact_reason(self, change: ChangeInfo, dependent: str) -> str:
        """Generate human-readable impact reason."""
        if change.category == ChangeCategory.DELETION:
            return f"Symbol '{change.symbol_name}' was deleted"
        elif change.removed_parameters:
            return f"Parameters removed: {', '.join(change.removed_parameters)}"
        elif change.added_parameters:
            return f"New required parameters: {', '.join(change.added_parameters)}"
        elif change.old_return_type != change.new_return_type:
            return f"Return type changed from {change.old_return_type} to {change.new_return_type}"
        else:
            return f"Symbol '{change.symbol_name}' was modified"
    
    def _get_dependency_chain(self, source: str, target: str) -> List[str]:
        """Get dependency chain from source to target."""
        # Simplified - would use BFS in real implementation
        return [source, target]
    
    def _detect_breaking_change(self, change: ChangeInfo,
                                 impacts: List[ImpactedArtifact]) -> Optional[BreakingChange]:
        """Detect if change is breaking."""
        breaking_impacts = [i for i in impacts if i.severity in (ImpactSeverity.CRITICAL, ImpactSeverity.HIGH)]
        
        if not breaking_impacts:
            return None
        
        is_breaking = (
            change.category == ChangeCategory.DELETION or
            bool(change.removed_parameters) or
            change.old_return_type != change.new_return_type
        )
        
        if not is_breaking:
            return None
        
        severity = ImpactSeverity.CRITICAL if change.category == ChangeCategory.DELETION else ImpactSeverity.HIGH
        
        breaking = BreakingChange(
            change=change,
            impacted_artifacts=breaking_impacts,
            severity=severity
        )
        
        if self.config.generate_migration_guide:
            breaking.migration_guide = self._generate_migration_guide(change)
            breaking.deprecation_message = self._generate_deprecation_message(change)
        
        return breaking
    
    def _generate_migration_guide(self, change: ChangeInfo) -> str:
        """Generate migration guide for breaking change."""
        if change.category == ChangeCategory.DELETION:
            return f"The symbol '{change.symbol_name}' has been removed. Please use an alternative or contact the maintainers."
        elif change.removed_parameters:
            return f"The parameters {', '.join(change.removed_parameters)} have been removed. Update your function calls to remove these arguments."
        elif change.old_return_type != change.new_return_type:
            return f"The return type has changed from {change.old_return_type} to {change.new_return_type}. Update your code to handle the new return type."
        else:
            return f"The behavior of '{change.symbol_name}' has changed. Please review the updated documentation."
    
    def _generate_deprecation_message(self, change: ChangeInfo) -> str:
        """Generate deprecation message."""
        return f"'{change.symbol_name}' is deprecated and will be removed in a future version."
    
    def _deduplicate_impacts(self, impacts: List[ImpactedArtifact]) -> List[ImpactedArtifact]:
        """Deduplicate impacts keeping the most severe."""
        impact_map = {}
        
        for impact in impacts:
            key = (impact.file_path, impact.symbol_name)
            if key not in impact_map:
                impact_map[key] = impact
            else:
                # Keep the more severe impact
                severity_order = [ImpactSeverity.CRITICAL, ImpactSeverity.HIGH, 
                                  ImpactSeverity.MEDIUM, ImpactSeverity.LOW, ImpactSeverity.NONE]
                if severity_order.index(impact.severity) < severity_order.index(impact_map[key].severity):
                    impact_map[key] = impact
        
        return list(impact_map.values())
    
    def _find_impacted_tests(self, module_impacts: List[ImpactedArtifact]) -> List[ImpactedArtifact]:
        """Find tests impacted by module changes."""
        test_impacts = []
        
        for impact in module_impacts:
            module_file = Path(impact.file_path)
            test_file = self._find_corresponding_test(module_file)
            
            if test_file and test_file.exists():
                test_impacts.append(ImpactedArtifact(
                    artifact_type='test',
                    file_path=str(test_file),
                    impact_type=ImpactType.TEST_FAILURE,
                    severity=self._downgrade_severity_for_distance(impact.severity, 1),
                    reason=f"Tests for {module_file.stem} may fail",
                    dependency_chain=impact.dependency_chain
                ))
        
        return test_impacts
    
    def _find_corresponding_test(self, module_file: Path) -> Optional[Path]:
        """Find corresponding test file."""
        # Common test patterns
        test_patterns = [
            module_file.parent / "tests" / f"test_{module_file.stem}.py",
            module_file.parent / f"test_{module_file.stem}.py",
            self.config.project_root / "tests" / f"test_{module_file.stem}.py",
        ]
        
        for pattern in test_patterns:
            if pattern.exists():
                return pattern
        
        return None
    
    def _find_impacted_docs(self, module_impacts: List[ImpactedArtifact]) -> List[ImpactedArtifact]:
        """Find documentation impacted by module changes."""
        doc_impacts = []
        
        for impact in module_impacts:
            module_file = Path(impact.file_path)
            doc_file = self._find_corresponding_doc(module_file)
            
            if doc_file:
                doc_impacts.append(ImpactedArtifact(
                    artifact_type='doc',
                    file_path=str(doc_file),
                    impact_type=ImpactType.DOC_OUTDATED,
                    severity=ImpactSeverity.LOW,
                    reason=f"Documentation for {module_file.stem} may be outdated",
                    suggested_action=f"Update {doc_file.name}"
                ))
        
        return doc_impacts
    
    def _find_corresponding_doc(self, module_file: Path) -> Optional[Path]:
        """Find corresponding documentation file."""
        doc_patterns = [
            self.config.project_root / "docs" / f"{module_file.stem}.md",
            self.config.project_root / "docs" / "api" / f"{module_file.stem}.md",
            self.config.project_root / "README.md",
        ]
        
        for pattern in doc_patterns:
            if pattern.exists():
                return pattern
        
        return None
    
    def _collect_affected_files(self, result: ImpactAnalysisResult) -> List[str]:
        """Collect all affected files."""
        files = set()
        
        for change in result.changes:
            files.add(change.file_path)
        
        for impact in result.impacted_modules:
            files.add(impact.file_path)
        
        for impact in result.impacted_tests:
            files.add(impact.file_path)
        
        for impact in result.impacted_docs:
            files.add(impact.file_path)
        
        return list(files)
    
    def _estimate_total_hours(self, result: ImpactAnalysisResult) -> float:
        """Estimate total hours to address impact."""
        hours = 0.0
        
        # Base hours per severity
        severity_hours = {
            ImpactSeverity.CRITICAL: 4.0,
            ImpactSeverity.HIGH: 2.0,
            ImpactSeverity.MEDIUM: 1.0,
            ImpactSeverity.LOW: 0.5,
            ImpactSeverity.NONE: 0.0
        }
        
        for impact in result.impacted_modules:
            hours += severity_hours.get(impact.severity, 1.0)
        
        for impact in result.impacted_tests:
            hours += 0.5
        
        for impact in result.impacted_docs:
            hours += 0.25
        
        for breaking in result.breaking_changes:
            hours += 2.0  # Extra for migration work
        
        return hours
    
    def _calculate_risk_score(self, result: ImpactAnalysisResult) -> float:
        """Calculate overall risk score (0.0 to 1.0)."""
        if not result.impacted_modules:
            return 0.0
        
        severity_weights = {
            ImpactSeverity.CRITICAL: 10,
            ImpactSeverity.HIGH: 5,
            ImpactSeverity.MEDIUM: 2,
            ImpactSeverity.LOW: 1,
            ImpactSeverity.NONE: 0
        }
        
        total_weight = 0
        max_weight = 0
        
        for impact in result.impacted_modules:
            weight = severity_weights.get(impact.severity, 1)
            total_weight += weight
            max_weight += 10  # Maximum possible weight
        
        # Adjust for number of impacted modules
        module_factor = min(1.0, len(result.impacted_modules) / 20)
        
        # Adjust for breaking changes
        breaking_factor = min(1.0, len(result.breaking_changes) / 5)
        
        base_score = total_weight / max_weight if max_weight > 0 else 0
        risk_score = (base_score * 0.5) + (module_factor * 0.3) + (breaking_factor * 0.2)
        
        return min(1.0, risk_score)


# ============================================================
# MAIN IMPACT ANALYZER
# ============================================================

class ImpactAnalyzer:
    """
    Analyzes the impact of code changes across the entire project.
    
    Features:
    - Detects changes between code versions
    - Calculates direct and transitive impact
    - Identifies breaking changes
    - Finds impacted tests and documentation
    - Estimates fix hours and risk score
    - Generates migration guides
    - Integrates with git for diff-based analysis
    """
    
    def __init__(self, config: ImpactAnalyzerConfig):
        self.config = config
        self.change_detector = ChangeDetector(config)
        self.impact_calculator: Optional[ImpactCalculator] = None
        
        self.state = StateManager(config.project_root / ".ai_state" / "impact_analyzer.json")
        
        logger.info(f"ImpactAnalyzer initialized for {config.project_root}")
    
    def analyze(self,
                original_code: Optional[str] = None,
                refined_code: Optional[str] = None,
                file_path: Optional[Path] = None) -> ImpactAnalysisResult:
        """
        Analyze impact of changes.
        
        Args:
            original_code: Original code (if None, uses git)
            refined_code: Refined code (if None, uses git)
            file_path: Path to the changed file
        """
        logger.info("Starting impact analysis...")
        
        # Initialize impact calculator
        if not self.impact_calculator:
            self.impact_calculator = ImpactCalculator(self.config)
        
        # Detect changes
        changes = self.change_detector.detect_changes(original_code, refined_code, file_path)
        
        if not changes:
            logger.info("No changes detected")
            return ImpactAnalysisResult()
        
        logger.info(f"Detected {len(changes)} changes")
        
        # Calculate impact
        result = self.impact_calculator.calculate_impact(changes)
        
        # Filter by severity threshold
        result.impacted_modules = [
            i for i in result.impacted_modules
            if self._meets_severity_threshold(i.severity)
        ]
        
        # Save analysis
        self._save_analysis(result)
        
        logger.info(f"Impact analysis complete: {len(result.impacted_modules)} modules, "
                   f"{len(result.impacted_tests)} tests, {len(result.breaking_changes)} breaking changes, "
                   f"risk score: {result.risk_score:.2f}")
        
        return result
    
    def analyze_git_diff(self, compare_with: str = 'HEAD~1') -> ImpactAnalysisResult:
        """Analyze impact of git changes."""
        self.config.compare_with = compare_with
        self.config.use_git_diff = True
        
        return self.analyze()
    
    def analyze_refinement(self, original: str, refined: str,
                           file_path: Path) -> ImpactAnalysisResult:
        """Analyze impact of a refinement operation."""
        return self.analyze(original, refined, file_path)
    
    def _meets_severity_threshold(self, severity: ImpactSeverity) -> bool:
        """Check if severity meets threshold."""
        severity_order = [
            ImpactSeverity.CRITICAL,
            ImpactSeverity.HIGH,
            ImpactSeverity.MEDIUM,
            ImpactSeverity.LOW,
            ImpactSeverity.NONE
        ]
        
        return severity_order.index(severity) <= severity_order.index(self.config.severity_threshold)
    
    def _save_analysis(self, result: ImpactAnalysisResult):
        """Save analysis result to state."""
        analyses = self.state.get('analyses', [])
        
        analyses.append({
            'timestamp': result.analyzed_at.isoformat(),
            'changes_count': len(result.changes),
            'impacted_modules': len(result.impacted_modules),
            'impacted_tests': len(result.impacted_tests),
            'breaking_changes': len(result.breaking_changes),
            'risk_score': result.risk_score,
            'estimated_hours': result.estimated_total_impact_hours
        })
        
        if len(analyses) > 50:
            analyses = analyses[-50:]
        
        self.state.set('analyses', analyses)
        self.state.save()
    
    def generate_report(self, result: ImpactAnalysisResult,
                        format: str = 'markdown') -> str:
        """Generate impact analysis report."""
        if format == 'json':
            return self._generate_json_report(result)
        else:
            return self._generate_markdown_report(result)
    
    def _generate_markdown_report(self, result: ImpactAnalysisResult) -> str:
        """Generate markdown report."""
        lines = [
            "# Impact Analysis Report",
            "",
            f"**Analyzed:** {result.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Risk Score:** {result.risk_score:.2%}",
            f"**Estimated Fix Hours:** {result.estimated_total_impact_hours:.1f}",
            "",
            "## Summary",
            "",
            f"- **Changes Detected:** {len(result.changes)}",
            f"- **Impacted Modules:** {len(result.impacted_modules)}",
            f"- **Impacted Tests:** {len(result.impacted_tests)}",
            f"- **Impacted Docs:** {len(result.impacted_docs)}",
            f"- **Breaking Changes:** {len(result.breaking_changes)}",
            f"- **Total Affected Files:** {len(result.affected_files)}",
            ""
        ]
        
        if result.changes:
            lines.extend([
                "## Changes",
                "",
                "| File | Symbol | Category |",
                "|------|--------|----------|",
            ])
            
            for change in result.changes:
                lines.append(f"| {change.file_path} | {change.symbol_name or 'N/A'} | {change.category.value} |")
            
            lines.append("")
        
        if result.breaking_changes:
            lines.extend([
                "## ⚠️ Breaking Changes",
                "",
            ])
            
            for i, breaking in enumerate(result.breaking_changes, 1):
                lines.extend([
                    f"### {i}. {breaking.change.symbol_name}",
                    f"**Severity:** {breaking.severity.value}",
                    f"**File:** {breaking.change.file_path}",
                    "",
                ])
                
                if breaking.migration_guide:
                    lines.extend([
                        "**Migration Guide:**",
                        breaking.migration_guide,
                        "",
                    ])
                
                if breaking.impacted_artifacts:
                    lines.append("**Impacted Artifacts:**")
                    for impact in breaking.impacted_artifacts[:5]:
                        lines.append(f"- {impact.file_path}")
                    lines.append("")
        
        if result.impacted_modules:
            lines.extend([
                "## Impacted Modules",
                "",
                "| Module | Severity | Impact Type | Reason |",
                "|--------|----------|-------------|--------|",
            ])
            
            for impact in result.impacted_modules[:20]:
                lines.append(f"| {impact.file_path} | {impact.severity.value} | {impact.impact_type.value} | {impact.reason[:50]} |")
            
            if len(result.impacted_modules) > 20:
                lines.append(f"| ... | ... | ... | *and {len(result.impacted_modules) - 20} more* |")
            
            lines.append("")
        
        if result.impacted_tests:
            lines.extend([
                "## Impacted Tests",
                "",
            ])
            
            for impact in result.impacted_tests[:10]:
                lines.append(f"- {impact.file_path}")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_json_report(self, result: ImpactAnalysisResult) -> str:
        """Generate JSON report."""
        data = {
            'analyzed_at': result.analyzed_at.isoformat(),
            'risk_score': result.risk_score,
            'estimated_hours': result.estimated_total_impact_hours,
            'changes': [
                {
                    'category': c.category.value,
                    'file': c.file_path,
                    'symbol': c.symbol_name,
                    'old_signature': c.old_signature,
                    'new_signature': c.new_signature
                }
                for c in result.changes
            ],
            'impacted_modules': [
                {
                    'file': i.file_path,
                    'severity': i.severity.value,
                    'impact_type': i.impact_type.value,
                    'reason': i.reason
                }
                for i in result.impacted_modules
            ],
            'impacted_tests': [
                {'file': i.file_path} for i in result.impacted_tests
            ],
            'impacted_docs': [
                {'file': i.file_path} for i in result.impacted_docs
            ],
            'breaking_changes': [
                {
                    'symbol': b.change.symbol_name,
                    'severity': b.severity.value,
                    'migration_guide': b.migration_guide,
                    'impacted_count': len(b.impacted_artifacts)
                }
                for b in result.breaking_changes
            ],
            'affected_files': result.affected_files
        }
        
        return json.dumps(data, indent=2)
    
    def get_affected_tests(self, result: ImpactAnalysisResult) -> List[str]:
        """Get list of test files that need to be run."""
        return [i.file_path for i in result.impacted_tests]
    
    def should_block_merge(self, result: ImpactAnalysisResult,
                           risk_threshold: float = 0.5) -> bool:
        """Determine if changes should block merge based on risk."""
        if result.risk_score >= risk_threshold:
            return True
        
        if result.breaking_changes:
            return True
        
        return False
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("ImpactAnalyzer closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for impact analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze impact of code changes")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    parser.add_argument("--file", type=Path, help="Specific file to analyze")
    parser.add_argument("--original", type=Path, help="Original file")
    parser.add_argument("--refined", type=Path, help="Refined file")
    parser.add_argument("--git-diff", action="store_true", help="Analyze git diff")
    parser.add_argument("--compare-with", default="HEAD~1", help="Git comparison point")
    parser.add_argument("--output", "-o", type=Path, help="Output report file")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown",
                       help="Report format")
    parser.add_argument("--threshold", choices=[s.value for s in ImpactSeverity],
                       default=ImpactSeverity.LOW.value, help="Severity threshold")
    parser.add_argument("--no-transitive", action="store_true",
                       help="Disable transitive dependency analysis")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    config = ImpactAnalyzerConfig(
        project_root=args.project_root,
        include_transitive_deps=not args.no_transitive,
        severity_threshold=ImpactSeverity(args.threshold)
    )
    
    analyzer = ImpactAnalyzer(config)
    
    if args.git_diff:
        result = analyzer.analyze_git_diff(args.compare_with)
    elif args.original and args.refined:
        original_code = args.original.read_text()
        refined_code = args.refined.read_text()
        result = analyzer.analyze(original_code, refined_code, args.refined)
    elif args.file:
        # Assume file was modified
        if args.file.exists():
            original_code = ""  # Would get from git
            refined_code = args.file.read_text()
            result = analyzer.analyze(original_code, refined_code, args.file)
    else:
        result = analyzer.analyze_git_diff()
    
    report = analyzer.generate_report(result, args.format if not args.json else 'json')
    
    if args.output:
        args.output.write_text(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)
    
    # Summary
    print(f"\n--- Summary ---")
    print(f"Risk Score: {result.risk_score:.2%}")
    print(f"Breaking Changes: {len(result.breaking_changes)}")
    print(f"Impacted Modules: {len(result.impacted_modules)}")
    print(f"Impacted Tests: {len(result.impacted_tests)}")
    print(f"Estimated Fix Hours: {result.estimated_total_impact_hours:.1f}")
    
    if analyzer.should_block_merge(result):
        print("\n⚠️ WARNING: Changes may block merge due to high risk!")
    
    analyzer.close()


if __name__ == "__main__":
    main()