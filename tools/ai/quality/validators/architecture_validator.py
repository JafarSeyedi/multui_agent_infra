#!/usr/bin/env python3
"""
Architecture Validator - Validates architectural rules and layer dependencies.

Part of the Quality tools (validators/architecture_validator.py)

This architecture_validator.py provides:

1. Predefined Architectural Patterns - Clean, Hexagonal, Layered, DDD
2. Custom Layer Definitions - Define your own layers with path/module patterns
3. Dependency Rule Validation - Can/cannot depend on rules
4. Layer Violation Detection - Identifies improper dependencies
5. Circular Dependency Detection - Finds cycles in dependency graph
6. Architecture Metrics - Abstraction, instability, distance from main sequence
7. Multiple Report Formats - JSON and Markdown reports
8. Mermaid Diagram Generation - Visual layer dependency diagrams
9. Severity Levels - Error, Warning, Info with configurable failure thresholds
10. Allow/Block Lists - Fine-grained rule exceptions

The architecture validator ensures your codebase maintains its intended architectural boundaries and prevents technical debt accumulation.

"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager
from ...analysis.scanners.import_graph import ImportGraphAnalyzer, ImportGraph
from ...analysis.scanners.project_scanner import ProjectScanner, ProjectGraph

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class LayerType(str, Enum):
    """Architectural layer types."""
    DOMAIN = "domain"           # Core business logic, entities, value objects
    APPLICATION = "application"  # Use cases, application services
    INFRASTRUCTURE = "infrastructure"  # Repositories, external services
    INTERFACE = "interface"     # Controllers, presenters, API endpoints
    SHARED = "shared"          # Shared utilities, cross-cutting concerns
    CONFIG = "config"          # Configuration
    TEST = "test"              # Test code
    UNKNOWN = "unknown"


class DependencyRule(str, Enum):
    """Types of dependency rules."""
    CAN_DEPEND_ON = "can_depend_on"
    CANNOT_DEPEND_ON = "cannot_depend_on"
    CAN_BE_DEPENDED_ON_BY = "can_be_depended_on_by"
    MUST_IMPLEMENT = "must_implement"
    MUST_NOT_IMPLEMENT = "must_not_implement"


class RuleSeverity(str, Enum):
    """Severity of rule violation."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class PatternType(str, Enum):
    """Architectural pattern type."""
    CLEAN = "clean"
    HEXAGONAL = "hexagonal"
    LAYERED = "layered"
    DDD = "ddd"
    CQRS = "cqrs"
    MICROSERVICE = "microservice"
    MODULAR_MONOLITH = "modular_monolith"
    CUSTOM = "custom"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class LayerDefinition:
    """Definition of an architectural layer."""
    name: str
    layer_type: LayerType
    path_patterns: List[str] = field(default_factory=list)
    module_patterns: List[str] = field(default_factory=list)
    allowed_dependencies: List[str] = field(default_factory=list)
    forbidden_dependencies: List[str] = field(default_factory=list)
    allowed_dependents: List[str] = field(default_factory=list)
    must_implement_interfaces: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ArchitectureRule:
    """A single architectural rule."""
    name: str
    rule_type: DependencyRule
    severity: RuleSeverity
    source_pattern: str
    target_pattern: Optional[str] = None
    description: str = ""
    allow_list: List[Tuple[str, str]] = field(default_factory=list)
    block_list: List[Tuple[str, str]] = field(default_factory=list)
    enabled: bool = True


@dataclass
class RuleViolation:
    """Violation of an architectural rule."""
    rule_name: str
    severity: RuleSeverity
    source_module: str
    target_module: str
    description: str
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchitectureMetrics:
    """Architectural health metrics."""
    total_modules: int = 0
    modules_by_layer: Dict[str, int] = field(default_factory=dict)
    dependency_count: int = 0
    layer_violations: int = 0
    circular_dependencies: int = 0
    abstraction_score: float = 0.0
    instability_score: float = 0.0
    distance_from_main_sequence: float = 0.0
    cohesion_score: float = 0.0
    coupling_score: float = 0.0


