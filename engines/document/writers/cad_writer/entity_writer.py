# """
# EntityWriter for CSDM v2.0 Ultra
# Responsible for writing all graphical entities into DWG using odapython.

# Covers:
#     - Basic geometry (Line, Circle, Arc, Polyline, Spline)
#     - Text / MText
#     - Hatch
#     - BlockReference (Insert)
#     - Leaders / MLeader
#     - Dimensions (all types)
#     - Solids / Surfaces / Meshes / 3DSolids
#     - Raster / Underlay
#     - Tables
#     - Viewports
#     - OLE objects
#     - XData
#     - Reactors
#     - Owner/Transform resolution (except relationship step)

# This writer assumes:
#     - Tables have already been written
#     - BlockRecords exist and are mapped in context registry
# """

# from __future__ import annotations
# from typing import Any, Dict, Callable

# from .base_context import WriterContext
# from engines.document.models.base.csdm_core import (
#     CSDMObject,
#     Vector3,
#     Matrix4,
# )
# from engines.document import csdm_entities as E


# class EntityWriter:
#     """
#     Main dispatcher for all entities.
#     """

#     def __init__(self, ctx: WriterContext):
#         self.ctx = ctx
#         self.oda = ctx.oda
#         self.dwg = ctx.dwg

#         # dispatch registry
#         self._handlers: Dict[str, Callable[[Any], Any]] = {
#             "LINE": self._write_line,
#             "CIRCLE": self._write_circle,
#             "ARC": self._write_arc,
#             "LWPOLYLINE": self._write_lwpolyline,
#             "POLYLINE": self._write_polyline,
#             "SPLINE": self._write_spline,
#             "TEXT": self._write_text,
#             "MTEXT": self._write_mtext,
#             "HATCH": self._write_hatch,
#             "INSERT": self._write_insert,
#             "DIMENSION": self._write_dimension,
#             "LEADER": self._write_leader,
#             "MLEADER": self._write_mleader,
#             "3DSOLID": self._write_3dsolid,
#             "MESH": self._write_mesh,
#             "SURFACE": self._write_surface,
#             "UNDERLAY": self._write_underlay,
#             "RASTER": self._write_raster,
#             "TABLE": self._write_table_entity,
#             "VIEWPORT": self._write_viewport,
#             "OLE2FRAME": self._write_ole2frame,
#         }

#     # =====================================================================
#     # Public API
#     # =====================================================================
#     def write(self):
#         self.ctx.log("Writing DWG entities...")

#         for entity in self.ctx.csdm_doc.entities:
#             handler = self._handlers.get(entity.type)
#             if handler is None:
#                 self.ctx.log(f"  WARNING: Unsupported entity: {entity.type}")
#                 continue

#             oda_ent = handler(entity)
#             if oda_ent:
#                 self._apply_common(entity, oda_ent)
#                 self.ctx.register(entity.handle, oda_ent)

#         self.ctx.log("DWG entities written.")

#     # =====================================================================
#     # Common properties for all entities
#     # =====================================================================
#     def _apply_common(self, e: E.BaseEntity, oda_obj: Any):
#         # layer
#         if e.layer:
#             oda_obj.setLayer(e.layer)

#         # linetype
#         if e.linetype:
#             oda_obj.setLinetype(e.linetype)

#         # lineweight
#         if e.lineweight is not None:
#             oda_obj.setLineweight(e.lineweight)

#         # color
#         if e.color is not None:
#             oda_obj.setColor(e.color)

#         # transparency
#         if e.transparency is not None:
#             oda_obj.setTransparency(e.transparency)

#         # owner
#         if e.owner:
#             owner = self.ctx.resolve(e.owner)
#             if owner:
#                 oda_obj.setOwner(owner)

#         # xdata
#         if e.xdata:
#             for xd in e.xdata:
#                 oda_obj.addXData(xd.appid, xd.to_oda())

#         # reactors
#         for r in e.reactors:
#             oda_obj.addReactor(r)

#     # =====================================================================
#     # Geometry
#     # =====================================================================
#     def _write_line(self, e: E.Line):
#         ent = self.dwg.newEntity("LINE")
#         ent.setStartPoint(e.start)
#         ent.setEndPoint(e.end)
#         return ent

#     def _write_circle(self, e: E.Circle):
#         ent = self.dwg.newEntity("CIRCLE")
#         ent.setCenter(e.center)
#         ent.setRadius(e.radius)
#         return ent

#     def _write_arc(self, e: E.Arc):
#         ent = self.dwg.newEntity("ARC")
#         ent.setCenter(e.center)
#         ent.setRadius(e.radius)
#         ent.setAngles(e.start_angle, e.end_angle)
#         return ent

#     # =====================================================================
#     # Polyline / LWPolyline
#     # =====================================================================
#     def _write_lwpolyline(self, e: E.LWPolyline):
#         ent = self.dwg.newEntity("LWPOLYLINE")
#         ent.setClosed(e.closed)

#         for v in e.vertices:
#             ent.addVertex(v.x, v.y, v.bulge)

#         return ent

#     def _write_polyline(self, e: E.Polyline):
#         ent = self.dwg.newEntity("POLYLINE")
#         ent.setClosed(e.closed)

#         for v in e.vertices:
#             p = ent.addVertex()
#             p.setPoint(v.position)
#             if v.bulge:
#                 p.setBulge(v.bulge)

#         return ent

#     # =====================================================================
#     # Spline
#     # =====================================================================
#     def _write_spline(self, e: E.Spline):
#         ent = self.dwg.newEntity("SPLINE")

