import json
import logging
from typing import Any, Dict, List, Protocol

from .models import SkillOutput, SkillStep
from .skill import SkillLoader

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        pass

    def generate_structured_output(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        **kwargs
    ) -> Any:
        """
        Generate a structured output from the LLM given a prompt and an output schema.
        This method should be implemented by the user to use their preferred LLM.
        """
        raise NotImplementedError("LLMClient.generate_structured_output must be implemented")

    def generate_text(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """
        Generate a text output from the LLM given a prompt.
        This method should be implemented by the user.
        """
        raise NotImplementedError("LLMClient.generate_text must be implemented")


def _build_output_schema_from_skill_outputs(outputs: List[SkillOutput]) -> Dict[str, Any]:
    """
    Build a JSON schema from a list of SkillOutput objects.
    If an output has an output_schema, use it; otherwise, build a primitive schema.
    """
    properties = {}
    required = []
    for output in outputs:
        if output.output_schema:
            properties[output.name] = output.output_schema
        else:
            # Map the type string to a JSON schema type
            json_type = output.type.lower()
            # We only handle primitive types here; for complex types, output_schema should be provided
            if json_type in ("string", "number", "integer", "boolean"):
                properties[output.name] = {
                    "type": json_type,
                    "description": output.description
                }
            else:
                # Fallback to string for unknown types
                properties[output.name] = {
                    "type": "string",
                    "description": output.description
                }
        # All skill outputs are considered required
        required.append(output.name)
    return {
        "type": "object",
        "properties": properties,
        "required": required
    }


def _build_output_schema_from_step(step: SkillStep, skill_outputs: List[SkillOutput]) -> Dict[str, Any]:
    """
    Build a JSON schema for a step.
    If the step has an output_schema, use it.
    Otherwise, if the skill has outputs, build a schema from the skill outputs.
    Otherwise, return an empty object schema.
    """
    if step.output_schema:
        return step.output_schema
    # If no step output schema, try to use the skill's outputs
    if skill_outputs:
        return _build_output_schema_from_skill_outputs(skill_outputs)
    # Fallback to empty object
    return {"type": "object", "properties": {}, "required": []}


class SkillExecutor(Protocol):
    def execute(self, skill_identifier: str, inputs: Dict[str, Any], **kwargs) -> Any: ...


class BatchSkillExecutor:
    def __init__(self, llm_client: LLMClient, skill_loader: SkillLoader):
        self.llm_client = llm_client
        self.skill_loader = skill_loader
        logger.debug("BatchSkillExecutor initialized")

    def execute(
        self,
        skill_identifier: str,
        inputs: Dict[str, Any],
        **kwargs
    ) -> Any:
        """
        Execute a skill in batch mode: load the entire skill context and call the LLM once.
        """
        logger.info(f"Executing skill {skill_identifier} in batch mode")
        skill = self.skill_loader.get_skill(skill_identifier)
        if not skill:
            raise ValueError(f"Skill not found: {skill_identifier}")

        base_path = self.skill_loader.get_skill_base_path(skill_identifier)
        if base_path is None:
            raise ValueError(f"Could not determine base path for skill: {skill_identifier}")

        # Load reference contents
        try:
            reference_contents = skill.get_reference_content(base_path)
        except FileNotFoundError as e:
            logger.error(f"Failed to load skill references: {e}")
            raise ValueError(f"Failed to load skill references: {e}")

        # Build the context for the LLM
        context_parts = [
            f"Skill Name: {skill.name}",
            f"Skill Description: {skill.description}",
            f"Skill Version: {skill.version}",
            f"\nSkill Content:\n{skill.content}",
        ]

        if reference_contents:
            context_parts.append("\nReferences:")
            for ref_name, ref_content in reference_contents.items():
                context_parts.append(f"\n--- {ref_name} ---\n{ref_content}")

        # Add instructions for the LLM about the expected output
        output_schema = _build_output_schema_from_skill_outputs(skill.outputs)

        # Build the prompt
        prompt_parts = [
            "You are an AI assistant tasked with executing a skill.",
            "Use the provided skill context to generate the expected output.",
            "\nSkill Context:",
            "\n".join(context_parts),
            "\n\nInputs:",
            json.dumps(inputs, indent=2),
            "\n\nPlease generate the output according to the skill's output specification."
        ]

        prompt = "\n".join(prompt_parts)
        logger.debug(f"Generated prompt for skill {skill_identifier}: {prompt[:200]}...")

        # Call the LLM with structured output, with fallback to text generation
        try:
            result = self.llm_client.generate_structured_output(
                prompt=prompt,
                output_schema=output_schema,
                **kwargs
            )
            logger.info(f"Successfully executed skill {skill_identifier} in batch mode")
            return result
        except Exception as e:
            logger.warning(f"Structured output failed for skill {skill_identifier}, falling back to text generation: {e}")
            try:
                text_result = self.llm_client.generate_text(prompt, **kwargs)
                # Try to parse the text as JSON
                try:
                    result = json.loads(text_result)
                    logger.info(f"Successfully executed skill {skill_identifier} in batch mode via text fallback")
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse LLM text output as JSON for skill {skill_identifier}")
                    raise ValueError(f"LLM text output is not valid JSON: {text_result}")
            except Exception as e2:
                logger.error(f"Both structured and text generation failed for skill {skill_identifier}: {e2}")
                raise RuntimeError(f"LLM call failed during batch skill execution: {e2}") from e


class StepWiseSkillExecutor:
    def __init__(self, llm_client: LLMClient, skill_loader: SkillLoader):
        self.llm_client = llm_client
        self.skill_loader = skill_loader
        logger.debug("StepWiseSkillExecutor initialized")

    def execute(
        self,
        skill_identifier: str,
        inputs: Dict[str, Any],
        **kwargs
    ) -> List[Any]:
        """
        Execute a skill in step-wise mode: break the skill into steps and call the LLM for each step.
        """
        logger.info(f"Executing skill {skill_identifier} in step-wise mode")
        skill = self.skill_loader.get_skill(skill_identifier)
        if not skill:
            raise ValueError(f"Skill not found: {skill_identifier}")

        base_path = self.skill_loader.get_skill_base_path(skill_identifier)
        if base_path is None:
            raise ValueError(f"Could not determine base path for skill: {skill_identifier}")

        if not skill.steps:
            logger.warning(f"Skill {skill_identifier} has no steps, falling back to batch execution")
            batch_executor = BatchSkillExecutor(self.llm_client, self.skill_loader)
            return [batch_executor.execute(skill_identifier, inputs, **kwargs)]

        # Load reference contents once for all steps
        try:
            reference_contents = skill.get_reference_content(base_path)
        except FileNotFoundError as e:
            logger.error(f"Failed to load skill references: {e}")
            raise ValueError(f"Failed to load skill references: {e}")

        step_results = []
        step_context = inputs.copy()  # We'll accumulate context from previous steps

        for i, step in enumerate(skill.steps):
            logger.debug(f"Executing step {i+1}/{len(skill.steps)}: {step.name}")
            # Build the prompt for this step
            context_parts = [
                f"Skill Name: {skill.name}",
                f"Skill Description: {skill.description}",
                f"Step {i+1} of {len(skill.steps)}: {step.name}",
                f"Step Description: {step.description}",
            ]
            if step.instructions:
                context_parts.append(f"Step Instructions:\n{step.instructions}")

            # Add the skill content and references
            context_parts.append(f"\nSkill Content:\n{skill.content}")
            if reference_contents:
                context_parts.append("\nReferences:")
                for ref_name, ref_content in reference_contents.items():
                    context_parts.append(f"\n--- {ref_name} ---\n{ref_content}")

            context_parts.append("\nAccumulated Context from Previous Steps:")
            context_parts.append(json.dumps(step_context, indent=2))

            # Build output schema for this step
            output_schema = _build_output_schema_from_step(step, skill.outputs)

            # Add the current step's expected output to the prompt
            context_parts.append("\nPlease generate the output for this step.")

            prompt = "\n".join(context_parts)
            logger.debug(f"Generated prompt for step {i+1}: {prompt[:200]}...")

            try:
                step_result = self.llm_client.generate_structured_output(
                    prompt=prompt,
                    output_schema=output_schema,
                    **kwargs
                )
                logger.debug(f"Step {i+1} result: {step_result}")
            except Exception as e:
                logger.warning(f"Structured output failed for step {i+1}, falling back to text generation: {e}")
                try:
                    text_result = self.llm_client.generate_text(prompt, **kwargs)
                    # Try to parse the text as JSON
                    try:
                        step_result = json.loads(text_result)
                        logger.debug(f"Step {i+1} result via text fallback: {step_result}")
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse LLM text output as JSON for step {i+1}")
                        raise ValueError(f"LLM text output is not valid JSON: {text_result}")
                except Exception as e2:
                    logger.error(f"Both structured and text generation failed for step {i+1}: {e2}")
                    raise RuntimeError(f"LLM call failed during step {i+1} execution: {e2}") from e

            step_results.append(step_result)
            # Update the step_context with the result of this step for the next step
            step_context.update(step_result)

        logger.info(f"Successfully executed skill {skill_identifier} in step-wise mode with {len(step_results)} steps")
        return step_results
