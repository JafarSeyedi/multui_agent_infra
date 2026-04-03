# rag/research/citation_manager.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(slots=True)
class Citation:
    id: int
    source: str
    snippet: str


class CitationManager:
    """
    Manages citations for generated research reports.

    Features
    --------
    - Deduplicates sources
    - Generates numeric citation tags
    - Builds final reference list
    """

    def __init__(self) -> None:
        self._refs: List[Citation] = []
        self._source_to_id: Dict[str, int] = {}
        self._next_id: int = 1

    def reset(self) -> None:
        """Reset citations between queries."""
        self._refs.clear()
        self._source_to_id.clear()
        self._next_id = 1

    def register_source(self, evidence_chunk) -> str:
        """
        Register an evidence chunk and return citation tag.

        Expected attributes on evidence_chunk:
        - text
        - source
        """

        source: str = getattr(evidence_chunk, "source", "unknown")
        text: str = getattr(evidence_chunk, "text", "")

        if source in self._source_to_id:
            cid = self._source_to_id[source]
            return f"[{cid}]"

        snippet = text[:180].replace("\n", " ").strip()

        cid = self._next_id
        self._next_id += 1

        citation = Citation(
            id=cid,
            source=source,
            snippet=snippet
        )

        self._refs.append(citation)
        self._source_to_id[source] = cid

        return f"[{cid}]"

    def build_reference_list(self) -> List[str]:
        """
        Build final formatted reference list.
        """

        refs: List[str] = []

        for c in self._refs:
            refs.append(
                f"[{c.id}] {c.source} — {c.snippet}..."
            )

        return refs
