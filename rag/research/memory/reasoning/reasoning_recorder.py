# rag/research/memory/reasoning/reasoning_recorder.py

from __future__ import annotations

from typing import Optional, Dict

from .reasoning_event import ReasoningEvent
from .event_types import ReasoningEventType
from .reasoning_tree import ReasoningTree


class ReasoningRecorder:
    """
    Main tracing engine.
    """

    def __init__(self):

        self.tree = ReasoningTree()

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
        meta: Optional[Dict] = None,
        tokens: Optional[int] = None
    ):

        e = ReasoningEvent(
            event_type=event_type,
            message=message,
            meta=meta,
            token_count=tokens
        )

        self.tree.current.add_event(e)

        return e

    def export(self):

        return self.tree.to_dict()

