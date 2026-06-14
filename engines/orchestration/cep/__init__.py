"""CEP runtime components."""

import importlib

_LAZY_MODULES: dict[str, str] = {
    "AggregationDefinition": ".aggregator",
    "AggregationFunction": ".aggregator",
    "Aggregator": ".aggregator",
    "CEPExecutionError": ".engine",
    "CEPEngine": ".engine",
    "CEPEventStore": ".event_store",
    "CEPRule": ".rule_evaluator",
    "CEPRuleCondition": ".rule_evaluator",
    "PatternDefinition": ".pattern_matcher",
    "PatternMatcher": ".pattern_matcher",
    "PatternOperator": ".pattern_matcher",
    "RuleEvaluator": ".rule_evaluator",
    "StoredEvent": ".event_store",
    "StreamProcessingResult": ".stream_processor",
    "StreamProcessor": ".stream_processor",
    "TemporalRelation": ".pattern_matcher",
    "WatermarkPolicy": ".stream_processor",
    "WindowDefinition": ".window_manager",
    "WindowManager": ".window_manager",
    "WindowState": ".window_manager",
    "WindowType": ".window_manager",
}


def __getattr__(name: str):
    if name in _LAZY_MODULES:
        mod = importlib.import_module(_LAZY_MODULES[name], __package__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(_LAZY_MODULES.keys())
