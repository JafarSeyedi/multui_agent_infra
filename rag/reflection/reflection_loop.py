from typing import List
from rag.rag_models import RetrievedDocument


class ReflectionLoop:

    def __init__(
        self,
        llm,
        critic,
        max_rounds: int = 2,
    ):
        self.llm = llm
        self.critic = critic
        self.max_rounds = max_rounds

    async def improve_query(self, query: str, context: str) -> str:

        prompt = f"""
You are a query rewriting model.

Original Query:
{query}

Retrieved Context:
{context}

The context seems insufficient. Rewrite the query to obtain missing information.
Produce a single improved query.
"""

        improved = await self.llm.generate(prompt)
        return improved.strip()

    async def run(
        self,
        original_query: str,
        retrieved_docs: List[RetrievedDocument],
        retriever_callable,
    ):
        """
        retriever_callable(query) → returns List[RetrievedDocument]
        """

        merged_docs = list(retrieved_docs)

        for _ in range(self.max_rounds):

            context_text = "\n".join([d.chunk.text for d in merged_docs])

            # 1. Evaluate
            insufficient = await self.critic.evaluate(
                original_query, context_text
            )
            if not insufficient:
                break

            # 2. Improve Query
            improved_q = await self.improve_query(original_query, context_text)

            # 3. Retrieve again
            new_docs = await retriever_callable(improved_q)

            # 4. Merge while removing duplicates
            seen = set()
            result = []
            for d in merged_docs + new_docs:
                if d.chunk.id not in seen:
                    seen.add(d.chunk.id)
                    result.append(d)
            merged_docs = result

        return merged_docs
