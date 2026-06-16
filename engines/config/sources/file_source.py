# engines/config/sources/file_source.py
from __future__ import annotations

import json
import os
from typing import Any

from ..plugin import IConfigSource


class FileConfigSource(IConfigSource):
    name = "file"

    def __init__(self, path: str) -> None:
        self._path = path

    async def load(self) -> dict[str, Any]:
        if not os.path.exists(self._path):
            return {}
        with open(self._path) as f:
            if self._path.endswith(".json"):
                return json.load(f)
            return dict(line.split("=", 1) for line in f if "=" in line)

    async def watch(self) -> None:
        pass
