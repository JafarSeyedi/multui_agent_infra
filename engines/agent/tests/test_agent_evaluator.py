import pytest
from engines.agent.agent_evaluator import AgentEvaluator, TestCase, AgentEvaluationResult


class FakeAgent:
    def __init__(self, name: str = "test-agent"):
        self.agent_name = name

    async def run(self, input_data: dict) -> str:
        return f"result:{input_data.get('x', 'none')}"


@pytest.mark.asyncio
async def test_evaluate_passed():
    agent = FakeAgent()
    evaluator = AgentEvaluator()
    cases = [
        TestCase(input={"x": "a"}, expected="result:a", name="case1"),
        TestCase(input={"x": "b"}, expected="result:b", name="case2"),
    ]
    evaluator.register_suite("test", cases)
    result = await evaluator.evaluate(agent, "test")
    assert result.passed == 2
    assert result.failed == 0
    assert result.test_cases == 2
    assert result.metrics["accuracy"] == 1.0


@pytest.mark.asyncio
async def test_evaluate_failed():
    agent = FakeAgent()
    evaluator = AgentEvaluator()
    cases = [
        TestCase(input={"x": "a"}, expected="wrong", name="fail_case"),
    ]
    evaluator.register_suite("test", cases)
    result = await evaluator.evaluate(agent, "test")
    assert result.passed == 0
    assert result.failed == 1
    assert len(result.errors) == 1


@pytest.mark.asyncio
async def test_evaluate_empty_suite():
    agent = FakeAgent()
    evaluator = AgentEvaluator()
    result = await evaluator.evaluate(agent)
    assert result.test_cases >= 0


def test_unknown_suite_raises():
    evaluator = AgentEvaluator()
    with pytest.raises(ValueError, match="Unknown suite"):
        import asyncio
        asyncio.run(evaluator.evaluate(FakeAgent(), "nonexistent"))
