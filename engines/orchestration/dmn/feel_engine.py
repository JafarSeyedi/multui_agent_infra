"""FEEL expression engine for decision logic.

Complete FEEL coverage progressively with strict typing and function libraries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ...expression.evaluator import EvaluationContext


class FEELError(Exception):
    pass


@dataclass
class FEELFunction:
    name: str
    parameters: list[str]
    func: Any


class FEELEngine:
    def __init__(self) -> None:
        self._functions: dict[str, FEELFunction] = {}
        self._register_builtins()

    def evaluate(self, expression: str, context: EvaluationContext | dict[str, Any]) -> Any:
        if isinstance(context, EvaluationContext):
            variables = context.variables
        else:
            variables = context

        expr = expression.strip()

        if not expr:
            return None

        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]

        if expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]

        if expr == "true":
            return True
        if expr == "false":
            return False
        if expr == "null":
            return None

        try:
            return float(expr) if "." in expr else int(expr)
        except ValueError:
            pass

        if expr.startswith("[") and expr.endswith("]"):
            inner = expr[1:-1].strip()
            if not inner:
                return []
            parts = self._split_list_items(inner)
            return [self.evaluate(p.strip(), variables) for p in parts]

        if expr.startswith("not(") and expr.endswith(")"):
            inner = expr[4:-1].strip()
            return not bool(self.evaluate(inner, variables))

        if " and " in expr:
            parts = expr.split(" and ", 1)
            return self.evaluate(parts[0].strip(), variables) and self.evaluate(parts[1].strip(), variables)

        if " or " in expr:
            parts = expr.split(" or ", 1)
            return self.evaluate(parts[0].strip(), variables) or self.evaluate(parts[1].strip(), variables)

        if "between " in expr:
            return self._evaluate_between(expr, variables)

        for op in ["<=", ">=", "!=", "<>", "<", ">"]:
            if op in expr:
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    left = self.evaluate(parts[0].strip(), variables)
                    right = self.evaluate(parts[1].strip(), variables)
                    if left is not None and right is not None:
                        if op == "<=":
                            return left <= right
                        if op == ">=":
                            return left >= right
                        if op in ("!=", "<>"):
                            return left != right
                        if op == "<":
                            return left < right
                        if op == ">":
                            return left > right

        if expr.endswith("]") and "[" in expr:
            bracket_start = expr.index("[")
            collection_name = expr[:bracket_start].strip()
            index_expr = expr[bracket_start + 1:-1].strip()
            collection = variables.get(collection_name) if isinstance(variables, dict) else None
            if collection is not None and isinstance(collection, (list, tuple)):
                try:
                    index = int(index_expr) - 1
                    return collection[index]
                except (ValueError, IndexError):
                    pass

        if expr in variables:
            return variables[expr]

        func_match = re.match(r"^(\w+)\((.*)\)$", expr)
        if func_match:
            func_name = func_match.group(1).lower()
            args_str = func_match.group(2).strip()
            args = [self.evaluate(a.strip(), variables) for a in args_str.split(",")] if args_str else []
            return self._call_function(func_name, args)

        for var_name, var_value in variables.items() if isinstance(variables, dict) else []:
            if expr == var_name:
                return var_value

        return expr

    def _evaluate_between(self, expr: str, variables: dict[str, Any]) -> bool:
        match = re.match(r"(.+?)\s+between\s+(.+?)\s+and\s+(.+)", expr)
        if match:
            value = self.evaluate(match.group(1).strip(), variables)
            lower = self.evaluate(match.group(2).strip(), variables)
            upper = self.evaluate(match.group(3).strip(), variables)
            if value is not None and lower is not None and upper is not None:
                return lower <= value <= upper
        return False

    def _split_list_items(self, text: str) -> list[str]:
        items: list[str] = []
        depth = 0
        current = ""
        for char in text:
            if char == "," and depth == 0:
                items.append(current)
                current = ""
            else:
                if char in "([{":
                    depth += 1
                elif char in ")]}":
                    depth -= 1
                current += char
        if current:
            items.append(current)
        return items

    def register_function(self, feel_func: FEELFunction) -> None:
        self._functions[feel_func.name.lower()] = feel_func

    def _call_function(self, name: str, args: list[Any]) -> Any:
        func = self._functions.get(name.lower())
        if func is None:
            raise FEELError(f"Unknown FEEL function: {name}")
        try:
            return func.func(*args)
        except Exception as e:
            raise FEELError(f"FEEL function {name} error: {e}")

    def _register_builtins(self) -> None:
        import math
        self.register_function(FEELFunction("abs", ["n"], lambda n: abs(n)))
        self.register_function(FEELFunction("ceil", ["n"], lambda n: math.ceil(n)))
        self.register_function(FEELFunction("floor", ["n"], lambda n: math.floor(n)))
        self.register_function(FEELFunction("round", ["n"], lambda n: round(n)))
        self.register_function(FEELFunction("modulo", ["a", "b"], lambda a, b: a % b))
        self.register_function(FEELFunction("sqrt", ["n"], lambda n: math.sqrt(n) if n >= 0 else None))
        self.register_function(FEELFunction("max", ["list"], lambda lst: max(lst) if lst else None))
        self.register_function(FEELFunction("min", ["list"], lambda lst: min(lst) if lst else None))
        self.register_function(FEELFunction("mean", ["list"], lambda lst: sum(lst) / len(lst) if lst else None))
        self.register_function(FEELFunction("sum", ["list"], lambda lst: sum(lst) if lst else 0))
        self.register_function(FEELFunction("count", ["list"], lambda lst: len(lst)))
        self.register_function(FEELFunction("contains", ["str", "substr"], lambda s, sub: sub in s if s and sub else False))
        self.register_function(FEELFunction("starts with", ["str", "prefix"], lambda s, p: s.startswith(p) if s and p else False))
        self.register_function(FEELFunction("ends with", ["str", "suffix"], lambda s, sfx: s.endswith(sfx) if s and sfx else False))
        self.register_function(FEELFunction("string length", ["str"], lambda s: len(s) if s else 0))
        self.register_function(FEELFunction("substring", ["str", "start", "length"], lambda s, st, ln: s[st - 1:st - 1 + ln] if s and st and ln else ""))
        self.register_function(FEELFunction("upper case", ["str"], lambda s: s.upper() if s else ""))
        self.register_function(FEELFunction("lower case", ["str"], lambda s: s.lower() if s else ""))
        self.register_function(FEELFunction("list contains", ["list", "item"], lambda lst, item: item in lst if lst else False))

    def validate(self, expression: str) -> list[str]:
        errors: list[str] = []
        try:
            self._validate_syntax(expression)
        except Exception as e:
            errors.append(str(e))
        return errors

    def _validate_syntax(self, expression: str) -> None:
        opens = expression.count("(")
        closes = expression.count(")")
        if opens != closes:
            raise FEELError(f"Mismatched parentheses: {opens} open, {close} close")
