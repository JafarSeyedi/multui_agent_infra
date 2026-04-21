from __future__ import annotations


class ReasoningEvaluator:
    def __init__(self, llm=None):
        self.llm = llm

    def evaluate(self, reasoning_steps):
        steps = [step for step in reasoning_steps if step]
        if not steps:
            return 0.0
        connected = sum(1 for step in steps if ':' in step or '-' in step)
        return min(1.0, 0.4 + (0.6 * connected / len(steps)))
