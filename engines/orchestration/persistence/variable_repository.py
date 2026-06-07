"""Variable value repository with MSDM schema validation."""

from __future__ import annotations

from typing import Any

from ...document.models.dsdm_models import DataDocument, DataSchemaReference, SchemaBinding
from ...document.models.msdm_models import Entity
from .runtime_records import VARIABLE_RECORD
from .repository import PersistentRuntimeRepository


class VariableRepository(PersistentRuntimeRepository):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            record_type=VARIABLE_RECORD,
            key_prefix="orchestration:variables:",
            measurement="orchestration_variables",
            **kwargs,
        )

    def get_by_instance(self, instance_id: str) -> list[dict[str, str | int | float | bool | None]]:
        return self.list(predicate=lambda row: row.get("instance_id") == instance_id)  # type: ignore[return-value]

    def get_by_scope(self, instance_id: str, scope_id: str) -> list[dict[str, Any]]:
        return self.list(
            predicate=lambda row: row.get("instance_id") == instance_id and row.get("scope_id") == scope_id
        )

    def _extract_schema_binding(self, payload: dict[str, Any]) -> SchemaBinding | None:
        """Extract MSDM schema binding from variable payload."""
        # Check if schema binding is stored in the payload's metadata
        metadata = payload.get("payload", {})
        schema_binding_data = metadata.get("schema_binding")
        
        if not schema_binding_data or not isinstance(schema_binding_data, dict):
            return None
            
        # Reconstruct SchemaBinding from stored data
        entity_data = schema_binding_data.get("entity")
        attribute_data = schema_binding_data.get("attribute")
        source_schema_data = schema_binding_data.get("source_schema")
        
        entity = None
        if entity_data and isinstance(entity_data, dict):
            entity = Entity(
                name=str(entity_data.get("name", "unknown")),
                # Note: In a full implementation, we would reconstruct the full Entity
                # For now, we'll create a minimal entity for validation purposes
            )
            
        attribute = None
        if attribute_data and isinstance(attribute_data, dict):
            # Similar to entity, we'd reconstruct the full Attribute
            pass
            
        source_schema = None
        if source_schema_data and isinstance(source_schema_data, dict):
            # We'd reconstruct the full MSDMDocument
            pass
            
        return SchemaBinding(
            entity=entity,
            attribute=attribute,
            source_schema=source_schema
        )

    def _validate_against_msdm_schema(self, payload: dict[str, Any]) -> list[str]:
        """Validate variable payload against MSDM schema if binding exists."""
        schema_binding = self._extract_schema_binding(payload)
        if not schema_binding or not schema_binding.entity:
            return []  # No schema binding, no validation needed
            
        # Create a simple DataDocument for validation
        # In a full implementation, we would use the actual schema binding
        # For now, we'll do basic type validation based on the variable's value_type
        errors = []
        
        value = payload.get("value")
        value_type = payload.get("value_type", "object")
        
        # Basic type validation
        if value is not None:
            type_map = {
                "string": str,
                "integer": int,
                "double": (float, int),  # Allow int where double is expected
                "float": (float, int),
                "boolean": bool,
                "list": (list, tuple),
                "json": dict,
                "bytes": bytes,
            }
            
            expected_type = type_map.get(value_type)
            if expected_type is not None:
                et: Any = expected_type
                if isinstance(et, tuple):
                    if not any(isinstance(value, t) for t in et):
                        errors.append(f"Variable value type mismatch: expected {value_type}, got {type(value).__name__}")
                elif not isinstance(value, et):
                    errors.append(f"Variable value type mismatch: expected {value_type}, got {type(value).__name__}")
        
        return errors

    async def save_persisted(self, key: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Save variable with MSDM schema validation."""
        # Validate against MSDM schema if present
        validation_errors = self._validate_against_msdm_schema(payload)
        if validation_errors:
            raise ValueError(f"MSDM schema validation failed: {', '.join(validation_errors)}")
            
        # Proceed with normal saving
        return await super().save_persisted(key, payload)

    def save(self, key: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Save variable with MSDM schema validation."""
        # Validate against MSDM schema if present
        validation_errors = self._validate_against_msdm_schema(payload)
        if validation_errors:
            raise ValueError(f"MSDM schema validation failed: {', '.join(validation_errors)}")
            
        # Proceed with normal saving
        return super().save(key, payload)
