# """
# TableWriter for CSDM v2.0 Ultra
# Responsible for populating all DWG tables using ODA API.

# Tables Covered:
#     - LAYER
#     - LTYPE
#     - STYLE (TextStyle)
#     - DIMSTYLE (incl. overrides)
#     - MLINESTYLE
#     - TABLESTYLE
#     - MLEADERSTYLE
#     - APPID
#     - UCS
#     - VIEW
#     - VPORT
#     - LIGHTLIST
#     - BLOCK_RECORD (only non-graphical block records)
# """

# from __future__ import annotations
# from typing import Any

# from .base_context import WriterContext
# from engines.document.models.base.csdm_tables import (
#     CSDMLayerTable,
#     CSDMLinetypeTable,
#     CSDMTextStyleTable,
#     CSDMDimStyleTable,
#     CSDMMLineStyleTable,
#     CSDMTableStyleTable,
#     CSDMMLeaderStyleTable,
#     CSDMUcsTable,
#     CSDMViewTable,
#     CSDMVPortTable,
#     CSDMAppIdTable,
#     CSDMLightTable,
# )
# from engines.document.models.base.csdm_core import CSDMDocument


# class TableWriter:
#     """
#     Writes all DWG tables from CSDMDocument.
#     This runs BEFORE entities, blocks, xdata, reactors, layouts.
#     """

#     def __init__(self, ctx: WriterContext):
#         self.ctx = ctx
#         self.oda = ctx.oda
#         self.dwg = ctx.dwg

#     # =====================================================================
#     # Public API
#     # =====================================================================
#     def write(self):
#         self.ctx.log("Writing DWG tables...")

#         tables = self.ctx.csdm_doc.tables

#         self._write_layers(tables.layers)
#         self._write_linetypes(tables.linetypes)
#         self._write_text_styles(tables.text_styles)
#         self._write_dimstyles(tables.dimstyles)
#         self._write_mline_styles(tables.mline_styles)
#         self._write_table_styles(tables.table_styles)
#         self._write_mleader_styles(tables.mleader_styles)
#         self._write_appids(tables.appids)
#         self._write_ucs(tables.ucs)
#         self._write_view(tables.views)
#         self._write_vports(tables.vports)
#         self._write_lightlist(tables.lights)

#         self.ctx.log("DWG tables written.")

#     # =====================================================================
#     # Layer Table
#     # =====================================================================
#     def _write_layers(self, table: CSDMLayerTable):
#         self.ctx.log("  Writing LayerTable")

#         lt = self.dwg.getTable("LAYER")

#         for layer in table.items:
#             rec = lt.create(layer.name)
#             rec.setColor(layer.color)
#             rec.setLinetype(layer.linetype)
#             rec.setLineweight(layer.lineweight)
#             rec.setFrozen(layer.frozen)
#             rec.setLocked(layer.locked)
#             rec.setPlot(layer.plot)
#             rec.setTransparency(layer.transparency)

#             self.ctx.register(layer.handle, rec)

#     # =====================================================================
#     # Linetype Table
#     # =====================================================================
#     def _write_linetypes(self, table: CSDMLinetypeTable):
#         self.ctx.log("  Writing LinetypeTable")

#         lt = self.dwg.getTable("LTYPE")

#         for lt_rec in table.items:
#             rec = lt.create(lt_rec.name)
#             rec.setDescription(lt_rec.description)
#             rec.setPattern(lt_rec.pattern, lt_rec.length)

#             self.ctx.register(lt_rec.handle, rec)

#     # =====================================================================
#     # TextStyle Table
#     # =====================================================================
#     def _write_text_styles(self, table: CSDMTextStyleTable):
#         self.ctx.log("  Writing TextStyleTable")

#         st = self.dwg.getTable("STYLE")

#         for t in table.items:
#             rec = st.create(t.name)
#             rec.setFont(t.font_name, t.big_font)
#             rec.setWidthFactor(t.width_factor)
#             rec.setObliquing(t.oblique)
#             rec.setTextHeight(t.height)
#             rec.setFlag(t.flags)

#             self.ctx.register(t.handle, rec)

#     # =====================================================================
#     # DimStyle Table
#     # =====================================================================
#     def _write_dimstyles(self, table: CSDMDimStyleTable):
#         self.ctx.log("  Writing DimStyleTable")

#         ds = self.dwg.getTable("DIMSTYLE")

#         for dim in table.items:
#             rec = ds.create(dim.name)

#             # Core fields
#             rec.setDimensionScale(dim.scale)
#             rec.setTextHeight(dim.text_height)
#             rec.setArrowSize(dim.arrow_size)
#             rec.setLineWeight(dim.lineweight)

#             # Numeric formatting
#             rec.setPrecision(dim.precision)
#             rec.setLinearUnit(dim.linear_unit)
#             rec.setAngularUnit(dim.angular_unit)

#             # Overrides
#             for key, value in dim.overrides.items():
#                 rec.setOverride(key, value)

