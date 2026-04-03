from __future__ import annotations

from typing import Any, List


class EvidenceCoverageScorer:
    def __init__(self, llm: Any = None):
        self.llm = llm

    async def score(self, query: str, evidence: List[Any]) -> float:
        texts = [self._to_text(item) for item in evidence[:30] if self._to_text(item)]
        if not texts:
            return 0.0

        if self.llm is not None:
            prompt = (
                "Rate the evidence coverage for the research question as a float between 0 and 1. "
                "Return only the number.\n"
                f"Question: {query}\nEvidence:\n" + "\n\n".join(texts)
            )
            response = await self._complete(prompt)
            try:
                return max(0.0, min(1.0, float(str(response).strip())))
            except Exception:
                pass

        query_terms = {term.casefold() for term in query.split() if len(term) > 3}
        evidence_blob = " ".join(texts).casefold()
        covered = sum(1 for term in query_terms if term in evidence_blob)
        lexical = covered / max(1, len(query_terms))
        volume = min(1.0, sum(len(text) for text in texts) / 4000)
        return round((0.65 * lexical) + (0.35 * volume), 4)

    async def _complete(self, prompt: str) -> str:
        if hasattr(self.llm, "complete"):
            return str(await self.llm.complete(prompt))
        if hasattr(self.llm, "generate"):
            return str(await self.llm.generate(prompt))
        if hasattr(self.llm, "ainvoke"):
            return str(await self.llm.ainvoke(prompt))
        raise TypeError("Unsupported LLM interface")

    def _to_text(self, item: Any) -> str:
        chunk = getattr(item, "chunk", item)
        return str(getattr(chunk, "text", "")).strip()
