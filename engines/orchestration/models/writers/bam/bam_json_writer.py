from __future__ import annotations

import json
from typing import Any

from .base_bam_writer import BaseBAMWriter


class BamJsonWriter(BaseBAMWriter):
    media_type = "application/json"
    supported_extensions = (".bam.json",)

    def _serialize(self, raw: dict[str, Any]) -> bytes:
        return json.dumps(raw, indent=2, default=str).encode("utf-8")
