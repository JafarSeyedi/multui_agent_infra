# engines/document/parsers/msdm_parsers/influxdb_schema_parser.py
"""
InfluxDB Schema Parser – converts .influxql or .flux schema files into an MSDMDocument.

Handles:
- InfluxDB 1.x / 2.x DDL: CREATE DATABASE/BUCKET, CREATE RETENTION POLICY, ALTER RETENTION POLICY,
  DROP DATABASE, etc. (stored as document‑level annotations for round‑trip).
- Custom measurement definition syntax for documenting time‑series schemas:
    CREATE MEASUREMENT <name> (
      FIELD <field_name> <field_type> [DEFAULT <value>],
      TAG <tag_name>,
      ...
    ) [WITH (retention_policy=<name>, ...)]
- InfluxQL continuous queries are preserved as annotations.
- Implicit measurement schemas derived from INSERT‐like samples (not yet supported).

All time‑series semantics (timestamp, tag, field) are mapped to MSDM Entity (kind=TIMESERIES)
and Attribute fields (is_tag, is_field, annotations for retention policy, etc.) for
lossless round‑trip.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from .base_msdm_parser import BaseMSDMParser
from ..base import ParseOptions
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    Constraint,
    ConstraintType,
    Index,
    Annotation,
    EntityKind,
    ScalarType,
)

# ── Regular Expressions ────────────────────────────────────────────
# Match CREATE DATABASE/BUCKET (InfluxDB 1.x / 2.x)
RE_CREATE_DATABASE = re.compile(
    r"CREATE\s+(?:DATABASE|BUCKET)\s+(\"?\w+\"?)\s*(?:WITH\s+(.+))?",
    re.IGNORECASE | re.DOTALL,
)

# Match CREATE RETENTION POLICY
RE_CREATE_RETENTION = re.compile(
    r"CREATE\s+RETENTION\s+POLICY\s+(\"?\w+\"?)\s+ON\s+(\w+)\s+DURATION\s+(\w+)\s+REPLICATION\s+(\d+)\s*(?:SHARD\s+DURATION\s+(\w+))?\s*(?:DEFAULT)?",
    re.IGNORECASE,
)

# Match custom measurement definition: CREATE MEASUREMENT name ( ... )
RE_CREATE_MEASUREMENT = re.compile(
    r"CREATE\s+MEASUREMENT\s+(\"?\w+\"?)\s*\(\s*(.*?)\s*\)\s*(?:WITH\s+(.+))?",
    re.IGNORECASE | re.DOTALL,
)

# Match field definition inside measurement: FIELD name type [DEFAULT value]
RE_FIELD_DEF = re.compile(
    r"FIELD\s+(\w+)\s+(\w+)\s*(?:DEFAULT\s+(.+?))?(?:,|$)",
    re.IGNORECASE,
)

# Match tag definition: TAG name
RE_TAG_DEF = re.compile(
    r"TAG\s+(\w+)\s*",
    re.IGNORECASE,
)

# Tokenize WITH options
RE_OPTION = re.compile(
    r"(\w+)\s*=\s*('[^']*'|\"[^\"]*\"|\S+)",
    re.IGNORECASE,
)


class InfluxDBSchemaParser(BaseMSDMParser):
    """Parser for InfluxDB schema files (.influxql, .flux)."""
    name = "influxdb_schema"
    supported_extensions = (".influxql", ".flux")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem

        # Remove comments (# and //)
        text = self._strip_comments(text)

        # Split into statements
        statements = self._split_statements(text)

        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            self._process_statement(stmt, doc)

        # If no entities were created, create a default one from annotations?
        if not doc.entities:
            # Create a placeholder entity to hold at least the database name
            db_name = next((a.value for a in doc.annotations if a.key == "database"), "unknown")
            entity = Entity(name=db_name, kind=EntityKind.TIMESERIES)
            doc.entities.append(entity)

        return doc

    # ── Comment stripping and statement splitting ──────────────────
    def _strip_comments(self, text: str) -> str:
        # Remove line comments starting with # or //
        text = re.sub(r"#.*", "", text)
        text = re.sub(r"//.*", "", text)
        return text

    def _split_statements(self, text: str) -> List[str]:
        """Split by semicolons that are not inside parentheses."""
        statements = []
        current = ""
        depth = 0
        for ch in text:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch == ';' and depth == 0:
                statements.append(current)
                current = ""
                continue
            current += ch
        if current.strip():
            statements.append(current)
        return statements

    def _process_statement(self, stmt: str, doc: MSDMDocument) -> None:
        upper = stmt.upper().strip()

        # CREATE DATABASE / BUCKET
        if upper.startswith("CREATE DATABASE") or upper.startswith("CREATE BUCKET"):
            m = RE_CREATE_DATABASE.match(stmt)
            if m:
                db_name = self._unquote(m.group(1))
                doc.annotations.append(Annotation(key="database", value=db_name))
                if m.group(2):
                    for key, val in self._parse_options(m.group(2)):
                        doc.annotations.append(Annotation(key=key, value=val))

        # CREATE RETENTION POLICY
        elif upper.startswith("CREATE RETENTION POLICY"):
            m = RE_CREATE_RETENTION.match(stmt)
            if m:
                policy_name = self._unquote(m.group(1))
                database = m.group(2)
                duration = m.group(3)
                replication = m.group(4)
                shard_duration = m.group(5) or None
                # Store as annotations on document
                doc.annotations.append(Annotation(key=f"retention_policy_{policy_name}_database", value=database))
                doc.annotations.append(Annotation(key=f"retention_policy_{policy_name}_duration", value=duration))
                doc.annotations.append(Annotation(key=f"retention_policy_{policy_name}_replication", value=replication))
                if shard_duration:
                    doc.annotations.append(Annotation(key=f"retention_policy_{policy_name}_shard_duration", value=shard_duration))
                if "DEFAULT" in stmt.upper():
                    doc.annotations.append(Annotation(key="default_retention_policy", value=policy_name))

        # CREATE MEASUREMENT (custom format)
        elif upper.startswith("CREATE MEASUREMENT"):
            self._parse_create_measurement(stmt, doc)

        # ALTER RETENTION POLICY, DROP DATABASE, etc. – store as raw annotations for round‑trip
        elif upper.startswith("ALTER") or upper.startswith("DROP"):
            doc.annotations.append(Annotation(key="raw_statement", value=stmt))

        # Continuous queries
        elif upper.startswith("CREATE CONTINUOUS QUERY"):
            doc.annotations.append(Annotation(key="continuous_query", value=stmt))

        else:
            # Unknown statement – keep as annotation
            doc.annotations.append(Annotation(key="unknown_statement", value=stmt))

    def _parse_create_measurement(self, stmt: str, doc: MSDMDocument) -> None:
        """Parse a custom CREATE MEASUREMENT statement and produce a TIMESERIES entity."""
        m = RE_CREATE_MEASUREMENT.match(stmt)
        if not m:
            return
        name = self._unquote(m.group(1))
        body = m.group(2).strip()
        with_options = m.group(3)

        entity = Entity(
            name=name,
            kind=EntityKind.TIMESERIES,
        )

        # Always add a timestamp attribute (implicit in InfluxDB)
        timestamp_attr = Attribute(
            name="time",
            data_type=DataType(base=ScalarType.TIMESTAMP),
            required=True,
            primary_key=True,
            is_field=False,
            is_tag=False,
        )
        timestamp_attr.annotations.append(Annotation(key="influxdb_implicit", value="true"))
        entity.attributes.append(timestamp_attr)

        # Parse field and tag definitions
        # body is something like: FIELD value float DEFAULT 0.0, TAG host, TAG region, FIELD temp int
        self._parse_measurement_fields(body, entity)

        # WITH options (retention policy, etc.)
        if with_options:
            for key, val in self._parse_options(with_options):
                entity.annotations.append(Annotation(key=key.lower(), value=val))

        doc.entities.append(entity)

    def _parse_measurement_fields(self, body: str, entity: Entity) -> None:
        """Extract FIELD and TAG definitions from the measurement body."""
        # Split by commas, but watch for parentheses in defaults
        parts = self._split_by_comma(body)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # FIELD
            m = RE_FIELD_DEF.match(part)
            if m:
                name = m.group(1)
                field_type_str = m.group(2).lower()
                default_val = m.group(3)
                dt = self._map_influx_type(field_type_str)
                attr = Attribute(
                    name=name,
                    data_type=dt,
                    is_field=True,
                    required=False,  # fields are not required unless specified
                )
                if default_val:
                    attr.default_value = default_val.strip()
                    attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=attr.default_value))
                entity.attributes.append(attr)
                continue

            # TAG
            m = RE_TAG_DEF.match(part)
            if m:
                name = m.group(1)
                attr = Attribute(
                    name=name,
                    data_type=DataType(base=ScalarType.STRING),
                    is_tag=True,
                    required=False,
                )
                entity.attributes.append(attr)

    def _map_influx_type(self, type_str: str) -> DataType:
        """Map InfluxDB field type name to MSDM DataType."""
        mapping = {
            "float": ScalarType.FLOAT,
            "double": ScalarType.DOUBLE,
            "integer": ScalarType.INT,
            "int": ScalarType.INT,
            "long": ScalarType.LONG,
            "string": ScalarType.STRING,
            "boolean": ScalarType.BOOLEAN,
            "bool": ScalarType.BOOLEAN,
            "text": ScalarType.STRING,
            "duration": ScalarType.DURATION,
            "timestamp": ScalarType.TIMESTAMP,
            "date": ScalarType.DATE,
        }
        base = mapping.get(type_str, ScalarType.ANY)
        return DataType(base=base)

    # ── Utility ─────────────────────────────────────────────────────
    @staticmethod
    def _unquote(s: str) -> str:
        s = s.strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        return s

    @staticmethod
    def _split_by_comma(text: str) -> List[str]:
        """Split by commas, ignoring those inside parentheses."""
        parts = []
        depth = 0
        current = ""
        for ch in text:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch == ',' and depth == 0:
                parts.append(current)
                current = ""
                continue
            current += ch
        if current.strip():
            parts.append(current)
        return parts

    @staticmethod
    def _parse_options(options_str: str) -> List[Tuple[str, str]]:
        """Parse key=value pairs from a WITH clause."""
        pairs = []
        for m in RE_OPTION.finditer(options_str):
            key = m.group(1)
            value = m.group(2).strip("'\"")
            pairs.append((key, value))
        return pairs