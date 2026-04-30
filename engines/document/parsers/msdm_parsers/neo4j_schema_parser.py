# engines/document/parsers/msdm_parsers/neo4j_schema_parser.py
"""
Neo4j Schema Parser – converts .cypher/.cql schema files into an MSDMDocument.

Handles:
- CREATE CONSTRAINT … ON (n:Label) ASSERT (n.property) IS NODE KEY
- CREATE CONSTRAINT … ON (n:Label) ASSERT (n.property) IS UNIQUE
- CREATE CONSTRAINT … ON (n:Label) ASSERT EXISTS (n.property)
- CREATE CONSTRAINT … ON ()-[r:REL_TYPE]-() ASSERT EXISTS (r.property)
- CREATE INDEX [index_name] FOR (n:Label) ON (n.property, …)
- Legacy CREATE INDEX ON :Label(property)
- Any unrecognised Cypher DDL is stored as a raw annotation for round‑trip.

All node labels become MSDM Entities with kind GRAPH_NODE, relationship types
become GRAPH_EDGE entities, and properties are extracted from constraints/indexes.
Primary keys (NODE KEY / UNIQUE) and required fields (EXISTS) are captured.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Set, Tuple

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

# ── Regex patterns ──────────────────────────────────────────────
# Modern syntax: CREATE CONSTRAINT [name] ON (n:Label) ASSERT (n.prop) IS [NODE KEY|UNIQUE|...]
RE_CONSTRAINT_NODE = re.compile(
    r'CREATE\s+CONSTRAINT\s+(?:\w+\s+)?ON\s+\(\s*\w+\s*:\s*(\w+)\s*\)\s+ASSERT\s+\(\s*\w+\.(\w+)\s*\)\s+IS\s+(NODE\s+KEY|UNIQUE|NOT\s+NULL|EXISTS)',
    re.IGNORECASE
)

# Legacy uniqueness constraint: CREATE CONSTRAINT ON (n:Label) ASSERT n.property IS UNIQUE
RE_CONSTRAINT_NODE_LEGACY = re.compile(
    r'CREATE\s+CONSTRAINT\s+ON\s+\(\s*\w+\s*:\s*(\w+)\s*\)\s+ASSERT\s+(\w+)\.(\w+)\s+IS\s+(UNIQUE|NODE\s+KEY|NOT\s+NULL)',
    re.IGNORECASE
)

# Existence constraint old: CREATE CONSTRAINT ON (n:Label) ASSERT EXISTS (n.property)
RE_EXISTS_NODE = re.compile(
    r'CREATE\s+CONSTRAINT\s+ON\s+\(\s*\w+\s*:\s*(\w+)\s*\)\s+ASSERT\s+EXISTS\s+\(\s*\w+\.(\w+)\s*\)',
    re.IGNORECASE
)

# Relationship property existence: CREATE CONSTRAINT ... ON ()-[r:REL_TYPE]-() ASSERT EXISTS (r.property)
RE_EXISTS_REL = re.compile(
    r'CREATE\s+CONSTRAINT\s+ON\s*\(\s*\)-\[\s*\w+\s*:\s*(\w+)\s*\]-\s*\(\s*\)\s*ASSERT\s+EXISTS\s*\(\s*\w+\.(\w+)\s*\)',
    re.IGNORECASE
)

# New index: CREATE INDEX [name] FOR (n:Label) ON (n.prop1, n.prop2, ...)
RE_INDEX_FOR = re.compile(
    r'CREATE\s+INDEX\s+(?:\w+\s+)?FOR\s+\(\s*\w+\s*:\s*(\w+)\s*\)\s+ON\s+\((.*?)\)',
    re.IGNORECASE
)

# Legacy index: CREATE INDEX ON :Label(prop)
RE_INDEX_ON = re.compile(
    r'CREATE\s+INDEX\s+ON\s+:\s*(\w+)\s*\(\s*(\w+)\s*\)',
    re.IGNORECASE
)

# Composite index columns (inside parentheses) – split by comma
RE_COLUMNS = re.compile(r'(\w+\.(\w+))', re.IGNORECASE)


class Neo4jSchemaParser(BaseMSDMParser):
    """Parser for Neo4j Cypher schema files (.cypher, .cql)."""
    name = "neo4j_schema"
    supported_extensions = (".cypher", ".cql")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem

        # Remove single-line and block comments
        text = self._strip_comments(text)

        # Split statements by semicolon
        statements = [s.strip() for s in text.split(';') if s.strip()]

        # Temporary stores for collected properties and constraints
        node_props: Dict[str, Dict[str, Set[str]]] = {}   # label -> { "unique": set(), "required": set(), "node_key": set() }
        rel_props: Dict[str, Dict[str, Set[str]]] = {}    # rel_type -> similar

        for stmt in statements:
            self._process_statement(stmt.upper(), stmt, node_props, rel_props, doc)

        # Build entities from collected properties
        self._build_entities(node_props, rel_props, doc)

        # Any remaining unrecognised statements can be stored as raw annotations
        # (already captured by _process_statement)

        return doc

    def _strip_comments(self, text: str) -> str:
        # Remove block comments /* */
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Remove line comments //
        text = re.sub(r'//[^\n]*', '', text)
        return text

    def _process_statement(self, upper: str, stmt: str,
                           node_props: Dict, rel_props: Dict, doc: MSDMDocument) -> None:
        """Classify and extract properties from a single DDL statement."""
        # --- Node constraints ---
        m = RE_CONSTRAINT_NODE.match(upper) or RE_CONSTRAINT_NODE_LEGACY.match(upper)
        if m:
            label = m.group(1).lower().capitalize()
            prop = m.group(2)
            constraint_type = m.group(3).replace(" ", "_").upper()  # NODE_KEY, UNIQUE, NOT_NULL, EXISTS
            if constraint_type == "NODE_KEY":
                self._add_prop(node_props, label, prop, "node_key")
            elif constraint_type == "UNIQUE":
                self._add_prop(node_props, label, prop, "unique")
            elif constraint_type in ("NOT_NULL", "EXISTS"):
                self._add_prop(node_props, label, prop, "required")
            return

        # Existence node
        m = RE_EXISTS_NODE.match(upper)
        if m:
            label = m.group(1).lower().capitalize()
            prop = m.group(2)
            self._add_prop(node_props, label, prop, "required")
            return

        # Relationship property existence
        m = RE_EXISTS_REL.match(upper)
        if m:
            rel_type = m.group(1).upper()
            prop = m.group(2)
            self._add_prop(rel_props, rel_type, prop, "required")
            return

        # Index (new syntax)
        m = RE_INDEX_FOR.match(upper)
        if m:
            label = m.group(1).lower().capitalize()
            cols_str = m.group(2)
            # Extract property names from n.propName
            props = [p.split('.')[-1] for p in RE_COLUMNS.findall(cols_str)]
            for p in props:
                self._add_prop(node_props, label, p, "indexed")   # we'll convert to index when building
            # Later, we'll create an Index object
            # Save the statement with the entity for later creation of Index
            # We'll attach to doc._indexes list
            if not hasattr(doc, '_indexes'):
                doc._indexes = []
            doc._indexes.append((label, props))
            return

        # Legacy index
        m = RE_INDEX_ON.match(upper)
        if m:
            label = m.group(1).lower().capitalize()
            prop = m.group(2)
            self._add_prop(node_props, label, prop, "indexed")
            if not hasattr(doc, '_indexes'):
                doc._indexes = []
            doc._indexes.append((label, [prop]))
            return

        # Anything else (including constraint with relationship uniqueness, etc.) – store as raw
        doc.annotations.append(Annotation(key="raw_statement", value=stmt))

    def _add_prop(self, props_dict: Dict, key: str, prop: str, ptype: str) -> None:
        """Add a property classification to the dictionary."""
        if key not in props_dict:
            props_dict[key] = {"unique": set(), "required": set(), "node_key": set(), "indexed": set()}
        if ptype in props_dict[key]:
            props_dict[key][ptype].add(prop)
        else:
            # collected categories, we can just have sets per type
            pass
        # Initialize if needed
        if key not in props_dict:
            props_dict[key] = {}
        if ptype not in props_dict[key]:
            props_dict[key][ptype] = set()
        props_dict[key][ptype].add(prop)

    def _build_entities(self, node_props: Dict, rel_props: Dict, doc: MSDMDocument) -> None:
        """Create Entities from collected node and relationship properties."""
        # Nodes
        for label, props_by_type in node_props.items():
            entity = Entity(name=label, kind=EntityKind.GRAPH_NODE)
            # Collect all property names
            all_props = set()
            for s in props_by_type.values():
                all_props.update(s)
            for prop_name in all_props:
                is_unique = prop_name in props_by_type.get("unique", set())
                is_required = prop_name in props_by_type.get("required", set()) or \
                              prop_name in props_by_type.get("node_key", set())
                is_pk = prop_name in props_by_type.get("node_key", set())
                attr = Attribute(
                    name=prop_name,
                    data_type=DataType(base=ScalarType.STRING),  # we can't infer type
                    required=is_required,
                    primary_key=is_pk,
                )
                if is_unique and not is_pk:
                    attr.constraints.append(Constraint(type=ConstraintType.UNIQUE))
                entity.attributes.append(attr)
            # Node key constraint as composite primary key if multiple
            node_key_props = props_by_type.get("node_key", set())
            if len(node_key_props) > 1:
                # Composite PK
                pk_constraint = Constraint(
                    type=ConstraintType.PRIMARY_KEY,
                    expression=",".join(sorted(node_key_props)),
                )
                for attr in entity.attributes:
                    if attr.name in node_key_props:
                        attr.primary_key = True
                        attr.constraints.append(pk_constraint)
            doc.entities.append(entity)

        # Relationships (edge entities)
        for rel_type, props_by_type in rel_props.items():
            entity = Entity(name=rel_type, kind=EntityKind.GRAPH_EDGE)
            all_props = set()
            for s in props_by_type.values():
                all_props.update(s)
            for prop_name in all_props:
                is_required = prop_name in props_by_type.get("required", set())
                attr = Attribute(
                    name=prop_name,
                    data_type=DataType(base=ScalarType.STRING),
                    required=is_required,
                )
                entity.attributes.append(attr)
            doc.entities.append(entity)

        # Add Index objects from collected indexes
        if hasattr(doc, '_indexes'):
            for label, props in doc._indexes:
                entity = next((e for e in doc.entities if e.name == label), None)
                if entity:
                    idx = Index(
                        name=f"idx_{label}_{'_'.join(props)}",
                        attributes=props,
                        unique=False,  # can't determine from index alone; if also unique constraint, we could set True
                    )
                    entity.indexes.append(idx)