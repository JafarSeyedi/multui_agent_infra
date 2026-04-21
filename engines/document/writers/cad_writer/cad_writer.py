# """
# CADWriter
# ==============
# Main orchestrator for generating DWG files from a BaseDocument (CSDM Document).

# This class is the only public writer exposed to the document engine.
# It receives a BaseDocument and produces binary DWG bytes.

# It operates by invoking a sequence of specialized writer modules:
#     1) DWGBuilder              — Create base DWG and root tables
#     2) TableWriter             — Populate all DWG tables
#     3) NonGraphicalWriter      — Write dictionaries, xrecords, plotsettings, materials, layouts...
#     4) BlockWriter             — Build all BlockRecords and nested block entities
#     5) EntityWriter            — Write graphical entities inside blocks
#     6) XDataWriter             — Attach full XData
#     7) ReactorWriter           — Attach reactors
#     8) ACISWriter              — SAT/BREP data for solids/surfaces
#     9) Finalizer               — Purge, audit, regen, optimize and save into bytes

# Author: DWG/CSDM Ultra Pipeline
# """

# from __future__ import annotations
# import traceback
# from typing import Any

# from engines.document.writers.base import BaseDocumentWriter
# from engines.document.parsers.models import BaseDocument

# from .cad_writer.base_context import WriterContext
# from .cad_writer.dwg_builder import DWGBuilder
# from .cad_writer.table_writer import TableWriter
# from .cad_writer.non_graphical_writer import NonGraphicalWriter
# from .cad_writer.block_writer import BlockWriter
# from .cad_writer.entity_writer import EntityWriter
# from .cad_writer.xdata_writer import XDataWriter
# from .cad_writer.reactor_writer import ReactorWriter
# from .cad_writer.acis_writer import ACISWriter
# from .cad_writer.finalizer import Finalizer


# class CADWriter(BaseDocumentWriter):
#     """
#     Public-facing writer class.

#     Called by:
#         engines/document/writers/document_writer_dispatcher.py
#     """

#     async def write(self, document: BaseDocument) -> bytes:
#         """
#         Main entry point.

#         Input: BaseDocument (already validated, normalized CSDM structure)
#         Output: DWG bytes
#         """

#         ctx = None

#         try:
#             # ----------------------------------------------------------
#             # Create Writer Context
#             # ----------------------------------------------------------
#             ctx = WriterContext(csdm_doc=engines.document.models.base.csdm)
#             ctx.log("=== Starting DWG generation pipeline ===")

#             # ==========================================================
#             # 1) DWG BUILDER
#             # ==========================================================
#             DWGBuilder(ctx).build()

#             # ==========================================================
#             # 2) TABLE WRITER
#             # ==========================================================
#             TableWriter(ctx).write()

#             # ==========================================================
#             # 3) NON-GRAPHICAL WRITER
#             # ==========================================================
#             NonGraphicalWriter(ctx).write()

#             # ==========================================================
#             # 4) BLOCK WRITER
#             # ==========================================================
#             BlockWriter(ctx).write()

#             # ==========================================================
#             # 5) ENTITY WRITER
#             # ==========================================================
#             EntityWriter(ctx).write()

#             # ==========================================================
#             # 6) XDATA
#             # ==========================================================
#             XDataWriter(ctx).write()

#             # ==========================================================
#             # 7) REACTORS
#             # ==========================================================
#             ReactorWriter(ctx).write()

#             # ==========================================================
#             # 8) ACIS
#             # ==========================================================
#             ACISWriter(ctx).write()

#             # ==========================================================
#             # 9) FINALIZATION
#             # ==========================================================
#             finalizer = Finalizer(ctx)
#             output_bytes = finalizer.finalize()

#             ctx.log("=== DWG pipeline successfully completed ===")
#             return output_bytes

#         except Exception as e:
#             err_msg = f"DWG writer failed: {e}\n{traceback.format_exc()}"
#             if ctx:
#                 ctx.error(err_msg)
#             else:
#                 print(err_msg)
#             raise

#         finally:
#             if ctx:
#                 try:
#                     ctx.close()
#                 except Exception:
#                     pass
