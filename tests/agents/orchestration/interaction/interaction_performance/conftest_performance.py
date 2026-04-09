# tests/agents/orchestration/interaction/interaction_performance/conftest_performance.py
from tests.agents.orchestration.interaction.interaction_unit.conftest import DummyMessageBus, TestRegistry

import pytest


@pytest.fixture
def registry() -> TestRegistry:
    return TestRegistry()


@pytest.fixture
def message_bus() -> DummyMessageBus:
    return DummyMessageBus()
