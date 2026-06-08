from __future__ import annotations

import traceback
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.csdm_core import CSDMDocument
from .base import CSDMBaseWriter
from .base import CSDMWriteOptions
from .dwg.pipeline import DWGPipeline


class DWGWriter(CSDMBaseWriter):
    def __init__(self, options: CSDMWriteOptions | None = None):
        super().__init__(options)

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        doc = self._extract_csdm_data(document)
        content = await self._write_dwg(doc)
        chunk_size = 64 * 1024
        for i in range(0, len(content), chunk_size):
            yield content[i:i+chunk_size]

    async def write(self, document: BaseDocument) -> bytes:
        doc = self._extract_csdm_data(document)
        content = await self._write_dwg(doc)
        return content

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None
    ) -> None:
        doc = self._extract_csdm_data(document)
        content = await self._write_dwg(doc)
        target.write_bytes(content)

    async def _write_dwg(self, doc: CSDMDocument) -> bytes:
        try:
            pipeline = DWGPipeline(doc)
            return pipeline.run()
        except ImportError:
            raise RuntimeError(
                "ODA (Open Design Alliance) library is required for DWG writing. "
                "Please install the odapython package."
            )
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"Failed to write DWG file: {e}")

    def get_supported_media_types(self) -> list[str]:
        return ["image/vnd.dwg"]

    def get_supported_extensions(self) -> list[str]:
        return [".dwg"]
