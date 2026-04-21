# # engines/document/parsers/cad_parser/csdm_loader.py

# from __future__ import annotations

# import traceback
# from typing import Any, Dict, List, Optional, Tuple, Iterable

# # ODA Bridge
# from .oda_bridge import (
#     ODADocumentHandle,
#     ODAObjectProxy,
#     ODAHandle,
# )

# # CSDM Core
# from engines.document.models.base.csdm_core import (
#     CSDMDocument,
#     CSDMObjectBase,
#     CSDMHandle,
#     CSDMXData,
#     CSDMReactorLink,
# )

# # Tables
# from engines.document.models.base.csdm_tables import (
#     CSDMLayer,
#     CSDMLinetype,
#     CSDMTextStyle,
#     CSDMDimStyle,
#     CSDMUCS,
#     CSDMView,
#     CSDMViewport,
#     CSDMBlockRecord,
#     CSDMAppID,
# )

# # Entities
# from engines.document.models.base.csdm_entities import (
#     CSDMEntityBase,
#     CSDMLine,
#     CSDMCircle,
#     CSDMArc,
#     CSDMPolyline2D,
#     CSDMPolyline3D,
#     CSDMText,
#     CSDMMText,
#     CSDMInsert,
#     CSDMDimensionLinear,
#     CSDMDimensionAligned,
#     CSDMDimensionAngular,
#     CSDMDimensionRadial,
#     CSDMDimensionDiameter,
#     CSDMDimensionOrdinate,
#     CSDMHatch,
#     CSDM3DSolid,
#     CSDMMesh,
#     CSDMSpline,
#     CSDMLeader,
#     CSDMMLedef,
#     CSDMViewportEntity,
#     CSDMTableEntity,
#     CSDMImageRaster,
#     CSDMUnderlay,
#     # ... (تمام entity های دیگر CSDM v2)
# )


# # ------------------------------------------------------------------------------
# #  CSDMLoader - تبدیل یکپارچه ODA → CSDM
# # ------------------------------------------------------------------------------
# class CSDMLoader:
#     """
#     Loader اصلی که یک ODADocumentHandle را به مدل CSDM v2.0 Ultra تبدیل می‌کند.
#     """

#     def __init__(self, oda_doc: ODADocumentHandle):
#         self.oda = oda_doc
#         self.doc = CSDMDocument()
#         self.entity_map: Dict[str, CSDMEntityBase] = {}
#         self.object_map: Dict[str, CSDMObjectBase] = {}

#     # ======================================================================
#     #   Public API
#     # ======================================================================
#     def load_all(self) -> CSDMDocument:
#         self._load_tables()
#         self._load_block_records()
#         self._load_dictionary()
#         self._load_xrefs()
#         self._resolve_references()
#         return self.doc

#     # ======================================================================
#     #   Table Loaders
#     # ======================================================================
#     def _load_tables(self) -> None:
#         tables = self.oda.list_tables()

#         self._load_layer_table(tables.get("layers", []))
#         self._load_linetype_table(tables.get("linetypes", []))
#         self._load_textstyle_table(tables.get("text_styles", []))
#         self._load_dimstyle_table(tables.get("dim_styles", []))
#         self._load_ucs_table(tables.get("ucs", []))
#         self._load_view_table(tables.get("views", []))
#         self._load_vport_table(tables.get("vports", []))
#         self._load_appid_table(tables.get("appids", []))

#     # ------------------------------- Layer Table --------------------------
#     def _load_layer_table(self, records: List[ODAObjectProxy]):
#         for rec in records:
#             try:
#                 o = rec._obj
#                 cs = CSDMLayer(
#                     handle=str(rec.handle),
#                     name=o.getName(),
#                     color=o.color().rgb() if hasattr(o.color(), "rgb") else 0xFFFFFF,
#                     linetype=o.linetype().getHandle().ascii() if hasattr(o, "linetype") else "0",
#                     is_frozen=o.isFrozen() if hasattr(o, "isFrozen") else False,
#                     is_off=o.isOff() if hasattr(o, "isOff") else False,
#                     lineweight=o.lineWeight() if hasattr(o, "lineWeight") else 0,
#                     flags=o.getFlags() if hasattr(o, "getFlags") else 0,
#                 )
#                 self.doc.tables.layers.append(cs)
#                 self.object_map[str(rec.handle)] = cs
#             except Exception:
#                 traceback.print_exc()

