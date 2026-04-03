from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, List


@dataclass
class Entity:
    name: str
    type: str
    confidence: float
    source_chunk: str


class EntityExtractor:
    def __init__(self, llm: Any = None):
        self.llm = llm

    async def extract(self, chunks: Iterable[Any]) -> List[Entity]:
        entities: List[Entity] = []
        for chunk in chunks:
            text = getattr(chunk, "text", "")
            chunk_id = getattr(chunk, "chunk_id", "unknown")
            entities.extend(await self._llm_extract(text, chunk_id))
            entities.extend(self._heuristic_extract(text, chunk_id))
        return self._deduplicate(entities)

    async def _llm_extract(self, text: str, chunk_id: str) -> List[Entity]:
        if self.llm is None or not text.strip():
            return []
        prompt = (
            "Extract key research entities from the text. Return JSON list of objects with name and type.\n"
            f"Text: {text}"
        )
        response = await self._complete(prompt)
        try:
            parsed = json.loads(response)
        except Exception:
            return []

        output: List[Entity] = []
        for item in parsed if isinstance(parsed, list) else []:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            output.append(
                Entity(
                    name=str(item["name"]).strip(),
                    type=str(item.get("type", "concept")).strip() or "concept",
                    confidence=0.9,
                    source_chunk=chunk_id,
                )
            )
        return output

    def _heuristic_extract(self, text: str, chunk_id: str) -> List[Entity]:
        pattern = r"\b[A-Z][a-zA-Z0-9\-]{2,}\b"
        return [
            Entity(name=match, type="keyword", confidence=0.5, source_chunk=chunk_id)
            for match in re.findall(pattern, text)
        ]

    def _deduplicate(self, entities: List[Entity]) -> List[Entity]:
        best = {}
        for entity in entities:
            key = (entity.name.casefold(), entity.type.casefold())
            current = best.get(key)
            if current is None or entity.confidence > current.confidence:
                best[key] = entity
        return list(best.values())

    async def _complete(self, prompt: str) -> str:
        if hasattr(self.llm, "complete"):
            return str(await self.llm.complete(prompt))
        if hasattr(self.llm, "generate"):
            return str(await self.llm.generate(prompt))
        if hasattr(self.llm, "ainvoke"):
            return str(await self.llm.ainvoke(prompt))
        raise TypeError("Unsupported LLM interface")
