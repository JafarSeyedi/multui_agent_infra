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

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import Annotation
from ...models.msdm_models import Attribute
from ...models.msdm_models import Constraint
from ...models.msdm_models import ConstraintType
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import EntityKind
from ...models.msdm_models import Index
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType, Namespace
from ..base import ParseOptions
from .base_msdm_parser import BaseMSDMParser

# ── Regex patterns ──────────────────────────────────────────────
RE_CONSTRAINT_NODE = re.compile(
    r'CREATE\s+CONSTRAINT\s+(?:\w+\s+)?ON\s+\(\s*\w+\s*:\s*(\w+)\s*\)\s+ASSERT\s+\(\s*\w+\.(\w+)\s*\)\s+IS\s+(NODE\s+KEY|UNIQUE|NOT\s+NULL|EXISTS)',
    re.IGNORECASE
)
RE_CONSTRAINT_NODE_LEGACY = re.compile(
    r'CREATE\s+CONSTRAINT\s+ON\s+\(\s*\w+\s*:\s*(\w+)\s*\)\s+ASSERT\s+(\w+)\.(\w+)\s+IS\s+(UNIQUE|NODE\s+KEY|NOT\s+NULL)',
    re.IGNORECASE
)
RE_EXISTS_NODE = re.compile(
    r'CREATE\s+CONSTRAINT\s+ON\s+\(\s*\w+\s*:\s*(\w+)\s*\)\s+ASSERT\s+EXISTS\s+\(\s*\w+\.(\w+)\s*\)',
    re.IGNORECASE
)
RE_EXISTS_REL = re.compile(
    r'CREATE\s+CONSTRAINT\s+ON\s*\(\s*\)-\[\s*\w+\s*:\s*(\w+)\s*\]-\s*\(\s*\)\s*ASSERT\s+EXISTS\s*\(\s*\w+\.(\w+)\s*\)',
    re.IGNORECASE
)
RE_INDEX_FOR = re.compile(
    r'CREATE\s+INDEX\s+(?:\w+\s+)?FOR\s+\(\s*\w+\s*:\s*(\w+)\s*\)\s+ON\s+\((.*?)\)',
    re.IGNORECASE
)
RE_INDEX_ON = re.compile(
    r'CREATE\s+INDEX\s+ON\s+:\s*(\w+)\s*\(\s*(\w+)\s*\)',
    re.IGNORECASE
)
RE_COLUMNS = re.compile(r'(\w+\.(\w+))', re.IGNORECASE)


class Neo4jSchemaParser(BaseMSDMParser):
    name = "neo4j_schema"
    supported_extensions = (".cypher", ".cql")

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        doc = MSDMDocument(
            document_id=Path(source_name).stem,
            title=Path(source_name).stem,
            media_type=MEDIA_TYPES.get("neo4j_schema", MEDIA_TYPES["txt"])
        )
        doc.namespace = Namespace(uri=Path(source_name).stem)

        text = self._strip_comments(text)
        statements = [s.strip() for s in text.split(';') if s.strip()]

        self._temp_indexes: list[tuple[str, list[str]]] = []
        node_props: dict[str, dict[str, set[str]]] = {}
        rel_props: dict[str, dict[str, set[str]]] = {}

        for stmt in statements:
            self._process_statement(stmt.upper(), stmt, node_props, rel_props, doc)

        self._build_entities(node_props, rel_props, doc)

        self.resolve_references(doc)
        return doc

    def _strip_comments(self, text: str) -> str:
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'//[^\n]*', '', text)
        return text

    def _process_statement(self, upper: str, stmt: str,
                           node_props: dict, rel_props: dict, doc: MSDMDocument) -> None:
        m = RE_CONSTRAINT_NODE.match(upper) or RE_CONSTRAINT_NODE_LEGACY.match(upper)
        if m:
            label = m.group(1).lower().capitalize()
            prop = m.group(2)
            constraint_type = m.group(3).replace(" ", "_").upper()
            if constraint_type == "NODE_KEY":
                self._add_prop(node_props, label, prop, "node_key")
            elif constraint_type == "UNIQUE":
                self._add_prop(node_props, label, prop, "unique")
            elif constraint_type in ("NOT_NULL", "EXISTS"):
                self._add_prop(node_props, label, prop, "required")
            return

        m = RE_EXISTS_NODE.match(upper)
        if m:
            label = m.group(1).lower().capitalize()
            prop = m.group(2)
            self._add_prop(node_props, label, prop, "required")
            return

        m = RE_EXISTS_REL.match(upper)
        if m:
            rel_type = m.group(1).upper()
            prop = m.group(2)
            self._add_prop(rel_props, rel_type, prop, "required")
            return

        m = RE_INDEX_FOR.match(upper)
        if m:
            label = m.group(1).lower().capitalize()
            cols_str = m.group(2)
            props = [p.split('.')[-1] for p in RE_COLUMNS.findall(cols_str)]
            for p in props:
                self._add_prop(node_props, label, p, "indexed")
            self._temp_indexes.append((label, props))
            return

        m = RE_INDEX_ON.match(upper)
        if m:
            label = m.group(1).lower().capitalize()
            prop = m.group(2)
            self._add_prop(node_props, label, prop, "indexed")
            self._temp_indexes.append((label, [prop]))
            return

        doc.annotations.append(Annotation(key="raw_statement", value=stmt))

    def _add_prop(self, props_dict: dict, key: str, prop: str, ptype: str) -> None:
        if key not in props_dict:
            props_dict[key] = {"unique": set(), "required": set(), "node_key": set(), "indexed": set()}
        if ptype in props_dict[key]:
            props_dict[key][ptype].add(prop)
        else:
            props_dict[key][ptype] = {prop}

    def _build_entities(self, node_props: dict, rel_props: dict, doc: MSDMDocument) -> None:
        # Nodes
        for label, props_by_type in node_props.items():
            entity = Entity(name=label, kind=EntityKind.GRAPH_NODE)
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
                    data_type=DataType(base=ScalarType.STRING),
                    required=is_required,
                )
                if is_unique and not is_pk:
                    attr.constraints.append(Constraint(type=ConstraintType.UNIQUE))
                entity.attributes.append(attr)
            node_key_props = props_by_type.get("node_key", set())
            if len(node_key_props) > 1:
                pk_constraint = Constraint(
                    type=ConstraintType.PRIMARY_KEY,
                    expression=",".join(sorted(node_key_props)),
                )
                for attr in entity.attributes:
                    if attr.name in node_key_props:
                        attr.constraints.append(pk_constraint)
            doc.entities.append(entity)

        # Relationships
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

        # Indexes
        for label, props in self._temp_indexes:
            n_entity = next((e for e in doc.entities if e.name == label), None)
            if n_entity:
                attrs: list[Attribute] = []
                for k in props:
                    for a in n_entity.attributes:
                        if a.name == k:
                            attrs.append(a)
                idx = Index(
                    name=f"idx_{label}_{'_'.join(props)}",
                    attributes=attrs,
                    unique=False,
                )
                n_entity.indexes.append(idx)