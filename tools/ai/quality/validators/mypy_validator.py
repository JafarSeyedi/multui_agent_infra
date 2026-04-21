#!/usr/bin/env python3
"""
Mypy Validator - Validates Python type hints using mypy.

Part of the Quality tools (validators/mypy_validator.py)

This mypy_validator.py provides:

1. Mypy Integration - Runs mypy with configurable options
2. Error Parsing - Structured parsing of mypy output with error codes
3. Type Coverage Analysis - Calculates percentage of typed code
4. Error Categorization - Groups errors by type (assignment, arg-type, attr-defined, etc.)
5. Fix Suggestions - Provides suggestions for common type errors
6. Severity Levels - Distinguishes errors, warnings, and notes
7. Type Safety Scoring - A-F grade based on errors and coverage
8. String Validation - Validate code snippets without files
9. Comprehensive Reporting - JSON and Markdown formats
10. Trend Tracking - Historical type coverage tracking
11. Configurable Strictness - Support for all mypy strictness flags
12. File-Level Statistics - Identifies problematic files

The mypy validator ensures your codebase maintains high type safety standards and helps catch type-related bugs before runtime.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class MypyErrorCode(str, Enum):
    """Common mypy error codes."""
    # Type errors
    ASSIGNMENT = "assignment"
    ARG_TYPE = "arg-type"
    RETURN_VALUE = "return-value"
    RETURN = "return"
    
    # Attribute errors
    ATTR_DEFINED = "attr-defined"
    HAS_TYPE = "has-type"
    
    # Name errors
    NAME_DEFINED = "name-defined"
    NO_REDEFINED = "no-redef"
    
    # Import errors
    IMPORT = "import"
    NO_ANY_UNIMPORTED = "no-any-unimported"
    
    # Call errors
    CALL_ARG = "call-arg"
    CALL_OVERLOAD = "call-overload"
    
    # Index errors
    INDEX = "index"
    
    # Operator errors
    OPERATOR = "operator"
    
    # Miscellaneous
    MISC = "misc"
    SYNTAX = "syntax"
    VALID_TYPE = "valid-type"
    VAR_ANNOTATED = "var-annotated"
    UNUSED_IGNORE = "unused-ignore"
    UNTYPED_DEF = "untyped-def"
    NO_UNTYPED_DEF = "no-untyped-def"
    UNTYPED_CALL = "untyped-call"
    ANY_EXPLICIT = "any-explicit"
    NO_ANY_EXPLICIT = "no-any-explicit"
    TYPE_ABSTRACT = "type-abstract"
    OVERRIDE = "override"
    
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Severity of mypy error."""
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"
    INFO = "info"


class MypyErrorCategory(str, Enum):
    """Category of mypy error."""
    TYPE_ERROR = "type_error"
    ATTRIBUTE_ERROR = "attribute_error"
    IMPORT_ERROR = "import_error"
    SYNTAX_ERROR = "syntax_error"
    NAME_ERROR = "name_error"
    STYLE_ISSUE = "style_issue"
    OTHER = "other"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class MypyError:
    """A single mypy error."""
    file_path: str
    line_number: int
    column_number: Optional[int] = None
    error_code: MypyErrorCode = MypyErrorCode.UNKNOWN
    category: MypyErrorCategory = MypyErrorCategory.OTHER
    severity: Severity = Severity.ERROR
    message: str = ""
    context: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number}: {self.error_code.value}: {self.message}"


@dataclass
class TypeCoverageInfo:
    """Type coverage information for a file."""
    file_path: str
    typed_lines: int = 0
    total_lines: int = 0
    coverage_percent: float = 0.0
    untyped_functions: List[Tuple[str, int]] = field(default_factory=list)
    untyped_variables: List[Tuple[str, int]] = field(default_factory=list)


