from __future__ import annotations

import logging
from abc import ABC
from abc import abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class DocumentImplementor(ABC):
    """Bridge implementor — abstracts document model ↔ parser/writer interaction."""

    @abstractmethod
    async def parse(self, source: Any, **kwargs: Any) -> Any:
        ...

    @abstractmethod
    async def write(self, model: Any, **kwargs: Any) -> Any:
        ...

    @property
    @abstractmethod
    def format(self) -> str:
        ...


class DocumentBridge:
    """Bridge abstraction — delegates to a DocumentImplementor.

    Separates high-level document operations from concrete
    parser/writer implementations.
    """

    def __init__(self, implementor: DocumentImplementor) -> None:
        self._impl = implementor

    @property
    def format(self) -> str:
        return self._impl.format

    async def parse(self, source: Any, **kwargs: Any) -> Any:
        return await self._impl.parse(source, **kwargs)

    async def write(self, model: Any, **kwargs: Any) -> Any:
        return await self._impl.write(model, **kwargs)


class ParsingStrategy(ABC):
    """Strategy pattern — pluggable parsing algorithms."""

    @abstractmethod
    async def parse(self, content: bytes, **kwargs: Any) -> Any:
        ...


class SerializationStrategy(ABC):
    """Strategy pattern — pluggable serialization formats."""

    @abstractmethod
    async def serialize(self, model: Any, **kwargs: Any) -> bytes:
        ...

    @abstractmethod
    async def deserialize(self, data: bytes, **kwargs: Any) -> Any:
        ...


class LazyDocumentProxy:
    """Proxy pattern — defers document loading until first access.

    Useful for large documents where parsing is expensive and
    may not be needed.
    """

    def __init__(self, loader: Any, source: str) -> None:
        self._loader = loader
        self._source = source
        self._document: Any | None = None
        self._loaded = False

    async def load(self) -> Any:
        if not self._loaded:
            self._document = await self._loader(self._source)
            self._loaded = True
        return self._document

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    async def pages(self) -> list[Any]:
        doc = await self.load()
        if hasattr(doc, "pages"):
            return doc.pages
        return []

    async def metadata(self) -> dict[str, Any]:
        doc = await self.load()
        if hasattr(doc, "metadata"):
            return doc.metadata
        return {}

    async def text(self) -> str:
        doc = await self.load()
        if hasattr(doc, "text"):
            return doc.text
        return ""
