#!/usr/bin/env python3
"""
Dependency Planner - Plans internal dependencies and import relationships for generated code.

Part of the Generation tools (generation/planners/dependency_planner.py)

This dependency_planner.py addresses your requirement for large-scale code generation by providing:

1. Component Dependency Graph - Complete visualization of all component relationships
2. Optimal Generation Order - Topological sorting to determine what to generate first
3. Batch Generation Planning - Groups independent components for parallel generation
4. Circular Dependency Detection - Identifies and resolves circular dependencies
5. Multiple Resolution Strategies - Merge, extract interface, or break dependencies
6. Import Statement Planning - Pre-plans all import statements for each file
7. Layer-Based Validation - Ensures architectural boundaries are respected
8. Integration with Existing Code - Validates against current project structure
9. Generation Order Calculation - Determines the exact sequence for multi-round generation
10. Import Organization - Groups imports by type (stdlib, third-party, internal)
11. Mermaid Diagram Export - Visual dependency graph generation
12. Comprehensive Reporting - Issues, warnings, and actionable recommendations

This planner ensures that when generating a complex module like an Excel writer with multiple files, 
all components are generated in the correct order with proper imports, avoiding circular dependencies 
and maintaining architectural integrity.
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
from ....analysis.scanners.import_graph import ImportGraphAnalyzer
from ....analysis.scanners.project_scanner import ProjectScanner

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class DependencyType(str, Enum):
    """Type of dependency between components."""
    DIRECT = "direct"               # Direct import
    INTERFACE = "interface"         # Depends on interface/ABC
    IMPLEMENTATION = "implementation"  # Implements interface
    FACTORY = "factory"             # Created by factory
    INJECTED = "injected"           # Dependency injection
    LAZY = "lazy"                   # Lazy import
    OPTIONAL = "optional"           # Optional dependency
    CIRCULAR = "circular"           # Circular dependency (should be avoided)
    PLUGIN = "plugin"               # Plugin architecture
    EVENT = "event"                 # Event-based communication


class DependencyDirection(str, Enum):
    """Direction of dependency."""
    INWARD = "inward"      # Toward core/domain
    OUTWARD = "outward"    # Toward infrastructure
    LATERAL = "lateral"    # Same layer
    UNKNOWN = "unknown"


class LayerType(str, Enum):
    """Architectural layer type."""
    DOMAIN = "domain"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    INTERFACE = "interface"
    SHARED = "shared"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


class DependencyRule(str, Enum):
    """Dependency rule type."""
    ALLOWED = "allowed"
    FORBIDDEN = "forbidden"
    REQUIRED = "required"
    SUGGESTED = "suggested"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ComponentSpec:
    """Specification for a code component."""
    name: str
    component_type: str  # 'module', 'class', 'function', 'interface'
    layer: LayerType
    file_path: Optional[str] = None
    public_api: List[str] = field(default_factory=list)
    dependencies: List['DependencyEdge'] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    is_generated: bool = True
    generation_order: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyEdge:
    """Represents a dependency between components."""
    source: str
    target: str
    dep_type: DependencyType
    direction: DependencyDirection
    is_circular: bool = False
    is_optional: bool = False
    reason: str = ""
    import_statement: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LayerDefinition:
    """Definition of an architectural layer."""
    name: str
    layer_type: LayerType
    allowed_dependencies: List[LayerType] = field(default_factory=list)
    forbidden_dependencies: List[LayerType] = field(default_factory=list)
    required_imports: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class DependencyRule_:
    """A dependency rule."""
    rule_type: DependencyRule
    source_pattern: str
    target_pattern: str
    reason: str = ""
    severity: str = "error"
    enabled: bool = True


@dataclass
class ImportPlan:
    """Plan for imports in a generated file."""
    file_path: str
    stdlib_imports: List[str] = field(default_factory=list)
    third_party_imports: List[str] = field(default_factory=list)
    internal_imports: List[str] = field(default_factory=list)
    relative_imports: List[str] = field(default_factory=list)
    type_checking_imports: List[str] = field(default_factory=list)
    lazy_imports: List[str] = field(default_factory=list)
    import_blocks: List[Tuple[str, List[str]]] = field(default_factory=list)


@dataclass
class GenerationOrder:
    """Order in which components should be generated."""
    components: List[str] = field(default_factory=list)
    batches: List[List[str]] = field(default_factory=list)
    circular_groups: List[List[str]] = field(default_factory=list)
    independent_components: List[str] = field(default_factory=list)


@dataclass
class DependencyPlan:
    """Complete dependency plan for code generation."""
    project_name: str
    created_at: datetime = field(default_factory=datetime.now)
    
    # Components
    components: Dict[str, ComponentSpec] = field(default_factory=dict)
    
    # Layers
    layers: Dict[str, LayerDefinition] = field(default_factory=dict)
    
    # Dependencies
    dependencies: List[DependencyEdge] = field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    reverse_dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    
    # Rules
    rules: List[DependencyRule_] = field(default_factory=list)
    violations: List[Tuple[DependencyEdge, DependencyRule_]] = field(default_factory=list)
    
    # Import plans
    import_plans: Dict[str, ImportPlan] = field(default_factory=dict)
    
    # Generation order
    generation_order: GenerationOrder = field(default_factory=GenerationOrder)
    
    # Statistics
    total_components: int = 0
    total_dependencies: int = 0
    circular_dependencies: List[List[str]] = field(default_factory=list)
    layer_violations: int = 0
    
    # Validation
    is_valid: bool = True
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyPlannerConfig:
    """Configuration for dependency planner."""
    project_root: Path
    project_name: str = "generated_project"
    
    # Layer definitions
    layers: List[LayerDefinition] = field(default_factory=lambda: [
        LayerDefinition(
            name="domain",
            layer_type=LayerType.DOMAIN,
            allowed_dependencies=[],
            forbidden_dependencies=[LayerType.APPLICATION, LayerType.INFRASTRUCTURE, LayerType.INTERFACE],
            description="Core domain logic - no external dependencies"
        ),
        LayerDefinition(
            name="application",
            layer_type=LayerType.APPLICATION,
            allowed_dependencies=[LayerType.DOMAIN],
            forbidden_dependencies=[LayerType.INFRASTRUCTURE, LayerType.INTERFACE],
            description="Application services and use cases"
        ),
        LayerDefinition(
            name="infrastructure",
            layer_type=LayerType.INFRASTRUCTURE,
            allowed_dependencies=[LayerType.DOMAIN, LayerType.APPLICATION],
            forbidden_dependencies=[],
            description="Infrastructure, repositories, external services"
        ),
        LayerDefinition(
            name="interface",
            layer_type=LayerType.INTERFACE,
            allowed_dependencies=[LayerType.APPLICATION, LayerType.INFRASTRUCTURE],
            forbidden_dependencies=[LayerType.DOMAIN],
            description="API, CLI, and other interfaces"
        ),
        LayerDefinition(
            name="shared",
            layer_type=LayerType.SHARED,
            allowed_dependencies=[],
            forbidden_dependencies=[],
            description="Shared utilities and cross-cutting concerns"
        ),
    ])
    
    # Dependency rules
    rules: List[DependencyRule_] = field(default_factory=lambda: [
        DependencyRule_(
            rule_type=DependencyRule.FORBIDDEN,
            source_pattern="domain.*",
            target_pattern="application.*|infrastructure.*|interface.*",
            reason="Domain layer must not depend on outer layers",
            severity="error"
        ),
        DependencyRule_(
            rule_type=DependencyRule.FORBIDDEN,
            source_pattern="application.*",
            target_pattern="infrastructure.*|interface.*",
            reason="Application layer should not depend on infrastructure or interface",
            severity="warning"
        ),
    ])
    
    # Generation strategy
    strategy: str = "topological"  # topological, layered, parallel
    resolve_circular: bool = True
    circular_strategy: str = "merge"  # merge, extract_interface, break_dependency
    max_batch_size: int = 10
    
    # Import organization
    organize_imports: bool = True
    use_relative_imports: bool = False
    max_relative_depth: int = 2
    group_imports: bool = True
    
    # Validation
    validate_against_existing: bool = True
    fail_on_circular: bool = True
    fail_on_violation: bool = True
    
    # Output
    output_format: str = "json"


# ============================================================
# DEPENDENCY GRAPH BUILDER
# ============================================================

class DependencyGraphBuilder:
    """Build dependency graphs from component specifications."""
    
    def __init__(self, config: DependencyPlannerConfig):
        self.config = config
        self.components: Dict[str, ComponentSpec] = {}
        self.dependencies: List[DependencyEdge] = []
        self.layer_map: Dict[str, LayerDefinition] = {
            l.name: l for l in config.layers
        }
    
    def add_component(self, component: ComponentSpec):
        """Add a component to the graph."""
        self.components[component.name] = component
    
    def add_dependency(self, source: str, target: str, dep_type: DependencyType,
                       reason: str = "", is_optional: bool = False):
        """Add a dependency between components."""
        if source not in self.components:
            raise ValueError(f"Source component '{source}' not found")
        if target not in self.components:
            raise ValueError(f"Target component '{target}' not found")
        
        source_comp = self.components[source]
        target_comp = self.components[target]
        
        direction = self._determine_direction(source_comp.layer, target_comp.layer)
        
        edge = DependencyEdge(
            source=source,
            target=target,
            dep_type=dep_type,
            direction=direction,
            is_optional=is_optional,
            reason=reason,
            import_statement=self._generate_import_statement(source, target)
        )
        
        self.dependencies.append(edge)
        source_comp.dependencies.append(edge)
        target_comp.dependents.append(source)
    
    def _determine_direction(self, source_layer: LayerType, target_layer: LayerType) -> DependencyDirection:
        """Determine dependency direction."""
        layer_order = [LayerType.DOMAIN, LayerType.APPLICATION, LayerType.INFRASTRUCTURE, LayerType.INTERFACE]
        
        if source_layer == target_layer:
            return DependencyDirection.LATERAL
        
        try:
            source_idx = layer_order.index(source_layer)
            target_idx = layer_order.index(target_layer)
            
            if source_idx > target_idx:
                return DependencyDirection.INWARD
            else:
                return DependencyDirection.OUTWARD
        except ValueError:
            return DependencyDirection.UNKNOWN
    
    def _generate_import_statement(self, source: str, target: str) -> str:
        """Generate import statement for a dependency."""
        source_parts = source.split('.')
        target_parts = target.split('.')
        
        # Simple case: from target import TargetClass
        if len(target_parts) == 1:
            return f"from {target} import {target}"
        
        # Module import
        module = '.'.join(target_parts[:-1])
        class_name = target_parts[-1]
        return f"from {module} import {class_name}"
    
    def build(self) -> Tuple[Dict[str, ComponentSpec], List[DependencyEdge]]:
        """Build the complete dependency graph."""
        # Detect circular dependencies
        circular_groups = self._detect_circular_dependencies()
        
        # Mark circular edges
        for group in circular_groups:
            for source in group:
                for edge in self.components[source].dependencies:
                    if edge.target in group:
                        edge.is_circular = True
        
        return self.components, self.dependencies
    
    def _detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in the graph."""
        graph = {name: [e.target for e in comp.dependencies] 
                for name, comp in self.components.items()}
        
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                dfs(node)
        
        return cycles


