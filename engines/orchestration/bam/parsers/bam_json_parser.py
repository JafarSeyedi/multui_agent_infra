from __future__ import annotations

import json
from typing import Any

from .base_bam_parser import BaseBAMParser


class BamJsonParser(BaseBAMParser):
    name = "bam_json"
    supported_extensions = (".bam.json",)

    def _decode(self, data: bytes) -> dict[str, Any]:
        return json.loads(data.decode("utf-8"))
