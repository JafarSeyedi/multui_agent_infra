# engines/config/tests/test_config_sources.py
import os
import tempfile

import pytest

from engines.config.sources.file_source import FileConfigSource
from engines.config.resolvers.environment_resolver import EnvironmentSecretResolver


@pytest.mark.asyncio
async def test_file_source_json():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"key": "val"}')
        path = f.name
    source = FileConfigSource(path)
    data = await source.load()
    assert data.get("key") == "val"
    os.unlink(path)


@pytest.mark.asyncio
async def test_file_source_missing():
    source = FileConfigSource("/nonexistent/config.txt")
    data = await source.load()
    assert data == {}


@pytest.mark.asyncio
async def test_environment_resolver():
    resolver = EnvironmentSecretResolver()
    os.environ["TEST_SECRET"] = "secret-value"
    result = await resolver.resolve("TEST_SECRET")
    assert result == "secret-value"
    del os.environ["TEST_SECRET"]
