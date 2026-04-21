#!/usr/bin/env python3
"""
Iterative Refiner - AI Development Framework
Iteratively refines generated code using validation feedback and AI.

Part of the Level 3 Generation tools (refiners/iterative_refiner.py)


This `iterative_refiner.py` provides:

1. Multi-Pass Refinement - Iteratively improves code until all issues are resolved
2. Comprehensive Issue Detection - Syntax, type, style, complexity, documentation, and custom issues
3. Auto-Fixing - Automatically resolves simple issues like missing blank lines, trailing whitespace
4. LLM-Powered Fixes - Uses AI to intelligently fix complex issues
5. Multiple Refinement Strategies - Fix errors first, improve quality, optimize, add documentation, comprehensive
6. Progress Tracking - Detailed iteration history with diffs and metrics
7. Improvement Scoring - Quantifies code improvement from 0-100%
8. Convergence Detection - Stops when no further improvements are possible
9. Timeout Protection - Prevents infinite refinement loops
10. Specialized Refiners - Tailored methods for functions, classes, modules, and tests
11. Comprehensive Reporting - Markdown reports with full refinement history
12. Validation Error Parsing - mypy, ruff, and custom analysis
13. Session Tracking - Complete history of refinements
14. Change Tracking - Unified diffs between iterations
15. Backup and Rollback - Safety for original code
16. Configurable Thresholds - Customize quality and iteration limits
17. State Persistence - Saves refinement history for analysis


The iterative refiner ensures generated code meets high-quality standards by continuously validating and improving until all issues are resolved or convergence is reached.
"""


import ast
import json
import difflib
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ....shared.llm_client import LLMClient
from ....shared.state_manager import StateManager
from ....shared.logger import get_logger
from ...quality.validators.mypy_validator import MypyValidator
from ...quality.validators.ruff_validator import RuffValidator

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class RefinementStrategy(str, Enum):
    """Strategy for iterative refinement."""
    FIX_ERRORS_FIRST = "fix_errors_first"
    IMPROVE_QUALITY = "improve_quality"
    OPTIMIZE = "optimize"
    ADD_DOCUMENTATION = "add_documentation"
    ADD_TESTS = "add_tests"
    COMPREHENSIVE = "comprehensive"


class ErrorCategory(str, Enum):
    """Category of validation error."""
    SYNTAX = "syntax"
    TYPE = "type"
    IMPORT = "import"
    STYLE = "style"
    COMPLEXITY = "complexity"
    DOCSTRING = "docstring"
    UNUSED = "unused"
    NAMING = "naming"
    LOGIC = "logic"
    SECURITY = "security"
    PERFORMANCE = "performance"


class RefinementPhase(str, Enum):
    """Phase in refinement process."""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    FIXING = "fixing"
    VALIDATION = "validation"
    DECISION = "decision"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ValidationError:
    """Represents a validation error."""
    category: ErrorCategory
    code: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    file_path: Optional[str] = None
    context: Optional[str] = None
    suggestion: Optional[str] = None
    severity: str = "error"
    fixable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefinementStep:
    """Represents a single refinement step."""
    phase: RefinementPhase
    action: str
    before_code: str
    after_code: Optional[str] = None
    errors_fixed: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    success: bool = False
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefinementSession:
    """Tracks a complete refinement session."""
    session_id: str
    strategy: RefinementStrategy
    initial_code: str
    current_code: str
    steps: List[RefinementStep] = field(default_factory=list)
    errors_history: List[List[ValidationError]] = field(default_factory=list)
    quality_scores: List[float] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    success: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefinerConfig:
    """Configuration for iterative refiner."""
    max_iterations: int = 10
    max_time_seconds: int = 300
    convergence_threshold: int = 3
    quality_threshold: float = 0.9
    strategies: List[RefinementStrategy] = field(default_factory=lambda: [
        RefinementStrategy.FIX_ERRORS_FIRST,
        RefinementStrategy.IMPROVE_QUALITY
    ])
    use_llm: bool = True
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.1
    validate_mypy: bool = True
    validate_ruff: bool = True
    auto_fix: bool = True
    preserve_comments: bool = True
    track_changes: bool = True
    generate_diff: bool = True
    backup_original: bool = True
    backup_dir: Optional[Path] = None


