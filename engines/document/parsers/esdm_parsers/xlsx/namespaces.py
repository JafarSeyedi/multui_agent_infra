# engines/document/parsers/spreadsheet_parser/xlsx/namespaces.py
"""Namespace constants for SpreadsheetML (Office Open XML)."""

NS = {
    "": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "x14ac": "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac",
    "x15ac": "http://schemas.microsoft.com/office/spreadsheetml/2010/11/ac",
    "x14": "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main",
    "x15": "http://schemas.microsoft.com/office/spreadsheetml/2010/11/main",
}

# Alias for main namespace
MAIN = NS[""]
REL = NS["r"]
