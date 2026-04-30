# engines/document/parsers/msdm_parsers/sql_ddl_parser.py
"""
SQL DDL Parser – parses .sql / .ddl scripts into an MSDMDocument.

Handles:
- CREATE TABLE (including IF NOT EXISTS, column definitions, constraints,
  table options for MySQL/PostgreSQL).
- ALTER TABLE (ADD COLUMN, ADD CONSTRAINT – stored as annotations for round‑trip)
- CREATE INDEX / CREATE UNIQUE INDEX (stored as Index objects)
- CREATE VIEW (stored as VIEW entity)
- Comments (inline -- and block /* */) are stripped.
- Dialect‑specific syntax (AUTO_INCREMENT, SERIAL, ENUM, etc.) is preserved
  inside annotations.

Every column is mapped to an MSDM Attribute; constraints (primary key, foreign key,
unique, check, default) become Constraint objects.  Table‑level options and
unrecognised statements are stored as document‑level annotations for lossless
round‑trip.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Set

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
    Relationship,
)

# ── SQL type → ScalarType mapping (common types) ─────────────────
SQL_TYPE_TO_SCALAR = {
    "char": ScalarType.STRING,
    "varchar": ScalarType.STRING,
    "character varying": ScalarType.STRING,
    "text": ScalarType.STRING,
    "tinytext": ScalarType.STRING,
    "mediumtext": ScalarType.STRING,
    "longtext": ScalarType.STRING,
    "nchar": ScalarType.STRING,
    "nvarchar": ScalarType.STRING,
    "clob": ScalarType.STRING,
    "int": ScalarType.INT,
    "integer": ScalarType.INT,
    "smallint": ScalarType.INT,
    "bigint": ScalarType.LONG,
    "tinyint": ScalarType.INT,
    "float": ScalarType.FLOAT,
    "real": ScalarType.FLOAT,
    "double": ScalarType.DOUBLE,
    "double precision": ScalarType.DOUBLE,
    "decimal": ScalarType.DECIMAL,
    "numeric": ScalarType.DECIMAL,
    "boolean": ScalarType.BOOLEAN,
    "bool": ScalarType.BOOLEAN,
    "date": ScalarType.DATE,
    "datetime": ScalarType.TIMESTAMP,
    "timestamp": ScalarType.TIMESTAMP,
    "time": ScalarType.TIME,
    "blob": ScalarType.BINARY,
    "binary": ScalarType.BINARY,
    "varbinary": ScalarType.BINARY,
    "json": ScalarType.JSON,
    "jsonb": ScalarType.JSON,
    "xml": ScalarType.XML,
    "uuid": ScalarType.UUID,
    "bytea": ScalarType.BINARY,
    "interval": ScalarType.DURATION,
}

# ── Regex patterns (case‑insensitive) ─────────────────────────────
# Matches CREATE TABLE [IF NOT EXISTS] table_name ( ... ) [options];
RE_CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\"?[\w.]+\"?)\s*\((.*)\)\s*(.*?)?;",
    re.IGNORECASE | re.DOTALL,
)

# Column definition inside the parentheses (simplified structure)
# We'll split columns by comma, respecting parentheses for functions.
RE_COLUMN = re.compile(
    r"""\s*"?(\w+)"?\s+                        # column name
        ((?:(?:tiny|medium|long)?text|         # any type name, possibly with params
           (?:var)?binary|
           (?:var)?char(?:acter)?(?:\s+varying)?|
           (?:tiny|medium|long)?blob|
           (?:small|big)?int(?:eger)?|
           tinyint|
           float(?:\s*\(\d+,\d+\))?|
           double(?:\s+precision)?(?:\s*\(\d+,\d+\))?|
           real|
           decimal|numeric|number\s*(?:\(\d+,\d+\))?|
           boolean|bool|
           date|
           datetime|timestamp\s*(?:\(\d+\))?\s*(?:with(?:out)?\s+time\s+zone)?|
           time\s*(?:\(\d+\))?\s*(?:with(?:out)?\s+time\s+zone)?|
           interval|
           json[b]?|
           xml|
           uuid|
           bytea|
           \w+\s*                        # catch‑all for unknown types
        )\s*)
        (.*)""",
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)

# Constraint definitions (inline or table‑level)
RE_CONSTRAINT = re.compile(
    r"(?:CONSTRAINT\s+\"?(\w+)\"?\s+)?"
    r"(PRIMARY\s+KEY|UNIQUE|CHECK|FOREIGN\s+KEY)\s*"
    r"(?:\(([^)]+)\))?"
    r"(.*)",
    re.IGNORECASE | re.DOTALL,
)

# CREATE INDEX / CREATE UNIQUE INDEX
RE_CREATE_INDEX = re.compile(
    r"CREATE\s+(UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)?\s*ON\s+(\w+)\s*\(([^)]+)\)",
    re.IGNORECASE,
)

# CREATE VIEW
RE_CREATE_VIEW = re.compile(
    r"CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(\w+)\s*(?:\([^)]+\))?\s*AS\s+",
    re.IGNORECASE,
)


class SqlDDLParser(BaseMSDMParser):
    """Parser for SQL DDL scripts (.sql, .ddl)."""
    name = "sql_ddl"
    supported_extensions = (".sql", ".ddl")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem

        # Remove comments
        text = self._strip_sql_comments(text)

        # Split into statements (respecting semicolons inside quotes/parens)
        statements = self._split_statements(text)

        # Map table name → Entity for index attachment
        table_entities: Dict[str, Entity] = {}

        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            upper = stmt.upper()
            if upper.startswith("CREATE TABLE"):
                entity = self._parse_create_table(stmt, doc)
                if entity:
                    table_entities[entity.name] = entity
            elif upper.startswith("CREATE INDEX") or upper.startswith("CREATE UNIQUE INDEX"):
                self._parse_create_index(stmt, doc, table_entities)
            elif upper.startswith("CREATE VIEW"):
                self._parse_create_view(stmt, doc)
            elif upper.startswith("CREATE") or upper.startswith("ALTER") or upper.startswith("DROP"):
                # Store raw statement for round‑trip
                doc.annotations.append(Annotation(key="raw_ddl", value=stmt))
            else:
                doc.annotations.append(Annotation(key="raw_ddl", value=stmt))

        return doc

    # ── SQL comment stripping and statement splitting ────────────
    def _strip_sql_comments(self, text: str) -> str:
        # Remove block comments
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        # Remove MySQL '#' line comments and standard '--' line comments
        text = re.sub(r"#[^\n]*", "", text)
        text = re.sub(r"--[^\n]*", "", text)
        return text

    def _split_statements(self, text: str) -> List[str]:
        statements = []
        current = ""
        depth = 0
        in_string = False
        for ch in text:
            if ch == "'" and not in_string:
                in_string = True
            elif ch == "'" and in_string:
                in_string = False
            if not in_string:
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

    # ── CREATE TABLE ──────────────────────────────────────────────
    def _parse_create_table(self, stmt: str, doc: MSDMDocument) -> Optional[Entity]:
        m = RE_CREATE_TABLE.search(stmt)   # search because whole statement might have extra
        if not m:
            return None
        table_name = self._unquote(m.group(1))
        columns_body = m.group(2)
        after = m.group(3) or ""

        entity = Entity(name=table_name, kind=EntityKind.TABLE)

        # Parse columns and constraints
        col_defs = self._split_column_defs(columns_body)
        for col_def in col_defs:
            col_def = col_def.strip()
            if not col_def:
                continue
            # Try to match as a constraint first
            if re.match(r"^\s*(?:CONSTRAINT\s+|PRIMARY\s+KEY|UNIQUE|CHECK|FOREIGN\s+KEY)", col_def, re.IGNORECASE):
                self._parse_table_constraint(col_def, entity)
            else:
                # Column definition
                attr, col_constraints = self._parse_column_definition(col_def, doc)
                if attr:
                    entity.attributes.append(attr)
                    # Inline constraints already added to attr.constraints
                    # Also check if it's a primary key (inline PRIMARY KEY)
                    if col_constraints.get("primary_key"):
                        attr.primary_key = True
                        attr.constraints.append(Constraint(type=ConstraintType.PRIMARY_KEY))
                    if col_constraints.get("unique"):
                        attr.constraints.append(Constraint(type=ConstraintType.UNIQUE))
                    if col_constraints.get("not_null"):
                        attr.required = True
                        attr.constraints.append(Constraint(type=ConstraintType.NOT_NULL))

        # Parse after‑table options (e.g., ENGINE=InnoDB, TABLESPACE, etc.)
        if after:
            for opt in self._parse_table_options(after):
                entity.annotations.append(opt)

        doc.entities.append(entity)
        return entity

    def _parse_column_definition(self, col_def: str, doc: MSDMDocument) -> Tuple[Optional[Attribute], Dict[str, bool]]:
        """Parse a single column definition. Returns (Attribute, flags dict)."""
        flags = {"primary_key": False, "unique": False, "not_null": False}
        m = RE_COLUMN.match(col_def)
        if not m:
            return None, flags
        col_name = self._unquote(m.group(1))
        type_str = m.group(2).strip()
        rest = m.group(3).strip()

        # Parse data type
        dt = self._sql_type_to_datatype(type_str)

        attr = Attribute(name=col_name, data_type=dt)

        # Parse remaining column constraints: NOT NULL, DEFAULT ..., PRIMARY KEY, UNIQUE, CHECK, REFERENCES
        self._parse_inline_constraints(rest, attr, flags, doc, col_name)
        return attr, flags

    def _sql_type_to_datatype(self, type_str: str) -> DataType:
        """Convert SQL type string to DataType, including precision/scale."""
        # Lowercase and remove extra spaces
        base_type = type_str.strip().lower()
        # Remove parentheses and extract precision/scale
        precision = None
        scale = None
        m = re.match(r"(\w+(?:\s+\w+)?)\s*\((\d+)(?:\s*,\s*(\d+))?\)", base_type)
        if m:
            base_type = m.group(1).replace(" ", "")
            precision = int(m.group(2))
            if m.group(3):
                scale = int(m.group(3))
        else:
            # e.g., "character varying(255)" → "character varying"
            base_type = re.sub(r"\(.*\)", "", base_type).strip()

        # Map
        scalar = SQL_TYPE_TO_SCALAR.get(base_type, ScalarType.ANY)
        dt = DataType(base=scalar)
        if precision is not None:
            dt.precision = precision
            dt.scale = scale
        # If type has a max length (common for string types), set precision as max_length?
        if scalar == ScalarType.STRING and precision is not None:
            dt.max_length = precision
        return dt

    def _parse_inline_constraints(self, rest: str, attr: Attribute,
                                  flags: Dict[str, bool], doc: MSDMDocument, col_name: str) -> None:
        """Parse the tail of a column definition for inline constraints."""
        rest = rest.strip()
        while rest:
            rest = rest.strip()
            if rest.upper().startswith("NOT NULL"):
                flags["not_null"] = True
                rest = rest[8:].strip()
            elif rest.upper().startswith("NULL"):
                # explicit NULL, ignore
                rest = rest[4:].strip()
            elif rest.upper().startswith("PRIMARY KEY"):
                flags["primary_key"] = True
                rest = rest[11:].strip()
            elif rest.upper().startswith("UNIQUE"):
                flags["unique"] = True
                rest = rest[6:].strip()
            elif rest.upper().startswith("DEFAULT"):
                # DEFAULT value could be quoted, numeric, or expression
                rest = rest[7:].strip()
                default_val, rest = self._extract_default_value(rest)
                if default_val is not None:
                    attr.default_value = default_val
                    attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=default_val))
            elif rest.upper().startswith("CHECK"):
                rest = rest[5:].strip()
                expr, rest = self._extract_parenthesized(rest)
                if expr:
                    attr.constraints.append(Constraint(type=ConstraintType.CHECK, expression=expr))
            elif rest.upper().startswith("REFERENCES"):
                rest = rest[10:].strip()
                # REFERENCES table_name(column)
                m = re.match(r"(\w+)\s*\((\w+)\)", rest, re.IGNORECASE)
                if m:
                    ref_entity = m.group(1)
                    ref_attr = m.group(2)
                    attr.constraints.append(Constraint(
                        type=ConstraintType.FOREIGN_KEY,
                        referenced_entity=ref_entity,
                        referenced_attributes=[ref_attr],
                    ))
                    rest = rest[m.end():].strip()
                else:
                    rest = ""
            elif rest.upper().startswith("AUTO_INCREMENT") or rest.upper().startswith("SERIAL"):
                attr.annotations.append(Annotation(key="auto_increment", value="true"))
                # skip until next space/comma
                rest = rest[rest.find(' ') if ' ' in rest else len(rest):]
            else:
                # Unknown tail; store as annotation and break
                attr.annotations.append(Annotation(key="column_suffix", value=rest))
                rest = ""

    def _extract_default_value(self, text: str) -> Tuple[Optional[str], str]:
        """Extract a default value literal from the start of text, returning (value, remaining)."""
        text = text.lstrip()
        if text.startswith("'"):
            # string literal
            idx = text.index("'", 1)
            default = text[:idx+1]
            return default, text[idx+1:]
        if text.startswith('"'):
            idx = text.index('"', 1)
            default = text[:idx+1]
            return default, text[idx+1:]
        # numeric or identifier
        m = re.match(r"([\w.+\-]+)", text)
        if m:
            default = m.group(1)
            return default, text[m.end():]
        return None, text

    def _extract_parenthesized(self, text: str) -> Tuple[Optional[str], str]:
        """If text starts with '(', extract content until matching ')'. """
        if not text.startswith('('):
            return None, text
        depth = 1
        i = 1
        while i < len(text) and depth > 0:
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
            i += 1
        return text[1:i-1], text[i:]

    def _parse_table_constraint(self, constraint_str: str, entity: Entity) -> None:
        """Parse a table‑level constraint (PRIMARY KEY, UNIQUE, FOREIGN KEY, CHECK)."""
        m = RE_CONSTRAINT.match(constraint_str)
        if not m:
            entity.annotations.append(Annotation(key="raw_constraint", value=constraint_str))
            return
        constr_name = m.group(1) if m.group(1) else None
        constr_type = m.group(2).upper().replace(" ", "_")
        columns_str = m.group(3)
        extra = m.group(4).strip() if m.group(4) else ""

        if constr_type == "PRIMARY_KEY":
            cols = [c.strip('" ') for c in columns_str.split(',')]
            constraint = Constraint(type=ConstraintType.PRIMARY_KEY, expression=",".join(cols))
            if constr_name:
                constraint.name = constr_name
            entity.constraints.append(constraint)
            # Mark attributes as primary keys
            for c in cols:
                attr = next((a for a in entity.attributes if a.name == c), None)
                if attr:
                    attr.primary_key = True
                    attr.constraints.append(constraint)
        elif constr_type in ("UNIQUE", "CHECK"):
            constraint = Constraint(type=ConstraintType(constr_type), expression=columns_str or extra)
            if constr_name:
                constraint.name = constr_name
            entity.constraints.append(constraint)
        elif constr_type == "FOREIGN_KEY":
            # columns_str holds the local columns, extra should contain REFERENCES ...
            fk_cols = [c.strip('" ') for c in columns_str.split(',')]
            ref_m = re.search(r"REFERENCES\s+(\w+)\s*\(([^)]+)\)", extra, re.IGNORECASE)
            if ref_m:
                ref_entity = ref_m.group(1)
                ref_cols = [c.strip('" ') for c in ref_m.group(2).split(',')]
                constraint = Constraint(
                    type=ConstraintType.FOREIGN_KEY,
                    expression=",".join(fk_cols),
                    referenced_entity=ref_entity,
                    referenced_attributes=ref_cols,
                )
                if constr_name:
                    constraint.name = constr_name
                entity.constraints.append(constraint)

    # ── Utility: split column definitions correctly ────────────
    def _split_column_defs(self, body: str) -> List[str]:
        """Split column definitions by commas, ignoring those inside parentheses."""
        defs = []
        depth = 0
        current = ""
        for ch in body:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif ch == ',' and depth == 0:
                defs.append(current)
                current = ""
                continue
            current += ch
        if current.strip():
            defs.append(current)
        return defs

    # ── CREATE INDEX ───────────────────────────────────────────────
    def _parse_create_index(self, stmt: str, doc: MSDMDocument,
                            table_entities: Dict[str, Entity]) -> None:
        m = RE_CREATE_INDEX.search(stmt)
        if not m:
            return
        unique = m.group(1) is not None and "UNIQUE" in m.group(1).upper()
        index_name = m.group(2) or ""
        table_name = m.group(3)
        columns = [c.strip() for c in m.group(4).split(',')]

        # Find the entity
        entity = table_entities.get(table_name)
        if not entity:
            return

        idx = Index(
            name=index_name,
            attributes=columns,
            unique=unique,
        )
        entity.indexes.append(idx)

    # ── CREATE VIEW ────────────────────────────────────────────────
    def _parse_create_view(self, stmt: str, doc: MSDMDocument) -> None:
        m = RE_CREATE_VIEW.search(stmt)
        if not m:
            return
        view_name = m.group(1)
        entity = Entity(name=view_name, kind=EntityKind.VIEW)
        # Store the full statement as an annotation (round‑trip)
        entity.annotations.append(Annotation(key="view_definition", value=stmt))
        doc.entities.append(entity)

    # ── Table‑level options parser ─────────────────────────────
    def _parse_table_options(self, options_str: str) -> List[Annotation]:
        """Parse OPTIONS like ENGINE=InnoDB, TABLESPACE ..., etc."""
        annotations = []
        # Simple key=value or key value pairs
        opts = re.split(r",\s*(?=\w+\s*=)", options_str)  # crude split
        for opt in opts:
            opt = opt.strip()
            if not opt:
                continue
            m = re.match(r"(\w+)\s*=\s*(.+)", opt, re.IGNORECASE)
            if m:
                key = m.group(1)
                val = m.group(2).strip(";")
                annotations.append(Annotation(key=key.lower(), value=val))
            else:
                # Single word option like "PACK_KEYS=1"
                annotations.append(Annotation(key="table_option", value=opt))
        return annotations

    @staticmethod
    def _unquote(s: str) -> str:
        s = s.strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith('`') and s.endswith('`')):
            return s[1:-1]
        return s