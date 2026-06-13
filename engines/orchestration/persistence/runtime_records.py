"""Model-driven runtime record schemas and DSDM serialization helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from collections.abc import Mapping
from uuid import uuid4

from ...document.models.dsdm_models import DataDocument, DataSchemaReference
from ...document.models.media_types import MEDIA_TYPES
from ...document.models.msdm_models import (
    Annotation,
    Attribute,
    DataType,
    Entity,
    EntityKind,
    MSDMDocument,
    ScalarType,
)
from ...document.parsers.dsdm_parsers.dsdm_utils import build_node_from_python, node_to_python
from ...document.writers.dsdm_writers.json_writer import JSONWriter


STATE_SNAPSHOT_RECORD = "state_snapshot"
INSTANCE_RECORD = "instance"
TOKEN_RECORD = "token"
VARIABLE_RECORD = "variable"
EVENT_RECORD = "event"
AUDIT_RECORD = "audit"
TIMER_RECORD = "timer"
JOB_RECORD = "job"


def _runtime_entity(name: str, attributes: list[Attribute]) -> Entity:
    return Entity(
        name=name,
        kind=EntityKind.TIMESERIES,
        description=f"Runtime record entity for {name}.",
        attributes=attributes,
    )


def _attr(name: str, scalar_type: ScalarType, *, required: bool = False) -> Attribute:
    return Attribute(name=name, data_type=DataType(base=scalar_type), required=required)


def build_runtime_schema() -> MSDMDocument:
    """Return the shared MSDM schema for orchestration runtime records."""
    entities = [
        _runtime_entity(
            "RuntimeStateSnapshot",
            [
                _attr("record_id", ScalarType.UUID, required=True),
                _attr("record_type", ScalarType.STRING, required=True),
                _attr("instance_id", ScalarType.STRING, required=True),
                _attr("state", ScalarType.STRING, required=True),
                _attr("created_at", ScalarType.DATETIME, required=True),
                _attr("updated_at", ScalarType.DATETIME, required=True),
                _attr("data", ScalarType.JSON),
            ],
        ),
        _runtime_entity(
            "RuntimeInstanceRecord",
            [
                _attr("record_id", ScalarType.UUID, required=True),
                _attr("record_type", ScalarType.STRING, required=True),
                _attr("instance_id", ScalarType.STRING, required=True),
                _attr("definition_id", ScalarType.STRING),
                _attr("definition_key", ScalarType.STRING),
                _attr("instance_type", ScalarType.STRING),
                _attr("state", ScalarType.STRING),
                _attr("business_key", ScalarType.STRING),
                _attr("payload", ScalarType.JSON),
                _attr("created_at", ScalarType.DATETIME, required=True),
                _attr("updated_at", ScalarType.DATETIME, required=True),
            ],
        ),
        _runtime_entity(
            "RuntimeTokenRecord",
            [
                _attr("record_id", ScalarType.UUID, required=True),
                _attr("record_type", ScalarType.STRING, required=True),
                _attr("instance_id", ScalarType.STRING, required=True),
                _attr("token_id", ScalarType.STRING, required=True),
                _attr("token_type", ScalarType.STRING),
                _attr("state", ScalarType.STRING),
                _attr("current_element_id", ScalarType.STRING),
                _attr("payload", ScalarType.JSON),
                _attr("created_at", ScalarType.DATETIME, required=True),
                _attr("updated_at", ScalarType.DATETIME, required=True),
            ],
        ),
        _runtime_entity(
            "RuntimeVariableRecord",
            [
                _attr("record_id", ScalarType.UUID, required=True),
                _attr("record_type", ScalarType.STRING, required=True),
                _attr("instance_id", ScalarType.STRING, required=True),
                _attr("scope_id", ScalarType.STRING),
                _attr("name", ScalarType.STRING, required=True),
                _attr("value", ScalarType.JSON),
                _attr("value_type", ScalarType.STRING),
                _attr("updated_at", ScalarType.DATETIME, required=True),
            ],
        ),
        _runtime_entity(
            "RuntimeEventRecord",
            [
                _attr("record_id", ScalarType.UUID, required=True),
                _attr("record_type", ScalarType.STRING, required=True),
                _attr("instance_id", ScalarType.STRING),
                _attr("event_type", ScalarType.STRING, required=True),
                _attr("correlation_id", ScalarType.STRING),
                _attr("payload", ScalarType.JSON),
                _attr("created_at", ScalarType.DATETIME, required=True),
            ],
        ),
        _runtime_entity(
            "RuntimeAuditRecord",
            [
                _attr("record_id", ScalarType.UUID, required=True),
                _attr("record_type", ScalarType.STRING, required=True),
                _attr("instance_id", ScalarType.STRING),
                _attr("activity_id", ScalarType.STRING),
                _attr("action", ScalarType.STRING, required=True),
                _attr("payload", ScalarType.JSON),
                _attr("created_at", ScalarType.DATETIME, required=True),
            ],
        ),
        _runtime_entity(
            "RuntimeTimerRecord",
            [
                _attr("record_id", ScalarType.UUID, required=True),
                _attr("record_type", ScalarType.STRING, required=True),
                _attr("instance_id", ScalarType.STRING),
                _attr("timer_id", ScalarType.STRING, required=True),
                _attr("name", ScalarType.STRING),
                _attr("deadline", ScalarType.DATETIME),
                _attr("state", ScalarType.STRING),
                _attr("payload", ScalarType.JSON),
                _attr("updated_at", ScalarType.DATETIME, required=True),
            ],
        ),
        _runtime_entity(
            "RuntimeJobRecord",
            [
                _attr("record_id", ScalarType.UUID, required=True),
                _attr("record_type", ScalarType.STRING, required=True),
                _attr("instance_id", ScalarType.STRING),
                _attr("job_id", ScalarType.STRING, required=True),
                _attr("job_type", ScalarType.STRING),
                _attr("state", ScalarType.STRING),
                _attr("payload", ScalarType.JSON),
                _attr("updated_at", ScalarType.DATETIME, required=True),
            ],
        ),
    ]
    return MSDMDocument(
        title="Orchestration Runtime Schema",
        document_id="orchestration-runtime-schema",
        media_type=MEDIA_TYPES["json_schema"],
        schema_name="orchestration.runtime",
        entities=entities,
        annotations=[
            Annotation(
                key="purpose",
                value="Canonical runtime schemas for orchestration state, events, variables, timers, jobs, and audits.",
            )
        ],
    )


RUNTIME_SCHEMA = build_runtime_schema()
RUNTIME_ENTITY_BY_RECORD_TYPE: dict[str, str] = {
    STATE_SNAPSHOT_RECORD: "RuntimeStateSnapshot",
    INSTANCE_RECORD: "RuntimeInstanceRecord",
    TOKEN_RECORD: "RuntimeTokenRecord",
    VARIABLE_RECORD: "RuntimeVariableRecord",
    EVENT_RECORD: "RuntimeEventRecord",
    AUDIT_RECORD: "RuntimeAuditRecord",
    TIMER_RECORD: "RuntimeTimerRecord",
    JOB_RECORD: "RuntimeJobRecord",
}


@dataclass(frozen=True)
class RuntimeRecordEnvelope:
    record_type: str
    payload: dict[str, Any]


async def serialize_runtime_record(record_type: str, payload: Mapping[str, Any]) -> str:
    """Serialize a runtime payload to JSON through a DSDM `DataDocument`."""
    document = build_runtime_data_document(record_type, payload)
    raw = await JSONWriter().write(document)
    return raw.decode("utf-8")


def deserialize_runtime_record(raw: str | bytes | Mapping[str, Any]) -> RuntimeRecordEnvelope:
    """Deserialize stored JSON payload back into a runtime record envelope."""
    if isinstance(raw, Mapping):
        payload = dict(raw)
    else:
        text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
        payload = json.loads(text)

    record_type = str(payload.get("record_type", STATE_SNAPSHOT_RECORD))
    document = build_runtime_data_document(record_type, payload)
    python_payload = data_document_to_python(document)
    return RuntimeRecordEnvelope(record_type=record_type, payload=python_payload)


def build_runtime_data_document(
    record_type: str,
    payload: Mapping[str, Any],
    *,
    document_id: str | None = None,
) -> DataDocument:
    """Create a DSDM `DataDocument` for a runtime payload."""
    normalized = normalize_runtime_payload(record_type, payload)
    root = build_node_from_python(normalized, path="$", name="runtime_record")
    entity = resolve_runtime_entity(record_type)
    root.schema_binding = None
    return DataDocument(
        title=f"{record_type} runtime record",
        document_id=document_id or str(normalized.get("record_id", uuid4().hex)),
        media_type=MEDIA_TYPES["json"],
        root=root,
        schema_ref=DataSchemaReference(
            name=entity.name,
            data_struct=RUNTIME_SCHEMA,
            version="1.0",
        ),
        metadata={"record_type": record_type, "schema_name": RUNTIME_SCHEMA.schema_name},
    )


def data_document_to_python(document: DataDocument) -> dict[str, Any]:
    value = node_to_python(document.root)
    if isinstance(value, dict):
        return value
    return {"value": value}


def resolve_runtime_entity(record_type: str) -> Entity:
    entity_name = RUNTIME_ENTITY_BY_RECORD_TYPE.get(record_type, "RuntimeEventRecord")
    for entity in RUNTIME_SCHEMA.entities:
        if entity.name == entity_name:
            return entity
    raise ValueError(f"Runtime entity not found for record type '{record_type}'")


def normalize_runtime_payload(record_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    now = utc_isoformat()
    normalized = dict(payload)
    normalized.setdefault("record_id", str(uuid4()))
    normalized.setdefault("record_type", record_type)
    normalized.setdefault("created_at", now)
    normalized.setdefault("updated_at", normalized.get("created_at", now))
    return normalized


def snapshot_payload(instance_id: str, state: str, created_at: datetime, updated_at: datetime, data: Mapping[str, Any]) -> dict[str, Any]:
    return normalize_runtime_payload(
        STATE_SNAPSHOT_RECORD,
        {
            "instance_id": instance_id,
            "state": state,
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
            "data": dict(data),
        },
    )


def utc_isoformat() -> str:
    return datetime.utcnow().isoformat()
