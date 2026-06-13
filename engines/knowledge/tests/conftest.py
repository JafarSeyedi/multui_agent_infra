# tests/knowledge/conftest.py
"""
Shared fixtures for knowledge engine tests.
"""
import pytest
import asyncio


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
