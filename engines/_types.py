"""Shared type aliases for the engines layer.

These aliases document the semantic intent of generic types used across
engine packages. They are intentionally broad — the real type narrowing
happens at usage sites (TypedDicts, Protocols, union types introduced
in per-file fixes).
"""

from __future__ import annotations

from typing import Any, TypeAlias


# A value stored as a process variable (context, instance, etc.).
# Intentionally broad — variables can hold any Python object.
VariableValue: TypeAlias = Any

# Variable name -> value mapping used as the evaluation scope for
# FEEL expressions, gateway conditions, and DMN decision tables.
FeelContext: TypeAlias = dict[str, Any]

# A value produced or consumed by DMN evaluation (hit-policy result,
# decision-table output, expression result, etc.).
DmnValue: TypeAlias = Any

# Payload for agent-to-agent communication (Mediator, bus events, etc.).
MessagePayload: TypeAlias = dict[str, Any]

# Arbitrary key-value metadata attached to contexts, instances, etc.
Metadata: TypeAlias = dict[str, Any]

# Raw parsed definition data (BPMN / DMN / CMMN / OSDM JSON/XML).
RawData: TypeAlias = dict[str, Any]
