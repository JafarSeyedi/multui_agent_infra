# engines/document/writers/ssdm_writers/base_ssdm_writer.py
"""
Base class for all SSDM (Service Standard Definition Model) writers.
"""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.ssdm_models import SSDMDocument
from ..base import BaseDocumentWriter
from ..base import WriteOptions
from ..versioning import VersioningContext
from ..versioning import VersionIncrement
from ..versioning import VersionWriteStrategy


class SSDMWriteOptions(WriteOptions):
    """Extensions to WriteOptions for SSDM writers."""
    version_strategy: VersionWriteStrategy = VersionWriteStrategy.NEW_VERSION
    pretty_print: bool = True
    include_metadata: bool = True


class BaseSSDMWriter(BaseDocumentWriter):
    """
    Common superclass for SSDM file writers.

    Subclasses implement:
    - ``_write_design(document) -> bytes``
    - ``get_supported_media_types`` and ``get_supported_extensions``.
    """

    name: str = "ssdm"
    supported_extensions: tuple[str, ...] = ()

    def __init__(self, options: SSDMWriteOptions | None = None):
        super().__init__(options or SSDMWriteOptions())
        self.sdm_options: SSDMWriteOptions = (
            self.options if isinstance(self.options, SSDMWriteOptions) else SSDMWriteOptions()
        )
        self._versioning = VersioningContext(
            strategy=self.sdm_options.version_strategy,
            increment_level=VersionIncrement.PATCH,
        )

    # ── Write interface ──────────────────────────────────────────
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        data = await self.write(document)
        yield data

    async def write(self, document: BaseDocument) -> bytes:
        if not isinstance(document, SSDMDocument):
            raise TypeError("BaseSSDMWriter expects an SSDMDocument")
        return await self._write_design(document)

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None,
    ) -> None:
        data = await self.write(document)
        if not isinstance(document, SSDMDocument):
            raise TypeError("Expected SSDMDocument")

        if self.sdm_options.version_strategy == VersionWriteStrategy.AUTO_INCREMENT:
            next_ver = self._versioning.auto_increment_version(target)
            document.version = next_ver

        final_path = self._versioning.versioned_path(target, document.version)
        final_path.write_bytes(data)

    @abstractmethod
    async def _write_design(self, document: SSDMDocument) -> bytes:
        """Return the serialised service definition as bytes."""
        ...

    @abstractmethod
    def get_supported_media_types(self) -> list[str]:
        ...

    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        ...
