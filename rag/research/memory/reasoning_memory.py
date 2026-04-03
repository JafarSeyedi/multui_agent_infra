# rag/research/memory/reasoning_memory.py

from __future__ import annotations

import time
from typing import List, Dict, Optional


class ReasoningStep:
    """
    Represents a single reasoning event in the research pipeline.
    """
    __slots__ = ("step", "details", "timestamp", "meta")

    def __init__(self, step: str, details: str, meta: Optional[dict] = None):
        self.step = step
        self.details = details
        self.meta = meta or {}
        self.timestamp = time.time()

    def to_dict(self):
        return {
            "step": self.step,
            "details": self.details,
            "meta": self.meta,
            "timestamp": self.timestamp
        }


class ReasoningMemory:
    """
    Stores the reasoning trace of the entire research process.

    Goals:
    - Debugging autonomous reasoning loops
    - Explainability and traceability
    - Feeding information into future memory modules
    """

    def __init__(self):
        self._steps: List[ReasoningStep] = []
        self._groups: List[dict] = []     # for nested sections
        self._current_group: Optional[str] = None

    # -------------------------------------------------------------------------
    # LOGGING
    # -------------------------------------------------------------------------

    def log(
        self,
        step: str,
        details: str,
        *,
        meta: Optional[dict] = None
    ):
        """
        Log a single reasoning event.
        """
        rs = ReasoningStep(step=step, details=details, meta=meta)
        self._steps.append(rs)

        # Automatically append to group if active
        if self._current_group is not None:
            self._groups[-1]["steps"].append(rs.to_dict())

        return rs

    # -------------------------------------------------------------------------
    # GROUPING (nested reasoning sections)
    # -------------------------------------------------------------------------

    def start_group(self, name: str):
        """
        Starts a named logical block such as:
        - RetrievalPhase
        - GraphReasoning
        - EvidenceFusion
        """
        group = {
            "name": name,
            "steps": [],
            "start_time": time.time(),
            "end_time": None
        }
        self._groups.append(group)
        self._current_group = name

        self.log("StartGroup", f"Entering reasoning group '{name}'")
        return group

    def end_group(self, name: Optional[str] = None):
        """
        Ends current reasoning block.
        """
        if not self._groups:
            return

        if name is None:
            name = self._current_group

        for g in reversed(self._groups):
            if g["name"] == name and g["end_time"] is None:
                g["end_time"] = time.time()
                self._current_group = None
                self.log("EndGroup", f"Exiting reasoning group '{name}'")
                return g

    # -------------------------------------------------------------------------
    # RETRIEVE TRACE
    # -------------------------------------------------------------------------

    def dump(self) -> Dict[str, object]:
        """
        Returns full trace including:
        - flat list of steps
        - grouped reasoning blocks
        """
        return {
            "flat": [s.to_dict() for s in self._steps],
            "groups": self._groups
        }

    def summary(self) -> List[str]:
        """
        Human-readable condensed version (for UI/debug).
        """
        output = []
        for s in self._steps:
            ts = time.strftime("%H:%M:%S", time.localtime(s.timestamp))
            output.append(f"[{ts}] {s.step}: {s.details}")

        return output

    # -------------------------------------------------------------------------
    # MEMORY COMPRESSION (optional, but useful)
    # -------------------------------------------------------------------------

    def compress(self, keep_groups: bool = True):
        """
        Reduce reasoning memory footprint for long research sessions.

        Strategy:
        - Keep only group summaries
        - Or keep only last N steps
        """
        if keep_groups:
            self._steps = self._steps[-30:]  # keep last 30 steps
        else:
            self._steps = []
        return True

