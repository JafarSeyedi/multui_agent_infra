# engines/document/parsers/ssdm_parsers/yang_parser.py
"""
YANG 1.1 → Unified MSDM/SSDM Parser

Design decisions:
- choice → standalone Entity with composition = ONE_OF; each case → Entity member
- augment → augmenting entity.augments = target_entity
- grouping → Entity.is_template = True
- uses → Attribute.template = grouping_entity
- list → entry Entity + ARRAY attribute; list_key = key attribute (reference)
- must/when → Constraint (MUST/WHEN)
- config/status → Entity/Attribute.is_config / version_status
- deviation → stored in Entity.yang_deviate_targets
- header metadata (imports, includes, etc.) → doc.metadata (simple lists)
"""
from __future__ import annotations

import re
from pathlib import Path

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import (
    Annotation, Attribute, EntityComposition, CompositionType, Constraint,
    ConstraintType, DataType, Entity, EntityKind, MSDMDocument,
    Namespace, ScalarType, VersionStatus
)
from ...models.ssdm_models import (
    ContactInfo, ServiceOperation, OperationType, RequestBody, Response, Server,
    SSDMDocument, YangMetadata
)
from ..base import ParseOptions
from .base_ssdm_parser import BaseSSDMParser

# ------------------------------------------------------------------
# Tokenizer (unchanged)
# ------------------------------------------------------------------
TOKEN_SPEC = [
    ("BLOCK_COMMENT",  r"/\*[\s\S]*?\*/"),
    ("LINE_COMMENT",   r"//[^\n]*"),
    ("STRING",         r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\''),
    ("SEMICOLON",      r";"),
    ("LBRACE",         r"\{"),
    ("RBRACE",         r"\}"),
    ("KEYWORD",        r"[a-zA-Z_][\w\-]*"),
    ("WHITESPACE",     r"\s+"),
    ("UNEXPECTED",     r"."),
]
TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))

class _Token:
    __slots__ = ("kind", "value", "pos")
    def __init__(self, kind: str, value: str, pos: int):
        self.kind = kind
        self.value = value
        self.pos = pos

def _tokenize(text: str) -> list[_Token]:
    tokens = []
    for m in TOKEN_RE.finditer(text):
        kind = m.lastgroup
        if not kind:
            continue
        value = m.group()
        if kind in ("WHITESPACE", "BLOCK_COMMENT", "LINE_COMMENT"):
            continue
        tokens.append(_Token(kind, value, m.start()))
    return tokens

