"""CMMN execution components."""

import importlib

_LAZY_MODULES: dict[str, str] = {
    "CaseExecutionError": ".case_executor",
    "CaseExecutor": ".case_executor",
    "CaseFileDefinition": ".case_file_manager",
    "CaseFileItem": ".case_file_manager",
    "CaseFileManager": ".case_file_manager",
    "CasePlanModel": ".case_executor",
    "CaseTaskConfig": ".task_handler",
    "CMMNEngine": ".engine",
    "CMMNExecutionError": ".engine",
    "CMMNTask": ".task_handler",
    "CMMNTaskHandler": ".task_handler",
    "CMMNTaskState": ".task_handler",
    "DecisionTaskConfig": ".task_handler",
    "DiscretionaryItem": ".discretionary_handler",
    "DiscretionaryTaskHandler": ".discretionary_handler",
    "HumanTaskConfig": ".task_handler",
    "Milestone": ".milestone_handler",
    "MilestoneHandler": ".milestone_handler",
    "MilestoneState": ".milestone_handler",
    "PlanningTableHandler": ".planning_table_handler",
    "PlanningTableTable": ".discretionary_handler",
    "ProcessTaskConfig": ".task_handler",
    "SentryEvaluator": ".sentry_evaluator",
    "SentryEvaluationResult": ".sentry_evaluator",
    "SentryRule": ".sentry_evaluator",
    "Stage": ".stage_handler",
    "StageHandler": ".stage_handler",
    "StageState": ".stage_handler",
}


def __getattr__(name: str):
    if name in _LAZY_MODULES:
        mod = importlib.import_module(_LAZY_MODULES[name], __package__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(_LAZY_MODULES.keys())
