# engines/config/tests/test_config_models.py
from engines.config.models.config_models import ConfigEntry, SecretRef
from engines.config.models.parsers.config_yaml_parser import parse_config_entry
from engines.config.models.writers.config_yaml_writer import write_config_entry


def test_config_entry():
    entry = ConfigEntry(key="k", value="v")
    assert entry.key == "k"


def test_config_roundtrip():
    entry = ConfigEntry(key="db.host", value="localhost", source="file")
    data = write_config_entry(entry)
    parsed = parse_config_entry(data)
    assert parsed.key == "db.host"
    assert parsed.value == "localhost"


def test_secret_ref():
    ref = SecretRef(ref="db-password", resolver="vault")
    assert ref.ref == "db-password"
