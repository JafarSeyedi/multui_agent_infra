# engines/document/writers/csdm_writers/dwg_writer.py
"""
DWG writer for CSDM (CAD Standard Definition Model).
Converts a CSDMDocument to DWG format using ODA.
"""
from __future__ import annotations

import traceback
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.csdm_core import CSDMDocument
from .base import CSDMBaseWriter
from .base import CSDMWriteOptions


class DWGWriter(CSDMBaseWriter):
    """
    Writer for DWG (Drawing) files.
    Exports CSDM document to binary DWG format using ODA.
    """

    def __init__(self, options: CSDMWriteOptions | None = None):
        super().__init__(options)

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """Yield DWG content in chunks."""
        doc = self._extract_csdm_data(document)
        content = await self._write_dwg(doc)
        # Yield in chunks for large files
        chunk_size = 64 * 1024  # 64KB chunks
        for i in range(0, len(content), chunk_size):
            yield content[i:i+chunk_size]

    async def write(self, document: BaseDocument) -> bytes:
        """Return full DWG content as bytes."""
        doc = self._extract_csdm_data(document)
        content = await self._write_dwg(doc)
        return content

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None
    ) -> None:
        """Write DWG directly to a file."""
        doc = self._extract_csdm_data(document)
        content = await self._write_dwg(doc)
        target.write_bytes(content)

    async def _write_dwg(self, doc: CSDMDocument) -> bytes:
        """Generate DWG content from CSDM document using ODA."""
        try:
            # Import ODA here to avoid dependency issues if not available
            import odapython as oda # type: ignore[import-not-found]
            
            # Create a new database
            db = oda.OdDbDatabase.createDatabase()
            
            # TODO: Implement full CSDM to DWG conversion
            # This would involve:
            # 1. Creating layers from doc.tables.layers
            # 2. Creating linetypes, text styles, etc.
            # 3. Creating blocks from doc.blocks
            # 4. Creating entities from doc.entities
            # 5. Setting up document properties
            
            # For now, return a minimal valid DWG
            # In a real implementation, this would populate the database with actual data
            
            # Save to bytes
            strm = oda.OdMemoryStream()
            db.writeFile(strm)
            return strm.getBytes()
            
        except ImportError:
            # ODA not available, raise informative error
            raise RuntimeError(
                "ODA (Open Design Alliance) library is required for DWG writing. "
                "Please install the odapython package."
            )
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"Failed to write DWG file: {e}")

    def get_supported_media_types(self) -> list[str]:
        """Get list of supported media types."""
        return ["image/vnd.dwg"]

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return [".dwg"]