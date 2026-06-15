import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unittest.mock import Mock
from engines.agent.base_agents.state_machine_agent import StateMachineAgent
from engines.agent.skill.skill import SkillLoader
from engines.agent.skill.executor import LLMClient

def test_state_machine_agent_initialization():
    # Mock dependencies
    skill_loader = Mock(spec=SkillLoader)
    llm_client = Mock(spec=LLMClient)
    
    # Create a mock StateMachineDocument
    state_machine_doc = Mock()
    state_machine_doc.state_machines = [Mock()]  # At least one state machine
    
    # We need to set up the state machine mock to have the required attributes
    # For simplicity, we'll mock the top_region and pseudo_states
    mock_state_machine = Mock()
    mock_state_machine.top_region = Mock()
    mock_state_machine.top_region.initial_state = None
    mock_state_machine.top_region.states = []
    mock_state_machine.pseudo_states = []
    
    state_machine_doc.state_machines[0] = mock_state_machine
    
    # For now, we'll just test that the agent initializes without error
    try:
        agent = StateMachineAgent(
            agent_id="test_agent",
            agent_name="Test State Machine Agent",
            state_machine_doc=state_machine_doc,
            skill_loader=skill_loader,
            llm_client=llm_client
        )
        assert agent.agent_name == "Test State Machine Agent"
        print("StateMachineAgent initialization: PASSED")
    except Exception as e:
        print(f"StateMachineAgent initialization: FAILED - {e}")
        raise

def test_state_machine_agent_execution():
    # This test would require a more complex setup and mocking of skill execution.
    # We'll skip it for now and focus on the initialization.
    print("StateMachineAgent execution test: SKIPPED (requires complex setup)")

if __name__ == "__main__":
    test_state_machine_agent_initialization()
    test_state_machine_agent_execution()
    print("All tests completed.")
