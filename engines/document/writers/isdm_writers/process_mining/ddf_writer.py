import json
from pathlib import Path
from typing import Any, cast, BinaryIO, TextIO

from engines.document.writers.base import BaseKnowledgeWriter, BaseDocument
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.isdm_models import ProcessMiningDocument


class DdfWriter(BaseKnowledgeWriter):
    supported_format = MEDIA_TYPES["ddf_json"]

    def can_write(self, document) -> bool:
        return isinstance(document, ProcessMiningDocument)

    async def write(self, document: ProcessMiningDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        data = {
            "framework_id": "",
            "description": "",
            "decision_points": [],
            "discovered_process_model": document.discovered_process_model or {},
        }
        json_bytes = json.dumps(data, indent=2).encode('utf-8')
        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(json_bytes)
            else:
                cast(BinaryIO, destination).write(json_bytes)
        return json_bytes


can_write = DdfWriter.can_write
write = DdfWriter.write
