# engines/document/writers/spreadsheet_writer/xlsx/shared_strings_writer.py
"""
Shared strings table writer for XLSX.
Serialises the shared strings collection into sharedStrings.xml.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET


from .const import XML_NAMESPACES
from ..base import ESDMBaseWriter


class SharedStringsWriter:
    """Writes sharedStrings.xml from the parent writer's shared strings cache."""

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer

    def write(self) -> str:
        """
        Generate sharedStrings.xml content.
        Returns the XML as a string, with proper declaration and namespace.
        """
        strings = self._parent._shared_strings
        if not strings:
            # Excel requires at least an empty sharedStrings.xml
            return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="0" uniqueCount="0" />'''

        root = ET.Element('sst', {
            'xmlns': XML_NAMESPACES[''],
            'count': str(len(strings)),
            'uniqueCount': str(len(strings))
        })

        for s in strings:
            si = ET.SubElement(root, 'si')
            t = ET.SubElement(si, 't')
            t.text = s
            # Optional: if string contains newlines or leading/trailing spaces, set xml:space="preserve"
            if '\n' in s or s.startswith(' ') or s.endswith(' '):
                t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

        return ET.tostring(root, encoding='unicode', xml_declaration=True)

