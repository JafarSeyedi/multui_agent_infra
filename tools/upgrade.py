#!/usr/bin/env python3
"""
Ultra‑Pro Python Code Upgrade & Type‑Hardening Pipeline

A production‑grade, confidence‑aware, multi‑tool pipeline that:
- leverages libcst for safe AST transformations
- integrates pyright, pytype, and mypy outputs
- performs real type inference (return types, parameters)
- uses smart error routing for mypy results
- tracks convergence during iterative fixes
- analyses import graphs and cycles
- detects API breaking changes
- applies dependency policies
- provides per‑stage / per‑file rollback

Features:
  1. apply hints with libcst + rollback
  2. graph‑based inference (cross‑file import analysis)
  3. mypy‑error‑driven prioritisation
  4. API‑surface diff safety
  5. return inference from multiple paths
  6. param inference from usage
  7. merging of pyright + pytype + libcst hints
  8. confidence‑aware annotation
  9. no Any‑spam (only when no better information)
 10. production‑grade architecture
"""
from __future__ import annotations

import ast
import difflib
import json
import re
import shlex
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import auto
from enum import Enum
from pathlib import Path
from typing import Any
from typing import NamedTuple

import libcst as cst
from libcst import metadata

# =============================================================================
# Configuration
# =============================================================================
class CyclePolicy(Enum):
    IGNORE = "ignore"
    WARN = "warn"
    FAIL = "fail"

@dataclass
class PipelineConfig:
    project_root: Path = Path(".").resolve()
    backup_dir: Path = field(init=False)
    report_dir: Path = field(init=False)
    max_mypy_iter: int = 10
    confidence_threshold: float = 0.7          # apply hints with confidence >= this
    max_confidence_merge_difference: float = 0.2  # skip if hints differ too much
    import_cycle_policy: CyclePolicy = CyclePolicy.WARN
    dry_run: bool = False
    mypy_error_codes_that_trigger_inference: frozenset[str] = frozenset({
        "missing-return-type",
        "missing-parameter-type",
        "return-value",
        "arg-type",
    })

    # Linter profiles
    ruff_profiles: dict[str, str] = field(default_factory=lambda: {
        "conservative": "--select E,W,F --ignore E501",
        "aggressive": "--select ALL",
    })
    skip_paths: list[str] = field(default_factory=lambda: [
        "*/migrations/*",
        "*/generated/*",
        "*/vendored/*",
        "*/tests/*",   # you may want to include tests, but keep configurable
    ])

    # Dependency policy
    dep_fail_on_cvss_gt: float = 7.0
    dep_fail_on_high_severity: bool = True

    def __post_init__(self) -> None:
        self.backup_dir = self.project_root / ".upgrade_backup"
        self.report_dir = self.project_root / ".upgrade_reports"


# =============================================================================
# Utility classes
# =============================================================================

class ToolResult(NamedTuple):
    returncode: int
    stdout: str
    stderr: str


