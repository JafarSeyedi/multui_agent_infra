from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class CandidateRelation:
    src: str
    dst: str
    relation: str
    confidence: float
    evidence_chunk: str


class RelationBuilder:
    def __init__(self, llm: Any = None):
        self.llm = llm

    async def build_relations(self, chunk, entities) -> list[CandidateRelation]:
        relations: list[CandidateRelation] = []
        relations.extend(await self._llm_relations(chunk.text, entities, chunk.chunk_id))
        relations.extend(self._pattern_relations(chunk.text, entities, chunk.chunk_id))
        relations.extend(self._cooccurrence_relations(entities, chunk.chunk_id))
        return self._deduplicate(relations)

    async def _llm_relations(self, text, entities, chunk_id):
        if not self.llm:
            return []
        prompt = (
            "Extract semantic relations among the entities in the text. "
            "Return JSON list with src, dst, relation.\n"
            f"Entities: {[entity.name for entity in entities]}\nText: {text}"
        )
        response = await self._complete(prompt)
        try:
            parsed = json.loads(response)
        except Exception:
            return []

        output = []
        for item in parsed if isinstance(parsed, list) else []:
            if not isinstance(item, dict):
                continue
            src = str(item.get("src", "")).strip()
            dst = str(item.get("dst", "")).strip()
            relation = str(item.get("relation", "related_to")).strip()
            if src and dst and src != dst:
                output.append(
                    CandidateRelation(
                        src=src,
                        dst=dst,
                        relation=relation,
                        confidence=0.9,
                        evidence_chunk=chunk_id,
                    )
                )
        return output

    def _pattern_relations(self, text, entities, chunk_id):
        names = {entity.name for entity in entities}
        patterns = [
            (r"(\w+) is based on (\w+)", "based_on"),
            (r"(\w+) extends (\w+)", "extends"),
            (r"(\w+) improves (\w+)", "improves"),
            (r"(\w+) uses (\w+)", "uses"),
        ]
        output = []
        for pattern, relation in patterns:
            for src, dst in re.findall(pattern, text):
                if src in names and dst in names and src != dst:
                    output.append(CandidateRelation(src=src, dst=dst, relation=relation, confidence=0.6, evidence_chunk=chunk_id))
        return output

    def _cooccurrence_relations(self, entities, chunk_id):
        names = []
        seen = set()
        for entity in entities:
            if entity.name not in seen:
                names.append(entity.name)
                seen.add(entity.name)

        output = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                output.append(
                    CandidateRelation(
                        src=names[i],
                        dst=names[j],
                        relation="co_occurs",
                        confidence=0.3,
                        evidence_chunk=chunk_id,
                    )
                )
        return output

    def _deduplicate(self, relations: list[CandidateRelation]) -> list[CandidateRelation]:
        best: dict[tuple[str, str, str], CandidateRelation] = {}  # ← real instance
        for relation in relations:
            key = (relation.src.casefold(), relation.dst.casefold(), relation.relation.casefold())
            current = best.get(key)
            if current is None or relation.confidence > current.confidence:
                best[key] = relation
        return list(best.values())

    async def _complete(self, prompt: str) -> str:
        if hasattr(self.llm, "complete"):
            return str(await self.llm.complete(prompt))
        if hasattr(self.llm, "generate"):
            return str(await self.llm.generate(prompt))
        if hasattr(self.llm, "ainvoke"):
            return str(await self.llm.ainvoke(prompt))
        raise TypeError("Unsupported LLM interface")
