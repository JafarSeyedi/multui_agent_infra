from __future__ import annotations


class CompletenessEvaluator:
    def __init__(self, llm=None):
        self.llm = llm

    def evaluate(self, query, answer):
        query_terms = {term.casefold() for term in query.split() if len(term) > 3}
        if not query_terms:
            return 1.0
        answer_text = answer.casefold()
        covered = sum(1 for term in query_terms if term in answer_text)
        return covered / len(query_terms)
