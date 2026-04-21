from __future__ import annotations

from typing import Any, List


class QueryRewriter:
    def __init__(self, llm: Any, num_queries: int = 4):
        self.llm = llm
        self.num_queries = num_queries

    async def rewrite(self, query: str, num_queries: int | None = None) -> List[str]:
        target = num_queries or self.num_queries
        prompt = (
            f"Generate {target} diverse retrieval queries for the user question below. "
            "Return one query per line without numbering.\n"
            f"Question: {query}"
        )

        response = await self.llm.generate(prompt)
        queries = [line.strip("- ").strip() for line in str(response).splitlines() if line.strip()]
        unique_queries = []
        seen = set()
        for item in [query, *queries]:
            key = item.casefold()
            if key not in seen:
                unique_queries.append(item)
                seen.add(key)
        return unique_queries[:target]
