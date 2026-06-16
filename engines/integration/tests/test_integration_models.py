# engines/integration/tests/test_integration_models.py
from engines.integration.models.integration_models import ConnectionConfig, SyncResult
from engines.integration.models.parsers.integration_parser import parse_connection_config
from engines.integration.models.writers.integration_writer import write_sync_result


def test_connection_config():
    cfg = ConnectionConfig(endpoint="https://api.example.com", credentials={"key": "val"})
    assert cfg.endpoint == "https://api.example.com"


def test_connection_config_parse():
    data = {"endpoint": "http://localhost", "options": {"timeout": 30}}
    parsed = parse_connection_config(data)
    assert parsed.endpoint == "http://localhost"
    assert parsed.options["timeout"] == 30


def test_sync_result_write():
    result = SyncResult(success_count=5, failure_count=1, errors=["timeout"])
    data = write_sync_result(result)
    assert data["success_count"] == 5
    assert data["failure_count"] == 1
