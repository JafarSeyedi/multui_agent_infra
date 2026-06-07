import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unittest.mock import Mock
from engines.agent.agent_registry import AgentRegistry
from engines.agent.base_agents.skill_agent import SkillAgent
from engines.agent.skill.skill import SkillLoader
from engines.agent.skill.executor import LLMClient

def test_agent_registry_register_and_get():
    # Create registry
    registry = AgentRegistry()
    
    # Create mock dependencies for the skill agent
    skill_loader = Mock(spec=SkillLoader)
    llm_client = Mock(spec=LLMClient)
    
    # Create a skill agent
    skill_agent = SkillAgent(
        agent_id="test_agent",
        agent_name="Test Skill Agent",
        skill_id="test_skill",
        skill_loader=skill_loader,
        llm_client=llm_client,
        execution_mode="batch"
    )
    
    # Register the agent
    registered_agent = registry.register(skill_agent)
    assert registered_agent == skill_agent
    
    # Retrieve the agent
    retrieved_agent = registry.get("Test Skill Agent")
    assert retrieved_agent == skill_agent
    
    print("AgentRegistry register and get: PASSED")

def test_agent_registry_run():
    # Create registry
    registry = AgentRegistry()
    
    # Create mock dependencies for the skill agent
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
    from engines.agent.skill.models import SkillOutput
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
    skill_agent = SkillAgent(
        agent_id="test_agent",
        agent_name="Test Skill Agent",
        skill_id="test_skill",
        skill_loader=skill_loader,
        llm_client=llm_client,
        execution_mode="batch"
    )
    
    # Register the agent
    registry.register(skill_agent)
    
    # Create input
    input_data = {
        "agent_name": "Test Skill Agent",
        "skill_input": {"input": "test"}
    }
    
    # Run the agent
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    output = loop.run_until_complete(registry.run("Test Skill Agent", input_data))
    
    # Check the output
    assert output.agent_name == "Test Skill Agent"
    assert output.skill_output == {"test_output": "test_result"}
    print("AgentRegistry run: PASSED")

if __name__ == "__main__":
    test_agent_registry_register_and_get()
    test_agent_registry_run()
    print("All tests completed.")
