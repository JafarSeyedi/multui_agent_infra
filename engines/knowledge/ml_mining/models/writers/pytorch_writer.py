from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO

from engines.document.writers.base import BaseDocument, BaseDocumentWriter
from engines.knowledge.ml_mining.models import MlMiningDocument


class PyTorchWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document: Any) -> bool:
        return isinstance(document, MlMiningDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | None = None,
                    **options: Any) -> bytes:
        doc = MlMiningDocument.model_validate(document)
        model_bytes = doc.model_data or b""

        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(model_bytes)
            else:
                destination.write(model_bytes)
        return model_bytes

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write_to_file(self, document: BaseDocument, target: Path,
                            options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/octet-stream"]

    def get_supported_extensions(self) -> list[str]:
        return [".pt", ".pth", ".pytorch"]
