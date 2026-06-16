# engines/artifacts/models/parsers/artifact_parser.py
from __future__ import annotations

from ..artifacts_models import Artifact


def parse_artifact(data: dict) -> Artifact:
    return Artifact(
        artifact_id=data.get("artifact_id", ""),
        name=data.get("name", ""),
        data=data.get("data", b""),
        metadata=data.get("metadata", {}),
        version=data.get("version", 1),
    )
