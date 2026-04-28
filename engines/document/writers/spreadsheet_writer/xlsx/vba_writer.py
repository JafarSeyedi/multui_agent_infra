# engines/document/writers/spreadsheet_writer/xlsx/vba_writer.py
"""
VBA (Visual Basic for Applications) writer for XLSM files.
Manages inclusion of vbaProject.bin and its relationships.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from ....models.esdm_models import Workbook
    from ..base import ESDMBaseWriter


class VBAWriter:
    """
    Handles VBA project for macro-enabled workbooks.
    """

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer

    def write(self, workbook: Workbook) -> Optional[Tuple[str, bytes, str]]:
        """
        Returns (target_path, binary_data, rel_id) if VBA is present and enabled,
        otherwise returns None.

        The returned data can be used to:
        - Add the binary to ZIP parts
        - Add a root relationship entry
        - Add Content_Types override (handled separately)
        """
        if not workbook.vba_project or not self._parent._esdm_options.write_macros:
            return None

        target = 'xl/vbaProject.bin'
        rel_id = 'rId_vba_project'
        # The binary content is already stored in workbook.vba_project
        return target, workbook.vba_project, rel_id