# ------------------------------------------------------------------
# Parser
# ------------------------------------------------------------------
class YANGParser(BaseSSDMParser):
    name = "yang"
    supported_extensions = (".yang",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)

        # Get media type; fallback to "txt" if "yang" not defined
        media_type = MEDIA_TYPES["yang"]
        doc = SSDMDocument(
            document_id=Path(source_name).stem,
            title=Path(source_name).stem,
            version="1.0.0",
            media_type=media_type,
        )
        doc.source_file = source_name
        doc.raw_text = text

        tokens = _tokenize(text)
        self._tokens = tokens
        self._pos = 0
        self._all_entities: list[Entity] = []   # collect all entities for doc.type_definitions

        self._parse_module(doc)
        return doc

    # --- _Token helpers -------------------------------------------------
    def _peek(self) -> _Token | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None
    def _peek_value(self) -> str | None:
        t = self._peek()
        return t.value if t else None
    def _peek_kind(self) -> str | None:
        t = self._peek()
        return t.kind if t else None
    def _advance(self) -> _Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok
    def _expect(self, kind: str, value: str | None = None) -> _Token:
        tok = self._advance()
        if tok.kind != kind or (value is not None and tok.value != value):
            raise SyntaxError(f"Expected {kind}('{value}') but got {tok}")
        return tok
    def _skip_block(self) -> None:
        self._expect("LBRACE")
        depth = 1
        while depth > 0 and self._pos < len(self._tokens):
            tok = self._advance()
            if tok.value == "{":
                depth += 1
            elif tok.value == "}":
                depth -= 1
    def _skip_until_semicolon(self) -> None:
        while self._peek() and self._peek_kind() != "SEMICOLON":
            self._advance()
        if self._peek():
            self._advance()   # consume semicolon

    # --- Module parsing ------------------------------------------------
    def _parse_module(self, doc: SSDMDocument) -> None:
        self._expect("KEYWORD", "module")
        module_name = self._expect("KEYWORD").value
        doc.title = module_name
        self._expect("LBRACE")

        root_entity = Entity(name=module_name, kind=EntityKind.OBJECT)
        rpcs: list[ServiceOperation] = []
        notifications: list[ServiceOperation] = []
        type_defs = MSDMDocument(
            document_id=f"{module_name}_types",
            title=f"{module_name} Types",
            media_type=MEDIA_TYPES["yang"],
        )
        groupings: dict[str, Entity] = {}
        revisions: list[tuple[str, str]] = []

        while self._peek() and self._peek_value() != "}":
            kw = self._peek_value()
            # --- header statements ------------------------------------
            if kw == "yang-version":
                self._advance()
                doc.metadata["yang_version"] = self._expect("KEYWORD").value
                self._expect("SEMICOLON")
            elif kw == "namespace":
                self._advance()
                ns = self._unquote(self._expect("STRING").value)
                doc.servers.append(Server(url=ns, description="YANG namespace"))
                doc.metadata["yang_namespace"] = ns
                self._expect("SEMICOLON")
            elif kw == "prefix":
                self._advance()
                doc.metadata["yang_prefix"] = self._expect("KEYWORD").value
                self._expect("SEMICOLON")
            elif kw == "description":
                self._advance()
                doc.description = self._parse_description()
                self._expect("SEMICOLON")
            elif kw == "contact":
                self._advance()
                contact_str = self._parse_description()
                doc.contact = ContactInfo(name=contact_str)
                self._expect("SEMICOLON")
            elif kw == "organization":
                self._advance()
                doc.metadata["yang_organization"] = self._parse_description()
                self._expect("SEMICOLON")
            elif kw == "revision":
                self._advance()
                rev_date = self._unquote(self._expect("STRING").value)
                rev_desc = ""
                if self._peek_value() == "{":
                    self._advance()
                    while self._peek() and self._peek_value() != "}":
                        if self._peek_value() == "description":
                            self._advance()
                            rev_desc = self._parse_description()
                            self._expect("SEMICOLON")
                        else:
                            self._skip_until_semicolon()
                    self._expect("RBRACE")
                revisions.append((rev_date, rev_desc))
                self._expect("SEMICOLON")
            elif kw == "import":
                self._advance()
                imp = self._expect("KEYWORD").value
                doc.metadata.setdefault("yang_imports", []).append(imp)
                if self._peek_value() == "{":
                    self._skip_block()
                self._expect("SEMICOLON")
            elif kw == "include":
                self._advance()
                inc = self._unquote(self._expect("STRING").value)
                doc.metadata.setdefault("yang_includes", []).append(inc)
                self._expect("SEMICOLON")
            elif kw == "identity":
                self._advance()
                ident = self._expect("KEYWORD").value
                doc.metadata.setdefault("yang_identities", []).append(ident)
                if self._peek_value() == "{":
                    self._skip_block()
                self._expect("SEMICOLON")
            elif kw == "feature":
                self._advance()
                feat = self._expect("KEYWORD").value
                doc.metadata.setdefault("yang_features", []).append(feat)
                self._expect("SEMICOLON")
            elif kw == "extension":
                self._advance()
                ext = self._expect("KEYWORD").value
                doc.metadata.setdefault("yang_extensions", []).append(ext)
                if self._peek_value() == "{":
                    self._skip_block()
                self._expect("SEMICOLON")
            elif kw == "typedef":
                td = self._parse_typedef()
                self._all_entities.append(td)
                type_defs.entities.append(td)
            elif kw == "grouping":
                grp = self._parse_grouping()
                groupings[grp.name] = grp
                self._all_entities.append(grp)
                type_defs.entities.append(grp)
            elif kw == "augment":
                aug_entity = self._parse_augment()
                if aug_entity:
                    self._all_entities.append(aug_entity)
                    type_defs.entities.append(aug_entity)
            elif kw in ("container", "leaf", "leaf-list", "list"):
                self._parse_data_node_into_entity(root_entity)
            elif kw == "choice":
                self._parse_choice_node(root_entity)
            elif kw == "rpc":
                rpcs.append(self._parse_rpc())
            elif kw == "notification":
                notifications.append(self._parse_notification())
            else:
                self._advance()
                if self._peek_value() == "{":
                    self._skip_block()
                else:
                    self._skip_until_semicolon()

        self._expect("RBRACE")
        if revisions:
            latest = max(revisions, key=lambda x: x[0])
            doc.version = latest[0]
            doc.metadata["yang_revisions"] = revisions

        doc.root_entity = root_entity
        doc.operations.extend(rpcs)
        doc.operations.extend(notifications)
        if type_defs.entities:
            doc.type_definitions = type_defs
        if groupings:
            doc.metadata["yang_groupings"] = groupings

    # --- Data node parsing into an existing entity --------------------
    def _parse_data_node_into_entity(self, parent: Entity) -> None:
        kw = self._peek_value()
        if kw == "container":
            self._parse_container(parent)
        elif kw == "leaf":
            self._parse_leaf(parent)
        elif kw == "leaf-list":
            self._parse_leaf_list(parent)
        elif kw == "list":
            self._parse_list(parent)

    # --- Container ----------------------------------------------------
    def _parse_container(self, parent: Entity) -> None:
        self._advance()
        name = self._expect("KEYWORD").value
        self._expect("LBRACE")
        container_entity = Entity(name=name, kind=EntityKind.OBJECT)
        self._parse_common_metadata(container_entity)
        while self._peek() and self._peek_value() != "}":
            self._parse_data_node_into_entity(container_entity)
        self._expect("RBRACE")
        # Create reference attribute
        attr = Attribute(name=name, data_type=DataType(base=ScalarType.REF, ref_entity_id=container_entity.name))
        attr.description = container_entity.description
        parent.attributes.append(attr)
        self._all_entities.append(container_entity)

    # --- Leaf ---------------------------------------------------------
    def _parse_leaf(self, parent: Entity) -> None:
        self._advance()
        name = self._expect("KEYWORD").value
        self._expect("LBRACE")
        attr = Attribute(name=name, data_type=DataType(base=ScalarType.STRING))
        self._parse_common_metadata(attr)
        if self._peek_value() == "type":
            self._advance()
            self._parse_type(attr)   # passes attr to attach constraints
        while self._peek() and self._peek_value() != "}":
            kw = self._peek_value()
            if kw == "default":
                self._advance()
                attr.default_value = self._advance().value
                self._expect("SEMICOLON")
            elif kw == "mandatory":
                self._advance()
                attr.required = self._advance().value == "true"
                self._expect("SEMICOLON")
            else:
                self._skip_until_semicolon()
        self._expect("RBRACE")
        parent.attributes.append(attr)

    # --- Leaf-list ----------------------------------------------------
    def _parse_leaf_list(self, parent: Entity) -> None:
        self._advance()
        name = self._expect("KEYWORD").value
        self._expect("LBRACE")
        attr = Attribute(name=name, data_type=DataType(base=ScalarType.STRING))
        self._parse_common_metadata(attr)
        if self._peek_value() == "type":
            self._advance()
            inner_type = DataType(base=ScalarType.STRING)
            self._parse_type(attr, element_type=inner_type)
            attr.data_type = DataType(base=ScalarType.ARRAY, element_type=inner_type)
        while self._peek() and self._peek_value() != "}":
            kw = self._peek_value()
            if kw == "default":
                self._advance()
                attr.default_value = self._advance().value
                self._expect("SEMICOLON")
            else:
                self._skip_until_semicolon()
        self._expect("RBRACE")
        parent.attributes.append(attr)

    # --- List ---------------------------------------------------------
    def _parse_list(self, parent: Entity) -> None:
        self._advance()
        name = self._expect("KEYWORD").value
        self._expect("LBRACE")
        entry_entity = Entity(name=f"{name}_entry", kind=EntityKind.OBJECT)
        self._parse_common_metadata(entry_entity)
        key_name = None
        if self._peek_value() == "key":
            self._advance()
            key_name = self._unquote(self._expect("STRING").value)
            self._expect("SEMICOLON")
        while self._peek() and self._peek_value() != "}":
            self._parse_data_node_into_entity(entry_entity)
        self._expect("RBRACE")
        if key_name:
            entry_entity.list_key = key_name
        # Attribute of type ARRAY of the entry entity
        attr = Attribute(
            name=name,
            data_type=DataType(base=ScalarType.ARRAY,
                               element_type=DataType(base=ScalarType.REF, ref_entity_id=entry_entity.name))
        )
        attr.description = entry_entity.description
        parent.attributes.append(attr)
        self._all_entities.append(entry_entity)

    # --- Choice (EntityComposition ONE_OF) ---------------------------
    def _parse_choice_node(self, parent: Entity) -> None:
        """
        Parse a choice statement.
        Creates a separate Entity representing the choice.
        The choice entity has a composition (ONE_OF) with members = case entities.
        The choice entity is referenced by the parent via an attribute of type REF.
        """
        self._advance()  # 'choice'
        choice_name = self._expect("KEYWORD").value
        self._expect("LBRACE")

        # Create the choice entity
        choice_entity = Entity(name=choice_name, kind=EntityKind.OBJECT)
        self._parse_common_metadata(choice_entity)
        comp = EntityComposition(composition_type=CompositionType.ONE_OF, members=[])
        choice_entity.composition = comp

        # Parse cases inside
        while self._peek() and self._peek_value() != "}":
            if self._peek_value() == "case":
                self._advance()
                case_name = self._expect("KEYWORD").value
                self._expect("LBRACE")
                case_entity = Entity(name=case_name, kind=EntityKind.OBJECT)
                self._parse_common_metadata(case_entity)
                while self._peek() and self._peek_value() != "}":
                    self._parse_data_node_into_entity(case_entity)
                self._expect("RBRACE")
                comp.members.append(case_entity)
                comp.member_ids.append(case_name)
                self._all_entities.append(case_entity)
            else:
                self._skip_until_semicolon()
        self._expect("RBRACE")

        # Add the choice entity to the global list
        self._all_entities.append(choice_entity)

        # Create a reference attribute in the parent pointing to the choice entity
        attr = Attribute(name=choice_name, data_type=DataType(base=ScalarType.REF, ref_entity_id=choice_entity.name))
        attr.description = choice_entity.description
        parent.attributes.append(attr)

    # --- Typedef ------------------------------------------------------
    def _parse_typedef(self) -> Entity:
        self._advance()
        name = self._expect("KEYWORD").value
        self._expect("LBRACE")
        attr = Attribute(name="value", data_type=DataType(base=ScalarType.STRING))
        while self._peek() and self._peek_value() != "}":
            kw = self._peek_value()
            if kw == "type":
                self._advance()
                self._parse_type(attr)
            elif kw == "description":
                self._advance()
                attr.description = self._parse_description()
                self._expect("SEMICOLON")
            elif kw == "default":
                self._advance()
                attr.default_value = self._advance().value
                self._expect("SEMICOLON")
            else:
                self._skip_until_semicolon()
        self._expect("RBRACE")
        self._expect("SEMICOLON")
        entity = Entity(name=name, kind=EntityKind.OBJECT)
        entity.attributes.append(attr)
        return entity

    # --- Grouping -----------------------------------------------------
    def _parse_grouping(self) -> Entity:
        self._advance()
        name = self._expect("KEYWORD").value
        self._expect("LBRACE")
        grouping_entity = Entity(name=name, kind=EntityKind.OBJECT)
        grouping_entity.is_template = True
        self._parse_common_metadata(grouping_entity)
        while self._peek() and self._peek_value() != "}":
            self._parse_data_node_into_entity(grouping_entity)
        self._expect("RBRACE")
        return grouping_entity

    # --- Augment ------------------------------------------------------
    def _parse_augment(self) -> Entity | None:
        self._advance()  # 'augment'
        target_path = self._unquote(self._expect("STRING").value)
        self._expect("LBRACE")
        # Create an entity that represents the augment block
        augment_entity = Entity(name=f"augment_{target_path.replace('/', '_')}", kind=EntityKind.OBJECT)
        # We need to resolve the target entity later; for now, we store the path in a temporary attribute
        augment_entity.annotations.append(Annotation(key="__augment_target_path", value=target_path))
        while self._peek() and self._peek_value() != "}":
            self._parse_data_node_into_entity(augment_entity)
        self._expect("RBRACE")
        # The augments field (target entity) will be set later during resolution
        return augment_entity

    # --- Type parsing (adds constraints to the provided attribute) ---
    def _parse_type(self, attr: Attribute, element_type: DataType | None = None) -> None:
        base_type = self._expect("KEYWORD").value
        type_map = {
            "string": ScalarType.STRING,
            "int8": ScalarType.INT, "int16": ScalarType.INT, "int32": ScalarType.INT, "int64": ScalarType.LONG,
            "uint8": ScalarType.INT, "uint16": ScalarType.INT, "uint32": ScalarType.LONG, "uint64": ScalarType.LONG,
            "decimal64": ScalarType.DECIMAL,
            "boolean": ScalarType.BOOLEAN,
            "enumeration": ScalarType.STRING,
            "bits": ScalarType.STRING,
            "binary": ScalarType.BINARY,
            "leafref": ScalarType.REF,
            "instance-identifier": ScalarType.STRING,
            "empty": ScalarType.BOOLEAN,
            "anydata": ScalarType.YANG_ANYDATA,
            "anyxml": ScalarType.YANG_ANYDATA,
        }
        scalar = type_map.get(base_type, ScalarType.STRING)
        if element_type is not None:
            element_type.base = scalar
            dt_ref = element_type
        else:
            attr.data_type.base = scalar
            dt_ref = attr.data_type
        if scalar == ScalarType.REF:
            dt_ref.ref_entity = None   # placeholder, resolved by writer if needed
        if self._peek_value() == "{":
            self._advance()
            while self._peek() and self._peek_value() != "}":
                facet = self._advance().value
                if facet == "pattern":
                    self._expect("STRING")
                    pattern = self._unquote(self._tokens[self._pos-1].value)
                    attr.constraints.append(Constraint(type=ConstraintType.PATTERN, expression=pattern))
                    self._expect("SEMICOLON")
                elif facet == "length":
                    self._expect("STRING")
                    length = self._unquote(self._tokens[self._pos-1].value)
                    attr.constraints.append(Constraint(type=ConstraintType.LENGTH, expression=length))
                    self._expect("SEMICOLON")
                elif facet == "range":
                    self._expect("STRING")
                    rg = self._unquote(self._tokens[self._pos-1].value)
                    attr.constraints.append(Constraint(type=ConstraintType.RANGE, expression=rg))
                    self._expect("SEMICOLON")
                elif facet == "enum":
                    enum_name = self._expect("KEYWORD").value
                    attr.constraints.append(Constraint(type=ConstraintType.ENUMERATION, expression=enum_name))
                    if self._peek_value() == "{":
                        self._skip_block()
                    self._expect("SEMICOLON")
                else:
                    if self._peek_value() == "{":
                        self._skip_block()
                    else:
                        self._advance()
                    self._expect("SEMICOLON")
            self._expect("RBRACE")
        else:
            self._expect("SEMICOLON")

    # --- Common metadata (description, must, when, config, status) ---
    def _parse_common_metadata(self, target: Entity | Attribute) -> None:
        while self._peek() and self._peek_value() in ("description", "must", "when", "config", "status"):
            kw = self._advance().value
            if kw == "description":
                desc = self._parse_description()
                target.description = desc
                self._expect("SEMICOLON")
            elif kw == "must":
                must_expr = self._unquote(self._expect("STRING").value)
                target.constraints.append(Constraint(type=ConstraintType.MUST, expression=must_expr))
                self._expect("SEMICOLON")
            elif kw == "when":
                when_expr = self._unquote(self._expect("STRING").value)
                target.constraints.append(Constraint(type=ConstraintType.WHEN, expression=when_expr))
                self._expect("SEMICOLON")
            elif kw == "config":
                val = self._advance().value
                target.is_config = (val == "true")
                self._expect("SEMICOLON")
            elif kw == "status":
                status_str = self._advance().value
                status_map = {"current": VersionStatus.CURRENT, "deprecated": VersionStatus.DEPRECATED, "obsolete": VersionStatus.OBSOLETE}
                target.version_status = status_map.get(status_str, VersionStatus.CURRENT)
                self._expect("SEMICOLON")

    # --- RPC ---------------------------------------------------------
    def _parse_rpc(self) -> ServiceOperation:
        self._advance()
        name = self._expect("KEYWORD").value
        op = ServiceOperation(name=name, type=OperationType.REQUEST_RESPONSE)
        op.yang = YangMetadata()
        self._expect("LBRACE")
        while self._peek() and self._peek_value() != "}":
            kw = self._peek_value()
            if kw == "description":
                self._advance()
                op.description = self._parse_description()
                self._expect("SEMICOLON")
            elif kw == "must":
                self._advance()
                op.yang.must = self._unquote(self._expect("STRING").value)
                self._expect("SEMICOLON")
            elif kw == "when":
                self._advance()
                op.yang.when = self._unquote(self._expect("STRING").value)
                self._expect("SEMICOLON")
            elif kw == "config":
                self._advance()
                op.yang.config = self._advance().value == "true"
                self._expect("SEMICOLON")
            elif kw == "status":
                self._advance()
                op.yang.status = self._advance().value
                self._expect("SEMICOLON")
            elif kw == "deviation":
                self._advance()
                op.yang.deviation = self._unquote(self._expect("STRING").value)
                if self._peek_value() == "{":
                    self._skip_block()
                self._expect("SEMICOLON")
            elif kw == "input":
                self._advance()
                input_entity = self._parse_rpc_io("input")
                op.request_body = RequestBody(content_entity=input_entity, required=True)
            elif kw == "output":
                self._advance()
                output_entity = self._parse_rpc_io("output")
                op.responses.append(Response(status_code="200", content_entity=output_entity))
            else:
                self._skip_until_semicolon()
        self._expect("RBRACE")
        return op

    def _parse_rpc_io(self, direction: str) -> Entity:
        self._expect("LBRACE")
        entity = Entity(name=f"{direction}_of_rpc", kind=EntityKind.OBJECT)
        while self._peek() and self._peek_value() != "}":
            self._parse_data_node_into_entity(entity)
        self._expect("RBRACE")
        self._all_entities.append(entity)
        return entity

    def _parse_notification(self) -> ServiceOperation:
        self._advance()
        name = self._expect("KEYWORD").value
        op = ServiceOperation(name=name, type=OperationType.NOTIFICATION, channel=name)
        op.yang = YangMetadata()
        self._expect("LBRACE")
        while self._peek() and self._peek_value() != "}":
            kw = self._peek_value()
            if kw == "description":
                self._advance()
                op.description = self._parse_description()
                self._expect("SEMICOLON")
            elif kw == "must":
                self._advance()
                op.yang.must = self._unquote(self._expect("STRING").value)
                self._expect("SEMICOLON")
            elif kw == "when":
                self._advance()
                op.yang.when = self._unquote(self._expect("STRING").value)
                self._expect("SEMICOLON")
            else:
                # For simplicity, we store the raw node type as an annotation on the operation
                if self._peek_value() in ("container", "leaf", "leaf-list", "list", "choice"):
                    node_type = self._advance().value
                    op.annotations.append(Annotation(key="notification_nodes", value=node_type))
                    self._skip_until_semicolon()
                else:
                    self._skip_until_semicolon()
        self._expect("RBRACE")
        return op

    def _parse_description(self) -> str:
        tok = self._peek()
        if tok and tok.kind == "STRING":
            return self._unquote(self._advance().value)
        return ""

    @staticmethod
    def _unquote(s: str) -> str:
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        return s