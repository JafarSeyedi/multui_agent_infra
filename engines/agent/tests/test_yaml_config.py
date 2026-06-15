from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from engines.agent.models import AgentDefinition, AgentType
from engines.agent.yaml_config import AgentDefinitionYamlReader, AgentDefinitionYamlWriter


class TestAgentDefinitionYamlRoundTrip:

    YAML_SAMPLE = """\
name: test_agent
description: A test agent
type: interaction_agent
input_schema:
  type: object
  properties:
    query:
      type: string
output_schema:
  type: object
  properties:
    answer:
      type: string
output_key: answer
config:
  model: gpt-4
"""

    def test_read_yaml(self):
        reader = AgentDefinitionYamlReader()
        definition = reader.read(self.YAML_SAMPLE)
        assert definition.name == "test_agent"
        assert definition.description == "A test agent"
        assert definition.type == AgentType.INTERACTION
        assert definition.input_schema == {"type": "object", "properties": {"query": {"type": "string"}}}
        assert definition.output_schema == {"type": "object", "properties": {"answer": {"type": "string"}}}
        assert definition.output_key == "answer"
        assert definition.config == {"model": "gpt-4"}

    def test_write_yaml(self):
        definition = AgentDefinition(
            name="agent1",
            description="desc",
            type=AgentType.SKILL,
            skill_id="skills/hello.skill.md",
            input_schema={"type": "object"},
            output_key="result",
        )
        writer = AgentDefinitionYamlWriter()
        output = writer.write(definition)
        assert "agent1" in output
        assert "skills/hello.skill.md" in output
        assert "result" in output
        assert "input_schema" in output

    def test_round_trip(self):
        definition = AgentDefinition(
            name="roundtrip",
            description="Round trip test",
            type=AgentType.INTERACTION,
            input_schema={"type": "object", "properties": {"x": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"y": {"type": "integer"}}},
            output_key="y",
            config={"temperature": 0.7},
        )
        writer = AgentDefinitionYamlWriter()
        yaml_str = writer.write(definition)
        reader = AgentDefinitionYamlReader()
        restored = reader.read(yaml_str)
        assert restored.name == definition.name
        assert restored.description == definition.description
        assert restored.type == definition.type
        assert restored.input_schema == definition.input_schema
        assert restored.output_schema == definition.output_schema
        assert restored.output_key == definition.output_key
        assert restored.config == definition.config

    def test_write_file_and_read_back(self):
        definition = AgentDefinition(
            name="file_test",
            description="File test",
            type=AgentType.STATE_MACHINE,
        )
        writer = AgentDefinitionYamlWriter()
        reader = AgentDefinitionYamlReader()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False,
        ) as f:
            path = Path(f.name)
            writer.write_file(definition, path)

        try:
            restored = reader.read_file(path)
            assert restored.name == "file_test"
            assert restored.type == AgentType.STATE_MACHINE
        finally:
            path.unlink()

    def test_read_minimal(self):
        yaml_str = "name: minimal\ndescription: Minimal agent\ntype: interaction_agent\n"
        reader = AgentDefinitionYamlReader()
        definition = reader.read(yaml_str)
        assert definition.name == "minimal"
        assert definition.input_schema is None
        assert definition.output_schema is None
        assert definition.output_key is None

    def test_write_minimal(self):
        definition = AgentDefinition(
            name="minimal",
            description="Minimal",
            type=AgentType.INTERACTION,
        )
        writer = AgentDefinitionYamlWriter()
        output = writer.write(definition)
        restored = yaml.safe_load(output)
        assert restored["name"] == "minimal"
        assert "input_schema" not in restored

    def test_read_from_file(self):
        reader = AgentDefinitionYamlReader()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False,
        ) as f:
            f.write(self.YAML_SAMPLE)
            path = Path(f.name)

        try:
            definition = reader.read_file(path)
            assert definition.name == "test_agent"
        finally:
            path.unlink()

    def test_write_with_output_key(self):
        definition = AgentDefinition(
            name="keyed",
            description="Has output key",
            type=AgentType.INTERACTION,
            output_key="result",
        )
        writer = AgentDefinitionYamlWriter()
        output = writer.write(definition)
        restored = yaml.safe_load(output)
        assert restored["output_key"] == "result"
