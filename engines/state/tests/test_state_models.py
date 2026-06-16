# engines/state/tests/test_state_models.py
from engines.state.models.state_models import StateEntry, CacheEntry
from engines.state.models.parsers.state_config_parser import parse_state_entry
from engines.state.models.writers.state_config_writer import write_state_entry


def test_state_entry_defaults():
    entry = StateEntry(instance_id="test-1")
    assert entry.version == 1
    assert entry.data == {}


def test_state_entry_roundtrip():
    entry = StateEntry(instance_id="t", data={"key": "val"}, version=2)
    data = write_state_entry(entry)
    parsed = parse_state_entry(data)
    assert parsed.instance_id == "t"
    assert parsed.data["key"] == "val"
    assert parsed.version == 2


def test_cache_entry():
    entry = CacheEntry(key="k", value="v", ttl=60.0)
    assert entry.key == "k"
    assert entry.value == "v"
