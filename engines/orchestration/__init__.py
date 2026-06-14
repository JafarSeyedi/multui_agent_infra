"""Unified orchestration runtime supporting BPMN, CMMN, DMN, State Machine, CEP, and multi-agent."""

import importlib

_LAZY_MODULES: dict[str, str] = {
    "ActivityInstance": ".core",
    "CompensationAction": ".core",
    "ContextManager": ".core",
    "ContextScope": ".core",
    "CorrelationEngine": ".core",
    "CorrelationKey": ".core",
    "CorrelationKeySet": ".core",
    "Deployment": ".core",
    "DeploymentMode": ".core",
    "EngineConfig": ".core",
    "EngineState": ".core",
    "Event": ".core",
    "EventBus": ".core",
    "EventPriority": ".core",
    "EventSubscription": ".core",
    "EventType": ".core",
    "ExecutionContext": ".core",
    "IncidentInfo": ".core",
    "InstanceManager": ".core",
    "InstanceState": ".core",
    "InstanceType": ".core",
    "IsolationLevel": ".core",
    "Message": ".core",
    "MessageSubscription": ".core",
    "OrchestrationEngine": ".core",
    "ProcessDefinition": ".core",
    "ProcessInstance": ".core",
    "ScheduleType": ".core",
    "ScheduledTask": ".core",
    "Scheduler": ".core",
    "Subscription": ".core",
    "TaskState": ".core",
    "Token": ".core",
    "TokenManager": ".core",
    "TokenSnapshot": ".core",
    "TokenState": ".core",
    "TokenType": ".core",
    "TransactionManager": ".core",
    "TransactionParticipant": ".core",
    "TransactionScope": ".core",
    "TransactionState": ".core",
    "Variable": ".core",
    "VariableScope": ".core",
}


def __getattr__(name: str):
    if name in _LAZY_MODULES:
        mod = importlib.import_module(_LAZY_MODULES[name], __package__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(_LAZY_MODULES.keys())
