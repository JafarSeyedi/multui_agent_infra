from __future__ import annotations

import hashlib
import math
from typing import Iterable, List, Optional, Sequence


class EmbeddingModel:
    """Deterministic embedding model with optional provider delegation.

    If a provider exposing `embed`, `aembed`, `encode`, or `__call__` is supplied,
    this class delegates to it. Otherwise, it falls back to a stable hashed embedding
    so the retrieval pipeline remains functional in local/dev environments.
    """

    def __init__(self, provider: Optional[object] = None, dimension: int = 256):
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self.provider = provider
        self.dimension = dimension

    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if self.provider is None:
            return [self._fallback_embed(text) for text in texts]

        if hasattr(self.provider, "aembed"):
            return await self.provider.aembed(texts)
        if hasattr(self.provider, "embed"):
            result = self.provider.embed(texts)
            if hasattr(result, "__await__"):
                return await result
            return result
        if hasattr(self.provider, "encode"):
            return [self._coerce_vector(self.provider.encode(text)) for text in texts]
        if callable(self.provider):
            return [self._coerce_vector(self.provider(text)) for text in texts]

        raise TypeError("Unsupported embedding provider interface")

    async def embed_one(self, text: str) -> List[float]:
        return (await self.embed([text]))[0]

    def _fallback_embed(self, text: str) -> List[float]:
        buckets = [0.0] * self.dimension
        if not text:
            return buckets

        for token in self._tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            buckets[index] += sign * (1.0 + len(token) / 10.0)

        norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
        return [value / norm for value in buckets]

    def _tokenize(self, text: str) -> Iterable[str]:
        return [token.casefold() for token in text.split() if token.strip()]

    def _coerce_vector(self, vector: Sequence[float]) -> List[float]:
        return [float(value) for value in vector]
