# rag/research/memory/reasoning/reasoning_node.py
from __future__ import annotations

import time

from .reasoning_event import ReasoningEvent


class ReasoningNode:
    """
    Node in hierarchical reasoning tree.
    """

    def __init__(self, name: str, parent: ReasoningNode | None = None):

        self.name = name
        self.parent = parent

        self.children: list[ReasoningNode] = []
        self.events: list[ReasoningEvent] = []

        self.start_time = time.time()
        self.end_time: float | None = None

        self.failed = False

    def add_event(self, event: ReasoningEvent):
        self.events.append(event)

    def add_child(self, child: ReasoningNode):
        self.children.append(child)

    def finish(self):
        self.end_time = time.time()

    def mark_failed(self):
        self.failed = True
        self.end_time = time.time()

    def to_dict(self):

        return {
            "name": self.name,
            "failed": self.failed,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "events": [e.to_dict() for e in self.events],
            "children": [c.to_dict() for c in self.children]
        }
