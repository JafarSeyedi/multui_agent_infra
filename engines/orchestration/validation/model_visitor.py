"""Visitor pattern for model validation and export.

Provides a ModelVisitor interface and a Visitable protocol
that model classes can implement to accept visitors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from ..bpmn.models.bpmn_models import (
    Activity,
    Event,
    Gateway,
    Process,
    SequenceFlow,
    SubProcess,
)


_VISIT_DISPATCH: dict[type, str] = {
    Process: "visit_process",
    SubProcess: "visit_subprocess",
    Activity: "visit_activity",
    Gateway: "visit_gateway",
    Event: "visit_event",
    SequenceFlow: "visit_sequence_flow",
}


class Visitable(Protocol):
    """Protocol for visitable model objects."""
    def accept(self, visitor: ModelVisitor) -> Any: ...


class ModelVisitor(ABC):
    """Abstract visitor for process models.

    Implementations can traverse model trees to perform
    validation, export, metrics calculation, or simulation.
    """

    @abstractmethod
    def visit_process(self, process: Any) -> Any: ...
    @abstractmethod
    def visit_activity(self, activity: Any) -> Any: ...
    @abstractmethod
    def visit_gateway(self, gateway: Any) -> Any: ...
    @abstractmethod
    def visit_event(self, event: Any) -> Any: ...
    @abstractmethod
    def visit_sequence_flow(self, flow: Any) -> Any: ...
    @abstractmethod
    def visit_subprocess(self, subprocess: Any) -> Any: ...

    def visit(self, node: Any) -> Any:
        """Dispatch to the appropriate visit_* method based on node type."""
        handler = _VISIT_DISPATCH.get(type(node))
        if handler:
            return getattr(self, handler)(node)
        return None
