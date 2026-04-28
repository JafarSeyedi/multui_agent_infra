# engines/document/writers/spreadsheet_writer/xlsx/extra_writers.py
"""
Writers for:
- [Content_Types].xml
- .rels files (workbook, worksheet)
- Legacy and threaded comments
- Hyperlinks + relationships
- Placeholder for drawings/charts
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, List, Tuple, Optional, Dict, Any

from .const import XML_NAMESPACES

if TYPE_CHECKING:
    from ....models.esdm_models import Workbook, Hyperlink, Comment, ThreadedComment, CommentText
    from ..base import ESDMBaseWriter


class ContentTypesWriter:
    """Generates [Content_Types].xml with overrides for all parts."""

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer

    def write(self, workbook: Workbook) -> str:
        overrides = [
            ('/xl/workbook.xml', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'),
            ('/xl/styles.xml', 'application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml'),
            ('/xl/sharedStrings.xml', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml'),
        ]
        # Worksheets
        for i in range(1, len(workbook.sheets) + 1):
            overrides.append((f'/xl/worksheets/sheet{i}.xml',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'))
        # Tables
        table_count = sum(len(sheet.tables) for sheet in workbook.sheets)
        for i in range(1, table_count + 1):
            overrides.append((f'/xl/tables/table{i}.xml',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.table+xml'))
        # Pivot caches & tables
        if workbook.pivot_caches:
            for i in range(1, len(workbook.pivot_caches) + 1):
                overrides.append((f'/xl/pivotCache/pivotCacheDefinition{i}.xml',
                                  'application/vnd.openxmlformats-officedocument.spreadsheetml.pivotCacheDefinition+xml'))
        if workbook.pivot_tables:
            for i in range(1, len(workbook.pivot_tables) + 1):
                overrides.append((f'/xl/pivotTables/pivotTable{i}.xml',
                                  'application/vnd.openxmlformats-officedocument.spreadsheetml.pivotTable+xml'))
        # VBA (XLSM)
        if workbook.vba_project and self._parent._esdm_options.write_macros:
            overrides.append(('/xl/vbaProject.bin', 'application/vnd.ms-office.vbaProject'))

        root = ET.Element('Types', xmlns='http://schemas.openxmlformats.org/package/2006/content-types')
        for part, ct in overrides:
            ET.SubElement(root, 'Override', {'PartName': part, 'ContentType': ct})
        ET.SubElement(root, 'Default', {'Extension': 'xml', 'ContentType': 'application/xml'})
        ET.SubElement(root, 'Default', {'Extension': 'rels', 'ContentType': 'application/vnd.openxmlformats-package.relationships+xml'})
        ET.SubElement(root, 'Default', {'Extension': 'bin', 'ContentType': 'application/vnd.ms-office.vbaProject'})
        return ET.tostring(root, encoding='unicode', xml_declaration=True)


class RelationshipsWriter:
    """Generates .rels files for workbook root and worksheets."""

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer

    def write_root_rels(self, workbook: Workbook) -> str:
        """_rels/.rels"""
        root = ET.Element('Relationships', xmlns='http://schemas.openxmlformats.org/package/2006/relationships')
        ET.SubElement(root, 'Relationship', {
            'Id': 'rId1',
            'Type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument',
            'Target': 'xl/workbook.xml'
        })
        ET.SubElement(root, 'Relationship', {
            'Id': 'rId2',
            'Type': 'http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties',
            'Target': 'docProps/core.xml'
        })
        # Optional: add VBA relationship
        if workbook.vba_project and self._parent._esdm_options.write_macros:
            ET.SubElement(root, 'Relationship', {
                'Id': 'rId3',
                'Type': 'http://schemas.microsoft.com/office/2006/relationships/vbaProject',
                'Target': 'xl/vbaProject.bin'
            })
        return ET.tostring(root, encoding='unicode', xml_declaration=True)

    def write_worksheet_rels(self, rels: List[Tuple[str, str, str]]) -> str:
        """xl/worksheets/_rels/sheetX.xml.rels"""
        root = ET.Element('Relationships', xmlns='http://schemas.openxmlformats.org/package/2006/relationships')
        for rel_id, target, rel_type in rels:
            ET.SubElement(root, 'Relationship', {
                'Id': rel_id,
                'Type': rel_type,
                'Target': target
            })
        return ET.tostring(root, encoding='unicode', xml_declaration=True)


class CommentWriter:
    """Handles legacy comments (VML) and threaded comments (modern)."""

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer

    def write_legacy_comments_vml(self, comments: List[Comment], sheet_index: int) -> Optional[str]:
        """
        Generate vmlDrawing1.vml for legacy comments (Excel 2007 style).
        Returns None if no comments.
        """
        if not comments:
            return None
        # Build VML XML (simplified; real VML is complex)
        root = ET.Element('xml', {'xmlns:v': 'urn:schemas-microsoft-com:vml',
                                  'xmlns:o': 'urn:schemas-microsoft-com:office:office',
                                  'xmlns:x': 'urn:schemas-microsoft-com:office:excel'})
        for idx, comment in enumerate(comments, start=1):
            shape = ET.SubElement(root, 'v:shape', {
                'id': f'_x0000_s{idx}',
                'type': '#_x0000_t202',
                'style': f'position:absolute; margin-left:10pt; margin-top:10pt; width:100pt; height:50pt; z-index:{idx}',
                'fillcolor': '#ffffe1'
            })
            ET.SubElement(shape, 'v:fill', {'color2': '#ffffe1'})
            ET.SubElement(shape, 'v:shadow', {'on': 't', 'obscured': 't'})
            ET.SubElement(shape, 'v:textbox', {'style': 'mso-direction-alt:auto'})
            # Author + text
            author = self._parent._comment_authors[comment.author_id] if comment.author_id < len(self._parent._comment_authors) else "Unknown"
            text = ''.join(run.text for run in comment.text.runs) if comment.text.runs else ""
            content = f'{author}:\n{text}'
            ET.SubElement(shape, 'div', {'style': 'text-align:left'}).text = content
            # Reference cell
            ET.SubElement(shape, 'x:ClientData', {'ObjectType': 'Note'})
        return ET.tostring(root, encoding='unicode', xml_declaration=True)

    def write_threaded_comments_xml(self, threaded_comments: List[ThreadedComment], sheet_index: int) -> Optional[str]:
        """
        Generate threadedComment1.xml for modern Excel comments.
        """
        if not threaded_comments:
            return None
        root = ET.Element('ThreadedComments', {'xmlns': XML_NAMESPACES['']})
        for idx, tc in enumerate(threaded_comments, start=1):
            tc_elem = ET.SubElement(root, 'threadedComment', {
                'ref': tc.ref,
                'id': f'{{00000000-0000-0000-0000-0000000000{idx:03}}}',
                'personId': 'person1',
                'dateTime': tc.date or ''
            })
            text_elem = ET.SubElement(tc_elem, 'text')
            text_elem.text = tc.text
        # Also need commentAuthors.xml, etc. For simplicity, we skip.
        return ET.tostring(root, encoding='unicode', xml_declaration=True)


class HyperlinkWriter:
    """Generates hyperlink elements inside worksheets and their relationships."""

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer

    def write_hyperlinks_and_rels(self, hyperlinks: List[Hyperlink],
                                   sheet_index: int) -> Tuple[List[ET.Element], List[Tuple[str, str, str]]]:
        """
        Returns:
        - list of hyperlink XML elements (to be appended to worksheet)
        - list of relationships (rel_id, target, type) for worksheet .rels
        """
        hyperlink_elems = []
        rels = []
        for idx, hl in enumerate(hyperlinks):
            rel_id = f'hyperlink_{sheet_index}_{idx}'
            hyperlink_elems.append(
                ET.Element('hyperlink', {
                    'ref': hl.ref,
                    'r:id': rel_id,
                    'tooltip': hl.tooltip or ''
                })
            )
            rels.append((rel_id, hl.target,
                         'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink'))
        return hyperlink_elems, rels


