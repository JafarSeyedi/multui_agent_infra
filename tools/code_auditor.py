"""
tools/code_auditor.py
Static code analyzer for Python projects
"""

import ast
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Iterator

# ==================== Issue Types ====================
SYNTAX_ERROR = "SYNTAX_ERROR"
EMPTY_FILE = "EMPTY_FILE"
# UNDEFINED_NAME = "UNDEFINED_NAME"
ABSTRACT_VIOLATION = "ABSTRACT_VIOLATION"
SIGNATURE_MISMATCH = "SIGNATURE_MISMATCH"
ASYNC_MISMATCH = "ASYNC_MISMATCH"
UNUSED_IMPORT = "UNUSED_IMPORT"
ARG_ORDER = "ARG_ORDER"
EMPTY_FUNC = "EMPTY_FUNC"
EMPTY_CLASS = "EMPTY_CLASS"
ABSTRACT_BODY = "ABSTRACT_BODY"
MISSING_PASS = "MISSING_PASS"
BARE_RAISE = "BARE_RAISE"
WRONG_ABSTRACT = "WRONG_ABSTRACT"
# TOO_LONG_FUNC = "TOO_LONG_FUNC"
# TOO_MANY_PARAMS = "TOO_MANY_PARAMS"
# MAGIC_NUMBER = "MAGIC_NUMBER"
# MISSING_DOCSTRING = "MISSING_DOCSTRING"
BARE_EXCEPT = "BARE_EXCEPT"
MUTABLE_DEFAULT = "MUTABLE_DEFAULT"


@dataclass
class Issue:
    type: str
    file: str
    line: int
    message: str

    def __str__(self):
        return f"[{self.type}] {self.file}:{self.line} — {self.message}"


