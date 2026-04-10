from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from rag.rag_models import DocumentChunk


@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    score: float
    source: str = "vector"
    meta: Dict[str, Any] = field(default_factory=dict)
