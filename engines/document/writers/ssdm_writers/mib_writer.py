# engines/document/writers/ssdm_writers/mib_writer.py
"""
MIB (SNMP Management Information Base) Writer – serialises an SSDM_DOCUMENT
containing an MIB module into text MIB format.

Uses the typed MibModule and MibObjectType fields; no annotations are needed.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, List, cast

from .base_ssdm_writer import BaseSSDMWriter, SSDMWriteOptions
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    MibModule,
    MibObjectType,
)
from ...models.base import BaseDocument


class MIBWriter(BaseSSDMWriter):
    """Serialises an SSDM_DOCUMENT to an SNMP MIB file."""

    name = "mib"
    supported_extensions = (".mib",)

    def __init__(self, options: Optional[SSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, document: SSDM_DOCUMENT) -> bytes:
        module = document.mib_module
        if not module:
            return b""

        lines: List[str] = []
        lines.append(f"{self._quote(module.name)} DEFINITIONS ::= BEGIN")
        lines.append("")

        # Imports
        if module.imports:
            lines.append("IMPORTS")
            for imp in module.imports:
                lines.append(f"    {imp}")
            lines.append(";")
            lines.append("")

        # Objects
        for obj in module.objects:
            self._write_object(lines, obj)

        lines.append("END")
        return "\n".join(lines).encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Write a single MIB object ──────────────────────────────────
    def _write_object(self, lines: List[str], obj: MibObjectType) -> None:
        lines.append(f"{obj.name} OBJECT-TYPE")
        lines.append(f"    SYNTAX  {obj.syntax}")
        lines.append(f"    ACCESS  {obj.access.value}")
        lines.append(f"    STATUS  {obj.status.value}")
        if obj.description:
            lines.append(f'    DESCRIPTION  "{obj.description}"')
        if obj.index:
            lines.append(f"    INDEX  {{ {obj.index} }}")
        # OID assignment
        lines.append(f"    ::= {{ {obj.oid} }}")
        lines.append("")

    @staticmethod
    def _quote(name: str) -> str:
        """Escape a MIB identifier if needed (simplified)."""
        if any(ch in name for ch in ' -{}[]'):
            return f'"{name}"'
        return name