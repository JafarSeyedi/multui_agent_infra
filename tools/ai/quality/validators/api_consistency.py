#!/usr/bin/env python3
"""
API Consistency Validator - Validates API compatibility and semantic versioning.

Part of the Quality tools (validators/api_consistency.py)

This api_consistency.py provides:

1. API Surface Comparison - Compares two versions of API surfaces
2. Breaking Change Detection - Identifies removals, signature changes, visibility changes
3. Semantic Versioning Impact - Calculates major/minor/patch impact
4. Parameter-Level Analysis - Detects added/removed parameters, type changes, default value changes
5. Base Class Change Detection - Identifies inheritance changes
6. Deprecation Tracking - Tracks deprecation additions and removals
7. Migration Guide Generation - Creates migration guides for breaking changes
8. Multiple Export Formats - JSON and Markdown reports
9. Git Integration - Compare against git history

Compatibility Status - Clear yes/no compatibility determination
"""

import ast
import json
import difflib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager
from ...analysis.scanners.api_surface_extractor import APISurfaceExtractor, APIElement, APIVisibility

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class ChangeType(str, Enum):
    """Type of API change."""
    ADDITION = "addition"               # New API element added
    REMOVAL = "removal"                 # API element removed
    RENAME = "rename"                   # API element renamed
    SIGNATURE_CHANGE = "signature_change"  # Function signature changed
    RETURN_TYPE_CHANGE = "return_type_change"
    PARAMETER_ADDED = "parameter_added"
    PARAMETER_REMOVED = "parameter_removed"
    PARAMETER_TYPE_CHANGED = "parameter_type_changed"
    DEFAULT_VALUE_CHANGED = "default_value_changed"
    VISIBILITY_CHANGED = "visibility_changed"  # public->private etc.
    DEPRECATION_ADDED = "deprecation_added"
    DEPRECATION_REMOVED = "deprecation_removed"
    EXCEPTION_ADDED = "exception_added"
    EXCEPTION_REMOVED = "exception_removed"
    DECORATOR_ADDED = "decorator_added"
    DECORATOR_REMOVED = "decorator_removed"
    BASE_CLASS_CHANGED = "base_class_changed"
    ATTRIBUTE_ADDED = "attribute_added"
    ATTRIBUTE_REMOVED = "attribute_removed"
    ATTRIBUTE_TYPE_CHANGED = "attribute_type_changed"


class SemVerImpact(str, Enum):
    """Semantic versioning impact."""
    MAJOR = "major"      # Breaking change
    MINOR = "minor"      # New functionality, backwards compatible
    PATCH = "patch"      # Bug fix, no API change
    NONE = "none"        # No impact


class CompatibilityStatus(str, Enum):
    """Compatibility check result."""
    COMPATIBLE = "compatible"
    BREAKING = "breaking"
    WARNING = "warning"
    INFO = "info"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class APIChange:
    """Represents a single API change."""
    change_type: ChangeType
    element_name: str
    element_type: str
    severity: CompatibilityStatus
    semver_impact: SemVerImpact
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    old_signature: Optional[str] = None
    new_signature: Optional[str] = None
    description: str = ""
    suggestion: Optional[str] = None
    location: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APICompatibilityReport:
    """Complete API compatibility report."""
    baseline_version: str
    target_version: str
    analyzed_at: datetime = field(default_factory=datetime.now)
    changes: List[APIChange] = field(default_factory=list)
    breaking_changes: List[APIChange] = field(default_factory=list)
    warnings: List[APIChange] = field(default_factory=list)
    additions: List[APIChange] = field(default_factory=list)
    overall_impact: SemVerImpact = SemVerImpact.NONE
    is_compatible: bool = True
    migration_guide: Optional[str] = None
    statistics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIValidatorConfig:
    """Configuration for API validator."""
    baseline_api_path: Optional[Path] = None
    check_visibility_changes: bool = True
    check_signature_changes: bool = True
    check_return_types: bool = True
    check_exceptions: bool = True
    check_deprecations: bool = True
    check_documentation: bool = False
    ignore_private: bool = True
    ignore_protected: bool = False
    ignore_deprecated: bool = False
    strict_mode: bool = False
    generate_migration_guide: bool = True
    output_format: str = "json"


