# # engines/document/parsers/cad_parser/oda_bridge.py
# from __future__ import annotations
# import io
# import traceback
# from dataclasses import dataclass
# from typing import Any, Dict, Iterable, List, Optional
# # Important: Main ODA API
# # If it has a different name in the system, just change this import.
# import odapython as oda # type: ignore
# # -------------------------------------------------------------
# # Handle Wrapper
# # -------------------------------------------------------------
# @dataclass(frozen=True)
# class ODAHandle:
#     raw: str
#     def __str__(self) -> str:
#         return self.raw
#     @staticmethod
#     def from_obj(obj: Any) -> "ODAHandle":
#         try:
#             h = obj.objectId().getHandle().ascii()
#             return ODAHandle(h)
#         except Exception:
#             return ODAHandle("0")
# # -------------------------------------------------------------
# # Object Proxy - A general wrapper for any ODA DbObject
# # -------------------------------------------------------------
# class ODAObjectProxy:
#     def __init__(self, obj: Any):
#         self._obj = obj
#     @property
#     def handle(self) -> ODAHandle:
#         return ODAHandle.from_obj(self._obj)
#     @property
#     def object_id(self) -> Any:
#         try:
#             return self._obj.objectId()
#         except Exception:
#             return None
#     @property
#     def object_class(self) -> str:
#         try:
#             return self._obj.isA().name()
#         except Exception:
#             return "Unknown"
#     @property
#     def owner_id(self) -> Optional[str]:
#         try:
#             return self._obj.ownerId().getHandle().ascii()
#         except Exception:
#             return None
#     def has_xdata(self) -> bool:
#         try:
#             return self._obj.hasXData()
#         except Exception:
#             return False
#     def read_xdata(self) -> Dict[str, Any]:
#         if not self.has_xdata():
#             return {}
#         out: Dict[str, Any] = {}
#         try:
#             xdata_dict = self._obj.xDataDictionary()
#             if xdata_dict is None:
#                 return {}
#             it = xdata_dict.newIterator()
#             while not it.done():
#                 key = it.key()
#                 val = it.object()
#                 try:
#                     out[key] = str(val)
#                 except Exception:
#                     out[key] = "UNKNOWN"
#                 it.next()
#         except Exception:
#             pass
#         return out
#     def __repr__(self):
#         return f"<ODAObjectProxy {self.object_class} {self.handle}>"
# # -------------------------------------------------------------
# # ODADocumentHandle - wrapper for DWG/DCF database
# # -------------------------------------------------------------
# class ODADocumentHandle:
#     def __init__(self, db: Any):
#         self.db = db
#     # ------------------------------ #
#     #  Table Extractors
#     # ------------------------------ #
#     def list_tables(self) -> Dict[str, List[ODAObjectProxy]]:
#         return {
#             "layers": self._extract_table(oda.OdDbLayerTable),
#             "linetypes": self._extract_table(oda.OdDbLinetypeTable),
#             "text_styles": self._extract_table(oda.OdDbTextStyleTable),
#             "dim_styles": self._extract_table(oda.OdDbDimStyleTable),
#             "ucs": self._extract_table(oda.OdDbUCSTable),
#             "views": self._extract_table(oda.OdDbViewTable),
#             "vports": self._extract_table(oda.OdDbViewportTable),
#             "block_records": self._extract_table(oda.OdDbBlockTable),
#             "appids": self._extract_table(oda.OdDbRegAppTable),
#         }
#     def _extract_table(self, table_type: Any) -> List[ODAObjectProxy]:
#         out: List[ODAObjectProxy] = []
#         try:
#             table_id = self.db.getSymbolTableId(table_type.desc())
#             table = table_id.safeOpenObject()
#             it = table.newIterator()
#             while not it.done():
#                 record = it.getRecordId().safeOpenObject()
#                 out.append(ODAObjectProxy(record))
#                 it.step()
#         except Exception:
#             pass
#         return out
#     # ------------------------------ #
#     #  Block Records & Entities
#     # ------------------------------ #
#     def list_block_records(self) -> List[ODAObjectProxy]:
#         try:
#             blk_id = self.db.getSymbolTableId(oda.OdDbBlockTable.desc())
#             blk = blk_id.safeOpenObject()
#         except Exception:
#             return []
#         results: List[ODAObjectProxy] = []
#         it = blk.newIterator()
#         while not it.done():
#             try:
#                 rec = it.getRecordId().safeOpenObject()
#                 results.append(ODAObjectProxy(rec))
#             except Exception:
#                 pass
#             it.step()
#         return results
#     def list_entities_in_block(self, block_record: ODAObjectProxy) -> List[ODAObjectProxy]:
#         out: List[ODAObjectProxy] = []
#         try:
#             blk = block_record._obj
#             it = blk.newIterator()
#             while not it.done():
#                 try:
#                     ent = it.entity().safeOpenObject()
#                     out.append(ODAObjectProxy(ent))
#                 except Exception:
#                     pass
#                 it.step()
#         except Exception:
#             pass
#         return out
#     # ------------------------------ #
#     #  Object Dictionary
#     # ------------------------------ #
#     def list_root_dictionary(self) -> Dict[str, ODAObjectProxy]:
#         out: Dict[str, ODAObjectProxy] = {}
#         try:
#             dict_id = self.db.objectDictionary()
#             root = dict_id.safeOpenObject()
#             it = root.newIterator()
#             while not it.done():
#                 key = it.name()
#                 obj = it.objectId().safeOpenObject()
#                 out[key] = ODAObjectProxy(obj)
#                 it.next()
#         except Exception:
#             pass
#         return out
#     # ------------------------------ #
#     #  XREFs
#     # ------------------------------ #
#     def list_xrefs(self) -> List[ODAObjectProxy]:
#         out: List[ODAObjectProxy] = []
#         try:
#             xref_dict = self.db.getXRefGraph()
#             for i in range(xref_dict.numNodes()):
#                 try:
#                     node = xref_dict.node(i)
#                     id_ = node.database().ownerId()
#                     out.append(ODAObjectProxy(id_.safeOpenObject()))
#                 except Exception:
#                     pass
#         except Exception:
#             pass
#         return out
#     # ------------------------------ #
#     #  ACIS / Geometry Extraction
#     # ------------------------------ #
#     def extract_geometry(self, obj: ODAObjectProxy) -> Dict[str, Any]:
#         try:
#             o = obj._obj
#             if hasattr(o, "shells"):
#                 return {"type": "3d_solid", "acis_data": "raw_solid"}
#             if hasattr(o, "mesh"):
#                 return {"type": "mesh", "faces": o.numFaces()}
#             if hasattr(o, "get_A_database"):
#                 # generic geometry placeholder
#                 return {"type": "generic_geom"}
#         except Exception:
#             pass
#         return {}
#     # ------------------------------ #
#     #  Reactors
#     # ------------------------------ #
#     def extract_reactors(self, obj: ODAObjectProxy) -> List[ODAHandle]:
#         out: List[ODAHandle] = []
#         try:
#             ids = obj._obj.getPersistentReactors()
#             for rid in ids:
#                 try:
#                     h = rid.getHandle().ascii()
#                     out.append(ODAHandle(h))
#                 except Exception:
#                     pass
#         except Exception:
#             pass
#         return out
# # -------------------------------------------------------------
# # ODABridge - Main layer for managing ODA database
# # -------------------------------------------------------------
# class ODABridge:
#     def __init__(self):
#         self.services = oda.OdRxServices()
#     # ------------------------------ #
#     #  Loaders
#     # ------------------------------ #
#     def load_bytes(self, data: bytes) -> ODADocumentHandle:
#         try:
#             db = oda.OdDbDatabase.createDatabase()
#             strm = oda.OdMemoryStream()
#             strm.setData(data)
#             db.readFile(strm)
#             return ODADocumentHandle(db)
#         except Exception as e:
#             traceback.print_exc()
#             raise RuntimeError(f"Failed to load DWG data from bytes: {e}")
#     def load_file(self, path: str) -> ODADocumentHandle:
#         try:
#             db = oda.OdDbDatabase.readFile(path)
#             return ODADocumentHandle(db)
#         except Exception as e:
#             traceback.print_exc()
#             raise RuntimeError(f"Failed to load DWG file '{path}': {e}")