@dataclass
class ArchitectureValidationReport:
    """Complete architecture validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    pattern_type: PatternType = PatternType.CUSTOM
    layers: List[LayerDefinition] = field(default_factory=list)
    rules: List[ArchitectureRule] = field(default_factory=list)
    violations: List[RuleViolation] = field(default_factory=list)
    warnings: List[RuleViolation] = field(default_factory=list)
    metrics: ArchitectureMetrics = field(default_factory=ArchitectureMetrics)
    module_layers: Dict[str, LayerType] = field(default_factory=dict)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    is_valid: bool = True
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchitectureValidatorConfig:
    """Configuration for architecture validator."""
    project_root: Path
    pattern_type: PatternType = PatternType.CUSTOM
    layers: List[LayerDefinition] = field(default_factory=list)
    custom_rules: List[ArchitectureRule] = field(default_factory=list)
    source_paths: List[str] = field(default_factory=lambda: ["engines", "tools", "src"])
    test_paths: List[str] = field(default_factory=lambda: ["tests", "test"])
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build"
    ])
    fail_on_error: bool = True
    fail_on_warning: bool = False
    generate_report: bool = True
    output_format: str = "markdown"


# ============================================================
# PREDEFINED ARCHITECTURAL PATTERNS
# ============================================================

class ArchitecturePatterns:
    """Predefined architectural patterns."""
    
    @staticmethod
    def clean_architecture() -> Tuple[List[LayerDefinition], List[ArchitectureRule]]:
        """Clean Architecture pattern."""
        layers = [
            LayerDefinition(
                name="domain",
                layer_type=LayerType.DOMAIN,
                path_patterns=["**/domain/**", "**/entities/**", "**/models/**"],
                module_patterns=["*.domain.*", "*.entities.*", "*.models.*"],
                allowed_dependencies=[],
                forbidden_dependencies=["application", "infrastructure", "interface"],
                description="Core business logic and entities"
            ),
            LayerDefinition(
                name="application",
                layer_type=LayerType.APPLICATION,
                path_patterns=["**/application/**", "**/usecases/**", "**/services/**"],
                module_patterns=["*.application.*", "*.usecases.*", "*.services.*"],
                allowed_dependencies=["domain"],
                forbidden_dependencies=["infrastructure", "interface"],
                description="Application use cases and services"
            ),
            LayerDefinition(
                name="infrastructure",
                layer_type=LayerType.INFRASTRUCTURE,
                path_patterns=["**/infrastructure/**", "**/repositories/**", "**/gateways/**"],
                module_patterns=["*.infrastructure.*", "*.repositories.*", "*.gateways.*"],
                allowed_dependencies=["domain", "application"],
                forbidden_dependencies=[],
                description="External services, repositories, gateways"
            ),
            LayerDefinition(
                name="interface",
                layer_type=LayerType.INTERFACE,
                path_patterns=["**/interfaces/**", "**/controllers/**", "**/api/**", "**/cli/**"],
                module_patterns=["*.interfaces.*", "*.controllers.*", "*.api.*", "*.cli.*"],
                allowed_dependencies=["application", "infrastructure"],
                forbidden_dependencies=["domain"],
                description="API endpoints, controllers, presenters"
            ),
            LayerDefinition(
                name="shared",
                layer_type=LayerType.SHARED,
                path_patterns=["**/shared/**", "**/utils/**", "**/common/**"],
                module_patterns=["*.shared.*", "*.utils.*", "*.common.*"],
                allowed_dependencies=[],
                forbidden_dependencies=[],
                description="Shared utilities and cross-cutting concerns"
            )
        ]
        
        rules = [
            ArchitectureRule(
                name="Domain Independence",
                rule_type=DependencyRule.CANNOT_DEPEND_ON,
                severity=RuleSeverity.ERROR,
                source_pattern="domain",
                target_pattern="application|infrastructure|interface",
                description="Domain layer must not depend on outer layers"
            ),
            ArchitectureRule(
                name="Application Dependencies",
                rule_type=DependencyRule.CANNOT_DEPEND_ON,
                severity=RuleSeverity.ERROR,
                source_pattern="application",
                target_pattern="infrastructure|interface",
                description="Application layer must not depend on infrastructure or interface"
            ),
            ArchitectureRule(
                name="Dependency Direction",
                rule_type=DependencyRule.CAN_DEPEND_ON,
                severity=RuleSeverity.ERROR,
                source_pattern="infrastructure",
                target_pattern="domain|application",
                description="Infrastructure may depend on domain and application"
            ),
        ]
        
        return layers, rules
    
    @staticmethod
    def hexagonal_architecture() -> Tuple[List[LayerDefinition], List[ArchitectureRule]]:
        """Hexagonal (Ports and Adapters) Architecture."""
        layers = [
            LayerDefinition(
                name="core",
                layer_type=LayerType.DOMAIN,
                path_patterns=["**/core/**", "**/domain/**"],
                module_patterns=["*.core.*", "*.domain.*"],
                allowed_dependencies=[],
                forbidden_dependencies=["adapters", "ports"],
                description="Core business logic"
            ),
            LayerDefinition(
                name="ports",
                layer_type=LayerType.APPLICATION,
                path_patterns=["**/ports/**", "**/interfaces/**"],
                module_patterns=["*.ports.*", "*.interfaces.*"],
                allowed_dependencies=["core"],
                forbidden_dependencies=["adapters"],
                description="Ports (interfaces) defining boundaries"
            ),
            LayerDefinition(
                name="adapters",
                layer_type=LayerType.INFRASTRUCTURE,
                path_patterns=["**/adapters/**", "**/infrastructure/**"],
                module_patterns=["*.adapters.*", "*.infrastructure.*"],
                allowed_dependencies=["core", "ports"],
                forbidden_dependencies=[],
                description="Adapters implementing ports"
            ),
        ]
        
        rules = [
            ArchitectureRule(
                name="Core Independence",
                rule_type=DependencyRule.CANNOT_DEPEND_ON,
                severity=RuleSeverity.ERROR,
                source_pattern="core",
                target_pattern="adapters",
                description="Core must not depend on adapters"
            ),
            ArchitectureRule(
                name="Ports Independence",
                rule_type=DependencyRule.CANNOT_DEPEND_ON,
                severity=RuleSeverity.ERROR,
                source_pattern="ports",
                target_pattern="adapters",
                description="Ports must not depend on adapters"
            ),
        ]
        
        return layers, rules
    
    @staticmethod
    def layered_architecture() -> Tuple[List[LayerDefinition], List[ArchitectureRule]]:
        """Traditional Layered Architecture."""
        layers = [
            LayerDefinition(
                name="presentation",
                layer_type=LayerType.INTERFACE,
                path_patterns=["**/presentation/**", "**/controllers/**", "**/views/**"],
                module_patterns=["*.presentation.*", "*.controllers.*", "*.views.*"],
                allowed_dependencies=["application"],
                forbidden_dependencies=["domain", "infrastructure"],
                description="Presentation layer"
            ),
            LayerDefinition(
                name="application",
                layer_type=LayerType.APPLICATION,
                path_patterns=["**/application/**", "**/services/**"],
                module_patterns=["*.application.*", "*.services.*"],
                allowed_dependencies=["domain"],
                forbidden_dependencies=["presentation", "infrastructure"],
                description="Application/Business layer"
            ),
            LayerDefinition(
                name="domain",
                layer_type=LayerType.DOMAIN,
                path_patterns=["**/domain/**", "**/models/**", "**/entities/**"],
                module_patterns=["*.domain.*", "*.models.*", "*.entities.*"],
                allowed_dependencies=[],
                forbidden_dependencies=["presentation", "application", "infrastructure"],
                description="Domain layer"
            ),
            LayerDefinition(
                name="infrastructure",
                layer_type=LayerType.INFRASTRUCTURE,
                path_patterns=["**/infrastructure/**", "**/data/**", "**/persistence/**"],
                module_patterns=["*.infrastructure.*", "*.data.*", "*.persistence.*"],
                allowed_dependencies=["domain"],
                forbidden_dependencies=["presentation", "application"],
                description="Infrastructure/Persistence layer"
            ),
        ]
        
        rules = [
            ArchitectureRule(
                name="Layered Dependencies",
                rule_type=DependencyRule.CAN_DEPEND_ON,
                severity=RuleSeverity.ERROR,
                source_pattern="presentation",
                target_pattern="application",
                description="Presentation depends on application"
            ),
            ArchitectureRule(
                name="No Layer Skipping",
                rule_type=DependencyRule.CANNOT_DEPEND_ON,
                severity=RuleSeverity.WARNING,
                source_pattern="presentation",
                target_pattern="domain|infrastructure",
                description="Presentation should not skip layers"
            ),
        ]
        
        return layers, rules
    
    @staticmethod
    def ddd_architecture() -> Tuple[List[LayerDefinition], List[ArchitectureRule]]:
        """Domain-Driven Design Architecture."""
        layers = [
            LayerDefinition(
                name="domain",
                layer_type=LayerType.DOMAIN,
                path_patterns=["**/domain/**"],
                module_patterns=["*.domain.*"],
                allowed_dependencies=[],
                forbidden_dependencies=["application", "infrastructure", "interfaces"],
                description="Domain layer with aggregates, entities, value objects"
            ),
            LayerDefinition(
                name="application",
                layer_type=LayerType.APPLICATION,
                path_patterns=["**/application/**"],
                module_patterns=["*.application.*"],
                allowed_dependencies=["domain"],
                forbidden_dependencies=["infrastructure", "interfaces"],
                description="Application services and use cases"
            ),
            LayerDefinition(
                name="infrastructure",
                layer_type=LayerType.INFRASTRUCTURE,
                path_patterns=["**/infrastructure/**"],
                module_patterns=["*.infrastructure.*"],
                allowed_dependencies=["domain", "application"],
                forbidden_dependencies=[],
                description="Infrastructure and repositories"
            ),
            LayerDefinition(
                name="interfaces",
                layer_type=LayerType.INTERFACE,
                path_patterns=["**/interfaces/**", "**/api/**"],
                module_patterns=["*.interfaces.*", "*.api.*"],
                allowed_dependencies=["application", "infrastructure"],
                forbidden_dependencies=["domain"],
                description="API, CLI, and other interfaces"
            ),
            LayerDefinition(
                name="shared_kernel",
                layer_type=LayerType.SHARED,
                path_patterns=["**/shared_kernel/**"],
                module_patterns=["*.shared_kernel.*"],
                allowed_dependencies=[],
                forbidden_dependencies=[],
                description="Shared kernel across bounded contexts"
            ),
        ]
        
        rules = [
            ArchitectureRule(
                name="Domain Purity",
                rule_type=DependencyRule.CANNOT_DEPEND_ON,
                severity=RuleSeverity.ERROR,
                source_pattern="domain",
                target_pattern="application|infrastructure|interfaces",
                description="Domain must remain pure and independent"
            ),
            ArchitectureRule(
                name="Repository Pattern",
                rule_type=DependencyRule.MUST_IMPLEMENT,
                severity=RuleSeverity.WARNING,
                source_pattern="infrastructure",
                target_pattern="domain.*Repository",
                description="Infrastructure should implement domain repository interfaces"
            ),
        ]
        
        return layers, rules


# ============================================================
# LAYER DETECTOR
# ============================================================

class LayerDetector:
    """Detects architectural layers from module paths."""
    
    def __init__(self, layers: List[LayerDefinition]):
        self.layers = layers
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for faster matching."""
        for layer in self.layers:
            layer._compiled_path_patterns = [
                re.compile(self._pattern_to_regex(p)) 
                for p in layer.path_patterns
            ]
            layer._compiled_module_patterns = [
                re.compile(self._pattern_to_regex(p)) 
                for p in layer.module_patterns
            ]
    
    def _pattern_to_regex(self, pattern: str) -> str:
        """Convert glob pattern to regex."""
        pattern = pattern.replace('.', r'\.')
        pattern = pattern.replace('**', '.*')
        pattern = pattern.replace('*', '[^/]*')
        return f"^{pattern}$"
    
    def detect_layer(self, module_name: str, file_path: Optional[str] = None) -> LayerType:
        """Detect the architectural layer of a module."""
        
        # Check by file path first
        if file_path:
            for layer in self.layers:
                for pattern in layer._compiled_path_patterns:
                    if pattern.match(file_path):
                        return layer.layer_type
        
        # Check by module name
        for layer in self.layers:
            for pattern in layer._compiled_module_patterns:
                if pattern.match(module_name):
                    return layer.layer_type
        
        # Check for test paths
        if file_path:
            if '/test/' in file_path or '/tests/' in file_path or file_path.startswith('test_'):
                return LayerType.TEST
        
        return LayerType.UNKNOWN
    
    def get_layer_definition(self, layer_type: LayerType) -> Optional[LayerDefinition]:
        """Get layer definition by type."""
        for layer in self.layers:
            if layer.layer_type == layer_type:
                return layer
        return None


