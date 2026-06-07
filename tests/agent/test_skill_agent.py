import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unittest.mock import Mock
from engines.agent.base_agents.skill_agent import SkillAgent, SkillAgentInput, SkillAgentOutput
from engines.agent.skill.skill import SkillLoader
from engines.agent.skill.executor import LLMClient
from engines.agent.skill.models import SkillOutput

def test_skill_agent_initialization():
    # Mock dependencies
    skill_loader = Mock(spec=SkillLoader)
    llm_client = Mock(spec=LLMClient)
    
    # Create a skill agent
    agent = SkillAgent(
        agent_id="test_agent",
        agent_name="Test Skill Agent",
        skill_id="test_skill",
        skill_loader=skill_loader,
        llm_client=llm_client,
        execution_mode="batch"
    )
    
    assert agent.agent_name == "Test Skill Agent"
    assert agent.skill_id == "test_skill"
    assert agent.execution_mode == "batch"
    print("SkillAgent initialization: PASSED")

def test_skill_agent_execution():
    # Mock dependencies
    skill_loader = Mock(spec=SkillLoader)
    llm_client = Mock(spec=LLMClient)
    
    # Mock the skill loader to return a skill
    mock_skill = Mock()
    mock_skill.name = "test_skill"
    skill_loader.get_skill.return_value = mock_skill
    skill_loader.get_skill_base_path.return_value = "/fake/path"
    
    # Mock the skill's get_reference_content to return empty dict
    mock_skill.get_reference_content.return_value = {}
    
    # Mock the skill's outputs attribute
    mock_output = Mock(spec=SkillOutput)
    mock_output.name = "test_output"
    mock_output.type = "string"
    mock_output.output_schema = None
    mock_output.description = "Test output"
    mock_skill.outputs = [mock_output]
    
    # Mock the LLM client to return a fixed output
    llm_client.generate_structured_output.return_value = {"test_output": "test_result"}
    llm_client.generate_text.return_value = '{"test_output": "test_result"}'
    
    # Create a skill agent
    agent = SkillAgent(
        agent_id="test_agent",
        agent_name="Test Skill Agent",
        skill_id="test_skill",
        skill_loader=skill_loader,
        llm_client=llm_client,
        execution_mode="batch"
    )
    
    # Create input
    input_data = SkillAgentInput(
        agent_name="Test Skill Agent",
        skill_input={"input": "test"}
    )
    
    # Execute the agent
    # Note: We are calling the execute method directly, which is async.
    # We'll run it in an event loop.
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    output = loop.run_until_complete(agent.execute(input_data))
    
    # Check the output
    assert isinstance(output, SkillAgentOutput)
    assert output.agent_name == "Test Skill Agent"
    assert output.skill_output == {"test_output": "test_result"}
    print("SkillAgent execution: PASSED")

if __name__ == "__main__":
    test_skill_agent_initialization()
    test_skill_agent_execution()
    print("All tests completed.")
