#!/usr/bin/env python3
"""
Docstring Validator - Validates docstring presence, completeness, and quality.

Part of the Quality tools (validators/docstring_validator.py)

This docstring_validator.py provides:

1. Docstring Presence Checking - Validates modules, classes, functions, and methods have docstrings
2. Multiple Style Support - Google, NumPy, Sphinx, Epydoc, and plain styles
3. Section Completeness - Checks for summary, args, returns, raises, examples sections
4. Parameter Documentation Coverage - Ensures all parameters are documented
5. Readability Scoring - Calculates Flesch-Kincaid style readability
6. Quality Scoring - Overall quality score with letter grade (A-F)
7. Configurable Requirements - Per-entity type and section requirements
8. Style Detection - Automatically detects docstring style
9. Comprehensive Metrics - Word count, sentence count, section coverage
10. Actionable Suggestions - Specific recommendations for improvement
11. Private/Magic Method Control - Configurable ignoring of private and magic methods
12. JSON and Markdown Reports - Multiple export formats

The docstring validator ensures your code is well-documented, improving maintainability and developer experience.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class DocstringStyle(str, Enum):
    """Docstring format style."""
    GOOGLE = "google"
    NUMPY = "numpy"
    SPHINX = "sphinx"
    EPYDOC = "epydoc"
    PLAIN = "plain"
    ANY = "any"


class DocstringSection(str, Enum):
    """Expected docstring sections."""
    SUMMARY = "summary"
    DESCRIPTION = "description"
    ARGS = "args"
    ARGUMENTS = "arguments"
    PARAMETERS = "parameters"
    PARAMS = "params"
    RETURNS = "returns"
    RETURN = "return"
    YIELDS = "yields"
    RAISES = "raises"
    EXCEPTIONS = "exceptions"
    EXAMPLES = "examples"
    EXAMPLE = "example"
    NOTES = "notes"
    NOTE = "note"
    SEE_ALSO = "see_also"
    REFERENCES = "references"
    ATTRIBUTES = "attributes"
    ATTRS = "attrs"
    METHODS = "methods"
    TODO = "todo"
    DEPRECATED = "deprecated"
    WARNING = "warning"
    VERSION = "version"
    AUTHOR = "author"
    SINCE = "since"


class Severity(str, Enum):
    """Severity of docstring issue."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class EntityType(str, Enum):
    """Type of code entity."""
    MODULE = "module"
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    PROPERTY = "property"
    CLASS_METHOD = "class_method"
    STATIC_METHOD = "static_method"
    PACKAGE = "package"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class DocstringIssue:
    """A single docstring issue."""
    issue_type: str
    severity: Severity
    entity_type: EntityType
    entity_name: str
    file_path: str
    line_number: Optional[int] = None
    description: str = ""
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocstringMetrics:
    """Docstring quality metrics for an entity."""
    entity_name: str
    entity_type: EntityType
    file_path: str
    line_number: int = 0
    has_docstring: bool = False
    docstring_length: int = 0
    word_count: int = 0
    sentence_count: int = 0
    has_summary: bool = False
    summary_length: int = 0
    has_args_section: bool = False
    args_documented: int = 0
    args_total: int = 0
    args_coverage: float = 0.0
    has_returns_section: bool = False
    has_raises_section: bool = False
    has_examples: bool = False
    sections_present: List[str] = field(default_factory=list)
    sections_missing: List[str] = field(default_factory=list)
    readability_score: float = 0.0
    quality_score: float = 0.0
    grade: str = "F"


