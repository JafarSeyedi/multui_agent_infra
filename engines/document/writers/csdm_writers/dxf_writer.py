# engines/document/writers/csdm_writers/dxf_writer.py
"""
DXF writer for CSDM (CAD Standard Definition Model).
Converts a CSDMDocument to DXF format.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.csdm_core import CSDMDocument
from .base import CSDMBaseWriter
from .base import CSDMWriteOptions


class DXFWriter(CSDMBaseWriter):
    """
    Writer for DXF (Drawing Exchange Format) files.
    Exports CSDM document to ASCII DXF format.
    """

    def __init__(self, options: CSDMWriteOptions | None = None):
        super().__init__(options)

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """Yield DXF content in chunks."""
        doc = self._extract_csdm_data(document)
        content = await self._write_dxf(doc)
        # Yield in chunks for large files
        chunk_size = 64 * 1024  # 64KB chunks
        for i in range(0, len(content), chunk_size):
            yield content[i:i+chunk_size].encode('utf-8')

    async def write(self, document: BaseDocument) -> bytes:
        """Return full DXF content as bytes."""
        doc = self._extract_csdm_data(document)
        content = await self._write_dxf(doc)
        return content.encode('utf-8')

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None
    ) -> None:
        """Write DXF directly to a file."""
        doc = self._extract_csdm_data(document)
        content = await self._write_dxf(doc)
        target.write_text(content, encoding='utf-8')

    async def _write_dxf(self, doc: CSDMDocument) -> str:
        """Generate DXF content from CSDM document."""
        lines = []
        
        # HEADER section
        lines.extend(self._write_header_section(doc))
        
        # TABLES section
        lines.extend(self._write_tables_section(doc))
        
        # BLOCKS section
        lines.extend(self._write_blocks_section(doc))
        
        # ENTITIES section
        lines.extend(self._write_entities_section(doc))
        
        # OBJECTS section
        lines.extend(self._write_objects_section(doc))
        
        # END OF FILE
        lines.append("  0")
        lines.append("ENDSEC")
        lines.append("  0")
        lines.append("EOF")
        
        return "\n".join(lines)

    def _write_header_section(self, doc: CSDMDocument) -> list[str]:
        """Write DXF HEADER section."""
        lines = []
        lines.append("  0")
        lines.append("SECTION")
        lines.append("  2")
        lines.append("HEADER")
        
        # Header variables
        lines.append("  9")
        lines.append("$ACADVER")
        lines.append("  1")
        lines.append("AC1027")  # AutoCAD 2018+
        
        lines.append("  9")
        lines.append("$INSUNITS")
        lines.append("  70")
        lines.append("6")  # Millimeters
        
        lines.append("  0")
        lines.append("ENDSEC")
        return lines

    def _write_tables_section(self, doc: CSDMDocument) -> list[str]:
        """Write DXF TABLES section."""
        lines = []
        lines.append("  0")
        lines.append("SECTION")
        lines.append("  2")
        lines.append("TABLES")
        
        # LTYPE table
        lines.append("  0")
        lines.append("TABLE")
        lines.append("  2")
        lines.append("LTYPE")
        lines.append("  70")
        lines.append("1")  # Number of linetypes
        # Continuous linetype (default)
        lines.append("  0")
        lines.append("LTYPE")
        lines.append("  2")
        lines.append("CONTINUOUS")
        lines.append("  70")
        lines.append("64")
        lines.append("  3")
        lines.append("Solid line")
        lines.append("  72")
        lines.append("65")
        lines.append("  73")
        lines.append("0")
        lines.append("  40")
        lines.append("0.0")
        lines.append("  0")
        lines.append("ENDTAB")
        
        # LAYER table
        lines.append("  0")
        lines.append("TABLE")
        lines.append("  2")
        lines.append("LAYER")
        layer_count = len(doc.tables.layers) if doc.tables and doc.tables.layers else 1
        lines.append("  70")
        lines.append(str(layer_count))
        
        # Default layer
        lines.append("  0")
        lines.append("LAYER")
        lines.append("  2")
        lines.append("0")
        lines.append("  70")
        lines.append("0")
        lines.append("  62")
        lines.append("7")  # White/black
        lines.append("  6")
        lines.append("CONTINUOUS")
        
        # Custom layers
        if doc.tables and doc.tables.layers:
            for layer in doc.tables.layers:
                lines.append("  0")
                lines.append("LAYER")
                lines.append("  2")
                lines.append(self._normalize_layer_name(layer.name))
                lines.append("  70")
                lines.append(str(layer.flags))
                lines.append("  62")
                lines.append(str(layer.color))
                lines.append("  6")
                lines.append(layer.linetype or "CONTINUOUS")
        
        lines.append("  0")
        lines.append("ENDTAB")
        
        # Other tables (simplified for now)
        # STYLE table
        lines.append("  0")
        lines.append("TABLE")
        lines.append("  2")
        lines.append("STYLE")
        lines.append("  70")
        lines.append("1")  # Standard style
        lines.append("  0")
        lines.append("STYLE")
        lines.append("  2")
        lines.append("STANDARD")
        lines.append("  70")
        lines.append("0")
        lines.append("  40")
        lines.append("0.0")
        lines.append("  41")
        lines.append("1.0")
        lines.append("  50")
        lines.append("0.0")
        lines.append("  71")
        lines.append("0")
        lines.append("  42")
        lines.append("0.2")
        lines.append("  3")
        lines.append("txt")
        lines.append("  4")
        lines.append("")
        lines.append("  0")
        lines.append("ENDTAB")
        
        lines.append("  0")
        lines.append("ENDSEC")
        return lines

    def _write_blocks_section(self, doc: CSDMDocument) -> list[str]:
        """Write DXF BLOCKS section."""
        lines = []
        lines.append("  0")
        lines.append("SECTION")
        lines.append("  2")
        lines.append("BLOCKS")
        
        # Model space block
        lines.append("  0")
        lines.append("BLOCK")
        lines.append("  8")
        lines.append("0")
        lines.append("  2")
        lines.append("*Model_Space")
        lines.append("  70")
        lines.append("0")
        lines.append(" 10")
        lines.append("0.0")
        lines.append(" 20")
        lines.append("0.0")
        lines.append(" 30")
        lines.append("0.0")
        lines.append("  3")
        lines.append("")
        lines.append("  1")
        lines.append("")
        lines.append("  0")
        lines.append("ENDBLK")
        
        # Paper space block
        lines.append("  0")
        lines.append("BLOCK")
        lines.append("  8")
        lines.append("0")
        lines.append("  2")
        lines.append("*Paper_Space")
        lines.append("  70")
        lines.append("0")
        lines.append(" 10")
        lines.append("0.0")
        lines.append(" 20")
        lines.append("0.0")
        lines.append(" 30")
        lines.append("0.0")
        lines.append("  3")
        lines.append("")
        lines.append("  1")
        lines.append("")
        lines.append("  0")
        lines.append("ENDBLK")
        
        lines.append("  0")
        lines.append("ENDSEC")
        return lines

    def _write_entities_section(self, doc: CSDMDocument) -> list[str]:
        """Write DXF ENTITIES section."""
        lines = []
        lines.append("  0")
        lines.append("SECTION")
        lines.append("  2")
        lines.append("ENTITIES")
        
        # Write entities from CSDM document
        if doc.entities:
            for entity in doc.entities:
                lines.extend(self._write_entity(entity))
        
        lines.append("  0")
        lines.append("ENDSEC")
        return lines

    def _write_entity(self, entity) -> list[str]:
        """Write a single entity to DXF format."""
        lines = []
        
        # Common entity properties
        lines.append("  0")
        # Determine entity type from CSDM entity
        if hasattr(entity, 'entity_type'):
            lines.append("  8")  # Layer
            lines.append(self._normalize_layer_name(getattr(entity, 'layer', '0')))
            lines.append("  6")   # Linetype
            lines.append("CONTINUOUS")  # Default
            
            # Handle specific entity types
            if entity.entity_type == "LINE":
                lines.append("LINE")
                lines.append(" 10")  # Start X
                lines.append(self._format_coordinate(getattr(entity, 'start', (0,0,0))[0]))
                lines.append(" 20")  # Start Y
                lines.append(self._format_coordinate(getattr(entity, 'start', (0,0,0))[1]))
                lines.append(" 30")  # Start Z
                lines.append(self._format_coordinate(getattr(entity, 'start', (0,0,0))[2]))
                lines.append(" 11")  # End X
                lines.append(self._format_coordinate(getattr(entity, 'end', (0,0,0))[0]))
                lines.append(" 21")  # End Y
                lines.append(self._format_coordinate(getattr(entity, 'end', (0,0,0))[1]))
                lines.append(" 31")  # End Z
                lines.append(self._format_coordinate(getattr(entity, 'end', (0,0,0))[2]))
                
            elif entity.entity_type == "CIRCLE":
                lines.append("CIRCLE")
                lines.append(" 10")  # Center X
                lines.append(self._format_coordinate(getattr(entity, 'center', (0,0,0))[0]))
                lines.append(" 20")  # Center Y
                lines.append(self._format_coordinate(getattr(entity, 'center', (0,0,0))[1]))
                lines.append(" 30")  # Center Z
                lines.append(self._format_coordinate(getattr(entity, 'center', (0,0,0))[2]))
                lines.append(" 40")  # Radius
                lines.append(self._format_coordinate(getattr(entity, 'radius', 0.0)))
                
            # Add more entity types as needed...
            else:
                # Generic entity fallback
                lines.append("POINT")  # Fallback to point
                lines.append(" 10")  # X
                lines.append(self._format_coordinate(getattr(entity, 'insert', (0,0,0))[0] if hasattr(entity, 'insert') else 0))
                lines.append(" 20")  # Y
                lines.append(self._format_coordinate(getattr(entity, 'insert', (0,0,0))[1] if hasattr(entity, 'insert') else 0))
                lines.append(" 30")  # Z
                lines.append(self._format_coordinate(getattr(entity, 'insert', (0,0,0))[2] if hasattr(entity, 'insert') else 0))
        
        return lines

    def _write_objects_section(self, doc: CSDMDocument) -> list[str]:
        """Write DXF OBJECTS section."""
        lines = []
        lines.append("  0")
        lines.append("SECTION")
        lines.append("  2")
        lines.append("OBJECTS")
        
        # Write dictionary objects if they exist
        if doc.objects:
            for obj_dict in (doc.objects.dictionaries, doc.objects.groups,
                             doc.objects.layouts, doc.objects.materials,
                             doc.objects.mleader_styles, doc.objects.table_styles,
                             doc.objects.image_defs, doc.objects.underlay_defs,
                             doc.objects.xrecords):
                for obj in obj_dict.values():
                    lines.extend(self._write_object(obj))
            for robj in doc.objects.reactors:
                lines.extend(self._write_object(robj))
        
        lines.append("  0")
        lines.append("ENDSEC")
        return lines

    def _write_object(self, obj) -> list[str]:
        """Write a single object to DXF format."""
        lines = []
        
        # Generic object writing
        lines.append("  0")
        lines.append("OBJECT")
        lines.append("  8")
        lines.append("0")  # Layer
        lines.append(" 100")  # Marker for DXF object
        lines.append("AcDbDictionary")
        lines.append("  2")
        lines.append(getattr(obj, 'name', 'UNKNOWN'))
        lines.append(" 70")
        lines.append("0")  # Dictionary flags
        lines.append("  3")
        lines.append(str(len(getattr(obj, 'entries', {}))))  # Number of entries
        
        return lines

    def get_supported_media_types(self) -> list[str]:
        """Get list of supported media types."""
        return ["image/vnd.dxf"]

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return [".dxf"]