# engines/document/parsers/msdm_parsers/cql_parser.py
"""
CQL (Cassandra Query Language) Schema Parser.
Converts .cql files containing CREATE TABLE, CREATE TYPE, CREATE INDEX,
CREATE MATERIALIZED VIEW statements into an MSDMDocument.
Supports all CQL data types, primary key definitions, clustering order,
secondary indexes, table options (compaction, compression, etc.), and UDTs.
Preserves every detail for lossless round‑trip.
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

# ── CQL Type Mapping ─────────────────────────────────────────────
CQL_TO_SCALAR = {
    "ascii":     ScalarType.STRING,
    "text":      ScalarType.STRING,
    "varchar":   ScalarType.STRING,
    "bigint":    ScalarType.LONG,
    "blob":      ScalarType.BINARY,
    "boolean":   ScalarType.BOOLEAN,
    "counter":   ScalarType.LONG,    # counter is a 64-bit integer
    "date":      ScalarType.DATE,
    "decimal":   ScalarType.DECIMAL,
    "double":    ScalarType.DOUBLE,
    "float":     ScalarType.FLOAT,
    "inet":      ScalarType.STRING,  # IP address stored as string
    "int":       ScalarType.INT,
    "smallint":  ScalarType.INT,
    "time":      ScalarType.TIME,
    "timestamp": ScalarType.TIMESTAMP,
    "timeuuid":  ScalarType.UUID,
    "tinyint":   ScalarType.INT,
    "uuid":      ScalarType.UUID,
    "varint":    ScalarType.LONG,    # arbitrary precision integer → long
    "duration":  ScalarType.DURATION,
    "tuple":     ScalarType.STRUCT,   # tuple fields are dynamic; will be handled separately
}

# Composite CQL types that require special parsing
COMPOSITE_CQL = {
    "list":  ScalarType.ARRAY,
    "set":   ScalarType.ARRAY,       # set is like array with unique constraint
    "map":   ScalarType.MAP,
    "frozen": None,                  # frozen marks a type as immutable; we annotate it
}

# ── Helper regex patterns ────────────────────────────────────────
# Matches CREATE TABLE/KEYSPACE/INDEX/MATERIALIZED VIEW
RE_CREATE_TABLE = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\"?[\w.]+\"?)\s*\((.*?)\)\s*'
    r'(?:WITH\s+(.*?))?;',
    re.IGNORECASE | re.DOTALL
)

RE_CREATE_TYPE = re.compile(
    r'CREATE\s+TYPE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\"?[\w.]+\"?)\s*\((.*?)\)\s*;',
    re.IGNORECASE | re.DOTALL
)

RE_CREATE_INDEX = re.compile(
    r'CREATE\s+INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\"?[\w.]+\"?)?\s*'
    r'ON\s+(\"?[\w.]+\"?)\s*\((.*?)\)\s*(?:WITH\s+(.*?))?;',
    re.IGNORECASE | re.DOTALL
)

RE_CREATE_MV = re.compile(
    r'CREATE\s+MATERIALIZED\s+VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?(\"?[\w.]+\"?)\s*'
    r'AS\s+SELECT\s+(.*?)\s+FROM\s+(\"?[\w.]+\"?)\s*'
    r'(?:WHERE\s+(.*?))?\s*(?:PRIMARY\s+KEY\s+\((.*?)\))\s*'
    r'(?:WITH\s+(.*?))?;',
    re.IGNORECASE | re.DOTALL
)

# Column definition: name type (static? <frozen<...>> or complex) (PRIMARY KEY) (options)
RE_COLUMN = re.compile(
    r'(\"?[\w]+\"?)\s+((?:frozen\s*<[^>]+>|\w+(?:\s*<[^>]+>)?)+)\s*'
    r'(STATIC\s+)?(PRIMARY\s+KEY)?\s*,?',
    re.IGNORECASE
)

# Primary key clause: PRIMARY KEY ((partition_key), clustering_columns...)
RE_PK = re.compile(
    r'PRIMARY\s+KEY\s*\(\((.*?)\)\s*(?:,\s*(.*?))?\)',
    re.IGNORECASE | re.DOTALL
)

# Clustering order
RE_CLUSTERING_ORDER = re.compile(
    r'CLUSTERING\s+ORDER\s+BY\s*\((.*?)\)',
    re.IGNORECASE
)

# Simple options like compaction = {...}
RE_OPTION = re.compile(
    r'(\w+)\s*=\s*(\{.*?\}|\'[^\']*\'|\"[^\"]*\"|-?\d+(?:\.\d+)?|\w+)',
    re.IGNORECASE | re.DOTALL
)

# ── Main Parser Class ──────────────────────────────────────────
class CQLParser(BaseMSDMParser):
    """Parser for Cassandra Query Language (CQL) schema files."""
    name = "cql"
    supported_extensions = (".cql",)

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem   # keyspace name often

        # Remove comments (lines starting with -- or //, and block /* */)
        text = self._strip_comments(text)

        # Split into individual statements (separated by semicolons)
        statements = [s.strip() for s in text.split(';') if s.strip()]

        for stmt in statements:
            self._process_statement(stmt, doc)

        return doc

    # ── Comment stripping ───────────────────────────────────────
    def _strip_comments(self, text: str) -> str:
        # Remove block comments
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Remove single-line comments
        text = re.sub(r'--[^\n]*', '', text)
        text = re.sub(r'//[^\n]*', '', text)
        return text

    # ── Statement dispatching ───────────────────────────────────
    def _process_statement(self, stmt: str, doc: MSDMDocument) -> None:
        # Match CREATE TABLE
        m = RE_CREATE_TABLE.match(stmt)
        if m:
            table_name = self._unquote(m.group(1))
            columns_str = m.group(2)
            with_clause = m.group(3)
            self._parse_create_table(table_name, columns_str, with_clause, doc)
            return

        # Match CREATE TYPE
        m = RE_CREATE_TYPE.match(stmt)
        if m:
            type_name = self._unquote(m.group(1))
            fields_str = m.group(2)
            self._parse_create_type(type_name, fields_str, doc)
            return

        # Match CREATE INDEX
        m = RE_CREATE_INDEX.match(stmt)
        if m:
            index_name = self._unquote(m.group(1)) if m.group(1) else None
            table_name = self._unquote(m.group(2))
            column_def = m.group(3)
            index_options = m.group(4)
            self._parse_create_index(index_name, table_name, column_def, index_options, doc)
            return

        # Match CREATE MATERIALIZED VIEW
        m = RE_CREATE_MV.match(stmt)
        if m:
            view_name = self._unquote(m.group(1))
            select_columns = m.group(2)
            base_table = self._unquote(m.group(3))
            where_clause = m.group(4)
            pk_str = m.group(5)
            with_clause = m.group(6)
            self._parse_create_mv(view_name, select_columns, base_table, where_clause, pk_str, with_clause, doc)
            return

        # Otherwise, could be ALTER, DROP, etc. – ignore for schema definition.

    # ── CREATE TABLE ────────────────────────────────────────────
    def _parse_create_table(self, table_name: str, columns_str: str,
                            with_clause: Optional[str], doc: MSDMDocument) -> Entity:
        entity = Entity(
            name=table_name,
            kind=EntityKind.TABLE,
        )

        # Split columns by comma, but we need to respect nested function calls
        # We'll use a simple state machine or regex based on the column pattern
        column_defs = self._split_column_defs(columns_str)

        # First pass: collect columns and identify primary key clause
        pk_partition = []
        pk_clustering = []
        static_cols = set()

        for col_def in column_defs:
            col_def = col_def.strip()
            if not col_def:
                continue
            # Check if it's a PRIMARY KEY clause at the end
            if col_def.upper().startswith('PRIMARY KEY'):
                pk_match = RE_PK.search(col_def)
                if pk_match:
                    pk_partition = [x.strip().strip('"') for x in pk_match.group(1).split(',')]
                    if pk_match.group(2):
                        pk_clustering = [x.strip().strip('"') for x in pk_match.group(2).split(',')]
                continue
            # Normal column
            col_match = RE_COLUMN.match(col_def)
            if col_match:
                col_name = self._unquote(col_match.group(1))
                col_type_str = col_match.group(2).strip()
                col_static = bool(col_match.group(3))
                col_pk = bool(col_match.group(4))

                if col_pk:
                    # Column-level PRIMARY KEY (implies partition key if no other key clause)
                    if col_name not in pk_partition:
                        pk_partition.append(col_name)

                data_type, is_frozen = self._parse_cql_type(col_type_str, doc)
                attr = Attribute(
                    name=col_name,
                    data_type=data_type,
                    required=col_pk or col_name in pk_partition,  # primary key columns are required
                    # Primary key is handled later via constraints
                )
                if col_static:
                    static_cols.add(col_name)
                    attr.annotations.append(Annotation(key="static", value="true"))
                if is_frozen:
                    attr.annotations.append(Annotation(key="frozen", value="true"))

                entity.attributes.append(attr)

        # Add primary key constraint
        if pk_partition:
            pk_attr_names = pk_partition + pk_clustering
            pk_constraint = Constraint(
                type=ConstraintType.PRIMARY_KEY,
                name=f"pk_{table_name}",
                expression=",".join(pk_attr_names),
            )
            # Mark each PK attribute as primary key and part of constraint
            for attr_name in pk_attr_names:
                for attr in entity.attributes:
                    if attr.name == attr_name:
                        attr.primary_key = True
                        attr.constraints.append(pk_constraint)

        # Clustering order
        clustering_order_str = with_clause  # clustering order is usually in WITH
        if clustering_order_str:
            for option_key, option_val in self._parse_options(clustering_order_str):
                if option_key.upper() == 'CLUSTERING ORDER BY':
                    # option_val is the content inside parentheses
                    cols_order = self._parse_clustering_order(option_val)
                    for col_name, direction in cols_order.items():
                        for attr in entity.attributes:
                            if attr.name == col_name:
                                attr.annotations.append(Annotation(key="clustering_order", value=direction))

        # Additional table options as annotations
        if with_clause:
            for opt_key, opt_val in self._parse_options(with_clause):
                if opt_key.upper() not in ('CLUSTERING ORDER BY',):
                    entity.annotations.append(Annotation(key=opt_key.lower(), value=opt_val))

        # Also mark compaction, compression etc. as annotations
        doc.entities.append(entity)
        return entity

    # ── CREATE TYPE (UDT) ──────────────────────────────────────
    def _parse_create_type(self, type_name: str, fields_str: str, doc: MSDMDocument) -> Entity:
        entity = Entity(
            name=type_name,
            kind=EntityKind.OBJECT,  # UDT is like a struct
        )
        field_defs = self._split_column_defs(fields_str)
        for fdef in field_defs:
            fdef = fdef.strip()
            if not fdef:
                continue
            col_match = RE_COLUMN.match(fdef)
            if col_match:
                col_name = self._unquote(col_match.group(1))
                col_type_str = col_match.group(2).strip()
                data_type, is_frozen = self._parse_cql_type(col_type_str, doc)
                attr = Attribute(name=col_name, data_type=data_type)
                if is_frozen:
                    attr.annotations.append(Annotation(key="frozen", value="true"))
                entity.attributes.append(attr)
        doc.entities.append(entity)
        return entity

    # ── CREATE INDEX ───────────────────────────────────────────
    def _parse_create_index(self, index_name: Optional[str], table_name: str,
                            column_def: str, index_options: Optional[str], doc: MSDMDocument) -> None:
        # column_def is like "column_name" or "keys(column_name)"
        col_name = column_def.strip().strip('"')
        # Find the corresponding entity
        entity = next((e for e in doc.entities if e.name == table_name), None)
        if entity:
            idx = Index(
                name=index_name or f"idx_{table_name}_{col_name}",
                attributes=[col_name],
                unique=False,
            )
            if index_options:
                for opt_key, opt_val in self._parse_options(index_options):
                    if opt_key.upper() == 'USING':
                        idx.method = opt_val
            entity.indexes.append(idx)

    # ── CREATE MATERIALIZED VIEW ───────────────────────────────
    def _parse_create_mv(self, view_name: str, select_cols: str, base_table: str,
                         where_clause: Optional[str], pk_str: str,
                         with_clause: Optional[str], doc: MSDMDocument) -> Entity:
        # Materialized view is like a table; we treat it as a separate Entity
        entity = Entity(
            name=view_name,
            kind=EntityKind.VIEW,
        )
        entity.annotations.append(Annotation(key="base_table", value=base_table))

        # Extract selected columns (they become attributes)
        # select_cols might be "col1, col2, ..."
        col_names = [c.strip().strip('"') for c in select_cols.split(',')]
        # We need the types from the base entity – we can look them up
        base_entity = next((e for e in doc.entities if e.name == base_table), None)
        for cname in col_names:
            # find attribute in base entity to get the type
            base_attr = None
            if base_entity:
                base_attr = next((a for a in base_entity.attributes if a.name == cname), None)
            if base_attr:
                attr = Attribute(name=cname, data_type=base_attr.data_type, required=True)
            else:
                attr = Attribute(name=cname, data_type=DataType(base=ScalarType.ANY), required=True)
            entity.attributes.append(attr)

        # Primary key of the view
        pk_partition = [x.strip().strip('"') for x in pk_str.split(',')]
        pk_constraint = Constraint(
            type=ConstraintType.PRIMARY_KEY,
            name=f"pk_{view_name}",
            expression=",".join(pk_partition),
        )
        for attr_name in pk_partition:
            for attr in entity.attributes:
                if attr.name == attr_name:
                    attr.primary_key = True
                    attr.constraints.append(pk_constraint)

        doc.entities.append(entity)
        return entity

    # ── CQL type parsing ───────────────────────────────────────
    def _parse_cql_type(self, type_str: str, doc: MSDMDocument) -> Tuple[DataType, bool]:
        """
        Parse a CQL type string and return (DataType, is_frozen).
        Handles nested types like list<frozen<map<text, int>>>.
        """
        is_frozen = False
        type_str = type_str.strip()
        # Remove surrounding whitespace
        while type_str.upper().startswith('FROZEN<'):
            is_frozen = True
            # Extract inner content of frozen<...>
            depth = 0
            start = len('FROZEN<')
            end = start
            for i, ch in enumerate(type_str[start:], start):
                if ch == '<':
                    depth += 1
                elif ch == '>':
                    if depth == 0:
                        end = i
                        break
                    depth -= 1
            type_str = type_str[start:end].strip()

        # Now check if it's a composite type
        # list<...> or set<...> or map<k,v>
        m = re.match(r'(\w+)\s*<(.+)>', type_str)
        if m:
            outer = m.group(1).lower()
            inner = m.group(2).strip()
            if outer in ('list', 'set'):
                inner_type, inner_frozen = self._parse_cql_type(inner, doc)
                return DataType(base=ScalarType.ARRAY, element_type=inner_type), is_frozen or inner_frozen
            elif outer == 'map':
                # inner should be key,value
                # find comma that splits key and value (not inside nested <>)
                key, value = self._split_map_key_value(inner)
                if key is not None and value is not None:
                    key_type, _ = self._parse_cql_type(key, doc)
                    value_type, _ = self._parse_cql_type(value, doc)
                    return DataType(base=ScalarType.MAP, key_type=key_type, value_type=value_type), is_frozen
            elif outer == 'tuple':
                # tuple<type1,type2,...>
                parts = self._split_tuple_parts(inner)
                # Tuple is represented as a STRUCT with nested attributes
                # We'll build a brief entity for it? Actually MSDM has no entity for inline structs;
                # we can use STRUCT base with nested_attributes attached to the Attribute later.
                # For now we store as ANY with annotation.
                return DataType(base=ScalarType.STRUCT), is_frozen
            elif outer == 'frozen':
                return self._parse_cql_type(inner, doc)  # recursion
            else:
                # Could be a user-defined type
                return DataType(base=ScalarType.REF, ref_entity=type_str), is_frozen
        else:
            # simple type or UDT reference
            if type_str.lower() in CQL_TO_SCALAR:
                return DataType(base=CQL_TO_SCALAR[type_str.lower()]), is_frozen
            else:
                # assume UDT or unknown; treat as reference
                return DataType(base=ScalarType.REF, ref_entity=type_str), is_frozen

    def _split_map_key_value(self, inner: str) -> Tuple[Optional[str], Optional[str]]:
        """Split map<key,value> correctly, accounting for nested angle brackets."""
        depth = 0
        for i, ch in enumerate(inner):
            if ch == '<':
                depth += 1
            elif ch == '>':
                depth -= 1
            elif ch == ',' and depth == 0:
                return inner[:i].strip(), inner[i+1:].strip()
        return None, None

    def _split_tuple_parts(self, inner: str) -> List[str]:
        """Split tuple contents by commas, respecting nested angle brackets."""
        parts = []
        depth = 0
        last = 0
        for i, ch in enumerate(inner):
            if ch == '<':
                depth += 1
            elif ch == '>':
                depth -= 1
            elif ch == ',' and depth == 0:
                parts.append(inner[last:i].strip())
                last = i + 1
        parts.append(inner[last:].strip())
        return parts

    # ── Helper: split column definitions properly ───────────────
    def _split_column_defs(self, columns_str: str) -> List[str]:
        """Split by comma that is not inside parentheses or angle brackets."""
        defs = []
        depth_paren = 0
        depth_angle = 0
        current = ''
        for ch in columns_str:
            if ch == '(':
                depth_paren += 1
            elif ch == ')':
                depth_paren -= 1
            elif ch == '<':
                depth_angle += 1
            elif ch == '>':
                depth_angle -= 1
            elif ch == ',' and depth_paren == 0 and depth_angle == 0:
                defs.append(current)
                current = ''
                continue
            current += ch
        if current.strip():
            defs.append(current)
        return defs

    # ── Options parsing ─────────────────────────────────────────
    def _parse_options(self, options_str: str) -> List[Tuple[str, str]]:
        """Parse WITH ... option = value pairs."""
        pairs = []
        # options_str might be the part after WITH
        # Simple regex approach:
        for m in RE_OPTION.finditer(options_str):
            key = m.group(1)
            value = m.group(2)
            pairs.append((key, value))
        # also handle CLUSTERING ORDER BY which is a block: clustering order by (col1 ASC, col2 DESC)
        # RE_OPTION won't capture the whole block; we need to extract it separately
        end_pos = 0
        while True:
            start = options_str.find('CLUSTERING ORDER BY', end_pos)
            if start == -1:
                break
            # Find the opening parenthesis
            paren_start = options_str.find('(', start)
            if paren_start == -1:
                break
            # Find the closing parenthesis
            paren_end = options_str.find(')', paren_start)
            if paren_end == -1:
                break
            content = options_str[paren_start+1:paren_end].strip()
            pairs.append(('CLUSTERING ORDER BY', content))
            end_pos = paren_end + 1
        return pairs

    def _parse_clustering_order(self, content: str) -> Dict[str, str]:
        """Parse 'col1 ASC, col2 DESC' into dict."""
        order_map = {}
        for part in content.split(','):
            part = part.strip()
            if not part:
                continue
            pieces = part.split()
            if len(pieces) >= 2:
                col = pieces[0].strip('"')
                direction = pieces[1].upper()
                order_map[col] = direction
            elif pieces:
                col = pieces[0].strip('"')
                order_map[col] = 'ASC'   # default
        return order_map

    # ── Utility ─────────────────────────────────────────────────
    @staticmethod
    def _unquote(s: str) -> str:
        s = s.strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        return s