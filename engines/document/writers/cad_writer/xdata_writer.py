# """
# XDataWriter
# Writes Extended Data (XData) from CSDM to DWG objects.

# XData structure in CSDM:
#     CSDMXData:
#         app_name: str
#         entries: List[CSDMXDataEntry]

#     CSDMXDataEntry:
#         group_code: int
#         value: any

# Runs AFTER:
#     - All DWG objects exist and registered
#     - RegApp records generated (through non_graphical_writer)

# Runs BEFORE:
#     - ReactorWriter
#     - Finalizer
# """

# from __future__ import annotations
# from typing import Any

# from .base_context import WriterContext
# from ...models.base.csdm_core import CSDMXData, CSDMXDataEntry


# class XDataWriter:
#     def __init__(self, ctx: WriterContext):
#         self.ctx = ctx
#         self.oda = ctx.oda
#         self.dwg = ctx.dwg

#     # ===============================================================
#     # PUBLIC
#     # ===============================================================
#     def write(self):
#         self.ctx.log("Writing XData...")

#         # XData can be on any object (entities, tables, blocks, dict items)
#         for handle, oda_obj in self.ctx.registry.items():

#             csdm_obj = self.ctx.csdm_doc.find_object_by_handle(handle)
#             if not csdm_obj:
#                 continue

#             xdata_list = getattr(csdm_obj, "xdata", None)
#             if not xdata_list:
#                 continue

#             for xdata in xdata_list:
#                 self._apply_xdata(oda_obj, xdata)

#         self.ctx.log("XData written.")

#     # ===============================================================
#     # APPLY ONE XDATA
#     # ===============================================================
#     def _apply_xdata(self, oda_obj: Any, xdata: CSDMXData):
#         """
#         Writes XData using ODA format:
#             beginXData(appName)
#             addXData(groupCode, value)
#             endXData()
#         """
#         try:
#             app = xdata.app_name

#             oda_obj.beginXData(app)

#             for entry in xdata.entries:
#                 gc = entry.group_code
#                 val = entry.value
#                 oda_obj.addXData(gc, val)

#             oda_obj.endXData()

#         except Exception as e:
#             self.ctx.error(f"Error writing XData to {oda_obj}: {e}")