#         ent.setDegree(e.degree)
#         ent.setFitPoints(e.fit_points)
#         ent.setControlPoints(e.control_points)
#         ent.setKnots(e.knots)

#         ent.setClosed(e.closed)
#         return ent

#     # =====================================================================
#     # Text
#     # =====================================================================
#     def _write_text(self, e: E.Text):
#         ent = self.dwg.newEntity("TEXT")
#         ent.setText(e.text)
#         ent.setPosition(e.position)
#         ent.setHeight(e.height)
#         ent.setRotation(e.rotation)
#         return ent

#     def _write_mtext(self, e: E.MText):
#         ent = self.dwg.newEntity("MTEXT")
#         ent.setText(e.text)
#         ent.setLocation(e.position)
#         ent.setRotation(e.rotation)
#         ent.setWidth(e.width)
#         return ent

#     # =====================================================================
#     # Hatch
#     # =====================================================================
#     def _write_hatch(self, e: E.Hatch):
#         ent = self.dwg.newEntity("HATCH")

#         ent.setPattern(e.pattern_name, e.angle, e.scale)
#         ent.setAssociative(e.associative)

#         for loop in e.loops:
#             l = ent.addLoop(loop.type)
#             for edge in loop.edges:
#                 l.addEdge(edge.to_oda())

#         return ent

#     # =====================================================================
#     # Insert (BlockReference)
#     # =====================================================================
#     def _write_insert(self, e: E.Insert):
#         ent = self.dwg.newEntity("INSERT")

#         block_rec = self.ctx.resolve(e.block_record)
#         if block_rec:
#             ent.setBlockRecord(block_rec)

#         ent.setPosition(e.position)
#         ent.setScale(e.scale)
#         ent.setRotation(e.rotation)

#         return ent

#     # =====================================================================
#     # Dimensions
#     # =====================================================================
#     def _write_dimension(self, e: E.Dimension):
#         ent = self.dwg.newEntity("DIMENSION")

#         ent.setPoints(e.def_points)
#         ent.setDimStyle(e.dimstyle)
#         ent.setMeasurement(e.measurement)

#         if e.text_override:
#             ent.setTextOverride(e.text_override)

#         return ent

#     # =====================================================================
#     # Leaders / MLeader
#     # =====================================================================
#     def _write_leader(self, e: E.Leader):
#         ent = self.dwg.newEntity("LEADER")
#         ent.setPoints(e.points)
#         ent.setAnnotative(e.annotative)
#         ent.setHasAnnotation(e.has_annotation)
#         return ent

#     def _write_mleader(self, e: E.MLeader):
#         ent = self.dwg.newEntity("MLEADER")
#         ent.setContentType(e.content_type)
#         ent.setText(e.text)
#         ent.setStyle(e.style)

#         for ln in e.leaders:
#             l = ent.addLeader()
#             for p in ln.points:
#                 l.addPoint(p)

#         return ent

#     # =====================================================================
#     # Solids
#     # =====================================================================
#     def _write_3dsolid(self, e: E.Solid3D):
#         ent = self.dwg.newEntity("3DSOLID")
#         if e.acis_data:
#             ent.loadAcis(e.acis_data)
#         return ent

#     # Surfaces
#     def _write_surface(self, e: E.Surface):
#         ent = self.dwg.newEntity("SURFACE")
#         if e.acis_data:
#             ent.loadAcis(e.acis_data)
#         return ent

#     # Mesh
#     def _write_mesh(self, e: E.Mesh):
#         ent = self.dwg.newEntity("MESH")
#         ent.setVertices(e.vertices)
#         ent.setFaces(e.faces)
#         return ent

#     # =====================================================================
#     # Underlay / Raster
#     # =====================================================================
#     def _write_underlay(self, e: E.Underlay):
#         ent = self.dwg.newEntity("UNDERLAY")
#         ent.setPath(e.path)
#         ent.setScale(e.scale)
#         ent.setRotation(e.rotation)
#         ent.setPosition(e.position)
#         return ent

#     def _write_raster(self, e: E.Raster):
#         ent = self.dwg.newEntity("RASTER")
#         ent.setImageSource(e.path)
#         ent.setPosition(e.position)
#         ent.setScale(e.scale)
#         return ent

#     # =====================================================================
#     # Table Entity
#     # =====================================================================
#     def _write_table_entity(self, e: E.TableEntity):
#         ent = self.dwg.newEntity("ACAD_TABLE")

#         ent.setNumRows(e.rows)
#         ent.setNumColumns(e.columns)
#         ent.setStyle(e.style)

#         for r, row in enumerate(e.cells):
#             for c, cell in enumerate(row):
#                 ent.setCellText(r, c, cell.text)
#                 ent.setCellFormat(r, c, cell.format)

#         return ent

#     # =====================================================================
#     # Viewport
#     # =====================================================================
#     def _write_viewport(self, e: E.Viewport):
#         ent = self.dwg.newEntity("VIEWPORT")

#         ent.setCenter(e.center)
#         ent.setHeight(e.height)
#         ent.setAspectRatio(e.aspect)
#         ent.setTarget(e.target)
#         ent.setViewDirection(e.direction)

#         return ent

#     # =====================================================================
#     # OLE
#     # =====================================================================
#     def _write_ole2frame(self, e: E.Ole2Frame):
#         ent = self.dwg.newEntity("OLE2FRAME")
#         ent.setBinaryData(e.data)
#         ent.setPosition(e.position)
#         ent.setSize(e.size)
#         return ent
