# rag/research/memory/reasoning/reasoning_tree.py

from __future__ import annotations

from typing import Optional

from .reasoning_node import ReasoningNode


class ReasoningTree:
    """
    Maintains hierarchical reasoning structure.
    """

    def __init__(self):

        self.root = ReasoningNode("root")
        self.current = self.root

    def start_group(self, name: str) -> ReasoningNode:

        node = ReasoningNode(name, parent=self.current)

        self.current.add_child(node)

        self.current = node

        return node

    def end_group(self):

        if self.current.parent is None:
            return

        self.current.finish()

        self.current = self.current.parent

    def rollback_group(self):

        """
        Marks current segment as failed and rolls back.
        """

        if self.current.parent is None:
            return

        self.current.mark_failed()

        self.current = self.current.parent

    def to_dict(self):

        return self.root.to_dict()