# ============================================================
# RULE VALIDATOR
# ============================================================

class RuleValidator:
    """Validates architectural rules against dependencies."""
    
    def __init__(self, rules: List[ArchitectureRule], layers: List[LayerDefinition]):
        self.rules = rules
        self.layers = layers
        self.layer_map = {l.name: l for l in layers}
    
    def validate_dependency(self, source_module: str, target_module: str,
                            source_layer: LayerType, target_layer: LayerType,
                            source_path: Optional[str] = None,
                            line_number: Optional[int] = None) -> List[RuleViolation]:
        """Validate a single dependency against all rules."""
        violations = []
        
        source_layer_name = source_layer.value if source_layer else "unknown"
        target_layer_name = target_layer.value if target_layer else "unknown"
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Check if source matches rule pattern
            if not self._matches_pattern(source_layer_name, rule.source_pattern):
                continue
            
            # Check target pattern if specified
            if rule.target_pattern:
                if not self._matches_pattern(target_layer_name, rule.target_pattern):
                    continue
            
            # Check allow list
            if rule.allow_list:
                allowed = any(
                    self._matches_pattern(source_layer_name, s) and 
                    self._matches_pattern(target_layer_name, t)
                    for s, t in rule.allow_list
                )
                if allowed:
                    continue
            
            # Check block list
            if rule.block_list:
                blocked = any(
                    self._matches_pattern(source_layer_name, s) and 
                    self._matches_pattern(target_layer_name, t)
                    for s, t in rule.block_list
                )
                if not blocked:
                    continue
            
            # Rule matched - create violation
            if rule.rule_type == DependencyRule.CANNOT_DEPEND_ON:
                violations.append(RuleViolation(
                    rule_name=rule.name,
                    severity=rule.severity,
                    source_module=source_module,
                    target_module=target_module,
                    description=f"{source_module} ({source_layer_name}) cannot depend on {target_module} ({target_layer_name}): {rule.description}",
                    line_number=line_number,
                    file_path=source_path,
                    suggestion=f"Consider using dependency inversion or moving the dependency to a lower layer"
                ))
            
            elif rule.rule_type == DependencyRule.CAN_DEPEND_ON:
                # This is an expected dependency - no violation
                pass
        
        return violations
    
    def _matches_pattern(self, value: str, pattern: str) -> bool:
        """Check if value matches regex pattern."""
        try:
            return bool(re.match(pattern, value, re.IGNORECASE))
        except re.error:
            return value == pattern


