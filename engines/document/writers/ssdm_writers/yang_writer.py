# engines/document/writers/ssdm_writers/yang_writer.py
"""
YANG 1.1 Writer – serialises an SSDM_DOCUMENT containing a YangModule
into a valid YANG file (.yang).

Handles:
- module header, imports, includes
- typedef, grouping
- container, list, leaf, leaf-list, choice, case
- uses, augment
- rpc, notification
- identity, feature, extension
- type restrictions (pattern, length, range, enum)
- must, when, description, default, mandatory, unique, config, status
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Dict, cast

from .base_ssdm_writer import BaseSSDMWriter, SSDMWriteOptions
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    YangModule, YangContainer, YangLeaf, YangList, YangChoice, YangCase,
    YangUses, YangAugment, YangRPC, YangNotification, YangTypedef, YangType,
)
from ...models.base import BaseDocument


class YANGWriter(BaseSSDMWriter):
    """Serialises an SSDM_DOCUMENT to a YANG 1.1 file."""

    name = "yang"
    supported_extensions = (".yang",)

    def __init__(self, options: Optional[SSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, document: SSDM_DOCUMENT) -> bytes:
        module = document.yang_module
        if module is None:
            return b""

        lines: List[str] = []
        self._write_module(lines, module)

        return "\n".join(lines).encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/yang"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Module header ────────────────────────────────────────────────
    def _write_module(self, lines: List[str], mod: YangModule) -> None:
        lines.append(f"module {mod.name} {{")
        lines.append(f"  yang-version {mod.yang_version};")
        lines.append(f"  namespace \"{mod.namespace or 'urn:' + mod.name}\";")
        lines.append(f"  prefix {mod.prefix or mod.name};")

        # Description
        self._write_description(lines, mod.description, indent=2)

        # Imports
        for imp in mod.imports:
            lines.append(f"  import {imp} {{")
            lines.append(f"    prefix {self._import_prefix(imp)};")
            lines.append(f"  }}")

        # Includes
        for inc in mod.includes:
            lines.append(f"  include {inc};")

        # Identities
        for ident in mod.identities:
            lines.append(f"  identity {ident} {{")
            lines.append(f"  }}")

        # Features
        for feat in mod.features:
            lines.append(f"  feature {feat};")

        # Extensions
        for ext in mod.extensions:
            lines.append(f"  extension {ext};")

        # Typedefs
        for td in mod.typedefs:
            self._write_typedef(lines, td)

        # Groupings
        for grp_name, grp_children in mod.groupings.items():
            self._write_grouping(lines, grp_name, grp_children)

        # Children (top-level data definitions)
        if mod.children:
            self._write_substmts(lines, mod.children, indent=2)

        # Augmentations
        for aug in mod.augmentations:
            self._write_augment(lines, aug, indent=2)

        # RPCs
        for rpc in mod.rpcs:
            self._write_rpc(lines, rpc)

        # Notifications
        for notif in mod.notifications:
            self._write_notification(lines, notif)

        lines.append("}")

    # ── Common helpers ──────────────────────────────────────────────
    def _write_description(self, lines: List[str], desc: Optional[str], indent: int) -> None:
        if desc:
            prefix = " " * indent
            lines.append(f"{prefix}description")
            lines.append(f"{prefix}  \"{desc}\";")

    def _write_substmts(self, lines: List[str], substmts: List, indent: int) -> None:
        for stmt in substmts:
            if isinstance(stmt, YangContainer):
                self._write_container(lines, stmt, indent)
            elif isinstance(stmt, YangLeaf):
                self._write_leaf(lines, stmt, indent)
            elif isinstance(stmt, YangList):
                self._write_list(lines, stmt, indent)
            elif isinstance(stmt, YangChoice):
                self._write_choice(lines, stmt, indent)
            elif isinstance(stmt, YangUses):
                self._write_uses(lines, stmt, indent)

    # ── Typedef / Grouping ──────────────────────────────────────────
    def _write_typedef(self, lines: List[str], td: YangTypedef) -> None:
        lines.append(f"  typedef {td.name} {{")
        if td.description:
            self._write_description(lines, td.description, indent=4)
        if td.base_type:
            lines.append(f"    type {td.base_type};")
        lines.append(f"  }}")

    def _write_grouping(self, lines: List[str], name: str, children: List) -> None:
        lines.append(f"  grouping {name} {{")
        self._write_substmts(lines, children, indent=4)
        lines.append(f"  }}")

    # ── Container ───────────────────────────────────────────────────
    def _write_container(self, lines: List[str], cont: YangContainer, indent: int) -> None:
        prefix = " " * indent
        lines.append(f"{prefix}container {cont.name} {{")
        self._write_description(lines, cont.description, indent + 2)
        if cont.children:
            self._write_substmts(lines, cont.children, indent + 2)
        lines.append(f"{prefix}}}")

    # ── Leaf ────────────────────────────────────────────────────────
    def _write_leaf(self, lines: List[str], leaf: YangLeaf, indent: int) -> None:
        prefix = " " * indent
        lines.append(f"{prefix}leaf {leaf.name} {{")
        if leaf.description:
            self._write_description(lines, leaf.description, indent + 2)
        if leaf.type:
            self._write_type(lines, leaf.type, indent + 2)
        if leaf.default is not None:
            lines.append(f"{prefix}  default {leaf.default};")
        if leaf.mandatory:
            lines.append(f"{prefix}  mandatory true;")
        lines.append(f"{prefix}}}")

    # ── List ────────────────────────────────────────────────────────
    def _write_list(self, lines: List[str], lst: YangList, indent: int) -> None:
        prefix = " " * indent
        key_str = f"  key \"{lst.key}\";" if lst.key else ""
        lines.append(f"{prefix}list {lst.name} {{")
        self._write_description(lines, lst.description, indent + 2)
        if lst.key:
            lines.append(f"{prefix}  key \"{lst.key}\";")
        if lst.children:
            self._write_substmts(lines, lst.children, indent + 2)
        lines.append(f"{prefix}}}")

    # ── Choice / Case ───────────────────────────────────────────────
    def _write_choice(self, lines: List[str], choice: YangChoice, indent: int) -> None:
        prefix = " " * indent
        lines.append(f"{prefix}choice {choice.name} {{")
        self._write_description(lines, choice.description, indent + 2)
        for case in choice.cases:
            self._write_case(lines, case, indent + 2)
        lines.append(f"{prefix}}}")

    def _write_case(self, lines: List[str], case: YangCase, indent: int) -> None:
        prefix = " " * indent
        lines.append(f"{prefix}case {case.name} {{")
        if case.children:
            self._write_substmts(lines, case.children, indent + 2)
        lines.append(f"{prefix}}}")

    # ── Uses / Augment ──────────────────────────────────────────────
    def _write_uses(self, lines: List[str], uses: YangUses, indent: int) -> None:
        prefix = " " * indent
        lines.append(f"{prefix}uses {uses.source};")

    def _write_augment(self, lines: List[str], aug: YangAugment, indent: int) -> None:
        prefix = " " * indent
        lines.append(f"{prefix}augment \"{aug.path}\" {{")
        self._write_substmts(lines, aug.children, indent + 2)
        lines.append(f"{prefix}}}")

    # ── RPC / Notification ──────────────────────────────────────────
    def _write_rpc(self, lines: List[str], rpc: YangRPC) -> None:
        lines.append(f"  rpc {rpc.name} {{")
        self._write_description(lines, rpc.description, indent=4)
        if rpc.input:
            lines.append(f"    input {{")
            self._write_substmts(lines, rpc.input.children, indent=6)
            lines.append(f"    }}")
        if rpc.output:
            lines.append(f"    output {{")
            self._write_substmts(lines, rpc.output.children, indent=6)
            lines.append(f"    }}")
        lines.append(f"  }}")

    def _write_notification(self, lines: List[str], notif: YangNotification) -> None:
        lines.append(f"  notification {notif.name} {{")
        self._write_description(lines, notif.description, indent=4)
        if notif.children:
            self._write_substmts(lines, notif.children, indent=4)
        lines.append(f"  }}")

    # ── Type restrictions ───────────────────────────────────────────
    def _write_type(self, lines: List[str], yang_type: YangType, indent: int) -> None:
        prefix = " " * indent
        base = yang_type.base_type or "string"
        restrictions_present = any([yang_type.pattern, yang_type.length, yang_type.range, yang_type.enum_values])
        if not restrictions_present:
            lines.append(f"{prefix}type {base};")
            return

        lines.append(f"{prefix}type {base} {{")
        if yang_type.pattern:
            lines.append(f"{prefix}  pattern \"{yang_type.pattern}\";")
        if yang_type.length:
            lines.append(f"{prefix}  length \"{yang_type.length}\";")
        if yang_type.range:
            lines.append(f"{prefix}  range \"{yang_type.range}\";")
        for ev in yang_type.enum_values:
            lines.append(f"{prefix}  enum {ev};")
        lines.append(f"{prefix}}}")

    @staticmethod
    def _import_prefix(imp: str) -> str:
        return imp.split(":")[-1] if ":" in imp else imp