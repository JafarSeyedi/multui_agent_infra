from __future__ import annotations


class HallucinationDetector:
    def __init__(self, llm=None):
        self.llm = llm

    def detect(self, answer, evidences):
        if not answer:
            return 1.0
        evidence_text = " ".join(getattr(evidence, "text", "") for evidence in evidences).casefold()
        answer_terms = [term.casefold() for term in answer.split() if len(term) > 5]
        if not answer_terms:
            return 0.0
        unsupported = sum(1 for term in answer_terms if term not in evidence_text)
        return min(1.0, unsupported / len(answer_terms))
