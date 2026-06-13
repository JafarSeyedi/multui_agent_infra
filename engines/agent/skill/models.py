from typing import Any
from pydantic import BaseModel, Field


class SkillInput(BaseModel):
    name: str
    description: str
    type: str = Field(default="string")
    required: bool = Field(default=False)


class SkillOutput(BaseModel):
    name: str
    description: str
    # The type can be a primitive type string or "object"/"array" when output_schema is provided
    type: str = Field(default="string")
    # Optional JSON schema for this output (for complex types)
    output_schema: dict[str, Any] | None = None


class SkillStep(BaseModel):
    name: str
    description: str
    # Optional: specific instructions for this step
    instructions: str | None = None
    # Optional: expected output schema for this step
    output_schema: dict[str, Any] | None = None


class Skill(BaseModel):
    name: str
    description: str
    version: str = Field(default="1.0.0")
    author: str | None = None
    tags: list[str] = Field(default_factory=list)
    inputs: list[SkillInput] = Field(default_factory=list)
    outputs: list[SkillOutput] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)  # relative file paths
    content: str  # the main markdown content after the frontmatter
    steps: list[SkillStep] | None = Field(default=None)  # if step-wise execution is defined
    # Execution mode: either "batch" or "step-wise". If not provided, inferred from steps.
    execution_mode: str | None = Field(default=None)  # "batch", "step-wise"

    def get_reference_content(self, base_path: str) -> dict:
        """
        Load the content of all reference files.
        Returns a dictionary mapping reference file path to its content.
        """
        reference_contents = {}
        for ref in self.references:
            ref_path = f"{base_path}/{ref}"
            try:
                with open(ref_path) as f:
                    reference_contents[ref] = f.read()
            except FileNotFoundError:
                # If reference not found, we can either raise an error or skip.
                # For now, we'll skip and log a warning, but we'll raise an error to be safe.
                raise FileNotFoundError(f"Reference file not found: {ref_path}")
        return reference_contents

    def get_effective_execution_mode(self) -> str:
        """
        Returns the effective execution mode: if execution_mode is set, use it;
        otherwise, if steps are defined, return "step-wise", else "batch".
        """
        if self.execution_mode:
            return self.execution_mode
        if self.steps:
            return "step-wise"
        return "batch"
