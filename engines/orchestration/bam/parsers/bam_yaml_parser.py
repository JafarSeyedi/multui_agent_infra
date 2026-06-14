from __future__ import annotations

from typing import Any

from .base_bam_parser import BaseBAMParser


_yaml: Any = None
try:
    import yaml as _yaml
except ImportError:
    pass


class BamYamlParser(BaseBAMParser):
    name = "bam_yaml"
    supported_extensions = (".bam.yaml", ".bam.yml")

    def _decode(self, data: bytes) -> dict[str, Any]:
        if _yaml is None:
            raise ImportError("PyYAML is required for .bam.yaml parsing")
        return _yaml.safe_load(data.decode("utf-8"))
