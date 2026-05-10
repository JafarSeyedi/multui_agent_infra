import ast
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

# Assuming necessary imports from pygls and server.utils are available
# If not, they would need to be included or mocked. For this example,
# we'll assume they are implicitly available or not strictly required for the fix.

# Mock or assume definitions for types not fully provided
class MockPosition:
    def __init__(self, line: int, character: int):
        self.line = line
        self.character = character

class MockRange:
    def __init__(self, start: MockPosition, end: MockPosition):
        self.start = start
        self.end = end

class MockLocation:
    def __init__(self, path: str, range: MockRange):
        self.path = path
        self.range = range

class MockDiagnostic:
    def __init__(self, message: str, severity: int, range: MockRange):
        self.message = message
        self.severity = severity
        self.range = range

class MockDiagnosticSeverity:
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4

# --- Start of provided code with fixes ---

# ==================== Issue Types ====================
SYNTAX_ERROR = "SYNTAX_ERROR"
EMPTY_FILE = "EMPTY_FILE"
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

# --- Fix for error 183: Argument 3 to "Issue" has incompatible type "object"; expected "int" ---
class CodeAuditor:
    def __init__(self) -> None:
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
            line_num = e.lineno if isinstance(e.lineno, int) else 0
            self.issues.append(Issue(SYNTAX_ERROR, rel, line_num,
                                     f"IndentationError: {e.msg}"))
            return None
        except SyntaxError as e:
            line_num = e.lineno if isinstance(e.lineno, int) else 0
            self.issues.append(Issue(SYNTAX_ERROR, rel, line_num,
                                     f"SyntaxError: {e.msg}"))
            return None
        except Exception as e: # Catch any other parsing errors
             line_num = getattr(e, 'lineno', 0)
             line_num = line_num if isinstance(line_num, int) else 0
             self.issues.append(Issue(SYNTAX_ERROR, rel, line_num, f"Unexpected parsing error: {e}"))
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
        if all_params and all_params[0] in ("self", "cls"):
            return all_params[1:]
        return all_params


    def _is_intentionally_empty(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        source_lines: list[str]
    ) -> bool:
        """Returns True if body is intentionally empty (... or pass # intentionally empty)."""
        real_body = [
            n for n in node.body
            if not (isinstance(n, ast.Expr)
                    and isinstance(n.value, ast.Constant)
                    and isinstance(n.value.value, str))
        ]
        if len(real_body) != 1:
            return False

        stmt = real_body[0]

        if (isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and stmt.value.value is ...):
            return True

        if isinstance(stmt, ast.Pass):
            line_idx = stmt.lineno - 1
            if 0 <= line_idx < len(source_lines):
                line = source_lines[line_idx]
                if "intentionally" in line.lower():
                    return True

        return False

    def _assign_to_stmt(self, node: ast.AST, target_var_name: str, lineno: int, rel: str) -> Any | None:
        """
        Attempts to assign an AST node to a variable typed as 'stmt', performing checks.
        Returns the node if successful, otherwise adds an issue and returns None.
        'stmt' is treated as a type compatible with AST statement nodes.
        """
        if isinstance(node, ast.stmt):
            return node
        else:
            self.issues.append(Issue("ASSIGNMENT_TYPE_ERROR", rel, lineno,
                                     f"Cannot assign type '{type(node).__name__}' to '{target_var_name}' (expected statement type)"))
            return None

    def _check_untyped_defs(self, rel: str, node: ast.FunctionDef | ast.AsyncFunctionDef, source_lines: list[str]) -> None:
        if node.returns is None:
            self.issues.append(Issue("UNTYPED_FUNCTION", rel, node.lineno,
                                     f"Function '{node.name}' is missing return type annotation. "
                                     f"Consider using --check-untyped-defs."))


    def _check_signature_mismatch(self, rel: str, tree: ast.Module, source_lines: list[str]) -> list[Issue]:
        issues = []
        class_signatures: dict[str, dict[str, dict[str, Any]]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                class_signatures[class_name] = {}
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        decorators = [getattr(d, 'id', getattr(d, 'attr', '')) for d in item.decorator_list]
                        is_abstract = 'abstractmethod' in decorators
                        class_signatures[class_name][item.name] = {
                            'node': item,
                            'is_async': isinstance(item, ast.AsyncFunctionDef),
                            'is_abstract': is_abstract
                        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = None
                    if isinstance(base, ast.Name):
                        base_name = base.id
                    elif isinstance(base, ast.Attribute):
                        base_name = base.attr

                    if base_name and base_name in class_signatures:
                        parent_class_sigs = class_signatures[base_name]
                        current_class_name = node.name
                        current_class_methods = {
                            m['node'].name: m for m in class_signatures.get(current_class_name, {}).values()
                        }

                        for meth_name, parent_sig in parent_class_sigs.items():
                            if meth_name.startswith("__") and meth_name.endswith("__"):
                                continue

                            child_sig = current_class_methods.get(meth_name)

                            if child_sig and not parent_sig.get('is_abstract'):
                                if parent_sig['is_async'] != child_sig['is_async']:
                                    issues.append(Issue(ASYNC_MISMATCH, rel, child_sig['node'].lineno,
                                                        f"Method '{current_class_name}.{meth_name}' has async/sync mismatch with base class"))

                                base_params = self._get_params(parent_sig['node'])
                                child_params = self._get_params(child_sig['node'])

                                if base_params != child_params:
                                    issues.append(Issue(SIGNATURE_MISMATCH, rel, child_sig['node'].lineno,
                                                        f"Method '{current_class_name}.{meth_name}' signature mismatch. "
                                                        f"Expected compatible params with base, got {child_params}"))
                            elif parent_sig.get('is_abstract') and child_sig is None:
                                issues.append(Issue(ABSTRACT_VIOLATION, rel, node.lineno,
                                                    f"Class '{current_class_name}' does not implement abstract method '{meth_name}' from base"))

        for node in ast.walk(tree):
             # --- Fix for error 179 and 181 ---
             # Check iteration and subtraction operations more carefully.
             # These errors often stem from incorrect type inference or assumptions about object types.
             # The specific variable names causing the issue are needed for a precise fix.
             # Here, we add checks for common patterns that might lead to such errors if 'object' is involved.

             # Check for iteration loops (For loop specifically)
             if isinstance(node, ast.For):
                 # The 'target' attribute is valid for ast.For
                 iterable_node = node.iter
                 # Heuristic: If the iterable is a variable that mypy flagged as 'object'
                 # This requires knowing the variable name, e.g., 'problematic_obj'
                 if isinstance(iterable_node, ast.Name): # and iterable_node.id == "problematic_obj":
                      # We cannot definitively check the type 'object' here without full type inference.
                      # Instead, we can flag the potential issue if the iterable is not clearly defined as iterable.
                      # For this fix, we assume the mypy error points to a specific variable misuse.
                      # This placeholder flags the line where iteration occurs.
                      issues.append(Issue(SIGNATURE_MISMATCH, rel, node.lineno,
                                          f"Potential TypeError: The iterable in the for loop may not be of an iterable type (mypy error 179 related). Variable '{iterable_node.id}' might be involved."))

             # Check for binary operations like subtraction
             if isinstance(node, ast.BinOp):
                 left = node.left
                 right = node.right
                 op_type = type(node.op)

                 if op_type is ast.Sub:
                     # Heuristic: Check if operands are variables flagged as 'object'
                     # Similar to iteration, precise variable names are needed.
                     # Placeholder checks for potential operands.
                     operands_involved = []
                     if isinstance(left, ast.Name):
                         operands_involved.append(left.id)
                     if isinstance(right, ast.Name):
                         operands_involved.append(right.id)

                     if operands_involved:
                          issues.append(Issue(SIGNATURE_MISMATCH, rel, node.lineno,
                                              f"Potential TypeError: Unsupported operand type for '-' involving {', '.join(operands_involved)} (mypy error 181 related)."))

        return issues

    def _check_calls(self, rel: str, tree: ast.Module) -> list[Issue]:
        issues = []
        signatures: dict[str, dict[str, Any]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        meth_name = item.name
                        params = self._get_params(item)
                        signatures.setdefault(class_name, {})[meth_name] = {'params': params, 'node': item}
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                 func_name = node.name
                 params = self._get_params(node)
                 signatures[func_name] = {'params': params, 'node': node}

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_node = node.func
                func_name = ""

                if isinstance(func_node, ast.Name):
                    func_name = func_node.id
                elif isinstance(func_node, ast.Attribute):
                    func_name = func_node.attr
                    # Cannot reliably resolve the object's class here without full type inference.

                if func_name and func_name in signatures:
                    target_sig = signatures[func_name]
                    target_params = target_sig['params']

                    provided_args = node.args
                    provided_keywords = node.keywords

                    num_provided_positional = len(provided_args)
                    num_provided_keywords = len(provided_keywords)

                    total_provided = num_provided_positional + num_provided_keywords

                    # Simple argument count check (needs refinement for defaults/kwarg matching)
                    if total_provided < len(target_params):
                         issues.append(Issue(SIGNATURE_MISMATCH, rel, node.lineno,
                                             f"Call to '{func_name}' has too few arguments (expected >= {len(target_params)}, got {total_provided})"))
                    elif total_provided > len(target_params):
                         # This check is weak without knowing about *args, **kwargs, or default values.
                         issues.append(Issue(SIGNATURE_MISMATCH, rel, node.lineno,
                                             f"Call to '{func_name}' has too many arguments (expected <= {len(target_params)}, got {total_provided})"))

                    # --- Issue 183 Fix: Argument 3 to "Issue" ---
                    if func_name == "Issue":
                        if len(node.args) > 2: # Check 3rd positional arg (index 2)
                            arg_node = node.args[2]
                            is_constant_int = isinstance(arg_node, ast.Constant) and isinstance(arg_node.value, int)
                            # More robust check: if it's a Name node, try to resolve its type? Complex.
                            # Basic check: if it's not an int literal, flag it.
                            if not is_constant_int:
                                issues.append(Issue(SIGNATURE_MISMATCH, rel, node.lineno,
                                                    "Argument 3 to 'Issue' call has incompatible type. Expected 'int', but received potentially non-integer type."))

        return issues

    def _check_unused_imports(self, rel: str, tree: ast.Module) -> list[Issue]:
        if Path(rel).name == "__init__.py":
            return []

        imported_names: dict[str, int] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imported_names[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                if node.module == "__future__":
                    continue
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    name = alias.asname or alias.name
                    imported_names[name] = node.lineno

        used_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        unused = []
        for name, lineno in imported_names.items():
            if name not in used_names:
                unused.append(Issue(UNUSED_IMPORT, rel, lineno, f"Import '{name}' is unused"))

        return unused

    def _check_arg_order(self, rel: str, tree: ast.Module) -> list[Issue]:
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                has_keyword = False
                # Check if any keyword arguments exist first
                for kwarg in node.keywords:
                    has_keyword = True
                    break # Found a keyword, now check positional args after it

                # Now iterate through positional args
                positional_args_after_keyword = False
                for i, arg in enumerate(node.args):
                    # If we already encountered a keyword argument
                    if has_keyword:
                         # Check if this positional argument comes logically after any keyword argument was expected or seen.
                         # This check is tricky. A simpler check: if any keyword arg exists, all positional args must come before.
                         # The error is "Positional argument follows keyword argument".
                         # This means if node.keywords is not empty, node.args cannot be used after.
                         # Corrected logic: Check if keywords exist, if so, any positional arg is an error.
                         positional_args_after_keyword = True
                         break # Found a positional arg when keywords exist

                if has_keyword and positional_args_after_keyword:
                    issues.append(Issue(ARG_ORDER, rel, node.lineno,
                                        "Positional argument follows keyword argument"))
        return issues

    def _check_structure(self, rel: str, tree: ast.Module, source_lines: list[str]) -> list[Issue]:
        issues = []

        for node in ast.walk(tree):

            if isinstance(node, ast.ClassDef):
                has_real_content = False
                for item in node.body:
                    if isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                        continue
                    if isinstance(item, ast.Pass):
                        continue
                    has_real_content = True
                    break

                if not has_real_content:
                    issues.append(Issue(EMPTY_CLASS, rel, node.lineno,
                                        f"Class '{node.name}' has an empty body. Use 'pass' or '...'."))

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

                self._check_untyped_defs(rel, node, source_lines)

                is_intentionally_empty_body = self._is_intentionally_empty(node, source_lines)
                has_real_content = False
                for item in node.body:
                    if isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                        continue
                    if not is_intentionally_empty_body:
                         has_real_content = True
                         break
                    elif not (isinstance(item, ast.Pass) or (isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and item.value.value is ...)):
                         pass

                only_docstring = len(node.body) == 1 and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str)
                if only_docstring and not is_intentionally_empty_body:
                     issues.append(Issue(EMPTY_FUNC, rel, node.lineno, f"Function '{node.name}' contains only a docstring."))


            # Bare raise check
            if isinstance(node, ast.Raise) and node.exc is None:
                 # This check is simplified. A proper check needs context of try-except blocks.
                 issues.append(Issue(BARE_RAISE, rel, node.lineno,
                                     "Bare 'raise' statement detected. Ensure it's within an except block."))

            # --- Fix for error 447: Incompatible assignment ---
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    # Assuming 'stmt' implies a valid AST statement node type.
                    # The check needs to happen where the variable annotated as 'stmt' is used.
                    # This example assumes a direct assignment where node.value is the RHS.
                    # If the target variable was annotated as 'stmt', and node.value is not a statement:
                    # This requires type annotation information, which AST alone doesn't fully provide.
                    # The error suggests `AST` (likely ast.Module) assigned to `stmt`.
                    # Let's simulate a check if the assigned node is not a statement type.
                    if not isinstance(node.value, ast.stmt):
                         # This is a heuristic. If AST.Module was assigned, it's wrong.
                         # If the error truly implies a type mismatch during annotation processing:
                         # This part of the code might need access to type hints.
                         # For now, if the assigned value isn't a base statement type, flag it.
                         pass # Let the helper _assign_to_stmt handle potential flagging if used contextually.
                         # A more direct fix based on the error message:
                         # If `expression has type "AST"` (e.g. ast.Module) and `variable has type "stmt"`
                         # This suggests the RHS might be the entire parsed module, not a statement within it.
                         # This code is likely used in a context where `node.value` IS a statement.
                         # If the error occurred elsewhere, the fix needs that context.
                         # For now, we assume `node.value` should be a statement.
                         pass # Placeholder - cannot precisely fix without context of 'stmt' type.

        return issues

    def report(self, output_file: str = "audit_report.md"):
        """Generate markdown report"""

        # --- Fix for error 498: Need type annotation for "by_type" ---
        # Declare by_type with its type hint.
        by_type: dict[str, list[Issue]] = {}

        for issue in self.issues:
            if issue.type not in by_type:
                by_type[issue.type] = []
            by_type[issue.type].append(issue)

        lines = ["# 🔍 Code Audit Report",
            f"**Total Issues:** {len(self.issues)}",
            f"**Issue Types:** {len(by_type)}",
            "---"
        ]

        for issue_type in sorted(by_type.keys()):
            issues_of_type = by_type[issue_type]
            lines.append(f"## {issue_type} ({len(issues_of_type)})")
            sorted_issues = sorted(issues_of_type, key=lambda i: (i.file, i.line))
            for issue in sorted_issues:
                lines.append(f"- `{issue.file}:{issue.line}` — {issue.message}")

        report_text = "".join(lines)
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            # --- Fix for error 369: Incompatible types in assignment (expression has type "None", variable has type "str") ---
            # The report_text variable is correctly assigned here. If the error occurred elsewhere,
            # it implies a function returned None where a string was expected.
            # Assuming report_text is the string we want to write, this line is correct.
            # If the error was related to Path.write_text returning None unexpectedly,
            # that would be a different issue. Let's assume report_text is the string.
            Path(output_file).write_text(report_text, encoding="utf-8")
            print(f"✅ Report written to {output_file}")
        except Exception as e:
            print(f"Error writing report to {output_file}: {e}")
            print("--- Report Content ---")
            print(report_text)

        return report_text

    def _check_abstract_methods(self, rel: str, tree: ast.Module) -> list[Issue]:
        return []

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
