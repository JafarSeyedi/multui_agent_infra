"""State machine orchestration components."""

import importlib

_LAZY_MODULES: dict[str, str] = {
    "ActionExecutionError": ".action_executor",
    "ActionExecutor": ".action_executor",
    "GuardCondition": ".guard_evaluator",
    "GuardEvaluator": ".guard_evaluator",
    "HierarchicalHandler": ".hierarchical_handler",
    "HistoryEntry": ".history_manager",
    "HistoryKind": ".history_manager",
    "ParallelStateHandler": ".parallel_state_handler",
    "PseudoStateKind": ".state_executor",
    "RegionContext": ".state_executor",
    "RegionState": ".parallel_state_handler",
    "StateAction": ".action_executor",
    "StateContext": ".state_executor",
    "StateKind": ".state_executor",
    "StateMachineEngine": ".engine",
    "StateMachineError": ".engine",
    "StateMachineExecutor": ".state_executor",
    "StateMachineHistory": ".history_manager",
    "StateMachineModel": ".state_executor",
    "StateNode": ".hierarchical_handler",
    "Transition": ".transition_handler",
    "TransitionHandler": ".transition_handler",
    "TriggerMatch": ".transition_handler",
}


def __getattr__(name: str):
    if name in _LAZY_MODULES:
        mod = importlib.import_module(_LAZY_MODULES[name], __package__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(_LAZY_MODULES.keys())