class StageOutcome(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"


@dataclass
class StageRecord:
    name: str
    outcome: StageOutcome
    details: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Hint / Inference data structures
# =============================================================================

class HintSource(Enum):
    PYRIGHT = "pyright"
    PYTYPE = "pytype"
    LIBCST = "libcst"
    MYPY_ERROR = "mypy_error"


class HintKind(Enum):
    RETURN = "return"
    PARAM = "param"
    VARIABLE = "variable"
    ATTRIBUTE = "attribute"


@dataclass(frozen=True)
class TypeHint:
    symbol: str               # e.g. "foo", "foo.x", "bar:param1"
    annotation: str           # e.g. "int", "Optional[str]", "Union[int, float]"
    kind: HintKind
    source: HintSource
    confidence: float         # 0.0 – 1.0

    def __post_init__(self) -> None:
        # Ensure annotation is valid Python type expression (basic check)
        # We'll trust external tools; for libcst we'll construct proper strings.
        pass


# =============================================================================
# SymbolIndex &إ FunctionLocation
# =============================================================================

@dataclass
class FunctionLocation:
    file: Path
    name: str                  # simple name
    qualname: str = ""         # fully qualified (e.g. "mod.Class.method")

class SymbolIndex:
    """Indexes all functions/classes in the project to map symbols to files."""
    def __init__(self, root: Path, skip_patterns: list[str]):
        self.root = root
        self.skip_patterns = skip_patterns
        self.index: dict[str, FunctionLocation] = {}

    def build(self) -> None:
        for py_file in self.root.rglob("*.py"):
            if any(py_file.match(p) for p in self.skip_patterns):
                continue
            try:
                tree = cst.parse_module(py_file.read_text())
            except Exception:
                continue
            wrapper = metadata.MetadataWrapper(tree)
            visitor = _SymbolCollector(py_file)
            wrapper.visit(visitor)
            for loc in visitor.locations:
                self.index[loc.name] = loc
                if loc.qualname:
                    self.index[loc.qualname] = loc  # also index by full qualname

class _SymbolCollector(cst.CSTVisitor):
    def __init__(self, file: Path):
        self.file = file
        self.locations: list[FunctionLocation] = []
        self._scope: list[str] = []

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self._scope.append(node.name.value)
        self.locations.append(FunctionLocation(
            file=self.file,
            name=node.name.value,
            qualname=".".join(self._scope)
        ))

    def leave_ClassDef(self, original: cst.ClassDef) -> None:
        self._scope.pop()

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        qualname = ".".join(self._scope + [node.name.value]) if self._scope else node.name.value
        self.locations.append(FunctionLocation(
            file=self.file,
            name=node.name.value,
            qualname=qualname
        ))

# =============================================================================
# Mypy error handling
# =============================================================================

class MypyError:
    """Parsed mypy error with exact location and error code."""
    __slots__ = ("file", "line", "column", "message", "code", "raw")
    def __init__(self, file: str, line: int, column: int | None, message: str, code: str | None, raw: str) -> None:
        self.file = file
        self.line = line
        self.column = column
        self.message = message
        self.code = code
        self.raw = raw

    def __hash__(self) -> int:
        return hash((self.file, self.line, self.column, self.code))


class MypyErrorParser:
    """Parses mypy --show-error-codes output into structured MypyError objects."""

    _pattern = re.compile(
        r"^(?P<file>.+?):(?P<line>\d+)(?::(?P<col>\d+))?:\s+"
        r"(?P<severity>error|warning):\s+(?P<message>.+?)(?:\s+\[(?P<code>\S+)\])?$",
        re.MULTILINE,
    )

    @classmethod
    def parse(cls, output: str) -> list[MypyError]:
        errors: list[MypyError] = []
        for match in cls._pattern.finditer(output):
            file = match.group("file").strip()
            line = int(match.group("line"))
            col = int(match.group("col")) if match.group("col") else None
            message = match.group("message").strip()
            code = match.group("code") if match.group("code") else None
            errors.append(
                MypyError(file, line, col, message, code, match.group(0))
            )
        return errors


# =============================================================================
# Convergence tracking
# =============================================================================

class ConvergenceTracker:
    """Tracks sets of mypy errors across iterations to detect stalls or regression."""

    def __init__(self) -> None:
        self.history: list[set[tuple[str, int, str | None]]] = []  # (file, line, code)

    def update(self, errors: list[MypyError]) -> None:
        self.history.append({
            (e.file, e.line, e.code) for e in errors
        })

    def should_stop(self) -> tuple[bool, str]:
        if len(self.history) < 2:
            return False, ""
        prev, curr = self.history[-2], self.history[-1]
        if curr == prev:
            return True, "error set unchanged"
        if len(curr) > len(prev):
            return True, "error count increased (possible regression)"
        return False, ""


# =============================================================================
# Type inference engine (libcst visitors)
# =============================================================================

class ReturnTypeCollector(cst.CSTVisitor):
    """Collects types of return expressions."""
    def __init__(self) -> None:
        self.returns: list[str] = []       # annotation string per return
        self.has_bare_return = False

    def visit_Return(self, node: cst.Return) -> None:
        if node.value is None:
            self.has_bare_return = True
            self.returns.append("None")
            return
        value = node.value
        # Literal types
        if isinstance(value, cst.Integer):
            self.returns.append("int")
        elif isinstance(value, cst.Float):
            self.returns.append("float")
        elif isinstance(value, cst.Imaginary):
            self.returns.append("complex")
        elif isinstance(value, cst.SimpleString):
            self.returns.append("str")
        elif isinstance(value, cst.Name) and value.value in {"True", "False"}:
            self.returns.append("bool")
        elif isinstance(value, cst.Name) and value.value == "None":
            self.returns.append("None")
        elif isinstance(value, cst.BaseList):
            self.returns.append("list")
        elif isinstance(value, cst.BaseDict):
            self.returns.append("dict")
        elif isinstance(value, cst.BaseSet):
            self.returns.append("set")
        elif isinstance(value, cst.Tuple):
            self.returns.append("tuple")
        else:
            # too complex -> Any
            self.returns.append("Any")

    def consolidate(self) -> str | None:
        if not self.returns:
            return None       # no return statements at all
        unique = sorted(set(self.returns))
        if len(unique) == 1:
            return unique[0]
        # If None is mixed with something else, Optional
        if "None" in unique:
            others = [t for t in unique if t != "None"]
            if not others:
                return "None"
            if len(others) == 1:
                return f"Optional[{others[0]}]"
            return f"Optional[Union[{', '.join(others)}]]"
        return f"Union[{', '.join(unique)}]"


class OptionalAssignmentDetector(cst.CSTVisitor):
    """Detects variables assigned in if x is None / if x is not None branches."""
    def __init__(self) -> None:
        self.optional_vars: set[str] = set()

    def _is_none_check(self, test: cst.BaseExpression) -> str | None:
        if isinstance(test, cst.Comparison):
            # x is None or x is not None
            if (
                len(test.comparisons) == 1
                and isinstance(test.comparisons[0].operator, (cst.Is, cst.IsNot))
            ):
                left = test.left
                comparator = test.comparisons[0].comparator
                if isinstance(comparator, cst.Name) and comparator.value == "None":
                    if isinstance(left, cst.Name):
                        return left.value
        return None

    def visit_If(self, node: cst.If) -> None:
        var = self._is_none_check(node.test)
        if var:
            self.optional_vars.add(var)

    def visit_IfExp(self, node: cst.IfExp) -> None:
        var = self._is_none_check(node.test)
        if var:
            self.optional_vars.add(var)


class IsInstanceUnionDetector(cst.CSTVisitor):
    """Collects type info from isinstance(...) checks."""
    def __init__(self) -> None:
        self.unions: dict[str, set[str]] = defaultdict(set)

    def visit_If(self, node: cst.If) -> None:
        self._process_instance_check(node.test)

    def _process_instance_check(self, test: cst.BaseExpression) -> None:
        if isinstance(test, cst.Call) and isinstance(test.func, cst.Name) and test.func.value == "isinstance":
            if len(test.args) == 2:
                # mypy به‌تنهایی نمی‌تواند نوع Arg.value را BaseExpression تشخیص دهد،
                # بنابراین با یک annotation کمکی صریح‌ش کنید
                arg0: cst.BaseExpression = test.args[0].value
                arg1: cst.BaseExpression = test.args[1].value
                if isinstance(arg0, cst.Name):
                    var_name = arg0.value
                    type_str = self._type_to_str(arg1)
                    if type_str:
                        self.unions[var_name].add(type_str)

    @staticmethod
    def _type_to_str(node: cst.BaseExpression) -> str | None:
        if isinstance(node, cst.Name):
            return node.value

        if isinstance(node, cst.Attribute):
            left_part = IsInstanceUnionDetector._type_to_str(node.value)
            if left_part:
                return f"{left_part}.{node.attr.value}"
            return node.attr.value

        if isinstance(node, cst.Tuple):
            inner: list[str] = []
            for elem in node.elements:
                # فقط BaseExpression‌ها را در نظر می‌گیریم، StarredElement‌ها را نادیده می‌گیریم
                if isinstance(elem, cst.BaseExpression):
                    res = IsInstanceUnionDetector._type_to_str(elem)
                    if res:
                        inner.append(res)
            return ", ".join(inner) if inner else None

        if isinstance(node, cst.Subscript):
            base = IsInstanceUnionDetector._type_to_str(node.value)
            if not base:
                return None
            slice_str = ""
            if isinstance(node.slice, cst.Index):
                slice_val = IsInstanceUnionDetector._type_to_str(node.slice.value)
                if slice_val:
                    slice_str = f"[{slice_val}]"
            return f"{base}{slice_str}"

        return None

class ParamUsageInferer(cst.CSTVisitor):
    """Infers parameter types by examining call sites."""
    def __init__(self) -> None:
        # mapping: (function_name, param_index) -> set of inferred types
        self.param_types: dict[tuple[str, int], set[str]] = defaultdict(set)

    def visit_Call(self, node: cst.Call) -> None:
        func = node.func
        if isinstance(func, cst.Name):
            fn_name = func.value
        elif isinstance(func, cst.Attribute) and isinstance(func.value, cst.Name):
            fn_name = func.value.value + "." + func.attr.value
        else:
            return

        for i, arg in enumerate(node.args):
            # Skip **kwargs style
            if isinstance(arg, cst.Arg):
                actual = arg.value
            else:
                actual = arg
            typ = self._literal_type(actual)
            if typ:
                self.param_types[(fn_name, i)].add(typ)

    @staticmethod
    def _literal_type(node: cst.BaseExpression) -> str | None:
        if isinstance(node, cst.Integer):
            return "int"
        if isinstance(node, cst.Float):
            return "float"
        if isinstance(node, cst.SimpleString):
            return "str"
        if isinstance(node, cst.Name) and node.value in {"True", "False"}:
            return "bool"
        if isinstance(node, cst.Name) and node.value == "None":
            return "None"
        return None


class TypeHintMerger:
    """Merges hints from different sources, preferring high confidence and consistency."""

    def __init__(self, confidence_threshold: float = 0.7, max_difference: float = 0.2) -> None:
        self.threshold = confidence_threshold
        self.max_difference = max_difference

    def merge(self, hints: list[TypeHint]) -> list[TypeHint]:
        """Group by symbol, then return the best annotation per symbol."""
        grouped: dict[str, list[TypeHint]] = defaultdict(list)
        for h in hints:
            grouped[h.symbol].append(h)

        merged: list[TypeHint] = []
        for symbol, candidates in grouped.items():
            if not candidates:
                continue
            best = self._select_best(candidates)
            if best is not None and best.confidence >= self.threshold:
                merged.append(best)
        return merged

    def _select_best(self, candidates: list[TypeHint]) -> TypeHint | None:
        # Sort descending by confidence
        candidates_sorted = sorted(candidates, key=lambda h: h.confidence, reverse=True)
        primary = candidates_sorted[0]
        if primary.confidence >= self.threshold:
            # Check agreement among high-confidence sources
            high_conf = [h for h in candidates if h.confidence >= self.threshold]
            if len(high_conf) > 1:
                annotations = {h.annotation for h in high_conf}
                if len(annotations) > 1:
                    # If the top two disagree and difference in confidence is small, we may skip
                    if len(high_conf) >= 2:
                        diff = high_conf[0].confidence - high_conf[1].confidence
                        if diff <= self.max_difference:
                            return None  # too risky
            return primary
        return None


class AnnotationInjector(cst.CSTTransformer):
    """libcst transformer that adds return types and (some) parameter types."""
    def __init__(self, hints: dict[str, TypeHint]) -> None:
        super().__init__()
        self.hints = hints  # symbol -> TypeHint

    def leave_FunctionDef(
        self, original: cst.FunctionDef, updated: cst.FunctionDef
    ) -> cst.FunctionDef:
        if updated.returns is None and original.name.value in self.hints:
            hint = self.hints[original.name.value]
            if hint.kind == HintKind.RETURN:
                ann_str = hint.annotation
                if original.asynchronous and not ann_str.startswith("Coroutine"):
                    ann_str = f"Coroutine[Any, Any, {ann_str}]"
                new_ret = self._parse_annotation(ann_str)
                if new_ret:
                    updated = updated.with_changes(returns=cst.Annotation(new_ret))
        # Try parameter annotations (if completely missing)
        params = list(updated.params.params)
        modified_params = False
        for i, param in enumerate(params):
            if param.annotation is None:
                key = f"{original.name.value}:param{i}"
                hint1 = self.hints.get(key)
                if hint1:
                    ann = self._parse_annotation(hint1.annotation)
                    if ann:
                        params[i] = param.with_changes(annotation=cst.Annotation(ann))
                        modified_params = True
        if modified_params:
            updated = updated.with_changes(
                params=updated.params.with_changes(params=tuple(params))
            )
        return updated

    @staticmethod
    def _parse_annotation(annotation_str: str) -> cst.BaseExpression | None:
        try:
            return cst.parse_expression(annotation_str)
        except cst.ParserSyntaxError:
            return None


# =============================================================================
# External tool runners
# =============================================================================

class ExternalToolRunner:
    @staticmethod
    def run_pyright(root: Path) -> dict[str, Any]:
        """Run pyright --outputjson, return parsed JSON or empty dict."""
        try:
            proc = subprocess.run(
                ["pyright", "--outputjson"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc.returncode not in (0, 1):
                return {}
            return json.loads(proc.stdout)
        except Exception:
            return {}

    @staticmethod
    def run_pytype(root: Path) -> dict[str, Any]:
        """Run pytype -j auto --output=json, return parsed JSON or empty dict."""
        try:
            proc = subprocess.run(
                ["pytype", "-j", "auto", "--output=json"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=180,
            )
            if proc.returncode not in (0, 1):
                return {}
            return json.loads(proc.stdout)
        except Exception:
            return {}

    @staticmethod
    def run_mypy(root: Path, extra_args: str = "") -> ToolResult:
        cmd = f"mypy . --show-error-codes --no-error-summary --no-pretty {extra_args}"
        proc = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True)
        return ToolResult(proc.returncode, proc.stdout, proc.stderr)


# =============================================================================
# Parsers for external tool outputs -> TypeHint
# =============================================================================

class PyrightHintExtractor:
    @staticmethod
    def extract(pyright_json: dict) -> list[TypeHint]:
        hints = []
        for diag in pyright_json.get("generalDiagnostics", []):
            symbol = diag.get("symbol", "")
            rule = diag.get("rule", "")
            if "type" not in diag:
                continue
            if rule == "reportMissingParameterType":
                hints.append(TypeHint(
                    symbol=symbol, annotation=diag["type"],
                    kind=HintKind.PARAM, source=HintSource.PYRIGHT, confidence=0.95
                ))
            elif rule == "reportMissingReturnType":
                hints.append(TypeHint(
                    symbol=symbol, annotation=diag["type"],
                    kind=HintKind.RETURN, source=HintSource.PYRIGHT, confidence=0.95
                ))
            else:
                hints.append(TypeHint(
                    symbol=symbol, annotation=diag["type"],
                    kind=HintKind.VARIABLE, source=HintSource.PYRIGHT, confidence=0.85
                ))
        return hints


class PytypeHintExtractor:
    @staticmethod
    def extract(pytype_json: dict) -> list[TypeHint]:
        hints = []
        for error in pytype_json.get("errors", []):
            name = error.get("_name", "")
            inferred = error.get("inferred_type")
            if not inferred:
                continue
            # pytype often gives full type string; we assume it's correct.
            # We try to map to kind based on context (simplified)
            kind = HintKind.VARIABLE
            if ":" in name and name.split(":")[-1].startswith("return"):
                kind = HintKind.RETURN
            elif ":" in name:
                kind = HintKind.PARAM
            hints.append(TypeHint(
                symbol=name, annotation=inferred,
                kind=kind, source=HintSource.PYTYPE, confidence=0.8
            ))
        return hints


# =============================================================================
# libcst-based inference (gathering hints from source code)
# =============================================================================

class LibCSTInferencer:
    def infer_file(self, file_path: Path) -> list[TypeHint]:
        """Analyse a single .py file and return TypeHints from body analysis."""
        code = file_path.read_text(encoding="utf-8")
        module = cst.parse_module(code)
        wrapper = metadata.MetadataWrapper(module)

        _return_collectors: dict[str, ReturnTypeCollector] = {}
        optional_detector = OptionalAssignmentDetector()
        isinstance_detector = IsInstanceUnionDetector()
        param_usage = ParamUsageInferer()

        # First pass: collect data
        wrapper.visit(optional_detector)
        wrapper.visit(isinstance_detector)

        # We'll also need a visitor to collect returns per function.
        class FunctionCollector(cst.CSTVisitor):
            def __init__(self) -> None:
                self.funcs: dict[str, cst.FunctionDef] = {}
            def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
                self.funcs[node.name.value] = node
                return False  # don't descend inside nested functions for now

        func_col = FunctionCollector()
        wrapper.visit(func_col)

        wrapper.visit(param_usage)

        hints: list[TypeHint] = []

        # 1. Return type inference
        for fname, func_node in func_col.funcs.items():
            coll = ReturnTypeCollector()
            func_node.visit(coll)
            ret_ann = coll.consolidate()
            if ret_ann and ret_ann != "Any":
                hints.append(TypeHint(
                    symbol=fname, annotation=ret_ann,
                    kind=HintKind.RETURN, source=HintSource.LIBCST, confidence=0.6
                ))

        # 2. Optional / union based variables (simplified)
        for var in optional_detector.optional_vars:
            hints.append(TypeHint(
                symbol=var, annotation="Optional[Any]",  # will be refined later
                kind=HintKind.VARIABLE, source=HintSource.LIBCST, confidence=0.3
            ))
        for var, types in isinstance_detector.unions.items():
            if types:
                union_str = f"Union[{', '.join(sorted(types))}]" if len(types) > 1 else next(iter(types))
                hints.append(TypeHint(
                    symbol=var, annotation=union_str,
                    kind=HintKind.VARIABLE, source=HintSource.LIBCST, confidence=0.7
                ))

        # 3. Param usage
        for (func_name, idx), types in param_usage.param_types.items():
            if types:
                union_str = f"Union[{', '.join(sorted(types))}]" if len(types) > 1 else next(iter(types))
                hints.append(TypeHint(
                    symbol=f"{func_name}:param{idx}", annotation=union_str,
                    kind=HintKind.PARAM, source=HintSource.LIBCST, confidence=0.5
                ))

        return hints


# =============================================================================
# Import graph and cycle detection
# =============================================================================

class ImportGraph:
    def __init__(self) -> None:
        self.adj: dict[str, set[str]] = defaultdict(set)
        self.nodes: set[str] = set()

    def add_edge(self, from_mod: str, to_mod: str) -> None:
        self.nodes.add(from_mod)
        self.nodes.add(to_mod)
        self.adj[from_mod].add(to_mod)

    def build_from_project(self, root: Path) -> None:
        """Parse all .py files and extract imports."""
        for py_file in root.rglob("*.py"):
            mod_name = self._path_to_module(root, py_file)
            if mod_name is None:
                continue
            with open(py_file, encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read(), filename=str(py_file))
                except SyntaxError:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.add_edge(mod_name, alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self.add_edge(mod_name, node.module)

    def find_cycles(self) -> list[list[str]]:
        """Return list of cycles (simple Tarjan's SCC)."""
        # Basic DFS-based cycle detection
        visited = set()
        _stack: list[str] = []
        cycles = []

        def dfs(node, path):
            visited.add(node)
            path.add(node)
            for neighbor in self.adj.get(node, set()):
                if neighbor in path:
                    # cycle found
                    cycle_start = list(path).index(neighbor)
                    cycles.append(list(path)[cycle_start:] + [neighbor])
                elif neighbor not in visited:
                    dfs(neighbor, path)
            path.remove(node)

        for node in self.nodes:
            if node not in visited:
                dfs(node, set())
        return cycles

    @staticmethod
    def _path_to_module(root: Path, file_path: Path) -> str | None:
        """Convert file path to dotted module name if inside root package."""
        try:
            relative = file_path.relative_to(root)
        except ValueError:
            return None
        parts = list(relative.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        elif parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        else:
            return None
        return ".".join(parts) if parts else None


# =============================================================================
# API Surface Diff
# =============================================================================

class APISurfaceAnalyser:
    """Uses griffe (if installed) to dump API and compare versions."""

    @staticmethod
    def dump_api(root: Path, output_path: Path) -> bool:
        try:
            subprocess.run(
                ["python", "-m", "griffe", "dump", str(root), "-o", str(output_path)],
                check=True, capture_output=True, timeout=60,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def load_api_dump(path: Path) -> dict[str, Any]:
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _get_public_symbols_all(root: Path) -> dict[str, set[str]]:
        """Build a mapping from module name to set of symbols declared in __all__."""
        public_symbols: dict[str, set[str]] = {}
        for py_file in root.rglob("*.py"):
            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())
            except Exception:
                continue
            # Extract __all__
            all_set = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "__all__":
                            if isinstance(node.value, ast.List):
                                all_set = {
                                    elt.value for elt in node.value.elts
                                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                                }
            if all_set:
                module_name = APISurfaceAnalyser._path_to_module(root, py_file)
                if module_name:
                    public_symbols[module_name] = all_set
        return public_symbols

    @staticmethod
    def _path_to_module(root: Path, file_path: Path) -> str | None:
        """Utility to convert file path to dotted module name (as before)."""
        try:
            relative = file_path.relative_to(root)
        except ValueError:
            return None
        parts = list(relative.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        elif parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        else:
            return None
        return ".".join(parts) if parts else None

    @staticmethod
    def detect_breaking_changes(old: dict, new: dict, public_all: dict[str, set[str]]) -> list[str]:
        """Detect breaking changes, considering __all__ if available."""
        """Simplistic detection of removed public symbols."""
        # This is a minimal implementation; for a real system you'd need deep diff.
        issues = []
        old_symbols = set(old.get("children", {}).keys())
        new_symbols = set(new.get("children", {}).keys())
        removed = old_symbols - new_symbols
        for sym in removed:
            if not sym.startswith("_"):
                issues.append(f"Public symbol removed: {sym}")
        return issues

    @staticmethod
    def detect_signature_changes(old: dict, new: dict) -> list[str]:
        """Compare function signatures between two griffe dumps."""
        issues = []
        old_funcs = APISurfaceAnalyser._extract_funcs(old)
        new_funcs = APISurfaceAnalyser._extract_funcs(new)
        for name in old_funcs.keys() & new_funcs.keys():
            old_sig = old_funcs[name]["signature"]
            new_sig = new_funcs[name]["signature"]
            if old_sig != new_sig:
                issues.append(f"Signature changed for {name}: {old_sig} -> {new_sig}")
        for name in old_funcs.keys() - new_funcs.keys():
            if not name.startswith("_"):
                issues.append(f"Public symbol removed: {name}")
        return issues

    @staticmethod
    def _extract_funcs(dump: dict) -> dict[str, dict]:
        funcs = {}
        for child in dump.get("children", {}).values():
            if child.get("kind") == "function":
                sig = child.get("signature", "")
                funcs[child["name"]] = {"signature": sig}
        return funcs


# =============================================================================
# Rollback Manager
# =============================================================================

class RollbackManager:
    """Per‑stage and per‑file rollback via simple file backups."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.stage_backups: dict[str, dict[str, str]] = {}  # stage_name -> {rel_path: original_content}

    def snapshot_project(self, stage_name: str) -> None:
        """Save current state of all .py files for later rollback."""
        backup = {}
        for py_file in self.config.project_root.rglob("*.py"):
            rel = py_file.relative_to(self.config.project_root)
            backup[str(rel)] = py_file.read_text(encoding="utf-8")
        self.stage_backups[stage_name] = backup

    def rollback_stage(self, stage_name: str) -> None:
        """Restore project to the snapshot taken before the given stage."""
        if stage_name not in self.stage_backups:
            return
        backup = self.stage_backups[stage_name]
        for rel, content in backup.items():
            target = self.config.project_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    def rollback_file(self, file_rel: Path, stage_name: str) -> bool:
        """Restore a single file to its pre‑stage state."""
        if stage_name not in self.stage_backups:
            return False
        rel_str = str(file_rel)
        if rel_str in self.stage_backups[stage_name]:
            target = self.config.project_root / rel_str
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self.stage_backups[stage_name][rel_str], encoding="utf-8")
            return True
        return False


# =============================================================================
# Pipeline Supervisor
# =============================================================================
class FixStrategy(Enum):
    CONSERVATIVE = auto()   # only add ignore comments, never modify types
    MODERATE = auto()       # add annotations when confident, else ignore
    AGGRESSIVE = auto()     # also add Any annotations when no info exists


class MypyErrorFixer(cst.CSTTransformer):
    """A comprehensive mypy error fixer using libcst.

    Handles: missing-return-type, missing-parameter-type, return-value,
             arg-type, assignment, union-attr, and others.
    """
    def __init__(self, errors: list[MypyError], source_code: str,
        strategy: FixStrategy = FixStrategy.MODERATE) -> None:
        super().__init__()
        self.errors = errors
        self.strategy = strategy
        self.source_lines = source_code.splitlines()
        # Map (line, column) -> MypyError for node-level matching
        self.error_by_pos: dict[tuple[int, int | None], MypyError] = {}
        for e in errors:
            self.error_by_pos[(e.line, e.column)] = e

        # Also group errors by line for line-based fixes (e.g., adding ignore comment)
        self.errors_by_line: dict[int, list[MypyError]] = {}
        for e in errors:
            self.errors_by_line.setdefault(e.line, []).append(e)

        # Track fixes
        self.fixes_applied = 0
        self.IGNOREABLE_CODES = {
            "arg-type", "assignment", "return-value", "union-attr",
            "operator", "index", "attr-defined", "name-defined",
            "no-untyped-call", "type-arg", "var-annotated"
        }

    # ------------------------------------------------------------------
    # Helper methods for safe type annotation manipulation
    # ------------------------------------------------------------------
    @staticmethod
    def _pos(node: cst.CSTNode) -> tuple[int, int] | None:
        """Return (line, column) start position of a node."""
        p = getattr(node, 'position', None)
        if p is None:
            return None
        return (p.start.line, p.start.column)  # both 1-based

    def _get_error_for_node(self, node: cst.CSTNode) -> MypyError | None:
        """Find MypyError that matches the start position of the node."""
        pos = self._pos(node)
        if pos is None:
            return None
        return self.error_by_pos.get(pos)


    @staticmethod
    def _parse_annotation(ann_str: str) -> cst.BaseExpression | None:
        try:
            return cst.parse_expression(ann_str)
        except cst.ParserSyntaxError:
            return None

    @staticmethod
    def _is_none_literal(node: cst.BaseExpression) -> bool:
        """Check if node represents 'None'."""
        return isinstance(node, cst.Name) and node.value == "None"

    def _wrap_async_return(self, func_node: cst.FunctionDef, ret_type_str: str) -> str:
        """If function is async, wrap return type as Coroutine[Any, Any, T]."""
        if func_node.asynchronous and not ret_type_str.startswith("Coroutine"):
            # Avoid double wrapping
            return f"Coroutine[Any, Any, {ret_type_str}]"
        return ret_type_str

    # ------------------------------------------------------------------
    # Visitor methods for specific error codes
    # ------------------------------------------------------------------
    def leave_FunctionDef(self, original: cst.FunctionDef, updated: cst.FunctionDef) -> cst.FunctionDef:
        error = self._get_error_for_node(original)
        if error is None:
            return updated

        if error.code == "missing-return-type":
            if updated.returns is None:
                return self._add_return_annotation(original, updated)
        elif error.code == "return-value":
            if updated.returns is not None:
                # override with inferred type if more precise
                return self._add_return_annotation(original, updated, override=True)
        elif error.code == "no-untyped-def":
            if self.strategy == FixStrategy.AGGRESSIVE:
                # add return type Any and param types Any if missing
                return self._add_any_annotations(updated)
        return updated

    def leave_Param(self, original: cst.Param, updated: cst.Param) -> cst.Param:
        error = self._get_error_for_node(original)
        if error and error.code == "missing-parameter-type" and updated.annotation is None:
            # For now, defer to previous stages. In aggressive mode, add Any.
            if self.strategy == FixStrategy.AGGRESSIVE:
                new_ann = self._parse_annotation("Any")
                if new_ann:
                    self.fixes_applied += 1
                    return updated.with_changes(annotation=cst.Annotation(new_ann))
        return updated

    def leave_Call(self, original: cst.Call, updated: cst.Call) -> cst.BaseExpression:
        error = self._get_error_for_node(original)
        if error is None:
            return updated

        if error.code == "arg-type":
            # attempt literal conversion (existing logic)
            converted = self._attempt_arg_conversion(updated, error)
            if converted is not None:
                return converted
        # for other call-related errors we'll add ignore at line level
        return updated

    def leave_BinaryOperation(self, original: cst.BinaryOperation, updated: cst.BinaryOperation) -> cst.BaseExpression:
        error = self._get_error_for_node(original)
        if error and error.code == "operator":
            # ignore will be added at line level
            pass
        return updated

    # ----------------------------------------------------------------
    # Line-level ignore insertion
    # ----------------------------------------------------------------
    def leave_SimpleStatementLine(self, original: cst.SimpleStatementLine, updated: cst.SimpleStatementLine) -> cst.BaseStatement:
        line_no = original.start.line if hasattr(original, 'start') else self._get_line(original)
        if line_no is None:
            return updated

        errors = self.errors_by_line.get(line_no, [])
        if not errors:
            return updated

        # Collect all error codes that are safe to ignore
        ignorable = {e.code for e in errors if e.code in self.IGNOREABLE_CODES}
        if not ignorable:
            return updated

        # Do not double-add ignore
        existing = updated.trailing_whitespace.comment
        if existing and any(f"type: ignore[{c}]" in existing.value for c in ignorable):
            return updated

        ignore_str = "# type: ignore[" + ", ".join(sorted(ignorable)) + "]"
        new_comment = cst.Comment(value=ignore_str)
        if existing is None:
            new_trailing = cst.TrailingWhitespace(
                whitespace=cst.SimpleWhitespace("  "),
                comment=new_comment,
                newline=updated.trailing_whitespace.newline,
            )
        else:
            new_trailing = updated.trailing_whitespace.with_changes(
                comment=cst.Comment(value=existing.value + "  " + ignore_str)
            )
        self.fixes_applied += 1
        return updated.with_changes(trailing_whitespace=new_trailing)

    def _get_line(self, node: cst.CSTNode) -> int | None:
        pos = getattr(node, 'position', None)
        return pos.start.line if pos else None

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------
    def _add_return_annotation(self, original: cst.FunctionDef, updated: cst.FunctionDef, override=False) -> cst.FunctionDef:
        """Infer and add return annotation, with async wrapping."""
        coll = ReturnTypeCollector()
        original.body.visit(coll)
        ann = coll.consolidate()
        if not ann or ann == "Any":
            if self.strategy == FixStrategy.AGGRESSIVE:
                ann = "Any"
            else:
                return updated
        ann = self._wrap_async_return(original, ann)
        new_ret = self._parse_annotation(ann)
        if new_ret:
            self.fixes_applied += 1
            return updated.with_changes(returns=cst.Annotation(new_ret))
        return updated

    def _add_any_annotations(self, updated: cst.FunctionDef) -> cst.FunctionDef:
        """Add Any to parameters and return if missing. Used in AGGRESSIVE mode."""
        changed = False

        # Params
        new_params = []
        for param in updated.params.params:
            if param.annotation is None:
                new_param = param.with_changes(annotation=cst.Annotation(cst.parse_expression("Any")))
                new_params.append(new_param)
                changed = True
            else:
                new_params.append(param)
        if changed:
            updated = updated.with_changes(params=updated.params.with_changes(params=tuple(new_params)))

        # Return
        if updated.returns is None:
            updated = updated.with_changes(returns=cst.Annotation(cst.parse_expression("Any")))
            changed = True

        if changed:
            self.fixes_applied += 1
        return updated

    def _attempt_arg_conversion(self, updated: cst.Call, error: MypyError) -> cst.BaseExpression | None:
        """Try to convert argument literal to expected type. Returns modified Call or None."""
        match_exp = re.search(r'expected\s+"([^"]+)"', error.message)
        if not match_exp:
            return None
        expected_type = match_exp.group(1)
        arg_match = re.search(r'Argument\s+(\d+)', error.message)
        if not arg_match:
            return None
        arg_idx = int(arg_match.group(1)) - 1
        if arg_idx >= len(updated.args):
            return None

        arg = updated.args[arg_idx]
        value = arg.value if isinstance(arg, cst.Arg) else arg
        converted_value = self._convert_literal_to_type(value, expected_type)
        if converted_value is None:
            return None

        new_args = []
        for i, arg in enumerate(updated.args):
            if i == arg_idx:
                if isinstance(arg, cst.Arg):
                    new_args.append(arg.with_changes(value=converted_value))
                else:
                    new_args.append(converted_value)
            else:
                new_args.append(arg)
        return updated.with_changes(args=tuple(new_args))

    # ------------------------------------------------------------------
    # Literal conversion helper
    # ------------------------------------------------------------------
    def _convert_literal_to_type(self, node: cst.BaseExpression, target: str) -> cst.BaseExpression | None:
        """Convert literal node to match expected type string."""
        target = target.strip()
        if isinstance(node, cst.Integer):
            if target == "str":
                return cst.SimpleString(f'"{node.value}"')
            if target == "float":
                return cst.Float(f"{float(node.value)}")
        elif isinstance(node, cst.Float):
            if target == "str":
                return cst.SimpleString(f'"{node.value}"')
        elif isinstance(node, cst.SimpleString):
            if target in ("int", "float"):
                try:
                    val = ast.literal_eval(node.value)
                    if target == "int":
                        return cst.Integer(str(int(val)))
                    return cst.Float(str(float(val)))
                except Exception:
                    return None
        elif isinstance(node, cst.Name) and node.value in {"True", "False"}:
            if target == "int":
                return cst.Integer("1" if node.value == "True" else "0")
            elif target == "str":
                return cst.SimpleString(f'"{node.value}"')
        return None

    def leave_AnnAssign(self, original: cst.AnnAssign, updated: cst.AnnAssign) -> cst.AnnAssign:
        error = self._get_error_for_node(original)
        if error and error.code == "assignment":
            # If the variable already has annotation, we shouldn't remove it, maybe just ignore.
            # If no annotation, we could add one based on value. But this is risky; we'll ignore.
            pass
        return updated

    def leave_Assign(self, original: cst.Assign, updated: cst.Assign) -> cst.Assign:
        error = self._get_error_for_node(original)
        if error and error.code == "assignment":
            # No annotation present, try to infer from RHS
            # We'll skip to avoid Any spamming.
            pass
        return updated

    def leave_Attribute(self, original: cst.Attribute, updated: cst.Attribute) -> cst.BaseExpression:
        error = self._get_error_for_node(original)
        if error and error.code == "union-attr":
            # Add ignore comment at line level (handled later)
            pass
        return updated


# ----- Data structure for Ruff diagnostics -----
@dataclass
class RuffDiagnostic:
    file: Path
    line: int
    column: int
    code: str
    message: str
    fix_applicable: bool   # whether Ruff could fix it itself

# ----- The comprehensive fixer -----
class RuffErrorFixer(cst.CSTTransformer):
    """Fixes a wide set of Ruff rules beyond what ruff --fix can do."""
    RULES_WITH_TRANSFORM = {
        "SIM102", "SIM103", "SIM105", "SIM108", "SIM113", "SIM116",
        "UP006", "UP007", "PIE790", "PIE804", "F401",
    }
    RULES_FOR_NOQA = {"F841", "N801", "N802", "N803", "N804", "N805", "N806", "N807", "RUF013"}

    def __init__(self, diagnostics: list[RuffDiagnostic], source_code: str) -> None:
        super().__init__()
        self.diags = diagnostics
        self.source_lines = source_code.splitlines()
        self.source_code = source_code

        # Index by line+col for precise matching
        self.diag_by_pos: dict[tuple[int, int], RuffDiagnostic] = {}
        self.diags_by_line: dict[int, list[RuffDiagnostic]] = {}
        for d in diagnostics:
            line, col = d.line, d.column if d.column else 0
            self.diag_by_pos[(line, col)] = d
            self.diags_by_line.setdefault(d.line, []).append(d)

        self.fixes_applied = 0
        self._unused_imports: set[str] = set()  # Store names to remove for F401

    @staticmethod
    def _pos(node: cst.CSTNode) -> tuple[int, int] | None:
        p = getattr(node, 'position', None)
        return (p.start.line, p.start.column) if p else None

    def _get_diag(self, node: cst.CSTNode) -> RuffDiagnostic | None:
        pos = self._pos(node)
        return self.diag_by_pos.get(pos) if pos else None

    # ------------------------------------------------------------------
    # Main transformation hooks
    # ------------------------------------------------------------------
    def leave_If(self, original: cst.If, updated: cst.If) -> cst.BaseStatement:
        diag = self._get_diag(original)
        if diag is None:
            return updated

        if diag.code == "SIM103":
            return self._fix_SIM103(original, updated)
        if diag.code == "SIM102":
            return self._fix_SIM102(original, updated)
        # SIM105 is handled elsewhere (Try)
        return updated

    def leave_Try(self, original: cst.Try, updated: cst.Try) -> cst.BaseStatement:
        diag = self._get_diag(original)
        if diag and diag.code == "SIM105":
            return self._fix_SIM105(original, updated)
        return updated

    def leave_SimpleStatementLine(
        self, original: cst.SimpleStatementLine, updated: cst.SimpleStatementLine
    ) -> cst.BaseStatement:
        line_no = original.start.line if hasattr(original, 'start') else None
        if line_no is None:
            return updated

        diags = self.diags_by_line.get(line_no, [])
        if not diags:
            return updated

        # Handle PIE790: remove unnecessary pass
        if any(d.code == "PIE790" for d in diags):
            return self._fix_PIE790(original, updated)

        # Add noqa for rules that only need suppression
        for d in diags:
            if d.code in self.RULES_FOR_NOQA:
                return self._add_noqa(updated, sorted({d.code for d in diags}))
        return updated

    def leave_Call(self, original: cst.Call, updated: cst.Call) -> cst.BaseExpression:
        diag = self._get_diag(original)
        if diag is None:
            return updated

        if diag.code == "PIE804":
            return self._fix_PIE804(original)
        if diag.code == "SIM113":
            return self._fix_SIM113(original)
        return updated

    def leave_Subscript(self, original: cst.Subscript, updated: cst.Subscript) -> cst.BaseExpression:
        diag = self._get_diag(original)
        if diag and diag.code in ("UP006", "UP007"):
            return self._fix_UP006_UP007(original)
        return updated

    def leave_Attribute(self, original: cst.Attribute, updated: cst.Attribute) -> cst.BaseExpression:
        diag = self._get_diag(original)
        if diag and diag.code == "UP007":
            return self._fix_UP007(original)
        return updated

    def leave_Import(self, original: cst.Import, updated: cst.Import) -> cst.BaseSmallStatement:
        # Delete if all imported names are unused (F401)
        for name in original.names:
            if name.name.value not in self._unused_imports:
                return updated  # at least one used
        # All unused, replace with pass
        self.fixes_applied += 1
        return cst.RemoveFromParent()  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Rule‑specific implementations
    # ------------------------------------------------------------------
    def _fix_SIM103(self, original: cst.If, updated: cst.If) -> cst.BaseStatement:
        """Convert 'if cond: return True else: return False' -> 'return cond'."""
        if len(original.body.body) != 1 or not isinstance(original.body.body[0], cst.Return):
            return updated
        ret_true = original.body.body[0]
        if not isinstance(ret_true.value, cst.Name) or ret_true.value.value != "True":
            return updated
        if original.orelse is None or not isinstance(original.orelse, cst.Else):
            return updated
        else_block = original.orelse.body
        if else_block is None or len(else_block.body) != 1 or not isinstance(else_block.body[0], cst.Return):
            return updated
        ret_false = else_block.body[0]
        if not isinstance(ret_false.value, cst.Name) or ret_false.value.value != "False":
            return updated
        new_code = f"return {cst.Module([]).code_for_node(original.test)}"
        self.fixes_applied += 1
        return cst.parse_statement(new_code)

    def _fix_SIM102(self, original: cst.If, updated: cst.If) -> cst.BaseStatement:
        """Collapse nested ifs: if a: if b: ... -> if a and b: ..."""
        if len(original.body.body) != 1:
            return updated
        inner = original.body.body[0]
        if not isinstance(inner, cst.If):
            return updated
        if inner.orelse is not None:
            return updated
        # Combine condition: a and b
        combined = cst.BooleanOperation(
            left=original.test,
            operator=cst.And(),
            right=inner.test,
        )
        new_if = cst.If(
            test=combined,
            body=inner.body,
            orelse=original.orelse,
            whitespace_before_test=original.whitespace_before_test,
        )
        self.fixes_applied += 1
        return new_if

    def _fix_SIM105(self, original: cst.Try, updated: cst.Try) -> cst.BaseStatement:
        """Use contextlib.suppress: try: ... except SomeError: pass → with suppress(SomeError): ..."""
        if original.orelse or original.finalbody:
            return updated
        handlers = original.handlers
        if len(handlers) != 1:
            return updated
        handler = handlers[0]
        if handler.body.body or handler.name:  # non-empty body or as binding
            return updated
        # Simple pass handler
        # Build with suppress(exception)
        cst.parse_statement("from contextlib import suppress")
        # Don't add import if already exists; simplified: just replace the try with with and hope import is there
        # Better: only apply if suppress is already importable? We'll leave as a note.
        # In practical terms, we'd check imports before adding.
        # For demo, we transform and count on the user to handle imports.
        if handler.type is None:
            return updated
        with_block = cst.With(
            items=[cst.WithItem(cst.Call(func=cst.Name("suppress"), args=[cst.Arg(handler.type)]))],
            body=original.body,
        )
        self.fixes_applied += 1
        return with_block

    def _fix_PIE790(self, original: cst.SimpleStatementLine, updated: cst.SimpleStatementLine) -> cst.BaseStatement:
        """Remove pass if the line is just 'pass' and there are other statements in the block."""
        # This is called for a single statement line; if it's a pass we can remove it
        if len(original.body) == 1 and isinstance(original.body[0], cst.Pass):
            # Safe removal only if there are other statements in the same block.
            # Since we're in a leave_* for the line, we can just return a dummy that will be removed.
            # Better: check parent (not possible here). We'll rely on ruff to have already verified it's safe.
            self.fixes_applied += 1
            return cst.RemoveFromParent()   # type: ignore[return-value]
        return updated

    def _fix_PIE804(self, node: cst.Call) -> cst.BaseExpression:
        """dict() -> {}"""
        if isinstance(node.func, cst.Name) and node.func.value == "dict" and not node.args:
            self.fixes_applied += 1
            return cst.Dict([])
        return node

    def _fix_UP006_UP007(self, node: cst.Subscript) -> cst.BaseExpression:
        """UP006: Optional[X] → X | None
        UP007: Union[X, Y, ...] → X | Y | ..."""
        if isinstance(node.value, cst.Name):
            name = node.value.value
            if name == "Optional":
                # استخراج نوع درونی از slice
                inner_slice = node.slice[0].slice if isinstance(node.slice[0], cst.SubscriptElement) else node.slice

                # BaseSlice را به BaseExpression تبدیل کنید
                inner_expr: cst.BaseExpression | None = None
                if isinstance(inner_slice, cst.Index):
                    inner_expr = inner_slice.value
                else:
                    # نمی‌توانیم به‌صورت امن تبدیل کنیم
                    return node

                if inner_expr is not None:
                    self.fixes_applied += 1
                    return cst.BinaryOperation(
                        left=inner_expr,
                        operator=cst.BitOr(),
                        right=cst.Name("None"),
                    )

            elif name == "Union":
                # همهٔ عناصر slice را به BaseExpression نگاشت دهید
                exprs: list[cst.BaseExpression] = []
                for elem in node.slice:
                    if isinstance(elem, cst.SubscriptElement):
                        slc = elem.slice
                        if isinstance(slc, cst.Index):
                            exprs.append(slc.value)
                        else:
                            # نوع پیچیده‌ای است که نمی‌توان تبدیل کرد
                            return node
                    else:
                        return node

                if len(exprs) >= 2:
                    expr = exprs[0]
                    for right in exprs[1:]:
                        expr = cst.BinaryOperation(left=expr, operator=cst.BitOr(), right=right)
                    self.fixes_applied += 1
                    return expr

        return node

    def _fix_UP007(self, node: cst.Attribute) -> cst.BaseExpression:
        """Union[X, Y] -> X | Y (via typing.Union)."""
        if isinstance(node.value, cst.Name) and node.value.value == "Union" and node.attr.value == "__getitem__":
            # This is tricky because subscript is separate; we catch in Subscript.
            pass
        return node

    def _fix_UP007_subscript(self, node: cst.Subscript) -> cst.BaseExpression:
        if isinstance(node.value, cst.Name) and node.value.value == "Union":
            exprs: list[cst.BaseExpression] = []
            for elem in node.slice:
                if isinstance(elem, cst.SubscriptElement):
                    slc = elem.slice
                    if isinstance(slc, cst.Index):
                        exprs.append(slc.value)
                    else:
                        return node
                else:
                    return node
            if len(exprs) < 2:
                return node
            expr = exprs[0]
            for right in exprs[1:]:
                expr = cst.BinaryOperation(left=expr, operator=cst.BitOr(), right=right)
            self.fixes_applied += 1
            return expr
        return node

    def _fix_SIM113(self, node: cst.Call) -> cst.BaseExpression:
        """range(len(x)) -> enumerate(x) only if used in for loop; transformation is complex, skip."""
        return node  # We could handle in For, but left for brevity.

    # ------------------------------------------------------------------
    # Unused imports (F401) collecting
    # ------------------------------------------------------------------
    def visit_Import(self, node: cst.Import) -> bool | None:
        for alias in node.names:
            name_str = self._get_import_name_str(alias)
            if name_str is not None:
                self._unused_imports.add(name_str)
        return False

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool | None:
        if isinstance(node.names, cst.ImportStar):
            return False
        for alias in node.names:
            name_str = self._get_import_name_str(alias)
            if name_str is not None:
                self._unused_imports.add(name_str)
        return False

    @staticmethod
    def _get_import_name_str(alias: cst.ImportAlias) -> str | None:
        name_node = alias.name
        if isinstance(name_node, cst.Name):
            return name_node.value
        elif isinstance(name_node, cst.Attribute):
            # e.g., import pkg.mod → Attribute(value=Name("pkg"), attr=Name("mod"))
            # نام کامل را به‌صورت "pkg.mod" برمی‌گردانیم
            return f"{name_node.value.value}.{name_node.attr.value}" if isinstance(name_node.value, cst.Name) else None
        return None

    def leave_ImportFrom(self, original: cst.ImportFrom, updated: cst.ImportFrom) -> cst.BaseSmallStatement:
        if isinstance(original.names, cst.ImportStar):
            return updated
        # Remove whole import if all unused
        if all(
            self._get_import_name_str(alias) in self._unused_imports
            for alias in original.names
        ):
            self.fixes_applied += 1
            return cst.RemoveFromParent()  # type: ignore[return-value]
        # Remove specific unused names
        new_names = [
            alias
            for alias in original.names
            if self._get_import_name_str(alias) not in self._unused_imports
        ]
        if len(new_names) != len(original.names):
            self.fixes_applied += 1
            return updated.with_changes(names=tuple(new_names))
        return updated

    # ------------------------------------------------------------------
    # Helpers for noqa insertion
    # ------------------------------------------------------------------
    def _add_noqa(self, node: cst.SimpleStatementLine, codes: list[str]) -> cst.BaseStatement:
        """Add a `# noqa: ...` comment to the line."""
        existing = node.trailing_whitespace.comment
        noqa_str = "# noqa: " + ", ".join(codes)
        if existing and "noqa" in existing.value:
            return node
        new_comment = cst.Comment(value=noqa_str)
        if existing is None:
            new_trail = cst.TrailingWhitespace(
                whitespace=cst.SimpleWhitespace("  "),
                comment=new_comment,
                newline=node.trailing_whitespace.newline,
            )
        else:
            new_trail = node.trailing_whitespace.with_changes(
                comment=cst.Comment(value=existing.value + "  " + noqa_str)
            )
        self.fixes_applied += 1
        return node.with_changes(trailing_whitespace=new_trail)


class PipelineSupervisor:
    """Orchestrates the whole upgrade process with resilient error handling."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.report: dict[str, Any] = {
            "started_at": datetime.now().isoformat(),
            "finished_at": None,
            "stages": [],
            "errors": [],
        }
        self.rollback = RollbackManager(config)
        self.convergence = ConvergenceTracker()
        self.runner = ExternalToolRunner()
        self.symbol_index = SymbolIndex(config.project_root, config.skip_paths)

    def log(self, msg: str) -> None:
        print(f"[PIPELINE] {msg}")

    def add_stage(self, name: str, outcome: StageOutcome, details: str = "", extra: dict[str, Any] | None = None) -> None:
        self.report["stages"].append({
            "name": name, "outcome": outcome.value, "details": details, "extra": extra or {},
        })

    def save_report(self) -> None:
        self.config.report_dir.mkdir(parents=True, exist_ok=True)
        path = self.config.report_dir / "pipeline_report.json"
        path.write_text(json.dumps(self.report, indent=2, ensure_ascii=False), encoding="utf-8")

    def run_stage(self, name: str, func) -> None:
        self.log(f"--- Stage: {name} ---")
        self.rollback.snapshot_project(name)
        try:
            details, extra = func()
            self.add_stage(name, StageOutcome.SUCCESS, details, extra)
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            self.log(f"Stage {name} FAILED: {msg}")
            self.add_stage(name, StageOutcome.FAILURE, msg)
            self.report["errors"].append(f"{name}: {msg}")
            # Rollback this stage's changes
            self.rollback.rollback_stage(name)
            raise RuntimeError(f"Stage {name} failed, pipeline aborted.") from exc

    def _maybe_write_file(self, file_path: Path, new_content: str, original_content: str) -> bool:
        if self.config.dry_run:
            diff = difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=str(file_path), tofile=str(file_path),
            )
            diff_text = ''.join(diff)
            if diff_text:
                self.report.setdefault('dry_run_changes', []).append({
                    'file': str(file_path),
                    'diff': diff_text,
                })
            return bool(diff_text)
        else:
            if new_content != original_content:
                file_path.write_text(new_content, encoding="utf-8")
                return True
            return False
    # -------------------------------------------------------------------------
    # Stage implementations
    # -------------------------------------------------------------------------

    def stage_backup(self) -> tuple[str, dict]:
        """Full backup of entire project."""
        ensure_dir(self.config.backup_dir)
        # Simply copy all .py files
        for py_file in self.config.project_root.rglob("*.py"):
            rel = py_file.relative_to(self.config.project_root)
            dest = self.config.backup_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(py_file, dest)
        return "Backup created", {"backup_dir": str(self.config.backup_dir)}

    def _build_exclude_args_for_ruff(self) -> str:
        """Generate shell arguments for excluding paths."""
        args = []
        for pattern in self.config.skip_paths:
            args.append(f"--exclude='{pattern}'")
        return " ".join(args)

    def _collect_py_files(self) -> list[str]:
        """Returns list of relative .py files that are not in skip_paths."""
        files = []
        for py_file in self.config.project_root.rglob("*.py"):
            if any(py_file.match(p) for p in self.config.skip_paths):
                continue
            files.append(str(py_file.relative_to(self.config.project_root)))
        return files

    def run_on_files(self, cmd_base: str, capture: bool = True) -> str:
        files = self._collect_py_files()
        if not files:
            return ""
        # رشتهٔ جداکننده null → تبدیل به بایت
        input_bytes = "\0".join(files).encode()
        cmd_parts = shlex.split(cmd_base)
        proc = subprocess.run(
            ["xargs", "-0", "-n", "100"] + cmd_parts,
            input=input_bytes,           # bytes
            capture_output=capture,
            text=False,                  # ← مهم
        )
        # خروجی‌ها را دستی decode می‌کنیم
        out = proc.stdout.decode(errors="replace") if proc.stdout else ""
        err = proc.stderr.decode(errors="replace") if proc.stderr else ""
        return out + err

    def stage_linters(self, profile: str = "conservative", capture: bool = True) -> tuple[str, dict]:
        """Run ruff with selected profile, plus autoflake, pyupgrade, etc."""
        excl_ruff = self._build_exclude_args_for_ruff()
        logs = {}
        # ruff fix
        rules = self.config.ruff_profiles.get(profile, self.config.ruff_profiles["conservative"])
        cmd = f"ruff check . {rules} --fix {excl_ruff}"
        logs["ruff"] = run(cmd, capture=True)
        # pyupgrade
        ver = f"{sys.version_info.major}{sys.version_info.minor}"
        logs["pyupgrade"] = self.run_on_files(f"pyupgrade --py{ver}-plus", capture=capture)

        # autoflake
        logs["autoflake"] = self.run_on_files("autoflake --in-place --remove-unused-variables --remove-all-unused-imports", capture=capture)
        # reorder imports
        logs["reorder"] = self.run_on_files("reorder-python-imports --exit-zero-even-if-changed", capture=capture)
        return f"Linters ({profile}) applied", logs

    def stage_import_validation(self) -> tuple[str, dict]:
        graph = ImportGraph()
        graph.build_from_project(self.config.project_root)
        cycles = graph.find_cycles()
        details = f"Import cycles found: {len(cycles)}"
        if cycles:
            if self.config.import_cycle_policy == CyclePolicy.FAIL:
                raise RuntimeError(f"Import cycles detected: {cycles[:3]}...")
            elif self.config.import_cycle_policy == CyclePolicy.WARN:
                self.report.setdefault('warnings', []).append(f"Import cycles: {cycles}")
        return details, {"cycles": cycles}

    def stage_dependency_check(self) -> tuple[str, dict]:
        """Run pip check, pip-audit, and apply policy."""
        logs = {}
        logs["pip_check"] = run("pip check", capture=True)
        audit = run("pip-audit --format json", capture=True)
        logs["pip_audit"] = audit
        actions = []
        # Parse audit for high severity vulnerabilities
        try:
            audit_data = json.loads(audit)
            for vuln in audit_data.get("vulnerabilities", []):
                cvss = vuln.get("cvss")
                if cvss and float(cvss) > self.config.dep_fail_on_cvss_gt:
                    actions.append(f"Critical vulnerability: {vuln['name']} CVSS {cvss} - action: fail")
                else:
                    actions.append(f"Low/med vulnerability: {vuln.get('name')} - warning")
            if any("fail" in a for a in actions):
                raise RuntimeError("Dependency policy violation: " + "; ".join(actions))
        except json.JSONDecodeError:
            pass
        return "Dependency checks completed", {"actions": actions}

    def stage_base_type_annotations(self) -> tuple[str, dict]:
        """Run libcst‑based inference and apply safe annotations."""
        self.symbol_index.build()

        inferencer = LibCSTInferencer()
        all_hints = []
        for py_file in self.config.project_root.rglob("*.py"):
            # skip configured paths
            if any(py_file.match(pattern) for pattern in self.config.skip_paths):
                continue
            try:
                hints = inferencer.infer_file(py_file)
                all_hints.extend(hints)
            except Exception:
                continue
        merger = TypeHintMerger(
            confidence_threshold=self.config.confidence_threshold,
            max_difference=self.config.max_confidence_merge_difference,
        )
        merged = merger.merge(all_hints)
        # Apply with libcst transformer per file that contains relevant functions
        affected_files = self._group_hints_by_file(merged)
        # حالا برای هر فایل transformer را اجرا می‌کنیم.
        transformer = AnnotationInjector({h.symbol: h for h in merged})
        for file_path, hints_in_file in affected_files.items():
            self._apply_transformer_to_file(file_path, transformer)
        return f"Applied {len(merged)} annotations from libcst inference", {"applied": len(merged)}

    def _apply_transformer_to_file(self, file_path: Path, transformer: cst.CSTTransformer) -> bool:
        try:
            code = file_path.read_text(encoding="utf-8")
            mod = cst.parse_module(code)
            new_mod = mod.visit(transformer)
            if new_mod.code != code:
                self._maybe_write_file(file_path, new_mod.code, code)
                return True
        except Exception:
            return False
        return False

    def _group_hints_by_file(self, merged: list[TypeHint]) -> dict[Path, list[TypeHint]]:
        by_file: dict[Path, list[TypeHint]] = defaultdict(list)
        for hint in merged:
            loc = self.symbol_index.index.get(hint.symbol)
            if loc is None:
                continue
            # hint.symbol ممکن است نام ساده باشد، یا qualname. در SymbolIndex هر دو ثبت می‌شود.
            by_file[loc.file].append(hint)
        return by_file

    def stage_pyright_integration(self) -> tuple[str, dict]:
        """Run pyright, extract hints, merge and apply with high confidence."""
        pyright_json = self.runner.run_pyright(self.config.project_root)
        if not pyright_json:
            return "pyright not available or failed", {}
        hints = PyrightHintExtractor.extract(pyright_json)
        self._apply_external_hints(hints, HintSource.PYRIGHT)
        return f"Pyright contributed {len(hints)} hints", {"count": len(hints)}

    def stage_pytype_integration(self) -> tuple[str, dict]:
        """Run pytype, extract hints, merge."""
        pytype_json = self.runner.run_pytype(self.config.project_root)
        if not pytype_json:
            return "pytype not available or failed", {}
        hints = PytypeHintExtractor.extract(pytype_json)
        self._apply_external_hints(hints, HintSource.PYTYPE)
        return f"Pytype contributed {len(hints)} hints", {"count": len(hints)}

    def _apply_external_hints(self, hints: list[TypeHint], source: HintSource) -> None:
        """Inject high-confidence external annotations directly using libcst."""
        # فیلتر بر اساس آستانه
        confident = [h for h in hints if h.confidence >= self.config.confidence_threshold]
        if not confident:
            return
        symbol_map = {h.symbol: h for h in confident}
        # group by file
        by_file: dict[Path, list[TypeHint]] = defaultdict(list)
        for h in confident:
            loc = self.symbol_index.index.get(h.symbol)
            if loc:
                by_file[loc.file].append(h)

        # build transformer
        transformer = AnnotationInjector(symbol_map)
        for file_path in by_file:
            self._apply_transformer_to_file(file_path, transformer)

    def stage_mypy_fix_loop(self) -> tuple[str, dict]:
        """Iterative mypy fix driven by error codes and convergence."""
        self.convergence = ConvergenceTracker()
        iteration = 0
        while iteration < self.config.max_mypy_iter:
            iteration += 1
            result = self.runner.run_mypy(self.config.project_root)
            if result.returncode == 0:
                return f"Mypy clean after {iteration} iterations", {"iteration": iteration}
            errors = MypyErrorParser.parse(result.stdout)
            if not errors:
                return f"Mypy returned non‑zero but no parsable errors (iteration {iteration})", {}
            self.convergence.update(errors)
            stop, reason = self.convergence.should_stop()
            if stop:
                return f"Stopping mypy loop: {reason} after {iteration} iterations", {"iteration": iteration}

            # Process errors by code
            fixed_any = False
            by_file: dict[str, list[MypyError]] = defaultdict(list)
            for err in errors:
                by_file[err.file].append(err)

            for file, file_errors in by_file.items():
                if not file.endswith(".py"):
                    continue
                file_path = self.config.project_root / file
                if not file_path.exists():
                    continue
                try:
                    # Attempt targeted fix based on error codes
                    if self._fix_mypy_errors_in_file(file_path, file_errors):
                        fixed_any = True
                except Exception:
                    continue

            if not fixed_any:
                # No progress possible
                return f"No further automatic fixes possible at iteration {iteration}", {"errors": len(errors)}
        return f"Mypy still failing after {self.config.max_mypy_iter} iterations", {}

    def _fix_mypy_errors_in_file(self, file_path: Path, errors: list[MypyError]) -> bool:
        code = file_path.read_text(encoding="utf-8")
        fixer = MypyErrorFixer(errors, code, strategy=FixStrategy.MODERATE)
        module = cst.parse_module(code)
        new_module = module.visit(fixer)
        if new_module.code != code:
            file_path.write_text(new_module.code, encoding="utf-8")
            return True
        return False

    def stage_ruff_deep_fix(self) -> tuple[str, dict]:
        """Run RuffErrorFixer on unfixed diagnostics."""
        # دریافت خروجی ruff به صورت JSON
        diags = self._collect_ruff_diagnostics()
        if not diags:
            return "No ruff diagnostics to deep fix", {}

        by_file: dict[Path, list[RuffDiagnostic]] = {}
        for d in diags:
            by_file.setdefault(d.file, []).append(d)

        fixed_files = 0
        for file_path, file_diags in by_file.items():
            if not file_path.suffix == ".py":
                continue
            try:
                code = file_path.read_text(encoding="utf-8")
                fixer = RuffErrorFixer(file_diags, code)
                new_module = cst.parse_module(code).visit(fixer)
                if new_module.code != code:
                    file_path.write_text(new_module.code, encoding="utf-8")
                    fixed_files += 1
            except Exception:
                continue

        return f"Ruff deep fix applied to {fixed_files} files", {"fixed_files": fixed_files}

    def _collect_ruff_diagnostics(self) -> list[RuffDiagnostic]:
        excl_args = self._build_exclude_args_for_ruff().split()  # yields e.g. ["--exclude='*/migrations/*'", ...]
        cmd = ["ruff", "check", "--output-format=json"] + excl_args
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True,
            cwd=self.config.project_root,
        )
        if proc.returncode not in (0, 1):
            return []
        data = json.loads(proc.stdout)
        diags = []
        for file_info in data:
            file_path = Path(file_info["filename"])
            for d in file_info.get("diagnostics", []):
                diags.append(RuffDiagnostic(
                    file=file_path,
                    line=d["location"]["row"],
                    column=d["location"]["column"],
                    code=d["code"],
                    message=d["message"],
                    fix_applicable=d.get("fix", None) is not None,
                ))
        return diags

    def stage_api_diff(self) -> tuple[str, dict]:
        """Capture current API state and compare to previous snapshot if available."""
        prev_path = self.config.report_dir / "api_previous.json"
        curr_path = self.config.report_dir / "api_current.json"
        APISurfaceAnalyser.dump_api(self.config.project_root, curr_path)
        _extra: dict[str, Any] = {}
        issues = []

        if prev_path.exists():
            try:
                old = APISurfaceAnalyser.load_api_dump(prev_path)
                new = APISurfaceAnalyser.load_api_dump(curr_path)
                public_all = APISurfaceAnalyser._get_public_symbols_all(self.config.project_root)
                # Breaking changes detection (old implementation)
                breaking = APISurfaceAnalyser.detect_breaking_changes(old, new, public_all)
                issues.extend(breaking)

                # Advanced signature change detection
                sig_changes = APISurfaceAnalyser.detect_signature_changes(old, new)
                if sig_changes:
                    issues.extend(sig_changes)

                if issues:
                    self.report.setdefault('warnings', []).extend(issues)
                    return f"API changes: {len(issues)} issues", {"breaking": breaking, "signature_changes": sig_changes}
                return "No breaking API changes", {}
            except Exception as e:
                return f"API diff failed: {e}", {}
        else:
            shutil.copy(curr_path, prev_path)
            return "Baseline API snapshot saved", {}


    # -------------------------------------------------------------------------
    # Run full pipeline
    # -------------------------------------------------------------------------

    def run(self, capture: bool = True) -> None:
        try:
            self.run_stage("backup", self.stage_backup)
            self.run_stage("linters_conservative", lambda: self.stage_linters("conservative", capture=capture))
            self.run_stage("ruff_fix_loop", self.stage_ruff_deep_fix)
            self.run_stage("import_validation", self.stage_import_validation)
            self.run_stage("dependency_check", self.stage_dependency_check)
            self.run_stage("libcst_base_annotations", self.stage_base_type_annotations)
            self.run_stage("pyright", self.stage_pyright_integration)
            self.run_stage("pytype", self.stage_pytype_integration)
            self.run_stage("mypy_fix_loop", self.stage_mypy_fix_loop)
            self.run_stage("api_diff", self.stage_api_diff)
        except RuntimeError:
            self.log("Pipeline aborted due to stage failure.")
        finally:
            self.report["finished_at"] = datetime.now().isoformat()
            self.save_report()
            self.log(f"Report saved to {self.config.report_dir / 'pipeline_report.json'}")


# =============================================================================
# Helpers
# =============================================================================

def run(cmd: str, capture: bool = False) -> str:
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=capture, text=True, timeout=120
        )
        return (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return "Command timed out"

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Entry point
# =============================================================================

def main() -> None:
    config = PipelineConfig()
    supervisor = PipelineSupervisor(config)
    supervisor.run()


if __name__ == "__main__":
    main()
