from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import AgentDefinition


class AgentDefinitionYamlReader:
    def read(self, data: str | bytes) -> AgentDefinition:
        raw: dict[str, Any] = yaml.safe_load(data)
        return AgentDefinition(**raw)

    def read_file(self, path: str | Path) -> AgentDefinition:
        with open(path, "r") as f:
            return self.read(f.read())


class AgentDefinitionYamlWriter:
    def write(self, definition: AgentDefinition) -> str:
        return yaml.safe_dump(
            definition.model_dump(mode="json", exclude_none=True),
            sort_keys=False,
            allow_unicode=True,
        )

    def write_file(self, definition: AgentDefinition, path: str | Path) -> None:
        with open(path, "w") as f:
            f.write(self.write(definition))
