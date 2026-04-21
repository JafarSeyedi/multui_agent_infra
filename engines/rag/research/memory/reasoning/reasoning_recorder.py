# rag/research/memory/reasoning/reasoning_recorder.py

from __future__ import annotations

import time
import uuid
from typing import Optional, Dict, Any

from .reasoning_event import ReasoningEvent
from .event_types import ReasoningEventType
from .reasoning_tree import ReasoningTree


class ReasoningRecorder:
    """
    Main tracing engine.
    """

    def __init__(self) -> None:
        self.tree = ReasoningTree()
        self._session_id: str = str(uuid.uuid4())

    def start(self, name: str):
        return self.tree.start_group(name)

    def end(self):
        self.tree.end_group()

    def rollback(self):
        self.tree.rollback_group()

    def event(
        self,
        event_type: ReasoningEventType,
        message: str,
        *,
        meta: Optional[Dict[str, Any]] = None,
        tokens: Optional[int] = None,
    ) -> ReasoningEvent:

        group = self.tree.current
        e = ReasoningEvent(
            id=str(uuid.uuid4()),
            timestamp=time.time(),
            session_id=self._session_id,
            group=group.name if hasattr(group, "name") else "root",
            step=group.step_count if hasattr(group, "step_count") else 0,
            phase="default",
            event_type=event_type.value,
            level="info",
            message=message,
            meta=meta or {},
            token_count=tokens,
        )

        group.add_event(e)
        return e

    def export(self) -> Dict[str, Any]:
        return self.tree.to_dict()