@dataclass
class DocstringReport:
    """Complete docstring validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    
    # Statistics
    total_modules: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_methods: int = 0
    total_entities: int = 0
    
    entities_with_docstrings: int = 0
    docstring_coverage: float = 0.0
    
    # Metrics
    module_metrics: Dict[str, DocstringMetrics] = field(default_factory=dict)
    class_metrics: Dict[str, DocstringMetrics] = field(default_factory=dict)
    function_metrics: Dict[str, DocstringMetrics] = field(default_factory=dict)
    
    # Issues
    issues: List[DocstringIssue] = field(default_factory=list)
    warnings: List[DocstringIssue] = field(default_factory=list)
    
    # Validation
    is_valid: bool = True
    overall_score: float = 0.0
    grade: str = "A"
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocstringValidatorConfig:
    """Configuration for docstring validator."""
    project_root: Path
    
    # Style configuration
    expected_style: DocstringStyle = DocstringStyle.GOOGLE
    enforce_style: bool = False
    
    # Coverage requirements
    require_module_docstring: bool = True
    require_class_docstring: bool = True
    require_function_docstring: bool = True
    require_method_docstring: bool = True
    require_property_docstring: bool = False
    require_private_docstring: bool = False
    require_magic_method_docstring: bool = False
    
    # Content requirements
    require_summary: bool = True
    min_summary_length: int = 10
    require_args_documentation: bool = True
    require_return_documentation: bool = True
    require_raises_documentation: bool = False
    require_examples: bool = False
    min_docstring_length: int = 20
    
    # Quality thresholds
    min_args_coverage: float = 100.0
    min_readability_score: float = 60.0
    min_quality_score: float = 70.0
    
    # Ignore patterns
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "test_*.py", "*_test.py",
        "migrations", "alembic", "setup.py", "conftest.py"
    ])
    
    ignore_names: List[str] = field(default_factory=lambda: [
        "__init__", "__new__", "__del__", "__repr__", "__str__", "__call__",
        "__getattr__", "__setattr__", "__delattr__", "__getitem__", "__setitem__"
    ])
    
    # Validation
    fail_on_error: bool = True
    fail_on_warning: bool = False
    
    # Reporting
    generate_report: bool = True
    output_format: str = "markdown"
    include_suggestions: bool = True


# ============================================================
# DOCSTRING PARSER
# ============================================================

class DocstringParser:
    """Parse and analyze docstrings."""
    
    def __init__(self, config: DocstringValidatorConfig):
        self.config = config
    
    def analyze(self, docstring: Optional[str], entity_type: EntityType,
                parameters: List[str] = None, has_return: bool = False,
                raises: List[str] = None) -> DocstringMetrics:
        """Analyze a docstring and return metrics."""
        metrics = DocstringMetrics(
            entity_name="",
            entity_type=entity_type,
            file_path="",
            has_docstring=docstring is not None and docstring.strip() != ""
        )
        
        if not metrics.has_docstring:
            return metrics
        
        docstring = docstring.strip()
        metrics.docstring_length = len(docstring)
        metrics.word_count = len(docstring.split())
        metrics.sentence_count = len(re.split(r'[.!?]+', docstring))
        
        # Detect style
        detected_style = self._detect_style(docstring)
        metrics.metadata['detected_style'] = detected_style.value
        
        # Parse sections based on detected style
        sections = self._parse_sections(docstring, detected_style)
        metrics.sections_present = list(sections.keys())
        
        # Check summary
        summary = sections.get('summary', '')
        if summary:
            metrics.has_summary = True
            metrics.summary_length = len(summary)
        
        # Check args section
        args_section = (sections.get('args') or sections.get('arguments') or 
                       sections.get('parameters') or sections.get('params'))
        if args_section:
            metrics.has_args_section = True
            if parameters:
                metrics.args_total = len(parameters)
                metrics.args_documented = self._count_documented_args(args_section, parameters)
                if metrics.args_total > 0:
                    metrics.args_coverage = (metrics.args_documented / metrics.args_total) * 100
        
        # Check returns section
        if has_return:
            metrics.has_returns_section = bool(sections.get('returns') or sections.get('return'))
        
        # Check raises section
        if raises:
            metrics.has_raises_section = bool(sections.get('raises') or sections.get('exceptions'))
        
        # Check examples
        metrics.has_examples = bool(sections.get('examples') or sections.get('example'))
        
        # Identify missing sections
        metrics.sections_missing = self._identify_missing_sections(
            metrics, entity_type, parameters, has_return, raises
        )
        
        # Calculate scores
        metrics.readability_score = self._calculate_readability(docstring)
        metrics.quality_score = self._calculate_quality_score(metrics)
        metrics.grade = self._calculate_grade(metrics.quality_score)
        
        return metrics
    
    def _detect_style(self, docstring: str) -> DocstringStyle:
        """Detect the docstring style."""
        docstring_lower = docstring.lower()
        
        # Google style indicators
        if re.search(r'^\s*(args|arguments|parameters|params):\s*$', docstring_lower, re.MULTILINE):
            return DocstringStyle.GOOGLE
        
        # NumPy style indicators
        if re.search(r'^\s*parameters\s*\n\s*[-=]+\s*$', docstring_lower, re.MULTILINE):
            return DocstringStyle.NUMPY
        
        # Sphinx style indicators
        if re.search(r'^:param\s+\w+:', docstring_lower, re.MULTILINE):
            return DocstringStyle.SPHINX
        
        # Epydoc style indicators
        if re.search(r'^@param\s+\w+:', docstring_lower, re.MULTILINE):
            return DocstringStyle.EPYDOC
        
        return DocstringStyle.PLAIN
    
    def _parse_sections(self, docstring: str, style: DocstringStyle) -> Dict[str, str]:
        """Parse docstring into sections."""
        sections = {}
        lines = docstring.split('\n')
        
        if style == DocstringStyle.GOOGLE:
            sections = self._parse_google_style(lines)
        elif style == DocstringStyle.NUMPY:
            sections = self._parse_numpy_style(lines)
        elif style == DocstringStyle.SPHINX:
            sections = self._parse_sphinx_style(lines)
        else:
            # Plain style - treat first line as summary, rest as description
            if lines:
                sections['summary'] = lines[0].strip()
                if len(lines) > 1:
                    sections['description'] = '\n'.join(lines[1:]).strip()
        
        return sections
    
    def _parse_google_style(self, lines: List[str]) -> Dict[str, str]:
        """Parse Google-style docstring."""
        sections = {}
        current_section = 'summary'
        section_content = []
        
        section_headers = {
            'args:', 'arguments:', 'parameters:', 'params:',
            'returns:', 'return:', 'yields:', 'yield:',
            'raises:', 'exceptions:',
            'examples:', 'example:',
            'notes:', 'note:',
            'see also:', 'references:',
            'attributes:', 'attrs:',
            'methods:', 'todo:', 'deprecated:', 'warning:',
            'version:', 'author:', 'since:'
        }
        
        for line in lines:
            stripped = line.strip()
            lower_stripped = stripped.lower()
            
            # Check for section header
            if lower_stripped in section_headers:
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = lower_stripped.rstrip(':')
                section_content = []
            else:
                section_content.append(line)
        
        # Add last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content).strip()
        
        return sections
    
    def _parse_numpy_style(self, lines: List[str]) -> Dict[str, str]:
        """Parse NumPy-style docstring."""
        sections = {}
        current_section = 'summary'
        section_content = []
        in_header = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check for section header (followed by dashes)
            if (i + 1 < len(lines) and 
                re.match(r'^[-=]+$', lines[i + 1].strip()) and
                stripped):
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = stripped.lower()
                section_content = []
                in_header = True
            elif in_header and re.match(r'^[-=]+$', stripped):
                in_header = False
            elif not in_header:
                section_content.append(line)
        
        # Add last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content).strip()
        
        return sections
    
    def _parse_sphinx_style(self, lines: List[str]) -> Dict[str, str]:
        """Parse Sphinx-style docstring."""
        sections = {}
        current_section = 'summary'
        section_content = []
        
        # Extract field lists
        field_pattern = re.compile(r'^:(\w+)(?:\s+(\w+))?:\s*(.*)$')
        fields = defaultdict(list)
        
        for line in lines:
            match = field_pattern.match(line.strip())
            if match:
                field_type = match.group(1)
                field_name = match.group(2)
                field_desc = match.group(3)
                
                if field_type == 'param':
                    fields['params'].append((field_name, field_desc))
                elif field_type == 'type':
                    fields['types'].append((field_name, field_desc))
                elif field_type == 'return':
                    fields['returns'].append(field_desc)
                elif field_type == 'rtype':
                    fields['rtypes'].append(field_desc)
                elif field_type == 'raises':
                    fields['raises'].append((field_name, field_desc))
            else:
                if current_section == 'summary' and not section_content:
                    section_content.append(line)
        
        # Build sections from fields
        if fields['params']:
            sections['params'] = '\n'.join(f"{n}: {d}" for n, d in fields['params'])
        if fields['returns']:
            sections['returns'] = '\n'.join(fields['returns'])
        if fields['raises']:
            sections['raises'] = '\n'.join(f"{n}: {d}" for n, d in fields['raises'])
        
        if section_content:
            sections['summary'] = '\n'.join(section_content).strip()
        
        return sections
    
    def _count_documented_args(self, args_section: str, parameters: List[str]) -> int:
        """Count how many parameters are documented."""
        documented = 0
        args_lower = args_section.lower()
        
        for param in parameters:
            # Look for parameter name in args section
            pattern = rf'\b{re.escape(param)}\s*[:\(]'
            if re.search(pattern, args_lower):
                documented += 1
        
        return documented
    
    def _identify_missing_sections(self, metrics: DocstringMetrics,
                                    entity_type: EntityType,
                                    parameters: List[str],
                                    has_return: bool,
                                    raises: List[str]) -> List[str]:
        """Identify missing required sections."""
        missing = []
        
        if self.config.require_summary and not metrics.has_summary:
            missing.append('summary')
        
        if parameters and self.config.require_args_documentation:
            if not metrics.has_args_section:
                missing.append('args')
            elif metrics.args_coverage < self.config.min_args_coverage:
                missing.append(f'args (coverage: {metrics.args_coverage:.0f}%)')
        
        if has_return and self.config.require_return_documentation:
            if not metrics.has_returns_section:
                missing.append('returns')
        
        if raises and self.config.require_raises_documentation:
            if not metrics.has_raises_section:
                missing.append('raises')
        
        if self.config.require_examples and not metrics.has_examples:
            missing.append('examples')
        
        return missing
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (Flesch-Kincaid style)."""
        # Simplified readability calculation
        sentences = max(1, len(re.split(r'[.!?]+', text)))
        words = text.split()
        word_count = max(1, len(words))
        
        # Average sentence length
        avg_sentence_length = word_count / sentences
        
        # Average word length
        avg_word_length = sum(len(w) for w in words) / word_count
        
        # Simplified score (higher is more readable)
        score = 100 - (avg_sentence_length * 1.5) - (avg_word_length * 5)
        return max(0, min(100, score))
    
    def _calculate_quality_score(self, metrics: DocstringMetrics) -> float:
        """Calculate overall docstring quality score."""
        if not metrics.has_docstring:
            return 0.0
        
        score = 0.0
        max_score = 0.0
        
        # Has summary (20%)
        max_score += 20
        if metrics.has_summary:
            if metrics.summary_length >= self.config.min_summary_length:
                score += 20
            else:
                score += 10
        
        # Has description (10%)
        max_score += 10
        if metrics.word_count > metrics.summary_length // 5 + 10:
            score += 10
        
        # Args documented (30%)
        if metrics.args_total > 0:
            max_score += 30
            score += (metrics.args_coverage / 100) * 30
        
        # Has returns (15%)
        if metrics.has_returns_section:
            max_score += 15
            score += 15
        
        # Has raises (10%)
        if metrics.has_raises_section:
            max_score += 10
            score += 10
        
        # Has examples (15%)
        if metrics.has_examples:
            max_score += 15
            score += 15
        
        # Readability (bonus up to 10)
        score += metrics.readability_score / 10
        
        return min(100, (score / max_score) * 100) if max_score > 0 else 0
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