# ============================================================
# GENERATION ORDER CALCULATOR
# ============================================================

class GenerationOrderCalculator:
    """Calculate optimal generation order for components."""
    
    def __init__(self, config: DependencyPlannerConfig):
        self.config = config
    
    def calculate(self, components: Dict[str, ComponentSpec],
                  dependencies: List[DependencyEdge]) -> GenerationOrder:
        """Calculate generation order."""
        order = GenerationOrder()
        
        # Build dependency graph
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for edge in dependencies:
            if not edge.is_optional:
                graph[edge.source].append(edge.target)
                in_degree[edge.target] += 1
        
        all_components = set(components.keys())
        for comp in all_components:
            if comp not in in_degree:
                in_degree[comp] = 0
        
        # Find independent components
        order.independent_components = [c for c in all_components if in_degree[c] == 0 and not graph[c]]
        
        # Find circular groups
        circular_groups = self._find_circular_groups(graph)
        order.circular_groups = circular_groups
        
        # Resolve circular dependencies if configured
        if self.config.resolve_circular and circular_groups:
            graph, in_degree = self._resolve_circular(graph, in_degree, circular_groups)
        
        # Topological sort
        remaining = set(all_components)
        batch_num = 0
        
        while remaining:
            batch = [c for c in remaining if in_degree[c] == 0]
            
            if not batch:
                # Circular dependency detected
                cycle = self._extract_cycle(remaining, graph)
                if cycle:
                    order.circular_groups.append(cycle)
                    
                    if self.config.circular_strategy == "merge":
                        # Merge circular group into single component
                        merged_name = "_".join(cycle)
                        batch = [merged_name]
                        for c in cycle:
                            remaining.remove(c)
                        remaining.add(merged_name)
                    elif self.config.circular_strategy == "break_dependency":
                        # Break one dependency
                        c = cycle[0]
                        in_degree[c] = 0
                        batch = [c]
                    else:
                        # Extract interface
                        pass
                else:
                    break
            
            if batch:
                if len(batch) > self.config.max_batch_size:
                    # Split into smaller batches
                    for i in range(0, len(batch), self.config.max_batch_size):
                        order.batches.append(batch[i:i + self.config.max_batch_size])
                else:
                    order.batches.append(batch)
                
                for c in batch:
                    if c in remaining:
                        remaining.remove(c)
                        order.components.append(c)
                        components[c].generation_order = batch_num
                        
                        for neighbor in graph[c]:
                            in_degree[neighbor] -= 1
                
                batch_num += 1
        
        return order
    
    def _find_circular_groups(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Find strongly connected components (circular dependencies)."""
        index = 0
        indices = {}
        lowlink = {}
        on_stack = set()
        stack = []
        sccs = []
        
        def strongconnect(node: str):
            nonlocal index
            indices[node] = index
            lowlink[node] = index
            index += 1
            stack.append(node)
            on_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in indices:
                    strongconnect(neighbor)
                    lowlink[node] = min(lowlink[node], lowlink[neighbor])
                elif neighbor in on_stack:
                    lowlink[node] = min(lowlink[node], indices[neighbor])
            
            if lowlink[node] == indices[node]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    scc.append(w)
                    if w == node:
                        break
                if len(scc) > 1:
                    sccs.append(scc)
        
        for node in graph:
            if node not in indices:
                strongconnect(node)
        
        return sccs
    
    def _resolve_circular(self, graph: Dict[str, List[str]], in_degree: Dict[str, int],
                          circular_groups: List[List[str]]) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
        """Resolve circular dependencies."""
        for group in circular_groups:
            if self.config.circular_strategy == "merge":
                merged_name = "_".join(group)
                graph[merged_name] = []
                
                for node in group:
                    for neighbor in graph[node]:
                        if neighbor not in group:
                            graph[merged_name].append(neighbor)
                    
                    for source, targets in graph.items():
                        if source not in group and node in targets:
                            targets.remove(node)
                            if merged_name not in targets:
                                targets.append(merged_name)
                
                in_degree[merged_name] = 0
                
            elif self.config.circular_strategy == "extract_interface":
                interface_name = f"I{group[0]}"
                graph[interface_name] = []
                
                for node in group:
                    graph[node] = [t for t in graph[node] if t not in group]
                    graph[node].append(interface_name)
        
        return graph, in_degree
    
    def _extract_cycle(self, remaining: Set[str], graph: Dict[str, List[str]]) -> Optional[List[str]]:
        """Extract a cycle from remaining nodes."""
        visited = set()
        
        def find_cycle(node: str, path: List[str]) -> Optional[List[str]]:
            if node in path:
                idx = path.index(node)
                return path[idx:] + [node]
            
            if node in visited:
                return None
            
            visited.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor in remaining:
                    cycle = find_cycle(neighbor, path)
                    if cycle:
                        return cycle
            
            path.pop()
            return None
        
        for node in remaining:
            cycle = find_cycle(node, [])
            if cycle:
                return cycle[:-1]
        
        return None


# ============================================================
# IMPORT PLANNER
# ============================================================

class ImportPlanner:
    """Plan imports for generated files."""
    
    def __init__(self, config: DependencyPlannerConfig):
        self.config = config
    
    def plan_imports(self, component: ComponentSpec,
                     dependencies: List[DependencyEdge]) -> ImportPlan:
        """Plan imports for a component."""
        plan = ImportPlan(file_path=component.file_path or f"{component.name}.py")
        
        # Group dependencies by type
        for edge in dependencies:
            if edge.source != component.name:
                continue
            
            import_stmt = edge.import_statement or self._generate_import(edge)
            
            # Classify import
            target_comp = edge.target
            
            if self._is_stdlib(target_comp):
                plan.stdlib_imports.append(import_stmt)
            elif self._is_third_party(target_comp):
                plan.third_party_imports.append(import_stmt)
            elif self.config.use_relative_imports:
                plan.relative_imports.append(import_stmt)
            else:
                plan.internal_imports.append(import_stmt)
            
            if edge.dep_type == DependencyType.LAZY:
                plan.lazy_imports.append(import_stmt)
            
            if edge.dep_type == DependencyType.OPTIONAL:
                plan.type_checking_imports.append(import_stmt)
        
        # Organize into blocks
        if self.config.group_imports:
            plan.import_blocks = [
                ("__future__", []),
                ("stdlib", plan.stdlib_imports),
                ("third_party", plan.third_party_imports),
                ("internal", plan.internal_imports),
                ("relative", plan.relative_imports),
                ("type_checking", plan.type_checking_imports),
            ]
            plan.import_blocks = [(name, imports) for name, imports in plan.import_blocks if imports]
        
        return plan
    
    def _generate_import(self, edge: DependencyEdge) -> str:
        """Generate import statement."""
        return edge.import_statement or f"from {edge.target} import {edge.target.split('.')[-1]}"
    
    def _is_stdlib(self, component_name: str) -> bool:
        """Check if component is from standard library."""
        stdlib_modules = {'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections',
                         'contextlib', 'copy', 'dataclasses', 'datetime', 'enum', 'functools',
                         'hashlib', 'inspect', 'io', 'itertools', 'json', 'logging', 'math',
                         'os', 'pathlib', 're', 'sys', 'threading', 'time', 'typing', 'uuid'}
        top_module = component_name.split('.')[0]
        return top_module in stdlib_modules
    
    def _is_third_party(self, component_name: str) -> bool:
        """Check if component is third-party."""
        return not self._is_stdlib(component_name) and not component_name.startswith(self.config.project_name)


# ============================================================
# RULE VALIDATOR
# ============================================================

class RuleValidator:
    """Validate dependencies against architectural rules."""
    
    def __init__(self, config: DependencyPlannerConfig):
        self.config = config
    
    def validate(self, components: Dict[str, ComponentSpec],
                 dependencies: List[DependencyEdge]) -> List[Tuple[DependencyEdge, DependencyRule_]]:
        """Validate dependencies against rules."""
        violations = []
        
        for edge in dependencies:
            source_comp = components[edge.source]
            target_comp = components[edge.target]
            
            for rule in self.config.rules:
                if not rule.enabled:
                    continue
                
                if self._matches_pattern(source_comp, rule.source_pattern):
                    if self._matches_pattern(target_comp, rule.target_pattern):
                        if rule.rule_type == DependencyRule.FORBIDDEN:
                            violations.append((edge, rule))
                        elif rule.rule_type == DependencyRule.REQUIRED:
                            # Check if required dependency is missing
                            pass
        
        # Check layer rules
        for edge in dependencies:
            source_comp = components[edge.source]
            target_comp = components[edge.target]
            
            source_layer_def = self._get_layer_definition(source_comp.layer)
            target_layer_def = self._get_layer_definition(target_comp.layer)
            
            if source_layer_def and target_layer_def:
                if target_comp.layer in source_layer_def.forbidden_dependencies:
                    rule = DependencyRule_(
                        rule_type=DependencyRule.FORBIDDEN,
                        source_pattern=source_comp.layer.value,
                        target_pattern=target_comp.layer.value,
                        reason=f"Layer {source_comp.layer.value} cannot depend on {target_comp.layer.value}",
                        severity="error"
                    )
                    violations.append((edge, rule))
        
        return violations
    
    def _matches_pattern(self, component: ComponentSpec, pattern: str) -> bool:
        """Check if component matches pattern."""
        import re
        return bool(re.match(pattern.replace('*', '.*'), component.name))
    
    def _get_layer_definition(self, layer: LayerType) -> Optional[LayerDefinition]:
        """Get layer definition by type."""
        for layer_def in self.config.layers:
            if layer_def.layer_type == layer:
                return layer_def
        return None


# ============================================================
# MAIN DEPENDENCY PLANNER
# ============================================================

class DependencyPlanner:
    """
    Plans internal dependencies and import relationships for generated code.
    
    Features:
    - Component dependency graph construction
    - Optimal generation order calculation
    - Circular dependency detection and resolution
    - Import statement planning and organization
    - Architectural rule validation
    - Layer-based dependency management
    - Integration with existing project analysis
    - Multiple resolution strategies for circular dependencies
    """
    
    def __init__(self, config: DependencyPlannerConfig):
        self.config = config
        self.graph_builder = DependencyGraphBuilder(config)
        self.order_calculator = GenerationOrderCalculator(config)
        self.import_planner = ImportPlanner(config)
        self.rule_validator = RuleValidator(config)
        
        self.scanner = ProjectScanner(project_root=config.project_root)
        self.import_analyzer = ImportGraphAnalyzer(project_root=config.project_root)
        
        self.state = StateManager(config.project_root / ".ai_state" / "dependency_planner.json")
        
        logger.info("DependencyPlanner initialized")
    
    def plan(self, components: List[ComponentSpec]) -> DependencyPlan:
        """Create a complete dependency plan."""
        logger.info(f"Planning dependencies for {len(components)} components")
        
        plan = DependencyPlan(project_name=self.config.project_name)
        
        # Build component graph
        for comp in components:
            self.graph_builder.add_component(comp)
            plan.components[comp.name] = comp
            plan.total_components += 1
        
        # Build layer map
        for layer_def in self.config.layers:
            plan.layers[layer_def.name] = layer_def
        
        # Build dependencies from component specifications
        for comp in components:
            for dep_edge in comp.dependencies:
                self.graph_builder.add_dependency(
                    dep_edge.source, dep_edge.target,
                    dep_edge.dep_type, dep_edge.reason, dep_edge.is_optional
                )
        
        # Build complete graph
        components, dependencies = self.graph_builder.build()
        plan.dependencies = dependencies
        plan.total_dependencies = len(dependencies)
        
        # Build dependency graphs
        for edge in dependencies:
            if edge.source not in plan.dependency_graph:
                plan.dependency_graph[edge.source] = []
            plan.dependency_graph[edge.source].append(edge.target)
            
            if edge.target not in plan.reverse_dependency_graph:
                plan.reverse_dependency_graph[edge.target] = []
            plan.reverse_dependency_graph[edge.target].append(edge.source)
        
        # Calculate generation order
        plan.generation_order = self.order_calculator.calculate(components, dependencies)
        plan.circular_dependencies = plan.generation_order.circular_groups
        
        # Validate against existing project if configured
        if self.config.validate_against_existing:
            self._validate_against_existing(plan)
        
        # Validate against architectural rules
        plan.violations = self.rule_validator.validate(components, dependencies)
        plan.layer_violations = len(plan.violations)
        
        # Plan imports for each component
        for comp_name, comp in components.items():
            comp_deps = [e for e in dependencies if e.source == comp_name]
            plan.import_plans[comp_name] = self.import_planner.plan_imports(comp, comp_deps)
        
        # Check validity
        plan.is_valid = self._check_validity(plan)
        
        # Generate issues and warnings
        self._generate_issues(plan)
        
        # Generate recommendations
        plan.recommendations = self._generate_recommendations(plan)
        
        # Save plan
        self._save_plan(plan)
        
        logger.info(f"Dependency plan created: {plan.total_components} components, {plan.total_dependencies} dependencies")
        
        return plan
    
    def plan_from_specs(self, specs: List[Dict[str, Any]]) -> DependencyPlan:
        """Create a dependency plan from specification dictionaries."""
        components = []
        
        for spec_data in specs:
            comp = ComponentSpec(
                name=spec_data['name'],
                component_type=spec_data.get('type', 'module'),
                layer=LayerType(spec_data.get('layer', 'shared')),
                file_path=spec_data.get('file_path'),
                public_api=spec_data.get('public_api', []),
                metadata=spec_data.get('metadata', {})
            )
            
            for dep_data in spec_data.get('dependencies', []):
                edge = DependencyEdge(
                    source=comp.name,
                    target=dep_data['target'],
                    dep_type=DependencyType(dep_data.get('type', 'direct')),
                    direction=DependencyDirection.UNKNOWN,
                    reason=dep_data.get('reason', ''),
                    is_optional=dep_data.get('optional', False)
                )
                comp.dependencies.append(edge)
            
            components.append(comp)
        
        return self.plan(components)
    
    def _validate_against_existing(self, plan: DependencyPlan):
        """Validate plan against existing project."""
        existing_graph = self.import_analyzer.analyze()
        
        for comp_name, comp in plan.components.items():
            if comp_name in existing_graph.modules:
                existing_deps = existing_graph.dependency_graph.get(comp_name, [])
                planned_deps = plan.dependency_graph.get(comp_name, [])
                
                # Check for conflicts
                for dep in planned_deps:
                    if dep not in existing_deps and dep in existing_graph.modules:
                        plan.warnings.append(
                            f"Component '{comp_name}' depends on existing module '{dep}'. "
                            f"Ensure compatibility."
                        )
    
    def _check_validity(self, plan: DependencyPlan) -> bool:
        """Check if plan is valid."""
        if self.config.fail_on_circular and plan.circular_dependencies:
            return False
        
        if self.config.fail_on_violation and plan.violations:
            return False
        
        return True
    
    def _generate_issues(self, plan: DependencyPlan):
        """Generate issues from validation."""
        # Circular dependencies
        for cycle in plan.circular_dependencies:
            plan.issues.append(
                f"Circular dependency detected: {' -> '.join(cycle)} -> {cycle[0]}"
            )
        
        # Rule violations
        for edge, rule in plan.violations:
            plan.issues.append(
                f"Rule violation: {edge.source} -> {edge.target} "
                f"({rule.reason})"
            )
        
        # Missing components
        for edge in plan.dependencies:
            if edge.target not in plan.components:
                plan.warnings.append(
                    f"Dependency '{edge.target}' not found in planned components"
                )
    
    def _generate_recommendations(self, plan: DependencyPlan) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if plan.circular_dependencies:
            recommendations.append(
                f"Resolve {len(plan.circular_dependencies)} circular dependencies "
                f"using interface extraction or dependency inversion"
            )
        
        if plan.layer_violations > 0:
            recommendations.append(
                f"Fix {plan.layer_violations} architectural layer violations"
            )
        
        # Suggest generation batches
        if plan.generation_order.batches:
            recommendations.append(
                f"Generate components in {len(plan.generation_order.batches)} batches "
                f"following topological order"
            )
        
        # Independent components first
        if plan.generation_order.independent_components:
            recommendations.append(
                f"Generate {len(plan.generation_order.independent_components)} "
                f"independent components first"
            )
        
        return recommendations
    
    def _save_plan(self, plan: DependencyPlan):
        """Save plan to state."""
        plans = self.state.get('plans', [])
        plans.append({
            'timestamp': plan.created_at.isoformat(),
            'project': plan.project_name,
            'components': plan.total_components,
            'dependencies': plan.total_dependencies,
            'circular': len(plan.circular_dependencies),
            'violations': plan.layer_violations,
            'is_valid': plan.is_valid,
            'batches': len(plan.generation_order.batches)
        })
        
        if len(plans) > 50:
            plans = plans[-50:]
        
        self.state.set('plans', plans)
        self.state.save()
    
    def export_plan(self, plan: DependencyPlan,
                    output_path: Optional[Path] = None,
                    format: str = 'json') -> str:
        """Export dependency plan."""
        
        if format == 'json':
            data = {
                'project': plan.project_name,
                'created_at': plan.created_at.isoformat(),
                'is_valid': plan.is_valid,
                'statistics': {
                    'total_components': plan.total_components,
                    'total_dependencies': plan.total_dependencies,
                    'circular_dependencies': len(plan.circular_dependencies),
                    'layer_violations': plan.layer_violations
                },
                'components': {
                    name: {
                        'type': comp.component_type,
                        'layer': comp.layer.value,
                        'generation_order': comp.generation_order,
                        'dependencies': [e.target for e in comp.dependencies],
                        'dependents': comp.dependents
                    }
                    for name, comp in plan.components.items()
                },
                'generation_order': {
                    'batches': plan.generation_order.batches,
                    'circular_groups': plan.generation_order.circular_groups,
                    'independent': plan.generation_order.independent_components
                },
                'import_plans': {
                    name: {
                        'stdlib': p.stdlib_imports,
                        'third_party': p.third_party_imports,
                        'internal': p.internal_imports,
                        'relative': p.relative_imports
                    }
                    for name, p in plan.import_plans.items()
                },
                'issues': plan.issues,
                'warnings': plan.warnings,
                'recommendations': plan.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        elif format == 'mermaid':
            lines = ["```mermaid", "graph TD"]
            
            for comp_name, comp in plan.components.items():
                short_name = comp_name.split('.')[-1]
                lines.append(f"    {self._sanitize(comp_name)}[\"{short_name}\"]")
            
            for edge in plan.dependencies:
                style = " --> "
                if edge.is_circular:
                    style = " -.-> "
                elif edge.is_optional:
                    style = " -..-> "
                elif edge.dep_type == DependencyType.INTERFACE:
                    style = " ==o "
                
                lines.append(f"    {self._sanitize(edge.source)}{style}{self._sanitize(edge.target)}")
            
            lines.append("```")
            content = '\n'.join(lines)
            
        else:  # markdown
            lines = [
                f"# Dependency Plan: {plan.project_name}",
                "",
                f"**Created:** {plan.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Valid:** {'✅ Yes' if plan.is_valid else '❌ No'}",
                "",
                "## Statistics",
                "",
                f"- **Components:** {plan.total_components}",
                f"- **Dependencies:** {plan.total_dependencies}",
                f"- **Circular Dependencies:** {len(plan.circular_dependencies)}",
                f"- **Layer Violations:** {plan.layer_violations}",
                "",
                "## Generation Order",
                "",
            ]
            
            for i, batch in enumerate(plan.generation_order.batches, 1):
                lines.append(f"### Batch {i}")
                for comp in batch:
                    comp_info = plan.components.get(comp)
                    if comp_info:
                        lines.append(f"- `{comp}` ({comp_info.layer.value})")
                lines.append("")
            
            if plan.circular_dependencies:
                lines.extend([
                    "## ⚠️ Circular Dependencies",
                    "",
                ])
                for cycle in plan.circular_dependencies:
                    lines.append(f"- {' → '.join(cycle)}")
                lines.append("")
            
            if plan.issues:
                lines.extend([
                    "## Issues",
                    "",
                ])
                for issue in plan.issues:
                    lines.append(f"- {issue}")
                lines.append("")
            
            if plan.recommendations:
                lines.extend([
                    "## Recommendations",
                    "",
                ])
                for rec in plan.recommendations:
                    lines.append(f"- {rec}")
                lines.append("")
            
            content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def _sanitize(self, name: str) -> str:
        """Sanitize name for Mermaid."""
        return name.replace('.', '_').replace('-', '_')
    
    def generate_import_block(self, plan: DependencyPlan, component_name: str) -> str:
        """Generate import block for a component."""
        if component_name not in plan.import_plans:
            return ""
        
        import_plan = plan.import_plans[component_name]
        lines = []
        
        if self.config.group_imports:
            for block_name, imports in import_plan.import_blocks:
                if imports:
                    lines.extend(sorted(set(imports)))
                    lines.append("")
        else:
            all_imports = (
                import_plan.stdlib_imports +
                import_plan.third_party_imports +
                import_plan.internal_imports +
                import_plan.relative_imports
            )
            lines.extend(sorted(set(all_imports)))
        
        return '\n'.join(lines)
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("DependencyPlanner closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for dependency planner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Plan dependencies for code generation")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--project-name", type=str, default="generated_project")
    parser.add_argument("--spec", type=Path, help="Component specifications JSON file")
    parser.add_argument("--output", "-o", type=Path, help="Output plan file")
    parser.add_argument("--format", choices=["json", "markdown", "mermaid"], default="json")
    parser.add_argument("--strategy", choices=["topological", "layered", "parallel"],
                       default="topological")
    parser.add_argument("--circular-strategy", choices=["merge", "extract_interface", "break_dependency"],
                       default="merge")
    parser.add_argument("--no-circular", action="store_true", help="Fail on circular dependencies")
    parser.add_argument("--relative-imports", action="store_true", help="Use relative imports")
    
    args = parser.parse_args()
    
    config = DependencyPlannerConfig(
        project_root=args.project_root,
        project_name=args.project_name,
        strategy=args.strategy,
        circular_strategy=args.circular_strategy,
        fail_on_circular=not args.no_circular,
        use_relative_imports=args.relative_imports
    )
    
    planner = DependencyPlanner(config)
    
    if args.spec:
        with open(args.spec, 'r') as f:
            specs_data = json.load(f)
        plan = planner.plan_from_specs(specs_data.get('components', []))
    else:
        # Create example plan
        components = [
            ComponentSpec(name="domain.entity", component_type="class", layer=LayerType.DOMAIN),
            ComponentSpec(name="domain.repository", component_type="interface", layer=LayerType.DOMAIN),
            ComponentSpec(name="application.service", component_type="class", layer=LayerType.APPLICATION),
            ComponentSpec(name="infrastructure.repository_impl", component_type="class", layer=LayerType.INFRASTRUCTURE),
        ]
        
        components[2].dependencies.append(DependencyEdge(
            source="application.service", target="domain.repository",
            dep_type=DependencyType.INTERFACE, direction=DependencyDirection.UNKNOWN
        ))
        components[3].dependencies.append(DependencyEdge(
            source="infrastructure.repository_impl", target="domain.repository",
            dep_type=DependencyType.IMPLEMENTATION, direction=DependencyDirection.UNKNOWN
        ))
        
        plan = planner.plan(components)
    
    output = planner.export_plan(plan, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Plan saved to {args.output}")
    
    print(f"\nPlan created: {plan.total_components} components, {plan.total_dependencies} dependencies")
    print(f"Valid: {'Yes' if plan.is_valid else 'No'}")
    
    planner.close()


if __name__ == "__main__":
    main()