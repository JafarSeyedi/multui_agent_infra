import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engines.agent.skill.skill import SkillLoader
from engines.agent.skill.executor import BatchSkillExecutor, StepWiseSkillExecutor, LLMClient

class MockLLMClient(LLMClient):
    def __init__(self, return_value):
        self.return_value = return_value
    
    def generate_structured_output(self, prompt, output_schema, **kwargs):
        # For simplicity, we return the preset value regardless of prompt and schema
        return self.return_value
    
    def generate_text(self, prompt, **kwargs):
        return "text response"

def test_batch_skill_executor():
    loader = SkillLoader(os.path.join(os.path.dirname(__file__), 'sample_skill'))
    skill_id = loader.list_skills()[0]
    
    # Mock LLM client that returns a fixed output
    mock_llm = MockLLMClient({"output_text": "HELLO WORLD"})
    executor = BatchSkillExecutor(mock_llm, loader)
    
    # Execute the skill with inputs
    inputs = {"input_text": "hello world"}
    result = executor.execute(skill_id, inputs)
    
    # Check that the result is what we mocked
    assert result == {"output_text": "HELLO WORLD"}
    
    # We could also check that the prompt was constructed correctly, but we trust the mock.

def test_stepwise_skill_executor():
    loader = SkillLoader(os.path.join(os.path.dirname(__file__), 'sample_skill'))
    skill_id = loader.list_skills()[0]
    
    # We need to mock the LLM client to return different values for each step.
    # We'll create a mock that returns a sequence of values.
    call_count = 0
    def mock_generate_structured_output(prompt, output_schema, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First step: return intermediate result
            return {"intermediate": "HELLO WORLD"}
        else:
            # Second step: return final output
            return {"output_text": "HELLO WORLD PROCESSED"}
    
    class MockLLMClientStepwise(LLMClient):
        def generate_structured_output(self, prompt, output_schema, **kwargs):
            return mock_generate_structured_output(prompt, output_schema, **kwargs)
        def generate_text(self, prompt, **kwargs):
            return "text response"
    
    mock_llm = MockLLMClientStepwise()
    executor = StepWiseSkillExecutor(mock_llm, loader)
    
    inputs = {"input_text": "hello world"}
    result = executor.execute(skill_id, inputs)
    
    # The result should be a list of two step results
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == {"intermediate": "HELLO WORLD"}
    assert result[1] == {"output_text": "HELLO WORLD PROCESSED"}

if __name__ == "__main__":
    test_batch_skill_executor()
    test_stepwise_skill_executor()
    print("All executor tests passed!")
