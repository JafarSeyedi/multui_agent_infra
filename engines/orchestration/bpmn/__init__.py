"""BPMN execution components."""

import importlib

_LAZY_MODULES: dict[str, str] = {
    "ActivityExecutionResult": ".activity_handler",
    "ActivityHandler": ".activity_handler",
    "ActivityIOSpecification": ".activity_handler",
    "ActivityLoopCharacteristics": ".activity_handler",
    "BoundaryBehavior": ".activity_handler",
    "AdhocHandler": ".adhoc_handler",
    "HandlerAdHocActivity": ".adhoc_handler",
    "HandlerAdHocExecutionState": ".adhoc_handler",
    "HandlerAdHocOutcome": ".adhoc_handler",
    "HandlerAdHocProcess": ".adhoc_handler",
    "HandlerAdHocOrdering": ".models.bpmn_models",
    "ChoreographyHandler": ".choreography_handler",
    "HandlerChoreographyOutcome": ".choreography_handler",
    "HandlerChoreographyState": ".choreography_handler",
    "HandlerChoreographyStep": ".choreography_handler",
    "CollaborationHandler": ".collaboration_handler",
    "HandlerCollaborationContext": ".collaboration_handler",
    "MessageRoutingResult": ".collaboration_handler",
    "DataObjectHandler": ".data_object_handler",
    "HandlerDataAssociation": ".data_object_handler",
    "HandlerDataObject": ".data_object_handler",
    "HandlerDataStoreRef": ".data_object_handler",
    "HandlerMessageObject": ".data_object_handler",
    "BPMNExecutionError": ".engine",
    "BPMNEngine": ".engine",
    "EventHandler": ".event_handler",
    "HandlerBPMNEvent": ".event_handler",
    "HandlerBPMNEventOutcome": ".event_handler",
    "TimerSchedule": ".event_handler",
    "GatewayBranch": ".gateway_handler",
    "GatewayContext": ".gateway_handler",
    "GatewayDecision": ".gateway_handler",
    "GatewayHandler": ".gateway_handler",
    "GlobalTaskExecutionResult": ".global_task_handler",
    "GlobalTaskHandler": ".global_task_handler",
    "HandlerGlobalTask": ".global_task_handler",
    "HandlerLoopConfiguration": ".loop_handler",
    "HandlerLoopIteration": ".loop_handler",
    "HandlerLoopOutcome": ".loop_handler",
    "HandlerLoopState": ".loop_handler",
    "LoopHandler": ".loop_handler",
    "TypedProcessModel": ".process_model",
    "classify_node": ".process_model",
    "BPMNProcessExecutor": ".process_executor",
    "ProcessExecutionOutcome": ".process_executor",
    "ProcessModel": ".process_executor",
    "FlowTraversalResult": ".sequence_flow",
    "HandlerSequenceFlow": ".sequence_flow",
    "SequenceFlowEngine": ".sequence_flow",
    "compute_next_nodes": ".sequence_flow",
    "find_default_flow": ".sequence_flow",
    "has_conditional_flows": ".sequence_flow",
    "HandlerTransactionBoundary": ".transaction_handler",
    "HandlerTransactionContext": ".transaction_handler",
    "TransactionHandler": ".transaction_handler",
    "TransactionState": ".transaction_handler",
}


def __getattr__(name: str):
    if name in _LAZY_MODULES:
        mod = importlib.import_module(_LAZY_MODULES[name], __package__)
        val = getattr(mod, name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")




__all__ = sorted(_LAZY_MODULES.keys())
