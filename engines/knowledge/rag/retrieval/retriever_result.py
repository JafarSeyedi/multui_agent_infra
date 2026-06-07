from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from engines.rag.rag_models import DocumentChunk


@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    score: float
    source: str = "vector"
    meta: dict[str, Any] = field(default_factory=dict)
