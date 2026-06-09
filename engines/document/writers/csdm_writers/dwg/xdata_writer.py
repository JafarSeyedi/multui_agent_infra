"""
XDataWriter
Writes Extended Data (XData) from CSDM to DWG objects.
XData structure in CSDM:
    CSDMObject.xdata -> XDataContainer
        entries: List[XDataEntry]
    XDataEntry:
        appid: str
        data: any
Runs AFTER:
    - All DWG objects exist and registered
    - RegApp records generated (through non_graphical_writer)
Runs BEFORE:
    - ReactorWriter
    - Finalizer
"""
from __future__ import annotations
from typing import Any
from .base_context import WriterContext
from ....models.csdm_core import CSDMHandle, XDataContainer, XDataEntry
class XDataWriter:
    def __init__(self, ctx: WriterContext) -> None:
        self.ctx = ctx
        self.oda = ctx.oda
        self.dwg = ctx.dwg
    # ===============================================================
    # PUBLIC
    # ===============================================================
    def write(self) -> None:
        self.ctx.log("Writing XData...")
        # XData can be on any object (entities, tables, blocks, dict items)
        for handle, oda_obj in self.ctx.registry.items():
            csdm_obj = self.ctx.csdm_doc.find_by_handle(CSDMHandle(value=handle))
            if not csdm_obj:
                continue
            xdata_container: XDataContainer | None = getattr(csdm_obj, "xdata", None)
            if not xdata_container:
                continue
            self._apply_xdata(oda_obj, xdata_container)
        self.ctx.log("XData written.")
    # ===============================================================
    # APPLY XDATA
    # ===============================================================
    def _apply_xdata(self, oda_obj: Any, xdata_container: XDataContainer):
        """
        Writes XData using ODA format:
            beginXData(appName)
            addXData(groupCode, value)
            endXData()
        """
        try:
            # Each XDataEntry has appid and data
            for entry in xdata_container.entries:
                app = entry.appid
                val = entry.data
                oda_obj.beginXData(app)
                oda_obj.addXData(app, val)
                oda_obj.endXData()
        except Exception as e:
            self.ctx.error(f"Error writing XData to {oda_obj}: {e}")