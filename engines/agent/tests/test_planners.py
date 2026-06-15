from __future__ import annotations

from engines.agent.planners import (
    BasePlanner,
    BuiltInPlanner,
    PlanReActPlanner,
    ThinkingConfig,
)


class TestBasePlanner:

    def test_apply_passthrough(self):
        planner = BasePlanner()
        result = planner.apply("do something")
        assert result == "do something"

    def test_get_config_empty(self):
        planner = BasePlanner()
        assert planner.get_config() == {}


class TestBuiltInPlanner:

    def test_default_thinking_config(self):
        planner = BuiltInPlanner()
        config = planner.get_config()
        assert config["thinking_config"]["thinking_budget"] == 1024
        assert config["thinking_config"]["include_thoughts"] is False

    def test_custom_thinking_config(self):
        config = ThinkingConfig(thinking_budget=512, include_thoughts=True)
        planner = BuiltInPlanner(thinking_config=config)
        result = planner.get_config()
        assert result["thinking_config"]["thinking_budget"] == 512
        assert result["thinking_config"]["include_thoughts"] is True

    def test_apply_passthrough(self):
        planner = BuiltInPlanner()
        result = planner.apply("answer this")
        assert result == "answer this"


class TestPlanReActPlanner:

    def test_apply_adds_structure(self):
        planner = PlanReActPlanner()
        result = planner.apply("calculate 2+2")
        assert "**Plan**" in result
        assert "**Action**" in result
        assert "**Reasoning**" in result
        assert "**Final Answer**" in result
        assert "calculate 2+2" in result

    def test_get_config(self):
        planner = PlanReActPlanner()
        config = planner.get_config()
        assert config["planner_type"] == "plan_react"

    def test_instruction_preserved(self):
        planner = PlanReActPlanner()
        result = planner.apply("find weather in London")
        assert result.startswith("find weather in London")