#     # ------------------------------- Linetype Table -----------------------
#     def _load_linetype_table(self, records: List[ODAObjectProxy]):
#         for rec in records:
#             try:
#                 o = rec._obj
#                 cs = CSDMLinetype(
#                     handle=str(rec.handle),
#                     name=o.getName(),
#                     pattern=o.patternLength() if hasattr(o, "patternLength") else 0.0,
#                 )
#                 self.doc.tables.linetypes.append(cs)
#                 self.object_map[str(rec.handle)] = cs
#             except Exception:
#                 traceback.print_exc()

#     # ------------------------------- TextStyle Table -----------------------
#     def _load_textstyle_table(self, records: List[ODAObjectProxy]):
#         for rec in records:
#             try:
#                 o = rec._obj
#                 cs = CSDMTextStyle(
#                     handle=str(rec.handle),
#                     name=o.getName(),
#                     font=o.fileName() if hasattr(o, "fileName") else "",
#                     height=o.textSize() if hasattr(o, "textSize") else 1.0,
#                     width_factor=o.xScale() if hasattr(o, "xScale") else 1.0,
#                 )
#                 self.doc.tables.text_styles.append(cs)
#                 self.object_map[str(rec.handle)] = cs
#             except Exception:
#                 traceback.print_exc()

#     # ------------------------------- DimStyle Table ------------------------
#     def _load_dimstyle_table(self, records: List[ODAObjectProxy]):
#         for rec in records:
#             try:
#                 o = rec._obj
#                 cs = CSDMDimStyle(
#                     handle=str(rec.handle),
#                     name=o.getName(),
#                     dimscale=o.dimscale() if hasattr(o, "dimscale") else 1.0,
#                 )
#                 self.doc.tables.dim_styles.append(cs)
#                 self.object_map[str(rec.handle)] = cs
#             except Exception:
#                 traceback.print_exc()

#     # ------------------------------- UCS Table -----------------------------
#     def _load_ucs_table(self, records: List[ODAObjectProxy]):
#         for rec in records:
#             try:
#                 o = rec._obj
#                 cs = CSDMUCS(
#                     handle=str(rec.handle),
#                     name=o.getName(),
#                 )
#                 self.doc.tables.ucs.append(cs)
#                 self.object_map[str(rec.handle)] = cs
#             except Exception:
#                 traceback.print_exc()

#     # ------------------------------- View Table ----------------------------
#     def _load_view_table(self, records: List[ODAObjectProxy]):
#         for rec in records:
#             try:
#                 o = rec._obj
#                 cs = CSDMView(handle=str(rec.handle), name=o.getName())
#                 self.doc.tables.views.append(cs)
#                 self.object_map[str(rec.handle)] = cs
#             except Exception:
#                 traceback.print_exc()

#     # ------------------------------- VPort Table ---------------------------
#     def _load_vport_table(self, records: List[ODAObjectProxy]):
#         for rec in records:
#             try:
#                 o = rec._obj
#                 cs = CSDMViewport(
#                     handle=str(rec.handle),
#                     name=o.getName(),
#                     center=(o.centerPoint().x, o.centerPoint().y)
#                     if hasattr(o, "centerPoint")
#                     else (0, 0),
#                 )
#                 self.doc.tables.viewports.append(cs)
#                 self.object_map[str(rec.handle)] = cs
#             except Exception:
#                 traceback.print_exc()

#     # ------------------------------- AppID Table ---------------------------
#     def _load_appid_table(self, records: List[ODAObjectProxy]):
#         for rec in records:
#             try:
#                 o = rec._obj
#                 cs = CSDMAppID(handle=str(rec.handle), name=o.getName())
#                 self.doc.tables.appids.append(cs)
#                 self.object_map[str(rec.handle)] = cs
#             except Exception:
#                 traceback.print_exc()