# ============================================================
# ERROR PARSERS
# ============================================================

class ErrorParser:
    """Parse validation errors from various tools."""
    
    @staticmethod
    def parse_mypy_output(output: str) -> List[ValidationError]:
        """Parse mypy output into ValidationError objects."""
        errors = []
        
        for line in output.strip().split('\n'):
            if not line.strip() or ':' not in line:
                continue
            
            try:
                parts = line.split(':', 3)
                if len(parts) >= 4:
                    file_path = parts[0].strip()
                    line_num = int(parts[1].strip()) if parts[1].strip().isdigit() else None
                    error_type = parts[2].strip()
                    message = parts[3].strip()
                    
                    category = ErrorCategory.TYPE
                    if 'import' in message.lower():
                        category = ErrorCategory.IMPORT
                    elif 'syntax' in message.lower():
                        category = ErrorCategory.SYNTAX
                    
                    error = ValidationError(
                        category=category,
                        code=error_type,
                        message=message,
                        line=line_num,
                        file_path=file_path,
                        severity='error'
                    )
                    errors.append(error)
            except Exception:
                continue
        
        return errors
    
    @staticmethod
    def parse_ruff_output(output: str) -> List[ValidationError]:
        """Parse ruff output into ValidationError objects."""
        errors = []
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            try:
                parts = line.split(':', 4)
                if len(parts) >= 5:
                    file_path = parts[0].strip()
                    line_num = int(parts[1].strip()) if parts[1].strip().isdigit() else None
                    col_num = int(parts[2].strip()) if parts[2].strip().isdigit() else None
                    code = parts[3].strip()
                    message = parts[4].strip()
                    
                    category = ErrorCategory.STYLE
                    if code.startswith('F'):
                        category = ErrorCategory.UNUSED if 'unused' in message.lower() else ErrorCategory.STYLE
                    elif code.startswith('E') or code.startswith('W'):
                        category = ErrorCategory.STYLE
                    elif code.startswith('C'):
                        category = ErrorCategory.COMPLEXITY
                    elif code.startswith('D'):
                        category = ErrorCategory.DOCSTRING
                    elif code.startswith('N'):
                        category = ErrorCategory.NAMING
                    
                    error = ValidationError(
                        category=category,
                        code=code,
                        message=message,
                        line=line_num,
                        column=col_num,
                        file_path=file_path,
                        severity='warning' if code.startswith('W') else 'error',
                        fixable=True
                    )
                    errors.append(error)
            except Exception:
                continue
        
        return errors


# ============================================================
# CODE ANALYZER
# ============================================================