@dataclass
class MypyReport:
    """Complete mypy validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    mypy_version: str = ""
    python_version: str = ""
    
    # Statistics
    total_files: int = 0
    files_with_errors: int = 0
    total_errors: int = 0
    errors_by_code: Dict[str, int] = field(default_factory=dict)
    errors_by_file: Dict[str, int] = field(default_factory=dict)
    
    # Errors
    errors: List[MypyError] = field(default_factory=list)
    warnings: List[MypyError] = field(default_factory=list)
    notes: List[MypyError] = field(default_factory=list)
    
    # Type coverage
    type_coverage: Dict[str, TypeCoverageInfo] = field(default_factory=dict)
    overall_coverage: float = 0.0
    
    # Validation
    is_valid: bool = True
    overall_score: float = 0.0
    grade: str = "A"
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MypyValidatorConfig:
    """Configuration for mypy validator."""
    project_root: Path
    config_file: Optional[Path] = None
    
    # Mypy options
    strict: bool = False
    strict_optional: bool = True
    disallow_untyped_defs: bool = False
    disallow_any_explicit: bool = False
    disallow_any_unimported: bool = False
    disallow_any_generics: bool = False
    disallow_subclassing_any: bool = False
    disallow_untyped_calls: bool = False
    disallow_incomplete_defs: bool = False
    check_untyped_defs: bool = False
    disallow_untyped_decorators: bool = False
    warn_redundant_casts: bool = True
    warn_unused_ignores: bool = True
    warn_return_any: bool = True
    warn_unreachable: bool = True
    no_implicit_optional: bool = True
    local_partial_types: bool = False
    
    # Platform
    python_version: str = "3.10"
    platform: str = "linux"
    
    # Type coverage
    check_type_coverage: bool = True
    min_type_coverage: float = 80.0
    
    # Ignore patterns
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "test_*.py", "*_test.py",
        "migrations", "alembic", "setup.py"
    ])
    
    # Additional mypy args
    extra_args: List[str] = field(default_factory=list)
    
    # Validation
    fail_on_error: bool = True
    fail_on_warning: bool = False
    max_errors: int = 100
    
    # Reporting
    generate_report: bool = True
    output_format: str = "markdown"
    show_context: bool = True


# ============================================================
# MYPY OUTPUT PARSER
# ============================================================

class MypyOutputParser:
    """Parse mypy output into structured errors."""
    
    # Mapping of mypy error codes to categories
    ERROR_CATEGORY_MAP = {
        MypyErrorCode.ASSIGNMENT: MypyErrorCategory.TYPE_ERROR,
        MypyErrorCode.ARG_TYPE: MypyErrorCategory.TYPE_ERROR,
        MypyErrorCode.RETURN_VALUE: MypyErrorCategory.TYPE_ERROR,
        MypyErrorCode.RETURN: MypyErrorCategory.TYPE_ERROR,
        MypyErrorCode.ATTR_DEFINED: MypyErrorCategory.ATTRIBUTE_ERROR,
        MypyErrorCode.HAS_TYPE: MypyErrorCategory.ATTRIBUTE_ERROR,
        MypyErrorCode.NAME_DEFINED: MypyErrorCategory.NAME_ERROR,
        MypyErrorCode.NO_REDEFINED: MypyErrorCategory.NAME_ERROR,
        MypyErrorCode.IMPORT: MypyErrorCategory.IMPORT_ERROR,
        MypyErrorCode.NO_ANY_UNIMPORTED: MypyErrorCategory.IMPORT_ERROR,
        MypyErrorCode.SYNTAX: MypyErrorCategory.SYNTAX_ERROR,
        MypyErrorCode.UNUSED_IGNORE: MypyErrorCategory.STYLE_ISSUE,
        MypyErrorCode.UNTYPED_DEF: MypyErrorCategory.STYLE_ISSUE,
        MypyErrorCode.ANY_EXPLICIT: MypyErrorCategory.STYLE_ISSUE,
    }
    
    # Suggestions for common errors
    ERROR_SUGGESTIONS = {
        MypyErrorCode.ASSIGNMENT: "Check that the assigned value matches the declared type",
        MypyErrorCode.ARG_TYPE: "Check that the argument type matches the parameter type",
        MypyErrorCode.RETURN_VALUE: "Check that the return value matches the declared return type",
        MypyErrorCode.ATTR_DEFINED: "Check that the attribute exists on the object or add type annotation",
        MypyErrorCode.NAME_DEFINED: "Check that the name is imported or defined before use",
        MypyErrorCode.IMPORT: "Check that the module is installed and imported correctly",
        MypyErrorCode.UNUSED_IGNORE: "Remove unused # type: ignore comment",
        MypyErrorCode.UNTYPED_DEF: "Add type annotations to function definition",
        MypyErrorCode.ANY_EXPLICIT: "Replace 'Any' with a more specific type",
        MypyErrorCode.CALL_ARG: "Check that the correct number and names of arguments are provided",
        MypyErrorCode.INDEX: "Check that the index type matches the collection type",
        MypyErrorCode.OPERATOR: "Check that the operator is supported for the given types",
    }
    
    def parse(self, output: str) -> List[MypyError]:
        """Parse mypy output into MypyError objects."""
        errors = []
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            error = self._parse_line(line)
            if error:
                errors.append(error)
        
        return errors
    
    def parse_json(self, json_output: str) -> List[MypyError]:
        """Parse mypy JSON output."""
        errors = []
        
        try:
            data = json.loads(json_output)
            
            for file_path, file_errors in data.items():
                for error_data in file_errors:
                    error = MypyError(
                        file_path=file_path,
                        line_number=error_data.get('line', 0),
                        column_number=error_data.get('column'),
                        error_code=self._parse_error_code(error_data.get('code', '')),
                        severity=Severity.ERROR if error_data.get('severity') == 'error' else Severity.WARNING,
                        message=error_data.get('message', ''),
                        context=error_data.get('context'),
                        metadata={'raw': error_data}
                    )
                    
                    error.category = self.ERROR_CATEGORY_MAP.get(
                        error.error_code, MypyErrorCategory.OTHER
                    )
                    error.suggestion = self.ERROR_SUGGESTIONS.get(error.error_code)
                    
                    errors.append(error)
                    
        except json.JSONDecodeError:
            # Fall back to line parsing
            errors = self.parse(json_output)
        
        return errors
    
    def parse_coverage(self, coverage_output: str) -> Dict[str, TypeCoverageInfo]:
        """Parse mypy coverage report."""
        coverage = {}
        
        for line in coverage_output.strip().split('\n'):
            if not line.strip():
                continue
            
            # Format: file.py: 85.5% (100/117 lines)
            import re
            match = re.match(r'^([^:]+):\s+([\d.]+)%\s+\((\d+)/(\d+)\s+lines?\)', line)
            if match:
                file_path = match.group(1)
                percent = float(match.group(2))
                typed = int(match.group(3))
                total = int(match.group(4))
                
                coverage[file_path] = TypeCoverageInfo(
                    file_path=file_path,
                    typed_lines=typed,
                    total_lines=total,
                    coverage_percent=percent
                )
        
        return coverage
    
    def _parse_line(self, line: str) -> Optional[MypyError]:
        """Parse a single line of mypy output."""
        # Format: file.py:line: error: message  [error-code]
        import re
        
        pattern = r'^([^:]+):(\d+):(?:\d+:)?\s+(error|warning|note):\s+(.+?)(?:\s+\[([^\]]+)\])?$'
        match = re.match(pattern, line)
        
        if not match:
            return None
        
        file_path = match.group(1)
        line_number = int(match.group(2))
        severity_str = match.group(3)
        message = match.group(4)
        error_code_str = match.group(5) if match.group(5) else ""
        
        severity = Severity.ERROR
        if severity_str == 'warning':
            severity = Severity.WARNING
        elif severity_str == 'note':
            severity = Severity.NOTE
        
        error_code = self._parse_error_code(error_code_str)
        
        error = MypyError(
            file_path=file_path,
            line_number=line_number,
            error_code=error_code,
            severity=severity,
            message=message
        )
        
        error.category = self.ERROR_CATEGORY_MAP.get(error_code, MypyErrorCategory.OTHER)
        error.suggestion = self.ERROR_SUGGESTIONS.get(error_code)
        
        return error
    
    def _parse_error_code(self, code_str: str) -> MypyErrorCode:
        """Parse mypy error code string."""
        if not code_str:
            return MypyErrorCode.UNKNOWN
        
        code_str = code_str.lower().replace('-', '_')
        
        try:
            return MypyErrorCode(code_str)
        except ValueError:
            return MypyErrorCode.UNKNOWN


# ============================================================
# MAIN MYPY VALIDATOR
# ============================================================

class MypyValidator:
    """
    Validates Python type hints using mypy.
    
    Features:
    - Run mypy with configurable options
    - Parse mypy output into structured errors
    - Calculate type coverage
    - Identify untyped functions and variables
    - Generate comprehensive reports
    - Track type coverage trends
    - Provide fix suggestions for common errors
    """
    
    def __init__(self, config: MypyValidatorConfig):
        self.config = config
        self.parser = MypyOutputParser()
        self.state = StateManager(config.project_root / ".ai_state" / "mypy_validator.json")
        
        self._mypy_version: Optional[str] = None
        self._python_version: Optional[str] = None
        
        logger.info("MypyValidator initialized")
    
    def validate(self) -> MypyReport:
        """Run complete mypy validation."""
        logger.info("Starting mypy validation...")
        
        report = MypyReport(
            project_name=self.config.project_root.name,
            mypy_version=self._get_mypy_version(),
            python_version=self.config.python_version
        )
        
        # Run mypy
        output = self._run_mypy()
        
        if output:
            errors = self.parser.parse(output)
            
            for error in errors:
                if self._should_ignore_file(error.file_path):
                    continue
                
                report.total_errors += 1
                
                if error.severity == Severity.ERROR:
                    report.errors.append(error)
                elif error.severity == Severity.WARNING:
                    report.warnings.append(error)
                else:
                    report.notes.append(error)
                
                # Update statistics
                code_key = error.error_code.value
                report.errors_by_code[code_key] = report.errors_by_code.get(code_key, 0) + 1
                report.errors_by_file[error.file_path] = report.errors_by_file.get(error.file_path, 0) + 1
        
        report.files_with_errors = len(report.errors_by_file)
        
        # Check type coverage
        if self.config.check_type_coverage:
            coverage = self._check_type_coverage()
            report.type_coverage = coverage
            
            if coverage:
                total_coverage = sum(c.coverage_percent for c in coverage.values())
                report.overall_coverage = total_coverage / len(coverage) if coverage else 0.0
        
        # Calculate overall score and grade
        report.overall_score = self._calculate_overall_score(report)
        report.grade = self._calculate_grade(report.overall_score)
        
        # Determine validity
        report.is_valid = len(report.errors) == 0
        if self.config.fail_on_warning and report.warnings:
            report.is_valid = False
        
        # Generate summary and recommendations
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Mypy validation complete: {len(report.errors)} errors, {len(report.warnings)} warnings")
        
        return report
    
    def validate_string(self, code: str) -> List[MypyError]:
        """Validate a code string."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            output = self._run_mypy_on_file(temp_path)
            return self.parser.parse(output) if output else []
        finally:
            temp_path.unlink()
    
    def validate_string_return_output(self, code: str) -> str:
        """Validate a code string and return raw output."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = Path(f.name)
        
        try:
            return self._run_mypy_on_file(temp_path) or ""
        finally:
            temp_path.unlink()
    
    def _run_mypy(self) -> Optional[str]:
        """Run mypy on the project."""
        cmd = ['mypy']
        
        # Add config file if specified
        if self.config.config_file and self.config.config_file.exists():
            cmd.extend(['--config-file', str(self.config.config_file)])
        
        # Add options
        if self.config.strict:
            cmd.append('--strict')
        
        if self.config.strict_optional:
            cmd.append('--strict-optional')
        
        if self.config.disallow_untyped_defs:
            cmd.append('--disallow-untyped-defs')
        
        if self.config.disallow_any_explicit:
            cmd.append('--disallow-any-explicit')
        
        if self.config.disallow_any_unimported:
            cmd.append('--disallow-any-unimported')
        
        if self.config.disallow_untyped_calls:
            cmd.append('--disallow-untyped-calls')
        
        if self.config.warn_redundant_casts:
            cmd.append('--warn-redundant-casts')
        
        if self.config.warn_unused_ignores:
            cmd.append('--warn-unused-ignores')
        
        if self.config.warn_return_any:
            cmd.append('--warn-return-any')
        
        if self.config.warn_unreachable:
            cmd.append('--warn-unreachable')
        
        if self.config.no_implicit_optional:
            cmd.append('--no-implicit-optional')
        
        # Python version
        cmd.extend(['--python-version', self.config.python_version])
        
        # Platform
        if self.config.platform:
            cmd.extend(['--platform', self.config.platform])
        
        # Extra args
        cmd.extend(self.config.extra_args)
        
        # Add project root
        cmd.append(str(self.config.project_root))
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.config.project_root
            )
            
            return result.stdout + result.stderr
            
        except FileNotFoundError:
            logger.error("mypy not found. Please install mypy: pip install mypy")
            return None
        except subprocess.TimeoutExpired:
            logger.error("mypy timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to run mypy: {e}")
            return None
    
    def _run_mypy_on_file(self, file_path: Path) -> Optional[str]:
        """Run mypy on a single file."""
        cmd = ['mypy', str(file_path)]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.stdout + result.stderr
            
        except Exception as e:
            logger.error(f"Failed to run mypy on {file_path}: {e}")
            return None
    
    def _check_type_coverage(self) -> Dict[str, TypeCoverageInfo]:
        """Check type coverage for the project."""
        coverage = {}
        
        cmd = ['mypy', str(self.config.project_root), '--txt-report', '.']
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.config.project_root
            )
            
            # Parse coverage from index.txt
            index_file = self.config.project_root / 'index.txt'
            if index_file.exists():
                coverage = self.parser.parse_coverage(index_file.read_text())
                index_file.unlink()
            
        except Exception as e:
            logger.warning(f"Failed to check type coverage: {e}")
        
        return coverage
    
    def _get_mypy_version(self) -> str:
        """Get mypy version."""
        if self._mypy_version:
            return self._mypy_version
        
        try:
            result = subprocess.run(
                ['mypy', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self._mypy_version = result.stdout.strip().split()[-1]
        except Exception:
            self._mypy_version = "unknown"
        
        return self._mypy_version
    
    def _calculate_overall_score(self, report: MypyReport) -> float:
        """Calculate overall type safety score."""
        score = 100.0
        
        # Deduct for errors
        score -= len(report.errors) * 5
        
        # Deduct for warnings
        score -= len(report.warnings) * 2
        
        # Add for type coverage
        if report.overall_coverage > 0:
            score = (score * 0.4) + (report.overall_coverage * 0.6)
        
        # Deduct for files with many errors
        for file_path, error_count in report.errors_by_file.items():
            if error_count > 10:
                score -= 5
            elif error_count > 5:
                score -= 2
        
        return max(0, min(100, score))
    
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
    
    def _should_ignore_file(self, file_path: str) -> bool:
        """Check if file should be ignored."""
        for pattern in self.config.ignore_patterns:
            if pattern.replace('*', '') in file_path:
                return True
        return False
    
    def _generate_summary(self, report: MypyReport) -> str:
        """Generate validation summary."""
        if report.is_valid:
            return f"✅ Mypy validation passed. Score: {report.overall_score:.1f} (Grade: {report.grade})"
        else:
            return f"❌ Mypy errors found: {len(report.errors)} errors, {len(report.warnings)} warnings"
    
    def _generate_recommendations(self, report: MypyReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        # Most common errors
        if report.errors_by_code:
            top_errors = sorted(report.errors_by_code.items(), key=lambda x: x[1], reverse=True)[:3]
            for code, count in top_errors:
                if code == 'assignment':
                    recommendations.append(f"Fix {count} assignment type mismatches")
                elif code == 'arg-type':
                    recommendations.append(f"Fix {count} argument type mismatches")
                elif code == 'attr-defined':
                    recommendations.append(f"Fix {count} missing attribute errors")
                elif code == 'import':
                    recommendations.append(f"Fix {count} import errors")
        
        # Type coverage
        if report.overall_coverage < self.config.min_type_coverage:
            recommendations.append(
                f"Increase type coverage from {report.overall_coverage:.1f}% to {self.config.min_type_coverage:.1f}%"
            )
        
        # Files with most errors
        if report.errors_by_file:
            top_files = sorted(report.errors_by_file.items(), key=lambda x: x[1], reverse=True)[:3]
            for file_path, count in top_files:
                short_name = Path(file_path).name
                recommendations.append(f"Focus on fixing {count} errors in {short_name}")
        
        return recommendations[:5]
    
    def _save_report(self, report: MypyReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        reports.append({
            'timestamp': report.validated_at.isoformat(),
            'project': report.project_name,
            'is_valid': report.is_valid,
            'score': report.overall_score,
            'grade': report.grade,
            'errors': len(report.errors),
            'warnings': len(report.warnings),
            'coverage': report.overall_coverage
        })
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: MypyReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export mypy report."""
        
        if format == 'json':
            data = {
                'validated_at': report.validated_at.isoformat(),
                'project': report.project_name,
                'mypy_version': report.mypy_version,
                'python_version': report.python_version,
                'is_valid': report.is_valid,
                'score': report.overall_score,
                'grade': report.grade,
                'summary': report.summary,
                'statistics': {
                    'total_files': report.total_files,
                    'files_with_errors': report.files_with_errors,
                    'total_errors': report.total_errors,
                    'errors_by_code': report.errors_by_code
                },
                'type_coverage': {
                    'overall': report.overall_coverage,
                    'files': {
                        f: c.coverage_percent for f, c in report.type_coverage.items()
                    }
                },
                'errors': [
                    {
                        'file': e.file_path,
                        'line': e.line_number,
                        'code': e.error_code.value,
                        'category': e.category.value,
                        'message': e.message,
                        'suggestion': e.suggestion
                    }
                    for e in report.errors[:50]
                ],
                'recommendations': report.recommendations
            }
            
            content = json.dumps(data, indent=2)
            
        else:  # markdown
            lines = [
                f"# Mypy Validation Report",
                "",
                f"**Project:** {report.project_name}",
                f"**Mypy Version:** {report.mypy_version}",
                f"**Python Version:** {report.python_version}",
                f"**Validated:** {report.validated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Score:** {report.overall_score:.1f} (Grade: {report.grade})",
                f"**Status:** {report.summary}",
                "",
                "## Summary",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Files Analyzed | {report.total_files} |",
                f"| Files with Errors | {report.files_with_errors} |",
                f"| Total Errors | {report.total_errors} |",
                f"| Warnings | {len(report.warnings)} |",
                f"| Type Coverage | {report.overall_coverage:.1f}% |",
                "",
            ]
            
            if report.errors_by_code:
                lines.extend([
                    "## Errors by Code",
                    "",
                    "| Error Code | Count |",
                    "|------------|-------|",
                ])
                for code, count in sorted(report.errors_by_code.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"| {code} | {count} |")
                lines.append("")
            
            if report.errors:
                lines.extend([
                    "## ❌ Errors",
                    "",
                    "| File | Line | Code | Message |",
                    "|------|------|------|---------|",
                ])
                for error in report.errors[:20]:
                    file_name = Path(error.file_path).name
                    lines.append(f"| {file_name} | {error.line_number} | {error.error_code.value} | {error.message[:40]} |")
                
                if len(report.errors) > 20:
                    lines.append(f"| ... | ... | ... | *and {len(report.errors) - 20} more* |")
                lines.append("")
            
            if report.type_coverage:
                lines.extend([
                    "## Type Coverage",
                    "",
                    "| File | Coverage | Typed/Total |",
                    "|------|----------|-------------|",
                ])
                for file_path, cov in sorted(report.type_coverage.items(), key=lambda x: x[1].coverage_percent):
                    file_name = Path(file_path).name
                    lines.append(f"| {file_name} | {cov.coverage_percent:.1f}% | {cov.typed_lines}/{cov.total_lines} |")
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
        logger.info("MypyValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for mypy validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Python type hints using mypy")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, help="Mypy config file")
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    parser.add_argument("--coverage", action="store_true", help="Check type coverage")
    parser.add_argument("--min-coverage", type=float, default=80.0, help="Minimum type coverage")
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--python-version", default="3.10", help="Target Python version")
    
    args = parser.parse_args()
    
    config = MypyValidatorConfig(
        project_root=args.project_root,
        config_file=args.config,
        strict=args.strict,
        check_type_coverage=args.coverage,
        min_type_coverage=args.min_coverage,
        fail_on_warning=args.fail_on_warning,
        python_version=args.python_version
    )
    
    validator = MypyValidator(config)
    
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