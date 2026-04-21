from __future__ import annotations

import re


class CitationEvaluator:
    def __init__(self, llm=None):
        self.llm = llm

    def evaluate(self, answer, evidences):
        if not answer:
            return 0.0
        citation_count = len(re.findall(r"\[\d+\]", answer))
        evidence_count = len(list(evidences)) if evidences is not None else 0
        if evidence_count == 0:
            return 0.0
        return min(1.0, citation_count / evidence_count)
