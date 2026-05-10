# engines/document/writers/ssdm_writers/base_ssdm_writer.py
"""
Base class for all SSDM (Service Standard Definition Model) writers.
"""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncIterator
from enum import Enum
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.ssdm_models import SSDMDocument 
from ..base import BaseDocumentWriter
from ..base import WriteOptions


class VersionStrategy(str, Enum):
    """How to handle versioning when writing a file."""
    OVERWRITE       = "overwrite"        # replace existing file (ignore version)
    NEW_VERSION     = "new_version"      # create a new file with version appended
    AUTO_INCREMENT  = "auto_increment"   # find highest existing version and increment


class VersionIncrement(str, Enum):
    """Which part of a semantic version to increment."""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class SSDMWriteOptions(WriteOptions):
    """Extensions to WriteOptions for SSDM writers."""
    version_strategy: VersionStrategy = VersionStrategy.NEW_VERSION
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
        # Default increment level for AUTO_INCREMENT strategy
        self.increment_level: VersionIncrement = VersionIncrement.PATCH

    # ── Write interface ──────────────────────────────────────────
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        data = await self.write(document)
        yield data

    async def write(self, document: BaseDocument) -> bytes:
        if not isinstance(document, SSDMDocument ):
            raise TypeError("BaseSSDMWriter expects an SSDMDocument ")
        return await self._write_design(document)

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None,
    ) -> None:
        data = await self.write(document)
        if not isinstance(document, SSDMDocument ):
            raise TypeError("Expected SSDMDocument ")

        # Handle AUTO_INCREMENT before computing versioned path
        if self.sdm_options.version_strategy == VersionStrategy.AUTO_INCREMENT:
            next_ver = self._auto_increment_version(target, self.increment_level)
            document.version = next_ver

        final_path = self._versioned_path(target, document)
        final_path.write_bytes(data)

    @abstractmethod
    async def _write_design(self, document: SSDMDocument ) -> bytes:
        """Return the serialised service definition as bytes."""
        ...

    @abstractmethod
    def get_supported_media_types(self) -> list[str]:
        ...

    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        ...

    # ── Versioning helpers (identical to OSDM base) ──────────────
    def _versioned_path(self, original: Path, document: SSDMDocument ) -> Path:
        if self.sdm_options.version_strategy == VersionStrategy.OVERWRITE:
            return original
        ver = document.version or "1.0.0"
        stem = original.stem
        if not stem.endswith(f"_v{ver}"):
            stem = f"{stem}_v{ver}"
        return original.with_name(f"{stem}{original.suffix}")

    def _auto_increment_version(self, target: Path, level: VersionIncrement = VersionIncrement.PATCH) -> str:
        """Scan existing files and increment the specified version segment."""
        import re
        base_stem = target.stem
        ext = target.suffix
        parent = target.parent
        pattern = re.compile(
            re.escape(base_stem) +
            r"_v(\d+)\.(\d+)\.(\d+)" +
            re.escape(ext)
        )
        max_major, max_minor, max_patch = 0, 0, -1
        for path in parent.glob(f"{base_stem}*{ext}"):
            m = pattern.match(path.name)
            if m:
                major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
                if (major, minor, patch) > (max_major, max_minor, max_patch):
                    max_major, max_minor, max_patch = major, minor, patch
        if max_patch == -1:
            return "1.0.0"
        return self._increment_version(f"{max_major}.{max_minor}.{max_patch}", level)

    @staticmethod
    def _increment_version(version_str: str, level: VersionIncrement) -> str:
        try:
            parts = list(map(int, version_str.split('.')))
            if len(parts) != 3:
                raise ValueError
        except ValueError:
            raise ValueError(f"Invalid semantic version: {version_str}")

        if level == VersionIncrement.MAJOR:
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif level == VersionIncrement.MINOR:
            parts[1] += 1
            parts[2] = 0
        else:   # PATCH
            parts[2] += 1
        return f"{parts[0]}.{parts[1]}.{parts[2]}"
