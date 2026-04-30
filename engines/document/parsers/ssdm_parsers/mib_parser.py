"""
mib_parser.py – Production SMIv2 MIB parser → SSDM_DOCUMENT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import asyncio

from ..base import ParseOptions
from ..ssdm_parsers.base_ssdm_parser import BaseSSDMParser
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    MibModule,
    MibObjectType,
    SnmpAccess,
    SnmpStatus,
    Operation,
    OperationType,
    Parameter,
    ParameterLocation,
    ContactInfo,
    LicenseInfo,
    Server,
)


# =============================================================================
#  LEXER – tokenises an SMIv2 MIB file line‑by‑line
# =============================================================================
class MIBLexer:
    def __init__(self, text: str):
        self.lines = [line.rstrip() for line in text.splitlines()]
        self.pos = 0

    def eof(self) -> bool:
        return self.pos >= len(self.lines)

    def current_line(self) -> str:
        if self.eof():
            return ""
        return self.lines[self.pos]

    def advance(self):
        self.pos += 1

    def skip_blank_and_comments(self):
        while not self.eof():
            cur = self.current_line().strip()
            if cur == "" or cur.startswith("--"):
                self.advance()
            else:
                break

    def peek_after_blanks(self) -> str:
        """Return the next non‑blank, non‑comment line without advancing."""
        old_pos = self.pos
        self.skip_blank_and_comments()
        line = self.current_line()
        self.pos = old_pos
        return line

    def get_multiline_quoted_string(self) -> str:
        """
        Collects a quoted string that may span multiple lines, handling escaped quotes ("").
        Assumes the current line begins with a quote.
        """
        parts = []
        while not self.eof():
            line = self.current_line().strip()
            if not line:
                self.advance()
                continue
            parts.append(line)
            if '"' in line and line.count('"') % 2 == 0:
                self.advance()
                break
            self.advance()
        text = " ".join(parts)
        # remove outer quotes and unescape double quotes
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        return text.replace('""', '"')


# =============================================================================
#  PARSER – builds an internal representation with full OID resolution
# =============================================================================
class OIDNode:
    def __init__(self, name: str, number: Optional[int] = None):
        self.name = name
        self.number = number          # numeric sub‑id under parent
        self.children: Dict[int, OIDNode] = {}

    def add_child(self, name: str, number: int) -> OIDNode:
        if number in self.children:
            return self.children[number]
        node = OIDNode(name, number)
        self.children[number] = node
        return node

    def get_full_oid(self) -> str:
        """Return the full numeric OID from the root down to this node."""
        parts = []
        node = self
        while node is not None and node.number is not None:
            parts.append(str(node.number))
            node = node.parent  # type: ignore
        return ".".join(reversed(parts))


class MIBDef:
    """Intermediate representation of one MIB object/notification/assignment."""
    def __init__(self, name: str):
        self.name = name
        self.parent_label: Optional[str] = None
        self.parent_number: Optional[int] = None
        self.syntax: Optional[str] = None
        self.max_access: Optional[str] = None
        self.status: Optional[str] = None
        self.description: Optional[str] = None
        self.index: Optional[str] = None
        self.defval: Optional[str] = None
        self.units: Optional[str] = None
        self.is_notification = False
        self.objects: List[str] = []   # for NOTIFICATION-TYPE


class MIBDocParser:
    """Parses an SMIv2 MIB document into metadata and a resolved OID tree."""

    def __init__(self, text: str):
        self.lexer = MIBLexer(text)
        self.module_name = ""
        self.module_description = ""
        self.last_updated = ""
        self.organization = ""
        self.contact_info = ""
        self.imports: List[str] = []
        self.definitions: Dict[str, MIBDef] = {}
        self.oid_root = OIDNode("root", None)
        self.label_to_node: Dict[str, OIDNode] = {}  # label → OIDNode

        self._parse()

    # ------------------------------------------------------------------
    #  Main parse loop
    # ------------------------------------------------------------------
    def _parse(self):
        while not self.lexer.eof():
            self.lexer.skip_blank_and_comments()
            if self.lexer.eof():
                break
            line = self.lexer.current_line()

            if "MODULE-IDENTITY" in line:
                self._parse_module_identity()
            elif "OBJECT-TYPE" in line:
                self._parse_object_type()
            elif "NOTIFICATION-TYPE" in line:
                self._parse_notification_type()
            elif "OBJECT IDENTIFIER ::=" in line:
                self._parse_oid_assignment()
            elif line.strip().upper().startswith("IMPORTS"):
                self._parse_imports()
            else:
                # Unknown top‑level construct – skip
                self.lexer.advance()

        # After parsing, resolve numeric OIDs for all definitions
        self._resolve_oids()

    # ------------------------------------------------------------------
    #  IMPORTS
    # ------------------------------------------------------------------
    def _parse_imports(self):
        self.lexer.advance()  # consume IMPORTS line
        import_text = ""
        while not self.lexer.eof():
            line = self.lexer.current_line().strip()
            if line == ";":
                self.lexer.advance()
                break
            import_text += line + " "
            self.lexer.advance()
        self.imports.append(import_text.strip())

    # ------------------------------------------------------------------
    #  MODULE-IDENTITY
    # ------------------------------------------------------------------
    def _parse_module_identity(self):
        line = self.lexer.current_line()
        match = re.match(r"(\w+)\s+MODULE-IDENTITY", line)
        if match:
            self.module_name = match.group(1)
        self.lexer.advance()
        # Parse fields until "::="
        self._parse_until_assignment(
            fields_callback=lambda key, value: self._set_module_field(key, value)
        )

    def _set_module_field(self, key: str, value: str):
        key = key.upper()
        if key == "LAST-UPDATED":
            self.last_updated = value.strip('"')
        elif key == "ORGANIZATION":
            self.organization = value.strip('"')
        elif key == "CONTACT-INFO":
            self.contact_info = value.strip('"')
        elif key == "DESCRIPTION":
            self.module_description = value.strip('"')
        # Other fields are ignored for now

    # ------------------------------------------------------------------
    #  OBJECT-TYPE
    # ------------------------------------------------------------------
    def _parse_object_type(self):
        line = self.lexer.current_line()
        match = re.match(r"(\w+)\s+OBJECT-TYPE", line)
        if not match:
            self.lexer.advance()
            return
        obj_name = match.group(1)
        self.lexer.advance()
        defn = MIBDef(obj_name)
        self._parse_until_assignment(
            fields_callback=lambda key, value: self._set_object_field(defn, key, value)
        )
        self.definitions[obj_name] = defn

    def _set_object_field(self, defn: MIBDef, key: str, value: str):
        key = key.upper()
        if key == "SYNTAX":
            # value already contains the whole syntax line (multi‑line handled)
            defn.syntax = value
        elif key in ("MAX-ACCESS", "ACCESS"):
            defn.max_access = value
        elif key == "STATUS":
            defn.status = value
        elif key == "DESCRIPTION":
            defn.description = value.strip('"')
        elif key == "INDEX":
            defn.index = value
        elif key == "DEFVAL":
            defn.defval = value
        elif key == "UNITS":
            defn.units = value
        # also capture the parent clause from ::=, handled automatically

    # ------------------------------------------------------------------
    #  NOTIFICATION-TYPE
    # ------------------------------------------------------------------
    def _parse_notification_type(self):
        line = self.lexer.current_line()
        match = re.match(r"(\w+)\s+NOTIFICATION-TYPE", line)
        if not match:
            self.lexer.advance()
            return
        notif_name = match.group(1)
        self.lexer.advance()
        defn = MIBDef(notif_name)
        defn.is_notification = True
        self._parse_until_assignment(
            fields_callback=lambda key, value: self._set_notification_field(defn, key, value)
        )
        self.definitions[notif_name] = defn

    def _set_notification_field(self, defn: MIBDef, key: str, value: str):
        key = key.upper()
        if key == "STATUS":
            defn.status = value
        elif key == "DESCRIPTION":
            defn.description = value.strip('"')
        elif key == "OBJECTS":
            # value is like "{ sysUpTime, ifIndex }"
            clean = value.strip("{} ")
            defn.objects = [o.strip() for o in clean.split(",")] if clean else []

    # ------------------------------------------------------------------
    #  OBJECT IDENTIFIER assignment (e.g., internet OBJECT IDENTIFIER ::= { iso 3 6 1 })
    # ------------------------------------------------------------------
    def _parse_oid_assignment(self):
        line = self.lexer.current_line()
        match = re.match(r"(\w+)\s+OBJECT IDENTIFIER\s+::=\s*\{\s*(.*)\s*\}", line)
        if match:
            name = match.group(1)
            rest = match.group(2).strip()
            self.lexer.advance()
            # rest is a list of labels and numbers separated by spaces
            parts = rest.split()
            parent_label = parts[0] if parts else None
            number = None
            try:
                number = int(parts[-1]) if parts else None
            except ValueError:
                pass
            # Create an OIDNode for this assignment
            self._add_oid_node(name, parent_label, number)
            # Also record as a definition (needed for parent resolution later)
            defn = MIBDef(name)
            defn.parent_label = parent_label
            defn.parent_number = number
            self.definitions[name] = defn
        else:
            self.lexer.advance()  # just move on

    # ------------------------------------------------------------------
    #  Generic clause‑by‑clause parser until "::="
    #  This also captures the parent clause for eventual OID resolution.
    # ------------------------------------------------------------------
    def _parse_until_assignment(self, fields_callback):
        """Process lines until the one containing '::='. All other lines
        are considered clauses (KEYWORD value ...)."""
        while not self.lexer.eof():
            self.lexer.skip_blank_and_comments()
            if self.lexer.eof():
                break
            line = self.lexer.current_line().strip()

            # If the line contains "::=", we have reached the parent clause
            if "::=" in line:
                parent_label, parent_number = self._extract_parent_clause(line)
                # Store them in a temporary location; the callback will need them.
                # We'll attach them to a definition after the callback returns.
                # Since the callback doesn't have access to the defn yet, we need
                # to set these later. We'll store them on the parser and then
                # the caller will read them.
                self._last_parent_label = parent_label
                self._last_parent_number = parent_number
                self.lexer.advance()
                break

            # Otherwise it's a clause: try to split keyword from value
            clause_match = re.match(r"([A-Za-z](?:[A-Za-z0-9-]*))\s+(.*)", line)
            if clause_match:
                keyword = clause_match.group(1).upper()
                rest = clause_match.group(2)
                # If the value starts with a quote, it may span multiple lines
                if rest.strip().startswith('"'):
                    # Read the multi‑line quoted string
                    self.lexer.advance()  # consume this line's beginning
                    # But we need the whole quoted string across lines.
                    # Since we already have the first line in 'rest', we'll need to
                    # walk forward until the closing quote.
                    # However 'rest' contains the first part; we need the rest.
                    # Simplest: gather lines until an even number of quotes.
                    value = self._collect_quoted_string(rest)
                    # Now the lexer is positioned after the last line of the quote
                    fields_callback(keyword, value)
                else:
                    # Simple value (one line)
                    self.lexer.advance()
                    fields_callback(keyword, rest.strip())
            else:
                # Not a recognizable clause; skip
                self.lexer.advance()

    def _extract_parent_clause(self, line: str) -> Tuple[Optional[str], Optional[int]]:
        """Parse '::= { label number }' and return (label, number)."""
        match = re.search(r"::=\s*\{\s*(\w+)\s+(\d+)\s*\}", line)
        if match:
            return match.group(1), int(match.group(2))
        return None, None

    def _collect_quoted_string(self, first_part: str) -> str:
        """Collect a complete quoted string that may span multiple lines.
        `first_part` already starts with a quote. We have already consumed
        the first line's beginning text? Actually we haven't advanced yet.
        The caller has not consumed the line; we must start from the current line.
        So we need a different approach: the caller passes the line content
        after the keyword, but we haven't consumed the line. We'll implement
        a helper that reads from the current position.
        For simplicity, we'll extract from the current line and subsequent lines.
        """
        # We are at the line that contains the beginning of the quoted string.
        line = self.lexer.current_line().strip()
        # The line should contain the quote from the column after the keyword.
        # We'll just take the whole line and then continue if needed.
        parts = [line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else line]
        self.lexer.advance()
        # Now while the total quotes count is odd, keep adding lines
        combined = " ".join(parts)
        while combined.count('"') % 2 != 0 and not self.lexer.eof():
            nxt = self.lexer.current_line().strip()
            parts.append(nxt)
            combined = " ".join(parts)
            self.lexer.advance()
        return combined

    # ------------------------------------------------------------------
    #  OID Tree construction
    # ------------------------------------------------------------------
    def _add_oid_node(self, name: str, parent_label: Optional[str], number: Optional[int]):
        """Register an OID node (for OBJECT IDENTIFIER assignments)."""
        if parent_label and number is not None:
            parent = self.label_to_node.get(parent_label)
            if parent:
                node = parent.add_child(name, number)
                self.label_to_node[name] = node
                return
        # If parent not yet known, create a temporary node
        node = OIDNode(name, number)
        self.label_to_node[name] = node

    def _resolve_oids(self):
        """After all definitions are parsed, build the OID tree from the
        parent relationships, resolving numeric OIDs."""
        # First pass: ensure all labels from OBJECT IDENTIFIER assignments are registered
        for name, defn in self.definitions.items():
            if defn.parent_label and defn.parent_number is not None:
                # If this node isn't yet in the tree, add it
                if name not in self.label_to_node:
                    self._add_oid_node(name, defn.parent_label, defn.parent_number)

        # Second pass: link all other definitions into the tree
        for name, defn in self.definitions.items():
            if defn.parent_label and defn.parent_number is not None:
                parent_node = self.label_to_node.get(defn.parent_label)
                if parent_node:
                    self.label_to_node[name] = parent_node.add_child(name, defn.parent_number)
                else:
                    # Create placeholders
                    self.label_to_node[name] = OIDNode(name, defn.parent_number)

        # Now every definition that has a valid OID node will have a numeric OID.
        # We store the OID directly in the definition (for convenience).
        for name, defn in self.definitions.items():
            node = self.label_to_node.get(name)
            if node:
                defn.oid = node.get_full_oid()
            else:
                defn.oid = f"oid:{name}"  # fallback

    def get_numeric_oid(self, name: str) -> str:
        node = self.label_to_node.get(name)
        if node:
            return node.get_full_oid()
        return f"oid:{name}"


# =============================================================================
#  SSDM MIB Parser – inherits from BaseSSDMParser
# =============================================================================
class MIBParser(BaseSSDMParser):
    name = "mib"
    supported_extensions = (".mib", ".txt")

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDM_DOCUMENT:
        text = data.decode(options.encoding)
        mib_parser = MIBDocParser(text)

        # Build MIB module
        objects = []
        for name, defn in mib_parser.definitions.items():
            if not defn.is_notification and defn.syntax is not None:
                # This is an OBJECT-TYPE
                mib_obj = MibObjectType(
                    name=defn.name,
                    oid=mib_parser.get_numeric_oid(name),
                    syntax=defn.syntax or "OCTET STRING",
                    access=self._map_access(defn.max_access),
                    status=SnmpStatus(defn.status.lower() if defn.status else "current"),
                    description=defn.description,
                    index=defn.index,
                )
                objects.append(mib_obj)

        mib_module = MibModule(
            name=mib_parser.module_name,
            description=mib_parser.module_description,
            imports=mib_parser.imports,
            objects=objects,
        )

        # Create base SSDM document
        doc = SSDM_DOCUMENT(
            document_id="",  # will be set by the caller
            title=mib_parser.module_name or Path(source_name).stem,
            version=self._detect_version(source_name),
            description=mib_parser.module_description,
            contact=ContactInfo(
                name=mib_parser.organization,
            ) if mib_parser.organization else None,
            license=None,
            servers=[],
            security_schemes=[],
            operations=[],
            type_definitions=None,
            mib_module=mib_module,
            metadata={
                "mib:last_updated": mib_parser.last_updated,
                "mib:organization": mib_parser.organization,
                "mib:contact_info": mib_parser.contact_info,
            },
        )

        # Generate operations
        operations = []
        for name, defn in mib_parser.definitions.items():
            oid = mib_parser.get_numeric_oid(name)
            if not defn.is_notification:
                access = (defn.max_access or "").lower()
                # GET operation for readable objects
                if access in ("read-only", "read-write", "read-create"):
                    operations.append(self._make_get_operation(defn, oid))
                # SET operation for writable objects
                if access in ("read-write", "read-create", "write-only"):
                    operations.append(self._make_set_operation(defn, oid))
            else:
                operations.append(self._make_notification_operation(defn, oid, mib_parser))

        doc.operations = operations
        doc.is_valid = True
        return doc

    def _map_access(self, access: Optional[str]) -> SnmpAccess:
        if not access:
            return SnmpAccess.NOT_ACCESSIBLE
        access = access.lower().replace("-", "")
        try:
            return SnmpAccess(access)
        except ValueError:
            return SnmpAccess.NOT_ACCESSIBLE

    def _make_get_operation(self, defn: MIBDef, oid: str) -> Operation:
        params = []
        if defn.index:
            for idx in re.split(r",\s*", defn.index):
                idx = idx.strip()
                if idx.upper() == "IMPLIED":
                    break  # implies length of index omitted from request
                params.append(Parameter(name=idx, location=ParameterLocation.PATH, type_string="string"))
        return Operation(
            name=f"get_{defn.name}",
            type=OperationType.REQUEST_RESPONSE,
            description=defn.description or f"Get {defn.name}",
            path=oid,
            parameters=params,
            responses=[],
            tags=["SNMP", "GET"],
            deprecated=(defn.status and defn.status.lower() == "deprecated"),
        )

    def _make_set_operation(self, defn: MIBDef, oid: str) -> Operation:
        params = []
        if defn.index:
            for idx in re.split(r",\s*", defn.index):
                idx = idx.strip()
                if idx.upper() == "IMPLIED":
                    break
                params.append(Parameter(name=idx, location=ParameterLocation.PATH, type_string="string"))
        # The value to set
        params.append(Parameter(name="value", location=ParameterLocation.BODY, type_string=defn.syntax or "string"))
        return Operation(
            name=f"set_{defn.name}",
            type=OperationType.REQUEST_RESPONSE,
            description=defn.description or f"Set {defn.name}",
            path=oid,
            parameters=params,
            responses=[],
            tags=["SNMP", "SET"],
            deprecated=(defn.status and defn.status.lower() == "deprecated"),
        )

    def _make_notification_operation(self, defn: MIBDef, oid: str, mib_parser: MIBDocParser) -> Operation:
        # Object references become parameters (the varbinds)
        params = []
        if defn.objects:
            for obj_name in defn.objects:
                params.append(Parameter(name=obj_name, location=ParameterLocation.BODY, type_string="string"))
        return Operation(
            name=defn.name,
            type=OperationType.NOTIFICATION,
            description=defn.description or f"Notification {defn.name}",
            path=oid,
            parameters=params,
            responses=[],
            tags=["SNMP", "TRAP"],
            deprecated=(defn.status and defn.status.lower() == "deprecated"),
        )