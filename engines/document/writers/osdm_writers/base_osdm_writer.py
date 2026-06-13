# engines/document/writers/osdm_writers/base_osdm_writer.py
"""
Base class for all OSDM format writers.
"""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.osdm_models import BaseOSDMDocument
from ..base import BaseDocumentWriter
from ..base import WriteOptions
from ..versioning import VersioningContext
from ..versioning import VersionIncrement
from ..versioning import VersionWriteStrategy


class OSDMWriteOptions(WriteOptions):
    """Extensions to the base WriteOptions for OSDM writers."""
    version_strategy: VersionWriteStrategy = VersionWriteStrategy.NEW_VERSION
    pretty_print: bool = True
    include_diagrams: bool = True
    include_metadata: bool = True


class BaseOSDMWriter(BaseDocumentWriter):
    """
    Common superclass for OSDM file writers.
    Subclasses implement:

    - ``_write_design(document) -> bytes``
    - ``get_supported_media_types`` and ``get_supported_extensions``.
    """

    name: str = "osdm"
    supported_extensions: tuple[str, ...] = ()

    def __init__(self, options: OSDMWriteOptions | None = None):
        super().__init__(options or OSDMWriteOptions())
        self.osdm_options: OSDMWriteOptions = (
            self.options if isinstance(self.options, OSDMWriteOptions) else OSDMWriteOptions()
        )
        self._versioning = VersioningContext(
            strategy=self.osdm_options.version_strategy,
            increment_level=VersionIncrement.PATCH,
        )

    # ── Write interface ──────────────────────────────────────────
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        data = await self.write(document)
        yield data

    async def write(self, document: BaseDocument) -> bytes:
        if not isinstance(document, BaseOSDMDocument):
            raise TypeError("BaseOSDMWriter expects a BaseOSDMDocument (or subclass)")
        return await self._write_design(document)

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None,
    ) -> None:
        if not isinstance(document, BaseOSDMDocument):
            raise TypeError("Expected BaseOSDMDocument")
        data = await self.write(document)

        if self.osdm_options.version_strategy == VersionWriteStrategy.AUTO_INCREMENT:
            next_ver = self._versioning.auto_increment_version(target)
            document.version = next_ver

        final_path = self._versioning.versioned_path(target, document.version)
        final_path.write_bytes(data)

    @abstractmethod
    async def _write_design(self, document: BaseOSDMDocument) -> bytes:
        """Return the serialised schema as bytes for the specific document type."""
        ...

    @abstractmethod
    def get_supported_media_types(self) -> list[str]:
        ...

    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        ...
