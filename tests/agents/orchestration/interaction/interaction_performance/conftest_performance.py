# tests/agents/orchestration/interaction/performance/conftest.py
from tests.agents.orchestration.interaction.unit.conftest import DummyMessageBus, TestRegistry

import pytest


@pytest.fixture
def registry() -> TestRegistry:
    return TestRegistry()


@pytest.fixture
def message_bus() -> DummyMessageBus:
    return DummyMessageBus()