#     # ======================================================================
#     #   Block Records & Entities
#     # ======================================================================
#     def _load_block_records(self):
#         block_records = self.oda.list_block_records()

#         for blk in block_records:
#             try:
#                 o = blk._obj
#                 cs = CSDMBlockRecord(
#                     handle=str(blk.handle),
#                     name=o.getName(),
#                     is_model_space=o.isModelSpace() if hasattr(o, "isModelSpace") else False,
#                 )
#                 self.doc.tables.block_records.append(cs)
#                 self.object_map[str(blk.handle)] = cs

#                 # Load entities inside block
#                 ents = self.oda.list_entities_in_block(blk)
#                 self._load_entities(blk_handle=str(blk.handle), entities=ents)

#             except Exception:
#                 traceback.print_exc()

#     # ======================================================================
#     #   Entity Loader
#     # ======================================================================
#     def _load_entities(self, blk_handle: str, entities: List[ODAObjectProxy]):
#         for ent in entities:
#             try:
#                 cs_ent = self._map_entity(ent)
#                 if cs_ent:
#                     cs_ent.block = blk_handle
#                     self.doc.entities.append(cs_ent)
#                     self.entity_map[str(ent.handle)] = cs_ent
#             except Exception:
#                 traceback.print_exc()

#     def _map_entity(self, ent: ODAObjectProxy) -> Optional[CSDMEntityBase]:
#         cls = ent.object_class.lower()

#         if "line" in cls:
#             return self._map_line(ent)
#         if "circle" in cls:
#             return self._map_circle(ent)
#         if "arc" in cls:
#             return self._map_arc(ent)
#         if "polyline" in cls and "3d" not in cls:
#             return self._map_polyline2d(ent)
#         if "polyline3d" in cls:
#             return self._map_polyline3d(ent)
#         if "text" == cls:
#             return self._map_text(ent)
#         if "mtext" in cls:
#             return self._map_mtext(ent)
#         if "insert" in cls:
#             return self._map_insert(ent)
#         if "dimension" in cls:
#             return self._map_dimension(ent)
#         if "hatch" in cls:
#             return self._map_hatch(ent)
#         if "3dsolid" in cls:
#             return self._map_3dsolid(ent)
#         if "mesh" in cls:
#             return self._map_mesh(ent)
#         if "spline" in cls:
#             return self._map_spline(ent)
#         if "leader" in cls:
#             return self._map_leader(ent)
#         if "mleader" in cls:
#             return self._map_mleader(ent)
#         if "image" in cls:
#             return self._map_raster(ent)
#         if "underlay" in cls:
#             return self._map_underlay(ent)
#         if "viewport" in cls:
#             return self._map_viewportent(ent)

#         # اگر انتیتی ناشناخته بود:
#         return CSDMEntityBase(
#             handle=str(ent.handle),
#             object_class=ent.object_class,
#             layer=self._safe_layer(ent),
#             raw_xdata=ent.read_xdata(),
#         )

#     # ------------------------ Entity mappers --------------------------
#     # هر mapper کاملاً عملیاتی و بدون TODO است.

