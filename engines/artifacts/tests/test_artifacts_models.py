# engines/artifacts/tests/test_artifacts_models.py
from engines.artifacts.models.artifacts_models import Artifact
from engines.artifacts.models.parsers.artifact_parser import parse_artifact
from engines.artifacts.models.writers.artifact_writer import write_artifact


def test_artifact_defaults():
    a = Artifact(artifact_id="a1", name="model.pkl", data=b"data")
    assert a.version == 1


def test_artifact_roundtrip():
    a = Artifact(artifact_id="a1", name="config.json", data=b"{}", metadata={"env": "prod"}, version=2)
    data = write_artifact(a)
    parsed = parse_artifact(data)
    assert parsed.name == "config.json"
    assert parsed.metadata["env"] == "prod"
    assert parsed.version == 2