# ============================================================
# MAIN DOCSTRING VALIDATOR
# ============================================================

class DocstringValidator:
    """
    Validates docstring presence, completeness, and quality.
    
    Features:
    - Check docstring presence for modules, classes, functions
    - Multiple style support (Google, NumPy, Sphinx, Epydoc)
    - Section completeness checking
    - Parameter documentation coverage
    - Readability scoring
    - Quality scoring and grading
    - Configurable requirements per entity type
    - Comprehensive reporting
    """
    
    def __init__(self, config: DocstringValidatorConfig):
        self.config = config
        self.parser = DocstringParser(config)
        self.state = StateManager(config.project_root / ".ai_state" / "docstring_validator.json")
        
        logger.info("DocstringValidator initialized")
    
    def validate(self) -> DocstringReport:
        """Run complete docstring validation."""
        logger.info("Starting docstring validation...")
        
        report = DocstringReport(
            project_name=self.config.project_root.name
        )
        
        # Find Python files
        python_files = list(self.config.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_ignore(file_path):
                continue
            
            try:
                self._validate_file(file_path, report)
            except Exception as e:
                logger.warning(f"Failed to validate {file_path}: {e}")
        
        # Calculate overall statistics
        report.total_entities = (report.total_modules + report.total_classes + 
                                  report.total_functions + report.total_methods)
        
        if report.total_entities > 0:
            report.docstring_coverage = (report.entities_with_docstrings / report.total_entities) * 100
        
        # Calculate overall score and grade
        report.overall_score = self._calculate_overall_score(report)
        report.grade = self._calculate_overall_grade(report.overall_score)
        
        # Determine validity
        report.is_valid = len(report.issues) == 0
        if self.config.fail_on_warning and report.warnings:
            report.is_valid = False
        
        # Generate summary and recommendations
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Docstring validation complete: {report.docstring_coverage:.1f}% coverage")
        
        return report
    
    def _validate_file(self, file_path: Path, report: DocstringReport):
        """Validate a single file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        visitor = DocstringVisitor(file_path, self.config, self.parser, report)
        visitor.visit(tree)
        
        # Add module metrics if available
        if visitor.module_metrics:
            report.module_metrics[str(file_path)] = visitor.module_metrics
            report.total_modules += 1
            if visitor.module_metrics.has_docstring:
                report.entities_with_docstrings += 1
    
    def _calculate_overall_score(self, report: DocstringReport) -> float:
        """Calculate overall docstring score."""
        if report.total_entities == 0:
            return 100.0
        
        # Weighted average of coverage and quality
        coverage_weight = 0.4
        quality_weight = 0.6
        
        coverage_score = report.docstring_coverage
        
        # Average quality score
        all_metrics = (list(report.module_metrics.values()) + 
                      list(report.class_metrics.values()) + 
                      list(report.function_metrics.values()))
        
        if all_metrics:
            quality_score = sum(m.quality_score for m in all_metrics) / len(all_metrics)
        else:
            quality_score = 0.0
        
        score = (coverage_score * coverage_weight) + (quality_score * quality_weight)
        
        # Deduct for issues
        score -= len(report.issues) * 3
        score -= len(report.warnings) * 1
        
        return max(0, min(100, score))
    
    def _calculate_overall_grade(self, score: float) -> str:
        """Calculate overall letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        path_str = str(file_path)
        for pattern in self.config.ignore_patterns:
            if pattern.replace('*', '') in path_str:
                return True
        return False
    
    def _generate_summary(self, report: DocstringReport) -> str:
        """Generate validation summary."""
        if report.is_valid:
            return f"✅ Docstring validation passed. Coverage: {report.docstring_coverage:.1f}% (Grade: {report.grade})"
        else:
            return f"❌ Docstring issues found: {len(report.issues)} issues, {len(report.warnings)} warnings"
    
    def _generate_recommendations(self, report: DocstringReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if report.docstring_coverage < 80:
            recommendations.append(f"Add docstrings to increase coverage from {report.docstring_coverage:.1f}% to at least 80%")
        
        # Find most common missing sections
        missing_summary = sum(1 for m in report.function_metrics.values() if not m.has_summary)
        if missing_summary > 0:
            recommendations.append(f"Add summaries to {missing_summary} functions")
        
        missing_args = sum(1 for m in report.function_metrics.values() 
                          if m.args_total > 0 and m.args_coverage < 100)
        if missing_args > 0:
            recommendations.append(f"Document all parameters for {missing_args} functions")
        
        if report.overall_score < 70:
            recommendations.append("Improve overall docstring quality score")
        
        return recommendations[:5]
    
    def _save_report(self, report: DocstringReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.validated_at.isoformat(),
            'project': report.project_name,
            'is_valid': report.is_valid,
            'coverage': report.docstring_coverage,
            'score': report.overall_score,
            'grade': report.grade,
            'issues': len(report.issues),
            'warnings': len(report.warnings)
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: DocstringReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export docstring report."""
        
        if format == 'json':
            data = {
                'validated_at': report.validated_at.isoformat(),
                'project': report.project_name,
                'is_valid': report.is_valid,
                'coverage': report.docstring_coverage,
                'score': report.overall_score,
                'grade': report.grade,
                'summary': report.summary,
                'statistics': {
                    'total_modules': report.total_modules,
                    'total_classes': report.total_classes,
                    'total_functions': report.total_functions,
                    'total_methods': report.total_methods,
                    'entities_with_docstrings': report.entities_with_docstrings
                },
                'issues': [
                    {
                        'type': i.issue_type,
                        'severity': i.severity.value,
                        'entity': i.entity_name,
                        'file': i.file_path,
                        'description': i.description
                    }
                    for i in report.issues
                ],
                'recommendations': report.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Docstring Validation Report",
                "",
                f"**Project:** {report.project_name}",
                f"**Validated:** {report.validated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Score:** {report.overall_score:.1f} (Grade: {report.grade})",
                f"**Status:** {report.summary}",
                "",
                "## Summary",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Modules | {report.total_modules} |",
                f"| Classes | {report.total_classes} |",
                f"| Functions | {report.total_functions} |",
                f"| Methods | {report.total_methods} |",
                f"| Docstring Coverage | {report.docstring_coverage:.1f}% |",
                f"| Quality Score | {report.overall_score:.1f} |",
                "",
            ]
            
            if report.issues:
                lines.extend([
                    "## ❌ Issues",
                    "",
                    "| Type | Severity | Entity | File | Description |",
                    "|------|----------|--------|------|-------------|",
                ])
                for issue in report.issues[:20]:
                    lines.append(f"| {issue.issue_type} | {issue.severity.value} | {issue.entity_name[:30]} | {Path(issue.file_path).name} | {issue.description[:40]} |")
                lines.append("")
            
            if report.recommendations:
                lines.extend([
                    "## Recommendations",
                    "",
                ])
                for rec in report.recommendations:
                    lines.append(f"- {rec}")
                lines.append("")
            
            content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("DocstringValidator closed")


# ============================================================
# AST VISITOR
# ============================================================

class DocstringVisitor(ast.NodeVisitor):
    """AST visitor for docstring validation."""
    
    def __init__(self, file_path: Path, config: DocstringValidatorConfig,
                 parser: DocstringParser, report: DocstringReport):
        self.file_path = str(file_path)
        self.config = config
        self.parser = parser
        self.report = report
        self.current_class: Optional[str] = None
        self.module_metrics: Optional[DocstringMetrics] = None
    
    def visit_Module(self, node: ast.Module):
        """Visit module."""
        docstring = ast.get_docstring(node)
        
        metrics = self.parser.analyze(
            docstring=docstring,
            entity_type=EntityType.MODULE,
            parameters=[],
            has_return=False
        )
        metrics.entity_name = Path(self.file_path).stem
        metrics.file_path = self.file_path
        metrics.line_number = 1
        
        self.module_metrics = metrics
        
        # Check module docstring requirement
        if self.config.require_module_docstring and not metrics.has_docstring:
            issue = DocstringIssue(
                issue_type="missing_module_docstring",
                severity=Severity.ERROR if self.config.fail_on_error else Severity.WARNING,
                entity_type=EntityType.MODULE,
                entity_name=metrics.entity_name,
                file_path=self.file_path,
                description="Module missing docstring",
                suggestion="Add a module-level docstring describing the module's purpose"
            )
            self._add_issue(issue)
        
        self._check_metrics(metrics)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        if self._should_ignore_entity(node.name):
            self.generic_visit(node)
            return
        
        docstring = ast.get_docstring(node)
        prev_class = self.current_class
        self.current_class = node.name
        
        # Get method names in class
        methods = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not self._should_ignore_entity(child.name):
                    methods.append(child.name)
        
        metrics = self.parser.analyze(
            docstring=docstring,
            entity_type=EntityType.CLASS,
            parameters=[],
            has_return=False
        )
        metrics.entity_name = node.name
        metrics.file_path = self.file_path
        metrics.line_number = node.lineno
        metrics.metadata['methods'] = methods
        
        self.report.class_metrics[f"{self.file_path}:{node.name}"] = metrics
        self.report.total_classes += 1
        if metrics.has_docstring:
            self.report.entities_with_docstrings += 1
        
        # Check class docstring requirement
        if self.config.require_class_docstring and not metrics.has_docstring:
            issue = DocstringIssue(
                issue_type="missing_class_docstring",
                severity=Severity.ERROR if self.config.fail_on_error else Severity.WARNING,
                entity_type=EntityType.CLASS,
                entity_name=node.name,
                file_path=self.file_path,
                line_number=node.lineno,
                description=f"Class '{node.name}' missing docstring",
                suggestion=f"Add a docstring describing the purpose of class '{node.name}'"
            )
            self._add_issue(issue)
        
        self._check_metrics(metrics)
        self.generic_visit(node)
        self.current_class = prev_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_function(node, is_async=False)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_function(node, is_async=True)
    
    def _visit_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool):
        """Visit function definition."""
        if self._should_ignore_entity(node.name):
            self.generic_visit(node)
            return
        
        entity_type = EntityType.METHOD if self.current_class else EntityType.FUNCTION
        if self.current_class:
            if node.name in self.config.ignore_names:
                if not self.config.require_magic_method_docstring:
                    self.generic_visit(node)
                    return
            elif not self.config.require_method_docstring:
                self.generic_visit(node)
                return
        elif not self.config.require_function_docstring:
            self.generic_visit(node)
            return
        
        docstring = ast.get_docstring(node)
        
        # Extract parameters
        parameters = [arg.arg for arg in node.args.args]
        if node.args.vararg:
            parameters.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            parameters.append(f"**{node.args.kwarg.arg}")
        
        # Check if has return
        has_return = self._has_return(node)
        
        # Extract raises
        raises = self._extract_raises(node)
        
        metrics = self.parser.analyze(
            docstring=docstring,
            entity_type=entity_type,
            parameters=parameters,
            has_return=has_return,
            raises=raises
        )
        
        entity_name = f"{self.current_class}.{node.name}" if self.current_class else node.name
        metrics.entity_name = entity_name
        metrics.file_path = self.file_path
        metrics.line_number = node.lineno
        
        if entity_type == EntityType.FUNCTION:
            self.report.function_metrics[f"{self.file_path}:{entity_name}"] = metrics
            self.report.total_functions += 1
        else:
            self.report.total_methods += 1
        
        if metrics.has_docstring:
            self.report.entities_with_docstrings += 1
        
        # Check function docstring requirement
        if not metrics.has_docstring:
            issue = DocstringIssue(
                issue_type="missing_function_docstring",
                severity=Severity.ERROR if self.config.fail_on_error else Severity.WARNING,
                entity_type=entity_type,
                entity_name=entity_name,
                file_path=self.file_path,
                line_number=node.lineno,
                description=f"{entity_type.value} '{entity_name}' missing docstring",
                suggestion=f"Add a docstring describing the {entity_type.value}"
            )
            self._add_issue(issue)
        
        self._check_metrics(metrics)
        self.generic_visit(node)
    
    def _has_return(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool:
        """Check if function has return statements."""
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                return True
        return False
    
    def _extract_raises(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[str]:
        """Extract raised exceptions from function."""
        raises = []
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                if child.exc:
                    if isinstance(child.exc, ast.Call):
                        if isinstance(child.exc.func, ast.Name):
                            raises.append(child.exc.func.id)
                    elif isinstance(child.exc, ast.Name):
                        raises.append(child.exc.id)
        return list(set(raises))
    
    def _check_metrics(self, metrics: DocstringMetrics):
        """Check metrics against thresholds."""
        if not metrics.has_docstring:
            return
        
        # Check summary
        if self.config.require_summary and not metrics.has_summary:
            issue = DocstringIssue(
                issue_type="missing_summary",
                severity=Severity.WARNING,
                entity_type=metrics.entity_type,
                entity_name=metrics.entity_name,
                file_path=self.file_path,
                line_number=metrics.line_number,
                description=f"Docstring missing summary line",
                suggestion="Add a one-line summary as the first line of the docstring"
            )
            self._add_issue(issue, is_warning=True)
        
        elif (metrics.has_summary and 
              metrics.summary_length < self.config.min_summary_length):
            issue = DocstringIssue(
                issue_type="summary_too_short",
                severity=Severity.INFO,
                entity_type=metrics.entity_type,
                entity_name=metrics.entity_name,
                file_path=self.file_path,
                line_number=metrics.line_number,
                description=f"Summary too short ({metrics.summary_length} chars, min {self.config.min_summary_length})",
                suggestion="Expand the summary to be more descriptive"
            )
            self._add_issue(issue, is_warning=True)
        
        # Check args documentation
        if (metrics.args_total > 0 and 
            metrics.args_coverage < self.config.min_args_coverage):
            issue = DocstringIssue(
                issue_type="incomplete_args",
                severity=Severity.WARNING,
                entity_type=metrics.entity_type,
                entity_name=metrics.entity_name,
                file_path=self.file_path,
                line_number=metrics.line_number,
                description=f"Only {metrics.args_documented}/{metrics.args_total} parameters documented",
                suggestion=f"Document all {metrics.args_total} parameters in the docstring"
            )
            self._add_issue(issue, is_warning=True)
        
        # Check quality score
        if metrics.quality_score < self.config.min_quality_score:
            issue = DocstringIssue(
                issue_type="low_quality",
                severity=Severity.INFO,
                entity_type=metrics.entity_type,
                entity_name=metrics.entity_name,
                file_path=self.file_path,
                line_number=metrics.line_number,
                description=f"Docstring quality score {metrics.quality_score:.0f}% (min {self.config.min_quality_score}%)",
                suggestion="Improve docstring by adding missing sections and more detail"
            )
            self._add_issue(issue, is_warning=True)
    
    def _should_ignore_entity(self, name: str) -> bool:
        """Check if entity should be ignored."""
        if name.startswith('_') and not self.config.require_private_docstring:
            return True
        if name in self.config.ignore_names:
            return True
        return False
    
    def _add_issue(self, issue: DocstringIssue, is_warning: bool = False):
        """Add an issue to the report."""
        if issue.severity == Severity.ERROR or not is_warning:
            self.report.issues.append(issue)
        else:
            self.report.warnings.append(issue)


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for docstring validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate docstrings in Python code")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--style", choices=[s.value for s in DocstringStyle],
                       default=DocstringStyle.GOOGLE.value)
    parser.add_argument("--enforce-style", action="store_true")
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--include-private", action="store_true")
    parser.add_argument("--min-coverage", type=float, default=80.0)
    
    args = parser.parse_args()
    
    config = DocstringValidatorConfig(
        project_root=args.project_root,
        expected_style=DocstringStyle(args.style),
        enforce_style=args.enforce_style,
        fail_on_warning=args.fail_on_warning,
        require_private_docstring=args.include_private
    )
    
    validator = DocstringValidator(config)
    
    report = validator.validate()
    
    output = validator.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    
    if config.fail_on_error and not report.is_valid:
        exit(1)
    
    validator.close()


if __name__ == "__main__":
    main()