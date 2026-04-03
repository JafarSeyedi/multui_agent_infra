from __future__ import annotations

from typing import Any, Iterable, List, Optional


class ResearchSummarizer:
    def __init__(self, llm: Optional[Any], guard=None):
        self.llm = llm
        self.guard = guard

    def build_prompt(self, query, evidence_chunks):
        evidence_text = "\n\n".join([f"[{i+1}] {getattr(chunk, 'text', '')}" for i, chunk in enumerate(evidence_chunks)])
        if self.guard and getattr(self.guard, 'strict_mode', False):
            system_prompt = (
                "You are a scientific research assistant.\n"
                "STRICT MODE ENABLED.\n"
                "Use only the provided evidence and cite factual claims."
            )
        else:
            system_prompt = (
                "You are a scientific research assistant.\n"
                "Write a structured answer using the provided evidence."
            )
        return f"{system_prompt}\n\nUser Question:\n{query}\n\nEvidence:\n{evidence_text}\n\nAnswer:\n"

    def enforce_citations(self, answer):
        if not self.guard or not getattr(self.guard, 'strict_mode', False):
            return answer
        sentences = [sentence.strip() for sentence in answer.split('.') if sentence.strip()]
        valid = [sentence for sentence in sentences if '[' in sentence and ']' in sentence]
        return '. '.join(valid) if valid else 'Insufficient evidence.'

    async def summarize(self, query, evidence_chunks):
        evidence_chunks = list(evidence_chunks)
        if self.llm is None:
            return self._fallback_summary(query, evidence_chunks)

        prompt = self.build_prompt(query, evidence_chunks)
        if hasattr(self.llm, 'generate'):
            answer = await self.llm.generate(prompt)
        elif hasattr(self.llm, 'complete'):
            answer = await self.llm.complete(prompt)
        elif hasattr(self.llm, 'ainvoke'):
            answer = await self.llm.ainvoke(prompt)
        else:
            raise TypeError('Unsupported LLM interface')
        return self.enforce_citations(str(answer))

    def _fallback_summary(self, query: str, evidence_chunks: Iterable[Any]) -> str:
        bullets: List[str] = []
        for idx, chunk in enumerate(evidence_chunks, start=1):
            text = str(getattr(chunk, 'text', '')).strip()
            if text:
                bullets.append(f"- {text} [{idx}]")
        if not bullets:
            return f"Question: {query}\n\nInsufficient evidence."
        return f"Question: {query}\n\nKey findings:\n" + "\n".join(bullets)