# ============================================================
# MAIN ARCHITECTURE VALIDATOR
# ============================================================

class ArchitectureValidator:
    """
    Validates architectural rules and layer dependencies.
    
    Features:
    - Predefined architectural patterns (Clean, Hexagonal, Layered, DDD)
    - Custom layer definitions
    - Dependency rule validation
    - Layer violation detection
    - Circular dependency detection
    - Architecture metrics calculation
    - Multiple report formats
    - Visual dependency graphs
    """
    
    def __init__(self, config: ArchitectureValidatorConfig):
        self.config = config
        
        # Load pattern if specified
        if config.pattern_type != PatternType.CUSTOM and not config.layers:
            self._load_pattern(config.pattern_type)
        
        self.layer_detector = LayerDetector(config.layers)
        self.rule_validator = RuleValidator(config.custom_rules, config.layers)
        
        self.scanner = ProjectScanner(project_root=config.project_root)
        self.import_analyzer = ImportGraphAnalyzer(
            project_root=config.project_root,
            include_external=False
        )
        
        self.state = StateManager(config.project_root / ".ai_state" / "architecture_validator.json")
        
        logger.info(f"ArchitectureValidator initialized with {config.pattern_type.value} pattern")
    
    def _load_pattern(self, pattern_type: PatternType):
        """Load predefined architectural pattern."""
        if pattern_type == PatternType.CLEAN:
            layers, rules = ArchitecturePatterns.clean_architecture()
        elif pattern_type == PatternType.HEXAGONAL:
            layers, rules = ArchitecturePatterns.hexagonal_architecture()
        elif pattern_type == PatternType.LAYERED:
            layers, rules = ArchitecturePatterns.layered_architecture()
        elif pattern_type == PatternType.DDD:
            layers, rules = ArchitecturePatterns.ddd_architecture()
        else:
            return
        
        self.config.layers = layers
        self.config.custom_rules = rules
    
    def validate(self) -> ArchitectureValidationReport:
        """Run complete architecture validation."""
        logger.info("Starting architecture validation...")
        
        report = ArchitectureValidationReport(
            pattern_type=self.config.pattern_type,
            layers=self.config.layers,
            rules=self.config.custom_rules
        )
        
        # Scan project
        project_graph = self.scanner.scan()
        import_graph = self.import_analyzer.analyze()
        
        # Detect layers for all modules
        module_layers = {}
        for module_name, module_info in project_graph.modules.items():
            file_path = module_info.file_info.path if module_info.file_info else None
            layer = self.layer_detector.detect_layer(module_name, file_path)
            
            # Skip test modules
            if layer == LayerType.TEST:
                continue
            
            module_layers[module_name] = layer
        
        report.module_layers = module_layers
        
        # Validate dependencies
        for module_name, layer in module_layers.items():
            deps = import_graph.dependency_graph.get(module_name, [])
            
            for dep in deps:
                dep_layer = module_layers.get(dep, LayerType.UNKNOWN)
                
                # Skip self-dependencies
                if module_name == dep:
                    continue
                
                # Skip external dependencies
                if dep_layer == LayerType.UNKNOWN:
                    continue
                
                # Find line number from AST
                line_number = self._find_import_line(module_name, dep)
                file_path = project_graph.modules[module_name].file_info.path if module_name in project_graph.modules else None
                
                violations = self.rule_validator.validate_dependency(
                    source_module=module_name,
                    target_module=dep,
                    source_layer=layer,
                    target_layer=dep_layer,
                    source_path=file_path,
                    line_number=line_number
                )
                
                for violation in violations:
                    if violation.severity == RuleSeverity.ERROR:
                        report.violations.append(violation)
                        report.is_valid = False
                    elif violation.severity == RuleSeverity.WARNING:
                        report.warnings.append(violation)
        
        # Build dependency graph for report
        report.dependency_graph = {
            module: deps for module, deps in import_graph.dependency_graph.items()
            if module in module_layers
        }
        
        # Detect circular dependencies
        circular_deps = self._detect_circular_dependencies(report.dependency_graph)
        for cycle in circular_deps:
            report.violations.append(RuleViolation(
                rule_name="Circular Dependency",
                severity=RuleSeverity.ERROR,
                source_module=cycle[0],
                target_module=cycle[-1],
                description=f"Circular dependency detected: {' -> '.join(cycle)}",
                suggestion="Break the cycle using dependency inversion or extract shared interfaces"
            ))
            report.is_valid = False
        
        # Calculate metrics
        report.metrics = self._calculate_metrics(project_graph, module_layers, import_graph)
        
        # Generate summary
        report.summary = self._generate_summary(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Architecture validation complete: {len(report.violations)} errors, {len(report.warnings)} warnings")
        
        return report
    
    def _find_import_line(self, source_module: str, target_module: str) -> Optional[int]:
        """Find line number of import statement."""
        # Simplified - would use AST analysis
        return None
    
    def _detect_circular_dependencies(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Detect circular dependencies in graph."""
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
    
    def _calculate_metrics(self, project_graph: ProjectGraph,
                           module_layers: Dict[str, LayerType],
                           import_graph: ImportGraph) -> ArchitectureMetrics:
        """Calculate architecture health metrics."""
        metrics = ArchitectureMetrics()
        
        metrics.total_modules = len(module_layers)
        
        # Modules by layer
        for layer in module_layers.values():
            layer_name = layer.value if layer else "unknown"
            metrics.modules_by_layer[layer_name] = metrics.modules_by_layer.get(layer_name, 0) + 1
        
        # Dependency count
        metrics.dependency_count = sum(len(deps) for deps in import_graph.dependency_graph.values())
        
        # Calculate abstraction and instability
        abstract_classes = 0
        total_classes = 0
        
        for module_info in project_graph.modules.values():
            for symbol in module_info.symbols:
                if symbol.symbol_type.value == 'class':
                    total_classes += 1
                    if symbol.is_abstract:
                        abstract_classes += 1
        
        if total_classes > 0:
            metrics.abstraction_score = abstract_classes / total_classes
        
        if metrics.total_modules > 0:
            avg_fan_out = metrics.dependency_count / metrics.total_modules
            metrics.instability_score = min(1.0, avg_fan_out / 10)
            metrics.distance_from_main_sequence = abs(metrics.abstraction_score + metrics.instability_score - 1.0)
        
        return metrics
    
    def _generate_summary(self, report: ArchitectureValidationReport) -> str:
        """Generate validation summary."""
        if report.is_valid:
            return f"✅ Architecture validation passed. {len(report.warnings)} warnings."
        else:
            return f"❌ Architecture validation failed. {len(report.violations)} errors, {len(report.warnings)} warnings."
    
    def _save_report(self, report: ArchitectureValidationReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.validated_at.isoformat(),
            'pattern': report.pattern_type.value,
            'is_valid': report.is_valid,
            'errors': len(report.violations),
            'warnings': len(report.warnings),
            'modules': report.metrics.total_modules
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: ArchitectureValidationReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export validation report."""
        
        if format == 'json':
            data = {
                'validated_at': report.validated_at.isoformat(),
                'pattern_type': report.pattern_type.value,
                'is_valid': report.is_valid,
                'summary': report.summary,
                'metrics': {
                    'total_modules': report.metrics.total_modules,
                    'modules_by_layer': report.metrics.modules_by_layer,
                    'dependency_count': report.metrics.dependency_count,
                    'abstraction_score': report.metrics.abstraction_score,
                    'instability_score': report.metrics.instability_score
                },
                'violations': [
                    {
                        'rule': v.rule_name,
                        'severity': v.severity.value,
                        'source': v.source_module,
                        'target': v.target_module,
                        'description': v.description,
                        'suggestion': v.suggestion
                    }
                    for v in report.violations
                ],
                'warnings': [
                    {
                        'rule': w.rule_name,
                        'source': w.source_module,
                        'target': w.target_module,
                        'description': w.description
                    }
                    for w in report.warnings
                ],
                'module_layers': {
                    k: v.value for k, v in report.module_layers.items()
                }
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Architecture Validation Report",
                "",
                f"**Pattern:** {report.pattern_type.value}",
                f"**Validated:** {report.validated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Status:** {report.summary}",
                "",
                "## Metrics",
                "",
                f"- **Total Modules:** {report.metrics.total_modules}",
                f"- **Total Dependencies:** {report.metrics.dependency_count}",
                f"- **Abstraction Score:** {report.metrics.abstraction_score:.2%}",
                f"- **Instability Score:** {report.metrics.instability_score:.2%}",
                f"- **Distance from Main Sequence:** {report.metrics.distance_from_main_sequence:.3f}",
                "",
                "## Modules by Layer",
                "",
                "| Layer | Count |",
                "|-------|-------|",
            ]
            
            for layer, count in sorted(report.metrics.modules_by_layer.items()):
                lines.append(f"| {layer} | {count} |")
            
            if report.violations:
                lines.extend([
                    "",
                    "## ❌ Violations",
                    ""
                ])
                for v in report.violations:
                    lines.append(f"- **{v.rule_name}**: {v.source_module} → {v.target_module}")
                    lines.append(f"  {v.description}")
                    if v.suggestion:
                        lines.append(f"  *Suggestion:* {v.suggestion}")
                    lines.append("")
            
            if report.warnings:
                lines.extend([
                    "## ⚠️ Warnings",
                    ""
                ])
                for w in report.warnings:
                    lines.append(f"- **{w.rule_name}**: {w.source_module} → {w.target_module}")
                    lines.append(f"  {w.description}")
                    lines.append("")
            
            if not report.violations and not report.warnings:
                lines.extend([
                    "",
                    "✅ No architecture violations found!",
                    ""
                ])
            
            # Layer definitions
            lines.extend([
                "## Layer Definitions",
                ""
            ])
            
            for layer in report.layers:
                lines.append(f"### {layer.name} ({layer.layer_type.value})")
                lines.append(f"{layer.description}")
                lines.append("")
                if layer.allowed_dependencies:
                    lines.append(f"**Allowed dependencies:** {', '.join(layer.allowed_dependencies)}")
                if layer.forbidden_dependencies:
                    lines.append(f"**Forbidden dependencies:** {', '.join(layer.forbidden_dependencies)}")
                lines.append("")
            
            content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def generate_mermaid_diagram(self, report: ArchitectureValidationReport,
                                  max_modules: int = 50) -> str:
        """Generate Mermaid diagram of architecture layers."""
        lines = [
            "```mermaid",
            "graph TB",
            "",
            "subgraph \"Interface Layer\"",
        ]
        
        interface_modules = [m for m, l in report.module_layers.items() if l == LayerType.INTERFACE]
        for module in interface_modules[:10]:
            short_name = module.split('.')[-1]
            lines.append(f"    {self._sanitize(module)}[\"{short_name}\"]")
        lines.append("end")
        
        lines.append("")
        lines.append("subgraph \"Application Layer\"")
        app_modules = [m for m, l in report.module_layers.items() if l == LayerType.APPLICATION]
        for module in app_modules[:10]:
            short_name = module.split('.')[-1]
            lines.append(f"    {self._sanitize(module)}[\"{short_name}\"]")
        lines.append("end")
        
        lines.append("")
        lines.append("subgraph \"Domain Layer\"")
        domain_modules = [m for m, l in report.module_layers.items() if l == LayerType.DOMAIN]
        for module in domain_modules[:10]:
            short_name = module.split('.')[-1]
            lines.append(f"    {self._sanitize(module)}[\"{short_name}\"]")
        lines.append("end")
        
        lines.append("")
        lines.append("subgraph \"Infrastructure Layer\"")
        infra_modules = [m for m, l in report.module_layers.items() if l == LayerType.INFRASTRUCTURE]
        for module in infra_modules[:10]:
            short_name = module.split('.')[-1]
            lines.append(f"    {self._sanitize(module)}[\"{short_name}\"]")
        lines.append("end")
        
        # Add dependencies
        lines.append("")
        for source, targets in report.dependency_graph.items():
            if source in report.module_layers:
                for target in targets[:5]:
                    if target in report.module_layers:
                        lines.append(f"    {self._sanitize(source)} --> {self._sanitize(target)}")
        
        lines.append("```")
        
        return '\n'.join(lines)
    
    def _sanitize(self, name: str) -> str:
        """Sanitize name for Mermaid."""
        return name.replace('.', '_').replace('-', '_')
    
    def validate_module(self, module_name: str) -> List[RuleViolation]:
        """Validate a single module against architecture rules."""
        # This would validate just one module
        pass
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("ArchitectureValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for architecture validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate architectural rules")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--pattern", choices=[p.value for p in PatternType],
                       default=PatternType.CUSTOM.value)
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--mermaid", action="store_true", help="Generate Mermaid diagram")
    parser.add_argument("--fail-on-warning", action="store_true")
    
    args = parser.parse_args()
    
    config = ArchitectureValidatorConfig(
        project_root=args.project_root,
        pattern_type=PatternType(args.pattern),
        fail_on_warning=args.fail_on_warning
    )
    
    validator = ArchitectureValidator(config)
    
    report = validator.validate()
    
    if args.mermaid:
        print(validator.generate_mermaid_diagram(report))
    else:
        output = validator.export_report(report, args.output, args.format)
        if not args.output:
            print(output)
        else:
            print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    
    # Exit code
    if config.fail_on_error and not report.is_valid:
        exit(1)
    if config.fail_on_warning and report.warnings:
        exit(1)
    
    validator.close()


if __name__ == "__main__":
    main()