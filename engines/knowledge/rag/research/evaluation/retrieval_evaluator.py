from __future__ import annotations

from typing import Any


class RetrievalEvaluator:
    def __init__(self, llm: Any = None):
        self.llm = llm

    def evaluate(self, query, evidences):
        query_terms = {term.casefold() for term in query.split() if len(term) > 3}
        scores = []
        for evidence in evidences:
            text = getattr(evidence, "text", "")
            if not text:
                continue
            if self.llm is not None and callable(self.llm):
                try:
                    response = self.llm(f"Score relevance from 0 to 1.\nQuery: {query}\nEvidence: {text}")
                    scores.append(float(str(response).strip()))
                    continue
                except Exception:
                    pass
            evidence_terms = {term.casefold() for term in text.split()}
            overlap = len(query_terms & evidence_terms) / max(1, len(query_terms))
            scores.append(overlap)
        return sum(scores) / len(scores) if scores else 0.0
