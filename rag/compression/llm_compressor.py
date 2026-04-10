from typing import List
from .base import BaseCompressor
from rag.rag_models import DocumentChunk


class LLMCompressor(BaseCompressor):

    def __init__(self, llm_client):
        self.llm = llm_client

    async def compress(
        self,
        query: str,
        chunks: List[DocumentChunk]
    ) -> List[DocumentChunk]:

        results = []

        for ch in chunks:

            prompt = f"""
You are a retrieval compression system.

User Query:
{query}

Context:
{ch.text}

Extract only the parts of the context relevant to answering the query.
Remove irrelevant information.

Return the compressed context only.
"""

            compressed = await self.llm.generate(prompt)

            ch.text = compressed.strip()

            results.append(ch)

        return results
