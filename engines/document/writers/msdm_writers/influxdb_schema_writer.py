# engines/document/writers/msdm_writers/influxdb_schema_writer.py
"""
InfluxDB Schema Writer – converts an MSDMDocument into InfluxQL DDL statements
(.influxql).  Handles CREATE DATABASE, CREATE RETENTION POLICY, and a custom
CREATE MEASUREMENT syntax for time‑series entities.  Raw statements (e.g.,
CONTINUOUS QUERY) preserved from the parser are written verbatim for round‑trip.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy
from engines.document.writers.base import WriteOptions
from engines.document.models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    ScalarType,
    Annotation,
    EntityKind,
)


class InfluxDBSchemaWriter(BaseMSDMWriter):
    """Writer for InfluxDB schema files (.influxql)."""
    name = "influxdb_schema"
    supported_extensions = (".influxql",)

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        lines = []
        # Extract global database / retention settings
        db_name = self._get_doc_annotation(document, "database")
        if db_name:
            lines.append(f"CREATE DATABASE {self._quote(db_name)}")
            lines.append("")

        # Retention policies
        policies = self._collect_retention_policies(document)
        for rp_name, (database, duration, replication, shard_duration, is_default) in policies.items():
            stmt = f"CREATE RETENTION POLICY {self._quote(rp_name)} ON {self._quote(database)} DURATION {duration} REPLICATION {replication}"
            if shard_duration:
                stmt += f" SHARD DURATION {shard_duration}"
            if is_default:
                stmt += " DEFAULT"
            lines.append(stmt)
            lines.append("")

        # Measurements (time‑series entities)
        for entity in document.entities:
            if entity.kind == EntityKind.TIMESERIES:
                lines.append(self._write_measurement(entity))
                lines.append("")

        # Raw statements (continuous queries, unknown DDL)
        for ann in document.annotations:
            if ann.key in ("raw_statement", "continuous_query", "unknown_statement"):
                lines.append(ann.value)
                lines.append("")

        # Join statements with semicolons
        script = ";\n".join(line for line in lines if line) + ";\n"
        return script.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── CREATE MEASUREMENT ─────────────────────────────────────────
    def _write_measurement(self, entity: Entity) -> str:
        """
        Build a custom CREATE MEASUREMENT statement.
        Example:
            CREATE MEASUREMENT "cpu" (
                FIELD "value" float,
                FIELD "temp" int DEFAULT 25,
                TAG "host",
                TAG "region"
            ) WITH (retention_policy='autogen')
        """
        name = self._quote(entity.name)
        # Collect fields and tags
        fields: List[str] = []
        tags: List[str] = []

        # The timestamp attribute is implicit; we'll skip it if it's marked with annotation "influxdb_implicit"
        for attr in entity.attributes:
            if self._is_implicit_timestamp(attr):
                continue
            if attr.is_field:
                type_str = self._scalar_to_influx_type(attr.data_type)
                default = attr.default_value
                field_def = f'FIELD {self._quote(attr.name)} {type_str}'
                if default is not None:
                    field_def += f" DEFAULT {self._format_default(default, attr.data_type)}"
                fields.append(field_def)
            elif attr.is_tag:
                tags.append(f'TAG {self._quote(attr.name)}')
            else:
                # If neither, treat as field by default
                type_str = self._scalar_to_influx_type(attr.data_type)
                fields.append(f'FIELD {self._quote(attr.name)} {type_str}')

        # Build the body
        body_parts = fields + tags
        if not body_parts:
            body_parts = ["-- no fields or tags"]

        body = ",\n    ".join(body_parts)
        stmt = f"CREATE MEASUREMENT {name} (\n    {body}\n)"

        # WITH options (retention policy, etc.)
        with_options = self._build_measurement_options(entity)
        if with_options:
            stmt += f" WITH ({with_options})"

        return stmt

    # ── Helpers ─────────────────────────────────────────────────────
    def _is_implicit_timestamp(self, attr: Attribute) -> bool:
        """Check if the attribute is the implicit InfluxDB 'time' field."""
        return attr.name == "time" and any(
            a.key == "influxdb_implicit" and a.value == "true" for a in attr.annotations
        )

    @staticmethod
    def _scalar_to_influx_type(dt: DataType) -> str:
        """Map MSDM DataType to InfluxDB field type name."""
        mapping = {
            ScalarType.FLOAT: "float",
            ScalarType.DOUBLE: "float",
            ScalarType.INT: "integer",
            ScalarType.LONG: "integer",
            ScalarType.STRING: "string",
            ScalarType.BOOLEAN: "boolean",
            ScalarType.DATE: "dateTime",
            ScalarType.TIME: "dateTime",
            ScalarType.TIMESTAMP: "dateTime",
            ScalarType.DURATION: "duration",
            ScalarType.BINARY: "string",   # fallback
            ScalarType.DECIMAL: "float",
            ScalarType.UUID: "string",
            ScalarType.ANY: "string",
        }
        return mapping.get(dt.base, "string")

    def _build_measurement_options(self, entity: Entity) -> str:
        """Extract WITH options from entity annotations (e.g., retention_policy)."""
        opts = []
        for ann in entity.annotations:
            if ann.key == "retention_policy":
                opts.append(f"{ann.key} = {self._quote_value(ann.value)}")
            elif ann.key in ("shard_duration", "replication"):
                opts.append(f"{ann.key} = {ann.value}")
        return ", ".join(opts)

    # ── Global options extraction ──────────────────────────────────
    def _get_doc_annotation(self, doc: MSDMDocument, key: str) -> Optional[str]:
        return next((a.value for a in doc.annotations if a.key == key), None)

    def _collect_retention_policies(self, doc: MSDMDocument) -> Dict[str, Tuple[str, str, str, Optional[str], bool]]:
        """
        Parse retention policy annotations and return a dict:
        policy_name → (database, duration, replication, shard_duration, is_default)
        """
        policies: Dict[str, Dict[str, str]] = {}
        for ann in doc.annotations:
            if ann.key.startswith("retention_policy_"):
                # e.g., retention_policy_myrp_duration → myrp, duration
                parts = ann.key.split("_", 2)   # "retention", "policy", "name_field"
                if len(parts) < 4:
                    continue
                rp_name = parts[2].rsplit("_", 1)[0]  # crude
                # Better: pattern: retention_policy_{name}_{field}
                # We'll extract more robustly:
                prefix = "retention_policy_"
                suffix = ann.key[len(prefix):]
                # Find the last underscore to split field
                for sep in ("_database", "_duration", "_replication", "_shard_duration"):
                    if suffix.endswith(sep):
                        rp_name = suffix[: -len(sep)]
                        field = sep.lstrip("_")
                        policies.setdefault(rp_name, {})[field] = ann.value
                        break

        result = {}
        default_rp = self._get_doc_annotation(doc, "default_retention_policy")
        for rp_name, fields in policies.items():
            database = fields.get("database", "")
            duration = fields.get("duration", "0s")
            replication = fields.get("replication", "1")
            shard = fields.get("shard_duration", None)
            is_default = rp_name == default_rp
            result[rp_name] = (database, duration, replication, shard, is_default)
        return result

    # ── Output formatting ──────────────────────────────────────────
    @staticmethod
    def _quote(name: str) -> str:
        """Double‑quote an identifier."""
        escaped = name.replace('"', '\\"')
        return f'"{escaped}"'

    @staticmethod
    def _quote_value(val: str) -> str:
        """Quote a string value if it's not a number."""
        val = val.strip()
        if val.isdigit() or (val.replace('.', '', 1).isdigit() and val.count('.') < 2):
            return val
        return f"'{val}'"

    def _format_default(self, default_str: str, dt: DataType) -> str:
        """Format a default value for a measurement field."""
        if dt.base == ScalarType.STRING:
            return f"'{default_str}'"
        return default_str