class CodeAuditor:
    def __init__(self):
        self.issues: list[Issue] = []

    def _iter_files(self, root: str) -> Iterator[tuple[str, str, ast.Module | None]]:
        """Yield (relative_path, source, ast_tree) for each .py file"""
        root_path = Path(root).resolve()
        for py_file in root_path.rglob("*.py"):
            rel = str(py_file.relative_to(root_path))
            try:
                source = py_file.read_text(encoding="utf-8")
            except Exception as e:
                self.issues.append(Issue("READ_ERROR", rel, 0, str(e)))
                continue

            if not source.strip():
                self.issues.append(Issue(EMPTY_FILE, rel, 0, "File is empty"))
                yield rel, source, None
                continue

            tree = self._check_syntax(rel, source)
            yield rel, source, tree

    def _check_syntax(self, rel: str, source: str) -> ast.Module | None:
        try:
            return ast.parse(source, filename=rel)
        except IndentationError as e:
            self.issues.append(Issue(SYNTAX_ERROR, rel, e.lineno or 0,
                                     f"IndentationError: {e.msg}"))
            return None
        except SyntaxError as e:
            self.issues.append(Issue(SYNTAX_ERROR, rel, e.lineno or 0,
                                     f"SyntaxError: {e.msg}"))
            return None

    @staticmethod
    def _get_params(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
        """Return parameter names excluding 'self' and 'cls'."""
        args = func_node.args
        all_params = (
            [a.arg for a in args.posonlyargs] +
            [a.arg for a in args.args] +
            [a.arg for a in args.kwonlyargs] +
            ([args.vararg.arg] if args.vararg else []) +
            ([args.kwarg.arg] if args.kwarg else [])
        )
        return [p for p in all_params if p not in ("self", "cls")]

    @staticmethod
    def _is_intentionally_empty(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        source_lines: list[str]
    ) -> bool:
        """Returns True if body is intentionally empty (... or pass # intentionally empty)."""
        # strip docstring from body
        real_body = [
            n for n in node.body
            if not (isinstance(n, ast.Expr)
                    and isinstance(n.value, ast.Constant)
                    and isinstance(n.value.value, str))
        ]
        if len(real_body) != 1:
            return False

        stmt = real_body[0]

        # ... (Ellipsis)
        if (isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and stmt.value.value is ...):
            return True

        # pass  # intentionally empty
        if isinstance(stmt, ast.Pass):
            line = source_lines[stmt.lineno - 1]
            if "intentionally" in line.lower():
                return True

        return False

    # def _check_undefined_names(self, rel: str, tree: ast.Module) -> list[Issue]:
    #     """Check for NameError-like issues (basic heuristic)"""
    #     defined = set()
    #     issues = []

    #     for node in ast.walk(tree):
    #         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
    #             defined.add(node.name)
    #         elif isinstance(node, ast.Import):
    #             for alias in node.names:
    #                 defined.add(alias.asname or alias.name.split(".")[0])
    #         elif isinstance(node, ast.ImportFrom):
    #             for alias in node.names:
    #                 if alias.name != "*":
    #                     defined.add(alias.asname or alias.name)
    #         elif isinstance(node, (ast.Assign, ast.AnnAssign)):
    #             for target in ast.walk(node):
    #                 if isinstance(target, ast.Name) and isinstance(target.ctx, ast.Store):
    #                     defined.add(target.id)

    #     for node in ast.walk(tree):
    #         if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
    #             if node.id not in defined and node.id not in dir(__builtins__):
    #                 issues.append(Issue(UNDEFINED_NAME, rel, node.lineno,
    #                                     f"Name '{node.id}' may be undefined"))
    #     return issues
    def _check_abstract_methods(self, rel: str, tree: ast.Module) -> list[Issue]:
        """Check if concrete classes implement all abstract methods"""
        issues = []
        classes = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                abstract_methods = set()
                concrete_methods = set()

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        decorators = [getattr(d, 'id', getattr(d, 'attr', ''))
                                      for d in item.decorator_list]
                        if 'abstractmethod' in decorators:
                            abstract_methods.add(item.name)
                        else:
                            concrete_methods.add(item.name)

                classes[node.name] = {
                    'abstract': abstract_methods,
                    'concrete': concrete_methods,'bases': [getattr(b, 'id', getattr(b, 'attr', '')) for b in node.bases],
                    'lineno': node.lineno
                }

        for cls_name, info in classes.items():
            if not info['abstract']:
                for base in info['bases']:
                    if base in classes:
                        missing = classes[base]['abstract'] - info['concrete']
                        for method in missing:
                            issues.append(Issue(ABSTRACT_VIOLATION, rel, info['lineno'],
                                                f"Class '{cls_name}' must implement abstract method '{method}' from '{base}'"))
        return issues

    @staticmethod
    def _get_params(func_node):
        args = func_node.args
        all_params = (
            [a.arg for a in args.posonlyargs] +
            [a.arg for a in args.args] +        # ← self اینجاست
            [a.arg for a in args.kwonlyargs] +
            ([args.vararg.arg] if args.vararg else []) +
            ([args.kwarg.arg] if args.kwarg else [])
        )
        return [p for p in all_params if p not in ("self", "cls")]

    def _check_signature_mismatch(self, rel: str, tree: ast.Module) -> list[Issue]:
        issues = []
        class_methods: dict[str, dict] = {}

        # جمع‌آوری متدهای هر کلاس
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_methods[node.name] = {
                    m.name: m
                    for m in node.body
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))  # ← این خط را اضافه کن
                }

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            base_names = [
                b.id if isinstance(b, ast.Name) else
                b.attr if isinstance(b, ast.Attribute) else None
                for b in node.bases
            ]

            for base_name in base_names:
                if base_name not in class_methods:
                    continue

                for meth_name, base_m in class_methods[base_name].items():
                    if meth_name.startswith("__") and meth_name.endswith("__"):
                        continue
                    child_m = class_methods.get(node.name, {}).get(meth_name)
                    if child_m is None:
                        continue

                    # async/sync
                    if isinstance(base_m, ast.AsyncFunctionDef) != isinstance(child_m, ast.AsyncFunctionDef):
                        issues.append(Issue(ASYNC_MISMATCH, rel, child_m.lineno,
                                            f"'{node.name}.{meth_name}': async/sync mismatch"))

                    # signature
                    base_params = self._get_params(base_m)
                    child_params = self._get_params(child_m)
                    if base_params != child_params:
                        issues.append(Issue(SIGNATURE_MISMATCH, rel, child_m.lineno,
                                            f"'{node.name}.{meth_name}': "
                                            f"expected {base_params}, got {child_params}"))

        return issues

    def _check_calls(self, rel: str, tree: ast.Module) -> list[Issue]:
        issues = []
        signatures = {}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = node.args
                # self/cls را از حساب خارج کن
                param_names = [a.arg for a in args.args]
                offset = 1 if param_names and param_names[0] in ("self", "cls") else 0
                total = len(args.args) - offset
                required = total - len(args.defaults)
                signatures[node.name] = {'required': required, 'total': total}

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            # فقط function call مستقیم (نه method call)
            if not isinstance(node.func, ast.Name):
                continue

            func_name = node.func.id
            if func_name not in signatures:
                continue

            sig = signatures[func_name]
            provided = len(node.args) + len(node.keywords)

            if provided < sig['required']:
                issues.append(Issue(SIGNATURE_MISMATCH, rel, node.lineno,
                                    f"Call to '{func_name}' missing required arguments "
                                    f"(needs {sig['required']}, got {provided})"))
            elif provided > sig['total']:
                issues.append(Issue(SIGNATURE_MISMATCH, rel, node.lineno,
                                    f"Call to '{func_name}' has too many arguments "
                                    f"(max {sig['total']}, got {provided})"))
        return issues

    def _check_unused_imports(self, rel: str, tree: ast.Module) -> list[Issue]:
        """Check for unused imports"""
        if Path(rel).name == "__init__.py":
            return []

        imported: dict[str, int] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "__future__":
                    continue
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    name = alias.asname or alias.name
                    imported[name] = node.lineno
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imported[name] = node.lineno

        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used.add(node.value.id)

        return [
            Issue(UNUSED_IMPORT, rel, lineno, f"Import '{name}' is unused")
            for name, lineno in imported.items()
            if name not in used
        ]

    def _check_arg_order(self, rel: str, tree: ast.Module) -> list[Issue]:
        """Check for positional arguments after keyword arguments"""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                seen_keyword = False
                for arg in node.args:
                    if seen_keyword:
                        issues.append(Issue(ARG_ORDER, rel, node.lineno,
                                            "Positional argument follows keyword argument"))
                        break
                for _ in node.keywords:
                    seen_keyword = True
        return issues
    def _check_structure(self, rel: str, tree: ast.Module, source_lines: list[str]) -> list[Issue]:
        """Check code structure issues"""
        issues = []

        for node in ast.walk(tree):

            # --- Empty class ---
            if isinstance(node, ast.ClassDef):
                bases = [getattr(b, 'id', getattr(b, 'attr', '')) for b in node.bases]
                has_abc = any(b in ('ABC', 'ABCMeta') for b in bases)

                non_trivial = [
                    n for n in node.body
                    if not isinstance(n, ast.Pass)
                    and not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))
                ]
                if not non_trivial:
                    issues.append(Issue(EMPTY_CLASS, rel, node.lineno,
                                        f"Class '{node.name}' has empty body"))

                # --- @abstractmethod without ABC ---
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        decorators = [getattr(d, 'id', getattr(d, 'attr', ''))for d in item.decorator_list]
                        if 'abstractmethod' in decorators and not has_abc:
                            issues.append(Issue(WRONG_ABSTRACT, rel, item.lineno,
                                                f"'{node.name}.{item.name}' uses @abstractmethod but class doesn't inherit ABC"))

                # # --- Missing docstring for public class ---
                # if not node.name.startswith('_'):
                #     has_docstring = (
                #         node.body
                #         and isinstance(node.body[0], ast.Expr)
                #         and isinstance(node.body[0].value, ast.Constant)
                #         and isinstance(node.body[0].value.value, str)
                #     )
                #     if not has_docstring:
                #         issues.append(Issue(MISSING_DOCSTRING, rel, node.lineno,
                #                             f"Public class '{node.name}' missing docstring"))

            # --- Function/method checks ---
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorators = [getattr(d, 'id', getattr(d, 'attr', ''))
                              for d in node.decorator_list]
                is_abstract = 'abstractmethod' in decorators

                # strip docstring for real body analysis
                real_body = [
                    n for n in node.body
                    if not (isinstance(n, ast.Expr)
                            and isinstance(n.value, ast.Constant)
                            and isinstance(n.value.value, str))
                ]

                has_only_ellipsis = (
                    len(real_body) == 1
                    and isinstance(real_body[0], ast.Expr)
                    and isinstance(real_body[0].value, ast.Constant)
                    and real_body[0].value.value is ...
                )
                has_only_pass = (
                    len(real_body) == 1
                    and isinstance(real_body[0], ast.Pass)
                )

                # Empty function check — با _is_intentionally_empty هماهنگ
                if not is_abstract and 'property' not in decorators:
                    is_empty = not real_body or has_only_pass or has_only_ellipsis
                    if is_empty and not self._is_intentionally_empty(node, source_lines):
                        issues.append(Issue(EMPTY_FUNC, rel, node.lineno,
                                            f"Function '{node.name}' has empty body "
                                            f"(use '...' or 'pass  # intentionally empty')"))

                # Abstract with body
                if is_abstract and real_body and not has_only_ellipsis and not has_only_pass:
                    issues.append(Issue(ABSTRACT_BODY, rel, node.lineno,
                                        f"Abstract method '{node.name}' should have empty body (use ... or pass)"))

                # # Too long function (>50 lines)
                # func_lines = node.end_lineno - node.lineno + 1
                # if func_lines > 50:
                #     issues.append(Issue(TOO_LONG_FUNC, rel, node.lineno,
                #                         f"Function '{node.name}' is too long ({func_lines} lines, max 50)"))

                # # Too many parameters (>5)
                # total_params = (
                #     len(node.args.posonlyargs) +
                #     len(node.args.args) +
                #     len(node.args.kwonlyargs) +
                #     (1 if node.args.vararg else 0) +
                #     (1 if node.args.kwarg else 0)
                # )
                # if node.args.args and node.args.args[0].arg in ('self', 'cls'):
                #     total_params -= 1
                # if total_params > 5:
                #     issues.append(Issue(TOO_MANY_PARAMS, rel, node.lineno,
                #                         f"Function '{node.name}' has too many parameters ({total_params}, max 5)"))

                # # Missing docstring for public function
                # if not node.name.startswith('_') and not is_abstract:
                #     has_docstring = (
                #         node.body
                #         and isinstance(node.body[0], ast.Expr)
                #         and isinstance(node.body[0].value, ast.Constant)
                #         and isinstance(node.body[0].value.value, str)
                #     )
                #     if not has_docstring:
                #         issues.append(Issue(MISSING_DOCSTRING, rel, node.lineno,
                #                             f"Public function '{node.name}' missing docstring"))

                # Bare except
                for item in ast.walk(node):
                    if isinstance(item, ast.ExceptHandler):
                        if item.type is None:
                            issues.append(Issue(BARE_EXCEPT, rel, item.lineno,
                                                "Bare 'except:' catches all exceptions (use specific exception types)"))

                # Mutable default arguments
                for default in node.args.defaults + node.args.kw_defaults:
                    if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append(Issue(MUTABLE_DEFAULT, rel, node.lineno,
                                            f"Function '{node.name}' has mutable default argument"))# --- Bare raise outside except ---
            if isinstance(node, ast.Raise) and node.exc is None:
                in_except = any(
                    isinstance(parent, ast.ExceptHandler)
                    and any(child is node for child in ast.walk(parent))
                    for parent in ast.walk(tree)
                    if isinstance(parent, ast.ExceptHandler)
                )
                if not in_except:
                    issues.append(Issue(BARE_RAISE, rel, node.lineno,
                                        "Bare 'raise' used outside except block"))

            # # --- Magic numbers ---
            # if isinstance(node, ast.Constant):
            #     if isinstance(node.value, (int, float)) and node.value not in (0, 1, -1, 2):
            #         issues.append(Issue(MAGIC_NUMBER, rel, node.lineno,
            #                             f"Magic number {node.value} should be a named constant"))

        return issues

    def audit(self, path: str):
        """Run all checks on the given path"""
        for rel, source, tree in self._iter_files(path):
            if tree is None:
                continue
            source_lines = source.splitlines()
            # for issue in self._check_signature_mismatch(rel, tree):
            #     print(f"SIG: {issue}")
            
            # for issue in self._check_calls(rel, tree):
            #     print(f"CALL: {issue}")
            # self.issues.extend(self._check_undefined_names(rel, tree))
            self.issues.extend(self._check_abstract_methods(rel, tree))
            self.issues.extend(self._check_signature_mismatch(rel, tree))
            self.issues.extend(self._check_calls(rel, tree))
            self.issues.extend(self._check_unused_imports(rel, tree))
            self.issues.extend(self._check_arg_order(rel, tree))
            self.issues.extend(self._check_structure(rel, tree, source_lines))

    def report(self, output_file: str = "audit_report.md"):
        """Generate markdown report"""
        by_type = {}
        for issue in self.issues:
            by_type.setdefault(issue.type, []).append(issue)

        lines = [
            "# 🔍 Code Audit Report\n",
            f"**Total Issues:** {len(self.issues)}\n",
            f"**Issue Types:** {len(by_type)}\n",
            "---\n"
        ]

        for issue_type in sorted(by_type.keys()):
            issues = by_type[issue_type]
            lines.append(f"\n## {issue_type} ({len(issues)})\n")
            for issue in issues:
                lines.append(f"- `{issue.file}:{issue.line}` — {issue.message}\n")

        report_text = "".join(lines)
        Path(output_file).write_text(report_text, encoding="utf-8")
        print(f"✅ Report written to {output_file}")
        return report_text


def main():
    if len(sys.argv) < 2:
        print("Usage: python code_auditor.py <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]
    auditor = CodeAuditor()
    auditor.audit(project_path)
    auditor.report()


if __name__ == "__main__":
    main()
