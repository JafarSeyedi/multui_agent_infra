# engines/document/writers/csdm_writers/base.py
"""
Base classes and shared utilities for CSDM writers (CAD formats).
"""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.csdm_core import CSDMDocument
from ..base import BaseDocumentWriter
from ..base import WriteOptions


class CSDMWriteOptions(WriteOptions):
    """Extended write options for CAD formats."""

    # CSDM specific
    include_geometry: bool = True          # Include geometric data
    include_properties: bool = True        # Include entity properties
    include_layers: bool = True            # Include layer information
    include_blocks: bool = True            # Include block definitions
    include_xrefs: bool = True             # Include external references
    precision: int = 6                     # Decimal precision for coordinates
    units: str = "mm"                      # Default units for output


class CSDMBaseWriter(BaseDocumentWriter):
    """
    Abstract base for all CSDM writers.
    
    Provides shared logic for CAD file writing.
    """

    def __init__(self, options: CSDMWriteOptions | None = None):
        # Ensure options are of the correct type
        if options is None:
            options = CSDMWriteOptions()
        elif not isinstance(options, CSDMWriteOptions):
            # Convert if a plain WriteOptions is passed
            options = CSDMWriteOptions(**options.model_dump())
        super().__init__(options)
        self._csdm_options = options

    # ------------------------------------------------------------------
    # Abstract methods from BaseDocumentWriter (must be overridden)
    # ------------------------------------------------------------------
    @abstractmethod
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """Yield chunks of the resulting file."""
        yield b""

    @abstractmethod
    async def write(self, document: BaseDocument) -> bytes:
        """Return full file content as bytes."""
        return b""

    @abstractmethod
    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None
    ) -> None:
        """Write directly to a file."""

    # ------------------------------------------------------------------
    # Shared utilities for CSDM writing
    # ------------------------------------------------------------------
    def _extract_csdm_data(self, document: BaseDocument) -> CSDMDocument:
        """Extract CSDM data from BaseDocument."""
        if not isinstance(document, CSDMDocument):
            raise ValueError("Document is not a CSDMDocument")
        return document

    def _format_coordinate(self, value: float) -> str:
        """Format a coordinate value according to precision settings."""
        return f"{value:.{self._csdm_options.precision}f}".rstrip('0').rstrip('.')

    def _normalize_layer_name(self, layer_name: str) -> str:
        """Normalize a layer name for output format."""
        return layer_name or "0"

    def _get_color_value(self, color_int: int) -> int:
        """Convert color integer to format-specific color value."""
        # Default implementation - can be overridden by specific writers
        return color_int