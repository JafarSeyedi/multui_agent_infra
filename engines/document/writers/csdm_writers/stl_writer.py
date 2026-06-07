# engines/document/writers/csdm_writers/stl_writer.py
"""
STL writer for CSDM (CAD Standard Definition Model).
Converts a CSDMDocument to STL format.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.csdm_core import CSDMDocument
from .base import CSDMBaseWriter
from .base import CSDMWriteOptions


class STLWriter(CSDMBaseWriter):
    """
    Writer for STL (STereoLithography) files.
    Exports CSDM document to binary or ASCII STL format.
    """

    def __init__(self, options: CSDMWriteOptions | None = None):
        super().__init__(options)

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """Yield STL content in chunks."""
        doc = self._extract_csdm_data(document)
        content = await self._write_stlc(doc)  # ASCII STL
        # Yield in chunks for large files
        chunk_size = 64 * 1024  # 64KB chunks
        for i in range(0, len(content), chunk_size):
            yield content[i:i+chunk_size].encode('utf-8')

    async def write(self, document: BaseDocument) -> bytes:
        """Return full STL content as bytes."""
        doc = self._extract_csdm_data(document)
        content = await self._write_stlc(doc)  # ASCII STL
        return content.encode('utf-8')

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None
    ) -> None:
        """Write STL directly to a file."""
        doc = self._extract_csdm_data(document)
        content = await self._write_stlc(doc)  # ASCII STL
        target.write_text(content, encoding='utf-8')

    async def _write_stlc(self, doc: CSDMDocument) -> str:
        """Generate ASCII STL content from CSDM document."""
        lines = []
        
        # STL header
        lines.append("solid csdm_model")
        
        # TODO: Implement full STL generation from CSDM geometric data
        # This would involve:
        # 1. Extracting all 3D geometric data from CSDM entities
        # 2. Converting to triangular meshes
        # 3. Calculating normals for each triangle
        # 4. Outputting each triangle in STL format
        
        # For now, add a minimal placeholder triangle (a unit square divided into 2 triangles)
        # Triangle 1
        lines.extend([
            "  facet normal 0.0 0.0 1.0",
            "    outer loop",
            "      vertex 0.0 0.0 0.0",
            "      vertex 1.0 0.0 0.0",
            "      vertex 0.0 1.0 0.0",
            "    endloop",
            "  endfacet"
        ])
        
        # Triangle 2
        lines.extend([
            "  facet normal 0.0 0.0 1.0",
            "    outer loop",
            "      vertex 1.0 0.0 0.0",
            "      vertex 1.0 1.0 0.0",
            "      vertex 0.0 1.0 0.0",
            "    endloop",
            "  endfacet"
        ])
        
        lines.append("endsolid csdm_model")
        
        return "\n".join(lines)

    def get_supported_media_types(self) -> list[str]:
        """Get list of supported media types."""
        return ["application/sla"]  # Common MIME for STL

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return [".stl"]