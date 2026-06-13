from __future__ import annotations

import ast
import operator
from typing import Any
from collections.abc import Callable

_ALLOWED_OPS: dict[type, Callable[..., Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
    ast.In: operator.contains,
    ast.NotIn: (lambda a, b: not operator.contains(b, a)),
    ast.And: operator.and_,
    ast.Or: operator.or_,
    ast.Not: operator.not_,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_expr_eval(expression: str, context: dict[str, Any] | None = None) -> Any:
    """Safely evaluate a Python expression using AST parsing with whitelist.

    Only allows: literals, identifiers, attribute access, subscripting,
    comparisons, boolean/math operators, and context variable lookups.
    """
    tree = ast.parse(expression.strip(), mode="eval")
    return _eval_node(tree.body, context or {})


def _eval_node(node: ast.AST, context: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        if node.id in context:
            return context[node.id]
        raise NameError(f"Name '{node.id}' is not defined")

    if isinstance(node, ast.Attribute):
        value = _eval_node(node.value, context)
        return getattr(value, node.attr)

    if isinstance(node, ast.Subscript):
        value = _eval_node(node.value, context)
        slice_val = _eval_node(node.slice, context)
        return value[slice_val]

    if isinstance(node, ast.List):
        return [_eval_node(el, context) for el in node.elts]

    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(el, context) for el in node.elts)

    if isinstance(node, ast.Dict):
        return {
            _eval_node(k, context): _eval_node(v, context)
            for k, v in zip(node.keys, node.values)
            if k is not None
        }

    if isinstance(node, ast.UnaryOp):
        op_func = _ALLOWED_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_func(_eval_node(node.operand, context))

    if isinstance(node, ast.BinOp):
        op_func = _ALLOWED_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
        return op_func(_eval_node(node.left, context), _eval_node(node.right, context))

    if isinstance(node, ast.BoolOp):
        values = [_eval_node(v, context) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)

    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, context)
        for op, comparator in zip(node.ops, node.comparators):
            op_func = _ALLOWED_OPS.get(type(op))
            if op_func is None:
                raise ValueError(f"Unsupported comparison: {type(op).__name__}")
            right = _eval_node(comparator, context)
            if not op_func(left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.IfExp):
        test = _eval_node(node.test, context)
        if test:
            return _eval_node(node.body, context)
        else:
            return _eval_node(node.orelse, context)

    if isinstance(node, ast.Call):
        func = _eval_node(node.func, context)
        args = [_eval_node(arg, context) for arg in node.args]
        kwargs = {kw.arg: _eval_node(kw.value, context) for kw in node.keywords if kw.arg is not None}
        return func(*args, **kwargs)

    raise ValueError(f"Unsupported expression: {type(node).__name__}")
