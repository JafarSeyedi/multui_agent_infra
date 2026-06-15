import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engines.agent.skill.skill import SkillLoader

def test_skill_loader_loads_skill():
    # Initialize loader with the sample skill directory
    loader = SkillLoader(os.path.join(os.path.dirname(__file__), 'sample_skill'))
    
    # List skills
    skills = loader.list_skills()
    assert len(skills) == 1
    skill_id = skills[0]
    
    # Get the skill
    skill = loader.get_skill(skill_id)
    assert skill is not None
    assert skill.name == "Sample Skill"
    assert skill.description == "A sample skill for testing."
    assert skill.version == "1.0.0"
    assert skill.author == "Kilo"
    assert skill.tags == ["sample", "test"]
    assert len(skill.inputs) == 1
    assert skill.inputs[0].name == "input_text"
    assert skill.inputs[0].description == "The input text to process."
    assert skill.inputs[0].type == "string"
    assert skill.inputs[0].required
    assert len(skill.outputs) == 1
    assert skill.outputs[0].name == "output_text"
    assert skill.outputs[0].description == "The processed output text."
    assert skill.outputs[0].type == "string"
    assert skill.references == ["reference.txt"]
    assert skill.steps is not None
    assert len(skill.steps) == 2
    assert skill.steps[0].name == "Step 1"
    assert skill.steps[0].description == "First step."
    assert skill.steps[0].instructions == "Process the input."
    assert skill.steps[0].output_schema == {
        "type": "object",
        "properties": {
            "intermediate": {
                "type": "string",
                "description": "Intermediate result."
            }
        },
        "required": ["intermediate"]
    }
    assert skill.steps[1].name == "Step 2"
    assert skill.steps[1].description == "Second step."
    assert skill.steps[1].instructions == "Finalize the output."
    assert skill.steps[1].output_schema == {
        "type": "object",
        "properties": {
            "output_text": {
                "type": "string",
                "description": "Final output."
            }
        },
        "required": ["output_text"]
    }
    # Check that the content is loaded correctly
    assert "This is the content of the sample skill." in skill.content
    assert "It processes the input text and returns it in uppercase." in skill.content
    
    # Check that reference content can be loaded
    base_path = loader.get_skill_base_path(skill_id)
    assert base_path is not None
    ref_contents = skill.get_reference_content(base_path)
    assert "reference.txt" in ref_contents
    # The reference file may have a newline at the end; we'll strip whitespace for comparison.
    assert ref_contents["reference.txt"].strip() == "This is a reference file."

if __name__ == "__main__":
    test_skill_loader_loads_skill()
    print("All tests passed!")