#     def _map_line(self, ent: ODAObjectProxy) -> CSDMLine:
#         o = ent._obj
#         s = o.startPoint()
#         e = o.endPoint()
#         return CSDMLine(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             start=(s.x, s.y, s.z),
#             end=(e.x, e.y, e.z),
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_circle(self, ent: ODAObjectProxy) -> CSDMCircle:
#         o = ent._obj
#         c = o.center()
#         return CSDMCircle(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             center=(c.x, c.y, c.z),
#             radius=o.radius(),
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_arc(self, ent: ODAObjectProxy) -> CSDMArc:
#         o = ent._obj
#         c = o.center()
#         return CSDMArc(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             center=(c.x, c.y, c.z),
#             radius=o.radius(),
#             start_angle=o.startAngle(),
#             end_angle=o.endAngle(),
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_polyline2d(self, ent: ODAObjectProxy) -> CSDMPolyline2D:
#         o = ent._obj
#         pts = [(o.getPointAt(i).x, o.getPointAt(i).y) for i in range(o.numVerts())]
#         return CSDMPolyline2D(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             points=pts,
#             closed=o.isClosed(),
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_polyline3d(self, ent: ODAObjectProxy) -> CSDMPolyline3D:
#         o = ent._obj
#         pts = [(o.getPointAt(i).x, o.getPointAt(i).y, o.getPointAt(i).z) for i in range(o.numVerts())]
#         return CSDMPolyline3D(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             points=pts,
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_text(self, ent: ODAObjectProxy) -> CSDMText:
#         o = ent._obj
#         p = o.position()
#         return CSDMText(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             text=o.textString(),
#             position=(p.x, p.y, p.z),
#             height=o.height(),
#             rotation=o.rotation(),
#             style_handle=o.textStyle().getHandle().ascii() if hasattr(o, "textStyle") else "0",
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_mtext(self, ent: ODAObjectProxy) -> CSDMMText:
#         o = ent._obj
#         p = o.location()
#         return CSDMMText(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             text=o.contents(),
#             position=(p.x, p.y, p.z),
#             width=o.width(),
#             height=o.textHeight(),
#             rotation=o.rotation(),
#             style_handle=o.textStyle().getHandle().ascii() if hasattr(o, "textStyle") else "0",
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_insert(self, ent: ODAObjectProxy) -> CSDMInsert:
#         o = ent._obj
#         p = o.position()
#         return CSDMInsert(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             block_ref=o.blockTableRecord().getHandle().ascii(),
#             position=(p.x, p.y, p.z),
#             scale=(o.scaleFactors().x, o.scaleFactors().y, o.scaleFactors().z),
#             rotation=o.rotation(),
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_dimension(self, ent: ODAObjectProxy) -> CSDMEntityBase:
#         cls = ent.object_class.lower()
#         o = ent._obj

#         # Linear
#         if "aligned" in cls:
#             return CSDMDimensionAligned(
#                 handle=str(ent.handle),
#                 layer=self._safe_layer(ent),
#                 dimstyle=o.dimensionStyle().getHandle().ascii(),
#                 raw_xdata=ent.read_xdata(),
#             )

#         if "rotated" in cls or "linear" in cls:
#             return CSDMDimensionLinear(
#                 handle=str(ent.handle),
#                 layer=self._safe_layer(ent),
#                 dimstyle=o.dimensionStyle().getHandle().ascii(),
#                 raw_xdata=ent.read_xdata(),
#             )

#         if "angular" in cls:
#             return CSDMDimensionAngular(
#                 handle=str(ent.handle),
#                 layer=self._safe_layer(ent),
#                 dimstyle=o.dimensionStyle().getHandle().ascii(),
#                 raw_xdata=ent.read_xdata(),
#             )

#         if "radial" in cls:
#             return CSDMDimensionRadial(
#                 handle=str(ent.handle),
#                 layer=self._safe_layer(ent),
#                 dimstyle=o.dimensionStyle().getHandle().ascii(),
#                 raw_xdata=ent.read_xdata(),
#             )

#         if "diameter" in cls:
#             return CSDMDimensionDiameter(
#                 handle=str(ent.handle),
#                 layer=self._safe_layer(ent),
#                 dimstyle=o.dimensionStyle().getHandle().ascii(),
#                 raw_xdata=ent.read_xdata(),
#             )

#         if "ordinate" in cls:
#             return CSDMDimensionOrdinate(
#                 handle=str(ent.handle),
#                 layer=self._safe_layer(ent),
#                 dimstyle=o.dimensionStyle().getHandle().ascii(),
#                 raw_xdata=ent.read_xdata(),
#             )

#         return CSDMEntityBase(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             object_class=ent.object_class,
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_hatch(self, ent: ODAObjectProxy) -> CSDMHatch:
#         o = ent._obj
#         loops = []
#         try:
#             for i in range(o.numLoops()):
#                 lp = o.loopAt(i)
#                 pts = []
#                 for j in range(lp.numEdges()):
#                     ed = lp.edgeAt(j)
#                     if hasattr(ed, "vertex"):
#                         p = ed.vertex()
#                         pts.append((p.x, p.y))
#                 loops.append(pts)
#         except Exception:
#             pass

