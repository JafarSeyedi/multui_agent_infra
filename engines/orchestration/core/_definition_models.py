"""Shared definition model classes extracted from engine.py.

Breaks the circular dependency between engine.py and engine_services.py
by providing Deployment and ProcessDefinition as a shared module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ProcessDefinition:
    id: str
    key: str
    name: str
    version: int
    deployment_id: str
    resource_name: str
    diagram_resource_name: str | None
    has_start_form_key: bool
    has_graphical_notation: bool
    is_suspended: bool
    tenant_id: str | None
    version_tag: str | None
    history_time_to_live: int | None
    is_startable_in_tasklist: bool
    definition_type: str
    definition_xml: str
    deployed_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Deployment:
    id: str
    name: str
    deployment_time: datetime
    source: str
    tenant_id: str | None
    definitions: list[ProcessDefinition] = field(default_factory=list)
