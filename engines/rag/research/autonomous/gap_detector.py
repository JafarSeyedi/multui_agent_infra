from __future__ import annotations

import re
from typing import Any


class GapDetector:
    def __init__(self, llm: Any = None):
        self.llm = llm

    async def detect_gaps(self, query: str, evidence: list[Any]) -> list[str]:
        snippets = [self._to_text(item) for item in evidence[:20] if self._to_text(item)]
        if not snippets:
            return [f"Need baseline evidence for: {query}"]

        if self.llm is not None:
            prompt = (
                "Identify the missing information needed to fully answer the research question. "
                "Return one gap per line.\n"
                f"Question: {query}\nEvidence:\n" + "\n\n".join(snippets)
            )
            response = await self._complete(prompt)
            gaps = [line.strip("- ").strip() for line in str(response).splitlines() if line.strip()]
            if gaps:
                return gaps[:5]

        return self._heuristic_gaps(query, snippets)

    def _heuristic_gaps(self, query: str, snippets: list[str]) -> list[str]:
        text_blob = " ".join(snippets).casefold()
        gaps: list[str] = []
        for token in [token.casefold() for token in re.findall(r"\w+", query) if len(token) > 4]:
            if token not in text_blob:
                gaps.append(f"Need evidence covering '{token}'")
        return gaps[:5]

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
