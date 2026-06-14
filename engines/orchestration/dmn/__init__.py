"""DMN decision runtime components."""

import importlib

_LAZY_MODULES: dict[str, str] = {
    "Binding": ".invocation_handler",
    "DMNEngine": ".engine",
    "DMNExecutionError": ".engine",
    "DecisionExecutor": ".decision_executor",
    "DecisionNode": ".decision_executor",
    "DecisionResult": ".decision_executor",
    "DecisionRule": ".decision_table_evaluator",
    "DecisionTable": ".decision_table_evaluator",
    "DecisionTableEvaluator": ".decision_table_evaluator",
    "FEELEngine": ".feel_engine",
    "FEELError": ".feel_engine",
    "FEELFunction": ".feel_engine",
    "HitPolicy": ".hit_policy_handler",
    "HitPolicyHandler": ".hit_policy_handler",
    "InputClause": ".decision_table_evaluator",
    "Invocation": ".invocation_handler",
    "InvocationHandler": ".invocation_handler",
    "InvocationResult": ".invocation_handler",
    "LiteralExpression": ".literal_expression_eval",
    "LiteralExpressionEvaluator": ".literal_expression_eval",
    "OutputClause": ".decision_table_evaluator",
    "apply_hit_policy": ".hit_policy_handler",
}


def __getattr__(name: str):
    if name in _LAZY_MODULES:
        mod = importlib.import_module(_LAZY_MODULES[name], __package__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(_LAZY_MODULES.keys())