# ============================================================
# API COMPARATOR
# ============================================================

class APIComparator:
    """Compares two API surfaces and detects changes."""
    
    def __init__(self, config: APIValidatorConfig):
        self.config = config
    
    def compare(self, 
                baseline_elements: Dict[str, APIElement],
                target_elements: Dict[str, APIElement]) -> List[APIChange]:
        """Compare two API surfaces and return all changes."""
        changes = []
        
        baseline_names = set(baseline_elements.keys())
        target_names = set(target_elements.keys())
        
        # Find removals
        removed = baseline_names - target_names
        for name in removed:
            element = baseline_elements[name]
            if self._should_ignore(element):
                continue
            
            change = APIChange(
                change_type=ChangeType.REMOVAL,
                element_name=name,
                element_type=element.element_type.value,
                severity=CompatibilityStatus.BREAKING,
                semver_impact=SemVerImpact.MAJOR,
                old_signature=element.signature,
                description=f"API element '{name}' was removed",
                suggestion=f"Either restore '{name}' or update all callers",
                location=element.file_path
            )
            changes.append(change)
        
        # Find additions
        added = target_names - baseline_names
        for name in added:
            element = target_elements[name]
            if self._should_ignore(element):
                continue
            
            # Determine if this is a minor or patch addition
            impact = SemVerImpact.MINOR
            if element.element_type.value in ('constant', 'type_alias'):
                impact = SemVerImpact.PATCH
            
            change = APIChange(
                change_type=ChangeType.ADDITION,
                element_name=name,
                element_type=element.element_type.value,
                severity=CompatibilityStatus.INFO,
                semver_impact=impact,
                new_signature=element.signature,
                description=f"New API element '{name}' added",
                location=element.file_path
            )
            changes.append(change)
        
        # Find modifications
        common = baseline_names & target_names
        for name in common:
            baseline = baseline_elements[name]
            target = target_elements[name]
            
            if self._should_ignore(baseline) or self._should_ignore(target):
                continue
            
            element_changes = self._compare_elements(baseline, target)
            changes.extend(element_changes)
        
        return changes
    
    def _should_ignore(self, element: APIElement) -> bool:
        """Check if element should be ignored."""
        if self.config.ignore_private and element.visibility == APIVisibility.PRIVATE:
            return True
        if self.config.ignore_protected and element.visibility == APIVisibility.PROTECTED:
            return True
        if self.config.ignore_deprecated and element.deprecation != "active":
            return True
        return False
    
    def _compare_elements(self, baseline: APIElement, 
                          target: APIElement) -> List[APIChange]:
        """Compare two versions of the same API element."""
        changes = []
        
        # Check visibility change
        if self.config.check_visibility_changes:
            if baseline.visibility != target.visibility:
                severity = CompatibilityStatus.BREAKING
                if baseline.visibility == APIVisibility.PUBLIC and target.visibility != APIVisibility.PUBLIC:
                    severity = CompatibilityStatus.BREAKING
                elif baseline.visibility != APIVisibility.PUBLIC and target.visibility == APIVisibility.PUBLIC:
                    severity = CompatibilityStatus.INFO
                
                changes.append(APIChange(
                    change_type=ChangeType.VISIBILITY_CHANGED,
                    element_name=baseline.qualified_name,
                    element_type=baseline.element_type.value,
                    severity=severity,
                    semver_impact=SemVerImpact.MAJOR if severity == CompatibilityStatus.BREAKING else SemVerImpact.MINOR,
                    old_value=baseline.visibility.value,
                    new_value=target.visibility.value,
                    description=f"Visibility changed from '{baseline.visibility.value}' to '{target.visibility.value}'",
                    location=target.file_path
                ))
        
        # Check signature changes
        if self.config.check_signature_changes:
            if baseline.element_type.value in ('function', 'method', 'async_function', 'async_method'):
                sig_changes = self._compare_signatures(baseline, target)
                changes.extend(sig_changes)
        
        # Check return type changes
        if self.config.check_return_types:
            if baseline.return_type != target.return_type:
                severity = CompatibilityStatus.BREAKING if self.config.strict_mode else CompatibilityStatus.WARNING
                changes.append(APIChange(
                    change_type=ChangeType.RETURN_TYPE_CHANGE,
                    element_name=baseline.qualified_name,
                    element_type=baseline.element_type.value,
                    severity=severity,
                    semver_impact=SemVerImpact.MAJOR if severity == CompatibilityStatus.BREAKING else SemVerImpact.MINOR,
                    old_value=baseline.return_type,
                    new_value=target.return_type,
                    description=f"Return type changed from '{baseline.return_type}' to '{target.return_type}'",
                    suggestion="Update callers to handle new return type",
                    location=target.file_path
                ))
        
        # Check deprecation status
        if self.config.check_deprecations:
            if baseline.deprecation == "active" and target.deprecation == "deprecated":
                changes.append(APIChange(
                    change_type=ChangeType.DEPRECATION_ADDED,
                    element_name=baseline.qualified_name,
                    element_type=baseline.element_type.value,
                    severity=CompatibilityStatus.WARNING,
                    semver_impact=SemVerImpact.MINOR,
                    description=f"Element marked as deprecated: {target.deprecation_message or 'No message'}",
                    suggestion="Update code to use alternative API",
                    location=target.file_path
                ))
            elif baseline.deprecation == "deprecated" and target.deprecation == "active":
                changes.append(APIChange(
                    change_type=ChangeType.DEPRECATION_REMOVED,
                    element_name=baseline.qualified_name,
                    element_type=baseline.element_type.value,
                    severity=CompatibilityStatus.INFO,
                    semver_impact=SemVerImpact.PATCH,
                    description="Deprecation removed - element is active again",
                    location=target.file_path
                ))
        
        # Check base classes for classes
        if baseline.element_type.value == 'class' and target.element_type.value == 'class':
            base_changes = self._compare_bases(baseline, target)
            changes.extend(base_changes)
        
        return changes
    
    def _compare_signatures(self, baseline: APIElement, 
                            target: APIElement) -> List[APIChange]:
        """Compare function/method signatures."""
        changes = []
        
        # Get parameters
        baseline_params = {p.name: p for p in baseline.parameters}
        target_params = {p.name: p for p in target.parameters}
        
        # Check removed parameters
        removed_params = set(baseline_params.keys()) - set(target_params.keys())
        for param_name in removed_params:
            param = baseline_params[param_name]
            if param.default_value is None:  # Required parameter removed
                severity = CompatibilityStatus.BREAKING
                impact = SemVerImpact.MAJOR
            else:
                severity = CompatibilityStatus.WARNING
                impact = SemVerImpact.MINOR
            
            changes.append(APIChange(
                change_type=ChangeType.PARAMETER_REMOVED,
                element_name=baseline.qualified_name,
                element_type=baseline.element_type.value,
                severity=severity,
                semver_impact=impact,
                old_value=param.name,
                description=f"Parameter '{param.name}' removed",
                suggestion="Update all callers to remove this argument" if severity == CompatibilityStatus.BREAKING else None,
                location=target.file_path
            ))
        
        # Check added parameters
        added_params = set(target_params.keys()) - set(baseline_params.keys())
        for param_name in added_params:
            param = target_params[param_name]
            if param.default_value is None:  # Required parameter added
                severity = CompatibilityStatus.BREAKING
                impact = SemVerImpact.MAJOR
            else:
                severity = CompatibilityStatus.INFO
                impact = SemVerImpact.MINOR
            
            changes.append(APIChange(
                change_type=ChangeType.PARAMETER_ADDED,
                element_name=baseline.qualified_name,
                element_type=baseline.element_type.value,
                severity=severity,
                semver_impact=impact,
                new_value=param.name,
                description=f"Parameter '{param.name}' added",
                suggestion="Update all callers to provide this argument" if severity == CompatibilityStatus.BREAKING else None,
                location=target.file_path
            ))
        
        # Check parameter type changes
        common_params = set(baseline_params.keys()) & set(target_params.keys())
        for param_name in common_params:
            baseline_param = baseline_params[param_name]
            target_param = target_params[param_name]
            
            if baseline_param.type_annotation != target_param.type_annotation:
                severity = CompatibilityStatus.BREAKING if self.config.strict_mode else CompatibilityStatus.WARNING
                changes.append(APIChange(
                    change_type=ChangeType.PARAMETER_TYPE_CHANGED,
                    element_name=baseline.qualified_name,
                    element_type=baseline.element_type.value,
                    severity=severity,
                    semver_impact=SemVerImpact.MAJOR if severity == CompatibilityStatus.BREAKING else SemVerImpact.MINOR,
                    old_value=baseline_param.type_annotation,
                    new_value=target_param.type_annotation,
                    description=f"Parameter '{param_name}' type changed from '{baseline_param.type_annotation}' to '{target_param.type_annotation}'",
                    location=target.file_path
                ))
            
            # Check default value changes
            if baseline_param.default_value != target_param.default_value:
                changes.append(APIChange(
                    change_type=ChangeType.DEFAULT_VALUE_CHANGED,
                    element_name=baseline.qualified_name,
                    element_type=baseline.element_type.value,
                    severity=CompatibilityStatus.WARNING,
                    semver_impact=SemVerImpact.MINOR,
                    old_value=baseline_param.default_value,
                    new_value=target_param.default_value,
                    description=f"Parameter '{param_name}' default value changed",
                    suggestion="Verify behavior with new default",
                    location=target.file_path
                ))
        
        return changes
    
    def _compare_bases(self, baseline: APIElement, 
                       target: APIElement) -> List[APIChange]:
        """Compare base classes."""
        changes = []
        
        baseline_bases = set(baseline.bases)
        target_bases = set(target.bases)
        
        removed_bases = baseline_bases - target_bases
        for base in removed_bases:
            changes.append(APIChange(
                change_type=ChangeType.BASE_CLASS_CHANGED,
                element_name=baseline.qualified_name,
                element_type='class',
                severity=CompatibilityStatus.BREAKING,
                semver_impact=SemVerImpact.MAJOR,
                old_value=base,
                description=f"Base class '{base}' removed",
                suggestion="Update subclasses or restore inheritance",
                location=target.file_path
            ))
        
        added_bases = target_bases - baseline_bases
        for base in added_bases:
            changes.append(APIChange(
                change_type=ChangeType.BASE_CLASS_CHANGED,
                element_name=baseline.qualified_name,
                element_type='class',
                severity=CompatibilityStatus.INFO,
                semver_impact=SemVerImpact.MINOR,
                new_value=base,
                description=f"Base class '{base}' added",
                location=target.file_path
            ))
        
        return changes


