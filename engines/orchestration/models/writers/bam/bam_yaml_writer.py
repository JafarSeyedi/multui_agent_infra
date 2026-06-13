from __future__ import annotations

from typing import Any

from .base_bam_writer import BaseBAMWriter


_yaml: Any = None
try:
    import yaml as _yaml
except ImportError:
    pass


class BamYamlWriter(BaseBAMWriter):
    media_type = "application/x-yaml"
    supported_extensions = (".bam.yaml", ".bam.yml")

    def _serialize(self, raw: dict[str, Any]) -> bytes:
        if _yaml is None:
            raise ImportError("PyYAML is required for .bam.yaml writing")
        return _yaml.safe_dump(raw, default_flow_style=False, sort_keys=False).encode("utf-8")
