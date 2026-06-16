# engines/artifacts/models/writers/artifact_writer.py
from __future__ import annotations

from ..artifacts_models import Artifact


def write_artifact(artifact: Artifact) -> dict:
    return {
        "artifact_id": artifact.artifact_id,
        "name": artifact.name,
        "metadata": artifact.metadata,
        "version": artifact.version,
    }
