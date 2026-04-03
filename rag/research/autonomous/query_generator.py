from __future__ import annotations

from typing import Any, Iterable, List


class FollowUpQueryGenerator:
    def __init__(self, llm: Any = None):
        self.llm = llm

    async def generate(self, gaps: Iterable[str]) -> List[str]:
        gap_list = [str(gap).strip() for gap in gaps if str(gap).strip()]
        if not gap_list:
            return []

        if self.llm is not None:
            prompt = (
                "Generate concise search queries to resolve the following research gaps. "
                "Return one query per line.\n" + "\n".join(f"- {gap}" for gap in gap_list)
            )
            response = await self._complete(prompt)
            queries = [line.strip("- ").strip() for line in str(response).splitlines() if line.strip()]
            if queries:
                return queries[: min(6, len(gap_list) * 2)]

        return [self._heuristic_query(gap) for gap in gap_list[:5]]

    async def _complete(self, prompt: str) -> str:
        if hasattr(self.llm, "complete"):
            return str(await self.llm.complete(prompt))
        if hasattr(self.llm, "generate"):
            return str(await self.llm.generate(prompt))
        if hasattr(self.llm, "ainvoke"):
            return str(await self.llm.ainvoke(prompt))
        raise TypeError("Unsupported LLM interface")

    def _heuristic_query(self, gap: str) -> str:
        return gap.removeprefix("Need evidence covering ").strip("' ")
