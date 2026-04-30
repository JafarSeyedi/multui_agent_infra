# engines/document/writers/osdm_writers/base_osdm_writer.py
"""
Base class for all OSDM format writers.
"""

from __future__ import annotations
from abc import abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, AsyncIterator, List, Tuple
from enum import Enum
import re

from pydantic import BaseModel

from ..base import BaseDocumentWriter, WriteOptions
from ...models.osdm_models import BaseOSDMDocument
from ...models.base import BaseDocument


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


class OSDMWriteOptions(WriteOptions):
    """Extensions to the base WriteOptions for OSDM writers."""
    version_strategy: VersionStrategy = VersionStrategy.NEW_VERSION
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

    def __init__(self, options: Optional[OSDMWriteOptions] = None):
        super().__init__(options or OSDMWriteOptions())
        self.osdm_options: OSDMWriteOptions = (
            self.options if isinstance(self.options, OSDMWriteOptions) else OSDMWriteOptions()
        )
        # Default increment level for AUTO_INCREMENT strategy
        self.increment_level: VersionIncrement = VersionIncrement.PATCH

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
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not isinstance(document, BaseOSDMDocument):
            raise TypeError("Expected BaseOSDMDocument")
        data = await self.write(document)

        # Handle AUTO_INCREMENT before computing versioned path
        if self.osdm_options.version_strategy == VersionStrategy.AUTO_INCREMENT:
            next_ver = self._auto_increment_version(target, self.increment_level)
            document.version = next_ver

        final_path = self._versioned_path(target, document)
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

    # ── Versioning helpers ────────────────────────────────────────
    def _versioned_path(self, original: Path, document: BaseOSDMDocument) -> Path:
        """
        If strategy is OVERWRITE, return the original path unchanged.
        For NEW_VERSION or AUTO_INCREMENT, append the document's version
        string to the stem, e.g., diagram_v1.2.3.bpmn.
        """
        if self.osdm_options.version_strategy == VersionStrategy.OVERWRITE:
            return original
        ver = document.version or "1.0.0"
        stem = original.stem
        # Avoid double version
        if not stem.endswith(f"_v{ver}"):
            stem = f"{stem}_v{ver}"
        return original.with_name(f"{stem}{original.suffix}")

    def _auto_increment_version(self, target: Path, level: VersionIncrement = VersionIncrement.PATCH) -> str:
        """
        Scan existing files with the same base name and extension,
        extract version numbers, find the maximum, and increment
        the specified segment. If no files found, returns '1.0.0'.
        """
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
        """
        Increment the specified part of a semantic version string (e.g., '1.2.3').
        Resets lower parts to zero when incrementing a higher-order part.
        """
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