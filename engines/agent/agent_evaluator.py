"""ADT-style agent evaluation tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass
class TestCase:
    """A single test case for agent evaluation."""
    input: dict[str, Any]
    expected: Any
    name: str = ""


@dataclass
class AgentEvaluationResult:
    """Result of evaluating an agent against a test suite."""
    agent_name: str
    test_cases: int = 0
    passed: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    total_time_ms: float = 0.0


class AgentEvaluator:
    """Evaluates agent performance against test suites."""

    def __init__(self) -> None:
        self._suites: dict[str, list[TestCase]] = {}

    def register_suite(self, name: str, cases: list[TestCase]) -> None:
        self._suites[name] = cases

    async def evaluate(self, agent: Any, suite_name: str = "") -> AgentEvaluationResult:
        if suite_name and suite_name in self._suites:
            cases = self._suites[suite_name]
        elif suite_name:
            raise ValueError(f"Unknown suite '{suite_name}'")
        else:
            cases = [TestCase(input={}, expected=None, name="default")]

        result = AgentEvaluationResult(
            agent_name=getattr(agent, "agent_name", str(agent)),
            test_cases=len(cases),
        )

        start = time()
        for case in cases:
            try:
                output = await agent.run(case.input)
                if case.expected is not None and output != case.expected:
                    result.failed += 1
                    result.errors.append(f"'{case.name}': expected {case.expected}, got {output}")
                else:
                    result.passed += 1
            except Exception as e:
                result.failed += 1
                result.errors.append(f"'{case.name}': raised {e}")
        result.total_time_ms = (time() - start) * 1000

        if result.test_cases > 0:
            result.metrics["accuracy"] = result.passed / result.test_cases
            result.metrics["avg_time_ms"] = result.total_time_ms / result.test_cases

        return result
