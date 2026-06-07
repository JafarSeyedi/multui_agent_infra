# tests/agents/orchestration/interaction/interaction_performance/conftest_performance.py
import pytest

from tests.agent.interaction.interaction_unit.conftest import DummyMessageBus1
from tests.agent.interaction.interaction_unit.conftest import TestRegistry


@pytest.fixture
def registry() -> TestRegistry:
    return TestRegistry()


@pytest.fixture
def message_bus() -> DummyMessageBus1:
    return DummyMessageBus1()