#             # Annotative
#             rec.setAnnotative(dim.annotative)

#             self.ctx.register(dim.handle, rec)

#     # =====================================================================
#     # MLineStyle
#     # =====================================================================
#     def _write_mline_styles(self, table: CSDMMLineStyleTable):
#         self.ctx.log("  Writing MLineStyleTable")

#         ms = self.dwg.getRootDictionary()["ACAD_MLINESTYLE"]

#         for ml in table.items:
#             rec = ms.create(ml.name)
#             rec.setDescription(ml.description)
#             rec.setStartAngle(ml.start_angle)
#             rec.setEndAngle(ml.end_angle)

#             for element in ml.elements:
#                 rec.addElement(
#                     offset=element.offset,
#                     color=element.color,
#                     linetype=element.linetype
#                 )

#             self.ctx.register(ml.handle, rec)

#     # =====================================================================
#     # CADTableStyle
#     # =====================================================================
#     def _write_table_styles(self, table: CSDMTableStyleTable):
#         self.ctx.log("  Writing TableStyleTable")

#         ts = self.dwg.getRootDictionary()["ACAD_TABLESTYLE"]

#         for t in table.items:
#             rec = ts.create(t.name)

#             rec.setFlowDirection(t.flow_direction)
#             rec.setHorzCellMargin(t.h_margin)
#             rec.setVertCellMargin(t.v_margin)

#             for key, cell in t.cells.items():
#                 rec.setCellFormat(
#                     key,
#                     cell.text_style,
#                     cell.alignment,
#                     cell.color,
#                     cell.data_type
#                 )

#             self.ctx.register(t.handle, rec)

#     # =====================================================================
#     # MLeaderStyle
#     # =====================================================================
#     def _write_mleader_styles(self, table: CSDMMLeaderStyleTable):
#         self.ctx.log("  Writing MLeaderStyleTable")

#         ml = self.dwg.getRootDictionary()["ACAD_MLEADERSTYLE"]

#         for s in table.items:
#             rec = ml.create(s.name)

#             rec.setArrowSize(s.arrow_size)
#             rec.setContentType(s.content_type)
#             rec.setTextStyle(s.text_style)
#             rec.setLeaderType(s.leader_type)
#             rec.setLandingGap(s.landing_gap)

#             self.ctx.register(s.handle, rec)

#     # =====================================================================
#     # AppID Table
#     # =====================================================================
#     def _write_appids(self, table: CSDMAppIdTable):
#         self.ctx.log("  Writing AppIdTable")

#         ap = self.dwg.getTable("APPID")

#         for app in table.items:
#             rec = ap.create(app.name)
#             rec.setFlag(app.flags)
#             self.ctx.register(app.handle, rec)

#     # =====================================================================
#     # UCS Table
#     # =====================================================================
#     def _write_ucs(self, table: CSDMUcsTable):
#         self.ctx.log("  Writing UcsTable")

#         ucs = self.dwg.getTable("UCS")

#         for u in table.items:
#             rec = ucs.create(u.name)
#             rec.setOrigin(u.origin)
#             rec.setXAxis(u.x_axis)
#             rec.setYAxis(u.y_axis)

#             self.ctx.register(u.handle, rec)

#     # =====================================================================
#     # View Table
#     # =====================================================================
#     def _write_view(self, table: CSDMViewTable):
#         self.ctx.log("  Writing ViewTable")

#         vw = self.dwg.getTable("VIEW")

#         for v in table.items:
#             rec = vw.create(v.name)
#             rec.setCenter(v.center)
#             rec.setWidth(v.width)
#             rec.setHeight(v.height)
#             rec.setDirection(v.direction)
#             rec.setTarget(v.target)

#             self.ctx.register(v.handle, rec)

#     # =====================================================================
#     # VPORT Table
#     # =====================================================================
#     def _write_vports(self, table: CSDMVPortTable):
#         self.ctx.log("  Writing VPortTable")

#         vp = self.dwg.getTable("VPORT")

#         for v in table.items:
#             rec = vp.create(v.name)
#             rec.setCenter(v.center)
#             rec.setHeight(v.height)
#             rec.setAspectRatio(v.aspect)
#             rec.setViewDirection(v.direction)
#             rec.setViewTarget(v.target)
#             rec.setTwistAngle(v.twist)

#             self.ctx.register(v.handle, rec)

#     # =====================================================================
#     # LightList Table
#     # =====================================================================
#     def _write_lightlist(self, table: CSDMLightTable):
#         self.ctx.log("  Writing LightList")

#         ll = self.dwg.getTable("LIGHTLIST")

#         for l in table.items:
#             rec = ll.create(l.name)
#             rec.setType(l.type)
#             rec.setIntensity(l.intensity)
#             rec.setPosition(l.position)
#             rec.setTarget(l.target)
#             rec.setColor(l.color)

#             self.ctx.register(l.handle, rec)