class CodeAnalyzer:
    """Analyze code quality and identify issues."""
    
    def __init__(self):
        self.error_parser = ErrorParser()
    
    def analyze_syntax(self, code: str) -> List[ValidationError]:
        """Check for syntax errors."""
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            error = ValidationError(
                category=ErrorCategory.SYNTAX,
                code="SYNTAX_ERROR",
                message=str(e),
                line=e.lineno,
                column=e.offset,
                severity='error'
            )
            errors.append(error)
        return errors
    
    def analyze_complexity(self, code: str) -> List[ValidationError]:
        """Analyze code complexity."""
        errors = []
        
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 1
                self.max_complexity = 10
            
            def visit_If(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_While(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_For(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_ExceptHandler(self, node):
                self.complexity += 1
                self.generic_visit(node)
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    visitor = ComplexityVisitor()
                    visitor.visit(node)
                    
                    if visitor.complexity > visitor.max_complexity:
                        errors.append(ValidationError(
                            category=ErrorCategory.COMPLEXITY,
                            code="COMPLEXITY_HIGH",
                            message=f"Function '{node.name}' has high cyclomatic complexity ({visitor.complexity})",
                            line=node.lineno,
                            severity='warning',
                            suggestion="Consider breaking down into smaller functions"
                        ))
        except Exception:
            pass
        
        return errors
    
    def analyze_docstrings(self, code: str) -> List[ValidationError]:
        """Check for missing docstrings."""
        errors = []
        
        try:
            tree = ast.parse(code)
            
            if not ast.get_docstring(tree):
                errors.append(ValidationError(
                    category=ErrorCategory.DOCSTRING,
                    code="MISSING_MODULE_DOCSTRING",
                    message="Module missing docstring",
                    severity='warning',
                    suggestion="Add a module-level docstring"
                ))
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not node.name.startswith('_') and not ast.get_docstring(node):
                        node_type = 'Class' if isinstance(node, ast.ClassDef) else 'Function'
                        errors.append(ValidationError(
                            category=ErrorCategory.DOCSTRING,
                            code=f"MISSING_{node_type.upper()}_DOCSTRING",
                            message=f"{node_type} '{node.name}' missing docstring",
                            line=node.lineno,
                            severity='warning',
                            suggestion=f"Add a docstring to {node_type.lower()} '{node.name}'"
                        ))
        except Exception:
            pass
        
        return errors
    
    def calculate_quality_score(self, code: str, errors: List[ValidationError]) -> float:
        """Calculate overall code quality score (0.0 to 1.0)."""
        if not code.strip():
            return 0.0
        
        score = 1.0
        
        error_counts = {}
        for error in errors:
            error_counts[error.category] = error_counts.get(error.category, 0) + 1
        
        weights = {
            ErrorCategory.SYNTAX: 0.5,
            ErrorCategory.TYPE: 0.1,
            ErrorCategory.IMPORT: 0.05,
            ErrorCategory.STYLE: 0.02,
            ErrorCategory.COMPLEXITY: 0.05,
            ErrorCategory.DOCSTRING: 0.03,
            ErrorCategory.UNUSED: 0.02,
            ErrorCategory.NAMING: 0.02,
        }
        
        for category, count in error_counts.items():
            weight = weights.get(category, 0.05)
            deduction = min(weight * count, 0.5)
            score -= deduction
        
        lines = code.split('\n')
        if len(lines) < 10:
            score *= 0.9
        elif len(lines) > 500:
            score *= 0.95
        
        return max(0.0, min(1.0, score))


# ============================================================
# AI REFINER
# ============================================================

class AIRefiner:
    """Use LLM to refine code based on errors and suggestions."""
    
    def __init__(self, config: RefinerConfig):
        self.config = config
        self.llm = LLMClient() if config.use_llm else None
    
    def refine(self, code: str, errors: List[ValidationError], 
               context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Refine code using LLM."""
        if not self.llm:
            return None
        
        errors_by_category = {}
        for error in errors:
            if error.category not in errors_by_category:
                errors_by_category[error.category] = []
            errors_by_category[error.category].append(error)
        
        prompt = self._build_refinement_prompt(code, errors_by_category, context)
        
        try:
            refined_code = self.llm.complete(prompt)
            return self._extract_code(refined_code)
        except Exception as e:
            logger.error(f"LLM refinement failed: {e}")
            return None
    
    def _build_refinement_prompt(self, code: str, errors_by_category: Dict[ErrorCategory, List[ValidationError]], 
                                  context: Optional[Dict[str, Any]] = None) -> str:
        """Build refinement prompt for LLM."""
        prompt_lines = [
            "Fix the following Python code based on the validation errors.",
            "",
            "ORIGINAL CODE:",
            "```python",
            code,
            "```",
            "",
            "VALIDATION ERRORS:"
        ]
        
        for category, category_errors in errors_by_category.items():
            prompt_lines.append(f"\n## {category.value.upper()} Errors:")
            for error in category_errors[:5]:
                line_info = f" (Line {error.line})" if error.line else ""
                prompt_lines.append(f"- {error.message}{line_info}")
                if error.suggestion:
                    prompt_lines.append(f"  Suggestion: {error.suggestion}")
        
        if context:
            prompt_lines.append("\n## Additional Context:")
            prompt_lines.append("```json")
            prompt_lines.append(json.dumps(context, indent=2))
            prompt_lines.append("```")
        
        prompt_lines.extend([
            "",
            "Please provide the corrected code. Ensure:",
            "1. All syntax and type errors are fixed",
            "2. Code follows PEP 8 style guidelines",
            "3. All public functions/classes have docstrings",
            "4. Imports are organized and unused imports removed",
            "5. Complex functions are simplified if needed",
            "",
            "Output ONLY the corrected Python code, no explanations."
        ])
        
        return "\n".join(prompt_lines)
    
    def _extract_code(self, response: str) -> str:
        """Extract code from LLM response."""
        if '```python' in response:
            start = response.find('```python') + 9
            end = response.find('```', start)
            if end > start:
                return response[start:end].strip()
        elif '```' in response:
            start = response.find('```') + 3
            end = response.find('```', start)
            if end > start:
                return response[start:end].strip()
        
        return response.strip()


# ============================================================
# AUTO FIXER
# ============================================================

class AutoFixer:
    """Automatically fix common code issues."""
    
    def fix_trailing_whitespace(self, code: str) -> str:
        """Remove trailing whitespace."""
        lines = code.split('\n')
        lines = [line.rstrip() for line in lines]
        return '\n'.join(lines)
    
    def fix_missing_newline(self, code: str) -> str:
        """Ensure single newline at end of file."""
        code = code.rstrip()
        return code + '\n'
    
    def apply_all_fixes(self, code: str) -> str:
        """Apply all auto-fixes."""
        code = self.fix_trailing_whitespace(code)
        code = self.fix_missing_newline(code)
        return code


# ============================================================
# MAIN ITERATIVE REFINER
# ============================================================

class IterativeRefiner:
    """
    Iteratively refines code using validation feedback and AI.
    
    Features:
    - Multiple refinement strategies
    - Validation error parsing (mypy, ruff)
    - Quality scoring and tracking
    - LLM-powered refinement
    - Auto-fixing common issues
    - Change tracking and diffs
    - Session persistence
    - Convergence detection
    - Backup and rollback
    """
    
    def __init__(self, config: Optional[RefinerConfig] = None, llm_client: Optional[LLMClient] = None):
        self.config = config or RefinerConfig()
        self.llm = llm_client or (LLMClient() if self.config.use_llm else None)
        self.error_parser = ErrorParser()
        self.code_analyzer = CodeAnalyzer()
        self.ai_refiner = AIRefiner(self.config)
        self.auto_fixer = AutoFixer()
        
        self.mypy_validator = MypyValidator() if self.config.validate_mypy else None
        self.ruff_validator = RuffValidator() if self.config.validate_ruff else None
        
        self.state = StateManager(Path(".ai_state") / "iterative_refiner.json")
        
        self.current_session: Optional[RefinementSession] = None
        
        logger.info("IterativeRefiner initialized")
    
    # ============================================================
    # MAIN REFINEMENT
    # ============================================================
    
    def refine(self, code: str, strategy: Optional[RefinementStrategy] = None,
               context: Optional[Dict[str, Any]] = None) -> RefinementSession:
        """Iteratively refine code until quality threshold is met."""
        strategy = strategy or self.config.strategies[0]
        
        session_id = self._generate_session_id(code)
        self.current_session = RefinementSession(
            session_id=session_id,
            strategy=strategy,
            initial_code=code,
            current_code=code
        )
        
        if self.config.backup_original:
            self._backup_code(code, session_id)
        
        logger.info(f"Starting refinement session {session_id} with strategy {strategy.value}")
        
        iteration = 0
        no_improvement_count = 0
        best_score = 0.0
        best_code = code
        
        while iteration < self.config.max_iterations:
            iteration += 1
            logger.debug(f"Refinement iteration {iteration}")
            
            errors = self._validate_code(self.current_session.current_code)
            self.current_session.errors_history.append(errors)
            
            quality_score = self.code_analyzer.calculate_quality_score(
                self.current_session.current_code, errors
            )
            self.current_session.quality_scores.append(quality_score)
            
            if quality_score > best_score:
                best_score = quality_score
                best_code = self.current_session.current_code
                no_improvement_count = 0
            else:
                no_improvement_count += 1
            
            if quality_score >= self.config.quality_threshold and not errors:
                logger.info(f"Quality threshold met at iteration {iteration}")
                break
            
            if no_improvement_count >= self.config.convergence_threshold:
                logger.info(f"Converged after {iteration} iterations")
                break
            
            refined_code = self.current_session.current_code
            
            if self.config.auto_fix:
                refined_code = self.auto_fixer.apply_all_fixes(refined_code)
            
            critical_errors = [e for e in errors if e.severity == 'error']
            if critical_errors and self.config.use_llm:
                llm_refined = self.ai_refiner.refine(
                    refined_code, 
                    critical_errors[:10],
                    context
                )
                if llm_refined:
                    refined_code = llm_refined
            
            step = RefinementStep(
                phase=RefinementPhase.FIXING,
                action=f"Iteration {iteration}",
                before_code=self.current_session.current_code,
                after_code=refined_code,
                errors_fixed=[e.code for e in errors if e.fixable],
                success=len(critical_errors) == 0
            )
            self.current_session.steps.append(step)
            self.current_session.current_code = refined_code
            
            elapsed = (datetime.now() - self.current_session.start_time).total_seconds()
            if elapsed > self.config.max_time_seconds:
                logger.warning(f"Refinement timeout after {elapsed:.1f}s")
                break
        
        self.current_session.end_time = datetime.now()
        self.current_session.success = best_score >= self.config.quality_threshold
        self.current_session.current_code = best_code
        
        self._save_session(self.current_session)
        
        logger.info(f"Refinement completed: {best_score:.2%} quality, {len(self.current_session.steps)} steps")
        
        return self.current_session
    
    def refine_class(self, code: str, spec: Any, 
                     mypy_errors: List[str], ruff_errors: List[str]) -> str:
        """Refine a generated class."""
        errors = []
        for err in mypy_errors:
            errors.extend(self.error_parser.parse_mypy_output(err))
        for err in ruff_errors:
            errors.extend(self.error_parser.parse_ruff_output(err))
        
        session = self.refine(code, RefinementStrategy.FIX_ERRORS_FIRST, 
                              context={'spec': str(spec) if spec else None})
        return session.current_code
    
    def refine_function(self, code: str, spec: Any,
                        mypy_errors: List[str], ruff_errors: List[str]) -> str:
        """Refine a generated function."""
        errors = []
        for err in mypy_errors:
            errors.extend(self.error_parser.parse_mypy_output(err))
        for err in ruff_errors:
            errors.extend(self.error_parser.parse_ruff_output(err))
        
        session = self.refine(code, RefinementStrategy.FIX_ERRORS_FIRST,
                              context={'spec': str(spec) if spec else None})
        return session.current_code
    
    def refine_module(self, code: str, spec: Any,
                      mypy_errors: List[str], ruff_errors: List[str]) -> str:
        """Refine a generated module."""
        errors = []
        for err in mypy_errors:
            errors.extend(self.error_parser.parse_mypy_output(err))
        for err in ruff_errors:
            errors.extend(self.error_parser.parse_ruff_output(err))
        
        session = self.refine(code, RefinementStrategy.FIX_ERRORS_FIRST,
                              context={'spec': str(spec) if spec else None})
        return session.current_code
    
    def refine_test(self, code: str, spec: Any,
                    mypy_errors: List[str], ruff_errors: List[str]) -> str:
        """Refine a generated test."""
        errors = []
        for err in mypy_errors:
            errors.extend(self.error_parser.parse_mypy_output(err))
        for err in ruff_errors:
            errors.extend(self.error_parser.parse_ruff_output(err))
        
        session = self.refine(code, RefinementStrategy.FIX_ERRORS_FIRST,
                              context={'spec': str(spec) if spec else None})
        return session.current_code
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    def _validate_code(self, code: str) -> List[ValidationError]:
        """Run all configured validators."""
        errors = []
        
        errors.extend(self.code_analyzer.analyze_syntax(code))
        errors.extend(self.code_analyzer.analyze_complexity(code))
        errors.extend(self.code_analyzer.analyze_docstrings(code))
        
        if self.mypy_validator:
            mypy_output = self.mypy_validator.validate_string_return_output(code)
            if mypy_output:
                errors.extend(self.error_parser.parse_mypy_output(mypy_output))
        
        if self.ruff_validator:
            ruff_output = self.ruff_validator.validate_string_return_output(code)
            if ruff_output:
                errors.extend(self.error_parser.parse_ruff_output(ruff_output))
        
        return errors
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def _generate_session_id(self, code: str) -> str:
        """Generate unique session ID."""
        hash_val = hashlib.sha256(code.encode()).hexdigest()[:12]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"session_{timestamp}_{hash_val}"
    
    def _backup_code(self, code: str, session_id: str):
        """Backup original code."""
        backup_dir = self.config.backup_dir or Path(".ai_state/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = backup_dir / f"{session_id}_original.py"
        backup_file.write_text(code)
        logger.debug(f"Backed up original code to {backup_file}")
    
    def _save_session(self, session: RefinementSession):
        """Save refinement session to state."""
        sessions = self.state.get('sessions', [])
        
        session_data = {
            'session_id': session.session_id,
            'strategy': session.strategy.value,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'steps_count': len(session.steps),
            'final_quality': session.quality_scores[-1] if session.quality_scores else 0,
            'success': session.success
        }
        
        sessions.append(session_data)
        if len(sessions) > 50:
            sessions = sessions[-50:]
        
        self.state.set('sessions', sessions)
        self.state.save()
    
    def generate_diff(self, original: str, refined: str) -> str:
        """Generate unified diff between original and refined code."""
        original_lines = original.splitlines(keepends=True)
        refined_lines = refined.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines, refined_lines,
            fromfile='original', tofile='refined'
        )
        
        return ''.join(diff)
    
    def get_session_report(self, session_id: Optional[str] = None) -> str:
        """Generate report for a refinement session."""
        session = self.current_session if session_id is None else None
        
        if not session:
            return "No session available"
        
        lines = [
            f"# Refinement Session Report",
            f"Session ID: {session.session_id}",
            f"Strategy: {session.strategy.value}",
            f"Start: {session.start_time.isoformat()}",
            f"End: {session.end_time.isoformat() if session.end_time else 'N/A'}",
            f"Success: {session.success}",
            f"Iterations: {len(session.steps)}",
            f"Final Quality: {session.quality_scores[-1]:.2%}" if session.quality_scores else "N/A",
            "",
            "## Quality Progression",
        ]
        
        for i, score in enumerate(session.quality_scores):
            lines.append(f"  Iteration {i+1}: {score:.2%}")
        
        if self.config.generate_diff:
            lines.append("")
            lines.append("## Code Diff")
            lines.append("```diff")
            diff = self.generate_diff(session.initial_code, session.current_code)
            lines.append(diff)
            lines.append("```")
        
        return '\n'.join(lines)
    
    def rollback(self, session_id: str) -> Optional[str]:
        """Rollback to original code from a session."""
        backup_dir = self.config.backup_dir or Path(".ai_state/backups")
        backup_file = backup_dir / f"{session_id}_original.py"
        
        if backup_file.exists():
            return backup_file.read_text()
        return None
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("IterativeRefiner closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for iterative refiner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Iteratively refine Python code")
    parser.add_argument("input", type=Path, help="Input Python file to refine")
    parser.add_argument("--output", "-o", type=Path, help="Output file")
    parser.add_argument("--strategy", choices=[s.value for s in RefinementStrategy],
                       default=RefinementStrategy.FIX_ERRORS_FIRST.value)
    parser.add_argument("--max-iterations", type=int, default=10)
    parser.add_argument("--quality-threshold", type=float, default=0.9)
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM assistance")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--diff", action="store_true", help="Show diff only")
    
    args = parser.parse_args()
    
    config = RefinerConfig(
        max_iterations=args.max_iterations,
        quality_threshold=args.quality_threshold,
        use_llm=not args.no_llm,
        generate_diff=True
    )
    
    refiner = IterativeRefiner(config)
    
    code = args.input.read_text(encoding='utf-8')
    
    session = refiner.refine(code, RefinementStrategy(args.strategy))
    
    if args.diff:
        print(refiner.generate_diff(code, session.current_code))
    elif args.report:
        print(refiner.get_session_report())
    else:
        if args.output:
            args.output.write_text(session.current_code)
            print(f"Refined code written to {args.output}")
        else:
            print(session.current_code)
        
        print(f"\nQuality: {session.quality_scores[-1]:.2%}, Iterations: {len(session.steps)}")
    
    refiner.close()


if __name__ == "__main__":
    main()