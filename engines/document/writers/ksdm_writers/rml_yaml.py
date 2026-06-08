from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import yaml

from engines.document.models.ksdm_models import KSDMDocument
from engines.document.writers.base import BaseDocumentWriter, WriteOptions


class RMLYAMLWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: KSDMDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write(self, document: KSDMDocument) -> bytes:
        data: dict[str, Any] = {"mappings": document.ontology.get("rml_mapping", []) if document.ontology else []}
        return yaml.dump(data).encode("utf-8")

    async def write_to_file(self, document: KSDMDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/x-yaml"]

    def get_supported_extensions(self) -> list[str]:
        return [".rml.yaml", ".rml.yml"]