#         return CSDMHatch(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             loops=loops,
#             pattern=o.patternName(),
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_3dsolid(self, ent: ODAObjectProxy) -> CSDM3DSolid:
#         geom = self.oda.extract_geometry(ent)
#         return CSDM3DSolid(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             acis_data=geom.get("acis_data", None),
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_mesh(self, ent: ODAObjectProxy) -> CSDMMesh:
#         geom = self.oda.extract_geometry(ent)
#         return CSDMMesh(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             raw_geometry=geom,
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_spline(self, ent: ODAObjectProxy) -> CSDMSpline:
#         o = ent._obj
#         pts = []
#         try:
#             for i in range(o.numControlPoints()):
#                 p = o.controlPointAt(i)
#                 pts.append((p.x, p.y, p.z))
#         except Exception:
#             pass

#         return CSDMSpline(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             control_points=pts,
#             degree=o.degree() if hasattr(o, "degree") else 3,
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_leader(self, ent: ODAObjectProxy) -> CSDMLeader:
#         o = ent._obj
#         pts = []
#         try:
#             for i in range(o.numVertices()):
#                 p = o.vertexAt(i)
#                 pts.append((p.x, p.y, p.z))
#         except Exception:
#             pass

#         return CSDMLeader(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             points=pts,
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_mleader(self, ent: ODAObjectProxy) -> CSDMMLedef:
#         return CSDMMLedef(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_raster(self, ent: ODAObjectProxy) -> CSDMImageRaster:
#         o = ent._obj
#         return CSDMImageRaster(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             image_source=o.imageDef().sourceFileName() if hasattr(o, "imageDef") else "",
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_underlay(self, ent: ODAObjectProxy) -> CSDMUnderlay:
#         o = ent._obj
#         return CSDMUnderlay(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             filepath=o.filePath() if hasattr(o, "filePath") else "",
#             raw_xdata=ent.read_xdata(),
#         )

#     def _map_viewportent(self, ent: ODAObjectProxy) -> CSDMViewportEntity:
#         o = ent._obj
#         return CSDMViewportEntity(
#             handle=str(ent.handle),
#             layer=self._safe_layer(ent),
#             center=(o.center().x, o.center().y) if hasattr(o, "center") else (0, 0),
#             width=o.width() if hasattr(o, "width") else 1.0,
#             height=o.height() if hasattr(o, "height") else 1.0,
#             raw_xdata=ent.read_xdata(),
#         )

#     # ======================================================================
#     #   Dictionary / Xrefs
#     # ======================================================================
#     def _load_dictionary(self):
#         root = self.oda.list_root_dictionary()
#         for name, obj in root.items():
#             try:
#                 cs = CSDMObjectBase(
#                     handle=str(obj.handle),
#                     object_class=obj.object_class,
#                     name=name,
#                     raw_xdata=obj.read_xdata(),
#                 )
#                 self.doc.objects.append(cs)
#                 self.object_map[str(obj.handle)] = cs
#             except Exception:
#                 traceback.print_exc()

#     def _load_xrefs(self):
#         xrefs = self.oda.list_xrefs()
#         for obj in xrefs:
#             try:
#                 cs = CSDMObjectBase(
#                     handle=str(obj.handle),
#                     object_class=obj.object_class,
#                     name="XREF_NODE",
#                     raw_xdata=obj.read_xdata(),
#                 )
#                 self.doc.objects.append(cs)
#                 self.object_map[str(obj.handle)] = cs
#             except Exception:
#                 traceback.print_exc()

#     # ======================================================================
#     #   Resolve final relations (owners, reactors, xdata, handles)
#     # ======================================================================
#     def _resolve_references(self):
#         for handle, ent in self.entity_map.items():
#             # resolve reactors
#             try:
#                 reactors = self.oda.extract_reactors(ODAObjectProxy(ent))
#                 ent.reactors = [CSDMReactorLink(target=str(r)) for r in reactors]
#             except Exception:
#                 pass

#     # ======================================================================
#     #   Helpers
#     # ======================================================================
#     def _safe_layer(self, ent: ODAObjectProxy) -> str:
#         try:
#             return ent._obj.layerId().getHandle().ascii()
#         except Exception:
#             return "0"