# ============================================================
# MAIN API VALIDATOR
# ============================================================

class APIConsistencyValidator:
    """
    Validates API consistency and semantic versioning compliance.
    
    Features:
    - Compare API surfaces between versions
    - Detect breaking changes
    - Calculate semantic version impact
    - Generate migration guides
    - Check backwards compatibility
    - Validate against baseline API
    - Export compatibility reports
    """
    
    def __init__(self, config: Optional[APIValidatorConfig] = None):
        self.config = config or APIValidatorConfig()
        self.comparator = APIComparator(self.config)
        self.extractor = APISurfaceExtractor()
        self.state = StateManager(Path(".ai_state") / "api_validator.json")
        
        logger.info("APIConsistencyValidator initialized")
    
    def validate(self, 
                 target_path: Path,
                 baseline_path: Optional[Path] = None) -> APICompatibilityReport:
        """
        Validate API consistency.
        
        Args:
            target_path: Path to target code (new version)
            baseline_path: Path to baseline API (old version)
        """
        logger.info(f"Validating API consistency for {target_path}")
        
        # Extract target API
        target_surface = self.extractor.extract(target_path)
        target_elements = target_surface.global_elements
        
        # Get baseline API
        if baseline_path:
            baseline_surface = self.extractor.extract(baseline_path)
            baseline_elements = baseline_surface.global_elements
            baseline_version = baseline_surface.project_version or "baseline"
        elif self.config.baseline_api_path:
            baseline_data = json.loads(self.config.baseline_api_path.read_text())
            baseline_elements = self._deserialize_elements(baseline_data.get('elements', []))
            baseline_version = baseline_data.get('version', 'baseline')
        else:
            # No baseline - assume all compatible
            logger.warning("No baseline API provided, assuming compatibility")
            return APICompatibilityReport(
                baseline_version="unknown",
                target_version=target_surface.project_version or "target",
                is_compatible=True,
                overall_impact=SemVerImpact.NONE
            )
        
        target_version = target_surface.project_version or "target"
        
        # Compare APIs
        changes = self.comparator.compare(baseline_elements, target_elements)
        
        # Build report
        report = APICompatibilityReport(
            baseline_version=baseline_version,
            target_version=target_version,
            changes=changes
        )
        
        # Categorize changes
        for change in changes:
            if change.severity == CompatibilityStatus.BREAKING:
                report.breaking_changes.append(change)
                report.is_compatible = False
            elif change.severity == CompatibilityStatus.WARNING:
                report.warnings.append(change)
            elif change.change_type == ChangeType.ADDITION:
                report.additions.append(change)
        
        # Determine overall semver impact
        report.overall_impact = self._determine_semver_impact(changes)
        
        # Calculate statistics
        report.statistics = self._calculate_statistics(changes)
        
        # Generate migration guide if needed
        if self.config.generate_migration_guide and report.breaking_changes:
            report.migration_guide = self._generate_migration_guide(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"API validation complete: {len(report.breaking_changes)} breaking, "
                   f"{len(report.warnings)} warnings, {len(report.additions)} additions")
        
        return report
    
    def validate_string(self, 
                        target_code: str,
                        baseline_code: Optional[str] = None) -> APICompatibilityReport:
        """Validate API consistency from code strings."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            target_file = tmp_path / "target.py"
            target_file.write_text(target_code)
            
            if baseline_code:
                baseline_file = tmp_path / "baseline.py"
                baseline_file.write_text(baseline_code)
                return self.validate(target_file, baseline_file)
            else:
                return self.validate(target_file)
    
    def validate_module(self, 
                         module_name: str,
                         baseline_commit: Optional[str] = None) -> APICompatibilityReport:
        """Validate API consistency against git history."""
        from ...shared.git_utils import GitUtils
        
        git = GitUtils(Path.cwd())
        
        # Get current code
        current_code = self._get_module_code(module_name)
        
        if baseline_commit:
            baseline_code = git.get_file_content_at_commit(module_name, baseline_commit)
        else:
            # Use previous commit
            baseline_code = git.get_file_content_at_commit(module_name, 'HEAD~1')
        
        if baseline_code:
            return self.validate_string(current_code, baseline_code)
        else:
            return self.validate_string(current_code)
    
    def _get_module_code(self, module_name: str) -> str:
        """Get current code for a module."""
        module_path = Path(module_name.replace('.', '/') + '.py')
        if module_path.exists():
            return module_path.read_text()
        
        # Try as package
        package_path = Path(module_name.replace('.', '/')) / '__init__.py'
        if package_path.exists():
            return package_path.read_text()
        
        raise FileNotFoundError(f"Module {module_name} not found")
    
    def _deserialize_elements(self, data: List[Dict]) -> Dict[str, APIElement]:
        """Deserialize API elements from JSON."""
        elements = {}
        for elem_data in data:
            element = APIElement(
                id=elem_data['id'],
                name=elem_data['name'],
                qualified_name=elem_data['qualified_name'],
                element_type=APIElementType(elem_data['element_type']),
                visibility=APIVisibility(elem_data.get('visibility', 'public')),
                module_path=elem_data['module_path'],
                file_path=elem_data.get('file_path'),
                signature=elem_data.get('signature'),
                return_type=elem_data.get('return_type'),
                deprecation=elem_data.get('deprecation', 'active'),
                deprecation_message=elem_data.get('deprecation_message'),
                bases=elem_data.get('bases', []),
                parameters=[
                    ParameterInfo(
                        name=p['name'],
                        type_annotation=p.get('type_annotation'),
                        default_value=p.get('default_value')
                    )
                    for p in elem_data.get('parameters', [])
                ]
            )
            elements[element.qualified_name] = element
        
        return elements
    
    def _determine_semver_impact(self, changes: List[APIChange]) -> SemVerImpact:
        """Determine overall semantic version impact."""
        for change in changes:
            if change.semver_impact == SemVerImpact.MAJOR:
                return SemVerImpact.MAJOR
        
        for change in changes:
            if change.semver_impact == SemVerImpact.MINOR:
                return SemVerImpact.MINOR
        
        for change in changes:
            if change.semver_impact == SemVerImpact.PATCH:
                return SemVerImpact.PATCH
        
        return SemVerImpact.NONE
    
    def _calculate_statistics(self, changes: List[APIChange]) -> Dict[str, Any]:
        """Calculate change statistics."""
        stats = {
            'total_changes': len(changes),
            'by_type': {},
            'by_severity': {
                'breaking': 0,
                'warning': 0,
                'info': 0
            },
            'by_element_type': {}
        }
        
        for change in changes:
            # By type
            change_type = change.change_type.value
            stats['by_type'][change_type] = stats['by_type'].get(change_type, 0) + 1
            
            # By severity
            if change.severity == CompatibilityStatus.BREAKING:
                stats['by_severity']['breaking'] += 1
            elif change.severity == CompatibilityStatus.WARNING:
                stats['by_severity']['warning'] += 1
            else:
                stats['by_severity']['info'] += 1
            
            # By element type
            elem_type = change.element_type
            stats['by_element_type'][elem_type] = stats['by_element_type'].get(elem_type, 0) + 1
        
        return stats
    
    def _generate_migration_guide(self, report: APICompatibilityReport) -> str:
        """Generate migration guide for breaking changes."""
        lines = [
            f"# Migration Guide: {report.baseline_version} → {report.target_version}",
            "",
            "## Breaking Changes",
            ""
        ]
        
        for i, change in enumerate(report.breaking_changes, 1):
            lines.extend([
                f"### {i}. {change.element_name}",
                "",
                f"**Type:** {change.change_type.value}",
                f"**Description:** {change.description}",
                ""
            ])
            
            if change.old_signature and change.new_signature:
                lines.extend([
                    "**Before:**",
                    f"```python",
                    change.old_signature,
                    "```",
                    "",
                    "**After:**",
                    f"```python",
                    change.new_signature,
                    "```",
                    ""
                ])
            
            if change.suggestion:
                lines.extend([
                    "**Migration:**",
                    change.suggestion,
                    ""
                ])
            
            lines.append("---")
            lines.append("")
        
        if report.additions:
            lines.extend([
                "## New Features",
                "",
            ])
            for change in report.additions[:10]:
                lines.append(f"- **{change.element_name}**: {change.description}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _save_report(self, report: APICompatibilityReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.analyzed_at.isoformat(),
            'baseline': report.baseline_version,
            'target': report.target_version,
            'compatible': report.is_compatible,
            'breaking_count': len(report.breaking_changes),
            'overall_impact': report.overall_impact.value
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: APICompatibilityReport, 
                      output_path: Optional[Path] = None,
                      format: str = 'json') -> str:
        """Export compatibility report."""
        if format == 'json':
            data = {
                'baseline_version': report.baseline_version,
                'target_version': report.target_version,
                'analyzed_at': report.analyzed_at.isoformat(),
                'is_compatible': report.is_compatible,
                'overall_impact': report.overall_impact.value,
                'statistics': report.statistics,
                'breaking_changes': [
                    {
                        'type': c.change_type.value,
                        'element': c.element_name,
                        'description': c.description,
                        'suggestion': c.suggestion,
                        'location': c.location
                    }
                    for c in report.breaking_changes
                ],
                'warnings': [
                    {
                        'type': c.change_type.value,
                        'element': c.element_name,
                        'description': c.description
                    }
                    for c in report.warnings
                ],
                'additions': [
                    {
                        'element': c.element_name,
                        'description': c.description
                    }
                    for c in report.additions
                ]
            }
            
            if report.migration_guide:
                data['migration_guide'] = report.migration_guide
            
            content = json.dumps(data, indent=2)
            
        elif format == 'markdown':
            lines = [
                f"# API Compatibility Report",
                "",
                f"**Baseline:** {report.baseline_version}",
                f"**Target:** {report.target_version}",
                f"**Compatible:** {'✅ Yes' if report.is_compatible else '❌ No'}",
                f"**SemVer Impact:** {report.overall_impact.value.upper()}",
                "",
                "## Summary",
                "",
                f"- Total Changes: {report.statistics['total_changes']}",
                f"- Breaking: {report.statistics['by_severity']['breaking']}",
                f"- Warnings: {report.statistics['by_severity']['warning']}",
                f"- Additions: {len(report.additions)}",
                ""
            ]
            
            if report.breaking_changes:
                lines.extend([
                    "## ⚠️ Breaking Changes",
                    ""
                ])
                for change in report.breaking_changes:
                    lines.append(f"- **{change.element_name}**: {change.description}")
                lines.append("")
            
            if report.migration_guide:
                lines.append(report.migration_guide)
            
            content = '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def is_compatible(self, report: APICompatibilityReport) -> bool:
        """Check if API is compatible."""
        return report.is_compatible
    
    def get_semver_bump(self, report: APICompatibilityReport) -> str:
        """Get recommended semantic version bump."""
        if report.overall_impact == SemVerImpact.MAJOR:
            return "major"
        elif report.overall_impact == SemVerImpact.MINOR:
            return "minor"
        elif report.overall_impact == SemVerImpact.PATCH:
            return "patch"
        else:
            return "none"
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("APIConsistencyValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for API consistency validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate API consistency")
    parser.add_argument("target", type=Path, help="Target code path")
    parser.add_argument("--baseline", "-b", type=Path, help="Baseline API path")
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--strict", action="store_true", help="Strict mode")
    parser.add_argument("--ignore-private", action="store_true", default=True)
    parser.add_argument("--migration-guide", action="store_true", help="Generate migration guide")
    
    args = parser.parse_args()
    
    config = APIValidatorConfig(
        strict_mode=args.strict,
        ignore_private=args.ignore_private,
        generate_migration_guide=args.migration_guide
    )
    
    validator = APIConsistencyValidator(config)
    
    report = validator.validate(args.target, args.baseline)
    
    output = validator.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    # Summary
    print(f"\n--- Summary ---")
    print(f"Compatible: {'Yes' if report.is_compatible else 'No'}")
    print(f"SemVer Bump: {validator.get_semver_bump(report)}")
    print(f"Breaking Changes: {len(report.breaking_changes)}")
    print(f"Warnings: {len(report.warnings)}")
    print(f"Additions: {len(report.additions)}")
    
    validator.close()


if __name__ == "__main__":
    main()