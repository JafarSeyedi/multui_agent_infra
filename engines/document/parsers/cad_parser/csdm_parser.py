# # engines/document/parsers/cad_parser/csdm_parser.py
# from __future__ import annotations
# import traceback
# from typing import Optional
# from ...parsers.base_document_parser import BaseDocumentParser, BaseDocument
# from ...models.base.csdm_core import CSDMDocument
# from .oda_bridge import ODABridge
# from .csdm_loader import CSDMLoader
# from .csdm_relationships import CSDMRelationshipResolver
# # ------------------------------------------------------------------------------
# #   Main Parser Class
# # ------------------------------------------------------------------------------
# class CSDMDocumentParser(BaseDocumentParser):
#     """
#     مسیر کامل پردازش DWG/DCF:
#     1) Load DWG using ODA
#     2) Extract data → ODA snapshot
#     3) Convert snapshot → CSDMDocument (via loader)
#     4) Resolve all relationships (handles, blocks, reactors)
#     5) Output final BaseDocument
#     """
#     FORMAT = ["dwg", "dwf", "dxf", "dcf"]
#     NAME = "cCadParser"
#     VERSION = "1.0.0"
#     # ===================================================================
#     #   ENTRY POINT
#     # ===================================================================
#     def parse(self, file_path: str) -> BaseDocument:
#         try:
#             # --------------------------------------------------------------
#             # 1) Load DWG via ODA
#             # --------------------------------------------------------------
#             oda = ODABridge()
#             dwg = oda.load_document(file_path)
#             # --------------------------------------------------------------
#             # 2) Extract raw ODA snapshot
#             # --------------------------------------------------------------
#             snap = oda.extract_full_snapshot(dwg)
#             # --------------------------------------------------------------
#             # 3) Convert snapshot → CSDMDocument
#             # --------------------------------------------------------------
#             loader = CSDMLoader()
#             csdm_doc: CSDMDocument = loader.build_from_snapshot(snap)
#             # --------------------------------------------------------------
#             # 4) Resolve all relationships
#             # --------------------------------------------------------------
#             resolver = CSDMRelationshipResolver(csdm_doc)
#             resolver.resolve_all()
#             # --------------------------------------------------------------
#             # 5) Output final BaseDocument
#             # --------------------------------------------------------------
#             return BaseDocument(
#                 data=csdm_doc,
#                 format="dwg",
#                 parser=self.NAME,
#                 version=self.VERSION,
#             )
#         except Exception as e:
#             traceback.print_exc()
#             raise RuntimeError(f"Failed to parse DWG file: {file_path}\n{e}")
